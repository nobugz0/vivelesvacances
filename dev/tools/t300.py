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
    # plafond : monter tout droit s'arrête au plafond, sans sanction
    pg.mouse.down(); t0 = time.time()
    while time.time() - t0 < 4 and ev(pg, 'window.__vdd.state') == 'play': ev(pg, 'window.__vdd.setWind(1)'); pg.wait_for_timeout(50)
    yc = ev(pg, 'window.__vdd.y'); pg.mouse.up(); pg.wait_for_timeout(300)
    check(abs(yc - ev(pg, 'window.__vdd.P.ceil')) < 2 and ev(pg, 'window.__vdd.state') == 'play', 'plafond : Marine s\'arrête à ceil (%.0f) et le niveau continue' % yc)
    # frôlement : un deltaplane passe juste au-dessus de la zone de contact -> bonus de sondage ; un autre passe au contact -> perte, pas de bonus
    ev(pg, 'window.__vdd.hold(false); window.__vdd.clearField()'); pg.wait_for_timeout(2500); ev(pg, 'window.__vdd.clearField()')
    p0 = ev(pg, 'window.__vdd.poll'); ev(pg, 'window.__vdd.addJourno("glider", window.__vdd.px + 420, window.__vdd.y - (22 + 28 + 20))'); pg.wait_for_timeout(2500)
    check(abs(ev(pg, 'window.__vdd.poll') - p0) < 0.001, 'un journaliste qui passe sans contact ne change pas les sondages (plus de gain à la distance ni au frôlement)')
    h0 = ev(pg, 'window.__vdd.stats.hits'); ev(pg, 'window.__vdd.addJourno("glider", window.__vdd.px + 420, window.__vdd.y)'); pg.wait_for_timeout(2500)
    check(ev(pg, 'window.__vdd.stats.hits') == h0 + 1 and abs(ev(pg, 'window.__vdd.poll') - (p0 - ev(pg, 'window.__vdd.P.hitPoll'))) < 0.001, 'au contact : −hitPoll (%.2f -> %.2f)' % (p0, ev(pg, 'window.__vdd.poll')))
    w = ev(pg, 'window.__vdd.world'); check(w['camFx'] > 1.25 and w['VWW'] < w['VWW0'], 'en vol, la caméra est rapprochée (camFx %.2f, bord droit %.0f < %.0f)' % (w['camFx'], w['VWW'], w['VWW0']))
    # archétypes : au niveau 1, ni hélico ni trampoline ; au niveau 4, le trampoliniste et le jet-ski arrivent, le jet-ski se cale sous Marine
    ev(pg, 'window.__vdd.P.level = 1; window.__vdd.startTestFly()'); seen = set(); t0 = time.time()
    while time.time() - t0 < 12: seen |= set(j['kind'] for j in ev(pg, 'window.__vdd.journos')); pg.wait_for_timeout(300)
    check('heli' not in seen and 'tramp' not in seen and 'jet' not in seen and 'boat' in seen, 'niveau 1 : barques et deltaplanes seulement (%s)' % sorted(seen))
    ev(pg, 'window.__vdd.P.level = 4; window.__vdd.startTestFly()'); seen = set(); t0 = time.time(); held = 0
    while time.time() - t0 < 40 and not ('tramp' in seen and held > 0):
        js = ev(pg, 'window.__vdd.journos'); seen |= set(j['kind'] for j in js); ev(pg, 'window.__vdd.hold(window.__vdd.y > 300)')
        if any(j['kind'] == 'jet' and abs(j['x'] - ev(pg, 'window.__vdd.px') - 60) < 3 for j in js): held += 1
        pg.wait_for_timeout(150)
    ev(pg, 'window.__vdd.hold(false)'); check('tramp' in seen and 'jet' in seen and held > 0, 'niveau 4 : trampoliniste et jet-ski présents, le jet-ski se cale sous Marine (%s, %d)' % (sorted(seen), held))
    ev(pg, 'window.__vdd.P.level = 1')
    # bot sur une vraie partie
    ev(pg, 'window.__vdd.startTestFly()'); pg.wait_for_timeout(300); bot(pg, 25, False)
    st = ev(pg, 'window.__vdd.stats'); print('   bot appui 25 s :', st, 'poll', round(ev(pg, 'window.__vdd.poll'), 2))
    check(st['coins'] > 40, 'le bot ramasse des pièces (%d)' % st['coins'])
    pg.screenshot(path=D + 'p3_tap_bot.png')
    ev(pg, 'window.__vdd.setT(34.5)'); pg.wait_for_timeout(900); ap = ev(pg, 'window.__vdd.phase'); pg.wait_for_timeout(2400); check(ap == 'approach' and ev(pg, 'window.__vdd.phase') == 'intro' and ev(pg, 'window.__vdd.world.camFx') < 1.05, 'fin du vol à 35 s -> approche du bateau, caméra reculée, puis la carte du scandale (jeu en pause)'); pg.screenshot(path=D + 'p3_recap.png')
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
        pg.mouse.move(640, 200); pg.mouse.down(); pg.wait_for_timeout(100); pg.mouse.up(); pg.wait_for_timeout(100)
        check(ev(pg, 'window.__vdd.phase') == 'storm' and abs(ev(pg, 'window.__vdd.y') - y0) < 1, 'le tap reprend le jeu, qui était en pause')
        pg.wait_for_timeout(int((ev(pg, 'window.__vdd.P.lineT') + 1.6)*1000)); pl = ev(pg, 'window.__vdd.pansList'); check(len(pl) > 0 and all(x['kind'] in ('shot', 'lob', 'curve') for x in pl), 'des casseroles sont lancées : tirs tendus, cloches sur Marine ou incurvées (%d)' % len(pl))
        sh = [x for x in pl if x['kind'] == 'shot']
        for _ in range(6):
            if sh: break
            pg.wait_for_timeout(500); sh = [x for x in ev(pg, 'window.__vdd.pansList') if x['kind'] == 'shot']
        check(len(sh) > 0 and all(x['g'] > 0 for x in sh), 'les tirs tendus décrivent une légère parabole (%d)' % len(sh))
        if lvl == 1: pg.wait_for_timeout(2000); check(len(ev(pg, 'window.__vdd.coinsList')) > 0, 'des pièces arrivent pendant la tempête (%d)' % len(ev(pg, 'window.__vdd.coinsList')))
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
    # D. la course par cercles : bouton de test, girouette au ras de l'eau, cercles lâchés, bot qui les passe (Marine avance, caméra se rapproche), capture ; sans rien faire, la girouette s'envole
    RING_BOT = """() => new Promise(res => { const v = window.__vdd; const step = () => { const c = v.chase; if (v.state !== 'play' || v.phase !== 'chase' || !c || c.caught || c.leaving){ v.hold(false); res(); return; }
      const nx = c.rings.filter(r => r.state === 'wait' && r.x > v.px).sort((a, b) => a.x - b.x)[0]; const ty = nx ? nx.y : c.y; v.hold(ty < v.y - 6); requestAnimationFrame(step); }; requestAnimationFrame(step); })"""
    b, pg, errs = boot(p, 'tap'); pg.click('#closeBtn'); pg.wait_for_timeout(200); pg.click('#chaseBtn'); pg.wait_for_timeout(600)
    c = ev(pg, 'window.__vdd.chase'); check(ev(pg, 'window.__vdd.phase') == 'chase' and c and c['t'] < 1, '« Tester la course » lance la course directement (t=%.1f)' % c['t'])
    check(c['y'] > ev(pg, 'window.__vdd.P.yMax') - 60, 'la girouette part au ras de l\'eau (y %.0f)' % c['y'])
    d0 = c['dist']; px0 = ev(pg, 'window.__vdd.px'); want = ev(pg, 'window.__vdd.P.chaseX0/100*window.__vdd.world.VWW0 - window.__vdd.px'); check(abs(d0 - want) < 40, 'girouette au départ à chaseX0 %% de la largeur de base, Marine à 22 %% (distance %.0f)' % d0)
    pg.wait_for_timeout(2800); c = ev(pg, 'window.__vdd.chase'); check(c['dropped'] >= 1 and len(c['rings']) >= 1 and all(abs(r['y'] - c['y']) < 400 for r in c['rings']), 'la girouette lâche des cercles derrière elle (%d)' % c['dropped'])
    ev(pg, RING_BOT); c = ev(pg, 'window.__vdd.chase'); print('   course (cercles) : t %.1f s, passés %d / lâchés %d, dist %.0f, attrapée %s' % (c['t'], c['passed'], c['dropped'], c['dist'], c['caught']))
    check(c['caught'] and c['passed'] == ev(pg, 'window.__vdd.P.ringNeed'), 'un bot qui vise les cercles en passe %d et attrape la girouette (%.1f s)' % (c['passed'], c['t']))
    check(ev(pg, 'window.__vdd.world.camFx') > 1.25, 'la caméra s\'est rapprochée à chaque cercle (camFx %.2f)' % ev(pg, 'window.__vdd.world.camFx'))
    px1 = ev(pg, 'window.__vdd.px'); check(c['dist'] < d0 and px1 > px0 + 100, 'Marine a avancé vers la girouette à chaque cercle (x %.0f -> %.0f, distance %.0f -> %.0f)' % (px0, px1, d0, c['dist']))
    check(ev(pg, 'window.__vdd.wind') >= 0.99, 'vol infini pendant la course (jauge de vent pleine)')
    pg.screenshot(path=D + 'p3_chase.png'); pg.wait_for_timeout(1200)
    check(ev(pg, 'window.__vdd.state') == 'recap' and ev(pg, 'window.__vdd.stats.gold'), 'girouette attrapée -> récap (mode test) avec volte-face')
    # sans rien faire : les cercles sont manqués, la girouette s'envole après le dernier, le niveau est réussi sans volte-face
    ev(pg, 'window.__vdd.startTestChase()'); pg.wait_for_timeout(300); ev(pg, 'window.__vdd.P.ringTotal = 4'); t0 = time.time(); seen = None
    while time.time() - t0 < 16 and ev(pg, 'window.__vdd.state') == 'play':
        c = ev(pg, 'window.__vdd.chase'); ev(pg, 'window.__vdd.hold(window.__vdd.y > 330)')   # reste à mi-hauteur, appui maintenu pendant l'envol
        if c and c['leaving'] and seen is None: pg.wait_for_timeout(900); seen = ev(pg, 'window.__vdd.chase'); pg.screenshot(path=D + 'p3_flyaway.png')
        pg.wait_for_timeout(100)
    pg.mouse.up(); c = ev(pg, 'window.__vdd.chase')
    check(seen is not None and seen['camFx'] < 0.95, 'tous les cercles lâchés sans le compte : la girouette s\'envole, la caméra recule (camFx %.2f)' % (seen['camFx'] if seen else 1))
    check(ev(pg, 'window.__vdd.state') == 'recap' and ev(pg, 'window.__vdd.endReason') == 'done' and not ev(pg, 'window.__vdd.stats.gold') and ev(pg, 'window.__vdd.onWater'), 'la girouette s\'envole, Marine retombe à l\'eau malgré l\'appui, niveau réussi sans volte-face')
    ev(pg, 'window.__vdd.P.ringTotal = 8')
    # menu à onglets, largeur <= 25 %
    pg.click('#gearBtn'); pg.wait_for_timeout(200)
    w = ev(pg, 'document.getElementById("debug").getBoundingClientRect().width'); W = ev(pg, 'window.innerWidth'); check(w <= W*0.25 + 1, 'menu de réglage : %.0f px sur %d (%.0f %%)' % (w, W, 100*w/W))
    tabs = ev(pg, 'Array.from(document.querySelectorAll("#debug .tabs button")).map(b => b.textContent)'); check(tabs == ['Commun', 'Appui', 'Tempête', 'Course'], 'onglets : ' + ', '.join(tabs))
    pg.click('#debug .tabs button[data-tab=Course]'); vis = ev(pg, 'Array.from(document.querySelectorAll("#debug .tab")).filter(t => !t.hidden).map(t => t.dataset.tab)'); check(vis == ['Course'], 'un seul onglet visible à la fois (%s)' % vis)
    pg.screenshot(path=D + 'p3_menu.png')
    check(not errs, 'aucune erreur JS (course) ' + str(errs[:3]))
    b.close()

    # E. la campagne enchaînée : menu (Continuer / Nouvelle campagne), écran intermédiaire, tuto sautable, achats, perte et reprise, enchaînement, sauvegarde, fiches, fin
    def wait_phase(pg, want, secs):
        t0 = time.time()
        while time.time() - t0 < secs and ev(pg, 'window.__vdd.phase') != want: pg.wait_for_timeout(100)
        return ev(pg, 'window.__vdd.phase')
    def wait_state(pg, want, secs):
        t0 = time.time()
        while time.time() - t0 < secs and ev(pg, 'window.__vdd.state') not in want: pg.wait_for_timeout(100)
        return ev(pg, 'window.__vdd.state')
    b = p.chromium.launch(args=['--allow-file-access-from-files', '--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1280, 'height': 720})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append('console.' + m.type + ': ' + m.text) if m.type == 'error' else None)
    pg.goto('file://' + D + FILE); pg.wait_for_timeout(1200); ev(pg, 'window.__vdd.resetCamp()'); pg.reload(); pg.wait_for_timeout(1200)
    check(ev(pg, 'document.getElementById("continueBtn").hidden') and not ev(pg, 'document.getElementById("newBtn").hidden'), 'menu : sans campagne en cours, seulement « Nouvelle campagne »')
    pg.click('#newBtn'); pg.wait_for_timeout(400); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]
    check(ev(pg, 'window.__vdd.state') == 'inter' and ev(pg, 'window.__vdd.levelN') == 0 and 'go' in ids and 'skipTuto' in ids and 'info:0' in ids and 'buy:votes' not in ids, 'nouvelle campagne : écran du tuto (C’est parti, Passer, i), sans boutique')
    pg.screenshot(path=D + 'p3_inter0.png')
    # fiche « i » depuis l'écran intermédiaire
    ev(pg, 'window.__vdd.tap("info:0")'); pg.wait_for_timeout(200); io = ev(pg, 'window.__vdd.infoOpen'); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]
    check(io and io['n'] == 0 and 'infoClose' in ids and 'src:0' in ids and 'infoPage' not in ids, 'fiche du tuto : volte-face et sources, pas de page scandale'); pg.screenshot(path=D + 'p3_info.png')
    ev(pg, 'window.__vdd.tap("go")'); check(ev(pg, 'window.__vdd.state') == 'inter', 'fiche ouverte : les boutons de l’écran sont inactifs'); ev(pg, 'window.__vdd.tap("infoClose")')
    # le tuto : vol court, pas de tempête, course facile ; puis l'écran du chapitre 1 porte le résultat
    ev(pg, 'window.__vdd.P.tutoFlight = 8; window.__vdd.tap("go")'); pg.wait_for_timeout(300)
    check(ev(pg, 'window.__vdd.state') == 'play' and ev(pg, 'window.__vdd.levelN') == 0 and ev(pg, 'window.__vdd.mode') == 'camp', 'le tuto démarre')
    pg.screenshot(path=D + 'p3_tuto.png'); bot(pg, 9, False)
    check(ev(pg, 'window.__vdd.phase') == 'chase' and ev(pg, 'window.__vdd.emitter') is None, 'au tuto, le vol enchaîne sur la course sans tempête')
    ev(pg, RING_BOT); c = ev(pg, 'window.__vdd.chase'); check(c['caught'], 'course du tuto attrapée par le bot (%.1f s)' % c['t'])
    st = wait_state(pg, ('inter',), 4); r = ev(pg, 'window.__vdd.camp.levels[0]'); coins0 = ev(pg, 'window.__vdd.camp.coins'); R = ev(pg, 'window.__vdd.lastResult')
    check(st == 'inter' and ev(pg, 'window.__vdd.levelN') == 1 and ev(pg, 'window.__vdd.camp.cur') == 1 and r and r['done'] and r['gold'] and coins0 > 0 and R and R['n'] == 0 and R['gold'], 'tuto terminé : l’écran du chapitre 1 s’affiche avec le résultat du tuto, pièces en réserve (%d)' % coins0)
    ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]; check('go' in ids and 'buy:votes' not in ids and ids.count('locked') >= 1, 'chapitre 1 sans assez de pièces : voix et bonus grisés'); pg.screenshot(path=D + 'p3_inter1.png')
    ev(pg, 'window.__vdd.camp.coins += 500; window.__vdd.saveCamp()'); pg.wait_for_timeout(150); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]
    check('buy:pump' in ids and 'buy:kevlar' in ids and 'buy:fire' not in ids and 'buy:votes' in ids, 'avec des pièces : pompe, kevlar et voix achetables, contre-feu grisé (rien à éteindre)')
    e0 = ev(pg, 'window.__vdd.camp.levels[1] ? window.__vdd.camp.levels[1].entry.poll : window.__vdd.P.pollStart'); c1 = ev(pg, 'window.__vdd.camp.coins'); pr = ev(pg, 'window.__vdd.votePrice'); ev(pg, 'window.__vdd.tap("buy:votes")'); pg.wait_for_timeout(150)
    check(ev(pg, 'window.__vdd.state') == 'inter' and ev(pg, 'window.__vdd.camp.coins') == c1 - pr and abs(ev(pg, 'window.__vdd.camp.levels[1].entry.poll') - e0 - ev(pg, 'window.__vdd.P.voteGain')) < 0.001 and ev(pg, 'window.__vdd.votePrice') > pr, 'acheter des voix : −%d pièces, +%.0f pt à l’entrée du chapitre, prix suivant %d' % (pr, ev(pg, 'window.__vdd.P.voteGain'), ev(pg, 'window.__vdd.votePrice')))
    pg.screenshot(path=D + 'p3_inter1_rich.png')
    c0 = ev(pg, 'window.__vdd.camp.coins'); ev(pg, 'window.__vdd.P.flight = 8; window.__vdd.tap("buy:kevlar")'); pg.wait_for_timeout(300)
    check(ev(pg, 'window.__vdd.state') == 'play' and ev(pg, 'window.__vdd.bonus') == 'kevlar' and ev(pg, 'window.__vdd.kevlarLeft') == 3 and ev(pg, 'window.__vdd.camp.coins') == c0 - 200, 'veste en kevlar achetée (200), chapitre 1 lancé, 3 journalistes gratuits')
    # perdre : coulée -> on recommence depuis l'état d'entrée, le bonus reste, les pièces ramassées restent
    pg.wait_for_timeout(8300); ap = ev(pg, 'window.__vdd.phase'); ex0 = ev(pg, 'window.__vdd.emitter && window.__vdd.emitter.x'); pg.wait_for_timeout(2200)
    check(ap == 'approach' and ev(pg, 'window.__vdd.phase') == 'intro' and ex0 >= ev(pg, 'window.__vdd.world.VWW0') - 240, 'après le vol, le bateau du scandale approche à vue (x %.0f) puis la carte s’affiche' % ex0)
    pg.screenshot(path=D + 'p3_intro.png')
    ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]; check('sinfo' in ids, 'la carte du scandale a son bouton i')
    ev(pg, 'window.__vdd.tap("sinfo")'); check(ev(pg, 'window.__vdd.infoOpen.page') == 'scandal', 'bouton i de la tempête : fiche du scandale'); pg.screenshot(path=D + 'p3_intro_info.png'); ev(pg, 'window.__vdd.tap("infoClose")')
    ev(pg, 'window.__vdd.beginStormPlay(); window.__vdd.setCass(9)'); st = wait_state(pg, ('recap',), 25)
    check(st == 'recap' and ev(pg, 'window.__vdd.endReason') == 'sunk', 'coulée pendant la tempête'); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]; check('again' in ids and 'title' in ids, 'écran de défaite : Recommencer et Menu')
    ev(pg, 'window.__vdd.tap("again")'); pg.wait_for_timeout(300)
    check(ev(pg, 'window.__vdd.state') == 'play' and ev(pg, 'window.__vdd.cass') == 0 and ev(pg, 'window.__vdd.bonus') == 'kevlar' and ev(pg, 'window.__vdd.levelN') == 1, 'Recommencer : chapitre 1 depuis son état d’entrée (0 casserole), bonus conservé')
    # réussir : tempête écourtée, cercles passés -> écran du chapitre 2 avec le résultat, état d'entrée transmis
    ev(pg, 'window.__vdd.P.stormMax = 3'); wait_phase(pg, 'intro', 14); ev(pg, 'window.__vdd.beginStormPlay()'); wait_phase(pg, 'chase', 12)
    ev(pg, RING_BOT); st = wait_state(pg, ('inter',), 5); r = ev(pg, 'window.__vdd.camp'); l1 = r['levels'][1]; l2 = r['levels'][2]
    check(st == 'inter' and ev(pg, 'window.__vdd.levelN') == 2 and r['cur'] == 2 and l1['done'] and l2 and abs(l2['entry']['poll'] - l1['poll']) < 0.01 and l2['entry']['cass'] == l1['cass'], 'chapitre 1 réussi : écran du chapitre 2, sondages et casseroles transmis (%.1f %%, %d)' % (l1['poll'], l1['cass']))
    check(ev(pg, 'window.__vdd.bonus') is None and ev(pg, 'window.__vdd.lastResult.n') == 1, 'le bonus est consommé ; le bandeau porte le résultat du chapitre 1'); pg.screenshot(path=D + 'p3_inter2.png')
    # sauvegarde : rechargement de la page, « Continuer » reprend au chapitre 2
    pg.reload(); pg.wait_for_timeout(1200); r = ev(pg, 'window.__vdd.camp')
    check(r['cur'] == 2 and r['levels'][1]['done'] and r['coins'] > 0 and not ev(pg, 'document.getElementById("continueBtn").hidden'), 'la campagne est rechargée (chapitre %d, %d pièces), « Continuer » proposé' % (r['cur'], r['coins']))
    pg.click('#continueBtn'); pg.wait_for_timeout(300); check(ev(pg, 'window.__vdd.state') == 'inter' and ev(pg, 'window.__vdd.levelN') == 2, '« Continuer » reprend à l’écran du chapitre 2')
    # passer le tuto depuis une nouvelle campagne
    ev(pg, 'window.__vdd.resetCamp(); window.__vdd.goInter(0, null); window.__vdd.tap("skipTuto")'); pg.wait_for_timeout(200); check(ev(pg, 'window.__vdd.levelN') == 1 and ev(pg, 'window.__vdd.camp.cur') == 1, '« Passer le tuto » mène au chapitre 1')
    # fin de campagne : chapitre 5, bureau de vote, bilan final
    ev(pg, 'window.__vdd.setCur(5); window.__vdd.goInter(5, null)'); pg.wait_for_timeout(200); check(ev(pg, 'window.__vdd.state') == 'inter' and ev(pg, 'window.__vdd.levelN') == 5, 'écran du chapitre 5')
    ev(pg, 'window.__vdd.P.flight = 6; window.__vdd.P.stormMax = 3; window.__vdd.tap("go")'); wait_phase(pg, 'intro', 12); ev(pg, 'window.__vdd.beginStormPlay()'); wait_phase(pg, 'chase', 12)
    ev(pg, RING_BOT); st = wait_state(pg, ('final',), 4); check(st == 'final', 'chapitre 5 fini : séquence finale (atterrissage, bureau de vote)')
    pg.wait_for_timeout(1500); pg.screenshot(path=D + 'p3_final_booth.png'); st = wait_state(pg, ('finalRecap',), 8)
    bo = ev(pg, 'window.__vdd.booth'); check(st == 'finalRecap' and bo and bo['reached'] and ev(pg, 'window.__vdd.onWater') and ev(pg, 'window.__vdd.camp.cur') == 6, 'Marine posée, bureau de vote atteint -> bilan final, campagne terminée (%.1f s)' % ev(pg, 'window.__vdd.finalT'))
    pg.screenshot(path=D + 'p3_final.png'); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]; check('newCamp' in ids and 'title' in ids, 'bilan final : Nouvelle campagne et Menu')
    ev(pg, 'window.__vdd.tap("title")'); pg.wait_for_timeout(200); check(ev(pg, 'window.__vdd.state') == 'title' and ev(pg, 'document.getElementById("continueBtn").hidden'), 'menu après la fin : plus de « Continuer »')
    # mobile : tap réel sur « C'est parti » de l'écran du tuto (cadre pivoté)
    ctx2 = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True); pm = ctx2.new_page(); pm.goto('file://' + D + FILE); pm.wait_for_timeout(1200)
    ev(pm, 'window.__vdd.resetCamp(); window.__vdd.goInter(0, null)'); pm.wait_for_timeout(300); bt = [x for x in ev(pm, 'window.__vdd.btns') if x['id'] == 'go'][0]
    sc = ev(pm, 'document.getElementById("wrap").getBoundingClientRect().width/390'); r = ev(pm, 'JSON.parse(JSON.stringify(document.getElementById("wrap").getBoundingClientRect()))')
    lx, ly = (bt['x'] + bt['w']/2)*sc, (bt['y'] + bt['h']/2)*sc; pm.touchscreen.tap(r['right'] - ly, r['top'] + lx); pm.wait_for_timeout(400)
    check(ev(pm, 'window.__vdd.state') == 'play' and ev(pm, 'window.__vdd.levelN') == 0, 'mobile (cadre pivoté) : le tap sur « C’est parti » lance le tuto'); ctx2.close()
    check(not errs, 'aucune erreur JS (campagne) ' + str(errs[:3]))
    b.close()
print('RESULT', 'PASS' if ok else 'FAIL')
