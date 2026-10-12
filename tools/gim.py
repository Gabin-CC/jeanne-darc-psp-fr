"""Lecture / écriture des images GIM de la PSP (« MIG.00.1PSP »).

Blocs : 0x02 racine > 0x03 image > 0x04 pixels, 0x05 palette, 0xFF infos.
En-tête d'un bloc pixels/palette (relatif au début des données du bloc) :
  +0 u16 taille en-tête   +4 u16 format   +6 u16 ordre (1 = swizzlé)
  +8 u16 largeur  +10 hauteur  +12 bpp  +14 alignement pitch  +16 alignement hauteur
  +28 u32 début pixels   +32 u32 fin pixels
Formats : 0 RGBA5650, 1 RGBA5551, 2 RGBA4444, 3 RGBA8888, 4 index4, 5 index8.

Seule la première image (niveau 0, trame 0) est gérée, ce qui couvre les textures d'interface.
"""
import struct

from PIL import Image


def _blocks(data, start, end):
    pos = start
    while pos + 16 <= end:
        bid, size, nxt, doff = struct.unpack_from('<HxxIII', data, pos)
        if size == 0:
            break
        yield bid, pos, size, doff
        if bid in (0x02, 0x03):
            yield from _blocks(data, pos + doff, pos + size)
        pos += nxt if nxt else size


def _unswizzle(buf, wbytes, h):
    out = bytearray(len(buf))
    rowblocks = wbytes // 16
    for i in range(len(buf) // 16):
        blk, line = divmod(i, 8)
        by, bx = divmod(blk, rowblocks)
        y = by * 8 + line
        if y < h:
            o = y * wbytes + bx * 16
            out[o:o + 16] = buf[i * 16:i * 16 + 16]
    return bytes(out)


def _swizzle(buf, wbytes, h):
    out = bytearray(len(buf))
    rowblocks = wbytes // 16
    for i in range(len(buf) // 16):
        blk, line = divmod(i, 8)
        by, bx = divmod(blk, rowblocks)
        y = by * 8 + line
        if y < h:
            o = y * wbytes + bx * 16
            out[i * 16:i * 16 + 16] = buf[o:o + 16]
    return bytes(out)


def _decode_color(fmt, v):
    if fmt == 3:
        return (v & 0xff, v >> 8 & 0xff, v >> 16 & 0xff, v >> 24 & 0xff)
    if fmt == 2:
        return tuple(((v >> s) & 0xf) * 17 for s in (0, 4, 8, 12))
    if fmt == 1:
        return ((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31, 255 if v >> 15 else 0)
    return ((v & 31) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v >> 11 & 31) * 255 // 31, 255)


def _encode_color(fmt, c):
    r, g, b, a = c
    if fmt == 3:
        return r | g << 8 | b << 16 | a << 24
    if fmt == 2:
        return (r >> 4) | (g >> 4) << 4 | (b >> 4) << 8 | (a >> 4) << 12
    if fmt == 1:
        return (r >> 3) | (g >> 3) << 5 | (b >> 3) << 10 | (a >= 128) << 15
    return (r >> 3) | (g >> 2) << 5 | (b >> 3) << 11


class Gim:
    def __init__(self, data: bytes):
        assert data[:11] == b'MIG.00.1PSP', 'pas un GIM'
        self.data = bytearray(data)
        self.img = self.pal = None
        for bid, pos, size, doff in _blocks(data, 0x10, len(data)):
            if bid == 0x04 and self.img is None:
                self.img = pos + doff
            elif bid == 0x05 and self.pal is None:
                self.pal = pos + doff

    def _hdr(self, base):
        d = self.data
        fmt, order, w, h, bpp, palign, halign = struct.unpack_from('<HHHHHHH', d, base + 4)
        ps, pe = struct.unpack_from('<II', d, base + 28)
        return dict(fmt=fmt, order=order, w=w, h=h, bpp=bpp, palign=palign, halign=halign, ps=base + ps, pe=base + pe)

    def _geometry(self, hd):
        bpp = {0: 16, 1: 16, 2: 16, 3: 32, 4: 4, 5: 8, 6: 16, 7: 32}[hd['fmt']]
        wbytes = (hd['w'] * bpp + 7) // 8
        wbytes = (wbytes + hd['palign'] - 1) // hd['palign'] * hd['palign'] if hd['palign'] else wbytes
        h = (hd['h'] + hd['halign'] - 1) // hd['halign'] * hd['halign'] if hd['halign'] else hd['h']
        return bpp, wbytes, h

    def palette(self):
        if self.pal is None:
            return None
        hd = self._hdr(self.pal)
        size = 4 if hd['fmt'] == 3 else 2
        n = (hd['pe'] - hd['ps']) // size
        fmtc = '<I' if size == 4 else '<H'
        return [_decode_color(hd['fmt'], struct.unpack_from(fmtc, self.data, hd['ps'] + i * size)[0]) for i in range(n)]

    def info(self):
        return self._hdr(self.img)

    def _to_image_dxt(self, hd):
        """DXT1/3/5, variante PSP : dans chaque bloc les indices précèdent les couleurs."""
        w, h = hd['w'], hd['h']
        bw, bh = (w + 3) // 4, (h + 3) // 4
        bsize = 8 if hd['fmt'] == 8 else 16
        d = self.data
        base = hd['ps']
        im = Image.new('RGBA', (bw * 4, bh * 4))
        px = im.load()
        c565 = lambda v: ((v & 31) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v >> 11) * 255 // 31)
        for by in range(bh):
            for bx in range(bw):
                o = base + (by * bw + bx) * bsize
                if o + bsize > len(d):
                    continue
                co = o if bsize == 8 else o + 8  # en DXT3/5 la partie alpha suit la couleur
                idx, c0, c1 = struct.unpack_from('<IHH', d, co)
                a0, a1 = c565(c0), c565(c1)
                if c0 > c1 or bsize == 16:
                    pal = [a0 + (255,), a1 + (255,),
                           tuple((2 * a0[i] + a1[i]) // 3 for i in range(3)) + (255,),
                           tuple((a0[i] + 2 * a1[i]) // 3 for i in range(3)) + (255,)]
                else:
                    pal = [a0 + (255,), a1 + (255,), tuple((a0[i] + a1[i]) // 2 for i in range(3)) + (255,), (0, 0, 0, 0)]
                for i in range(16):
                    px[bx * 4 + i % 4, by * 4 + i // 4] = pal[(idx >> (2 * i)) & 3]
        return im.crop((0, 0, w, h))

    def to_image(self) -> Image.Image:
        hd = self._hdr(self.img)
        if hd['fmt'] in (8, 9, 10):
            return self._to_image_dxt(hd)
        bpp, wbytes, h = self._geometry(hd)
        raw = bytes(self.data[hd['ps']:hd['ps'] + wbytes * h])
        if hd['order'] == 1:
            raw = _unswizzle(raw, wbytes, h)
        w, H = hd['w'], hd['h']
        im = Image.new('RGBA', (w, H))
        px = im.load()
        if hd['fmt'] in (4, 5):
            pal = self.palette()
            for y in range(H):
                row = raw[y * wbytes:(y + 1) * wbytes]
                for x in range(w):
                    idx = (row[x >> 1] >> (4 * (x & 1))) & 0xf if bpp == 4 else row[x]
                    px[x, y] = pal[idx] if idx < len(pal) else (0, 0, 0, 0)
        else:
            size = bpp // 8
            fmtc = '<I' if size == 4 else '<H'
            for y in range(H):
                for x in range(w):
                    v = struct.unpack_from(fmtc, raw, y * wbytes + x * size)[0]
                    px[x, y] = _decode_color(hd['fmt'], v)
        return im

    def from_image(self, im: Image.Image) -> bytes:
        """Réencode `im` (même taille) dans le format d'origine ; palette recalculée si indexé."""
        hd = self._hdr(self.img)
        bpp, wbytes, h = self._geometry(hd)
        im = im.convert('RGBA')
        assert im.size == (hd['w'], hd['h'])
        raw = bytearray(wbytes * h)
        if hd['fmt'] in (4, 5):
            phd = self._hdr(self.pal)
            psize = 4 if phd['fmt'] == 3 else 2
            ncol = min((phd['pe'] - phd['ps']) // psize, 16 if bpp == 4 else 256)
            q = _quantize_rgba(im, ncol)
            pal, idxs = q
            for y in range(hd['h']):
                for x in range(hd['w']):
                    i = idxs[y * hd['w'] + x]
                    if bpp == 4:
                        raw[y * wbytes + (x >> 1)] |= i << (4 * (x & 1))
                    else:
                        raw[y * wbytes + x] = i
            fmtc = '<I' if psize == 4 else '<H'
            for i in range((phd['pe'] - phd['ps']) // psize):
                c = pal[i] if i < len(pal) else (0, 0, 0, 0)
                struct.pack_into(fmtc, self.data, phd['ps'] + i * psize, _encode_color(phd['fmt'], c))
        else:
            size = bpp // 8
            fmtc = '<I' if size == 4 else '<H'
            px = im.load()
            for y in range(hd['h']):
                for x in range(hd['w']):
                    struct.pack_into(fmtc, raw, y * wbytes + x * size, _encode_color(hd['fmt'], px[x, y]))
        if hd['order'] == 1:
            raw = _swizzle(bytes(raw), wbytes, h)
        self.data[hd['ps']:hd['ps'] + len(raw)] = raw
        return bytes(self.data)


def _quantize_rgba(im, ncol):
    """Quantification RGBA -> (palette [(r,g,b,a)], indices) en conservant l'alpha."""
    colors = list(im.getdata())
    uniq = list(dict.fromkeys(colors))
    if len(uniq) <= ncol:
        lut = {c: i for i, c in enumerate(uniq)}
        return uniq, [lut[c] for c in colors]
    # Quantification en espace RGBA via PIL (méthode FASTOCTREE qui gère l'alpha)
    q = im.quantize(colors=ncol, method=Image.Quantize.FASTOCTREE)
    flat = q.getpalette('RGBA') if hasattr(q, 'getpalette') else None
    if flat is None or len(flat) < 4 * ncol:
        flat = (flat or []) + [0] * (4 * ncol - len(flat or []))
    pal = [tuple(flat[i * 4:i * 4 + 4]) for i in range(ncol)]
    return pal, list(q.getdata())
