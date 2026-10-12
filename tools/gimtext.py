"""Détection et remplacement de mots dans les atlas de texte GIM (interface).

- detect_words(im) : cadres des mots (composantes connexes regroupées par ligne).
- render_word(im, box, text, font, ...) : efface le mot d'origine et dessine `text` dans
  le même cadre, en reprenant les couleurs (dégradé vertical du remplissage, contour) du mot
  d'origine. Le texte est resserré horizontalement si nécessaire pour tenir dans le cadre.
"""
from PIL import Image, ImageFilter, ImageFont, ImageDraw, ImageChops

FONTS = {
    'serif': '/System/Library/Fonts/Supplemental/Georgia Bold.ttf',
    'times': '/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf',
    'sans': ('/System/Library/Fonts/Optima.ttc', 1),  # Optima Bold
    'helv': ('/System/Library/Fonts/Helvetica.ttc', 1),  # Helvetica Bold
    'optima': ('/System/Library/Fonts/Optima.ttc', 0),  # Optima Regular
    'sans_it': ('/System/Library/Fonts/Optima.ttc', 3),  # Optima Bold Italic
    'black': ('/System/Library/Fonts/Optima.ttc', 4),  # Optima ExtraBlack
}


def _font(name, size):
    f = FONTS[name]
    if isinstance(f, tuple):
        return ImageFont.truetype(f[0], size, index=f[1])
    return ImageFont.truetype(f, size)


def detect_words(im, alpha_min=40, gap=4, region=None):
    """Renvoie une liste de cadres (x0, y0, x1, y1) exclusifs."""
    a = im.getchannel('A')
    W, H = im.size
    px = a.load()
    x0r, y0r, x1r, y1r = region or (0, 0, W, H)
    seen = set()
    comps = []
    for y in range(y0r, y1r):
        for x in range(x0r, x1r):
            if px[x, y] >= alpha_min and (x, y) not in seen:
                stack = [(x, y)]
                seen.add((x, y))
                bx0 = bx1 = x
                by0 = by1 = y
                while stack:
                    cx, cy = stack.pop()
                    bx0, bx1, by0, by1 = min(bx0, cx), max(bx1, cx), min(by0, cy), max(by1, cy)
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1),
                                   (cx + 1, cy + 1), (cx - 1, cy - 1), (cx + 1, cy - 1), (cx - 1, cy + 1)):
                        if x0r <= nx < x1r and y0r <= ny < y1r and (nx, ny) not in seen and px[nx, ny] >= alpha_min:
                            seen.add((nx, ny))
                            stack.append((nx, ny))
                comps.append([bx0, by0, bx1 + 1, by1 + 1])
    # regroupe les composantes proches sur la même ligne
    merged = True
    while merged:
        merged = False
        comps.sort()
        out = []
        for c in comps:
            for o in out:
                vov = min(o[3], c[3]) - max(o[1], c[1])
                hgap = max(c[0] - o[2], o[0] - c[2])
                if vov > 0.4 * min(o[3] - o[1], c[3] - c[1]) and hgap <= gap:
                    o[:] = [min(o[0], c[0]), min(o[1], c[1]), max(o[2], c[2]), max(o[3], c[3])]
                    merged = True
                    break
            else:
                out.append(c)
        comps = out
    return [tuple(c) for c in sorted(comps, key=lambda c: (c[1], c[0]))]


def annotate(im, boxes, scale=3):
    bg = Image.new('RGBA', im.size, (70, 70, 90, 255))
    bg.alpha_composite(im)
    big = bg.resize((im.width * scale, im.height * scale), Image.NEAREST)
    d = ImageDraw.Draw(big)
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        d.rectangle((x0 * scale, y0 * scale, x1 * scale - 1, y1 * scale - 1), outline=(255, 0, 0, 255))
        d.text((x0 * scale + 1, y0 * scale), str(i), fill=(255, 255, 0, 255))
    return big


def _style(im, box):
    """Couleurs du mot d'origine : dégradé de remplissage par ligne, couleur de contour, ombre."""
    crop = im.crop(box)
    px = crop.load()
    w, h = crop.size
    opaque = [(px[x, y], y) for y in range(h) for x in range(w) if px[x, y][3] > 200]
    if not opaque:
        return None
    lum = lambda c: 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    lums = sorted(lum(c) for c, _ in opaque)
    thr = lums[len(lums) // 2]
    fill_rows = []
    for y in range(h):
        row = [c for c, yy in opaque if yy == y and lum(c) >= thr]
        fill_rows.append(tuple(sum(c[i] for c in row) // len(row) for i in range(3)) if row else None)
    # interpole les lignes vides
    known = [i for i, c in enumerate(fill_rows) if c]
    for i in range(h):
        if not fill_rows[i]:
            j = min(known, key=lambda k: abs(k - i))
            fill_rows[i] = fill_rows[j]
    dark = [c for c, _ in opaque if lum(c) < lums[len(lums) // 6 + 1]]
    outline = tuple(sum(c[i] for c in dark) // len(dark) for i in range(3)) if dark else (30, 20, 10)
    return fill_rows, outline


def render_word(im, box, text, font='sans', cap=None, base=None, outline_px=1, shadow=True,
                align='center', plain=False, min_condense=0.62, color=None, bg=None,
                fill_color=None, outline_color=None, fill_sat=False, glow=0, src=None):
    """Remplace le contenu de `box` par `text`.

    cap  : hauteur des majuscules en pixels ; base : ordonnée de la ligne de base.
    plain : texte d'une seule couleur, sans contour ni ombre (couleur prise sur l'original).
    """
    x0, y0, x1, y1 = box
    src = src or im  # image où prélever les couleurs (avant tout effacement)
    fill_rows, outline = _style(src, box)
    if fill_sat:  # dégradé pris sur les pixels saturés (le halo clair est ignoré)
        crop = src.crop(box)
        cp = crop.load()
        sat = lambda c: max(c[:3]) - min(c[:3])
        rows = []
        for y in range(crop.height):
            cs = sorted((cp[x, y] for x in range(crop.width) if cp[x, y][3] > 200 and sat(cp[x, y]) > 60),
                        key=lambda c: sum(c[:3]))
            if fill_sat == 'dark':
                cs = cs[:max(1, len(cs) // 2)]  # moitié la plus foncée : le cœur de la lettre
            rows.append(tuple(sum(c[i] for c in cs) // len(cs) for i in range(3)) if cs else None)
        known = [i for i, c in enumerate(rows) if c]
        fill_rows = [rows[i] or rows[min(known, key=lambda k: abs(k - i))] for i in range(len(rows))] if known else fill_rows
    if fill_color:
        fill_rows = [tuple(fill_color)] * (y1 - y0)
    if outline_color:
        outline = tuple(outline_color)
    if plain:
        outline_px, shadow = 0, False
        crop = src.crop(box)  # (couleur estimée avant effacement)
        ops = [c for c in crop.getdata() if c[3] > 200]
        col = tuple(color) if color else (tuple(sum(c[i] for c in ops) // len(ops) for i in range(3)) if ops else (15, 14, 13))
    w, h = x1 - x0, y1 - y0
    if bg is None:
        im.paste(Image.new('RGBA', (w, h), (0, 0, 0, 0)), (x0, y0))
    elif bg == 'rows':  # fond reconstruit : interpolation entre les colonnes x0-1 et x1
        p = im.load()
        for y in range(y0, y1):
            cl, cr = p[x0 - 1, y], p[x1, y]
            for x in range(x0, x1):
                t = (x - x0 + 1) / (w + 1)
                p[x, y] = tuple(round(cl[i] * (1 - t) + cr[i] * t) for i in range(4))
    else:
        im.paste(Image.new('RGBA', (w, h), tuple(bg) + (255,)), (x0, y0))
    sh = 1 if shadow else 0
    if cap is None:
        cap = max(4, round((h - 2 * outline_px - sh) * 0.78))
    if base is None:
        base = y0 + outline_px + cap
    S = 4
    # taille de police pour obtenir la hauteur de majuscule voulue
    size = cap * S * 2
    f = _font(font, size)
    hb = f.getbbox('H')
    size = max(6, int(size * cap * S / (hb[3] - hb[1])))
    f = _font(font, size)
    hb = f.getbbox('H')
    asc_to_base = hb[3]  # ordonnée de la ligne de base dans le repère de dessin
    bb = f.getbbox(text)
    pad = 2 * S
    canvas = Image.new('L', (bb[2] - bb[0] + 2 * pad, bb[3] + pad), 0)
    ImageDraw.Draw(canvas).text((pad - bb[0], 0), text, font=f, fill=255)
    ink = canvas.getbbox()
    canvas = canvas.crop(ink)
    base_c = asc_to_base - ink[1]  # ligne de base dans le canevas recadré
    avail = (w - 2 * outline_px - sh) * S
    avail_h = (h - 2 * outline_px - sh) * S
    sx = sy = 1.0
    if canvas.width > avail:
        sx = avail / canvas.width
        if sx < min_condense:  # trop serré : on réduit aussi la hauteur
            sy = sx / min_condense
    if canvas.height * sy > avail_h:  # accents / jambages hors cadre : on réduit
        k = avail_h / (canvas.height * sy)
        sx, sy = sx * k, sy * k
    new = canvas.resize((max(1, int(canvas.width * sx)), max(1, int(canvas.height * sy))), Image.LANCZOS)
    small = new.resize((max(1, round(new.width / S)), max(1, round(new.height / S))), Image.LANCZOS)
    base_in_small = base_c * sy / S
    mw = small.width
    if align == 'left':
        ox = outline_px
    elif align == 'right':
        ox = w - mw - outline_px - sh
    else:
        ox = (w - mw - sh) // 2
    oy = round(base - y0 - base_in_small)
    oy = max(outline_px, min(oy, h - sh - outline_px - small.height))
    layer_mask = Image.new('L', (w, h), 0)
    layer_mask.paste(small, (ox, oy))
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if plain:
        out.paste(Image.new('RGBA', (w, h), col + (255,)), (0, 0), layer_mask)
    else:
        if shadow:
            shm = ImageChops.offset(layer_mask.filter(ImageFilter.MaxFilter(3)), 1, 1)
            out.paste(Image.new('RGBA', (w, h), outline + (170,)), (0, 0), shm)
        if glow:
            gl = layer_mask.filter(ImageFilter.MaxFilter(2 * outline_px + 3)).filter(ImageFilter.GaussianBlur(glow))
            out.paste(Image.new('RGBA', (w, h), outline + (200,)), (0, 0), gl)
        if outline_px:
            ol = layer_mask.filter(ImageFilter.MaxFilter(2 * outline_px + 1))
            out.paste(Image.new('RGBA', (w, h), outline + (255,)), (0, 0), ol)
        fill = Image.new('RGBA', (w, h))
        fp = fill.load()
        n = len(fill_rows)
        for y in range(h):
            c = fill_rows[min(n - 1, max(0, y))]
            for x in range(w):
                fp[x, y] = c + (255,)
        out.paste(fill, (0, 0), layer_mask)
    im.alpha_composite(out, (x0, y0))
    return im


def render_curve_letters(im, centers, text, font='times', cap=11, radius=8, src=None):
    """Remplace des lettres espacées le long d'une courbe (inscription de carte) :
    efface les lettres d'origine (inpainting OpenCV) puis répartit `text` sur la même courbe."""
    import numpy as np
    import cv2
    src = src or im
    arr = np.array(src.convert('RGBA'))
    rgb = arr[:, :, :3].copy()
    lum = rgb.astype(int).sum(axis=2)
    mask = np.zeros(lum.shape, np.uint8)
    ink = []
    for cx, cy in centers:
        y0, y1 = max(0, cy - radius), min(lum.shape[0], cy + radius + 1)
        x0, x1 = max(0, cx - radius), min(lum.shape[1], cx + radius + 1)
        patch = lum[y0:y1, x0:x1]
        thr = np.percentile(patch, 70) - 60
        sel = patch < thr
        mask[y0:y1, x0:x1][sel] = 255
        ink.append(rgb[y0:y1, x0:x1][sel])
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
    rgb = cv2.inpaint(np.ascontiguousarray(rgb), mask, 3, cv2.INPAINT_TELEA)
    allink = np.concatenate(ink) if ink else np.array([[80, 50, 20]])
    dark = allink[allink.astype(int).sum(axis=1) <= np.percentile(allink.astype(int).sum(axis=1), 25)]
    color = tuple(int(v) for v in np.median(dark if len(dark) else allink, axis=0))
    # courbe : polyligne par les centres d'origine, rééchantillonnée pour len(text) lettres
    pts = np.array(centers, float)
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    tgt = np.linspace(0, seg[-1], len(text))
    xs, ys = np.interp(tgt, seg, pts[:, 0]), np.interp(tgt, seg, pts[:, 1])
    base = Image.fromarray(np.dstack([rgb, arr[:, :, 3]]), 'RGBA')
    S = 4
    f = _font(font, cap * S * 2)
    hb = f.getbbox('H')
    f = _font(font, max(6, int(cap * S * 2 * cap * S / (hb[3] - hb[1]))))
    layer = Image.new('L', (im.width * S, im.height * S), 0)
    d = ImageDraw.Draw(layer)
    for ch, x, y in zip(text, xs, ys):
        bb = f.getbbox(ch)
        d.text((x * S - (bb[0] + bb[2]) / 2, y * S - (bb[1] + bb[3]) / 2), ch, font=f, fill=255,
               stroke_width=S // 2, stroke_fill=255)
    layer = layer.resize(im.size, Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.4))
    ink_img = Image.new('RGBA', im.size, color + (255,))
    base.paste(ink_img, (0, 0), layer)
    im.paste(base, (0, 0))
    return im
