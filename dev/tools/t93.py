import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
from playwright.sync_api import sync_playwright
import time
D=GAME+''
def ev(pg,s): return pg.evaluate(s)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--allow-file-access-from-files']); pg=b.new_page(viewport={'width':1280,'height':720})
    errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file://'+D+'vent-de-defiance.html'); pg.wait_for_timeout(900)
    pg.uncheck('#tutoBox'); pg.click('#startBtn'); pg.wait_for_timeout(200); ev(pg,"window.__vdd.setInv(true)")
    t0=time.time(); air=[]; cards=0; lastm=None
    while time.time()-t0 < 330:
        st=ev(pg,"window.__vdd.state")
        if st!='play': break
        m=ev(pg,"window.__vdd.mode")
        if m=='card' and lastm!='card':
            cards+=1
            if not ev(pg,"window.__vdd.onWater"): air.append(round(ev(pg,'window.__vdd.t'),1))
        lastm=m
        if m=='card': pg.keyboard.press('Enter')
        elif m=='volte':
            v=ev(pg,"window.__vdd.vf")
            if v['phase']=='intro': pg.keyboard.press('Space')
            elif v['phase']=='spin' and v['t']>2.6: pg.keyboard.press('Space')
            elif v['phase'] in ('result','impact','tack') and v['t']>0.6: pg.keyboard.press('Space')
        pg.wait_for_timeout(60)
    print('voltes', ev(pg,'window.__vdd.stats'), 'state', ev(pg,"window.__vdd.state"), 'real s', round(time.time()-t0,1), 'cards', cards, 'cards opened in the air', air, errs)
