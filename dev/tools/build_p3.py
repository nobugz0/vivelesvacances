"""Proto 3 : fichier unique (comme build_proto.py, avec les sprites générés du proto 3 : atlas5, ciel, mer).
Usage : python3 tools/build_p3.py proto3.html proto3-single.html"""
import os, sys, subprocess
from PIL import Image
G = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'game')
for src, dst, q in (('atlas5.png', 'atlas5_q90.webp', 90), ('sky5.png', 'sky5.webp', 85), ('sea5.png', 'sea5.webp', 85), ('storm5.png', 'storm5.webp', 85), ('logo5.png', 'logo5.webp', 90)):
    Image.open(os.path.join(G, src)).save(os.path.join(G, 'single', dst), 'WEBP', quality=q, method=6)
tmp = os.path.join(G, '_p3_tmp.html')
s = open(os.path.join(G, sys.argv[1]), encoding='utf-8').read()
import base64
for name, path in (('atlas5.png', 'single/atlas5_q90.webp'), ('sky5.png', 'single/sky5.webp'), ('sea5.png', 'single/sea5.webp'), ('storm5.png', 'single/storm5.webp'), ('closeup5.jpg', 'closeup5.jpg'), ('menu5.jpg', 'menu5.jpg'), ('logo5.png', 'single/logo5.webp')):
    uri = ('data:image/jpeg;base64,' if path.endswith('.jpg') else 'data:image/webp;base64,') + base64.b64encode(open(os.path.join(G, path), 'rb').read()).decode()
    s = s.replace("'" + name + "'", "'" + uri + "'").replace('"' + name + '"', '"' + uri + '"')
open(tmp, 'w', encoding='utf-8').write(s)
try:
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_proto.py'), '_p3_tmp.html', sys.argv[2]], check=True)
finally:
    os.remove(tmp)
