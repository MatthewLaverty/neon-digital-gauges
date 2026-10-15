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
for k,(x,y) in {'temp':(836.5,650.5),'fuel':(1385.5,668.5),'speedo':(2053.5,692.5),'tach':(3110.5,726.5)}.items(): cv2.circle(E8,(int(x),int(y)),82,1,-1)
for (x0,y0,x1,y1) in [(1855,950,2175,1020),(2395,970,2705,1045)]:
    P=ap([[x0,y0],[x1,y0],[x1,y1],[x0,y1]]); cv2.fillPoly(E8,[np.round(P).astype(np.int32)],1)
extra=json.load(open('masks_v2.json')) if __import__('os').path.exists('masks_v2.json') else {'circles':[],'polys':[]}
for x,y,r in extra['circles']: cv2.circle(E8,(int(x),int(y)),int(r),1,-1)
for P in extra['polys']: cv2.fillPoly(E8,[np.array(P,np.int32)],1)
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
np.save('alpha_v2.npy',alpha); json.dump({k:list(map(float,v)) for k,v in piv.items()},open('pivots_v2.json','w'))
Image.fromarray((alpha*255).astype(np.uint8)).resize((2000,680)).save('alpha_v2_vis.png')
