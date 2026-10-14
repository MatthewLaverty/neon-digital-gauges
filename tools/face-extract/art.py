import numpy as np, cv2, json
from PIL import Image
m=np.asarray(Image.open('master_10pxmm.png').convert('RGB'))
H_,W_=m.shape[:2]
alpha=np.load('alpha.npy')
hsv=cv2.cvtColor(m,cv2.COLOR_RGB2HSV); Hh,Ss,Vv=[hsv[...,i].astype(np.float32) for i in range(3)]
pv={'temp':(832,660,73),'fuel':(1378,674,71),'speedo':(2048,700,93),'tach':(3126,736,73)}
# needle orange: saturated tach needle pixels
yy,xx=np.mgrid[0:H_,0:W_]
tx,ty,_=pv['tach']
nd=((Hh<12)|(Hh>165))&(Ss>150)&(Vv>120)&(np.hypot(xx-tx,yy-ty)<400)&(np.abs(yy-ty)<40)
ORANGE=np.median(m[nd],0).astype(int)
bl=(Hh>90)&(Hh<130)&(Ss>70)&(alpha>0.8)
BLUE=np.median(m[bl],0).astype(int)
print('needle orange',ORANGE,'blue',BLUE,'n',nd.sum(),bl.sum())
# classify colors using smoothed hue (per component majority)
blue=(Hh>90)&(Hh<130)&(Ss>60)
warm=((Hh<22)|(Hh>165))&(Ss>80)
cls=np.zeros((H_,W_),np.uint8)  # 0 white 1 blue 2 orange
binm=(alpha>0.3).astype(np.uint8)
n,lab,st,_=cv2.connectedComponentsWithStats(binm,8)
bf=np.bincount(lab.ravel(),weights=(blue&(binm>0)).ravel(),minlength=n)/np.maximum(st[:,4],1)
wf=np.bincount(lab.ravel(),weights=(warm&(binm>0)).ravel(),minlength=n)/np.maximum(st[:,4],1)
cc=np.zeros(n,np.uint8); cc[bf>0.4]=1; cc[(wf>0.4)&(bf<=0.4)]=2; cc[0]=0
# tach redline: tick components by angle
ang=np.degrees(np.arctan2(-(yy-ty),xx-tx))  # 0=right, ccw positive
rad=np.hypot(xx-tx,yy-ty)
ticks=[]
for i in range(1,n):
    cx=st[i,0]+st[i,2]/2; cy=st[i,1]+st[i,3]/2; r=np.hypot(cx-tx,cy-ty)
    if 300<r<420 and st[i,4]>150: ticks.append((i,r,np.degrees(np.arctan2(-(cy-ty),cx-tx))))
print('tick candidates',len(ticks))

np.save('lab.npy',lab); np.save('cc.npy',cc)
red_ids=[int(t[0]) for t in ticks if t[1]>345 and -32<t[2]<22]
print('redline ids',red_ids,[round(t[2],1) for t in ticks if t[1]>345 and -32<t[2]<22])
json.dump({'red_ids':red_ids,'ORANGE':ORANGE.tolist(),'BLUE':BLUE.tolist()},open('colors.json','w'))
