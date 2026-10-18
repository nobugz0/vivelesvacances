# Marine la maline : passation du prototype (18/10/2026)

Branche `proto`. La branche `main` contient uniquement la version en ligne (index.html construit, servi par GitHub Pages).

## Où en est le jeu

| | Fichier source | Publié |
|---|---|---|
| Version en ligne (v41) | `game/vent-de-defiance.html` | GitHub Pages, artifact « Marine la maline » (claude.ai/artifact/2RAHDYhZEednF9efVrMrHv) |
| Prototype v2 | `game/proto.html` | artifact « Marine la maline (prototype) » (claude.ai/artifact/AfPc42bbuHMj331LQqkwhV) |

Les deux sont des pages canvas en un seul fichier HTML (environ 3 000 lignes). Le prototype part de la v41 et n'a jamais été poussé en ligne.

## Design du prototype v2 (validé par Pierre)

- **Tutoriel et difficulté adaptative coupés** (forcés dans `start()`), pour tester le cœur du jeu.
- **Sondages = barre de vie.** Départ 25 %. Ils baissent en continu : `drainBase + drainCass × casseroles` par seconde. Fin de partie sous `pollFloor` (10 %), écran « Décrochage ! ». Plus de plafond à 100 casseroles. Les casseroles ne touchent jamais au game feel.
- **Multiplicateur ×1 à ×5.** +1 par orbe ou journaliste bousculé, retour à ×1 sur une casserole ou une interview. Il s'applique aux gains de sondage et s'affiche près de Marine.
- **Seule la charge sur l'eau bouscule les journalistes** (le planage ne le fait plus).
- **Charge = vitesse = risque.** Après la charge pleine, un palier de vitesse toutes les `tierTime` s (`tierMul` [1,32 ; 1,55 ; 1,8]). Le saut garde la vitesse.
- **Orbes fantômes** (`fastShare`, environ 25 % des orbes hors or) : translucides, attrapables seulement à partir du palier 2, et elles paient double.
- **Trajectoires 30 % plus courtes et moins hautes** pour le saut chargé à fond et le planage (gravité 1286, jumpMin 394 pour garder la hauteur du plus petit saut, glideTime 0,98).
- **Orbe d'or :** zoom serré sur Marine (sprites `grab0-2`), ralenti à 4 % (`grabSlow`), jauge de timing. Toujours des sondages. Dans le vert : contre-feu (−20 casseroles). Parfait : toutes les casseroles disparaissent. Plus de gros plan sur fond noir, plus de choix contre-feu ou récupération.
- **Volte-face :** swipe vers la gauche (flèche gauche ou V au clavier), possible dans tous les états sauf le planage.
  - Animation `mode = 'turn'` d'environ 0,9 s : zoom et ralenti, les 3 images de `tack.jpg` en cut, puis le décor bascule (côte ↔ large). Le défilement ne change jamais de sens.
  - Ce qui était devant Marine (à l'écran) passe derrière elle (`flipWorld`). Le calendrier avance de `turnWeeks` (1,4 semaine), Marine repart à 60 % de sa vitesse et perd ses paliers.
  - **Zones obligatoires** (5 par partie, longueur `voltZoneLen` = 7 semaines) : bouées, fanions et panneau de l'ancienne position (`VSHORT`), puis le mur. Une volte-face dans la zone fait sombrer le mur, retourne le panneau vers la nouvelle position et rapporte de +1 à +5 points, d'autant plus qu'elle est faite près du mur (« In extremis ! »). Le mur ne se saute plus : le toucher affiche l'écran d'impact, +10 casseroles et −2 points.
  - Supprimés : l'écran girouette, les panneaux de changement de bord en fin de volte et la carte postale.
- **Gains actuels :** bronze 0,3 ; argent 0,6 ; or 1,2 ; journaliste bousculé 0,4 ; interview −1. Sondages plafonnés à 100 %.

## Pistes évoquées, pas encore faites

- **Calendrier en temps réel, distance qui dépend de la vitesse** (modèle Tiny Wings). Sans ça, aller vite fait juste défiler les semaines plus vite : la charge ne rapporte plus que via les orbes fantômes. C'est la contradiction principale du design actuel.
- **Saut automatique au-dessus des petites barques** (modèle Super Mario Run), pour alléger les commandes. Si ça marche, le planage est l'entrée à supprimer en premier.
- **Petits revirements obligatoires fréquents** entre les 5 grandes zones (modèle Temple Run).
- **Bardella en poursuivant visible** qui se rapproche quand les sondages baissent (modèles Ski Safari et Temple Run).
- **3 missions actives par partie** (Jetpack Joyride, Ski Safari, Tiny Wings).
- **Barrages de journalistes qu'on ne franchit qu'en charge** (Robot Unicorn Attack).
- **Volte-face en fausse 3D :** zoom à fond, 4 ou 5 images qui tournent autour de Marine. Il faut générer une nouvelle planche de sprites (prompts à écrire, voir `sprites/`).
- **Mis de côté par Pierre :** tutoriel, difficulté adaptative, mode infini, double saut, catalogue de volte-faces en badges, informations sourcées, nouveau sprite de Bardella, nouvelles images de changement de bord (version large).

## Points à juger en main

- Seuil du swipe : 40 px en moins de 0,35 s (`swipeDist`, `swipeTime`).
- Le multiplicateur ×5 rend les gains forts : un bot invincible finit autour de 85 à 99 %.
- Le miroir avant/arrière n'est visible que pour les objets à moins d'environ 0,7 semaine devant Marine, la caméra laissant peu de place derrière elle.

## Arborescence

- `game/` : sources et images. `game/single/` contient les versions compressées utilisées pour le fichier unique.
- `tools/`
  - `build_proto.py <source> <sortie>` : intègre les images dans un HTML unique (sortie dans `game/single/`).
  - `build_single.py` (version en ligne vers `single/marine-la-maline.html`) puis `build_gh.py` (vers `../../index.html`, la racine du dépôt), `stamp.py` (date de build, à adapter : il vise encore `vent-de-defiance.html`).
  - `patch_proto.py`, `patch_proto2.py` : historique des modifications du prototype, déjà appliquées. Ne pas les relancer.
  - Tests Playwright : `t200.py` à `t202b.py` (prototype : drain, volte en zone, swipe, paliers, partie complète par bot), `t93.py`, `t119.py`, `t123.py`, `t130.py`, `t143.py` (version en ligne).
  - Tous les chemins partent de `dev/game/`, ou de la variable d'environnement `VDD_GAME`. Il faut Python 3, Playwright et Chromium.
- `sprites/`
  - `sp4/` : planches 16-bit générées, `seg.py` (découpe) et `build4.py` (assemblage de `atlas4.png` et `atlas4.json`).
  - `sprite-gen/` : script de génération par l'API images d'OpenAI, avec `sheets.json` (prompts) et le modèle de page du Sprite Studio. La clé API reste en local, jamais dans le dépôt. Les photos de référence ne sont pas versionnées.
  - `prompts/` : prompts des planches.

## Repères dans le code (`game/proto.html`)

- `DEF` (vers la ligne 331) : tous les réglages.
- `doVolte`, `updateTurn`, `flipWorld`, `drawTurn`, `drawVolteHint`, `swipeStart` et `swipeMove` : la volte-face.
- `update()` : vitesse, paliers, gravité, drain des sondages, collisions, mur.
- `buildLevel` et `layout()` : génération du niveau (espacements calculés depuis la physique du saut).
- `beginGrab`, `grabEnd`, `drawGrabClose` : l'orbe d'or.
- `addPoll`, `bumpMult`, `breakMult`, `drawMult` : sondages et multiplicateur.
- `window.__vdd` : points d'accès pour les tests.
