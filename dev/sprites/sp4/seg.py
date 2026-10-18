import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'game')) + '/'
import numpy as np, json, sys
from PIL import Image
from scipy import ndimage as ndi
D=GAME+'../sprites/sp4/'
out={}
for k in ['sheet1','sheet2','sheet3','sheet4','sheet5','sheet6']:
    a=np.array(Image.open(D+k+'.png').convert('RGB')).astype(int)
    bg=np.median(np.concatenate([a[:4].reshape(-1,3),a[-4:].reshape(-1,3),a[:,:4].reshape(-1,3),a[:,-4:].reshape(-1,3)]),0)
    dist=np.sqrt(((a-bg)**2).sum(2)); fg=dist>28
    lab,n=ndi.label(ndi.binary_dilation(fg,iterations=9))
    sizes=ndi.sum(fg,lab,range(1,n+1))
    boxes=[]
    for i,sl in enumerate(ndi.find_objects(lab)):
        if sizes[i]<3000: continue
        y0,y1,x0,x1=sl[0].start,sl[0].stop,sl[1].start,sl[1].stop
        boxes.append([x0,y0,x1-x0,y1-y0,int(sizes[i])])
    rows=sorted(boxes,key=lambda b:(b[1]+b[3]/2))
    # group rows
    R=[];
    for b in rows:
        cy=b[1]+b[3]/2
        if R and abs(cy-R[-1][0])<200: R[-1][1].append(b)
        else: R.append([cy,[b]])
    order=[b for _,bs in R for b in sorted(bs,key=lambda b:b[0])]
    out[k]={'bg':bg.tolist(),'boxes':order}
    print(k,len(order),[b[:4] for b in order])
json.dump(out,open(D+'boxes.json','w'))
