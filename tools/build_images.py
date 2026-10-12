"""Applique trad/images.json aux images GIM : renvoie {chemin_relatif_DATA: octets GIM}.

Usage direct : python3 tools/build_images.py [dossier_apercu]  -> écrit des PNG d'aperçu.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gim import Gim
from gimtext import render_word
from gimbanner import render_location, render_chapter, render_caption

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = os.path.join(ROOT, 'extract/PSP_GAME/USRDIR/DATA')


def _extend(im, box, up=2, down=4):
    """Agrandit le cadre vers le haut / bas tant que les lignes sont transparentes."""
    x0, y0, x1, y1 = box
    a = im.getchannel('A').load()
    empty = lambda y: 0 <= y < im.height and all(a[x, y] < 20 for x in range(x0, x1))
    for _ in range(up):
        if empty(y0 - 1):
            y0 -= 1
    for _ in range(down):
        if empty(y1):
            y1 += 1
    return x0, y0, x1, y1


def build(preview_dir=None):
    spec = json.load(open(os.path.join(ROOT, 'trad/images.json'), encoding='utf-8'))
    out = {}
    for rel, it in spec.pop('_banners', {}).items():
        g = Gim(open(os.path.join(DATA, rel), 'rb').read())
        im = g.to_image()
        if it['kind'] == 'location':
            render_location(im, it['fr'])
        elif it['kind'] == 'chapter':
            render_chapter(im, it['line1'], it['fr'])
        else:
            render_caption(im, it['fr'])
        out[rel] = g.from_image(im)
        _preview(im, rel, preview_dir)
    for rel, items in spec.items():
        g = Gim(open(os.path.join(DATA, rel), 'rb').read())
        im = g.to_image()
        orig = im.copy()
        for it in items:
            it = dict(it)
            it['box'] = list(_extend(orig, it['box'], up=it.get('ext_up', 2), down=it.get('ext_down', 4)))
            it.pop('ext_up', None)
            it.pop('ext_down', None)
            opts = {k: v for k, v in it.items() if k not in ('box', 'fr', 'outline')}
            if 'outline' in it:
                opts['outline_px'] = it['outline']
            render_word(im, tuple(it['box']), it['fr'], **opts)
        out[rel] = g.from_image(im)
        _preview(im, rel, preview_dir, 3)
    return out


def _preview(im, rel, preview_dir, scale=1):
    if not preview_dir:
        return
    from PIL import Image
    os.makedirs(preview_dir, exist_ok=True)
    base = Image.new('RGBA', im.size, (70, 70, 90, 255))
    base.alpha_composite(im)
    base.resize((im.width * scale, im.height * scale), Image.NEAREST).save(
        os.path.join(preview_dir, os.path.basename(rel) + '.png'))


if __name__ == '__main__':
    r = build(sys.argv[1] if len(sys.argv) > 1 else None)
    print(len(r), 'images')
