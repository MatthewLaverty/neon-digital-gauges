import numpy as np, cv2, json, os
from PIL import Image
m=np.asarray(Image.open('master_10pxmm.png').convert('RGB'))
hsv=cv2.cvtColor(m,cv2.COLOR_RGB2HSV).astype(np.float32); Hh,Ss,Vv=hsv[...,0],hsv[...,1],hsv[...,2]
hue_red=np.minimum(Hh,180-Hh)  # distance from red
soft=np.clip((Ss-70)/60,0,1)*np.clip((14-hue_red)/6,0,1)*np.clip((Vv-60)/40,0,1)
pv={'temp':(832,660,73),'fuel':(1378,674,71),'speedo':(2048,700,93),'tach':(3126,736,73)}
H_,W_=Hh.shape; yy,xx=np.mgrid[0:H_,0:W_]
info={}
for k,(px,py,hr) in pv.items():
    b=(soft>0.5).astype(np.uint8); n,lab,st,_=cv2.connectedComponentsWithStats(b,8)
    d=np.hypot(xx-px,yy-py)
    best=None
    for i in range(1,n):
        if st[i,4]<300: continue
        dm=d[lab==i]
        if dm.min()<hr+25:
            if best is None or st[i,4]>st[best,4]: best=i
    msk=lab==best
    ys,xs=np.nonzero(msk); dd=np.hypot(xs-px,ys-py); j=np.argmax(dd)
    tip=(xs[j],ys[j]); L=dd[j]
    # direction from robust mean of far pixels
    far=dd>hr+20; ang=np.degrees(np.arctan2(-(ys[far]-py).mean(),(xs[far]-px).mean()))
    # width profile: perpendicular extent at mid
    info[k]={'len_px':float(L),'len_mm':float(L/10),'angle_deg':float(ang),'tip':[int(tip[0]),int(tip[1])],'comp':int(best)}
    print(k,{a:(round(v,2) if isinstance(v,float) else v) for a,v in info[k].items()})
json.dump(info,open('needles_meas.json','w'),indent=1)
np.save('needle_soft.npy',soft)
