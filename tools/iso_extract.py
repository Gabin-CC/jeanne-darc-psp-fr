"""Extrait tout le contenu d'un ISO PSP (ISO9660) vers un dossier."""
import os, sys, pycdlib

iso_path, out = sys.argv[1], sys.argv[2]
iso = pycdlib.PyCdlib()
iso.open(iso_path)
for root, dirs, files in iso.walk(iso_path='/'):
    for f in files:
        src = (root.rstrip('/') + '/' + f)
        name = f.split(';')[0]
        dst = os.path.join(out, root.lstrip('/'), name)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        iso.get_file_from_iso(dst, iso_path=src)
        rec = iso.get_record(iso_path=src)
        print(f"{rec.extent_location():8d} {rec.get_data_length():11d} {src.split(';')[0]}")
iso.close()
