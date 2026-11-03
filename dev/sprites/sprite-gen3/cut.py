"""Proto 3 : découpe des planches générées (fond magenta) en sprites, atlas5.png + atlas5.js.

Usage : python3 cut.py            (depuis n'importe où)
Entrées : sheets/<id>_*_v<n>.png (la variante retenue est dans PICK)
Sorties : ../../game/atlas5.png, ../../game/sky5.png, ../../game/sea5.png, ../../game/atlas5.js (entrées ATLAS + métadonnées),
          contact5.png (planche contact pour vérifier la découpe)
Toutes les images sont stockées à la moitié de la taille générée (1 pixel d'art = 2 px).
"""
import glob, json, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, '..', '..', 'game')
SHEETS = os.path.join(HERE, 'sheets')
PICK = {'m_fly': 1, 'm_react': 2, 'm_fall': 1}   # variante retenue (1 par défaut)
HALF = 0.5

def sheet(id_):
    v = PICK.get(id_, 1)
    fs = sorted(glob.glob(os.path.join(SHEETS, f'{id_}_*_v{v}.png')))
    if not fs: raise SystemExit(f'planche introuvable : {id_} v{v}')
    return np.array(Image.open(fs[-1]).convert('RGB')).astype(np.int16)

def key(a):
    """alpha : 0 sur le magenta (et ses franges), 255 ailleurs"""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = (r > 150) & (b > 150) & (g < 110) & (np.abs(r - b) < 90)
    fringe = (r > 120) & (b > 120) & (g < (np.minimum(r, b) - 60))
    alpha = np.where(mag | fringe, 0, 255).astype(np.uint8)
    return alpha

def clean(alpha, min_area, rel=True):
    lab, n = ndi.label(alpha > 0)
    if n == 0: return alpha, []
    sizes = ndi.sum(alpha > 0, lab, range(1, n + 1))
    keep = np.zeros(n + 1, bool); keep[1:] = (sizes >= min_area) & ((sizes >= 0.02*sizes.max()) if rel else True)   # pas de poussières isolées
    return np.where(keep[lab], alpha, 0).astype(np.uint8), [(i + 1, s) for i, s in enumerate(sizes) if s >= min_area]

def cells(a, cols, rows):
    H, W = a.shape[:2]; cw, ch = W // cols, H // rows
    return [(c * cw, r * ch, cw, ch) for r in range(rows) for c in range(cols)]
def unframe(al, m=8):
    al = al.copy(); al[:m] = 0; al[-m:] = 0; al[:, :m] = 0; al[:, -m:] = 0; return al   # les traits de grille au bord des cases

def erase_lines(rgb, alpha, bar):
    """efface les lignes de kite peintes (blanches, au-dessus et à droite de la barre) : le jeu les trace lui-même"""
    if bar is None: return alpha
    bx, by, bxr = bar
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    white = (r > 170) & (g > 170) & (b > 170) & (np.max(rgb, -1) - np.min(rgb, -1) < 60)
    yy, xx = np.mgrid[0:alpha.shape[0], 0:alpha.shape[1]]
    zone = (yy < by - 6) & (xx > bxr - 18)
    a2 = alpha.copy(); a2[white & zone] = 0
    # le contour gris foncé des lignes : petits restes isolés
    a2, _ = clean(a2, 150, rel=False)
    return a2

def bar_of(rgb, alpha):
    """la barre de kite : pixels bleu vif dans les deux tiers hauts (la planche, en bas, a aussi du bleu)"""
    ys, xs = np.nonzero(alpha)
    if len(ys) == 0: return None
    y0, y1 = ys.min(), ys.max()
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    blue = (b > 150) & (r < 110) & (g < 150) & (b - r > 90) & (alpha > 0)
    blue[int(y0 + (y1 - y0) * 0.72):] = False
    blue[:, :int(xs.min() + (xs.max() - xs.min()) * 0.4)] = False   # la barre est devant (à droite) ; la planche qui flotte derrière est à gauche
    by, bx = np.nonzero(blue)
    if len(by) < 20: return None
    return float(np.median(bx)), float(np.median(by)), float(np.percentile(bx, 95))

OUT = []   # (name, rgba image, anchor x, anchor y, meta)

def add(name, rgb, alpha, anchor='bottom', meta=None, flip=False, min_area=120, rel=True, fixed=None, smooth=False):
    alpha, _ = clean(alpha, min_area, rel)
    ys, xs = np.nonzero(alpha)
    if len(ys) == 0: print('VIDE', name); return
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    rgba = np.dstack([rgb[y0:y1, x0:x1].clip(0, 255).astype(np.uint8), alpha[y0:y1, x0:x1]])
    im = Image.fromarray(rgba, 'RGBA')
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    w, h = im.size
    ax, ay = (w / 2, h) if anchor == 'bottom' else (w / 2, h / 2)
    if fixed: ax, ay = fixed[0] - x0, fixed[1] - y0   # ancre commune (coordonnées de la case) : les poses s'échangent sans sauter
    meta = dict(meta or {})
    if 'bar' in meta and meta['bar']:   # coordonnées relatives à l'ancre
        bx, by = meta['bar'][0] - x0, meta['bar'][1] - y0
        if flip: bx = w - bx
        meta['bar'] = [round((bx - ax) * HALF, 1), round((by - ay) * HALF, 1)]
    if 'tips' in meta:
        meta['tips'] = [[round((tx - x0 - ax) * HALF, 1), round((ty - y0 - ay) * HALF, 1)] for tx, ty in meta['tips']]
    im = im.resize((max(1, round(w * HALF)), max(1, round(h * HALF))), Image.LANCZOS if smooth else Image.NEAREST)
    OUT.append((name, im, ax * HALF, ay * HALF, meta))

def grid(id_, cols, rows, names, anchor='bottom', marine=False, flips=(), split=None):
    a = sheet(id_); alpha = key(a)
    for i, (x, y, w, h) in enumerate(cells(a, cols, rows)):
        if i >= len(names) or not names[i]: continue
        rgb, al = a[y:y + h, x:x + w], unframe(alpha[y:y + h, x:x + w])
        al, _ = clean(al, 120)
        meta = {}
        if marine:
            bar = bar_of(rgb, al)
            al = erase_lines(rgb, al, bar)
            if bar: meta['bar'] = [bar[0], bar[1]]
        if split and names[i] in split:   # une case qui contient deux éléments séparés : le plus haut et le plus bas
            lab, n = ndi.label(al > 0); comps = ndi.find_objects(lab)
            sizes = ndi.sum(al > 0, lab, range(1, n + 1)); order = np.argsort(-sizes)[:2]
            parts = sorted([(comps[k][0].start, k + 1) for k in order])
            for (top, lid), nm in zip(parts, split[names[i]]):
                add(nm, rgb, np.where(lab == lid, al, 0).astype(np.uint8), anchor)
            continue
        add(names[i], rgb, al, anchor, meta, flip=names[i] in flips)

# Marine
grid('m_fly', 3, 2, ['mRide0', 'mRide1', 'mClimb', 'mGlide', 'mDive', 'mLand'], marine=True)
grid('m_react', 3, 2, ['mHit', 'mTalk', 'mPoint', 'mBarge', 'mCatch', 'mDazed'], marine=True)
grid('m_fall', 3, 2, ['mDrag0', 'mDrag1', 'mRemount', 'mSink0', 'mSink1', 'mHead'], marine=True)
# la voile : on garde la toile, on enlève les lignes peintes ; points d'attache = les deux extrémités basses de la toile
a = sheet('kite'); alpha = key(a)
for i, (x, y, w, h) in enumerate(cells(a, 2, 2)):
    rgb, al = a[y:y + h, x:x + w], alpha[y:y + h, x:x + w]
    lab, n = ndi.label(al > 0); sizes = ndi.sum(al > 0, lab, range(1, n + 1)); big = int(np.argmax(sizes)) + 1
    canopy = np.where(lab == big, al, 0).astype(np.uint8)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    white = (r > 170) & (g > 170) & (b > 170) & (np.max(rgb, -1) - np.min(rgb, -1) < 50)
    canopy[white & (ndi.binary_opening(canopy > 0, iterations=3) == 0)] = 0   # les lignes fines collées à la toile
    canopy, _ = clean(canopy, 400)
    ys, xs = np.nonzero(canopy); xm = (xs.min() + xs.max()) / 2
    L = xs < xm; R = ~L
    tl = (xs[L][np.argmax(ys[L])], ys[L].max()); tr = (xs[R][np.argmax(ys[R])], ys[R].max())
    add(f'nk{i}', rgb, canopy, 'center', {'tips': [tl, tr]}, min_area=400)
# journalistes
grid('j_boats', 3, 2, ['jb0', 'jb1', 'jb2', 'jt0', 'jt1', 'jbHit'], split={'jt1': ['jtJump', 'jtBoat']})
grid('j_air', 3, 2, ['jg0', 'jg1', 'jh0', 'jh1', 'jj0', 'jj1'], anchor='center', flips=('jh0',))
import os
if glob.glob(os.path.join(SHEETS, 'j_glider2_*_v1.png')):   # deltaplane avec micro tendu : remplace jg0/jg1 (6 poses : jg0..jg5)
    grid('j_glider2', 3, 2, ['jg0', 'jg1', 'jg2', 'jg3', 'jg4', 'jg5'], anchor='center')
# étrangers : debout (rangée du haut), en chute (rangée du bas)
grid('etr_a', 3, 2, ['e0s', 'e1s', 'e2s', 'e0f', 'e1f', 'e2f'])
grid('etr_b', 3, 2, ['e3s', 'e4s', 'e5s', 'e3f', 'e4f', 'e5f'])
grid('theme_boats', 3, 2, ['tb0', 'tb1', 'tb2', 'tb3', 'tb4', 'tb5'])
grid('scandal_a', 2, 2, ['nJus0', 'nJus1', 'nJus2', 'nJus3'])
grid('scandal_b', 3, 2, ['nRn0', 'nRn1', 'nRn2', 'nPan0', 'nPan1', 'nPan2'])
for n in ('nPan0', 'nPan1', 'nPan2'):   # projectiles : ancre au centre
    i = [k for k, o in enumerate(OUT) if o[0] == n][0]; nm, im, ax, ay, meta = OUT[i]; OUT[i] = (nm, im, im.size[0] / 2, im.size[1] / 2, meta)
a = sheet('montretout'); alpha = key(a)
add('mtHouse', a[:560], alpha[:560]); add('mtArch', a[560:], alpha[560:])
grid('decor_items', 3, 2, ['nSun', 'nCloud0', 'nCloud1', 'nCloud2', 'nCloud3', 'nGulls'], anchor='center')
grid('decor_far', 3, 2, ['far0', 'far1', 'far2', 'far3', 'far4', 'far5'])
grid('vane', 3, 2, ['vane0', 'vane1', 'vane2', 'vane3', 'flagCloth', 'sparkle'], anchor='center')
# les deux mouettes : une case, deux images
i = [k for k, o in enumerate(OUT) if o[0] == 'nGulls'][0]; nm, im, ax, ay, meta = OUT.pop(i)
arr = np.array(im); lab, n = ndi.label(arr[..., 3] > 0); objs = sorted(ndi.find_objects(lab), key=lambda s: s[1].start)
for k, sl in enumerate(objs[:2]):
    sub = Image.fromarray(arr[sl], 'RGBA'); OUT.append((f'nGull{k}', sub, sub.size[0] / 2, sub.size[1] / 2, {}))

# Bardella : il arrive de la droite, il doit regarder à gauche (la planche est sortie tournée à droite) ; en fuite, il repart à droite
if glob.glob(os.path.join(SHEETS, 'bard_poses_*_v1.png')):
    grid('bard_poses', 3, 2, ['bRide0', 'bRide1', 'bWind', 'bThrow', 'bHit', 'bFlee'], marine=True, flips=('bRide0', 'bRide1', 'bWind', 'bThrow', 'bHit'))
# les illustrations des cartes : le rectangle encadré de chaque case, opaque, réduit à 240 px de large
def cards(id_, cols, rows, names):
    if not glob.glob(os.path.join(SHEETS, f'{id_}_*_v1.png')): return
    a = sheet(id_); alpha = key(a)
    for i, (x, y, w, h) in enumerate(cells(a, cols, rows)):
        if i >= len(names) or not names[i]: continue
        al = unframe(alpha[y:y + h, x:x + w], 4); lab, n = ndi.label(al > 0)
        if n == 0: continue
        sizes = ndi.sum(al > 0, lab, range(1, n + 1)); sl = ndi.find_objects(lab)[int(np.argmax(sizes))]
        rgb = a[y:y + h, x:x + w][sl].clip(0, 255).astype(np.uint8)
        im = Image.fromarray(np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)]), 'RGBA')
        im = im.resize((240, round(240 * im.size[1] / im.size[0])), Image.LANCZOS)
        OUT.append((names[i], im, im.size[0] / 2, im.size[1] / 2, {}))
cards('cards_theme', 3, 2, ['cTheme0', 'cTheme1', 'cTheme2', 'cTheme3', 'cTheme4', 'cTheme5'])
cards('cards_volte', 3, 2, ['cVolte0', 'cVolte1', 'cVolte2', 'cVolte3', 'cVolte4', 'cVolte5'])
cards('cards_scandal', 3, 2, ['cScan1', 'cScan2', 'cScan4', 'cScan5', 'cPump', 'cKevlar'])
cards('cards_tuto', 2, 2, ['cTuto0', 'cTuto1', 'cTuto2', 'cTuto3'])
for v in (1, 2):   # la carte des brebis galeuses (une image carrée), quand elle existe
    if glob.glob(os.path.join(SHEETS, f'cards_brebis{"2" if v == 2 else ""}_*_v1.png')):
        cards('cards_brebis' + ('2' if v == 2 else ''), 1, 1, ['cScan3'])

# poses de Marine redessinées sur une même pose de repos (planche m_lock) : elles remplacent les anciennes ; la gerbe d'eau n'est gardée que sur la glisse
def no_spray(rgb, al):
    """la gerbe d'eau : les pixels clairs (blanc, bleu d'écume) dans le tiers bas et le tiers gauche (derrière la planche)"""
    ys, xs = np.nonzero(al)
    if len(ys) == 0: return al
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    light = ((r > 150) & (g > 150) & (b > 150)) | ((b > 150) & (r < 150) & (g > 120))
    yy, xx = np.mgrid[0:al.shape[0], 0:al.shape[1]]
    zone = (yy > y0 + (y1 - y0) * 0.7) & (xx < x0 + (x1 - x0) * 0.33)
    al = al.copy(); al[light & zone] = 0
    lab, n = ndi.label(al > 0)
    if n:
        sizes = ndi.sum(al > 0, lab, range(1, n + 1)); big = int(np.argmax(sizes)) + 1
        cy = ndi.center_of_mass(al > 0, lab, range(1, n + 1))
        for k in range(n):   # restes de gouttelettes dans le bas ; les étoiles, en haut, restent
            if k + 1 != big and sizes[k] < 2000 and cy[k][0] > y0 + (y1 - y0) * 0.6: al[lab == k + 1] = 0
    return al
if glob.glob(os.path.join(SHEETS, 'm_lock_*_v1.png')):
    LOCK = ['mRide0', 'mHit', 'mDazed', 'mClimb', 'mGlide', 'mCatch']
    OUT[:] = [o for o in OUT if o[0] not in LOCK]
    a = sheet('m_lock'); alpha = key(a); fy = None
    for i, (x, y, w, h) in enumerate(cells(a, 3, 2)):
        rgb, al = a[y:y + h, x:x + w], alpha[y:y + h, x:x + w].copy()
        bar = bar_of(rgb, al); al = erase_lines(rgb, al, bar)
        if LOCK[i] != 'mRide0': al = no_spray(rgb, al)
        if fy is None: fy = int(np.nonzero(al)[0].max()) + 1   # le dessous de la planche de la pose de repos
        add(LOCK[i], rgb, al, 'bottom', {'bar': [bar[0], bar[1]]} if bar else {}, min_area=60, rel=False, fixed=(w * 0.5, fy))

# le kit d'interface (graphisme plat, lissé) : icônes et tampons ; le logo du titre est aussi exporté à part, en grand
def ui_grid(id_, cols, rows, names):
    if not glob.glob(os.path.join(SHEETS, f'{id_}_*_v1.png')): return None
    a = sheet(id_); alpha = key(a); cs = cells(a, cols, rows)
    for i, (x, y, w, h) in enumerate(cs):
        if i < len(names) and names[i]: add(names[i], a[y:y + h, x:x + w], unframe(alpha[y:y + h, x:x + w]), 'center', smooth=True, min_area=200)
    return a, alpha, cs
ui_grid('ui_icons', 4, 3, ['iPolls', 'iCaisse', 'iCoin', 'iVolte', 'iScandale', 'iMic', 'iKevlar', 'iPump', 'iVote', 'iElysee', 'iMontretout', 'i2027'])
r = ui_grid('ui_logos', 2, 2, ['logoTitle', 'stampVolte', 'stampScandale', 'stampElim'])
if r:
    a, alpha, cs = r; x, y, w, h = cs[0]; al, _ = clean(alpha[y:y + h, x:x + w].copy(), 200); ys, xs = np.nonzero(al)
    rgba = np.dstack([a[y:y + h, x:x + w].clip(0, 255).astype(np.uint8), al])[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    Image.fromarray(rgba, 'RGBA').save(os.path.join(GAME, 'logo5.png'), optimize=True)
if glob.glob(os.path.join(SHEETS, 'menu_art_*_v1.png')):   # le fond de l'écran titre, au format du cadre (845 x 390)
    m = Image.fromarray(sheet('menu_art').astype(np.uint8)); mh = round(1536 * 390 / 845); top = (1024 - mh) // 2
    m.crop((0, top, 1536, top + mh)).resize((1300, 600), Image.LANCZOS).save(os.path.join(GAME, 'menu5.jpg'), quality=86)

# chute et remontée (planche m_fall2, même base que m_lock) : perd l'équilibre, tombe, traînée, remonte, se relève
if glob.glob(os.path.join(SHEETS, 'm_fall2_*_v1.png')):
    F2 = [None, 'mTip', 'mFall', 'mDrag0', 'mRemount', 'mStand']
    OUT[:] = [o for o in OUT if o[0] not in ('mDrag0', 'mDrag1', 'mRemount') + tuple(n for n in F2 if n)]
    a = sheet('m_fall2'); alpha = key(a); fy = None
    for i, (x, y, w, h) in enumerate(cells(a, 3, 2)):
        rgb, al = a[y:y + h, x:x + w], unframe(alpha[y:y + h, x:x + w])
        bar = bar_of(rgb, al); al = erase_lines(rgb, al, bar)
        if i == 0: fy = int(np.nonzero(al)[0].max()) + 1; continue
        if F2[i] not in ('mDrag0',): al = no_spray(rgb, al)
        add(F2[i], rgb, al, 'bottom', {'bar': [bar[0], bar[1]]} if bar else {}, min_area=60, rel=False, fixed=(w * 0.5, fy))
# barques du thème animées : deux images chacune (tbN = image A, tbNb = image B)
for sid, base in (('theme_anim_a', 0), ('theme_anim_b', 3)):
    if not glob.glob(os.path.join(SHEETS, f'{sid}_*_v1.png')): continue
    names = [f'tb{base + c}' for c in range(3)] + [f'tb{base + c}b' for c in range(3)]
    OUT[:] = [o for o in OUT if o[0] not in names]
    grid(sid, 3, 2, names)
# le contre-feu : le baril en feu (3 images) et sa carte
if glob.glob(os.path.join(SHEETS, 'bonus_fire_*_v1.png')):
    grid('bonus_fire', 3, 2, ['fire0', 'fire1', 'fire2', None, None, None], anchor='center')
    cards('bonus_fire', 3, 2, [None, None, None, 'cFire', None, None])
# décor lointain 2 (far6..far11) et second plan (mid0..mid5)
if glob.glob(os.path.join(SHEETS, 'decor_far2_*_v1.png')):
    grid('decor_far2', 3, 2, ['far6', 'far7', 'far8', 'far9', 'far10', 'far11'])
if glob.glob(os.path.join(SHEETS, 'decor_mid_*_v1.png')):
    grid('decor_mid', 3, 2, ['mid0', 'mid1', 'mid2', 'mid3', 'mid4', 'mid5'])
# Marine tirée par la voile, sans planche (planche m_pull, même base que m_lock) : ancre fixe sur la base
if glob.glob(os.path.join(SHEETS, 'm_pull_*_v1.png')):
    FP = ['mPull0', 'mPull1', 'mPull2', 'mPull3', 'mPull4', 'mPull5']
    OUT[:] = [o for o in OUT if o[0] not in tuple(n for n in FP if n)]
    a = sheet('m_pull'); alpha = key(a); fy = None
    for i, (x, y, w, h) in enumerate(cells(a, 3, 2)):
        rgb, al = a[y:y + h, x:x + w], unframe(alpha[y:y + h, x:x + w])
        bar = bar_of(rgb, al); al = erase_lines(rgb, al, bar)
        if i == 0: fy = int(np.nonzero(al)[0].max()) + 1
        add(FP[i], rgb, al, 'bottom', {'bar': [bar[0], bar[1]]} if bar else {}, min_area=60, rel=False, fixed=(w * 0.5, fy))
# icônes UI 2 : baril (contre-feu), vent, coche, étoile, bateau, coq
if glob.glob(os.path.join(SHEETS, 'ui_icons2_*_v1.png')):
    ui_grid('ui_icons2', 3, 2, ['iFire', 'iWind', 'iCheck', 'iStar', 'iBoat', 'iCoq'])

# assemblage : rangées, largeur 2048
W = 2048; x = y = rowh = 0; ent = {}; meta = {}
for nm, im, ax, ay, me in sorted(OUT, key=lambda o: -o[1].size[1]):
    w, h = im.size
    if x + w > W: x = 0; y += rowh + 2; rowh = 0
    ent[nm] = [x, y, w, h, round(ax, 1), round(ay, 1), 5]; im._pos = (x, y)
    if me: meta[nm] = me
    x += w + 2; rowh = max(rowh, h)
atlas = Image.new('RGBA', (W, y + rowh), (0, 0, 0, 0))
for nm, im, ax, ay, me in OUT: atlas.paste(im, im._pos)
atlas.save(os.path.join(GAME, 'atlas5.png'), optimize=True)
for nm, out in (('decor_sky', 'sky5.png'), ('decor_sea', 'sea5.png')):
    Image.fromarray(sheet(nm).astype(np.uint8)).resize((768, 512), Image.NEAREST).save(os.path.join(GAME, out), optimize=True)
open(os.path.join(GAME, 'atlas5.js'), 'w').write('Object.assign(ATLAS, ' + json.dumps(ent) + ');\nconst META5 = ' + json.dumps(meta) + ';\n')
# planche contact
cols = 8; cw, chh = 256, 200; rows = (len(OUT) + cols - 1) // cols
c = Image.new('RGB', (cols * cw, rows * chh), (90, 110, 140)); d = ImageDraw.Draw(c)
for k, (nm, im, ax, ay, me) in enumerate(OUT):
    t = im.copy(); t.thumbnail((cw - 10, chh - 30)); px, py = (k % cols) * cw + 5, (k // cols) * chh + 22
    c.paste(t, (px, py), t); d.text((px, py - 16), nm, fill='white')
    if me.get('bar'):
        s = t.size[0] / im.size[0]; d.ellipse([px + (ax + me['bar'][0]) * s - 4, py + (ay + me['bar'][1]) * s - 4, px + (ax + me['bar'][0]) * s + 4, py + (ay + me['bar'][1]) * s + 4], outline='yellow', width=2)
    for tp in me.get('tips', []):
        s = t.size[0] / im.size[0]; d.ellipse([px + (ax + tp[0]) * s - 4, py + (ay + tp[1]) * s - 4, px + (ax + tp[0]) * s + 4, py + (ay + tp[1]) * s + 4], outline='cyan', width=2)
c.save(os.path.join(HERE, 'contact5.png'))
print(len(OUT), 'sprites, atlas', atlas.size)
