"""Remise en page des boîtes de dialogue (max=34) de trad/dialogues/, selon les règles validées en jeu :
- lignes remplies au maximum avec des mots entiers, 2 lignes par boîte ;
- un changement de boîte dans la VO => un changement de boîte dans la VF ;
- ailleurs, une phrase qui ne tient pas entière dans la place restante part dans la boîte suivante ;
- une phrase qui tient entière sur la 2e ligne y commence ;
- une phrase plus longue qu'une boîte continue dans la suivante, coupée après sa dernière virgule (, ; :) ;
- fin de phrase : . ! ? ... (jamais : ni ;).
Les bulles de combat (max=16) ne sont pas touchées.

Usage : python3 tools/mise_en_page.py [--apply]   (sans --apply : liste seulement le nombre de répliques à revoir)"""
import glob, json, os, re, sys

ADV = json.load(open(os.path.join(os.path.dirname(__file__), 'psp_font_widths.json'), encoding='utf-8'))
PX = 326  # même valeur que check_trad.PX_DIALOGUE
END = re.compile(r'([.!?…]|\.\.\.)["»)]?$|\\u2014$')

def px(t):
    t = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), re.sub(r'<[^>]*>', '', t))
    return sum(ADV.get(c, ADV['M']) for c in t.rstrip())

def tokens(text):
    out = []
    for w in text.split():
        if out and re.fullmatch(r'[!?:;»]+', w):
            out[-1] += ' ' + w  # la ponctuation reste collée au mot précédent
        else:
            out.append(w)
    return out

def lines_of(words):
    lines = []
    for w in words:
        if lines and px(lines[-1] + ' ' + w) <= PX:
            lines[-1] += ' ' + w
        else:
            lines.append(w)
    return lines

def layout(text):
    """Texte d'une « pause VO » -> liste de boîtes."""
    words = tokens(text)
    sentences, cur = [], []
    for w in words:
        cur.append(w)
        if END.search(w):
            sentences.append(cur); cur = []
    if cur:
        sentences.append(cur)
    boxes, box = [], []  # box : lignes (chaînes) de la boîte en cours
    for s in sentences:
        st = ' '.join(s)
        if box:
            if px(box[-1] + ' ' + st) <= PX:  # la phrase tient au bout de la ligne en cours
                box[-1] += ' ' + st
                continue
            if len(box) == 1 and px(st) <= PX:  # elle tient entière sur la 2e ligne : elle y commence
                box.append(st)
                continue
            cont = lines_of(tokens(' '.join(box)) + s)
            if len(cont) <= 2:  # sinon elle continue sur la 2e ligne
                box = cont
                continue
            boxes.append(box); box = []
        ls = lines_of(s)
        while len(ls) > 2:  # phrase plus longue qu'une boîte : elle continue dans la suivante,
            fit = 0         # en coupant après la dernière virgule qui tient dans la boîte
            while fit < len(s) and len(lines_of(s[:fit + 1])) <= 2:
                fit += 1
            cut = next((k for k in range(fit, 0, -1) if re.search(r'[,;:]$', s[k - 1])), fit)
            boxes.append(lines_of(s[:cut]))
            s = s[cut:]
            ls = lines_of(s)
        box = ls
    if box:
        boxes.append(box)
    return ['\n'.join(b) for b in boxes]

def segments(fr, en):
    """Découpe la VF en autant de segments que la VO a de boîtes, en gardant les coupures de Pinky
    qui suivent une fin de phrase en priorité."""
    k = en.count('\f')
    if k:
        # même nombre de phrases en VO et en VF : la pause tombe après la même phrase
        sent = lambda t: [x for x in re.split(r'(?<=[.!?…])["»)]?\s+', re.sub(r'\s+', ' ', t).strip()) if x]
        en_counts = [len(sent(b)) for b in en.split('\f')]
        fr_s = sent(fr.replace('\f', ' '))
        if len(fr_s) == sum(en_counts) and all(en_counts):
            out, i = [], 0
            for c in en_counts:
                out.append(' '.join(fr_s[i:i + c])); i += c
            return out
    cuts = [i for i, c in enumerate(fr) if c == '\f']
    if len(cuts) <= k:
        return fr.split('\f')
    end_cuts = [i for i in cuts if END.search(fr[:i].rstrip())]
    keep = (end_cuts + [i for i in cuts if i not in end_cuts])[:k]
    out, prev = [], 0
    for i in sorted(keep):
        out.append(fr[prev:i]); prev = i + 1
    out.append(fr[prev:])
    return out

def reflow(e):
    fr, en = e['fr'], e['en']
    if e.get('max') != 34 or not fr or fr.startswith('&') or '\x14' in fr:
        return None
    boxes = []
    for seg in segments(fr, en):
        boxes += layout(re.sub(r'\s+', ' ', seg).strip())
    new = '\f'.join(boxes)
    return new if new != fr else None

if __name__ == '__main__':
    apply = '--apply' in sys.argv
    n = 0; out = []
    for p in sorted(glob.glob('trad/dialogues/*.json')):
        raw = open(p, encoding='utf-8').read(); d = json.loads(raw); ch = False
        for e in d:
            new = reflow(e)
            if new:
                out.append((e['ctx'], e['en'], e['fr'], new)); n += 1
                if apply:
                    e['fr'] = new; ch = True
        if apply and ch:
            open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print(n, 'répliques', 'remises en page' if apply else 'à remettre en page', f'(largeur {PX} px)')
