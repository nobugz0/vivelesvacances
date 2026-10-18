import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
from playwright.sync_api import sync_playwright
import time
D=GAME+''
def ev(pg,s): return pg.evaluate(s)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--allow-file-access-from-files']); pg=b.new_page(viewport={'width':1280,'height':720})
    errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file://'+D+'single/marine-la-maline-proto.html'); pg.wait_for_timeout(900); pg.click('#startBtn'); pg.wait_for_timeout(2500); ev(pg,"window.__vdd.setInv(true)")
    t0=time.time(); grabs=0; shot=0; st='idle'; maxm=1; voltes=0
    while time.time()-t0<200 and ev(pg,'window.__vdd.state')=='play':
        m=ev(pg,'window.__vdd.mode'); maxm=max(maxm, ev(pg,'window.__vdd.mult'))
        if m=='card': pg.keyboard.press('Enter'); pg.wait_for_timeout(120); continue
        if m=='grab':
            g=ev(pg,'window.__vdd.grab')
            if not g: pg.wait_for_timeout(15); continue
            if not g['res'] and g['t']/g['dur']>0.5: pg.keyboard.press('Space'); grabs+=1
            if g['res'] and shot<2: pg.screenshot(path=D+'proto_grab%d.png'%shot); shot+=1
            pg.wait_for_timeout(15); continue
        if m: pg.keyboard.press('Space'); pg.wait_for_timeout(150); continue
        if st=='idle' and ev(pg,'window.__vdd.onWater'): pg.keyboard.down('Space'); st='c'; tc=time.time()
        elif st=='c' and time.time()-tc>0.6: pg.keyboard.up('Space'); st='a'
        elif st=='a':
            if ev(pg,'window.__vdd.voltWindow()'): pg.keyboard.press('KeyV'); voltes+=1; st='idle'
            elif ev(pg,'window.__vdd.onWater'): st='idle'
        pg.wait_for_timeout(20)
    print('end', ev(pg,'window.__vdd.state'), 'week', round(ev(pg,'window.__vdd.t'),1), 'grabs', grabs, 'max mult', maxm, 'V', voltes, 'stats', ev(pg,'window.__vdd.stats'), 'poll', ev(pg,'window.__vdd.poll'), errs[:3])
    b.close()
