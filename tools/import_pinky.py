"""Import de la traduction humaine de l'équipe PSP Traduction (Pinky & Bleachy, scripts du 24/02/2019).

Format des fichiers « Scripts FR 24 02 2019/STxxxxYY.txt » (Windows-1252, CRLF) :
    <PT0128>            numéros de pointeurs (= index de table + 1), plusieurs par bloc
    <PT0129>
    Texte français      une ou plusieurs lignes ; [Clear Screen] = nouvelle boîte ; [Code14] = \\x14
    [Fin]
On aligne chaque bloc sur la réplique anglaise du même index dans EVENT/STxxxxYY.BIN.

Usage : python3 tools/import_pinky.py  -> écrit trad/pinky/dialogues.json  {en: {fr, files}}
"""
import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from jda_event import EventFile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(ROOT, 'trad officielle/Jeanne/Scripts FR 24 02 2019')
EVENT = os.path.join(ROOT, 'extract/PSP_GAME/USRDIR/DATA/EVENT')
PT = re.compile(r'^<PT(\d+)>$')


def parse(path):
    """[(indices, texte)] pour un fichier de script."""
    # Windows-1252 (et non Latin-1) : 0x92 = ’, 0x9C = œ… ; apostrophe typographique -> '
    raw = open(path, 'rb').read().decode('cp1252', errors='replace').replace('\u2019', "'")
    lines = raw.replace('\r\n', '\n').split('\n')
    blocks, idx, text = [], [], []
    for ln in lines:
        m = PT.match(ln.strip())
        if m:
            if text:  # nouveau bloc sans [Fin] explicite
                blocks.append((idx, text))
                idx, text = [], []
            idx.append(int(m.group(1)) - 1)
        elif ln.strip() == '[Fin]':
            blocks.append((idx, text))
            idx, text = [], []
        elif ln.strip() == '[Fin du script]':
            break
        elif idx:
            text.append(ln)
    out = []
    for idx, text in blocks:
        t = '\n'.join(text).strip('\n')
        t = t.replace('[Clear Screen]\n', '\f').replace('\n[Clear Screen]', '\f').replace('[Clear Screen]', '\f')
        t = t.replace('[Code14]', '\x14')
        out.append((idx, t))
    return out


def main():
    mem = collections.defaultdict(lambda: collections.Counter())
    where = collections.defaultdict(set)
    skipped = 0
    for path in sorted(glob.glob(os.path.join(SRC, 'ST*.txt'))):
        name = os.path.basename(path)[:-4]
        ev = os.path.join(EVENT, name + '.BIN')
        if not os.path.exists(ev):
            continue
        e = EventFile(open(ev, 'rb').read())
        by_off = {}
        for i, s in e.strings():
            by_off[e.offs[i]] = s
        for idx, fr in parse(path):
            if not fr or '[Balise' in fr:
                skipped += 1
                continue
            ens = {by_off.get(e.offs[i]) for i in idx if 0 <= i < e.n} - {None}
            for en in ens:
                mem[en][fr] += 1
                where[en].add(name)
    out = {en: {'fr': c.most_common(1)[0][0], 'variantes': len(c), 'files': sorted(where[en])[:5]}
           for en, c in mem.items()}
    os.makedirs(os.path.join(ROOT, 'trad/pinky'), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, 'trad/pinky/dialogues.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'{len(out)} répliques anglaises alignées ({skipped} blocs ignorés)')


if __name__ == '__main__':
    main()
