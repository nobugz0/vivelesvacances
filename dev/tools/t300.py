"""Proto 3 : vol, vent, tempête, course, campagne enchaînée (cartes, bonus cumulables). Démarrage, les deux commandes, collecte, contacts, atterrissage, limite d'altitude, menu de réglage, fin de vol."""
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
    pg.goto('file://' + D + FILE); pg.wait_for_timeout(1200); ev(pg, 'document.getElementById(\"ttests\").hidden = false')
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
        cd = ev(pg, 'window.__vdd.card')
        if cd and cd['t'] > 0.5 and cd['kind'] in ('msg', 'theme'): ev(pg, 'window.__vdd.closeCard()')   # le bot ne ferme que les cartes du vol ; la girouette, c'est au test de la voir
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
    p0 = ev(pg, 'window.__vdd.poll'); ev(pg, 'window.__vdd.addJourno("glider", window.__vdd.px + 420, window.__vdd.y - (46 + 28 + 20))'); pg.wait_for_timeout(2500)
    check(abs(ev(pg, 'window.__vdd.poll') - p0) < 0.001, 'un journaliste qui passe sans contact ne change pas les sondages (plus de gain à la distance ni au frôlement)')
    h0 = ev(pg, 'window.__vdd.stats.hits'); ev(pg, 'window.__vdd.addJourno("glider", window.__vdd.px + 420, window.__vdd.y)'); pg.wait_for_timeout(2500)
    check(ev(pg, 'window.__vdd.stats.hits') == h0 + 1 and abs(ev(pg, 'window.__vdd.poll') - (p0 - ev(pg, 'window.__vdd.P.hitPoll'))) < 0.001, 'au contact : −hitPoll (%.2f -> %.2f)' % (p0, ev(pg, 'window.__vdd.poll')))
    w = ev(pg, 'window.__vdd.world'); check(w['camFx'] > 1.15 and w['VWW'] < w['VWW0'], 'en vol, la caméra est rapprochée (camFx %.2f, bord droit %.0f < %.0f)' % (w['camFx'], w['VWW'], w['VWW0']))
    # la bande du score (HUD_H px écran) n'est pas navigable : au plafond, le corps de Marine (py - 60) reste sous la bande, à tous les zooms du jeu (vol et course)
    for z in (ev(pg, 'window.__vdd.P.camFly'), ev(pg, 'window.__vdd.P.camChase')):
        top = (ev(pg, 'window.__vdd.P.ceil') - 60)*w['Z']*z; check(top >= ev(pg, 'window.__vdd.HUD_H'), 'zone du score réservée : au plafond, Marine commence à %.0f px écran, sous la bande de %d px (zoom %.2f)' % (top, ev(pg, 'window.__vdd.HUD_H'), z))
    # archétypes : au niveau 1, ni hélico ni trampoline ; au niveau 4, le trampoliniste et le jet-ski arrivent, le jet-ski se cale sous Marine
    ev(pg, 'window.__vdd.P.level = 1; window.__vdd.startTestFly()'); seen = set(); t0 = time.time()
    while time.time() - t0 < 16: seen |= set(j['kind'] for j in ev(pg, 'window.__vdd.journos') if j['kind'] != 'etr'); pg.wait_for_timeout(300)
    check('heli' not in seen and 'tramp' not in seen and 'jet' not in seen and 'boat' in seen, 'niveau 1 : barques et deltaplanes seulement (%s)' % sorted(seen))
    ev(pg, 'window.__vdd.P.level = 4; window.__vdd.startTestFly()'); pg.wait_for_timeout(300); ev(pg, 'window.__vdd.clearField(); window.__vdd.addJourno("tramp", window.__vdd.px + 420, 0); window.__vdd.addJourno("jet", window.__vdd.px + 700, 0)'); seen = set(); t0 = time.time(); held = 0
    while time.time() - t0 < 8 and held == 0:
        js = ev(pg, 'window.__vdd.journos'); seen |= set(j['kind'] for j in js); ev(pg, 'window.__vdd.hold(window.__vdd.y > 300)')
        if any(j['kind'] == 'jet' and abs(j['x'] - ev(pg, 'window.__vdd.px') - 60) < 3 for j in js): held += 1
        pg.wait_for_timeout(150)
    ev(pg, 'window.__vdd.hold(false)'); check('tramp' in seen and 'jet' in seen and held > 0, 'niveau 4 : trampoliniste et jet-ski présents, le jet-ski se cale sous Marine (%s, %d)' % (sorted(seen), held))
    ev(pg, 'window.__vdd.P.level = 1')
    # bot sur une vraie partie
    ev(pg, 'window.__vdd.startTestFly()'); pg.wait_for_timeout(300); bot(pg, 20, False)
    st = ev(pg, 'window.__vdd.stats'); print('   bot appui 20 s :', st, 'poll', round(ev(pg, 'window.__vdd.poll'), 2))
    check(st['coins'] > 40, 'le bot ramasse des pièces (%d)' % st['coins'])
    check(ev(pg, 'window.__vdd.boatN') < 3 or st['themeBoats'] >= 1, 'une barque sur trois porte le thème de la séquence (%d barques, %d du thème)' % (ev(pg, 'window.__vdd.boatN'), st['themeBoats']))
    pg.screenshot(path=D + 'p3_tap_bot.png')
    # journalistes : une partie seulement crie une question, jamais deux fois la même d'affilée ; une barque muette sautée vaut une réplique à Marine
    qs = ev(pg, 'window.__vdd.qLog'); nn = [q for q in qs if q]
    check(len(qs) >= 3 and 0 < len(nn) < len(qs) and all(nn[i] != nn[i + 1] for i in range(len(nn) - 1)) and len(set(nn[:6])) == len(nn[:6]), 'journalistes : %d sur %d ont une question, les six premières toutes différentes, jamais la même deux fois de suite' % (len(nn), len(qs)))
    ev(pg, 'window.__vdd.startTestFly()'); pg.wait_for_timeout(300)   # un vol neuf : le précédent touche à sa fin (26 s)
    ev(pg, 'window.__vdd.clearField(); window.__vdd.setY(window.__vdd.P.ceil + 60); window.__vdd.hold(true); window.__vdd.addJourno("boat", window.__vdd.px + 300, 0, true)'); t0 = time.time(); mb = None
    while time.time() - t0 < 3 and not mb: mb = ev(pg, 'window.__vdd.mBubble'); pg.wait_for_timeout(50)
    ev(pg, 'window.__vdd.hold(false)'); check(mb is not None, 'Marine saute une barque muette : elle réplique (« %s »)' % mb); pg.screenshot(path=D + 'p3_phrase.png')
    # tout coûte des sondages : sous pollFall Marine tombe de sa planche ; frapper un étranger rapporte et la remonte
    ev(pg, 'window.__vdd.clearField(); window.__vdd.hold(false)'); pg.wait_for_timeout(1800); ev(pg, 'window.__vdd.setPoll(17.4); window.__vdd.addJourno("boat", window.__vdd.px + 260, 0, true)'); t0 = time.time()
    while time.time() - t0 < 4 and not ev(pg, 'window.__vdd.fallen'): pg.wait_for_timeout(50)
    check(ev(pg, 'window.__vdd.fallen') and abs(ev(pg, 'window.__vdd.poll') - 16.4) < 0.01, 'un contact sous %.0f %% : Marine tombe de sa planche (%.1f %%)' % (ev(pg, 'window.__vdd.P.pollFall'), ev(pg, 'window.__vdd.poll'))); pg.screenshot(path=D + 'p3_fallen.png')
    etr0 = ev(pg, 'window.__vdd.stats.etr'); ev(pg, 'window.__vdd.clearField(); window.__vdd.addJourno("etr", window.__vdd.px + 420, 0)'); t0 = time.time(); cry = None
    while time.time() - t0 < 4 and ev(pg, 'window.__vdd.stats.etr') == etr0: cry = cry or ev(pg, 'window.__vdd.mBubble'); pg.wait_for_timeout(50)
    check(ev(pg, 'window.__vdd.stats.etr') == etr0 + 1 and abs(ev(pg, 'window.__vdd.poll') - 17.4) < 0.01 and not ev(pg, 'window.__vdd.fallen') and cry is not None, 'un étranger frappé : Marine l’a désigné (« %s »), +%.0f pt, elle remonte sur sa planche' % (cry, ev(pg, 'window.__vdd.P.etrGain')))
    pg.wait_for_timeout(300); js = ev(pg, 'window.__vdd.journos'); check(any(j['kind'] == 'etr' and j['fall'] is not None and j['fall'] > 0 for j in js), 'l’étranger frappé tombe à l’eau'); pg.screenshot(path=D + 'p3_etr.png')
    ev(pg, 'window.__vdd.resetCamp(); window.__vdd.startLevel(2)'); pg.wait_for_timeout(600); cd = ev(pg, 'window.__vdd.card')
    check(cd is None and ev(pg, 'window.__vdd.levelN') == 2, 'au départ d\'une séquence (campagne) : plus de carton de début de séquence'); pg.screenshot(path=D + 'p3_theme.png')
    pg.wait_for_timeout(7700); cols = {}
    for c in ev(pg, 'window.__vdd.coinsList'): cols.setdefault(round(c['x']), set()).add(round(c['y']))
    mx_rows = max((len(v) for v in cols.values()), default=0); check(0 < mx_rows <= 3, 'les pièces vont par 1 à 3 rangées, jamais plus (max %d)' % mx_rows)
    dur = ev(pg, 'window.__vdd.P.flight*0.85'); ev(pg, 'window.__vdd.setT(%f)' % (dur - 0.3)); pg.wait_for_timeout(1200); cd = ev(pg, 'window.__vdd.card')
    check(cd and cd['kind'] == 'vane' and ev(pg, 'window.__vdd.phase') == 'vane', 'fin du vol (séquence 2 : %.1f s) -> la carte de la girouette : la course vient avant le scandale' % dur); pg.screenshot(path=D + 'p3_recap.png')
    check(len(ev(pg, 'window.__vdd.journos')) == 0, 'plus aucun obstacle à l\'écran quand la course commence'); ev(pg, 'window.__vdd.tap("title")'); pg.wait_for_timeout(200); ev(pg, 'window.__vdd.startTestFly()'); pg.wait_for_timeout(300)
    # menu de réglage
    pg.click('#gearBtn'); pg.wait_for_timeout(200)
    check(not ev(pg, 'document.getElementById("debug").hidden'), 'la roue crantée ouvre le menu de réglage')
    n = ev(pg, 'document.querySelectorAll("#debug input[type=range]").length'); check(n == len([1 for sp in ev(pg, 'window.__vdd.PSPEC') if sp['g'] != 'Vent']), '%d curseurs, un par paramètre hors vent' % n)
    ev(pg, '(() => { const i = document.getElementById("dbg_cam"); i.value = 0.5; i.dispatchEvent(new Event("input")); })()'); pg.wait_for_timeout(50)
    w2 = ev(pg, 'window.__vdd.world'); check(abs(w2['Z'] - 0.5) < 1e-6 and w2['WH'] == 780, 'le curseur caméra change le monde (%s)' % w2)
    pg.click('#dbgSave'); pg.wait_for_timeout(300); msg = ev(pg, 'document.getElementById("dbgMsg").textContent'); check('Enregistré' in msg, 'sauvegarde : ' + msg)
    pg.screenshot(path=D + 'p3_debug.png')
    ev(pg, '(() => { const i = document.getElementById("dbg_cam"); i.value = 0.6; i.dispatchEvent(new Event("input")); })()'); pg.click('#dbgSave'); pg.wait_for_timeout(300)
    pg.reload(); pg.wait_for_timeout(1200); ev(pg, 'document.getElementById("ttests").hidden = false'); check(abs(ev(pg, 'window.__vdd.P.cam') - 0.6) < 1e-6, 'les réglages sauvegardés reviennent après rechargement')
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
    for lvl, kind, dodge in [(1, 'justice', True), (3, 'rn', False), (4, 'bard', True)]:   # ordre des séquences : Inéligibilité, Europe, Retraites, Énergie, Budget
        b, pg, errs = boot(p, 'tap'); pg.click('#closeBtn'); pg.wait_for_timeout(200); ev(pg, 'window.__vdd.P.level = %d' % lvl); pg.click('#stormBtn'); pg.wait_for_timeout(800)
        e = ev(pg, 'window.__vdd.emitter'); check(ev(pg, 'window.__vdd.phase') == 'intro' and e and e['kind'] == kind and ev(pg, 'window.__vdd.t') < 1, 'niveau %d : « Tester la tempête » ouvre la carte directement, émetteur %s' % (lvl, e and e['kind']))
        y0 = ev(pg, 'window.__vdd.y'); pg.wait_for_timeout(600)
        ev(pg, 'window.__vdd.tap("card")'); pg.wait_for_timeout(100)
        check(ev(pg, 'window.__vdd.phase') == 'storm' and abs(ev(pg, 'window.__vdd.y') - y0) < 1, 'le bouton de la carte reprend le jeu, qui était en pause')
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
            ev(pg, '''() => new Promise(res => { const v = window.__vdd; const step = () => { if (v.state !== 'play'){ v.hold(false); res(); return; } if (v.card){ if (v.card.t > 0.5) v.closeCard(); requestAnimationFrame(step); return; }
              const px = v.px, y = v.y, P = v.P, top = P.ceil + 60, bot = P.yMax; const th = [];
              for (const c of v.pansList){ const tc = (c.x - px)/Math.max(1, -c.vx), t = tc + Math.max(0, c.delay); if (t < 1.4 && c.x > px - 30) th.push(c.y + c.vy*tc + 0.5*c.g*tc*tc); }
              let best = y, bestD = -1; for (let k = 0; k <= 8; k++){ const cy = top + (bot - top)*k/8; const d = th.length ? Math.min(...th.map(t => Math.abs(t - cy))) : 1e9; const score = d - Math.abs(cy - y)*0.15; if (score > bestD){ bestD = score; best = cy; } }
              if (!th.length) best = v.onWater ? y : Math.max(y, bot - 120);
              const up = best < y - 8 && (v.wind > 0.05 || v.onWater); v.hold(up); requestAnimationFrame(step); }; requestAnimationFrame(step); })''')
        else:
            t0 = time.time()
            while time.time() - t0 < 55 and ev(pg, 'window.__vdd.state') == 'play':
                cd = ev(pg, 'window.__vdd.card')
                if cd and cd['t'] > 0.5: ev(pg, 'window.__vdd.closeCard()')
                pg.wait_for_timeout(100)
        pg.mouse.up(); print('   tempête niveau %d (%s) : casseroles %d, sondages %.1f, raison %s' % (lvl, 'esquive' if dodge else 'immobile sur l\'eau', ev(pg, 'window.__vdd.stats.cass'), ev(pg, 'window.__vdd.poll'), ev(pg, 'window.__vdd.endReason')))
        check(ev(pg, 'window.__vdd.state') == 'recap' and ev(pg, 'window.__vdd.endReason') in ('done', 'out'), 'la tempête se termine (délai ou éliminée)')
        if not dodge: check(ev(pg, 'window.__vdd.stats.cass') >= 3, 'rester sur l\'eau sans bouger ne suffit pas : les cloches sur Marine touchent (%d)' % ev(pg, 'window.__vdd.stats.cass'))
        if dodge: check(ev(pg, 'window.__vdd.endReason') == 'done', 'un bot qui esquive par couloirs traverse la tempête (%d casseroles)' % ev(pg, 'window.__vdd.cass'))
        check(not errs, 'aucune erreur JS (tempête %d) ' % lvl + str(errs[:3]))
        b.close()
    b, pg, errs = boot(p, 'tap'); ev(pg, 'window.__vdd.startTest()'); pg.wait_for_timeout(800); ev(pg, 'window.__vdd.beginStormPlay(); window.__vdd.setPoll(15.2)')
    t0 = time.time()
    while time.time() - t0 < 25 and ev(pg, 'window.__vdd.state') == 'play': pg.wait_for_timeout(100)
    check(ev(pg, 'window.__vdd.endReason') == 'out' and ev(pg, 'window.__vdd.poll') < ev(pg, 'window.__vdd.P.pollOut'), 'une casserole sous %.0f %% : éliminée -> on recommence le chapitre' % ev(pg, 'window.__vdd.P.pollOut')); pg.screenshot(path=D + 'p3_out.png'); b.close()
    def wait_phase(pg, want, secs):
        t0 = time.time()
        while time.time() - t0 < secs and ev(pg, 'window.__vdd.phase') != want: pg.wait_for_timeout(100)
        return ev(pg, 'window.__vdd.phase')
    def wait_state(pg, want, secs):
        t0 = time.time()
        while time.time() - t0 < secs and ev(pg, 'window.__vdd.state') not in want: pg.wait_for_timeout(100)
        return ev(pg, 'window.__vdd.state')
    def wait_card(pg, kind, secs):
        t0 = time.time()
        while time.time() - t0 < secs:
            c = ev(pg, 'window.__vdd.card')
            if c and c['kind'] == kind: pg.wait_for_timeout(500); return c
            pg.wait_for_timeout(100)
        return None
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
    check(ev(pg, 'window.__vdd.world.camFx') > 1.22, 'la caméra s\'est rapprochée à chaque cercle (camFx %.2f)' % ev(pg, 'window.__vdd.world.camFx'))
    px1 = ev(pg, 'window.__vdd.px'); step = ev(pg, 'window.__vdd.P.ringStep'); need = ev(pg, 'window.__vdd.P.ringNeed'); ratio = (c['xCatch'] - c['x0'])/(c['oxCatch'] - 40 - c['x0'])
    check(step*(need - 1)/100 - 0.03 < ratio < step*need/100 + 0.03, 'Marine a avancé d\'un petit cran par cercle (%d %% × %d cercles : %.0f %% de la distance au moment de la capture, x %.0f -> %.0f)' % (step, need, ratio*100, c['x0'], c['xCatch']))
    check(ev(pg, 'window.__vdd.wind') <= 1, 'pendant la course, le vol compte comme d\'habitude (jauge %.2f)' % ev(pg, 'window.__vdd.wind'))
    pg.screenshot(path=D + 'p3_chase.png'); t0 = time.time()
    while time.time() - t0 < 3 and not ev(pg, 'window.__vdd.card'): pg.wait_for_timeout(50)
    px2 = ev(pg, 'window.__vdd.px'); cd = ev(pg, 'window.__vdd.card'); check(cd and cd['kind'] == 'position' and px2 > px1 + 150 and ev(pg, 'window.__vdd.stats.gold'), 'au compte, Marine fonce sur la girouette (x %.0f -> %.0f) puis la carte de la volte-face' % (px1, px2)); pg.wait_for_timeout(500); pg.screenshot(path=D + 'p3_position.png')
    ev(pg, 'window.__vdd.closeCard()'); pg.wait_for_timeout(400); check(ev(pg, 'window.__vdd.phase') == 'cruise' and ev(pg, 'window.__vdd.chase') is None, 'après la carte : on navigue un peu (phase cruise)')
    st = wait_state(pg, ('recap',), 6); check(st == 'recap' and ev(pg, 'window.__vdd.endReason') == 'done', 'navigation de cruiseT s -> fin du niveau (récap en mode test)')
    # sans rien faire : les cercles sont manqués, la girouette s'envole après le dernier, le niveau est réussi sans volte-face
    ev(pg, 'window.__vdd.startTestChase()'); pg.wait_for_timeout(300); ev(pg, 'window.__vdd.P.ringTotal = 4'); t0 = time.time(); seen = None
    while time.time() - t0 < 16 and ev(pg, 'window.__vdd.state') == 'play':
        c = ev(pg, 'window.__vdd.chase'); ev(pg, 'window.__vdd.hold(window.__vdd.y > 330)')   # reste à mi-hauteur, appui maintenu pendant l'envol
        if c and c['leaving'] and seen is None: pg.wait_for_timeout(900); seen = ev(pg, 'window.__vdd.chase'); pg.screenshot(path=D + 'p3_flyaway.png')
        pg.wait_for_timeout(100)
    pg.mouse.up(); c = ev(pg, 'window.__vdd.chase')
    check(seen is not None and seen['camFx'] < 0.95, 'tous les cercles lâchés sans le compte : la girouette s\'envole, la caméra recule (camFx %.2f)' % (seen['camFx'] if seen else 1))
    check(ev(pg, 'window.__vdd.state') == 'recap' and ev(pg, 'window.__vdd.endReason') == 'done' and not ev(pg, 'window.__vdd.stats.gold'), 'la girouette s\'envole, pas de carte, navigation puis niveau fini sans volte-face')
    ev(pg, 'window.__vdd.P.ringTotal = 8')
    # menu à onglets, largeur <= 25 %
    pg.click('#gearBtn'); pg.wait_for_timeout(200)
    w = ev(pg, 'document.getElementById("debug").getBoundingClientRect().width'); W = ev(pg, 'window.innerWidth'); check(w <= W*0.25 + 1, 'menu de réglage : %.0f px sur %d (%.0f %%)' % (w, W, 100*w/W))
    tabs = ev(pg, 'Array.from(document.querySelectorAll("#debug .tabs button")).map(b => b.textContent)'); check(tabs == ['Commun', 'Appui', 'Tempête', 'Course'], 'onglets : ' + ', '.join(tabs))
    pg.click('#debug .tabs button[data-tab=Course]'); vis = ev(pg, 'Array.from(document.querySelectorAll("#debug .tab")).filter(t => !t.hidden).map(t => t.dataset.tab)'); check(vis == ['Course'], 'un seul onglet visible à la fois (%s)' % vis)
    pg.screenshot(path=D + 'p3_menu.png')
    check(not errs, 'aucune erreur JS (course) ' + str(errs[:3]))
    b.close()

    # E. la campagne enchaînée : menu, tuto direct avec ses cartes, carte girouette, carte position, navigation, écran des bonus (cumulables), arrivée du bateau, carte scandale, perte et reprise, sauvegarde, fin
    b = p.chromium.launch(args=['--allow-file-access-from-files', '--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1280, 'height': 720})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append('console.' + m.type + ': ' + m.text) if m.type == 'error' else None)
    pg.goto('file://' + D + FILE); pg.wait_for_timeout(1200); ev(pg, 'document.getElementById(\"ttests\").hidden = false'); ev(pg, 'window.__vdd.resetCamp()'); pg.reload(); pg.wait_for_timeout(1200); ev(pg, 'document.getElementById("ttests").hidden = false')
    check(ev(pg, 'document.getElementById("continueBtn")') is None and not ev(pg, 'document.getElementById("newBtn").hidden') and ev(pg, 'document.getElementById("tutoChk").checked'), 'menu : « Nouvelle campagne » et la case « Tuto » cochée, plus de « Continuer »')
    ev(pg, 'window.__vdd.P.tutoFlight = 26'); pg.click('#newBtn'); pg.wait_for_timeout(500); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]; cd = ev(pg, 'window.__vdd.card')
    check(ev(pg, 'window.__vdd.state') == 'play' and ev(pg, 'window.__vdd.levelN') == 0 and ev(pg, 'window.__vdd.mode') == 'camp' and cd and cd['kind'] == 'msg' and 'skipTuto' not in ids and 'card' in ids and ev(pg, 'window.__vdd.t') < 0.3, 'nouvelle campagne : le tuto démarre tout de suite, première carte, bouton Compris (pas de « Passer le tuto »), jeu en attente')
    pg.screenshot(path=D + 'p3_tuto_msg1.png')
    pg.mouse.move(640, 500); pg.mouse.down(); pg.wait_for_timeout(100); pg.mouse.up(); pg.wait_for_timeout(200); check(ev(pg, 'window.__vdd.card') is None and ev(pg, 'window.__vdd.onWater'), 'le tap ferme la carte sans faire décoller Marine')
    t0 = time.time(); c2 = None
    while time.time() - t0 < 18 and not c2:
        cd = ev(pg, 'window.__vdd.card'); c2 = cd if cd and cd['kind'] == 'msg' else None
        cl = ev(pg, 'window.__vdd.coinsList.filter(c => c.x > window.__vdd.px - 20).sort((a, b) => a.x - b.x)[0]'); ev(pg, 'window.__vdd.hold(%s)' % ('true' if cl and ev(pg, 'window.__vdd.y') > cl['y'] else 'false')); pg.wait_for_timeout(60)
    ev(pg, 'window.__vdd.hold(false)'); check(c2 and 'caisse noire' in (c2['text'] or '') and ev(pg, 'window.__vdd.stats.coins') >= 3, 'après les premières pièces attrapées (%d) : carte « caisse noire »' % ev(pg, 'window.__vdd.stats.coins')); pg.screenshot(path=D + 'p3_tuto_msg2.png'); ev(pg, 'window.__vdd.closeCard()')
    # d'abord les pièces seules ; huit ramassées -> trois étrangers (carte au premier en vue) ; puis les journalistes (carte au premier en vue) ; puis la girouette
    t0 = time.time(); seenJ = False
    while time.time() - t0 < 24 and not (ev(pg, 'window.__vdd.card') and 'étranger' in (ev(pg, 'window.__vdd.card')['text'] or '')):
        cd = ev(pg, 'window.__vdd.card')
        if cd and cd['t'] > 0.5 and 'étranger' not in (cd['text'] or ''): ev(pg, 'window.__vdd.closeCard()')   # la carte « envol » passe avant
        seenJ = seenJ or ev(pg, 'window.__vdd.journos.some(j => j.kind !== "etr" && j.x < window.__vdd.world.VWW - 80)'); pg.wait_for_timeout(100)
    c3 = ev(pg, 'window.__vdd.card'); check(not seenJ and c3 and 'étranger' in (c3['text'] or ''), 'tuto : les pièces seules (%d ramassées), pas de journaliste, puis la carte « étrangers » au premier en vue (%.1f s)' % (ev(pg, 'window.__vdd.stats.coins'), ev(pg, 'window.__vdd.t'))); pg.screenshot(path=D + 'p3_tuto_msg3.png'); ev(pg, 'window.__vdd.closeCard()')
    t0 = time.time(); c4 = None
    while time.time() - t0 < 20 and not c4:
        cd = ev(pg, 'window.__vdd.card')
        if cd and 'interviews' in (cd['text'] or ''): c4 = cd
        elif cd and cd['t'] > 0.5: ev(pg, 'window.__vdd.closeCard()')
        ev(pg, 'window.__vdd.hold(window.__vdd.y > 420)'); pg.wait_for_timeout(100)
    ev(pg, 'window.__vdd.hold(false)'); check(c4 is not None and ev(pg, 'window.__vdd.tutoStage') == 2, 'tuto : après les trois étrangers, un journaliste arrive et sa carte s\'affiche (%.1f s)' % ev(pg, 'window.__vdd.t')); pg.screenshot(path=D + 'p3_tuto_msg4.png'); ev(pg, 'window.__vdd.closeCard()')
    t0 = time.time(); cv = None
    while time.time() - t0 < 40 and not cv:
        ev(pg, 'window.__vdd.setPoll(40)'); bot(pg, 1, False); cd = ev(pg, 'window.__vdd.card')   # le bot ne sait pas éviter : on le garde dans les sondages
        if cd and cd['kind'] == 'vane': cv = cd
        elif cd and cd['t'] > 0.5: ev(pg, 'window.__vdd.closeCard()')
    check(cv is not None and ev(pg, 'window.__vdd.phase') == 'vane' and ev(pg, 'window.__vdd.emitter') is None, 'fin du vol du tuto (trois étapes passées, champ vide) : pas de tempête, carte de la girouette (%.1f s)' % ev(pg, 'window.__vdd.t')); pg.screenshot(path=D + 'p3_vane_card.png')
    ev(pg, 'window.__vdd.closeCard()'); pg.wait_for_timeout(300); check(ev(pg, 'window.__vdd.phase') == 'chase', 'la carte fermée lance la course')
    ev(pg, RING_BOT); c = ev(pg, 'window.__vdd.chase'); check(c['caught'], 'course du tuto attrapée par le bot (%.1f s)' % c['t'])
    cp = wait_card(pg, 'position', 3); check(cp is not None, 'girouette attrapée : carte de la volte-face (ancienne position barrée, nouvelle)'); pg.screenshot(path=D + 'p3_position_tuto.png')
    ev(pg, 'window.__vdd.closeCard()'); t0 = time.time(); tr = False
    while time.time() - t0 < 10 and not tr: tr = ev(pg, 'window.__vdd.trans'); pg.wait_for_timeout(100)
    check(ev(pg, 'window.__vdd.phase') == 'cruise' and ev(pg, 'window.__vdd.gate') is None and tr, 'après la navigation du tuto : pas de porte, l’iris se referme'); pg.screenshot(path=D + 'p3_gate.png')
    # après le tuto, la séquence 1 démarre directement (le QG n'a de sens qu'après une séquence) ; le QG est testé en y allant par le hook
    wait_state(pg, ('play',), 6); pg.wait_for_timeout(1200); cd = {'kind': 'none'} if ev(pg, 'window.__vdd.levelN') == 1 else None; r = ev(pg, 'window.__vdd.camp.levels[0]'); coins0 = ev(pg, 'window.__vdd.camp.coins')
    check(cd is not None and ev(pg, 'window.__vdd.state') == 'play' and ev(pg, 'window.__vdd.levelN') == 1 and ev(pg, 'window.__vdd.camp.cur') == 1 and r and r['done'] and r['gold'] and coins0 > 0, 'après le tuto : la séquence 1 directement, pièces en réserve (%d)' % coins0)
    ev(pg, 'window.__vdd.goInter(1)'); st = wait_state(pg, ('inter',), 3); pg.wait_for_timeout(800)
    check(st == 'inter' and ev(pg, 'window.__vdd.interStep') == 1 and ev(pg, 'window.__vdd.levelN') == 1, 'le QG (par le hook) : étape 1, les bonus de la séquence 1')
    ev(pg, 'window.__vdd.camp.coins = 0; window.__vdd.saveCamp()'); pg.wait_for_timeout(150); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]; check('next' in ids and ids.count('locked') == 3 and 'go' not in ids, 'étape 1 : trois bonus, sans or : « Pas assez d’or » partout, Suivant'); pg.screenshot(path=D + 'p3_inter1.png')
    ev(pg, 'window.__vdd.camp.coins += 800; window.__vdd.saveCamp()'); pg.wait_for_timeout(150); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]
    check('buy:pump' in ids and 'buy:kevlar' in ids, 'avec des pièces : pompe et kevlar achetables')
    c0 = ev(pg, 'window.__vdd.camp.coins'); ev(pg, 'window.__vdd.tap("buy:kevlar")'); pg.wait_for_timeout(150); ev(pg, 'window.__vdd.tap("buy:pump")'); pg.wait_for_timeout(150); bs = ev(pg, 'window.__vdd.bonuses'); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]
    check(ev(pg, 'window.__vdd.state') == 'inter' and bs.get('kevlar') and bs.get('pump') and ev(pg, 'window.__vdd.camp.coins') == c0 - 320 and 'buy:kevlar' in ids and 'buy:pump' in ids, 'deux bonus activés à la suite (−320), l’écran reste, les boutons passent à « Désactiver »')
    ev(pg, 'window.__vdd.tap("buy:pump")'); pg.wait_for_timeout(150); check(not ev(pg, 'window.__vdd.bonuses').get('pump') and ev(pg, 'window.__vdd.camp.coins') == c0 - 200, 'un clic sur un bonus activé le désactive et rembourse (+120)'); ev(pg, 'window.__vdd.tap("buy:pump")'); pg.wait_for_timeout(150); pg.screenshot(path=D + 'p3_inter1_rich.png')
    ev(pg, 'window.__vdd.tap("next")'); pg.wait_for_timeout(700); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]; check(ev(pg, 'window.__vdd.interStep') == 2 and 'buy:votes' in ids and 'go' in ids and 'prev' in ids, 'étape 2 : acheter des voix, Repartir, retour aux bonus'); pg.screenshot(path=D + 'p3_inter1_votes.png')
    e0 = ev(pg, 'window.__vdd.camp.levels[1] ? window.__vdd.camp.levels[1].entry.poll : window.__vdd.P.pollStart'); c1 = ev(pg, 'window.__vdd.camp.coins'); pr = ev(pg, 'window.__vdd.votePrice'); ev(pg, 'window.__vdd.tap("buy:votes")'); pg.wait_for_timeout(150); pr2 = ev(pg, 'window.__vdd.votePrice'); ev(pg, 'window.__vdd.tap("buy:votes")'); pg.wait_for_timeout(150)
    check(ev(pg, 'window.__vdd.state') == 'inter' and ev(pg, 'window.__vdd.camp.coins') == c1 - pr - pr2 and abs(ev(pg, 'window.__vdd.camp.levels[1].entry.poll') - e0 - 2*ev(pg, 'window.__vdd.P.voteGain')) < 0.001 and pr2 > pr, 'acheter des voix deux fois : −%d puis −%d pièces, +%.0f pt à l’entrée du chapitre' % (pr, pr2, 2*ev(pg, 'window.__vdd.P.voteGain')))
    ev(pg, 'window.__vdd.P.flight = 8; window.__vdd.tap("go")'); pg.wait_for_timeout(1300)
    cd = ev(pg, 'window.__vdd.card'); check(ev(pg, 'window.__vdd.state') == 'play' and ev(pg, 'window.__vdd.levelN') == 1 and ev(pg, 'window.__vdd.kevlarLeft') == 3 and not cd, 'C’est parti : séquence 1 lancée avec les deux bonus, carton du thème'); pg.screenshot(path=D + 'p3_chap1_start.png'); ev(pg, 'window.__vdd.closeCard()')
    # la course d'abord : carte girouette, cercles, carte volte-face, respiration ; puis l'arrivée du bateau en approachT s et la carte du scandale
    cv = wait_card(pg, 'vane', 12); check(cv is not None, 'chapitre 1 : la carte de la girouette à la fin du vol'); ev(pg, 'window.__vdd.closeCard()'); wait_phase(pg, 'chase', 3)
    ev(pg, RING_BOT); cp = wait_card(pg, 'position', 4); check(cp is not None, 'chapitre 1 : carte de la volte-face'); ev(pg, 'window.__vdd.closeCard()'); pg.wait_for_timeout(200)
    check(ev(pg, 'window.__vdd.phase') == 'breath', 'après la volte-face, une respiration de vol libre avant le scandale')
    ap = wait_phase(pg, 'approach', 6); pg.wait_for_timeout(300); pxb = ev(pg, 'window.__vdd.px'); check(abs(pxb - max(190, ev(pg, 'window.__vdd.world.VWW0')*0.22)) < 3, 'Marine est revenue à sa place (x %.0f) avant le scandale' % pxb); ex0 = ev(pg, 'window.__vdd.emitter.x'); pg.wait_for_timeout(2000); ap2 = ev(pg, 'window.__vdd.phase'); ex1 = ev(pg, 'window.__vdd.emitter.x'); cs = wait_card(pg, 'scandal', 4)
    check(ap == 'approach' and ap2 == 'approach' and ex0 - ex1 > 150 and cs is not None and ev(pg, 'window.__vdd.emitter.x') < ev(pg, 'window.__vdd.world.VWW0') - 200, 'le bateau arrive par la droite pendant approachT s (x %.0f -> %.0f) ; en place, la carte du scandale' % (ex0, ex1))
    pg.screenshot(path=D + 'p3_intro.png'); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]; check('card' in ids and 'sinfo' in ids, 'carte du scandale : titre, une phrase, un bouton, le « i »')
    ev(pg, 'window.__vdd.tap("sinfo")'); check(ev(pg, 'window.__vdd.infoOpen.page') == 'scandal', 'le « i » ouvre la fiche du scandale'); pg.screenshot(path=D + 'p3_intro_info.png'); ev(pg, 'window.__vdd.tap("infoClose")')
    # perdre : coulée -> on recommence depuis l'état d'entrée, les bonus restent
    e1 = ev(pg, 'window.__vdd.camp.levels[1].entry.poll'); ev(pg, 'window.__vdd.closeCard(); window.__vdd.setPoll(15.2); window.__vdd.setKevlar(0); window.__vdd.hold(false)'); st = wait_state(pg, ('recap',), 30)
    check(st == 'recap' and ev(pg, 'window.__vdd.endReason') == 'out', 'éliminée pendant la tempête (sondages sous %.0f %%)' % ev(pg, 'window.__vdd.P.pollOut')); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]; check('again' in ids and 'title' in ids, 'écran de défaite : Recommencer et Menu'); pg.wait_for_timeout(600); pg.screenshot(path=D + 'p3_out_camp.png')
    ev(pg, 'window.__vdd.tap("again")'); pg.wait_for_timeout(300)
    check(ev(pg, 'window.__vdd.state') == 'play' and abs(ev(pg, 'window.__vdd.poll') - e1) < 0.01 and ev(pg, 'window.__vdd.bonuses').get('kevlar') and ev(pg, 'window.__vdd.levelN') == 1, 'Recommencer : chapitre 1 depuis son état d’entrée (%.1f %%), bonus conservés' % e1)
    # réussir : girouette -> course -> volte-face -> scandale (tempête écourtée) -> accalmie -> navigation -> porte -> QG du chapitre 2
    ev(pg, 'window.__vdd.P.stormMax = 3'); cv = wait_card(pg, 'vane', 14); ev(pg, 'window.__vdd.closeCard()'); wait_phase(pg, 'chase', 3); ev(pg, RING_BOT); cp = wait_card(pg, 'position', 4); pg.screenshot(path=D + 'p3_position1.png'); ev(pg, 'window.__vdd.closeCard()')
    cs = wait_card(pg, 'scandal', 12); check(cv is not None and cp is not None and cs is not None, 'chapitre 1 rejoué : girouette, volte-face, puis le scandale'); ev(pg, 'window.__vdd.closeCard()')
    ph = wait_phase(pg, 'calm', 20); check(ph == 'calm', 'après la tempête : accalmie (l’émetteur a fui, Marine s’en sort)'); pg.wait_for_timeout(600); pg.screenshot(path=D + 'p3_calm.png')
    st = wait_state(pg, ('inter',), 14); r = ev(pg, 'window.__vdd.camp'); l1 = r['levels'][1]; l2 = r['levels'][2]
    check(st == 'inter' and ev(pg, 'window.__vdd.levelN') == 2 and r['cur'] == 2 and l1['done'] and l2 and abs(l2['entry']['poll'] - l1['poll']) < 0.01, 'chapitre 1 réussi : porte, QG du chapitre 2, sondages transmis (%.1f %%)' % l1['poll'])
    check(not ev(pg, 'window.__vdd.bonuses'), 'les bonus sont consommés'); pg.screenshot(path=D + 'p3_inter2.png')
    # sauvegarde : rechargement de la page, « Continuer » reprend à l'écran des bonus du chapitre 2
    pg.reload(); pg.wait_for_timeout(1200); ev(pg, 'document.getElementById("ttests").hidden = false'); r = ev(pg, 'window.__vdd.camp')
    check(r['cur'] == 2 and r['levels'][1]['done'] and r['coins'] > 0, 'la campagne est rechargée (chapitre %d, %d pièces)' % (r['cur'], r['coins']))
    # fin de campagne : chapitre 5, bureau de vote, bilan final
    ev(pg, 'window.__vdd.setCur(5); window.__vdd.goInter(5)'); pg.wait_for_timeout(200); check(ev(pg, 'window.__vdd.state') == 'inter' and ev(pg, 'window.__vdd.levelN') == 5, 'écran des bonus du chapitre 5')
    ev(pg, 'window.__vdd.P.flight = 6; window.__vdd.P.stormMax = 3; window.__vdd.setInterStep(2); window.__vdd.tap("go")'); cv = wait_card(pg, 'vane', 16); ev(pg, 'window.__vdd.closeCard()'); wait_phase(pg, 'chase', 3)
    ev(pg, RING_BOT); cp = wait_card(pg, 'position', 4); ev(pg, 'window.__vdd.closeCard()'); cs = wait_card(pg, 'scandal', 12); ev(pg, 'window.__vdd.closeCard()'); st = wait_state(pg, ('final',), 24); check(cs is not None and cv is not None and cp is not None and st == 'final', 'chapitre 5 fini : séquence finale (atterrissage, bureau de vote)')
    pg.wait_for_timeout(1500); pg.screenshot(path=D + 'p3_final_booth.png'); st = wait_state(pg, ('finalRecap',), 8)
    bo = ev(pg, 'window.__vdd.booth'); check(st == 'finalRecap' and bo and bo['reached'] and ev(pg, 'window.__vdd.onWater') and ev(pg, 'window.__vdd.camp.cur') == 6, 'Marine posée, bureau de vote atteint -> bilan final, campagne terminée (%.1f s)' % ev(pg, 'window.__vdd.finalT'))
    pg.screenshot(path=D + 'p3_final.png'); ids = [x['id'] for x in ev(pg, 'window.__vdd.btns')]; check('newCamp' in ids and 'title' in ids, 'bilan final : Nouvelle campagne et Menu')
    ev(pg, 'window.__vdd.tap("title")'); pg.wait_for_timeout(200); check(ev(pg, 'window.__vdd.state') == 'title', 'menu après la fin')
    # menu : un bouton par chapitre lance le chapitre directement
    ev(pg, 'window.__vdd.resetCamp()'); pg.click('#chapRow button[data-ch="3"]'); pg.wait_for_timeout(400); check(ev(pg, 'window.__vdd.state') == 'play' and ev(pg, 'window.__vdd.levelN') == 3 and ev(pg, 'window.__vdd.mode') == 'camp', 'menu : « Séq. 3 » lance la séquence 3 directement'); ev(pg, 'window.__vdd.tap("title")')
    # mobile : tap réel sur « C'est parti » de l'écran des bonus (cadre pivoté)
    ctx2 = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True); pm = ctx2.new_page(); pm.goto('file://' + D + FILE); pm.wait_for_timeout(1200)
    ev(pm, 'window.__vdd.resetCamp(); window.__vdd.setCur(1); window.__vdd.goInter(1); window.__vdd.setInterStep(2)'); pm.wait_for_timeout(300); bt = [x for x in ev(pm, 'window.__vdd.btns') if x['id'] == 'go'][0]
    sc = ev(pm, 'document.getElementById("wrap").getBoundingClientRect().width/390'); r = ev(pm, 'JSON.parse(JSON.stringify(document.getElementById("wrap").getBoundingClientRect()))')
    lx, ly = (bt['x'] + bt['w']/2)*sc, (bt['y'] + bt['h']/2)*sc; pm.touchscreen.tap(r['right'] - ly, r['top'] + lx); pm.wait_for_timeout(1300)
    check(ev(pm, 'window.__vdd.state') == 'play' and ev(pm, 'window.__vdd.levelN') == 1, 'mobile (cadre pivoté) : le tap sur « C’est parti » lance le chapitre 1'); ctx2.close()
    check(not errs, 'aucune erreur JS (campagne) ' + str(errs[:3]))
    b.close()
print('RESULT', 'PASS' if ok else 'FAIL')
