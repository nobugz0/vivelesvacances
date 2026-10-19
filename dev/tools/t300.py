"""Proto 3, étape 1 : vol jouable. Démarrage, les deux commandes, collecte, contacts, atterrissage, limite d'altitude, menu de réglage, fin de vol."""
import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
from playwright.sync_api import sync_playwright
import time, sys, os
D = GAME
FILE = sys.argv[1] if len(sys.argv) > 1 else 'proto3.html'
def ev(pg, s): return pg.evaluate(s)
def boot(p, ctrl, vp=(1280, 720)):
    b = p.chromium.launch(args=['--allow-file-access-from-files', '--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': vp[0], 'height': vp[1]})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append('console.' + m.type + ': ' + m.text) if m.type == 'error' else None)
    pg.goto('file://' + D + FILE); pg.wait_for_timeout(1200)
    ev(pg, 'window.__vdd.setCtrl(%r)' % ctrl); pg.click('#flyBtn'); pg.wait_for_timeout(600)
    return b, pg, errs
ok = True
def check(cond, msg):
    global ok
    print(('OK  ' if cond else 'FAIL') + ' ' + msg)
    if not cond: ok = False
def bot(pg, seconds, wind):
    """suit la pièce la plus proche devant, sans jamais dépasser la limite d'altitude"""
    t0 = time.time(); ceil = ev(pg, 'window.__vdd.P.ceil')
    if wind: pg.mouse.move(900, 360); pg.mouse.down()
    while time.time() - t0 < seconds and ev(pg, 'window.__vdd.state') == 'play':
        cs = ev(pg, 'window.__vdd.coinsList.filter(c => c.x > window.__vdd.px - 10 && c.x < window.__vdd.px + 500)'); y = ev(pg, 'window.__vdd.y')
        ty = max(ceil + (170 if wind else 70), min(cs, key=lambda c: c['x'])['y']) if cs else ceil + 200
        if wind:
            d = max(-1, min(1, (y - ty)/140.0)); pg.mouse.move(900, 360 - d*270)
        else:
            if ev(pg, 'window.__vdd.wind') < 0.15 and not ev(pg, 'window.__vdd.onWater'): pg.mouse.up()
            elif ty < y - 8: pg.mouse.down()
            else: pg.mouse.up()
        pg.wait_for_timeout(40)
    pg.mouse.up()
with sync_playwright() as p:
    # 0. cadre fixe 845 x 390, de 100 à 150 %
    for vp, want in [((1280, 720), 845*1.5), ((1920, 1080), 845*1.5), ((844, 390), 844), ((600, 400), 600)]:
        b, pg, errs = boot(p, 'tap', vp); w = ev(pg, 'document.getElementById("wrap").getBoundingClientRect().width'); h = ev(pg, 'document.getElementById("wrap").getBoundingClientRect().height')
        check(abs(w - want) < 2 and abs(h - want*390/845) < 2, 'fenêtre %dx%d -> cadre %.0fx%.0f' % (vp[0], vp[1], w, h)); b.close()
    # A. appui
    b, pg, errs = boot(p, 'tap')
    check(ev(pg, 'window.__vdd.state') == 'play' and ev(pg, 'window.__vdd.ctrl') == 'tap', 'démarrage en mode appui')
    w = ev(pg, 'window.__vdd.world'); print('   monde', w, 'yMax', ev(pg, 'window.__vdd.P.yMax'))
    check(ev(pg, 'window.__vdd.onWater'), 'Marine démarre posée sur l\'eau')
    y0 = ev(pg, 'window.__vdd.y'); pg.mouse.move(640, 360); pg.mouse.down(); pg.wait_for_timeout(700); y1 = ev(pg, 'window.__vdd.y')
    check(y1 < y0 - 60, 'appui = monte (%.0f -> %.0f)' % (y0, y1))
    pg.mouse.up(); pg.wait_for_timeout(1400); y2 = ev(pg, 'window.__vdd.y')
    check(y2 > y1 + 60, 'relâché = inversion, plané puis chute (%.0f -> %.0f)' % (y1, y2))
    # orbe d'argent : on force une orbe et on va la chercher au-dessus de la ligne, en ressortant avant que la jauge soit pleine
    o0 = ev(pg, 'window.__vdd.stats.orbs')
    ev(pg, 'window.__vdd.P.orbEvery = 2'); ev(pg, '''() => new Promise(res => { const v = window.__vdd; let t0 = performance.now(), ph = 'wait';
      const step = () => { const now = performance.now(); const o = v.orbs.find(o => o.alert <= 0);
        const near = o && (o.x - v.px) < v.P.speed/v.world.Z*0.55;   // on ne monte au-dessus de la ligne que quand l'orbe est à moins de 0,55 s
        if (near){ v.hold(v.y > o.y + 4); if (v.blowGauge > 0.85) v.hold(false); }
        else v.hold(v.y > v.P.ceil + 60);
        if (v.stats.orbs > %d || now - t0 > 20000 || v.state !== 'play'){ v.hold(false); res(); return; }
        requestAnimationFrame(step); }; requestAnimationFrame(step); })''' % o0)
    check(ev(pg, 'window.__vdd.stats.orbs') > o0 and ev(pg, 'window.__vdd.state') == 'play', 'orbe d\'argent attrapée au-dessus de la ligne sans être emportée (jauge %.2f)' % ev(pg, 'window.__vdd.blowGauge'))
    pg.screenshot(path=D + 'p3_orb.png'); ev(pg, 'window.__vdd.P.orbEvery = 13')
    # limite d'altitude : monter tout droit finit emporté par le vent
    pg.mouse.down(); t0 = time.time()
    while time.time() - t0 < 6 and ev(pg, 'window.__vdd.state') == 'play': ev(pg, 'window.__vdd.setWind(1)'); pg.wait_for_timeout(50)
    pg.mouse.up(); pg.wait_for_timeout(1200)
    check(ev(pg, 'window.__vdd.endReason') == 'blown' and ev(pg, 'window.__vdd.state') == 'recap', 'trop haut trop longtemps = emportée par le vent -> écran de niveau perdu')
    pg.screenshot(path=D + 'p3_blown.png')
    # bot sur une vraie partie
    ev(pg, 'window.__vdd.startTestFly()'); pg.wait_for_timeout(300); bot(pg, 25, False)
    st = ev(pg, 'window.__vdd.stats'); print('   bot appui 25 s :', st, 'poll', round(ev(pg, 'window.__vdd.poll'), 2))
    check(st['coins'] > 40, 'le bot ramasse des pièces (%d)' % st['coins'])
    st = ev(pg, 'window.__vdd.stats'); expect = 25 + 10*ev(pg, 'window.__vdd.t')/75 - st['hits'] + st['orbs']
    check(abs(ev(pg, 'window.__vdd.poll') - expect) < 0.3, 'sondages = 25 + distance - contacts + orbes (%.2f, attendu %.2f)' % (ev(pg, 'window.__vdd.poll'), expect))
    pg.screenshot(path=D + 'p3_tap_bot.png')
    ev(pg, 'window.__vdd.setT(74.5)'); pg.wait_for_timeout(900); check(ev(pg, 'window.__vdd.phase') == 'intro', 'fin du vol à 75 s -> la carte du scandale (jeu en pause)'); pg.screenshot(path=D + 'p3_recap.png')
    # menu de réglage
    pg.click('#gearBtn'); pg.wait_for_timeout(200)
    check(not ev(pg, 'document.getElementById("debug").hidden'), 'la roue crantée ouvre le menu de réglage')
    n = ev(pg, 'document.querySelectorAll("#debug input[type=range]").length'); check(n == len([1 for sp in ev(pg, 'window.__vdd.PSPEC') if sp['g'] != 'Vent']), '%d curseurs, un par paramètre hors vent' % n)
    ev(pg, '(() => { const i = document.getElementById("dbg_cam"); i.value = 0.5; i.dispatchEvent(new Event("input")); })()'); pg.wait_for_timeout(50)
    w2 = ev(pg, 'window.__vdd.world'); check(abs(w2['Z'] - 0.5) < 1e-6 and w2['WH'] == 780, 'le curseur caméra change le monde (%s)' % w2)
    pg.click('#dbgSave'); pg.wait_for_timeout(300); msg = ev(pg, 'document.getElementById("dbgMsg").textContent'); check('Enregistré' in msg, 'sauvegarde : ' + msg)
    pg.screenshot(path=D + 'p3_debug.png')
    ev(pg, '(() => { const i = document.getElementById("dbg_cam"); i.value = 0.6; i.dispatchEvent(new Event("input")); })()'); pg.click('#dbgSave'); pg.wait_for_timeout(300)
    pg.reload(); pg.wait_for_timeout(1200); check(abs(ev(pg, 'window.__vdd.P.cam') - 0.6) < 1e-6, 'les réglages sauvegardés reviennent après rechargement')
    ev(pg, 'localStorage.removeItem("p3-settings")')
    check(not errs, 'aucune erreur JS (appui) ' + str(errs[:3]))
    b.close()

    # B. réserve de vent : tenir l'appui vide la jauge en windCap s, puis l'appui ne répond plus ; se poser recharge
    b, pg, errs = boot(p, 'tap')
    ev(pg, 'window.__vdd.setWind(1)'); pg.mouse.move(640, 300); pg.mouse.down(); pg.wait_for_timeout(600)
    w1 = ev(pg, 'window.__vdd.wind'); check(0.75 < w1 < 0.95, 'l\'appui consomme la jauge (%.2f après 0,6 s, cap %s s)' % (w1, ev(pg, 'window.__vdd.P.windCap')))
    pg.mouse.up(); pg.wait_for_timeout(300); w2 = ev(pg, 'window.__vdd.wind'); check(abs(w2 - w1) < 0.02 or ev(pg, 'window.__vdd.onWater'), 'relâché en l\'air : la jauge ne bouge pas (%.2f)' % w2)
    ev(pg, 'window.__vdd.setWind(0.02)'); pg.mouse.down(); pg.wait_for_timeout(400)
    check(ev(pg, 'window.__vdd.wind') == 0 and ev(pg, 'window.__vdd.vy') >= 0, 'jauge vide : l\'appui ne fait plus monter (vy %.0f)' % ev(pg, 'window.__vdd.vy'))
    pg.screenshot(path=D + 'p3_nowind.png')
    t0 = time.time()
    while time.time() - t0 < 4 and not ev(pg, 'window.__vdd.onWater'): pg.wait_for_timeout(50)
    pg.wait_for_timeout(100); w3 = ev(pg, 'window.__vdd.wind'); check(w3 >= ev(pg, 'window.__vdd.P.windMin')/100 - 0.01, 'à la pose : reliquat immédiat (%.2f)' % w3)
    pg.mouse.up(); pg.wait_for_timeout(1600); check(ev(pg, 'window.__vdd.wind') > 0.95, 'sur l\'eau : rechargée en windRefill s (%.2f)' % ev(pg, 'window.__vdd.wind'))
    check(ev(pg, 'document.getElementById("ctrlSel")') is None and ev(pg, 'document.querySelectorAll("#debug input[type=range]").length') == len([1 for sp in ev(pg, 'window.__vdd.PSPEC') if sp['g'] != 'Vent']), 'la commande vent n\'est plus proposée (menu titre ni réglages)')
    check(not errs, 'aucune erreur JS (vent) ' + str(errs[:3]))
    b.close()
    # C. la tempête : bouton de test direct, carte de pause, tirs par couloirs avec préavis, retombées, chaîne ; un bot qui esquive et un bot immobile
    for lvl, kind, dodge in [(1, 'justice', True), (2, 'rn', False), (3, 'bard', True)]:
        b, pg, errs = boot(p, 'tap'); pg.click('#closeBtn'); pg.wait_for_timeout(200); ev(pg, 'window.__vdd.P.level = %d' % lvl); pg.click('#stormBtn'); pg.wait_for_timeout(800)
        e = ev(pg, 'window.__vdd.emitter'); check(ev(pg, 'window.__vdd.phase') == 'intro' and e and e['kind'] == kind and ev(pg, 'window.__vdd.t') < 1, 'niveau %d : « Tester la tempête » ouvre la carte directement, émetteur %s' % (lvl, e and e['kind']))
        y0 = ev(pg, 'window.__vdd.y'); pg.wait_for_timeout(600)
        if lvl == 1: pg.screenshot(path=D + 'p3_intro.png')
        pg.mouse.move(640, 200); pg.mouse.down(); pg.wait_for_timeout(100); pg.mouse.up(); pg.wait_for_timeout(100)
        check(ev(pg, 'window.__vdd.phase') == 'storm' and abs(ev(pg, 'window.__vdd.y') - y0) < 1, 'le tap reprend le jeu, qui était en pause')
        pg.wait_for_timeout(2500); pl = ev(pg, 'window.__vdd.pansList'); check(len(pl) > 0 and all(x['kind'] in ('shot', 'lob', 'curve') for x in pl), 'des casseroles sont lancées : tirs tendus, cloches sur Marine ou incurvées (%d)' % len(pl))
        if lvl == 1: pg.wait_for_timeout(1200); pg.screenshot(path=D + 'p3_storm.png')
        if dodge:
            # bot dans la page, à la frame : se place dans le couloir le plus loin de toute menace qui atteint sa colonne dans les 1,3 s
            ev(pg, '''() => new Promise(res => { const v = window.__vdd; const step = () => { if (v.state !== 'play'){ v.hold(false); res(); return; }
              const px = v.px, y = v.y, P = v.P, top = P.ceil + 60, bot = P.yMax; const th = [];
              for (const c of v.pansList){ const tc = (c.x - px)/Math.max(1, -c.vx), t = tc + Math.max(0, c.delay); if (t < 1.4 && c.x > px - 30) th.push(c.y + c.vy*tc + 0.5*c.g*tc*tc); }
              let best = y, bestD = -1; for (let k = 0; k <= 8; k++){ const cy = top + (bot - top)*k/8; const d = th.length ? Math.min(...th.map(t => Math.abs(t - cy))) : 1e9; const score = d - Math.abs(cy - y)*0.15; if (score > bestD){ bestD = score; best = cy; } }
              if (!th.length) best = v.onWater ? y : Math.max(y, bot - 120);
              const up = best < y - 8 && (v.wind > 0.05 || v.onWater); v.hold(up); requestAnimationFrame(step); }; requestAnimationFrame(step); })''')
        else:
            t0 = time.time()
            while time.time() - t0 < 30 and ev(pg, 'window.__vdd.state') == 'play': pg.wait_for_timeout(100)
        pg.mouse.up(); print('   tempête niveau %d (%s) : casseroles %d, chaîne %d, raison %s' % (lvl, 'esquive' if dodge else 'immobile sur l\'eau', ev(pg, 'window.__vdd.cass'), len(ev(pg, 'window.__vdd.chain')), ev(pg, 'window.__vdd.endReason')))
        check(ev(pg, 'window.__vdd.state') == 'recap' and ev(pg, 'window.__vdd.endReason') in ('done', 'sunk'), 'la tempête se termine (délai ou coulée)')
        if not dodge: check(ev(pg, 'window.__vdd.cass') >= 3, 'rester sur l\'eau sans bouger ne suffit pas : les cloches sur Marine touchent (%d)' % ev(pg, 'window.__vdd.cass'))
        if dodge: check(ev(pg, 'window.__vdd.endReason') == 'done', 'un bot qui esquive par couloirs traverse la tempête (%d casseroles)' % ev(pg, 'window.__vdd.cass'))
        check(not errs, 'aucune erreur JS (tempête %d) ' % lvl + str(errs[:3]))
        b.close()
    b, pg, errs = boot(p, 'tap'); ev(pg, 'window.__vdd.startTest()'); pg.wait_for_timeout(800); ev(pg, 'window.__vdd.beginStormPlay(); window.__vdd.setCass(9)')
    t0 = time.time()
    while time.time() - t0 < 25 and ev(pg, 'window.__vdd.state') == 'play': pg.wait_for_timeout(100)
    check(ev(pg, 'window.__vdd.endReason') == 'sunk', 'à cassMax casseroles, Marine coule -> on recommence le niveau'); pg.screenshot(path=D + 'p3_sunk.png'); b.close()
    # D. la course : bouton de test, orbe et traîne, jauge qui se remplit dans la traîne, rattrapage progressif, fin par capture ou départ ; menu à onglets
    b, pg, errs = boot(p, 'tap'); pg.click('#closeBtn'); pg.wait_for_timeout(200); pg.click('#chaseBtn'); pg.wait_for_timeout(600)
    c = ev(pg, 'window.__vdd.chase'); check(ev(pg, 'window.__vdd.phase') == 'chase' and c and c['t'] < 1, '« Tester la course » lance la course directement (t=%.1f)' % c['t'])
    d0 = c['dist']; px0 = ev(pg, 'window.__vdd.px'); want = ev(pg, 'window.__vdd.P.chaseX0/100*window.__vdd.world.VWW - window.__vdd.px'); check(abs(d0 - want) < 40, 'orbe au départ à chaseX0 %% de l\'écran, Marine à 22 %% (distance %.0f)' % d0)
    # bot qui suit la traîne à la frame : vise ty
    ev(pg, '''() => new Promise(res => { const v = window.__vdd; const step = () => { const c = v.chase; if (v.state !== 'play' || !c || c.caught || c.leaving){ v.hold(false); res(); return; }
      const ty = c.ty === undefined ? c.y : c.ty; const up = ty < v.y - 6 && (v.wind > 0.05 || v.onWater); v.hold(up); if (!window.__dmax || c.dist > window.__dmax) window.__dmax = c.dist; if (v.onWater && v.wind > 0.9) window.__refilled = true; requestAnimationFrame(step); }; requestAnimationFrame(step); })''')
    c = ev(pg, 'window.__vdd.chase'); print('   course (suivi) : t %.1f s, jauge %.2f, dist %.0f, attrapée %s' % (c['t'], c['gauge'], c['dist'], c['caught']))
    check(c['caught'] and c['t'] < ev(pg, 'window.__vdd.P.chaseMax'), 'un bot qui suit la traîne remplit la jauge avant la fin (%.1f s)' % c['t'])
    px1 = ev(pg, 'window.__vdd.px'); check(c['dist'] < d0 and px1 > px0 + 100, 'Marine a avancé vers l\'orbe en remplissant la jauge (x %.0f -> %.0f, distance %.0f -> %.0f)' % (px0, px1, d0, c['dist']))
    check(ev(pg, 'window.__vdd.wind') >= 0.99, 'vol infini pendant la course (jauge de vent pleine)')
    pg.screenshot(path=D + 'p3_chase.png'); pg.wait_for_timeout(1200)
    check(ev(pg, 'window.__vdd.state') == 'recap' and ev(pg, 'window.__vdd.stats.gold'), 'actu d\'or attrapée -> récap avec volte-face')
    # sans suivre : l'orbe s'en va à chaseMax, le niveau est réussi sans volte-face
    ev(pg, 'window.__vdd.startTestChase()'); pg.wait_for_timeout(300); ev(pg, 'window.__vdd.P.chaseMax = 6'); t0 = time.time(); seen = None
    while time.time() - t0 < 14 and ev(pg, 'window.__vdd.state') == 'play':
        c = ev(pg, 'window.__vdd.chase'); ev(pg, 'window.__vdd.hold(window.__vdd.y > 330)')   # reste à mi-hauteur, appui maintenu pendant l'envol
        if c and c['leaving'] and seen is None and c['dist'] > 0: pg.wait_for_timeout(900); seen = ev(pg, 'window.__vdd.chase'); pg.screenshot(path=D + 'p3_flyaway.png')
        pg.wait_for_timeout(100)
    pg.mouse.up(); c = ev(pg, 'window.__vdd.chase')
    check(seen is not None and seen['camFx'] < 0.95, 'quand le temps est écoulé, la caméra recule (camFx %.2f)' % (seen['camFx'] if seen else 1))
    check(ev(pg, 'window.__vdd.state') == 'recap' and ev(pg, 'window.__vdd.endReason') == 'done' and not ev(pg, 'window.__vdd.stats.gold') and ev(pg, 'window.__vdd.onWater'), 'l\'actu s\'envole, Marine retombe à l\'eau malgré l\'appui, niveau réussi sans volte-face')
    ev(pg, 'window.__vdd.P.chaseMax = 15')
    # menu à onglets, largeur <= 25 %
    pg.click('#gearBtn'); pg.wait_for_timeout(200)
    w = ev(pg, 'document.getElementById("debug").getBoundingClientRect().width'); W = ev(pg, 'window.innerWidth'); check(w <= W*0.25 + 1, 'menu de réglage : %.0f px sur %d (%.0f %%)' % (w, W, 100*w/W))
    tabs = ev(pg, 'Array.from(document.querySelectorAll("#debug .tabs button")).map(b => b.textContent)'); check(tabs == ['Commun', 'Appui', 'Tempête', 'Course'], 'onglets : ' + ', '.join(tabs))
    pg.click('#debug .tabs button[data-tab=Course]'); vis = ev(pg, 'Array.from(document.querySelectorAll("#debug .tab")).filter(t => !t.hidden).map(t => t.dataset.tab)'); check(vis == ['Course'], 'un seul onglet visible à la fois (%s)' % vis)
    pg.screenshot(path=D + 'p3_menu.png')
    check(not errs, 'aucune erreur JS (course) ' + str(errs[:3]))
    b.close()

    # E. la campagne : menu, carte, tuto, boutique et bonus, perte et reprise, déblocage, sauvegarde, fiches « i », fin de campagne
    TRAIL_BOT = """() => new Promise(res => { const v = window.__vdd; const step = () => { const c = v.chase; if (v.state !== 'play' || v.phase !== 'chase' || !c || c.caught || c.leaving){ v.hold(false); res(); return; }
      const ty = c.ty === undefined ? c.y : c.ty; v.hold(ty < v.y - 6); requestAnimationFrame(step); }; requestAnimationFrame(step); })"""
    def wait_state(pg, want, secs):
        t0 = time.time()
        while time.time() - t0 < secs and ev(pg, 'window.__vdd.state') not in want: pg.wait_for_timeout(100)
        return ev(pg, 'window.__vdd.state')
    b = p.chromium.launch(args=['--allow-file-access-from-files', '--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1280, 'height': 720})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append('console.' + m.type + ': ' + m.text) if m.type == 'error' else None)
    pg.goto('file://' + D + FILE); pg.wait_for_timeout(1200); ev(pg, 'window.__vdd.resetCamp()')
    pg.click('#startBtn'); pg.wait_for_timeout(400)
    ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]
    check(ev(pg, 'window.__vdd.state') == 'map' and ev(pg, 'window.__vdd.camp.unlocked') == 2, '« Lancer la campagne » ouvre la carte ; tuto et niveau 1 ouverts (%d chapitres)' % ev(pg, 'window.__vdd.camp.unlocked'))
    check('play:0' in ids and 'play:1' in ids and ids.count('locked') == 4 and 'info:1' in ids, 'carte : deux boutons Jouer, quatre verrouillés, boutons i (%s)' % ids)
    pg.screenshot(path=D + 'p3_map.png')
    # fiche « i » du niveau 1 : volte-face puis scandale, sources
    ev(pg, 'window.__vdd.tap("info:1")'); pg.wait_for_timeout(200); io = ev(pg, 'window.__vdd.infoOpen'); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]
    check(io and io['n'] == 1 and io['page'] == 'level' and 'infoPage' in ids and 'infoClose' in ids and 'src:0' in ids, 'fiche du niveau 1 : volte-face, sources cliquables, bouton vers le scandale')
    pg.screenshot(path=D + 'p3_info.png'); ev(pg, 'window.__vdd.tap("infoPage")'); pg.wait_for_timeout(200)
    check(ev(pg, 'window.__vdd.infoOpen.page') == 'scandal', 'la fiche passe au scandale'); pg.screenshot(path=D + 'p3_info_scandal.png')
    ev(pg, 'window.__vdd.tap("play:1")'); check(ev(pg, 'window.__vdd.state') == 'map', 'fiche ouverte : les boutons de la carte sont inactifs')
    ev(pg, 'window.__vdd.tap("infoClose")'); check(ev(pg, 'window.__vdd.infoOpen') is None, 'fermeture de la fiche')
    # le tuto : pas de boutique, vol court, pas de tempête, course facile
    ev(pg, 'window.__vdd.P.tutoFlight = 8'); ev(pg, 'window.__vdd.tap("play:0")'); pg.wait_for_timeout(300)
    check(ev(pg, 'window.__vdd.state') == 'play' and ev(pg, 'window.__vdd.levelN') == 0 and ev(pg, 'window.__vdd.mode') == 'camp', 'le tuto démarre directement (sans boutique)')
    pg.screenshot(path=D + 'p3_tuto.png'); bot(pg, 9, False)
    check(ev(pg, 'window.__vdd.phase') == 'chase' and ev(pg, 'window.__vdd.emitter') is None, 'au tuto, le vol enchaîne sur la course sans tempête')
    ev(pg, TRAIL_BOT); c = ev(pg, 'window.__vdd.chase'); check(c['caught'], 'course du tuto attrapée par le bot (%.1f s)' % c['t'])
    st = wait_state(pg, ('recap',), 4); r = ev(pg, 'window.__vdd.camp.levels[0]'); coins0 = ev(pg, 'window.__vdd.camp.coins')
    check(st == 'recap' and r and r['done'] and r['gold'] and coins0 > 0, 'tuto terminé : résultat enregistré, pièces en réserve (%d)' % coins0)
    ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]; check('map' in ids and 'again' in ids, 'récap de campagne : Carte et Rejouer')
    ev(pg, 'window.__vdd.tap("map")'); pg.wait_for_timeout(200); check(ev(pg, 'window.__vdd.state') == 'map' and ev(pg, 'window.__vdd.camp.unlocked') == 2, 'retour à la carte ; le tuto ne débloque rien de plus')
    # niveau 1 : boutique, prix en rouge si on ne peut pas, achat, bonus actif
    ev(pg, 'window.__vdd.tap("play:1")'); pg.wait_for_timeout(200); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]
    check(ev(pg, 'window.__vdd.state') == 'shop' and 'nobonus' in ids, 'niveau 1 : la boutique s\'ouvre (%s)' % ids)
    check(ev(pg, 'window.__vdd.camp.coins') < 120 and 'buy:pump' not in ids and ids.count('locked') == 3, 'sans assez de pièces, les trois bonus sont grisés')
    pg.screenshot(path=D + 'p3_shop_poor.png'); ev(pg, 'window.__vdd.camp.coins += 500; window.__vdd.saveCamp()'); pg.wait_for_timeout(100); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]
    check('buy:pump' in ids and 'buy:kevlar' in ids and 'buy:fire' not in ids, 'avec des pièces : pompe et kevlar achetables, contre-feu grisé (rien à éteindre)'); pg.screenshot(path=D + 'p3_shop.png')
    c0 = ev(pg, 'window.__vdd.camp.coins'); ev(pg, 'window.__vdd.P.flight = 8; window.__vdd.tap("buy:kevlar")'); pg.wait_for_timeout(300)
    check(ev(pg, 'window.__vdd.state') == 'play' and ev(pg, 'window.__vdd.bonus') == 'kevlar' and ev(pg, 'window.__vdd.kevlarLeft') == 3 and ev(pg, 'window.__vdd.camp.coins') == c0 - 200, 'veste en kevlar achetée (200), niveau 1 lancé, 3 journalistes gratuits')
    # perdre : coulée -> on recommence depuis l'état d'entrée, le bonus reste, les pièces ramassées restent
    pg.wait_for_timeout(8500); check(ev(pg, 'window.__vdd.phase') == 'intro', 'après le vol, la tempête du niveau 1 (carte de pause)')
    ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]; check('sinfo' in ids, 'la carte du scandale a son bouton i')
    ev(pg, 'window.__vdd.tap("sinfo")'); check(ev(pg, 'window.__vdd.infoOpen.page') == 'scandal', 'bouton i de la tempête : fiche du scandale'); pg.screenshot(path=D + 'p3_intro_info.png'); ev(pg, 'window.__vdd.tap("infoClose")')
    ev(pg, 'window.__vdd.beginStormPlay(); window.__vdd.setCass(9)'); st = wait_state(pg, ('recap',), 25)
    check(st == 'recap' and ev(pg, 'window.__vdd.endReason') == 'sunk', 'coulée pendant la tempête')
    ev(pg, 'window.__vdd.tap("again")'); pg.wait_for_timeout(300)
    check(ev(pg, 'window.__vdd.state') == 'play' and ev(pg, 'window.__vdd.cass') == 0 and ev(pg, 'window.__vdd.bonus') == 'kevlar' and ev(pg, 'window.__vdd.levelN') == 1, 'Recommencer : niveau 1 depuis son état d\'entrée (0 casserole), bonus conservé')
    # réussir : tempête écourtée, course suivie -> niveau 2 débloqué, état d'entrée transmis
    ev(pg, 'window.__vdd.P.stormMax = 3'); pg.wait_for_timeout(8500); ev(pg, 'window.__vdd.beginStormPlay()'); t0 = time.time()
    while time.time() - t0 < 12 and ev(pg, 'window.__vdd.phase') != 'chase': pg.wait_for_timeout(100)
    ev(pg, TRAIL_BOT); st = wait_state(pg, ('recap',), 5); r = ev(pg, 'window.__vdd.camp'); l1 = r['levels'][1]; l2 = r['levels'][2]
    check(st == 'recap' and l1['done'] and r['unlocked'] == 3 and l2 and abs(l2['entry']['poll'] - l1['poll']) < 0.01 and l2['entry']['cass'] == l1['cass'], 'niveau 1 réussi : niveau 2 débloqué, sondages et casseroles transmis (%.1f %%, %d)' % (l1['poll'], l1['cass']))
    check(ev(pg, 'window.__vdd.bonus') is None, 'le bonus est consommé à la fin du niveau')
    # sauvegarde : rechargement de la page
    pg.reload(); pg.wait_for_timeout(1200); r = ev(pg, 'window.__vdd.camp')
    check(r['unlocked'] == 3 and r['levels'][1]['done'] and r['coins'] > 0, 'la campagne est rechargée depuis l\'appareil (%d chapitres, %d pièces)' % (r['unlocked'], r['coins']))
    # fin de campagne : niveau 5 (tout débloqué), bureau de vote, bilan final
    ev(pg, 'window.__vdd.unlockAll(); window.__vdd.goShop(5)'); pg.wait_for_timeout(200); check(ev(pg, 'window.__vdd.state') == 'shop' and ev(pg, 'window.__vdd.levelN') == 5, 'tout débloquer -> boutique du niveau 5')
    ev(pg, 'window.__vdd.P.flight = 6; window.__vdd.P.stormMax = 3; window.__vdd.tap("nobonus")'); pg.wait_for_timeout(6500); ev(pg, 'window.__vdd.beginStormPlay()'); t0 = time.time()
    while time.time() - t0 < 12 and ev(pg, 'window.__vdd.phase') != 'chase': pg.wait_for_timeout(100)
    ev(pg, TRAIL_BOT); st = wait_state(pg, ('final',), 4); check(st == 'final', 'niveau 5 fini : séquence finale (atterrissage, bureau de vote)')
    pg.wait_for_timeout(1500); pg.screenshot(path=D + 'p3_final_booth.png'); st = wait_state(pg, ('finalRecap',), 8)
    bo = ev(pg, 'window.__vdd.booth'); check(st == 'finalRecap' and bo and bo['reached'] and ev(pg, 'window.__vdd.onWater'), 'Marine posée, bureau de vote atteint -> bilan final (%.1f s)' % ev(pg, 'window.__vdd.finalT'))
    pg.screenshot(path=D + 'p3_final.png'); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]; check('map' in ids and 'title' in ids, 'bilan final : Carte et Menu')
    ev(pg, 'window.__vdd.tap("map")'); pg.wait_for_timeout(200); check(ev(pg, 'window.__vdd.state') == 'map' and ev(pg, 'window.__vdd.camp.levels[5].done'), 'retour à la carte, niveau 5 enregistré'); pg.screenshot(path=D + 'p3_map_done.png')
    # mobile : tap réel sur une carte de la carte de campagne (cadre pivoté)
    ctx2 = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True); pm = ctx2.new_page(); pm.goto('file://' + D + FILE); pm.wait_for_timeout(1200)
    ev(pm, 'window.__vdd.goMap()'); pm.wait_for_timeout(300); bt = [x for x in ev(pm, 'window.__vdd.btns') if x['id'] == 'play:0'][0]
    sc = ev(pm, 'document.getElementById("wrap").getBoundingClientRect().width/390'); r = ev(pm, 'JSON.parse(JSON.stringify(document.getElementById("wrap").getBoundingClientRect()))')
    lx, ly = (bt['x'] + bt['w']/2)*sc, (bt['y'] + bt['h']/2)*sc; pm.touchscreen.tap(r['right'] - ly, r['top'] + lx); pm.wait_for_timeout(400)
    check(ev(pm, 'window.__vdd.state') == 'play' and ev(pm, 'window.__vdd.levelN') == 0, 'mobile (cadre pivoté) : le tap sur « Jouer » du tuto lance le tuto'); ctx2.close()
    check(not errs, 'aucune erreur JS (campagne) ' + str(errs[:3]))
    b.close()
print('RESULT', 'PASS' if ok else 'FAIL')
