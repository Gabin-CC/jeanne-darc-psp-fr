"""Noms de lieux pré-rendus de la carte du monde (WMAP.SPF, atlas 12 et 13).

Chaque atlas a deux colonnes (x < 128, x >= 128) de noms centrés, sur 1 ou 2 lignes, en texte
crème à contour sombre avec un halo. On détecte les lignes de texte de chaque colonne et on les
associe, dans l'ordre, aux noms fournis (avec leur nombre de lignes d'origine).
"""
from PIL import Image, ImageFilter, ImageDraw

from gimtext import _font


def _bands(im, x0, x1):
    """Lignes de texte (y0, y1, xmin, xmax) d'une colonne, d'après les pixels crème opaques."""
    p = im.load()
    rows = []
    for y in range(im.height):
        xs = [x for x in range(x0, x1) if p[x, y][3] > 200 and sum(p[x, y][:3]) > 450]
        rows.append((min(xs), max(xs)) if xs else None)
    bands, cur = [], None
    for y, r in enumerate(rows):
        if r:
            if cur and y - cur[1] <= 2:
                cur = [cur[0], y, min(cur[2], r[0]), max(cur[3], r[1])]
            else:
                if cur:
                    bands.append(cur)
                cur = [y, y, r[0], r[1]]
        elif cur and y - cur[1] > 2:
            bands.append(cur)
            cur = None
    if cur:
        bands.append(cur)
    return [b for b in bands if b[1] - b[0] >= 5]


def _style(im, bands):
    p = im.load()
    fill = [p[x, y] for b in bands for y in range(b[0], b[1] + 1) for x in range(b[2], b[3] + 1)
            if p[x, y][3] > 200 and sum(p[x, y][:3]) > 450]
    dark = [p[x, y] for b in bands for y in range(b[0], b[1] + 1) for x in range(b[2], b[3] + 1)
            if p[x, y][3] > 200 and sum(p[x, y][:3]) < 150]
    avg = lambda cs, d: tuple(sum(c[i] for c in cs) // len(cs) for i in range(3)) if cs else d
    return avg(fill, (235, 225, 200)), avg(dark, (25, 20, 15))


def _render_line(text, cap, max_w, S=4):
    f = _font('sans', cap * S * 2)
    hb = f.getbbox('H')
    size = max(6, int(cap * S * 2 * cap * S / (hb[3] - hb[1])))
    f = _font('sans', size)
    base = f.getbbox('H')[3]
    bb = f.getbbox(text)
    m = Image.new('L', (bb[2] - bb[0] + 8 * S, max(bb[3], base) + 8 * S), 0)
    ImageDraw.Draw(m).text((4 * S - bb[0], 4 * S), text, font=f, fill=255)
    ink = m.getbbox()
    m = m.crop(ink)
    base_m = base + 4 * S - ink[1]
    sx = min(1.0, max_w * S / m.width)
    sy = 1.0 if sx >= 0.6 else sx / 0.6
    m = m.resize((max(1, int(m.width * sx)), max(1, int(m.height * sy))), Image.LANCZOS)
    m = m.resize((max(1, round(m.width / S)), max(1, round(m.height / S))), Image.LANCZOS)
    return m, base_m * sy / S


def render_atlas(im, left, right, cap=9):
    """left/right : listes de (nb_lignes_origine, [lignes françaises]) dans l'ordre vertical."""
    W = im.width
    out = im.copy()
    for (x0, x1), names in (((0, W // 2), left), ((W // 2, W), right)):
        bands = _bands(im, x0, x1)
        need = sum(n for n, _ in names)
        assert len(bands) == need, f'colonne {x0}: {len(bands)} lignes détectées, {need} attendues'
        fill, dark = _style(im, bands)
        k = 0
        groups = []
        for n, lines in names:
            groups.append((bands[k:k + n], lines))
            k += n
        for gi, (bs, lines) in enumerate(groups):
            top = bs[0][0] - 4 if gi == 0 else (groups[gi - 1][0][-1][1] + bs[0][0]) // 2 + 1
            bot = bs[-1][1] + 4 if gi == len(groups) - 1 else (bs[-1][1] + groups[gi + 1][0][0][0]) // 2
            top, bot = max(0, top), min(im.height, bot)
            out.paste(Image.new('RGBA', (x1 - x0, bot - top), (0, 0, 0, 0)), (x0, top))
            width = max(b[3] for b in bs) - min(b[2] for b in bs) + 1
            cx = (max(b[3] for b in bs) + min(b[2] for b in bs) + 1) / 2
            layer = Image.new('L', im.size, 0)
            for b, txt in zip(bs, lines):
                m, base_m = _render_line(txt, cap, width + 4)
                base_y = b[0] + cap + 1
                layer.paste(m, (round(cx - m.width / 2), round(base_y - base_m)), m)
            region = (x0, top, x1, bot)
            lm = Image.new('L', im.size, 0)
            lm.paste(layer.crop(region), region[:2])
            glow = lm.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
            outline = lm.filter(ImageFilter.MaxFilter(3))
            g = Image.new('RGBA', im.size, (0, 0, 0, 0))
            g.paste(Image.new('RGBA', im.size, dark + (170,)), (0, 0), glow)
            g.paste(Image.new('RGBA', im.size, dark + (255,)), (0, 0), outline)
            g.paste(Image.new('RGBA', im.size, fill + (255,)), (0, 0), lm)
            out.alpha_composite(g.crop(region), region[:2])
    im.paste(out, (0, 0))
    return im
