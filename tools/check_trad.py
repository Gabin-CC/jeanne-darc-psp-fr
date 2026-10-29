"""Vérifie des fichiers de traduction. Usage : python3 tools/check_trad.py trad/dialogues/003.json [...]

Sans argument : vérifie tout trad/. Code de sortie 1 s'il y a des erreurs.
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from jda_fixed import fit

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Avance (px) de chaque caractère dans la police du jeu (flash0/font/ltn5.pgf, serif gras, lue via PPSSPP)
ADV = json.load(open(os.path.join(os.path.dirname(__file__), 'psp_font_widths.json'), encoding='utf-8'))
PX_DIALOGUE = 320  # mesuré en jeu (~328 px, marge pour les arrondis) : au-delà, le jeu coupe la ligne en plein mot
PX_BULLE = 200  # bulle de combat, largeur fixe (~205 px) : au-delà, le texte déborde
CODES = re.compile(r'%[0-9.]*[dsxf]|\\u[0-9a-fA-F]{4}')


def trad_files():
    """Fichiers de traduction : dialogues + chaînes à taille fixe (objets, cartes, interface, menus)."""
    return (sorted(glob.glob(os.path.join(ROOT, 'trad/dialogues/*.json'))) +
            [os.path.join(ROOT, 'trad', n) for n in ('logic.json', 'cartes.json', 'interface.json', 'menus.json')])


def check_entry(e, fixed):
    err = []
    en, fr = e['en'], e['fr']
    if fr == '':
        return err
    if en.startswith('&') != fr.startswith('&'):
        err.append('préfixe & incohérent')
    fmt = lambda t: sorted(c for c in CODES.findall(t) if c.startswith('%'))  # %d/%s obligatoires
    if fmt(en) != fmt(fr):
        err.append(f'codes différents : {CODES.findall(en)} -> {CODES.findall(fr)}')
    if fixed:
        n = len(fit(fr, e['max']))
        if n > e['max']:
            err.append(f'trop long : {n} octets > {e["max"]}')
        if '\n' in en and en.count('\n') != fr.count('\n') and re.fullmatch(r'[^\n]{1,24}(\n[^\n]{0,24})+\n?', en):
            err.append(f'liste de menu : {en.count(chr(10))} sauts de ligne attendus, {fr.count(chr(10))} trouvés')
        try:
            fr.encode('latin-1') if not re.search('[œŒ—…]', fr) else None
        except UnicodeEncodeError as x:
            err.append(f'caractère non latin-1 : {x.object[x.start]!r}')
    else:
        px = lambda t: sum(ADV.get(c, ADV['M']) for c in re.sub(
            r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), re.sub(r'<[^>]*>', '', t)).rstrip())
        nb_en = max(len(b.split('\n')) for b in en.split('\f'))
        for box in fr.split('\f'):
            lines = box.split('\n')
            if len(lines) > max(nb_en, 2):
                err.append(f'{len(lines)} lignes dans une boîte : {box!r}')
            for l in lines:
                if e.get('max') == 34:  # boîte de dialogue : largeur en pixels
                    if px(l) > PX_DIALOGUE:
                        err.append(f'ligne trop large ({px(l):.0f}>{PX_DIALOGUE} px) : {l!r}')
                elif px(l) > PX_BULLE and re.search(r' (?![!?:;»])', l.strip()):  # un mot seul ne peut pas être coupé
                    err.append(f'ligne trop large ({px(l):.0f}>{PX_BULLE} px) : {l!r}')
    return err


def check_file(path):
    fixed = 'dialogues' not in path
    try:
        data = json.load(open(path, encoding='utf-8'))
    except Exception as x:
        print(f'{path}: JSON INVALIDE : {x}')
        return 1, 0, 0
    n_err = done = 0
    for e in data:
        if set(e) < {'en', 'fr'}:
            print(f'{path}: entrée mal formée {e}')
            n_err += 1
            continue
        done += e['fr'] != ''
        for msg in check_entry(e, fixed):
            print(f'{path}: [{e["en"][:40]!r}] {msg}')
            n_err += 1
    return n_err, done, len(data)


def main():
    paths = sys.argv[1:] or trad_files()
    tot_err = tot_done = tot = 0
    for p in paths:
        e, d, n = check_file(p)
        tot_err += e
        tot_done += d
        tot += n
    print(f'{tot_done}/{tot} traduites, {tot_err} erreur(s)')
    sys.exit(1 if tot_err else 0)


if __name__ == '__main__':
    main()
