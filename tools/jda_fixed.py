"""Chaînes dans des champs de taille fixe (LOGIC/LOGIC.PAC, MAP/*.DAT).

La capacité d'un champ = octets disponibles entre le début de la chaîne et le
prochain octet non nul, moins le terminateur. Pour éviter d'écraser un champ
numérique valant 0 dans un enregistrement donné, on prend le minimum sur
toute la "colonne" (même champ dans les autres enregistrements / fichiers).
"""
import re

from jda_event import encode

STR_RE = re.compile(rb'[\x20-\x7e\xa0-\xff\n]{2,}')


def find_strings(data: bytes):
    """[(pos, texte, gap)] ; gap = nb d'octets utilisables (terminateur exclu)."""
    out = []
    for m in STR_RE.finditer(data):
        p, s = m.start(), m.group()
        if p and data[p - 1] != 0:
            continue
        if not re.search(rb'[A-Za-z]{2}', s) or data[m.end():m.end() + 1] not in (b'\0', b''):
            continue
        if any(0x80 <= b < 0xa0 for b in data[m.end():m.end() + 1]):
            continue
        q = m.end()
        while q < len(data) and data[q] == 0:
            q += 1
        out.append((p, s.decode('latin-1'), q - p - 1))
    return out


def columns_by_stride(strings):
    """Regroupe les chaînes d'un même fichier en colonnes (pas d'enregistrement constant)."""
    pos = {p for p, _, _ in strings}
    col_of = {}
    for p, _, _ in strings:
        stride = None
        for s in range(16, 0x800, 2):
            if (p + s in pos and (p + 2 * s in pos or p - s in pos)) or (p - s in pos and p - 2 * s in pos):
                stride = s
                break
        if stride is None:
            col_of[p] = p
            continue
        b = p
        while b - stride in pos:
            b -= stride
        col_of[p] = (stride, b)
    return col_of


def fit(text: str, cap: int) -> bytes:
    """Encode en remplaçant œ/— par des équivalents courts si ça ne tient pas."""
    raw = encode(text)
    if len(raw) > cap:
        raw = encode(text.replace('œ', 'oe').replace('Œ', 'OE').replace('—', '-').replace('…', '...'))
    return raw


def apply(data: bytes, repl: dict) -> bytes:
    """repl : {pos: (bytes, capacité)} -> fichier modifié (taille identique)."""
    out = bytearray(data)
    for p, (raw, cap) in repl.items():
        assert len(raw) <= cap, (p, raw, cap)
        old_end = p
        while old_end < p + cap and out[old_end] != 0:
            old_end += 1
        out[p:old_end] = b'\0' * (old_end - p)
        out[p:p + len(raw)] = raw
    return bytes(out)
