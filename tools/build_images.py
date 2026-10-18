"""Textures françaises : renvoie {chemin_relatif_DATA: octets GIM/GMO}.

- trad/raven/ : textures et pages d'aide de Raven (équipe PSP Traduction), reprises telles quelles ;
- trad/images.json : nos retouches restantes (carte du monde WMAP.SPF, icônes WMICON04).
Les copies exactes de ces textures dans les archives SPF sont remplacées aussi.

Usage direct : python3 tools/build_images.py [dossier_apercu]  -> écrit des PNG d'aperçu.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gim import Gim
from gimtext import render_word
import gimwm
import re
from PIL import Image

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


def _gim_spans(data):
    """Positions (début, fin) des GIM contenus dans une archive SPF."""
    offs = [m.start() for m in re.finditer(b'MIG.00.1PSP', data)]
    return [(o, offs[k + 1] if k + 1 < len(offs) else len(data)) for k, o in enumerate(offs)]


def patch_archives(out, archives):
    """Remplace, dans toutes les archives SPF, les copies exactes des GIM modifiés."""
    originals = {open(os.path.join(DATA, rel), 'rb').read(): new for rel, new in out.items()
                 if rel.upper().endswith(('.GIM', '.GMO'))}
    seen = set()
    for root, _, files in os.walk(DATA):
        for f in files:
            if not f.upper().endswith('.SPF') or f in seen:
                continue
            seen.add(f)
            rel = os.path.relpath(os.path.join(root, f), DATA)
            key = next((k for k in archives if os.path.basename(k) == f), None)
            data = archives[key] if key else bytearray(open(os.path.join(DATA, rel), 'rb').read())
            hit = False
            for orig, new in originals.items():
                if len(new) > len(orig):
                    continue  # ne tiendrait pas dans l'archive
                new = new + b'\0' * (len(orig) - len(new))
                i = data.find(orig)
                while i >= 0:
                    data[i:i + len(orig)] = new
                    hit = True
                    i = data.find(orig, i + len(orig))
            if hit and not key:
                archives[rel] = data
    return archives


RAVEN = os.path.join(ROOT, 'trad/raven')


def raven_textures():
    """Textures refaites par Raven (équipe PSP Traduction) : GIM tels quels, pages d'aide PNG
    converties en GIM avec une palette recalculée."""
    out = {}
    gdir = os.path.join(RAVEN, 'gim')
    for root, _, files in os.walk(gdir):
        for f in files:
            if not f.upper().endswith('.GIM'):
                continue
            rel = os.path.relpath(os.path.join(root, f), gdir)
            if not os.path.exists(os.path.join(DATA, rel)):
                rel = os.path.join('GUI', rel)  # LOADING, MENU04, MENU05, MENU07 sont dans GUI/
            out[rel] = open(os.path.join(root, f), 'rb').read()
    mdir = os.path.join(RAVEN, 'gmo')  # bannières de compétences (Aura de Feu, Garde Unie)
    for f in sorted(os.listdir(mdir)) if os.path.isdir(mdir) else []:
        if f.upper().endswith('.GMO'):
            out[os.path.join('EFFECT', f.upper())] = open(os.path.join(mdir, f), 'rb').read()
    hdir = os.path.join(RAVEN, 'help')
    for f in sorted(os.listdir(hdir)) if os.path.isdir(hdir) else []:
        if f.lower().endswith('.png'):
            rel = os.path.join('HELP', f[:-4].upper() + '.GIM')
            g = Gim(open(os.path.join(DATA, rel), 'rb').read())
            out[rel] = g.from_image(Image.open(os.path.join(hdir, f)).convert('RGBA'), new_palette=True)
    return out


def build(preview_dir=None):
    spec = json.load(open(os.path.join(ROOT, 'trad/images.json'), encoding='utf-8'))
    out = {}
    archives = {}
    out.update(raven_textures())
    for key, it in spec.pop('_wmap', {}).items():
        rel, idx = key.split('#')
        data = archives.setdefault(rel, bytearray(open(os.path.join(DATA, rel), 'rb').read()))
        a, b = _gim_spans(bytes(data))[int(idx)]
        g = Gim(bytes(data[a:b]))
        im = g.to_image()
        gimwm.render_atlas(im, it['left'], it['right'])
        new = g.from_image(im)
        assert len(new) == b - a
        data[a:b] = new
        _preview(im, rel + idx, preview_dir, 2)
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
            render_word(im, tuple(it['box']), it['fr'], src=orig, **opts)
        out[rel] = g.from_image(im)
        _preview(im, rel, preview_dir, 3)
    for rel, data in patch_archives(out, archives).items():
        out[rel] = bytes(data)
    return out


def _preview(im, rel, preview_dir, scale=1):
    if not preview_dir:
        return
    os.makedirs(preview_dir, exist_ok=True)
    base = Image.new('RGBA', im.size, (70, 70, 90, 255))
    base.alpha_composite(im)
    base.resize((im.width * scale, im.height * scale), Image.NEAREST).save(
        os.path.join(preview_dir, os.path.basename(rel) + '.png'))


if __name__ == '__main__':
    r = build(sys.argv[1] if len(sys.argv) > 1 else None)
    print(len(r), 'images')
