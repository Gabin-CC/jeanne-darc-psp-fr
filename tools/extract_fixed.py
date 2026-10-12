"""Extrait les chaînes à champ fixe vers trad/logic.json (LOGIC.PAC) et trad/cartes.json (MAP/*.DAT).

Chaque entrée : {"en", "fr", "max"} ; max = octets disponibles (latin-1 ;
œ et — coûtent 6 octets, remplacés automatiquement par oe et - si besoin).
Les traductions existantes sont conservées.
"""
import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from jda_fixed import find_strings, columns_by_stride

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = os.path.join(ROOT, 'extract/PSP_GAME/USRDIR/DATA')

SKIP = re.compile(r'^(System Reserved|FOR DEBUG|\* .*|[a-z]+\d+.*|map\d+.*|__.*)$')


def logic_fields():
    """{pos: (texte, capacité)} pour LOGIC.PAC."""
    data = open(os.path.join(DATA, 'LOGIC/LOGIC.PAC'), 'rb').read()
    strings = find_strings(data)
    col_of = columns_by_stride(strings)
    cap = collections.defaultdict(lambda: 10 ** 9)
    for p, _, g in strings:
        cap[col_of[p]] = min(cap[col_of[p]], g)
    return {p: (s, cap[col_of[p]]) for p, s, g in strings}


def map_fields():
    """{nom_fichier: {pos: (texte, capacité)}} ; colonne = même offset dans tous les MAP*.DAT."""
    files = {os.path.basename(f): open(f, 'rb').read() for f in sorted(glob.glob(os.path.join(DATA, 'MAP/MAP*.DAT')))}
    found = {n: find_strings(d) for n, d in files.items()}
    cap = collections.defaultdict(lambda: 10 ** 9)
    for n, ss in found.items():
        for p, _, g in ss:
            cap[p] = min(cap[p], g)
    return {n: {p: (s, cap[p]) for p, s, g in ss} for n, ss in found.items()}


BOOT = os.path.join(ROOT, 'extract/PSP_GAME/SYSDIR/BOOT.BIN')
TECH = re.compile(r'(rror|0x%|%s|%f|%\.\d|::|\.(c|h|cpp|BIN|SPF|GIM|gim|DAT|PMF|PRX|prx|SFO|pgf)\b|sce[A-Z]|_[A-Za-z]|[a-z][A-Z][a-z]+[A-Z]|Thread|thread|Stack|Init|\b(THID|SPAD|MIDI|Midi|DEBUG|debug)\b|^[a-z_]+$|/)')


# Chaînes affichées au joueur malgré un %s (exclues à tort par TECH)
BOOT_ALLOW = {'Stage %d  %s ', 'Stage  %s ', '%s, \na free stage, appeared!', '\nMale\nFemale\nUnknown\nN/A\nMale?\n'}


def boot_fields():
    """{pos: (texte, capacité)} pour les chaînes affichables de BOOT.BIN."""
    data = open(BOOT, 'rb').read()
    out = {}
    for p, s, g in find_strings(data):
        if p < 0x110000 or not re.search(r'[a-z]{3}', s) or (TECH.search(s) and s not in BOOT_ALLOW):
            continue
        out[p] = (s, g)
    return out


GUI_UPPER = {'EXP', 'HP', 'MP', 'SP', 'TURN', 'OK', 'CONTINUE'}


def gui_fields():
    """{pos: (texte, capacité)} pour les libellés de GUI/GUISHT.SPF (champ de 16 octets,
    terminateur facultatif quand le champ est plein)."""
    data = open(os.path.join(DATA, 'GUI/GUISHT.SPF'), 'rb').read()
    out = {}
    for p, s, g in find_strings(data):
        if s.endswith('SHT') and len(s) > 16:  # « Restore Defaults » + magic du fichier suivant
            s = s[:16]
        if p < 0xb60 or p % 4 or len(s) > 16 or s.endswith('.SHT') or re.fullmatch(r'menu\d+|menu_tex|shopmenu', s):
            continue
        if not re.search(r'[a-z]', s) and s not in GUI_UPPER:
            continue
        if any(data[p + len(s):p + 16]):
            continue
        out[p] = (s, 16)
    return out


def basemap_fields():
    """{pos: (texte, capacité)} : noms de lieux de la carte du monde (LOGIC/BASEMAP.DAT).
    Enregistrements de 0x80 octets, nom à +2 sur 36 octets (données à +0x26)."""
    data = open(os.path.join(DATA, 'LOGIC/BASEMAP.DAT'), 'rb').read()
    out = {}
    for r in range(0, len(data), 0x80):
        p = r + 2
        s = data[p:data.index(b'\0', p)].decode('latin-1')
        if s and s != '---':
            out[p] = (s, 35)
    return out


def write_memory(path, items, min_len=3):
    """items : [(texte, capacité, contexte)] dans l'ordre."""
    old = {}
    if os.path.exists(path):
        old = {e['en']: e for e in json.load(open(path, encoding='utf-8'))}
    mem = collections.OrderedDict()
    for s, c, ctx in items:
        if SKIP.match(s) or len(s) < min_len or c < min_len + 1:
            continue
        if s in mem:
            mem[s]['max'] = min(mem[s]['max'], c)
        else:
            mem[s] = {'ctx': ctx, 'max': c, 'en': s, 'fr': old.get(s, {}).get('fr', '')}
    json.dump(list(mem.values()), open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{os.path.relpath(path, ROOT)} : {len(mem)} chaînes')


def main():
    os.makedirs(os.path.join(ROOT, 'trad'), exist_ok=True)
    lf = logic_fields()
    write_memory(os.path.join(ROOT, 'trad/logic.json'), [(s, c, hex(p)) for p, (s, c) in sorted(lf.items())])
    mf = map_fields()
    write_memory(os.path.join(ROOT, 'trad/cartes.json'),
                 [(s, c, n) for n, fields in mf.items() for p, (s, c) in sorted(fields.items())])
    items = [(s, c, 'GUISHT ' + hex(p)) for p, (s, c) in sorted(gui_fields().items())]
    items += [(s, c, 'BASEMAP ' + hex(p)) for p, (s, c) in sorted(basemap_fields().items())]
    write_memory(os.path.join(ROOT, 'trad/interface.json'), items, min_len=2)
    bf = boot_fields()
    write_memory(os.path.join(ROOT, 'trad/menus.json'), [(s, c, hex(p)) for p, (s, c) in sorted(bf.items())])


if __name__ == '__main__':
    main()
