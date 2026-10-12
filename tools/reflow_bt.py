"""Re-découpe les répliques de combat (max=16) où la traduction a ajouté des \\f
alors que l'anglais tient en une boîte : on recolle et on re-découpe à la largeur
de la plus longue ligne anglaise (+2), 2 lignes par boîte.

Usage : python3 tools/reflow_bt.py trad/dialogues/000.json [...]
"""
import json
import sys


def wrap(text, width):
    lines, cur = [], ''
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w) if cur else w
    if cur:
        lines.append(cur)
    return lines


def reflow(e):
    en, fr = e['en'], e['fr']
    if e.get('max') != 16 or not fr or '\f' in en or '\f' not in fr:
        return None
    width = max(16, max(len(l.rstrip()) for l in en.split('\n'))) + 2
    lines = wrap(' '.join(fr.replace('\f', ' ').replace('\n', ' ').split()), width)
    boxes = ['\n'.join(lines[i:i + 2]) for i in range(0, len(lines), 2)]
    new = '\f'.join(boxes)
    return new if new != fr else None


def main():
    for path in sys.argv[1:]:
        data = json.load(open(path, encoding='utf-8'))
        n = 0
        for e in data:
            new = reflow(e)
            if new:
                e['fr'] = new
                n += 1
        json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'{path}: {n} répliques re-découpées')


if __name__ == '__main__':
    main()
