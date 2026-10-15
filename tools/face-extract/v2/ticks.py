import numpy as np, cv2, json
from PIL import Image
m=np.asarray(Image.open('mosaic_old.png').convert('RGB'))
V=m.max(2).astype(np.float32)
bg=cv2.GaussianBlur(cv2.morphologyEx(V,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(41,41))),(0,0),8)
b=((V-bg)>60).astype(np.uint8)
b=cv2.morphologyEx(b,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,lab,st,cen=cv2.connectedComponentsWithStats(b,8)
np.save('lab_mos.npy',lab)
def ticks(px,py,lo,hi,amin,amax):
    T=[]
    for i in range(1,n):
        cx,cy=cen[i]; r=np.hypot(cx-px,cy-py)
        if not(lo<r<hi and amin<st[i,4]<amax): continue
        x,y,w,h=st[i,:4]; ys,xs=np.nonzero(lab[y:y+h,x:x+w]==i); xs=xs+x; ys=ys+y
        P=np.c_[xs,ys].astype(float); c=P.mean(0); U,S,Vt=np.linalg.svd(P-c,full_matrices=False)
        elong=S[0]/max(S[1],1e-6)
        d=Vt[0]; radial=(c-[px,py])/np.linalg.norm(c-[px,py])
        if elong<2.2 or abs(d@radial)<0.9: continue
        t=(P-c)@d; e1=P[t>np.percentile(t,92)].mean(0); e2=P[t<np.percentile(t,8)].mean(0)
        if np.hypot(*(e1-[px,py]))<np.hypot(*(e2-[px,py])): e1,e2=e2,e1
        T.append([*e1,*e2])
    T=np.array(T); a=np.degrees(np.arctan2(-(T[:,1]-py),T[:,0]-px)); o=np.argsort(-((a-250)%360))
    return T[o]
res={}
for k,(px,py,lo,hi,amn,amx) in {'tach':(3126,736,300,420,300,3000),'speedo':(2048,700,400,520,300,4000)}.items():
    T=ticks(px,py,lo,hi,amn,amx)
    a=np.degrees(np.arctan2(-(T[:,1]-py),T[:,0]-px))
    print(k,len(T),np.round(a,1))
    res[k]=T.tolist()
json.dump(res,open('ticks_old.json','w'))
