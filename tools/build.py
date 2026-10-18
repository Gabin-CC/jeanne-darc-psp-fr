"""Construit l'ISO français à partir de l'ISO US et des traductions de trad/.

Usage : python3 tools/build.py [--check]
  --check : vérifie seulement les traductions (longueurs de ligne), sans ISO.
"""
import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from jda_event import EventFile
import iso_patch
import jda_fixed
from extract_fixed import logic_fields, map_fields, gui_fields, basemap_fields, boot_fields, BOOT

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_ISO = os.path.join(ROOT, "Jeanne d'Arc (USA).iso")
DST_ISO = os.path.join(ROOT, "Jeanne d'Arc (FR).iso")
DATA = os.path.join(ROOT, 'extract/PSP_GAME/USRDIR/DATA')


def load_dialogues():
    mem = {}
    for p in sorted(glob.glob(os.path.join(ROOT, 'trad/dialogues/*.json'))):
        for e in json.load(open(p, encoding='utf-8')):
            if e['fr'].strip():
                mem[e['en']] = e
    return mem


def check():
    """Vérifie toutes les traductions (même règles que check_trad.py)."""
    import check_trad
    tot_err = 0
    for p in check_trad.trad_files():
        tot_err += check_trad.check_file(p)[0]
    print(f'{tot_err} erreur(s) de traduction')


def iso_paths_by_name():
    """{nom_de_fichier: [chemins ISO]} lu directement dans l'ISO source."""
    by = collections.defaultdict(list)
    with open(SRC_ISO, 'rb') as f:
        for p in iso_patch.walk(f):
            by[os.path.basename(p)].append(p)
    return by


HYPHEN = re.compile(r'(?<=[^\W\d_])-(?=[^\W\d_])')


def typo(text):
    """Trait d'union entre deux lettres -> U+2012, plus étroit dans la police de la PSP."""
    return HYPHEN.sub('\u2012', text)


def build_events(mem, by_name):
    repl = {}
    for path in sorted(glob.glob(os.path.join(DATA, 'EVENT/ST*.BIN'))):
        data = open(path, 'rb').read()
        e = EventFile(data)
        tr = {i: typo(mem[s]['fr']) for i, s in e.strings() if s in mem}
        if not tr:
            continue
        new = e.build(tr)
        for p in by_name[os.path.basename(path)]:
            repl[p] = new
    return repl


def load_fixed(name):
    p = os.path.join(ROOT, 'trad', name)
    if not os.path.exists(p):
        return {}
    return {e['en']: e['fr'] for e in json.load(open(p, encoding='utf-8')) if e['fr'] != ''}


def build_fixed(path, fields, mem, by_name, repl, targets=None):
    """fields : {pos: (texte, capacité)} ; targets : chemins ISO à écrire (défaut : même nom)."""
    edits = {}
    for p, (s, cap) in fields.items():
        if s in mem:
            raw = jda_fixed.fit(mem[s], cap)
            if len(raw) > cap:
                print(f'  ! trop long ({len(raw)}>{cap} octets) : {mem[s]!r}')
                continue
            edits[p] = (raw, cap)
    if edits:
        new = jda_fixed.apply(open(path, 'rb').read(), edits)
        for ip in targets or by_name[os.path.basename(path)]:
            repl[ip] = new


def main():
    mem = load_dialogues()
    check()
    if '--check' in sys.argv:
        return
    by_name = iso_paths_by_name()
    repl = {}
    repl.update(build_events(mem, by_name))
    logic = load_fixed('logic.json')
    build_fixed(os.path.join(DATA, 'LOGIC/LOGIC.PAC'), logic_fields(), logic, by_name, repl)
    cartes = load_fixed('cartes.json')
    for name, fields in map_fields().items():
        build_fixed(os.path.join(DATA, 'MAP', name), fields, cartes, by_name, repl)
    interface = load_fixed('interface.json')
    build_fixed(os.path.join(DATA, 'GUI/GUISHT.SPF'), gui_fields(), interface, by_name, repl)
    build_fixed(os.path.join(DATA, 'LOGIC/BASEMAP.DAT'), basemap_fields(), interface, by_name, repl)
    # Exécutable : la version modifiée (ELF non chiffré) remplace aussi EBOOT.BIN
    build_fixed(BOOT, boot_fields(), load_fixed('menus.json'), by_name, repl,
                targets=['/PSP_GAME/SYSDIR/BOOT.BIN', '/PSP_GAME/SYSDIR/EBOOT.BIN'])
    # Images (textures d'interface)
    import build_images
    for rel, data in build_images.build().items():
        for ip in by_name[os.path.basename(rel)]:
            repl[ip] = data
    # Vidéos sous-titrées, MENU_03 (NIVEAU FINI) et MENU_TEX (NIVEAU + !) tirés de l'ISO patché de l'équipe (12/04/2013)
    for path in sorted(glob.glob(os.path.join(ROOT, 'trad/equipe2013/*'))):
        for ip in by_name[os.path.basename(path)]:
            repl[ip] = open(path, 'rb').read()
    print(f'Écriture de {os.path.basename(DST_ISO)}...')
    iso_patch.patch(SRC_ISO, DST_ISO, repl)


if __name__ == '__main__':
    main()
