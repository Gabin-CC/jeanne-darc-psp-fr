"""Fusionne la traduction de l'équipe PSP Traduction (trad/pinky/dialogues.json, produit par
import_pinky.py) dans trad/dialogues/*.json.

- Leur texte remplace le nôtre (champ "src": "pinky") ; le nôtre reste là où ils n'ont rien ("src": "ia").
- Nettoyage minimal : espaces en fin de ligne, espaces doublés.
- Une boîte n'est ré-enroulée que si une de ses lignes dépasse la largeur (dialogues : 38,
  bulles de combat : 20) ; on ajoute alors des boîtes (\\f) si 2 lignes ne suffisent pas.
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from reflow_lines import wrap, vlen

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WIDTH = {34: 38, 16: 20}


def clean(t):
    t = '\n'.join(re.sub(r' {2,}', ' ', l).rstrip() for l in t.split('\n'))
    return '\f'.join(b.strip('\n') for b in t.split('\f'))


def fit(t, width, en):
    """Ré-enroule les boîtes trop larges (2 lignes max par boîte, 3 si l'anglais en a 3)."""
    max_lines = max(2, max(len(b.split('\n')) for b in en.split('\f')))
    out = []
    for box in t.split('\f'):
        if all(vlen(l) <= width for l in box.split('\n')):
            out.append(box)
            continue
        lines = wrap(box.replace('\n', ' ').split(), width)
        out += ['\n'.join(lines[i:i + max_lines]) for i in range(0, len(lines), max_lines)]
    return '\f'.join(out)


def main():
    pinky = json.load(open(os.path.join(ROOT, 'trad/pinky/dialogues.json'), encoding='utf-8'))
    n_p = n_ia = n_fit = 0
    for path in sorted(glob.glob(os.path.join(ROOT, 'trad/dialogues/*.json'))):
        data = json.load(open(path, encoding='utf-8'))
        out = []
        for e in data:
            e = dict(e)
            if e['en'] in pinky and pinky[e['en']]['fr'].strip():
                fr = clean(pinky[e['en']]['fr'])
                if e['en'].startswith('&') and not fr.startswith('&'):
                    fr = '&' + fr
                width = WIDTH.get(e['max'], 38)
                fitted = fit(fr, width, e['en']) if not e['en'].startswith('&') else fr
                n_fit += fitted != fr
                e['fr'], e['src'] = fitted, 'pinky'
                n_p += 1
            else:
                e['src'] = 'ia'
                n_ia += 1
            out.append(e)
        json.dump(out, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{n_p} répliques de l\'équipe PSP Traduction ({n_fit} ré-enroulées), {n_ia} de la traduction IA')


if __name__ == '__main__':
    main()
