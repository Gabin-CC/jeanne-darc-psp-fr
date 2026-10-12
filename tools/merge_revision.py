"""Fusionne trad/revision/*.json dans trad/dialogues/ : chaque entrée {lot, i, en, fr}
dont `fr` est non vide remplace la traduction de la réplique (lot, i).

Usage : python3 tools/merge_revision.py trad/revision/colet.json [...]
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def main():
    lots = {}
    n = 0
    for path in sys.argv[1:]:
        for r in json.load(open(path, encoding='utf-8')):
            if not r['fr'].strip():
                continue
            if r['lot'] not in lots:
                lots[r['lot']] = json.load(open(os.path.join(ROOT, 'trad/dialogues/%s.json' % r['lot']), encoding='utf-8'))
            e = lots[r['lot']][r['i']]
            assert e['en'] == r['en'], (path, r['lot'], r['i'])
            e['fr'] = r['fr']
            n += 1
    for lot, data in lots.items():
        json.dump(data, open(os.path.join(ROOT, 'trad/dialogues/%s.json' % lot), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
    print(f'{n} répliques mises à jour dans {len(lots)} lots')


if __name__ == '__main__':
    main()
