import os as _os
GAME = _os.environ.get('VDD_GAME', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'game')) + '/'
import numpy as np, json
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
D=GAME+'../sprites/sp4/'
SC=0.41
NAMES={'sheet1':['rideN0','rideN1','takeN','airN','glide0','glide1'],
       'sheet2':['landOk0','landOk1','landOk2','charge0','charge1','charge2'],
       'sheet3':['boost0','boost1','boost2','ram0','ram1','ram2'],
       'sheet4':['fall0','fall1','fall2','wallHit0','wallHit1','wallHit2'],
       'sheet5':['grab0','grab1','grab2','turn0','turn1','turn2'],
       'sheet6':['sink0','sink1','sink2']}
B=json.load(open(D+'boxes.json'))
frames=[]
for sh,names in NAMES.items():
    a=np.array(Image.open(D+sh+'.png').convert('RGB')).astype(int); bg=np.array(B[sh]['bg'])
    dist=np.sqrt(((a-bg)**2).sum(2)); fg=dist>28
    lab,n=ndi.label(ndi.binary_dilation(fg,iterations=9))
    for name,(x,y,w,h,_) in zip(names,B[sh]['boxes']):
        sub=lab[y:y+h,x:x+w]; ids,cnt=np.unique(sub[sub>0],return_counts=True); me=ids[np.argmax(cnt)]
        m=(sub==me)&fg[y:y+h,x:x+w]
        # soften: semi-transparent for pixels close to bg
        d=dist[y:y+h,x:x+w]
        # background = near-bg pixels connected to the crop border, plus big enclosed holes of pure bg; the dark navy suit stays opaque
        close=d<5.5; lab2,n2=ndi.label(close); edge=set(np.unique(np.concatenate([lab2[0],lab2[-1],lab2[:,0],lab2[:,-1]])))-{0}
        bgm=np.isin(lab2,list(edge))
        own=(sub==me)
        alpha=np.where(bgm|~own,0,255).astype(float)
        ring=ndi.binary_dilation(bgm)&~bgm&own
        alpha[ring]=np.clip((d[ring]-4)/20,0,1)*255
        c=a[y:y+h,x:x+w]
        r,g,b=c[...,0],c[...,1],c[...,2]
        red=(r>170)&(g<110)&(b<110)&m; blue=(b>140)&(r<90)&m
        board=red|blue
        H=h
        if name.startswith('sink'):
            ys=np.where(m.any(1))[0]; py=ys[-1]; xs=np.where(m[py-6:py+1].any(0))[0]; px=(xs[0]+xs[-1])/2
        else:
            low=board.copy(); low[:int(h*0.45)]=False
            yy,xx=np.where(low)
            if len(yy)<20: yy,xx=np.where(m); 
            py=np.percentile(yy,99.5); px=(np.percentile(xx,3)+np.percentile(xx,97))/2
        if name.startswith('wallHit'):
            xs=np.where(m.any(0))[0]; px=xs[-1]
            ys=np.where(m.any(1))[0]; py=ys[-1]
        # kite line end: topmost light, unsaturated pixels
        mx=np.maximum(np.maximum(r,g),b); mn=np.minimum(np.minimum(r,g),b)
        line=m&(mn>165)&(mx-mn<45)
        ly,lx=np.where(line[:int(h*0.35)])
        if len(ly)>10:
            t=ly.min(); sel=ly<=t+6; le=[float(lx[sel].mean()-px),float(t-py)]
        else: le=None
        img=Image.fromarray(np.dstack([c,alpha]).astype(np.uint8),'RGBA')
        sc=SC*(0.6 if sh=='sheet6' else 1)
        nw,nh=round(w*sc),round(h*sc); img=img.resize((nw,nh),Image.LANCZOS)
        frames.append(dict(name=name,img=img,px=px*sc,py=py*sc,le=[v*sc for v in le] if le else None))
# pack
W=2048; xs=ys=0; rowh=0; pos=[]
for f in frames:
    w,h=f['img'].size
    if xs+w>W: xs=0; ys+=rowh+2; rowh=0
    pos.append((xs,ys)); xs+=w+2; rowh=max(rowh,h)
atlas=Image.new('RGBA',(W,ys+rowh))
J={}; LE={}
for f,(x,y) in zip(frames,pos):
    atlas.alpha_composite(f['img'],(x,y)); w,h=f['img'].size
    J[f['name']]=[x,y,w,h,round(f['px'],1),round(f['py'],1),4]
    if f['le']: LE[f['name']]=[round(f['le'][0],1),round(f['le'][1],1)]
atlas.save(D+'atlas4.png',optimize=True)
json.dump({'atlas':J,'le':LE},open(D+'atlas4.json','w'))
print(atlas.size, len(J)); print({k:J[k][2:6] for k in list(J)[:6]}); print('noLE',[k for k in J if k not in LE])
# preview with pivots
pv=Image.new('RGB',(9*180,4*230),(27,36,51)); dr=ImageDraw.Draw(pv)
for i,f in enumerate(frames):
    cx,cy=(i%9)*180+90,(i//9)*230+200
    pv.paste(f['img'],(int(cx-f['px']),int(cy-f['py'])),f['img'])
    dr.line([cx-8,cy,cx+8,cy],fill=(255,0,0)); dr.line([cx,cy-8,cx,cy+8],fill=(255,0,0))
    if f['le']: dr.ellipse([cx+f['le'][0]-3,cy+f['le'][1]-3,cx+f['le'][0]+3,cy+f['le'][1]+3],outline=(0,255,0))
    dr.text((cx-80,cy+8),f['name'],fill=(255,255,255))
pv.save(D+'preview.png')
