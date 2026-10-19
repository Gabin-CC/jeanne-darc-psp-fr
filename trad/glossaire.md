# Glossaire et règles — Traduction FR de Jeanne d'Arc (PSP)

Source : version US anglaise. Contexte : guerre de Cent Ans revisitée en fantasy
(démons, magie, races non humaines). Ton : épique mais naturel, dialogues vivants,
pas de langue trop moderne ni d'anglicismes. Le jeu se passe en France : les noms
historiques et géographiques reprennent leur forme française.

## Règles techniques (OBLIGATOIRES)

- Garder **exactement** les codes : `\n` (saut de ligne), `\f` (nouvelle boîte),
  `%d`, `%s`, `\u2122` et autres échappements `\uXXXX` littéraux (les recopier tels quels).
- Une chaîne qui commence par `&` est un **nom de locuteur** : la traduction commence aussi par `&`.
- Dialogues (`max` = 34) : **36 caractères max par ligne**, 2 lignes max par boîte
  (3 seulement si l'anglais en a 3). Couper avec `\n` à un endroit naturel ; utiliser `\f`
  pour ouvrir une nouvelle boîte si le texte est trop long.
- Bulles de combat (`max` = 16) : **18 caractères max par ligne**, 2 lignes max. Faire court.
- Champs fixes (`logic.json`, `cartes.json`, `menus.json`) : `max` = nombre d'**octets**
  maximum (1 lettre accentuée = 1 octet ; `œ` et `—` = 6 octets, évite-les dans ces fichiers).
  C'est une limite dure : au-delà, la chaîne n'est pas insérée. Abréger si nécessaire.
- Garder le même nombre d'éléments dans les listes séparées par `\n` (menus).
- Laisser `fr` **vide** pour ce qui n'est pas du texte joueur : debug, noms de fichiers,
  outils de dev, déchets binaires (ex. `\nnK`), texte japonais.
- Les guillemets : « texte » (avec espaces). Points de suspension : `...`.
- Ponctuation française : espace avant `?`, `!`, `:`, `;` (espace normale).
- Ne jamais traduire un nom propre de la colonne « garder ».

## Tutoiement / vouvoiement

- Jeanne, Liane, Roger, Jacques (père de Jeanne, « Papa »), les gens de Domrémy
  entre eux : **tu**.
- Les compagnons d'armes proches finissent par se tutoyer (La Hire ↔ Jeanne : tu,
  Jeanne ↔ Roger : tu, Colet ↔ Jeanne : tu). Gilles, Richemont, nobles : **vous**.
- Tout le monde vouvoie Charles VII ; Charles vouvoie Jeanne.
- Soldats → Jeanne : **vous**. Jeanne → soldats (ses troupes) : **vous** (pluriel).
- Démons et ennemis → héros : tu méprisant.

## Personnages (garder tel quel sauf indication)

| Anglais | Français |
|---|---|
| Jeanne, Liane, Roger, Jacques, La Hire, Gilles, Colet, Cuisses, Marcel, Jean, Richard, Richemont, Bertrand, Georges, Pierre, René, Claire, Beatrix, Bartolomeo, Dominic, Rufus, Alain, Mawra, Rose, Blaze, Luther, Talbot, Glasdale, Isabeau, Aldric, William, Warren | identiques |
| Charles VII / Charles | Charles VII / Charles |
| Henry / Henry VI | Henry / Henry VI |
| Captain Robert | le capitaine Robert |
| Duke of Bedford / Burgundy / Lorraine | duc de Bedford / de Bourgogne / de Lorraine |
| the Dauphin | le Dauphin |
| the Maid / La Pucelle | la Pucelle |
| Jeannette | Jeannette |
| Gilvaroth, Avaritia, Ira, Luxuria, Superbia | identiques |
| the Fiend | le Malin |
| Noble in Black | le Noble en noir |
| Lady Bandit / Lady Elf | la Bandite / la Dame elfe |
| Magician Girl | la Petite magicienne |
| Raven | Corbeau |
| Toad | Crapaud |
| Slinker | le Rôdeur |
| Elder / Mayor / Physician / Gaoler | l'Ancien / le Maire / le Médecin / le Geôlier |
| Girl's Voice / Man's Voice / Woman's Voice | Voix de fille / Voix d'homme / Voix de femme |

## Peuples, classes, unités

| Anglais | Français |
|---|---|
| English / Englishman / the English | anglais / Anglais / les Anglais |
| French (Soldier) | (soldat) français |
| Burgundians | les Bourguignons |
| Therion / Therions / Therion Cub / Grunt | Thérion / Thérions / Petit thérion / Thérion guerrier |
| Beast Warrior | Guerrier-bête |
| Orc / Orc Knight / Phantom Orc | Orque / Chevalier orque / Orque fantôme |
| Dark Elf / Elf | Elfe noir / Elfe |
| Dwarf / Dwarf Doyen | Nain / Doyen nain |
| Necromancer / Mage / Lich | Nécromancien / Mage / Liche |
| Lizardman / Gargoyle / Ogre / Cyclops / Troll / Golem / Ghost / Demon | Homme-lézard / Gargouille / Ogre / Cyclope / Troll / Golem / Spectre / Démon |
| Swordmaster / Militiaman / Sellsword / Brigand / Thief | Maître d'armes / Milicien / Mercenaire / Brigand / Voleur |
| Knight / Paladin / Archer | Chevalier / Paladin / Archer |
| Reapers | les Faucheurs |

## Lieux

Domrémy, Vaucouleurs, Chinon, Orléans, Reims, Paris, Rouen, Troyes, Châlons, Neufchâteau,
Compiègne, Clairoix, Patay, Nancy, la Loire, la Charité → **identiques (orthographe française)**.
Brittany → la Bretagne ; Burgundy → la Bourgogne ; England → l'Angleterre ;
Les Tourelles, Les Augustins → les Tourelles, les Augustins ;
Alrond Wood → le bois d'Alrond ; Gwygone Mines → les mines de Gwygone ;
Soir Valley → la vallée de Soir ; Parith, Moutier → identiques ; The Quarry → la Carrière.

## Termes de jeu

| Anglais | Français |
|---|---|
| HP / MP | PV / PM |
| Attack / Defense / Magic Attack / Magic Defense | Attaque / Défense / Attaque mag. / Défense mag. |
| Move / Range | Déplacement / Portée |
| G (argent) | G |
| Skill / Skill Stone / Bind Skills | Compétence / Pierre de compétence / Lier les compétences |
| Turn / Phase | Tour / Phase |
| Quicksave | Sauvegarde rapide |
| Transform / Revert | Transformation / Retour |
| Armlet (le bracelet de Jeanne) | le Bracelet |
| Gem of X | Gemme de X |
| Suit of X | Armure de X |
| Anime Theatre | Théâtre animé |
| Memory Stick™ | Memory Stick\u2122 (recopier l'échappement tel quel) |
| Burn / Freeze / Poison / Stun / Paralysis / Sleep / Marked | Brûlure / Gel / Poison / Étourdi / Paralysie / Sommeil / Marqué |
| Sire / Your Highness / Your Grace / Milord | Sire / Votre Altesse / Votre Grâce / Monseigneur |
| God / Heaven | Dieu / le Ciel |

Les noms d'objets, d'armes, de sorts et de compétences sont fixés par `trad/logic.json` :
dans les dialogues, réutiliser **exactement** la traduction qui s'y trouve.

## Références complémentaires

- `trad/termes_logic.md` : noms d'objets, armes, sorts, compétences, ennemis (référence obligatoire).
- `trad/cartes.json` : titres de chapitres, noms d'unités et objectifs déjà traduits.
- Wyvern → wyverne. Qrow → Qrow. sol / luna / stella (éléments) → identiques.
- Durendal → Durandal. Armlet → Bracelet.

## Dialogues de l'équipe PSP Traduction

- Les dialogues sont la traduction de Pinky, reprise **telle quelle** : pas d'accent anglais
  ajouté (la règle d'accent de la v1 est abandonnée), seules l'orthographe et les contre-sens validés par
  Pinky ont été corrigés.
- Le vocabulaire des objets, menus et cartes est aligné sur le leur (voir `termes_logic.md`).

## Tics de langage (indépendants de la nationalité)


- **Georges** : zézaie — s/ch/j → z (« Précizément », « Z'ai touzours voulu »).
- **La Hire** : r roulés (« Parrrdonne »), parle de lui à la 3e personne, tutoie tout le monde, appelle Jeanne « Général ».
- **Rufus** (guerrier-bête) : consonnes initiales → « R » (« Rerci », « Ron nom est Rufus »), « Ouaf ».
- **Henry VI** : « Nous » royal.
- **Rose** : « mes chéris ! » (tic « loves! »).
- Talbot tutoie Jeanne (« petite »), elle le vouvoie ; Gilles vouvoie La Hire ; Roger et Gilles se vouvoient.
- frogs (insulte anglaise) → bouffeurs de grenouilles ; harlot/wench → gueuse ; Savior → salvatrice ;
  Young/Aging Noble → Jeune noble / Vieux noble ; English Army → Armée anglaise ; Lady Fortune → Dame Fortune.
