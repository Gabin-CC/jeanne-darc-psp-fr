"""Rendu des images « bandeau » : noms de lieux (PICT/MN*.GIM), cartons de chapitre
(PICT0006-0014) et légendes de scène (PICT0015-0017).

Chaque fonction redessine entièrement la zone de texte de l'image d'origine en reprenant
ses couleurs (dégradé vertical), son contour et son soulignement.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageChops

from gimtext import _font


def _longest_run(a, y, W, thr):
    best = run = 0
    for x in range(W):
        run = run + 1 if a[x, y][3] > thr else 0
        best = max(best, run)
    return best


def _text_mask(text, font, cap, S=4):
    """Masque du texte sur-échantillonné S fois ; renvoie (masque, ligne_de_base_dans_le_masque)."""
    size = cap * S * 2
    f = _font(font, size)
    hb = f.getbbox('H')
    size = max(6, int(size * cap * S / (hb[3] - hb[1])))
    f = _font(font, size)
    base = f.getbbox('H')[3]
    bb = f.getbbox(text)
    pad = 4 * S
    m = Image.new('L', (bb[2] - bb[0] + 2 * pad, max(bb[3], base) + 2 * pad), 0)
    ImageDraw.Draw(m).text((pad - bb[0], pad), text, font=f, fill=255)
    ink = m.getbbox()
    return m.crop(ink), base + pad - ink[1]


def _place(mask, base_in_mask, cx, base, max_w, S=4, min_condense=0.6):
    """Réduit le masque à l'échelle 1 (resserré si > max_w) ; renvoie (petit_masque, x, y)."""
    sx = sy = 1.0
    if mask.width / S > max_w:
        sx = max_w * S / mask.width
        if sx < min_condense:
            sy = sx / min_condense
    m = mask.resize((max(1, int(mask.width * sx)), max(1, int(mask.height * sy))), Image.LANCZOS)
    m = m.resize((max(1, round(m.width / S)), max(1, round(m.height / S))), Image.LANCZOS)
    return m, round(cx - m.width / 2), round(base - base_in_mask * sy / S)


def _row_colors(im, y0, y1, pred):
    """Couleur moyenne des pixels vérifiant `pred` pour chaque ligne de [y0, y1)."""
    p = im.load()
    rows = {}
    for y in range(y0, y1):
        cs = sorted((p[x, y] for x in range(im.width) if pred(p[x, y])), key=lambda c: -sum(c[:3]))
        cs = cs[:max(1, len(cs) // 3)]  # les plus clairs : couleur du plein de la lettre
        if cs:
            rows[y] = tuple(sum(c[i] for c in cs) // len(cs) for i in range(3))
    known = sorted(rows)
    return {y: rows[min(known, key=lambda k: abs(k - y))] for y in range(im.height)} if known else {}


def _compose(size, mask, x, y, fill_rows, outline=None, shadow=None):
    w, h = size
    lm = Image.new('L', (w, h), 0)
    lm.paste(mask, (x, y))
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if shadow:
        sh = ImageChops.offset(lm.filter(ImageFilter.MaxFilter(3)), 1, 1)
        out.paste(Image.new('RGBA', (w, h), shadow), (0, 0), sh)
    if outline:
        out.paste(Image.new('RGBA', (w, h), outline), (0, 0), lm.filter(ImageFilter.MaxFilter(3)))
    fill = Image.new('RGBA', (w, h))
    fp = fill.load()
    for yy in range(h):
        c = fill_rows.get(yy, (255, 255, 255))
        for xx in range(w):
            fp[xx, yy] = c + (255,)
    out.paste(fill, (0, 0), lm)
    return out


def render_location(im, text, font='sans', cap=17, base=27):
    """Bandeau de lieu 512x64 : texte blanc à contour noir + soulignement noir/blanc/noir."""
    W = im.width
    a = im.load()
    line_rows = [y for y in range(base + 4, im.height) if _longest_run(a, y, W, 30) > 30]
    xs = [x for x in range(W) if line_rows and a[x, line_rows[0]][3] > 30]
    line = {y: a[(xs[0] + xs[-1]) // 2, y] for y in line_rows} if xs else {}
    old_text = [x for y in range(0, base + 6) for x in range(W) if a[x, y][3] > 30]
    margin = ((xs[-1] - xs[0]) - (max(old_text) - min(old_text))) // 2 if xs and old_text else 14
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    mask, bm = _text_mask(text, font, cap)
    m, x, y = _place(mask, bm, W // 2, base, W - 2 * margin - 8)
    out.alpha_composite(_compose(im.size, m, x, y, {}, outline=(0, 0, 0, 255), shadow=(0, 0, 0, 120)))
    if line:
        lx0, lx1 = max(0, x - margin), min(W, x + m.width + margin)
        p = out.load()
        for yy, c in line.items():
            for xx in range(lx0, lx1):
                p[xx, yy] = c
    im.paste(out, (0, 0))
    return im


def render_chapter(im, line1, line2, font='times'):
    """Carton de chapitre 480x272 sur fond noir : deux lignes dorées centrées."""
    W, H = im.size
    gold = lambda c: c[0] > 60 and c[0] > c[2] + 20
    rows = _row_colors(im, 0, H, gold)
    p = im.load()
    out = Image.new('RGBA', im.size, (0, 0, 0, 255))
    for txt, cap, base in ((line1, 13, 106), (line2, 18, 149)):
        mask, bm = _text_mask(txt, font, cap)
        m, x, y = _place(mask, bm, W // 2, base, W - 40)
        out.alpha_composite(_compose(im.size, m, x, y, rows))
    im.paste(out, (0, 0))
    return im


def render_caption(im, text, font='helv'):
    """Légende 256x32 : texte blanc très resserré sur toute la largeur + soulignement."""
    W, H = im.size
    a = im.load()
    line_rows = [y for y in range(H // 2, H) if _longest_run(a, y, W, 100) > 30]
    text_rows = [y for y in range(H) if y not in line_rows and any(a[x, y][3] > 100 for x in range(W))]
    top, bottom = min(text_rows), max(text_rows)
    xs_line = [x for x in range(W) if line_rows and a[x, line_rows[0]][3] > 100]
    line = {y: a[(xs_line[0] + xs_line[-1]) // 2, y] for y in line_rows}
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    base = min(line_rows) - 3 if line_rows else bottom
    cap = round((base - top) * 0.95)
    mask, bm = _text_mask(text, font, cap)
    m, x, y = _place(mask, bm, W // 2, base, W - 4, min_condense=0.45)
    out.alpha_composite(_compose(im.size, m, x, y, {}))
    p = out.load()
    for yy, c in line.items():
        for xx in range(max(0, x - 2), min(W, x + m.width + 2)):
            p[xx, yy] = c
    im.paste(out, (0, 0))
    return im
