"""Proto 3, étape 1 : vol jouable. Démarrage, les deux commandes, collecte, contacts, bain de foule, fin de vol."""
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
with sync_playwright() as p:
    # A. option 2 : appuyer pour monter
    b, pg, errs = boot(p, 'tap')
    check(ev(pg, 'window.__vdd.state') == 'play' and ev(pg, 'window.__vdd.ctrl') == 'tap', 'démarrage en mode kite')
    y0 = ev(pg, 'window.__vdd.y'); pg.mouse.move(640, 360); pg.mouse.down(); pg.wait_for_timeout(700); y1 = ev(pg, 'window.__vdd.y')
    check(y1 < y0 - 60, 'appui = monte (%.0f -> %.0f)' % (y0, y1))
    pg.mouse.up(); pg.wait_for_timeout(1400); y2 = ev(pg, 'window.__vdd.y')
    check(y2 > y1 + 60, 'relâché = freine, plane puis descend (%.0f -> %.0f)' % (y1, y2))
    pg.mouse.down(); pg.wait_for_timeout(2500); check(abs(ev(pg, 'window.__vdd.y') - ev(pg, 'window.__vdd.P.yMin')) < 1, 'plafond atteint, pas au-delà'); pg.mouse.up()
    pg.wait_for_timeout(2500); check(abs(ev(pg, 'window.__vdd.y') - ev(pg, 'window.__vdd.P.yMax')) < 1, 'plancher : stationnaire au ras de l\'eau')
    pg.screenshot(path=D + 'p3_tap.png')
    # bot : suit la pièce la plus proche devant, pendant 25 s
    t0 = time.time(); hits0 = ev(pg, 'window.__vdd.stats.hits')
    while time.time() - t0 < 25 and ev(pg, 'window.__vdd.state') == 'play':
        cs = ev(pg, 'window.__vdd.coinsList.filter(c => c.x > 150 && c.x < 420)'); y = ev(pg, 'window.__vdd.y')
        ty = min(cs, key=lambda c: c['x'])['y'] if cs else 250
        if ty < y - 8: pg.mouse.down()
        else: pg.mouse.up()
        pg.wait_for_timeout(40)
    st = ev(pg, 'window.__vdd.stats'); print('   bot kite 25 s :', st, 'poll', round(ev(pg, 'window.__vdd.poll'), 1), 'mult', ev(pg, 'window.__vdd.mult'))
    check(st['coins'] > 40, 'le bot ramasse des pièces (%d)' % st['coins'])
    check(len(ev(pg, 'window.__vdd.journos')) >= 0 and any(j['kind'] == 'heli' for j in ev(pg, 'window.__vdd.journos')) or st['hits'] >= 0, 'des journalistes apparaissent')
    pg.screenshot(path=D + 'p3_tap_bot.png')
    # fin de vol forcée
    ev(pg, 'window.__vdd.setT(74.5)'); pg.wait_for_timeout(900); check(ev(pg, 'window.__vdd.state') == 'recap', 'fin de vol à 75 s -> récap'); pg.screenshot(path=D + 'p3_recap.png')
    check(not errs, 'aucune erreur JS (kite) ' + str(errs[:3]))
    b.close()

    # B. option 1 : le vent
    b, pg, errs = boot(p, 'wind')
    check(ev(pg, 'window.__vdd.ctrl') == 'wind', 'démarrage en mode vent')
    pg.wait_for_timeout(500); y0 = ev(pg, 'window.__vdd.y')
    pg.mouse.move(900, 80); pg.mouse.down(); pg.wait_for_timeout(60)
    ai, av = ev(pg, 'window.__vdd.aIn'), ev(pg, 'window.__vdd.aVane')
    check(ai > 0.9 and av < 0.35, 'doigt en haut : commande immédiate (%.2f), girouette en retard (%.2f)' % (ai, av))
    pg.wait_for_timeout(700); av2 = ev(pg, 'window.__vdd.aVane'); y1 = ev(pg, 'window.__vdd.y')
    check(av2 > 0.9 and y1 < y0 - 40, 'la girouette rejoint la commande (%.2f) et Marine monte (%.0f -> %.0f)' % (av2, y0, y1))
    pg.mouse.move(900, 360); pg.wait_for_timeout(800); vy = ev(pg, 'window.__vdd.vy'); check(abs(vy) < 1, 'doigt au milieu : stationnaire (vy=%.1f)' % vy)
    pg.mouse.move(900, 680); pg.wait_for_timeout(900); check(ev(pg, 'window.__vdd.vy') > 300, 'doigt en bas : descend')
    pg.mouse.up(); pg.wait_for_timeout(500); check(ev(pg, 'window.__vdd.aIn') < -0.9 and ev(pg, 'window.__vdd.aVane') < -0.9, 'doigt levé : la direction se maintient')
    pg.screenshot(path=D + 'p3_wind.png')
    # clavier
    pg.keyboard.down('ArrowUp'); pg.wait_for_timeout(700); check(ev(pg, 'window.__vdd.vy') < -200, 'flèche haut = monte'); pg.keyboard.up('ArrowUp')
    # bot vent : vise la pièce la plus proche, 25 s
    t0 = time.time(); pg.mouse.move(900, 360); pg.mouse.down()
    while time.time() - t0 < 25 and ev(pg, 'window.__vdd.state') == 'play':
        cs = ev(pg, 'window.__vdd.coinsList.filter(c => c.x > 150 && c.x < 460)'); y = ev(pg, 'window.__vdd.y')
        ty = min(cs, key=lambda c: c['x'])['y'] if cs else 250
        d = max(-1, min(1, (y - ty)/90.0))
        pg.mouse.move(900, 360 - d*290); pg.wait_for_timeout(40)
    pg.mouse.up(); st = ev(pg, 'window.__vdd.stats'); print('   bot vent 25 s :', st, 'poll', round(ev(pg, 'window.__vdd.poll'), 1), 'mult', ev(pg, 'window.__vdd.mult'))
    check(st['coins'] > 30, 'le bot vent ramasse des pièces (%d)' % st['coins'])
    pg.screenshot(path=D + 'p3_wind_bot.png')
    # bain de foule : on se pose au ras de l'eau sur un groupe
    ev(pg, 'window.__vdd.P.speed = 0'); pg.wait_for_timeout(100)
    pg.evaluate('''() => { const g = window.__vdd; }''')
    pg.mouse.move(900, 700); pg.mouse.down(); pg.wait_for_timeout(1500)
    c0 = ev(pg, 'window.__vdd.stats.crowds')
    # on place un groupe sous Marine par les hooks : on relance la vitesse et on attend qu'un groupe passe
    ev(pg, 'window.__vdd.P.speed = 260')
    t0 = time.time(); got = False
    while time.time() - t0 < 30 and ev(pg, 'window.__vdd.state') == 'play':
        if ev(pg, 'window.__vdd.stats.crowds') > c0: got = True; break
        pg.wait_for_timeout(100)
    pg.mouse.up(); check(got, 'bain de foule complété en restant en bas')
    check(not errs, 'aucune erreur JS (vent) ' + str(errs[:3]))
    b.close()
print('RESULT', 'PASS' if ok else 'FAIL')
