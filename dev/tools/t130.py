import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
# screenshots of every restyled screen, from the single file (no file-origin canvas taint)
from playwright.sync_api import sync_playwright
import sys
D=GAME+''
F='file://'+D+'single/vent-de-defiance.html'
def ev(pg,s): return pg.evaluate(s)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--allow-file-access-from-files']); pg=b.new_page(viewport={'width':1280,'height':720})
    errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(F); pg.wait_for_timeout(2500); pg.screenshot(path=D+'shots/n_title.png')
    pg.uncheck('#tutoBox'); pg.click('#startBtn'); pg.wait_for_timeout(300); ev(pg,"window.__vdd.setInv(true)")
    pg.wait_for_timeout(1300); pg.screenshot(path=D+'shots/n_sign.png'); pg.wait_for_timeout(1900)
    got=set()
    for i in range(400):
        m=ev(pg,'window.__vdd.mode'); c=ev(pg,'window.__vdd.card')
        if m=='card' and c:
            k='big' if c['info'] else 'story'
            if k not in got: pg.wait_for_timeout(700); pg.screenshot(path=D+'shots/n_card_%s.png'%k); got.add(k)
            pg.keyboard.press('Enter')
        if m is None and 'hud' not in got and ev(pg,'window.__vdd.t')>58: pg.screenshot(path=D+'shots/n_hud.png'); got.add('hud')
        if len(got)>=3: break
        pg.wait_for_timeout(100)
    # charging pose
    pg.mouse.move(640,360); pg.mouse.down(); pg.wait_for_timeout(350); pg.screenshot(path=D+'shots/n_charge.png'); print('spdMul while charging', ev(pg,'window.__vdd.spdMul')); pg.mouse.up(); pg.wait_for_timeout(1500)
    # gold orb choice
    ev(pg,"window.__vdd.orb('g', 0.5, 70)")
    for i in range(60):
        if ev(pg,'window.__vdd.mode')=='grab': break
        pg.wait_for_timeout(50)
    for i in range(80):
        g=ev(pg,'window.__vdd.grab')
        if g and g['tut']: pg.keyboard.press('Space'); pg.wait_for_timeout(150); continue
        if g and not g['res'] and g['t']/g['dur']>0.70: pg.keyboard.press('Space'); break
        pg.wait_for_timeout(16)
    for i in range(60):
        if ev(pg,'window.__vdd.mode')=='choice': break
        pg.wait_for_timeout(50)
    ch=ev(pg,'window.__vdd.choice'); print('choice', ch)
    while ch and ch['tut']: pg.keyboard.press('Space'); pg.wait_for_timeout(200); ch=ev(pg,'window.__vdd.choice')
    pg.wait_for_timeout(300); pg.screenshot(path=D+'shots/n_choice.png')
    if ch: pg.keyboard.press('ArrowLeft'); pg.wait_for_timeout(250); pg.screenshot(path=D+'shots/n_choice_picked.png'); pg.wait_for_timeout(1200)
    # info page
    ev(pg,"window.__vdd.openInfo([{kicker:'GROSSE CASSEROLE', title:'Le prêt qui vient du froid', lead:'En 2014, le parti emprunte 9,4 millions d’euros.', d:'Texte de test sur plusieurs lignes. '.repeat(12), src:['Source A, 01/01/2024','Source B, 02/02/2024']}])"); pg.wait_for_timeout(300); pg.screenshot(path=D+'shots/n_info.png'); ev(pg,'window.__vdd.closeInfo()')
    # volte-face
    ev(pg,'window.__vdd.startVolte(2)'); pg.wait_for_timeout(500); pg.screenshot(path=D+'shots/n_volte_intro.png')
    pg.keyboard.press('Space'); pg.wait_for_timeout(1200); pg.screenshot(path=D+'shots/n_volte_spin.png')
    for i in range(200):
        v=ev(pg,'window.__vdd.vf')
        if v['phase']=='spin' and v['t']>2.55: pg.keyboard.press('Space'); break
        pg.wait_for_timeout(16)
    pg.wait_for_timeout(250); pg.screenshot(path=D+'shots/n_volte_stamp.png'); v=ev(pg,'window.__vdd.vf'); print('grade', v)
    pg.wait_for_timeout(2300); pg.screenshot(path=D+'shots/n_volte_result.png')
    pg.keyboard.press('Space'); pg.wait_for_timeout(500)
    ev(pg,"window.__vdd.finish('win')"); pg.wait_for_timeout(700); pg.screenshot(path=D+'shots/n_end.png')
    # phone, portrait (rotated game)
    m=b.new_page(viewport={'width':390,'height':844}, is_mobile=True, has_touch=True, device_scale_factor=2)
    m.goto(F); m.wait_for_timeout(2500); m.screenshot(path=D+'shots/n_phone_title.png')
    m.tap('#startBtn'); m.wait_for_timeout(5000); m.screenshot(path=D+'shots/n_phone_play.png')
    print('errors', errs)
