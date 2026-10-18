import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'game')) + '/'
import re, sys, datetime, zoneinfo
f=GAME+'vent-de-defiance.html'; s=open(f).read()
now=datetime.datetime.now(zoneinfo.ZoneInfo('Europe/Paris')).strftime('%d/%m/%Y à %Hh%M')
s2=re.sub(r"BUILD = '[^']*'", "BUILD = '%s'"%now, s, count=1); assert s2!=s or now in s
open(f,'w').write(s2); print('stamped', now)
