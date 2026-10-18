import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
# GitHub Pages copy: the single file plus the home-screen app settings
S=GAME+'single/marine-la-maline.html'; R=GAME+'../../index.html'
s=open(S).read()
head='''<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Marine la maline">
<meta name="theme-color" content="#0f1d33">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-180.png">
<link rel="manifest" href="manifest.webmanifest">
'''
a='<title>Marine la maline</title>\n'; assert s.count(a)==1; s=s.replace(a,a+head)
s=s.replace('Pour jouer, ouvre ce lien dans Safari :','Pour jouer, ouvre ce lien dans Safari, puis Partager, Sur l’écran d’accueil :')
open(R,'w').write(s); print('gh ok')
