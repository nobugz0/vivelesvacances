import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
import base64, re
D=GAME+''
s=open(D+'vent-de-defiance.html').read()
assets={'atlas.png':('single/atlas_q90.webp','image/webp'),'atlas2.png':('single/atlas2_q90.webp','image/webp'),'atlas3.png':('single/atlas3_q90.webp','image/webp'),'atlas4.png':('single/atlas4_q90.webp','image/webp'),
 'music.mp3':('single/music.mp3','audio/mpeg'), 'ui.webp':('ui.webp','image/webp'), 'uiframe.webp':('uiframe.webp','image/webp')}
for n in ['closeup','end','gameover','start','tack']: assets[n+'.jpg']=('single/%s.jpg'%n,'image/jpeg')
for name,(path,mime) in assets.items():
    uri='data:%s;base64,%s'%(mime, base64.b64encode(open(D+path,'rb').read()).decode())
    cnt=len(re.findall(r'(?<![\w/.-])'+re.escape(name), s))
    s=re.sub(r'(?<![\w/.-])'+re.escape(name), lambda m: uri, s)
    print(name, cnt)
left=re.findall(r'[\w-]+\.(?:png|jpg|mp3|webp)', s); print('left', set(left))
open(D+'single/marine-la-maline.html','w').write(s)
import os; print(os.path.getsize(D+'single/marine-la-maline.html')/1e6,'MB')
