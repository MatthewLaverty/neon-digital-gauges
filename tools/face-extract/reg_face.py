import numpy as np, cv2, json
from PIL import Image
w=np.asarray(Image.open('w69.png').convert('RGB'))
g69=w.max(2).astype(np.float32)
bg=cv2.GaussianBlur(cv2.morphologyEx(g69,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(41,41))),(0,0),8)
gr69=np.clip((g69-bg-40)/60,0,1)
alpha=np.load('alpha.npy')
S=json.load(open('overlay_mm.json'))['shapes']
res={}
for k in ['temp','fuel','speedo','tach']:
    p=np.asarray(S[k]); p=np.c_[(p[:,0]+205)*10,(68-p[:,1])*10].astype(np.int32)
    hm=np.zeros(alpha.shape,np.uint8); cv2.fillPoly(hm,[p],1)
    hm=cv2.erode(hm,np.ones((41,41),np.uint8))
    x,y,ww,hh=cv2.boundingRect(p); pad=60
    sl=(slice(y-pad,y+hh+pad),slice(x-pad,x+ww+pad))
    T=cv2.GaussianBlur((gr69*hm)[sl],(0,0),3).astype(np.float32)
    I=cv2.GaussianBlur(alpha[sl].astype(np.float32),(0,0),3)
    best=None
    for mode,M0 in [(cv2.MOTION_TRANSLATION,np.eye(2,3,dtype=np.float32)),(cv2.MOTION_AFFINE,None)]:
        Mi=np.eye(2,3,dtype=np.float32) if M0 is not None else best[1].copy()
        try:
            cc,M=cv2.findTransformECC(T,I,Mi,mode,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,300,1e-6),hm[sl].astype(np.uint8),5)
        except cv2.error as e: print(k,'fail',e); continue
        best=(cc,M,mode)
        print(k,mode,round(cc,3),M.round(4).tolist())
    # M maps template(w69/hole) coords -> input(face master) coords within crop
    M=best[1].astype(np.float64); A=np.vstack([M,[0,0,1]])
    Sh=np.array([[1,0,x-pad],[0,1,y-pad],[0,0,1]])
    Fm=Sh@A@np.linalg.inv(Sh)   # hole-frame px -> face master px
    res[k]=Fm.tolist()
json.dump(res,open('face_reg.json','w'),indent=1)
