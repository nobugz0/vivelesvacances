import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
from playwright.sync_api import sync_playwright
import time, math
D=GAME+''
def ev(pg,s): return pg.evaluate(s)
def boot(p):
    b=p.chromium.launch(args=['--allow-file-access-from-files']); pg=b.new_page(viewport={'width':1280,'height':720})
    errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file://'+D+'proto.html'); pg.wait_for_timeout(900); pg.click('#startBtn'); pg.wait_for_timeout(3500)
    return b,pg,errs
def wait_window(pg, tmax=2.0):
    t0=time.time()
    while time.time()-t0<tmax:
        if ev(pg,'window.__vdd.voltWindow()'): return True
        pg.wait_for_timeout(15)
    return False
def clear(pg, n=30, quick=False):
    seen=False
    for _ in range(abs(n)):
        m=ev(pg,'window.__vdd.mode')
        if m=='card': pg.keyboard.press('Enter'); seen=True; pg.wait_for_timeout(120)
        elif m: pg.keyboard.press('Space'); pg.wait_for_timeout(200)
        elif n<0 and seen: return
        else: pg.wait_for_timeout(50)
def charged_jump(pg):
    pg.keyboard.down('Space'); pg.wait_for_timeout(700); pg.keyboard.up('Space')
with sync_playwright() as p:
    pass
    if 0:
        b,pg,errs=boot(p); t0=time.time(); log=[]
        while time.time()-t0<200 and ev(pg,'window.__vdd.state')=='play':
            m=ev(pg,'window.__vdd.mode')
            if m in ('card','volte'): pg.keyboard.press('Enter'); pg.keyboard.press('Space')
            if int(time.time()-t0)%10==0: log.append((int(time.time()-t0), round(ev(pg,'window.__vdd.poll'),1), round(ev(pg,'window.__vdd.weight'))))
            pg.wait_for_timeout(100)
        print('A idle: end after', round(time.time()-t0), 's, week', round(ev(pg,'window.__vdd.t'),1), 'state', ev(pg,'window.__vdd.state'), 'polls/cass', sorted(set(log))[::3], errs); b.close()
    # B: keyboard volte inside the first zone, then a free gesture volte outside any zone
    b,pg,errs=boot(p); vw=ev(pg,'window.__vdd.voltW'); print('voltW', vw)
    ev(pg,'window.__vdd.setInv(true)'); ev(pg,'window.__vdd.t = %f' % (vw[1]-7.2)); pg.wait_for_timeout(250)
    ev(pg,'window.__vdd.setInv(false)'); t0=time.time(); st='idle'; cards=[]
    while time.time()-t0<8:
        m=ev(pg,'window.__vdd.mode'); tt=ev(pg,'window.__vdd.t')
        if m=='card': cards.append((round(tt,1), ev(pg,'window.__vdd.cardTitle') if 0 else '')); pg.keyboard.press('Enter'); pg.wait_for_timeout(250); continue
        if m: print('mode', m, tt); break
        if st=='idle' and ev(pg,'window.__vdd.onWater'): pg.keyboard.down('Space'); st='charging'; tc=time.time()
        elif st=='charging' and time.time()-tc>0.6: pg.keyboard.up('Space'); st='air'; print('jump at', round(tt,2), 'charge', ev(pg,'window.__vdd.jumpCharge'))
        elif st=='air' and ev(pg,'window.__vdd.voltWindow()'): pg.screenshot(path=D+'proto_window.png'); pg.keyboard.press('KeyV'); print('V at', round(tt,2)); pg.wait_for_timeout(250); pg.screenshot(path=D+'proto_volte.png'); break
        pg.wait_for_timeout(20)
    print('cards', cards, 'wall', vw[1])
    pg.wait_for_timeout(2500); print('B after zone: mode', ev(pg,'window.__vdd.mode'), 'poll', round(ev(pg,'window.__vdd.poll'),1), 'mult', ev(pg,'window.__vdd.mult'), 'stats', ev(pg,'window.__vdd.stats'))
    pg.screenshot(path=D+'proto_after.png')
    # gesture with the mouse: thumb lifted, then a half circle from the bottom, round the right, up to the left
    clear(pg, 10); ev(pg,'window.__vdd.setInv(true)'); ev(pg,'window.__vdd.t = %f' % (vw[1]+6)); pg.wait_for_timeout(600); clear(pg, 10)
    while not ev(pg,'window.__vdd.onWater'): pg.wait_for_timeout(30)
    pg.mouse.move(640,500); pg.mouse.down(); pg.wait_for_timeout(700); pg.mouse.up()
    print('jc', ev(pg,'window.__vdd.jumpCharge'), ev(pg,'window.__vdd.onWater')); ok=wait_window(pg); print('sea before', ev(pg,'window.__vdd.sea'))
    cx,cy,r=640,360,70; pg.mouse.move(cx,cy+r); pg.mouse.down()
    for i in range(1,13):
        a=math.pi/2 - i*math.pi/12; pg.mouse.move(cx+r*math.cos(a)*1.0, cy+r*math.sin(a)); pg.wait_for_timeout(12)
    pg.mouse.up(); pg.wait_for_timeout(100)
    print('gesture window', ok, 'sea', ev(pg,'window.__vdd.sea'), 'voltOk', ev(pg,'window.__vdd.voltOk'), errs)
    pg.wait_for_timeout(400); pg.screenshot(path=D+'proto_gesture.png')
    # C: miss the wall on purpose
    ev(pg,'window.__vdd.setInv(true)'); ev(pg,'window.__vdd.t = %f' % (vw[2]-1.0)); pg.wait_for_timeout(300)
    for _ in range(20):
        if ev(pg,'window.__vdd.mode')=='card': pg.keyboard.press('Enter'); pg.wait_for_timeout(150)
    ev(pg,'window.__vdd.setInv(false)'); p0=ev(pg,'window.__vdd.poll')
    t0=time.time()
    while time.time()-t0<6 and ev(pg,'window.__vdd.mode')!='volte': pg.wait_for_timeout(50)
    pg.wait_for_timeout(600); pg.screenshot(path=D+'proto_wall.png')
    print('C wall: mode', ev(pg,'window.__vdd.mode'), 'poll', round(p0,1),'->',round(ev(pg,'window.__vdd.poll'),1), 'cass', ev(pg,'window.__vdd.weight'), errs)
    for _ in range(10): pg.keyboard.press('Space'); pg.wait_for_timeout(300)
    pg.wait_for_timeout(500); print('after impact mode', ev(pg,'window.__vdd.mode')); pg.screenshot(path=D+'proto_wall2.png')
    b.close()
