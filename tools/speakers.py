"""Attribue un locuteur à chaque réplique en lisant le bytecode des scripts EVENT.

Dans le bytecode, une réplique est précédée de la référence à son locuteur :
  00 81 <idx &Nom>  ...  00 81 <idx réplique>
Renvoie {texte_anglais: Counter(locuteurs)}.
"""
import collections
import glob
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
from jda_event import EventFile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


CHARS = {1: 'Jeanne', 2: 'Liane', 3: 'Roger', 4: 'Gilles', 5: 'Rufus', 6: 'La Hire', 7: 'Bartolomeo',
         8: 'Jean', 9: 'Bertrand', 10: 'Marcel', 11: 'Beatrix', 12: 'Richard', 13: 'Claire',
         14: 'Colet', 15: 'Rose', 16: 'Cuisses'}
# Bulle de combat : 05 83 86 03 03 00 | 00 80 00 <id> 00 00 | ... | 12 01 | (00 81 <idx>)+
BT_RE = re.compile(rb'\x05\x83\x86\x03\x03\x00\x00\x80\x00(.)\x00\x00.{0,24}?\x12\x01((?:\x00\x81..)+)', re.S)


def speakers():
    out = collections.defaultdict(collections.Counter)
    for path in glob.glob(os.path.join(ROOT, 'extract/PSP_GAME/USRDIR/DATA/EVENT/ST*.BIN')):
        d = open(path, 'rb').read()
        e = EventFile(d)
        text = {i: s for i, s in e.strings()}
        by_off = {}
        for i, s in text.items():
            by_off[e.offs[i]] = s
        code = d[e.code_start:e.text_start]
        for m in BT_RE.finditer(code):
            who = CHARS.get(m.group(1)[0], 'unité#%d' % m.group(1)[0])
            for k in range(0, len(m.group(2)), 4):
                idx = struct.unpack_from('<H', m.group(2), k + 2)[0]
                if idx < e.n and e.offs[idx] in by_off and not by_off[e.offs[idx]].startswith('&'):
                    out[by_off[e.offs[idx]]][who] += 1
        cur, cur_pos = None, -999
        for m in re.finditer(b'\x00\x81', code):
            idx = struct.unpack_from('<H', code, m.start() + 2)[0]
            if idx >= e.n:
                continue
            s = by_off.get(e.offs[idx])
            if s is None:
                continue
            if s.startswith('&'):
                cur, cur_pos = s[1:], m.start()
            elif cur and m.start() - cur_pos < 0x40:
                out[s][cur] += 1
                cur_pos = m.start()
    return out


if __name__ == '__main__':
    sp = speakers()
    print(len(sp), 'répliques avec locuteur')
    for k in list(sp)[:5]:
        print(sp[k].most_common(3), repr(k[:50]))
