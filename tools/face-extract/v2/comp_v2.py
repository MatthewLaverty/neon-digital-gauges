import numpy as np, cv2, json
from PIL import Image
m=np.asarray(Image.open('master_v2.png').convert('RGB')); alpha=np.load('alpha_v2.npy'); H_,W_=alpha.shape
piv=json.load(open('pivots_v2.json')); col=json.load(open('../scans/colors.json'))
RED=np.array(col['ORANGE'],float); BLUE=np.array(col['BLUE'],float)
hsv=cv2.cvtColor(m,cv2.COLOR_RGB2HSV); Hh,Ss=hsv[...,0].astype(np.float32),hsv[...,1].astype(np.float32)
blue=(Hh>90)&(Hh<130)&(Ss>60)
b=(alpha>0.3).astype(np.uint8); n,lab,st,cen=cv2.connectedComponentsWithStats(b,8)
bf=np.bincount(lab.ravel(),weights=(blue&(b>0)).ravel(),minlength=n)/np.maximum(st[:,4],1)
cc=np.zeros(n,np.uint8); cc[bf>0.4]=1; cc[0]=0
def polar(k,i):
    px,py=piv[k]; cx,cy=cen[i]; return np.hypot(cx-px,cy-py)/10, np.degrees(np.arctan2(-(cy-py),cx-px))
log={}
# tach
tx=[]
for i in range(1,n):
    r,a=polar('tach',i)
    if st[i,4]<150: continue
    if 34<r<40.5 and -32<a<22: cc[i]=2; tx.append(('tick',round(r,1),round(a,1)))
    if 26<r<33.5 and -45<a<15: cc[i]=2; tx.append(('numeral',round(r,1),round(a,1),st[i,2:4].tolist()))
log['tach_red']=tx
# temp ticks: H tick = topmost tick near arc top end (r 34-37, angle 105-130 & warm/yellow); C tick = blue near bottom
cand=[]
for i in range(1,n):
    r,a=polar('temp',i)
    if 30<r<40.5 and st[i,4]>200: cand.append((i,round(r,1),round(a,1),round(float(bf[i]),2)))
log['temp_cands']=cand
hot=[c for c in cand if 100<c[2]<135]; hot=min(hot,key=lambda c:c[2])   # farthest clockwise-from-top = H end (largest angle)
cold=[c for c in cand if c[2]<-140 and c[3]>0.4]; cold=min(cold,key=lambda c:c[2]) if cold else None
cc[hot[0]]=2; log['temp_H_tick']=hot
if cold: cc[cold[0]]=1; log['temp_C_tick']=cold
# fuel E tick: lowest tick (most negative angle beyond -140)
fc=[]
for i in range(1,n):
    r,a=polar('fuel',i)
    if 30<r<38 and st[i,4]>200 and a<-140: fc.append((i,round(r,1),round(a,1)))
e=max(fc,key=lambda c:c[2]%360); cc[e[0]]=2; log['fuel_E_tick']=e; log['fuel_cands']=fc
cls=cc[lab]
halo=(lab==0)&(alpha>0)
d,idx=cv2.distanceTransformWithLabels((lab==0).astype(np.uint8),cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
ys,xs=np.nonzero(lab>0); lut=np.zeros(idx.max()+1,np.uint8); lut[idx[ys,xs]]=cls[ys,xs]; cls=np.where(lab>0,cls,lut[idx])
pal=np.array([[255,255,255],BLUE,RED],float)
out=(alpha[...,None]*pal[cls]).clip(0,255).astype(np.uint8)
Image.fromarray(out).save('face_clean_v2.png'); Image.fromarray(out).resize((2000,680),Image.LANCZOS).save('face_clean_v2_vis.jpg')
print(json.dumps(log,indent=0,default=str))
