"""Proto 3, étape 1 : vol jouable. Démarrage, les deux commandes, collecte, contacts, atterrissage, limite d'altitude, menu de réglage, fin de vol."""
import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
from playwright.sync_api import sync_playwright
import time, sys
D = GAME
FILE = sys.argv[1] if len(sys.argv) > 1 else 'proto3.html'
def ev(pg, s): return pg.evaluate(s)
def boot(p, ctrl):
    b = p.chromium.launch(args=['--allow-file-access-from-files', '--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1280, 'height': 720})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append('console.' + m.type + ': ' + m.text) if m.type == 'error' else None)
    pg.goto('file://' + D + FILE); pg.wait_for_timeout(1200)
    ev(pg, 'window.__vdd.setCtrl(%r)' % ctrl); pg.click('#startBtn'); pg.wait_for_timeout(600)
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
            d = max(-1, min(1, (y - ty)/140.0)); pg.mouse.move(900, 360 - d*290)
        else:
            if ty < y - 8: pg.mouse.down()
            else: pg.mouse.up()
        pg.wait_for_timeout(40)
    pg.mouse.up()
with sync_playwright() as p:
    # A. appui
    b, pg, errs = boot(p, 'tap')
    check(ev(pg, 'window.__vdd.state') == 'play' and ev(pg, 'window.__vdd.ctrl') == 'tap', 'démarrage en mode appui')
    w = ev(pg, 'window.__vdd.world'); print('   monde', w, 'yMax', ev(pg, 'window.__vdd.P.yMax'))
    check(ev(pg, 'window.__vdd.onWater'), 'Marine démarre posée sur l\'eau')
    y0 = ev(pg, 'window.__vdd.y'); pg.mouse.move(640, 360); pg.mouse.down(); pg.wait_for_timeout(700); y1 = ev(pg, 'window.__vdd.y')
    check(y1 < y0 - 60, 'appui = monte (%.0f -> %.0f)' % (y0, y1))
    pg.mouse.up(); pg.wait_for_timeout(1400); y2 = ev(pg, 'window.__vdd.y')
    check(y2 > y1 + 60, 'relâché = inversion, plané puis chute (%.0f -> %.0f)' % (y1, y2))
    # atterrissage parfait (mode appui) : on monte, on relâche, et on redonne l'input sous landH de hauteur
    l0 = ev(pg, 'window.__vdd.stats.lands')
    ev(pg, '''() => new Promise(res => { const v = window.__vdd; v.hold(true); let ph = 'up', t0 = performance.now();
      const step = () => { const now = performance.now();
        if (ph === 'up' && now - t0 > 700){ v.hold(false); ph = 'fall'; }
        else if (ph === 'fall' && v.vy > 0 && v.P.yMax - v.y <= v.P.landH - 6){ v.hold(true); ph = 'press'; }
        else if (ph === 'press' && now - t0 > 2500){ v.hold(false); ph = 'done'; }
        if (ph === 'done' || now - t0 > 6000){ v.hold(false); res(); return; }
        requestAnimationFrame(step); }; requestAnimationFrame(step); })''')
    check(ev(pg, 'window.__vdd.stats.lands') > l0, 'atterrissage parfait validé à l\'input (input à %s px, seuil %s, chute depuis %.0f px)' % (ev(pg, 'window.__vdd.lastPressH'), ev(pg, 'window.__vdd.P.landH'), ev(pg, 'window.__vdd.P.yMax - window.__vdd.airTop')))
    pg.screenshot(path=D + 'p3_land.png')
    # limite d'altitude : monter tout droit finit emporté par le vent
    pg.mouse.down(); t0 = time.time()
    while time.time() - t0 < 6 and ev(pg, 'window.__vdd.state') == 'play': pg.wait_for_timeout(50)
    pg.mouse.up(); pg.wait_for_timeout(1200)
    check(ev(pg, 'window.__vdd.endReason') == 'blown' and ev(pg, 'window.__vdd.state') == 'recap', 'trop haut = emportée par le vent -> écran de niveau perdu')
    pg.screenshot(path=D + 'p3_blown.png')
    # bot sur une vraie partie
    ev(pg, 'window.__vdd.start()'); pg.wait_for_timeout(300); bot(pg, 25, False)
    st = ev(pg, 'window.__vdd.stats'); print('   bot appui 25 s :', st, 'poll', round(ev(pg, 'window.__vdd.poll'), 2))
    check(st['coins'] > 40, 'le bot ramasse des pièces (%d)' % st['coins'])
    check(ev(pg, 'window.__vdd.poll') > 25, 'les sondages montent avec la distance (%.2f)' % ev(pg, 'window.__vdd.poll'))
    pg.screenshot(path=D + 'p3_tap_bot.png')
    ev(pg, 'window.__vdd.setT(74.5)'); pg.wait_for_timeout(900); check(ev(pg, 'window.__vdd.state') == 'recap' and ev(pg, 'window.__vdd.endReason') == 'done', 'fin de vol à 75 s -> récap'); pg.screenshot(path=D + 'p3_recap.png')
    # menu de réglage
    pg.click('#gearBtn'); pg.wait_for_timeout(200)
    check(not ev(pg, 'document.getElementById("debug").hidden'), 'la roue crantée ouvre le menu de réglage')
    n = ev(pg, 'document.querySelectorAll("#debug input[type=range]").length'); check(n == len(ev(pg, 'window.__vdd.PSPEC')), '%d curseurs, un par paramètre' % n)
    ev(pg, '(() => { const i = document.getElementById("dbg_cam"); i.value = 0.5; i.dispatchEvent(new Event("input")); })()'); pg.wait_for_timeout(50)
    w2 = ev(pg, 'window.__vdd.world'); check(abs(w2['Z'] - 0.5) < 1e-6 and w2['WH'] == 900, 'le curseur caméra change le monde (%s)' % w2)
    pg.click('#dbgCtrl button[data-ctrl=wind]'); check(ev(pg, 'window.__vdd.ctrl') == 'wind', 'le menu bascule le mode de commande')
    pg.click('#dbgSave'); pg.wait_for_timeout(300); msg = ev(pg, 'document.getElementById("dbgMsg").textContent'); check('Enregistré' in msg, 'sauvegarde : ' + msg)
    pg.screenshot(path=D + 'p3_debug.png')
    pg.reload(); pg.wait_for_timeout(1200); check(abs(ev(pg, 'window.__vdd.P.cam') - 0.5) < 1e-6 and ev(pg, 'window.__vdd.ctrl') == 'wind', 'les réglages sauvegardés reviennent après rechargement')
    ev(pg, 'localStorage.removeItem("p3-settings")')
    check(not errs, 'aucune erreur JS (appui) ' + str(errs[:3]))
    b.close()

    # B. vent
    b, pg, errs = boot(p, 'wind')
    check(ev(pg, 'window.__vdd.ctrl') == 'wind', 'démarrage en mode vent')
    pg.wait_for_timeout(300); y0 = ev(pg, 'window.__vdd.y')
    pg.mouse.move(900, 80); pg.mouse.down(); pg.wait_for_timeout(60)
    ai, av = ev(pg, 'window.__vdd.aIn'), ev(pg, 'window.__vdd.aVane')
    check(ai > 0.9 and av < 0.5, 'doigt en haut : commande immédiate (%.2f), girouette en retard (%.2f)' % (ai, av))
    pg.wait_for_timeout(700); av2 = ev(pg, 'window.__vdd.aVane'); y1 = ev(pg, 'window.__vdd.y')
    check(av2 > 0.9 and y1 < y0 - 40, 'la girouette rejoint la commande (%.2f) et Marine monte (%.0f -> %.0f)' % (av2, y0, y1))
    pg.mouse.move(900, 360); pg.wait_for_timeout(800); vy = ev(pg, 'window.__vdd.vy'); check(abs(vy) < 1, 'doigt au milieu : stationnaire (vy=%.1f)' % vy)
    pg.mouse.move(900, 680); pg.wait_for_timeout(400); check(ev(pg, 'window.__vdd.vy') > 300, 'doigt en bas : descend')
    pg.mouse.up(); pg.wait_for_timeout(300); check(ev(pg, 'window.__vdd.aIn') < -0.9 and ev(pg, 'window.__vdd.aVane') < -0.9, 'doigt levé : la direction se maintient')
    pg.keyboard.down('ArrowUp'); pg.wait_for_timeout(600); check(ev(pg, 'window.__vdd.vy') < -200, 'flèche haut = monte'); pg.keyboard.up('ArrowUp')
    pg.mouse.move(900, 360); pg.mouse.down(); pg.wait_for_timeout(100)   # la direction se maintient : on remet le vent à l'horizontale avant la suite
    pg.screenshot(path=D + 'p3_wind.png')
    check(ev(pg, 'window.__vdd.aVane') == ev(pg, 'window.__vdd.aVane') and ev(pg, 'window.__vdd.aVane') is not None, 'girouette : angle défini')
    bot(pg, 25, True)
    st = ev(pg, 'window.__vdd.stats'); print('   bot vent 25 s :', st, 'poll', round(ev(pg, 'window.__vdd.poll'), 2))
    check(st['coins'] > 30 and ev(pg, 'window.__vdd.state') == 'play', 'le bot vent ramasse des pièces (%d) sans se faire emporter' % st['coins'])
    pg.screenshot(path=D + 'p3_wind_bot.png')
    check(not errs, 'aucune erreur JS (vent) ' + str(errs[:3]))
    b.close()
print('RESULT', 'PASS' if ok else 'FAIL')
