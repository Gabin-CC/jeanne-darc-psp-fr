"""Récupère les vidéos sous-titrées de l'équipe PSP Traduction depuis leurs patchs alpha de 2013.

Les vidéos (≈ 245 Mo, contenu du jeu) ne sont pas versionnées : on les régénère à partir des quatre
patchs xdelta de l'équipe, qui s'enchaînent (chacun s'applique au résultat du précédent) :
    patch-alpha-07-04-13.xdelta    ISO US -> 07/04
    patch-alpha-08-04-13.xdelta    07/04  -> 08/04
    patch-alpha-08-04-13-2.xdelta  08/04  -> 08/04 (2)
    patch-alpha-12-04-13.xdelta    -> 12/04
Les archives .rar de l'équipe s'ouvrent avec bsdtar (macOS) : `bsdtar -xf JDA-12-04-13.rar`.

Usage : python3 tools/import_equipe2013.py DOSSIER_DES_PATCHS
  -> écrit trad/equipe2013/*.PMF (les vidéos modifiées par l'équipe), lues ensuite par build.py.
Prérequis : xdelta3, et "Jeanne d'Arc (USA).iso" à la racine du dépôt.
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from iso_patch import walk, SECTOR

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_ISO = os.path.join(ROOT, "Jeanne d'Arc (USA).iso")
OUT = os.path.join(ROOT, 'trad/equipe2013')
CHAIN = ['patch-alpha-07-04-13.xdelta', 'patch-alpha-08-04-13.xdelta',
         'patch-alpha-08-04-13-2.xdelta', 'patch-alpha-12-04-13.xdelta']


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    patches = [os.path.join(sys.argv[1], n) for n in CHAIN]
    missing = [p for p in patches if not os.path.exists(p)]
    if missing:
        sys.exit('patch(s) introuvable(s) : ' + ', '.join(missing))
    with tempfile.TemporaryDirectory() as tmp:
        src = SRC_ISO
        for i, p in enumerate(patches):
            dst = os.path.join(tmp, f'{i}.iso')
            print(f'Application de {os.path.basename(p)}...')
            subprocess.run(['xdelta3', '-d', '-f', '-s', src, p, dst], check=True)
            if src != SRC_ISO:
                os.remove(src)  # une seule image intermédiaire à la fois (≈ 1 Go chacune)
            src = dst
        os.makedirs(OUT, exist_ok=True)
        n = 0
        with open(src, 'rb') as f, open(SRC_ISO, 'rb') as fu:
            team, us = walk(f), walk(fu)
            for path, (_, lba, size) in sorted(team.items()):
                if not path.endswith('.PMF'):
                    continue
                f.seek(lba * SECTOR)
                data = f.read(size)
                fu.seek(us[path][1] * SECTOR)
                if data != fu.read(us[path][2]):
                    open(os.path.join(OUT, os.path.basename(path)), 'wb').write(data)
                    n += 1
    print(f'{n} vidéos écrites dans trad/equipe2013/')


if __name__ == '__main__':
    main()
