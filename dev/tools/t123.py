import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
from playwright.sync_api import sync_playwright
D=GAME+''
with sync_playwright() as p:
    b=p.chromium.launch(); 
    for name,vp in [('desk',{'width':1280,'height':720}),('phone',{'width':844,'height':390})]:
        pg=b.new_page(viewport=vp, has_touch=(name=='phone'))
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        fails=[]; pg.on('requestfailed', lambda r: fails.append(r.url[:60]))
        pg.goto('file://'+D+'iso/vent-de-defiance.html'); pg.wait_for_timeout(1500); pg.screenshot(path=D+'shots/v23_iso_title_%s.png'%name)
        pg.uncheck('#tutoBox'); pg.click('#startBtn'); pg.wait_for_timeout(3500); pg.screenshot(path=D+'shots/v23_iso_play_%s.png'%name)
        print(name, errs, fails, pg.evaluate("[!!document.querySelector('audio').duration, document.querySelector('audio').readyState]"))
