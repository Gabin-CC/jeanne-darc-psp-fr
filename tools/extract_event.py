"""Extrait les dialogues EVENT/ST*.BIN vers une mémoire de traduction :
trad/dialogues/NNN.json, chaque chaîne anglaise unique n'apparaît qu'une fois,
dans l'ordre de l'histoire (stage par stage : avant bataille, combat, après).

Une chaîne déjà présente dans un lot existant n'est pas réextraite : les
traductions saisies sont conservées.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from jda_event import EventFile

ROOT = os.path.join(os.path.dirname(__file__), '..')
SRC = os.path.join(ROOT, 'extract/PSP_GAME/USRDIR/DATA/EVENT')
DST = os.path.join(ROOT, 'trad/dialogues')
CHUNK = 250

KIND_ORDER = {'BM': 0, 'BT': 1, 'AB': 2}
LIMITS = {'BM': 34, 'AB': 34, 'BT': 16}


def load_memory():
    mem = {}
    for p in sorted(glob.glob(os.path.join(DST, '*.json'))):
        for e in json.load(open(p, encoding='utf-8')):
            mem[e['en']] = e
    return mem


def main():
    os.makedirs(DST, exist_ok=True)
    known = load_memory()
    paths = sorted(glob.glob(os.path.join(SRC, 'ST*.BIN')),
                   key=lambda p: (os.path.basename(p)[2:6], KIND_ORDER.get(os.path.basename(p)[6:8], 9)))
    new = []
    seen = set(known)
    for path in paths:
        name = os.path.basename(path)[:-4]
        for _, s in EventFile(open(path, 'rb').read()).strings():
            if s in seen:
                continue
            seen.add(s)
            new.append({'ctx': name, 'max': LIMITS.get(name[6:8]), 'en': s, 'fr': ''})
    start = len(glob.glob(os.path.join(DST, '*.json')))
    for k in range(0, len(new), CHUNK):
        out = os.path.join(DST, '%03d.json' % (start + k // CHUNK))
        with open(out, 'w', encoding='utf-8') as fh:
            json.dump(new[k:k + CHUNK], fh, ensure_ascii=False, indent=1)
    print(f'{len(known)} chaînes déjà connues, {len(new)} nouvelles -> {(len(new) + CHUNK - 1) // CHUNK} lots')


if __name__ == '__main__':
    main()
