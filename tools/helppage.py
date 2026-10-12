"""Pages d'aide illustrées (HELP/*.GIM) : effacement du texte anglais par reconstitution du fond
(inpainting OpenCV) puis écriture du texte français.

Spécification (liste d'opérations, dans l'ordre) :
  {"erase": [x0,y0,x1,y1], "mode": "light"|"dark", "thr": 170, "grow": 2, "keep": [[x0,y0,x1,y1], ...]}
      efface les pixels clairs (mode light : lum > thr) ou sombres (dark : lum < thr) de la zone,
      élargis de `grow` px (contour / ombre), sauf dans les zones `keep` (icônes).
  {"text": [x, base], "segs": [["texte", [r,g,b]], ...], "font": "gill", "cap": 10, "max_w": 200,
   "align": "left"|"center", "outline": [r,g,b] | null, "shadow": [r,g,b] | null, "spacing": 0}
      écrit une ligne (plusieurs couleurs possibles) ; x = bord gauche (ou centre si align=center).
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from gimtext import _font, FONTS

FONTS.setdefault('gill', ('/System/Library/Fonts/Supplemental/GillSans.ttc', 4))  # Gill Sans SemiBold
FONTS.setdefault('cond', ('/System/Library/Fonts/Supplemental/Avenir Next Condensed.ttc', 2))
FONTS.setdefault('hand', ('/System/Library/Fonts/Supplemental/ChalkboardSE.ttc', 2))
FONTS.setdefault('georgia', '/System/Library/Fonts/Supplemental/Georgia Bold.ttf')


def erase_flat(im, box, sample_dx=3):
    """Fond uni à dégradé vertical : chaque ligne est repeinte avec la couleur médiane prise juste
    à gauche de la zone."""
    x0, y0, x1, y1 = box
    arr = np.array(im.convert('RGBA'))
    for y in range(y0, y1):
        ref = arr[y, max(0, x0 - sample_dx):x0]
        arr[y, x0:x1] = np.median(ref, axis=0).astype(np.uint8)
    im.paste(Image.fromarray(arr, 'RGBA'), (0, 0))


def erase(im, box, mode='light', thr=170, grow=2, keep=()):
    if mode == 'flat':
        return erase_flat(im, box)
    import cv2
    arr = np.array(im.convert('RGBA'))
    rgb = arr[:, :, :3].copy()
    lum = rgb.astype(int).mean(axis=2)
    x0, y0, x1, y1 = box
    sel = np.zeros(lum.shape, bool)
    sub = lum[y0:y1, x0:x1]
    sel[y0:y1, x0:x1] = sub > thr if mode == 'light' else sub < thr
    mask = sel.astype(np.uint8) * 255
    if grow:
        mask = cv2.dilate(mask, np.ones((2 * grow + 1, 2 * grow + 1), np.uint8))
    clip = np.zeros_like(mask)
    clip[y0:y1, x0:x1] = 255
    mask &= clip
    for kx0, ky0, kx1, ky1 in keep:
        mask[ky0:ky1, kx0:kx1] = 0
    rgb = cv2.inpaint(np.ascontiguousarray(rgb), mask, 3, cv2.INPAINT_TELEA)
    out = Image.fromarray(np.dstack([rgb, arr[:, :, 3]]), 'RGBA')
    im.paste(out, (0, 0))


def text(im, pos, segs, font='gill', cap=10, max_w=None, align='left', outline=None, shadow=None,
         spacing=0, S=4):
    x, base = pos
    f = _font(font, cap * S * 2)
    hb = f.getbbox('H')
    f = _font(font, max(6, int(cap * S * 2 * cap * S / (hb[3] - hb[1]))))
    asc = f.getbbox('H')[3]
    # rendu de chaque segment côte à côte sur un grand canevas
    full = ''.join(s for s, _ in segs)
    width = int(f.getlength(full) + spacing * S * len(full)) + 8 * S
    H = asc + cap * S * 2
    mask = Image.new('L', (width, H), 0)
    colmap = Image.new('RGB', (width, H), (255, 255, 255))
    dm, dc = ImageDraw.Draw(mask), ImageDraw.Draw(colmap)
    cx = 4 * S
    for s, col in segs:
        for ch in s:
            dm.text((cx, cap * S), ch, font=f, fill=255)
            w = f.getlength(ch) + spacing * S
            dc.rectangle((cx - S, 0, cx + w + S, H), fill=tuple(col))
            cx += w
    ink = mask.getbbox()
    if not ink:
        return
    mask, colmap = mask.crop((ink[0], 0, ink[2], H)), colmap.crop((ink[0], 0, ink[2], H))
    base_in = cap * S + asc
    sx = 1.0
    if max_w and mask.width / S > max_w:
        sx = max_w * S / mask.width
    sy = 1.0 if sx >= 0.62 else sx / 0.62
    nw, nh = max(1, round(mask.width * sx / S)), max(1, round(mask.height * sy / S))
    m = mask.resize((nw, nh), Image.LANCZOS)
    c = colmap.resize((nw, nh), Image.NEAREST)
    ox = round(x - nw / 2) if align == 'center' else round(x)
    oy = round(base - base_in * sy / S)
    W, Hh = im.size
    lm = Image.new('L', (W, Hh), 0)
    lm.paste(m, (ox, oy))
    layer = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    if shadow:
        sh = lm.filter(ImageFilter.MaxFilter(3))
        sh = Image.fromarray(np.roll(np.array(sh), (1, 1), axis=(0, 1)))
        layer.paste(Image.new('RGBA', (W, Hh), tuple(shadow) + (200,)), (0, 0), sh)
    if outline:
        layer.paste(Image.new('RGBA', (W, Hh), tuple(outline) + (255,)), (0, 0), lm.filter(ImageFilter.MaxFilter(3)))
    fill = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    fill.paste(c.convert('RGBA'), (ox, oy))
    layer.paste(fill, (0, 0), lm)
    im.alpha_composite(layer)


def render_page(im, ops):
    for op in ops:
        if 'erase' in op:
            erase(im, op['erase'], op.get('mode', 'light'), op.get('thr', 170), op.get('grow', 2),
                  op.get('keep', ()))
        elif 'text' in op:
            text(im, op['text'], op['segs'], op.get('font', 'gill'), op.get('cap', 10), op.get('max_w'),
                 op.get('align', 'left'), op.get('outline'), op.get('shadow'), op.get('spacing', 0))
    return im
