"""Recompose les lignes des boîtes de dialogue pour utiliser moins de lignes quand c'est possible.

Pour chaque boîte (séparée par \\f), le texte est ré-enroulé à la largeur max ; on garde la
nouvelle version seulement si elle compte moins de lignes. Largeur : 34 caractères pour les
dialogues (max=34), max(16, plus longue ligne anglaise) pour les bulles de combat.

Usage : python3 tools/reflow_lines.py [--dry] trad/dialogues/*.json
"""
import json
import re
import sys

ESC = re.compile(r'\\u[0-9a-fA-F]{4}')


def vlen(s):
    """Longueur affichée (un échappement \\uXXXX compte pour 1 caractère)."""
    return len(ESC.sub('x', s))


def wrap(words, width):
    lines, cur = [], ''
    for w in words:
        cand = (cur + ' ' + w) if cur else w
        if cur and vlen(cand) > width:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def reflow_entry(e):
    fr, en = e['fr'], e['en']
    if not fr or fr.startswith('&') or '\x14' in fr:
        return None
    if e.get('max') == 16:
        width = max(16, max(vlen(l.rstrip()) for l in en.replace('\f', '\n').split('\n')))
    else:
        width = 34
    boxes = []
    changed = False
    for box in fr.split('\f'):
        lines = box.split('\n')
        words = ' '.join(l.strip() for l in lines).split()
        new = wrap(words, width)
        if len(new) < len([l for l in lines if l.strip()]) and all(vlen(l) <= width for l in new):
            boxes.append('\n'.join(new))
            changed = True
        else:
            boxes.append(box)
    return '\f'.join(boxes) if changed else None


def main():
    dry = '--dry' in sys.argv
    total = 0
    for path in [a for a in sys.argv[1:] if not a.startswith('--')]:
        data = json.load(open(path, encoding='utf-8'))
        n = 0
        for e in data:
            new = reflow_entry(e)
            if new:
                if dry and n < 3:
                    print(f'  {e["fr"]!r}\n   -> {new!r}')
                if not dry:
                    e['fr'] = new
                n += 1
        if not dry:
            json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        total += n
    print(f'{total} répliques recomposées')


if __name__ == '__main__':
    main()
