import numpy as np, cv2, json
from PIL import Image
from alpha_v2 import graphics
m=np.asarray(Image.open('master_v2.png').convert('RGB')); H_,W_=m.shape[:2]
Hf=np.array(json.load(open('final_frame.json'))['Hf_old_to_new'])
def ap(P): P=np.atleast_2d(np.asarray(P,float)); Q=np.c_[P,np.ones(len(P))]@Hf.T; return Q[:,:2]/Q[:,2:]
hsv=cv2.cvtColor(m,cv2.COLOR_RGB2HSV); Hh,Ss=hsv[...,0].astype(np.float32),hsv[...,1].astype(np.float32)
alpha,diff=graphics(m,t0=55,t1=110)
F=json.load(open('fit_v2.json'))
piv={'temp':F['temp']['tick_pivot_px'],'fuel':F['fuel']['tick_pivot_px'],'speedo':F['speedo']['center_px'],'tach':F['tach']['center_px']}
E8=np.zeros((H_,W_),np.uint8)
for k,(x,y) in piv.items(): cv2.circle(E8,(int(round(x)),int(round(y))),85,1,-1)

for (x0,y0,x1,y1) in [(1855,950,2175,1020),(2395,970,2705,1045)]:
    P=ap([[x0,y0],[x1,y0],[x1,y1],[x0,y1]]); cv2.fillPoly(E8,[np.round(P).astype(np.int32)],1)
extra=json.load(open('masks_v2.json')) if __import__('os').path.exists('masks_v2.json') else {'circles':[],'polys':[]}
for x,y,r in extra['circles']: cv2.circle(E8,(int(round(x)),int(round(y))),int(r),1,-1)
for P in extra['polys']: cv2.fillPoly(E8,[np.round(np.array(P)).astype(np.int32)],1)
for x,y,r in extra.get('bushings',[]): cv2.circle(E8,(int(round(x)),int(round(y))),int(r),1,-1)
alpha[E8>0]=0
blue=(Hh>90)&(Hh<130)&(Ss>60)
b=(alpha>0.35).astype(np.uint8); n,lab,st,cen=cv2.connectedComponentsWithStats(b,8)
bf=np.bincount(lab.ravel(),weights=(blue&(b>0)).ravel(),minlength=n)/np.maximum(st[:,4],1)
kill=np.zeros(n,bool)
for i in range(1,n):
    x,y,w,h,ar=st[i]
    if ar<150 and bf[i]<0.5: kill[i]=True
    if ar/(w*h)<0.2 and max(w,h)>40 and ar<1000: kill[i]=True
alpha[kill[lab]&(lab>0)]=0
core=cv2.morphologyEx((alpha>0.6).astype(np.uint8),cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))); alpha[cv2.dilate(core,np.ones((7,7),np.uint8))==0]=0
FF=json.load(open('final_frame.json'))['fit']['tach']; tc=FF['center_px']; th0=FF['theta0_deg_imgYdown']; dt=FF['step_deg']
def tick_mask(i_tick):
    th=np.radians(th0+i_tick*dt); r=(FF['R_tip_mm']+FF['R_inner_mm'])/2*10
    p=(tc[0]+r*np.cos(th),tc[1]+r*np.sin(th)); bb=(alpha>0.3).astype(np.uint8); nn,ll,ss,cc=cv2.connectedComponentsWithStats(bb,8)
    d=np.hypot(cc[:,0]-p[0],cc[:,1]-p[1]); d[0]=1e9; return ll==np.argmin(d), np.min(d)
m1,d1=tick_mask(2); m0,d0=tick_mask(0)
print('tach 1000 tick found at',round(d1,1),'px from expected; 0 tick',round(d0,1))
src=alpha*cv2.dilate(m1.astype(np.uint8),np.ones((5,5),np.uint8))
Mr=cv2.getRotationMatrix2D((tc[0],tc[1]),2*dt,1.0)   # +angle = CCW on screen = back two 500 rpm steps
syn=cv2.warpAffine(src.astype(np.float32),Mr,(W_,H_),flags=cv2.INTER_LINEAR)
if d0<40: alpha[cv2.dilate(m0.astype(np.uint8),np.ones((7,7),np.uint8))>0]=0
alpha=np.maximum(alpha,syn)
np.save('alpha_v2.npy',alpha); json.dump({k:list(map(float,v)) for k,v in piv.items()},open('pivots_v2.json','w'))
Image.fromarray((alpha*255).astype(np.uint8)).resize((2000,680)).save('alpha_v2_vis.png')
