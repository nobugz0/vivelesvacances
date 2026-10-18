import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
from playwright.sync_api import sync_playwright
D=GAME+''
with sync_playwright() as p:
    b=p.chromium.launch(args=['--allow-file-access-from-files']); pg=b.new_page(viewport={'width':1280,'height':720}); errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.goto('file://'+D+'vent-de-defiance.html'); pg.wait_for_timeout(800)
    pg.uncheck('#tutoBox'); pg.click('#startBtn'); pg.wait_for_timeout(300); pg.evaluate("window.__vdd.setInv(true)")
    for k in range(60):
        if pg.evaluate("window.__vdd.mode")==None and pg.evaluate("window.__vdd.onWater"): break
        pg.keyboard.press('Space'); pg.wait_for_timeout(200)
    pg.wait_for_timeout(5000)
    for k in range(40):
        if pg.evaluate("window.__vdd.mode")==None: break
        pg.keyboard.press('Space'); pg.wait_for_timeout(250)
    for attempt in range(6):
        for k in range(60):
            if pg.evaluate("window.__vdd.mode")==None and pg.evaluate("window.__vdd.onWater"): break
            pg.keyboard.press('Space'); pg.wait_for_timeout(300)
        pg.keyboard.down('Space'); pg.wait_for_timeout(500); pg.keyboard.up('Space'); pg.wait_for_timeout(60)
        pg.keyboard.down('Space')
        ok=False
        for k in range(80):
            st=pg.evaluate("[window.__vdd.onWater, window.__vdd.charging, window.__vdd.mode, window.__vdd.charge]")
            if st[2]: break
            if st[0] and k>3: ok=True; break
            pg.wait_for_timeout(40)
        print('attempt',attempt, st)
        pg.keyboard.up('Space')
        if ok: break
    seen=[st]
    seen=[]
    for k in range(80):
        st=pg.evaluate("[window.__vdd.onWater, window.__vdd.charging, window.__vdd.mode]"); seen.append(st)
        if st[0] and st[1]: break
        pg.wait_for_timeout(50)
    print('last', seen[-1], 'samples', len(seen), errs)
