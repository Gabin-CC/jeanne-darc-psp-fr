"""Patch d'un ISO PSP : remplace des fichiers, en place s'ils tiennent dans leurs
secteurs, sinon en les déplaçant en fin d'image.

Met à jour : enregistrement de répertoire ISO9660 (LBA + taille),
USRDIR/DATA/FILEINFO.DAT (table nom/taille/LBA utilisée par le jeu)
et la taille du volume dans le PVD.
"""
import shutil
import struct

SECTOR = 2048
FILEINFO = '/PSP_GAME/USRDIR/DATA/FILEINFO.DAT'


def walk(f):
    """Renvoie {chemin: (offset_enregistrement, lba, taille)} pour tous les fichiers."""
    f.seek(16 * SECTOR)
    pvd = f.read(SECTOR)
    root = pvd[156:156 + 34]
    out = {}

    def rec_dir(lba, size, path):
        f.seek(lba * SECTOR)
        data = f.read(size)
        pos = 0
        while pos < len(data):
            ln = data[pos]
            if ln == 0:  # fin de secteur
                pos = (pos // SECTOR + 1) * SECTOR
                continue
            r = data[pos:pos + ln]
            e_lba, e_size = struct.unpack_from('<I', r, 2)[0], struct.unpack_from('<I', r, 10)[0]
            flags, nlen = r[25], r[32]
            name = r[33:33 + nlen]
            if name not in (b'\0', b'\1'):
                name = name.decode('ascii').split(';')[0]
                p = path + '/' + name
                if flags & 2:
                    rec_dir(e_lba, e_size, p)
                else:
                    out[p] = (lba * SECTOR + pos, e_lba, e_size)
            pos += ln

    rec_dir(struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0], '')
    return out


def sectors(n):
    return (n + SECTOR - 1) // SECTOR


def patch(src_iso, dst_iso, replacements, log=print):
    """replacements : {chemin_iso: bytes}."""
    if src_iso != dst_iso:
        shutil.copyfile(src_iso, dst_iso)
    with open(dst_iso, 'r+b') as f:
        files = walk(f)
        f.seek(0, 2)
        end_lba = sectors(f.tell())
        fi_rec, fi_lba, fi_size = files[FILEINFO]
        f.seek(fi_lba * SECTOR)
        fileinfo = bytearray(f.read(fi_size))
        fi_by_lba = {}
        for pos in range(0x950, len(fileinfo), 0x14):
            fi_by_lba.setdefault(struct.unpack_from('<I', fileinfo, pos + 0x10)[0], []).append(pos)

        moved = 0
        for path, data in sorted(replacements.items()):
            rec, lba, size = files[path]
            if sectors(len(data)) <= sectors(size):
                new_lba = lba
            else:
                new_lba = end_lba
                end_lba += sectors(len(data))
                moved += 1
            f.seek(new_lba * SECTOR)
            f.write(data + b'\0' * (sectors(len(data)) * SECTOR - len(data)))
            f.seek(rec + 2)
            f.write(struct.pack('<I', new_lba) + struct.pack('>I', new_lba)
                    + struct.pack('<I', len(data)) + struct.pack('>I', len(data)))
            for pos in fi_by_lba.get(lba, []):
                struct.pack_into('<II', fileinfo, pos + 0x0C, len(data), new_lba)
            if lba not in fi_by_lba and not path.startswith('/PSP_GAME/SYSDIR'):
                log('  ! absent de FILEINFO : ' + path)

        f.seek(fi_lba * SECTOR)
        f.write(fileinfo)
        f.seek(16 * SECTOR + 80)
        f.write(struct.pack('<I', end_lba) + struct.pack('>I', end_lba))
        f.truncate(end_lba * SECTOR)
    log(f'{len(replacements)} fichiers remplacés, {moved} déplacés en fin d\'image')
