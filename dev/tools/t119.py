import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
from playwright.sync_api import sync_playwright
import time
D=GAME+''
def ev(pg,s): return pg.evaluate(s)
SCHED=[(27.3-0.3,40),(28.9-0.3,40),(40.7-0.95,470),(46.2-0.25,150),(49.8-0.25,150),(54.7-0.85,450)]
with sync_playwright() as p:
    b=p.chromium.launch(args=['--allow-file-access-from-files']); pg=b.new_page(viewport={'width':1280,'height':720})
    errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file://'+D+'vent-de-defiance.html'); pg.wait_for_timeout(900)
    pg.check('#tutoBox'); pg.click('#startBtn'); pg.wait_for_timeout(200)
    done=set(); shots=set(); t0=time.time(); lastI=-1; lastT=0; rewinds={}
    for it in range(12000):
        st=ev(pg,"window.__vdd.tut"); m=ev(pg,"window.__vdd.mode"); t=ev(pg,"window.__vdd.t")
        if st['i']!=lastI: print('step',st['i'],'at t',round(t,2),'prev S',{k:v for k,v in st['s'].items() if k!='snap'}); lastI=st['i']
        if t < lastT-0.5: rewinds[st['i']]=rewinds.get(st['i'],0)+1; done=set(x for x in done if x[0] < t-0.6)
        lastT=t
        if 26.3<t<26.6 and 'ar' not in shots and m is None: shots.add('ar'); pg.screenshot(path=D+'shots/v33_arrow.png')
        if m=='card':
            if st['btn']:
                if ('c',st['i']) not in shots: shots.add(('c',st['i'])); pg.wait_for_timeout(450); pg.screenshot(path=D+'shots/v21_card%d.png'%st['i'])
                pg.mouse.click(300,200)
            elif st['wait']=='tap': pg.keyboard.press('Space')
            elif st['wait']=='boost':
                if ('b',st['i']) not in shots: shots.add(('b',st['i'])); pg.screenshot(path=D+'shots/v32_boostwait.png')
                r0=ev(pg,'window.__vdd.stats').get('ram',0); pg.keyboard.down('Space'); pg.wait_for_timeout(500); pg.screenshot(path=D+'shots/v32_boost.png')
                need=3 if st['i']==2 else 1
                for k in range(140):
                    if ev(pg,'window.__vdd.stats').get('ram',0)>=r0+need: break
                    pg.wait_for_timeout(25)
                pg.wait_for_timeout(120); pg.screenshot(path=D+'shots/v32_ram.png'); pg.keyboard.up('Space'); print('rammed', ev(pg,'window.__vdd.stats').get('ram',0)-r0)
            elif st['wait']=='charge':
                pg.keyboard.down('Space'); pg.wait_for_timeout(250)
                if ('ch',st['i']) not in shots: shots.add(('ch',st['i'])); pg.screenshot(path=D+'shots/v21_charge%d.png'%st['i'])
                pg.wait_for_timeout(300); pg.keyboard.up('Space')
            elif st['wait'] in ('glide','glide2'):
                if ('gl',st['i']) not in shots: shots.add(('gl',st['i'])); pg.screenshot(path=D+'shots/v21_glide%d.png'%st['i'])
                pg.keyboard.down('Space')
                for k in range(150):
                    if ev(pg,"window.__vdd.onWater"): break
                    pg.wait_for_timeout(30)
                pg.keyboard.up('Space')
            pg.wait_for_timeout(20); continue
        if m=='grab':
            g=ev(pg,"window.__vdd.grab")
            if g and g.get('tut'):
                if ('g',g['tut']) not in shots: shots.add(('g',g['tut'])); pg.wait_for_timeout(2600 if g['tut']==1 else 300); pg.screenshot(path=D+'shots/v21_grabtut%d.png'%g['tut'])
                pg.keyboard.press('Space'); pg.wait_for_timeout(150); continue
            if g and not g['res'] and g['t']/g['dur']>=0.72: pg.keyboard.press('Space')
            continue
        if m=='choice':
            c=ev(pg,"window.__vdd.choice")
            if c and c.get('picked'): pg.wait_for_timeout(50); continue
            pg.keyboard.press('Space' if c and c.get('tut') else 'ArrowLeft'); pg.wait_for_timeout(150); continue
        if m=='volte':
            v=ev(pg,"window.__vdd.vf")
            if v['phase']=='intro': pg.wait_for_timeout(300); pg.keyboard.press('Space')
            elif v['phase']=='spin' and v['t']>2.65: pg.keyboard.press('Space')
            elif v['phase']=='result':
                if 'vr' not in shots: shots.add('vr'); pg.wait_for_timeout(900); pg.screenshot(path=D+'shots/v21_volte_result.png')
                pg.keyboard.press('Space')
            elif v['phase']=='tack':
                if 'tk' not in shots: shots.add('tk'); pg.wait_for_timeout(1700); pg.screenshot(path=D+'shots/v21_tack.png')
            elif v['phase']=='impact':
                if 'im' not in shots: shots.add('im'); pg.wait_for_timeout(900); pg.screenshot(path=D+'shots/v21_impact.png')
                pg.keyboard.press('Space')
            pg.wait_for_timeout(30); continue
        for (tp,hold) in SCHED:
            if (tp,hold) in done: continue
            if tp <= t < tp+0.25 and ev(pg,"window.__vdd.onWater"):
                done.add((tp,hold)); pg.keyboard.down('Space'); pg.wait_for_timeout(hold); pg.keyboard.up('Space')
        if st['i']>=9 and t>58.5: print('tutorial done at real s', round(time.time()-t0,1)); break
        pg.wait_for_timeout(10)
    print('rewinds', rewinds, 'stats', ev(pg,'window.__vdd.stats'), 'weight', ev(pg,'window.__vdd.weight'), 'poll', ev(pg,'window.__vdd.poll'))
    pg.screenshot(path=D+'shots/v21_end.png')
    print('adapt', ev(pg,'window.__vdd.adapt'))
    print('end step', ev(pg,"window.__vdd.tut")['i'], round(ev(pg,'window.__vdd.t'),2), errs)
