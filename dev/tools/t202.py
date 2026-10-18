import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
from playwright.sync_api import sync_playwright
import time
D=GAME+''
F=__import__('sys').argv[1] if len(__import__('sys').argv)>1 else 'proto.html'
def ev(pg,s): return pg.evaluate(s)
def clear(pg):
    for _ in range(40):
        m=ev(pg,'window.__vdd.mode')
        if m=='card': pg.keyboard.press('Enter'); pg.wait_for_timeout(150)
        elif m: pg.wait_for_timeout(50)
        else: return
with sync_playwright() as p:
    b=p.chromium.launch(args=['--allow-file-access-from-files']); pg=b.new_page(viewport={'width':1280,'height':720})
    errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file://'+D+F); pg.wait_for_timeout(900); pg.click('#startBtn'); pg.wait_for_timeout(3500)
    vw=ev(pg,'window.__vdd.voltW'); print('voltW', vw)
    # 1. free swipe on the water in front of a journalists' boat
    ev(pg,'window.__vdd.setInv(true)'); clear(pg)
    for _ in range(400):
        if ev(pg,'window.__vdd.mode')=='card': pg.keyboard.press('Enter'); pg.wait_for_timeout(150); continue
        a=ev(pg,'window.__vdd.obsAhead')
        if a and 0.4 < a[0] < 1.2 and not ev(pg,'window.__vdd.mode'): break
        pg.wait_for_timeout(20)
    print('boats ahead before', ev(pg,'window.__vdd.obsAhead'), 'near', ev(pg,'window.__vdd.obsNear'), 't', round(ev(pg,'window.__vdd.t'),2), 'sea', ev(pg,'window.__vdd.sea'))
    pg.screenshot(path=D+'p2_before.png')
    print('mode at swipe', ev(pg,'window.__vdd.mode'), ev(pg,'window.__vdd.state'))
    pg.mouse.move(700,400); pg.mouse.down(); pg.mouse.move(680,402); pg.mouse.move(640,404); pg.mouse.move(600,405); pg.mouse.up()
    shots=[]
    for i in range(14):
        pg.wait_for_timeout(70); tr=ev(pg,'window.__vdd.turn'); shots.append(tr and round(tr['t'],2))
        if i in (1,4,7,11): pg.screenshot(path=D+'p2_turn%d.png'%i)
    pg.wait_for_timeout(400)
    print('turn timeline', shots); print('after: near', ev(pg,'window.__vdd.obsNear'), 't', round(ev(pg,'window.__vdd.t'),2), 'sea', ev(pg,'window.__vdd.sea'), 'spd', round(ev(pg,'window.__vdd.spdMul'),2))
    pg.screenshot(path=D+'p2_after.png')
    # 2. speed tiers while holding
    clear(pg); pg.keyboard.down('Space'); tiers=[]
    for i in range(14): pg.wait_for_timeout(200); tiers.append((round(ev(pg,'window.__vdd.spdMul'),2), ev(pg,'window.__vdd.speedTier')))
    pg.screenshot(path=D+'p2_speed.png'); pg.keyboard.up('Space'); print('tiers', tiers, 'fast orbs', ev(pg,'window.__vdd.fastN'))
    # 3. zone volte late (close to the wall)
    ev(pg,'window.__vdd.t = %f' % (vw[1]-7.4)); pg.wait_for_timeout(300); clear(pg); p0=ev(pg,'window.__vdd.poll'); ev(pg,'window.__vdd.setInv(false)')
    while ev(pg,'window.__vdd.t') < vw[1]-0.8:
        if ev(pg,'window.__vdd.mode')=='card': pg.keyboard.press('Enter')
        pg.wait_for_timeout(15)
    pg.screenshot(path=D+'p2_zone.png'); pg.keyboard.press('ArrowLeft'); pg.wait_for_timeout(1400)
    print('zone late: poll', round(p0,2), '->', round(ev(pg,'window.__vdd.poll'),2), 'stats good', ev(pg,'window.__vdd.stats')['good'], 'mode', ev(pg,'window.__vdd.mode'), errs)
    pg.screenshot(path=D+'p2_zone_after.png')
    b.close()
