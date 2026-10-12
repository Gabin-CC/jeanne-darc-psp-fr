"""Lecture / reconstruction des fichiers de script EVENT/ST*.BIN de Jeanne d'Arc (PSP).

Format (little endian) :
  0x00  u32  offset de la table (toujours 0x40)
  0x04  u32  taille du bytecode
  0x08  u32  taille du bloc texte (alignée sur 0x10)
  0x0C  u32  signature 0x5C7EE8
  0x10  u32  nombre de chaînes
  0x14  u32  nombre d'entrées de la table
  0x18  u32  taille de la table (octets)
  0x40       table d'offsets u32, relatifs au début du bloc texte
  ...        bytecode
  ...        bloc texte : chaînes terminées par \\0, alignées sur 2 octets

Le bloc texte est découpé en "slots" aux frontières données par la table.
Un slot non traduit est recopié à l'identique (certains contiennent du binaire,
ex. les références de locuteur `&[...]`).
"""
import struct

ENC = 'latin-1'


class EventFile:
    def __init__(self, data: bytes):
        self.data = data
        h = struct.unpack_from('<8I', data, 0)
        assert h[0] == 0x40, 'en-tête inattendu'
        self.h = list(h)
        self.n = h[5]
        self.offs = list(struct.unpack_from('<%dI' % self.n, data, 0x40))
        self.code_start = 0x40 + h[6]
        self.text_start = self.code_start + h[1]
        self.text_size = h[2]
        assert self.text_start + self.text_size == len(data), 'taille incohérente'
        text = data[self.text_start:]
        bounds = sorted(set(o for o in self.offs if o <= self.text_size) | {0, self.text_size})
        self.slots = {}  # offset -> bytes bruts du slot
        for a, b in zip(bounds, bounds[1:]):
            self.slots[a] = text[a:b]
        self.bounds = bounds

    def strings(self):
        """Renvoie [(index_table, texte)] pour les slots traduisibles, dans l'ordre du bloc."""
        first_idx = {}
        for i, o in enumerate(self.offs):
            first_idx.setdefault(o, i)
        out = []
        for o in self.bounds[:-1]:
            s = slot_text(self.slots[o])
            if s is not None and o in first_idx:
                out.append((first_idx[o], s))
        return out

    def build(self, tr: dict) -> bytes:
        """tr : {index_table: nouveau_texte}. Renvoie le fichier reconstruit."""
        by_off = {self.offs[i]: t for i, t in tr.items()}
        new_text = bytearray()
        remap = {}
        for o in self.bounds[:-1]:
            remap[o] = len(new_text)
            if o in by_off:
                new_text += encode(by_off[o]) + b'\0'
                if len(new_text) % 2:
                    new_text += b'\0'
            else:
                new_text += self.slots[o]
        while len(new_text) % 0x10:
            new_text += b'\0'
        remap[self.text_size] = len(new_text)
        h = self.h[:]
        h[2] = len(new_text)
        out = bytearray(self.data[:self.text_start])
        struct.pack_into('<8I', out, 0, *h)
        struct.pack_into('<%dI' % self.n, out, 0x40, *[remap[o] if o in remap else o for o in self.offs])
        return bytes(out + new_text)


def slot_text(slot: bytes):
    """Texte d'un slot s'il est traduisible (latin-1 imprimable + \\n + \\f), sinon None."""
    s = slot.rstrip(b'\0')
    if not s or b'\0' in s or s.startswith(b'&['):
        return None
    if any(b < 0x20 and b not in (0x0a, 0x0c, 0x14) for b in s):  # 0x14 : réplique coupée
        return None
    if any(0x80 <= b < 0xa0 for b in s):  # Shift-JIS (stages de debug japonais)
        return None
    if not any(0x41 <= b <= 0x7a for b in s):
        return None
    if s.startswith(b'__'):  # identifiant interne (__EventDefaultValue)
        return None
    return s.decode(ENC)


# Caractères hors Latin-1 qu'on rencontre en français : on passe par l'échappement \\uXXXX
# que le moteur comprend déjà (la VO utilise \\u2014).
def encode(text: str) -> bytes:
    out = []
    for ch in text:
        if ord(ch) < 0x100:
            out.append(ch)
        else:
            out.append('\\u%04x' % ord(ch))
    return ''.join(out).encode(ENC)
