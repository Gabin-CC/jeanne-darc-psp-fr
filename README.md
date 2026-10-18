<p align="center"><img src="docs/banniere.png" alt="Jeanne d'Arc PSP — Traduction française" width="720"></p>

<p align="center">
  <a href="https://github.com/Gabin-CC/jeanne-darc-psp-fr/releases/latest"><img src="https://img.shields.io/github/v/release/Gabin-CC/jeanne-darc-psp-fr?label=t%C3%A9l%C3%A9charger&color=b8860b" alt="Dernière version"></a>
  <a href="https://github.com/Gabin-CC/jeanne-darc-psp-fr/releases"><img src="https://img.shields.io/github/downloads/Gabin-CC/jeanne-darc-psp-fr/total?label=t%C3%A9l%C3%A9chargements" alt="Téléchargements"></a>
  <img src="https://img.shields.io/badge/PPSSPP-compatible-2e7d32" alt="Compatible PPSSPP">
</p>

# Jeanne d'Arc (PSP) — Traduction française

**👉 [Télécharger le patch](https://github.com/Gabin-CC/jeanne-darc-psp-fr/releases/latest)** — instructions d'installation [plus bas](#installer-le-patch-joueurs).

Traduction amateur intégrale en français de **Jeanne d'Arc** (Level-5, PSP, 2007), à partir de la
version américaine. Le jeu n'est jamais sorti officiellement en français (la réédition PS4/PS5 de
2024 est en anglais et en japonais uniquement).

> *Fan translation of the PSP game Jeanne d'Arc into French. Apply the `.xdelta` patch from the
> Releases page to your own dump of the US version (ULUS-10261).*

## Ce qui est traduit

| | |
|---|---|
| Dialogues (toute l'histoire, colisée et stages annexes) | ✅ ~6 100 répliques |
| Objets, armes, armures, sorts, compétences et descriptions | ✅ |
| Menus, sauvegarde, options, aide textuelle | ✅ |
| Titres de chapitres, objectifs, noms de lieux, carte du monde | ✅ |
| Textures : écran titre, interface de combat, menus, carte du monde, bandeaux de lieux, cartons de chapitre | ✅ |
| Pages d'aide illustrées (`HELP/*.GIM`) | ⚠️ page « Combat » traduite, les autres en anglais |
| Vidéos | (pas de texte à traduire) |

Partis pris de traduction :
- noms historiques et géographiques sous leur forme française (Domrémy, Orléans, duc de Bourgogne, Henri VI…) ;
- les Français parlent un français correct, **les Anglais parlent avec un léger accent anglais** ;
- les tics de langage des personnages sont conservés (La Hire roule les r, Rufus remplace ses consonnes par des R, les nains zozotent…).

Le glossaire complet est dans [`trad/glossaire.md`](trad/glossaire.md).

## Aperçu

| Préparation de la bataille | Menu de combat |
|---|---|
| ![Placement des unités en français](docs/capture_placement.png) | ![Menu de combat en français](docs/capture_combat.png) |

Les textures elles aussi sont traduites — exemple avec une page d'aide (en haut l'original, en bas la version française) :

<p align="center"><img src="docs/aide_avant_apres.png" alt="Page d'aide avant / après traduction" width="640"></p>

## Installer le patch (joueurs)

1. Il vous faut **votre propre** image ISO de la version US (*Jeanne d'Arc*, ULUS-10261) :
   - MD5 attendu : `306f1eb4c983a555f3b548ad7c09386e`
2. Téléchargez `Jeanne_dArc_FR.xdelta` depuis la page **Releases** du dépôt.
3. Appliquez le patch avec l'un de ces outils :
   - en ligne, sans installation : [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/) ;
   - Windows : *xdelta UI* ou *Delta Patcher* ;
   - ligne de commande : `xdelta3 -d -s "Jeanne d'Arc (USA).iso" Jeanne_dArc_FR.xdelta "Jeanne d'Arc (FR).iso"`
4. Vérifiez le résultat — MD5 de l'ISO français : `ff0cbd643a58e71aa5dbb3f4fddacb2d` (v1.0.1).

Compatible **PPSSPP** et **PSP avec custom firmware** (l'exécutable est fourni déchiffré).

> ⚠️ Sur PPSSPP, ne chargez pas un *savestate* créé avec une autre version de l'ISO : il restaure
> la mémoire de l'ancienne version (textes et textures anglais). Les sauvegardes faites dans le jeu
> fonctionnent sans problème.

## Limites connues

- « LEVEL UP! », « STAGE CLEARED » et les bannières de compétences « Burning Aura » /
  « Unified Guard » restent en anglais : le jeu les compose lettre par lettre et aucun mot français
  ne correspond au même motif de lettres. « GAME OVER » est conservé (usage courant en français).
- La police système de la PSP n'a pas de tiret court : les traits d'union utilisent le caractère
  U+2012, le plus fin disponible.
- Seule la première page d'aide illustrée (« Combat ») est traduite ; les 34 autres restent en anglais.

## Reconstruire le patch depuis les sources

Prérequis : Python 3.10+, `xdelta3`, et **macOS** pour les textures (les images sont rendues avec les
polices système Optima, Georgia, Times New Roman et Helvetica — voir `tools/gimtext.py`).

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 1. Placer "Jeanne d'Arc (USA).iso" à la racine du dépôt, puis l'extraire
.venv/bin/python tools/iso_extract.py "Jeanne d'Arc (USA).iso" extract

# 1 bis. Vidéos sous-titrées de l'équipe PSP Traduction (non versionnées : contenu du jeu)
#        à partir de leurs quatre patchs alpha de 2013, voir tools/import_equipe2013.py
.venv/bin/python tools/import_equipe2013.py chemin/vers/patchs_2013

# 2. Vérifier les traductions puis construire "Jeanne d'Arc (FR).iso"
.venv/bin/python tools/check_trad.py
.venv/bin/python tools/build.py

# 3. Générer le patch
xdelta3 -e -9 -S none -s "Jeanne d'Arc (USA).iso" "Jeanne d'Arc (FR).iso" Jeanne_dArc_FR.xdelta   # -S none : compatible Rom Patcher JS
```

## Organisation

```
trad/
  dialogues/NNN.json   mémoire de traduction des dialogues (ordre de l'histoire)
                       {ctx: fichier source, max: largeur de ligne, who: locuteur, en, fr}
  logic.json           objets, sorts, compétences, ennemis (champs de taille fixe, max = octets)
  cartes.json          titres de chapitres, objectifs, noms d'unités
  menus.json           textes de l'exécutable (menus, sauvegarde…)
  interface.json       libellés d'interface et noms de lieux de la carte du monde
  images.json          textures retouchées (cadres, texte français, police)
  raven/               textures et pages d'aide de Raven (équipe PSP Traduction)
  equipe2013/          MENU_03, MENU_TEX et vidéos (*.PMF, non versionnées) de l'équipe PSP Traduction
  glossaire.md         noms, termes, tutoiement/vouvoiement, règles de style
  termes_logic.md      noms officiels des objets, sorts et compétences
tools/
  build.py             construit l'ISO français
  import_equipe2013.py récupère les vidéos sous-titrées depuis les patchs 2013 de l'équipe
  check_trad.py        vérifie longueurs, codes de contrôle, octets
  jda_event.py         format des scripts de dialogue (EVENT/ST*.BIN)
  jda_fixed.py         chaînes en champs de taille fixe
  iso_patch.py         réécriture de l'ISO + table FILEINFO.DAT du jeu
  gim.py               lecture/écriture des textures GIM de la PSP
  gimtext.py, gimbanner.py, gimwm.py, helppage.py, build_images.py   rendu du texte français dans les textures
  speakers.py          attribution des répliques aux personnages (lecture du bytecode)
  extract_*.py         extraction des textes depuis l'ISO
```

### Notes techniques

- Les dialogues sont dans `EVENT/ST*.BIN` : en-tête, table d'offsets relatifs, bytecode, puis bloc de
  texte Latin-1. Les caractères hors Latin-1 (œ, —, ‒) passent par des échappements `\uXXXX` que le
  moteur interprète.
- Le jeu lit ses fichiers par LBA via `USRDIR/DATA/FILEINFO.DAT` : les fichiers agrandis sont
  déplacés en fin d'image et la table est mise à jour. Les copies d'un même fichier dans les
  dossiers `ASxxxx/` sont toutes patchées.

## Contribuer

Les corrections sont les bienvenues (coquilles, tournures, débordements à l'écran) :

1. Modifiez le champ `fr` dans le fichier JSON concerné (ne touchez pas à `en`).
2. Respectez [`trad/glossaire.md`](trad/glossaire.md) et conservez les codes `\n`, `\f`, `%d`, `\uXXXX`.
3. Lancez `tools/check_trad.py` : il doit afficher 0 erreur.
4. Ouvrez une *pull request*, idéalement avec une capture d'écran.

Pour signaler un problème en jeu, ouvrez une *issue* avec une capture et le contexte (chapitre, scène).

## Licences et mentions légales

- Code (`tools/`) : licence [MIT](LICENSE).
- Traductions et fichiers de `trad/` : [CC BY 4.0](LICENSE-TRADUCTION.md).

*Jeanne d'Arc* est une marque et une œuvre de Level-5 Inc. et Sony Interactive Entertainment. Ce
projet amateur n'est ni affilié ni approuvé par eux. Aucune donnée du jeu (ISO, fichiers extraits)
n'est distribuée : il faut posséder le jeu. Les fichiers de traduction contiennent le texte anglais
d'origine à titre de référence pour les traducteurs.
