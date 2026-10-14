import numpy as np, cv2, json
from PIL import Image
m=np.asarray(Image.open('master_10pxmm.png').convert('RGB'))
meta=json.load(open('master_meta.json')); R=meta['R']; Xmin=meta['Xmin']; Ymax=meta['Ymax']
g=cv2.cvtColor(m,cv2.COLOR_RGB2GRAY); hsv=cv2.cvtColor(m,cv2.COLOR_RGB2HSV)
seeds={'temp':(660,510),'fuel':(1080,530),'speedo':(1610,540),'tach':(2450,580)}
out={}
vis=m.copy()
for k,(sx,sy) in seeds.items():
    r=140; p=g[sy-r:sy+r,sx-r:sx+r].astype(np.float32); p=cv2.GaussianBlur(p,(0,0),2)
    red=(hsv[sy-r:sy+r,sx-r:sx+r,1]>110)
    print(k,'dark pct',np.percentile(p,[5,20,50,80]).round())
    t,_=cv2.threshold(p.astype(np.uint8),0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    dm=((p<t)&~red).astype(np.uint8)
    dm=cv2.morphologyEx(dm,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
    n,lab,st,cen=cv2.connectedComponentsWithStats(dm)
    L=lab[r,r] if lab[r,r]>0 else 1+np.argmax(st[1:,4])
    hm=(lab==L).astype(np.uint8)
    cs,_=cv2.findContours(hm,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); c=max(cs,key=cv2.contourArea)[:,0,:].astype(float)
    # robust circle fit (iterative trimming)
    pts=c
    for it in range(6):
        A=np.c_[2*pts,np.ones(len(pts))]; b=(pts**2).sum(1); cx,cy,cc=np.linalg.lstsq(A,b,rcond=None)[0]; rr=np.sqrt(cc+cx*cx+cy*cy)
        res=np.abs(np.hypot(pts[:,0]-cx,pts[:,1]-cy)-rr); pts=pts[res<max(2.0,np.percentile(res,70))]
    X=sx-r+cx; Y=sy-r+cy
    out[k]={'pivot_mm':[X/R+Xmin, Ymax-Y/R],'hub_r_mm':rr/R}
    cv2.circle(vis,(int(X),int(Y)),int(rr),(0,255,0),2); cv2.circle(vis,(int(X),int(Y)),3,(0,255,0),-1)
    print(k,out[k])
json.dump(out,open('pivots.json','w'),indent=1)
Image.fromarray(vis[300:800,450:2800]).resize((1175,250)).save('pivots_vis.jpg')
