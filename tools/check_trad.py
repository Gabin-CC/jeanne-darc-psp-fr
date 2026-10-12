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
CODES = re.compile(r'%[0-9.]*[dsxf]|\\u[0-9a-fA-F]{4}')


def check_entry(e, fixed):
    err = []
    en, fr = e['en'], e['fr']
    if not fr.strip():
        return err
    if en.startswith('&') != fr.startswith('&'):
        err.append('préfixe & incohérent')
    if sorted(CODES.findall(en)) != sorted(CODES.findall(fr)):
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
        vlen = lambda t: len(re.sub(r'\\u[0-9a-fA-F]{4}', 'x', t.rstrip()))
        en_longest = max(vlen(l) for l in en.replace('\f', '\n').split('\n'))
        lim = max(e.get('max') or 34, en_longest) + 2
        nb_en = max(len(b.split('\n')) for b in en.split('\f'))
        for box in fr.split('\f'):
            lines = box.split('\n')
            if len(lines) > max(nb_en, 2):
                err.append(f'{len(lines)} lignes dans une boîte : {box!r}')
            for l in lines:
                if vlen(l) > lim:
                    err.append(f'ligne trop longue ({vlen(l)}>{lim}) : {l!r}')
    return err


def check_file(path):
    fixed = 'dialogues' not in path and '/revision/' not in path
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
        done += bool(e['fr'].strip())
        for msg in check_entry(e, fixed):
            print(f'{path}: [{e["en"][:40]!r}] {msg}')
            n_err += 1
    return n_err, done, len(data)


def main():
    paths = sys.argv[1:] or sorted(p for p in glob.glob(os.path.join(ROOT, 'trad/**/*.json'), recursive=True)
                                   if '/revision/' not in p and not p.endswith('images.json'))
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
