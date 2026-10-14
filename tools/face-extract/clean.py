import numpy as np, cv2, json
from PIL import Image
m=np.asarray(Image.open('master_10pxmm.png').convert('RGB'))
H_,W_=m.shape[:2]
meta=json.load(open('master_meta.json')); R=meta['R']; Xmin=meta['Xmin']; Ymax=meta['Ymax']
hsv=cv2.cvtColor(m,cv2.COLOR_RGB2HSV); Hh,Ss,Vv=[hsv[...,i].astype(np.float32) for i in range(3)]
V=m.max(2).astype(np.float32)
bg=cv2.morphologyEx(V,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(41,41)))
bg=cv2.GaussianBlur(bg,(0,0),8)
diff=V-bg
np.save('diff.npy',diff)
pv={'temp':(832,660,73),'fuel':(1378,674,71),'speedo':(2048,700,93),'tach':(3126,736,73)}
# needle (red) mask
red=((Hh<12)|(Hh>165))&(Ss>110)&(Vv>90)
red=cv2.dilate(red.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))>0
excl=red.copy()
def circ(mask,x,y,r): cv2.circle(mask,(int(x),int(y)),int(r),1,-1)
E8=np.zeros((H_,W_),np.uint8)
for k,(x,y,r) in pv.items(): circ(E8,x,y,r+6)
# odometer windows, stop pins, knob
cv2.rectangle(E8,(1855,950),(2175,1020),1,-1); cv2.rectangle(E8,(2395,970),(2705,1045),1,-1)
for (x,y,r) in [(2385,930,22),(2890,840,22),(803,357,32),(587,778,32),(1314,383,32),(1122,804,32)]: circ(E8,x,y,r)
cv2.fillPoly(E8,[np.array([(2840,860),(2965,870),(2960,965),(2870,1065),(2745,1065),(2760,975)],np.int32)],1)
excl|=E8>0
np.save('excl.npy',excl)
print('diff pct in face',np.percentile(diff[400:1000,500:3400],[50,90,95,98,99]).round(1))
t0,t1=40.0,100.0
alpha=np.clip((diff-t0)/(t1-t0),0,1)
alpha[excl]=0
# speck removal: components of (alpha>0.5) with small area, unless blue
bin_=(alpha>0.35).astype(np.uint8)
n,lab,st,_=cv2.connectedComponentsWithStats(bin_,8)
blue=((Hh>90)&(Hh<130)&(Ss>70))
small=np.zeros(n,bool)
for i in range(1,n):
    if st[i,4]<60:
        x,y,w,h=st[i,:4]; reg=lab[y:y+h,x:x+w]==i
        if blue[y:y+h,x:x+w][reg].mean()<0.5: small[i]=True
alpha[small[lab]&(lab>0)]=0
# also zero faint halo not connected to strong cores
core=(alpha>0.6).astype(np.uint8); grow=cv2.dilate(core,np.ones((7,7),np.uint8))
alpha[grow==0]=0
# remove thin reflection streaks: sparse components (fill<0.2) that are small
b2=(alpha>0.3).astype(np.uint8); n2,l2,s2,_=cv2.connectedComponentsWithStats(b2,8)
kill=np.zeros(n2,bool)
for i in range(1,n2):
    x,y,w,h,ar=s2[i]
    if ar/(w*h)<0.2 and max(w,h)>40 and ar<1000: kill[i]=True
alpha[kill[l2]]=0
yy,xx=np.mgrid[0:H_,0:W_]; alpha[np.hypot(xx-2048,yy-700)<150]=0  # needle glint near speedo hub
np.save('alpha.npy',alpha)
Image.fromarray((alpha*255).astype(np.uint8)).resize((W_//2,H_//2)).save('alpha_vis.png')
