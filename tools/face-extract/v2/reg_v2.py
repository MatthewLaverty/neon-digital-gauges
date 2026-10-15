import numpy as np, cv2, json
from PIL import Image
from alpha_v2 import graphics
m=np.asarray(Image.open('master_v2.png').convert('RGB')); w=np.asarray(Image.open('w69_v2.png').convert('RGB'))
A,_=graphics(m); B,_=graphics(w)
S=json.load(open('overlay_mm_v2.json'))['shapes']; res={}
for k in ['temp','fuel','speedo','tach']:
    p=np.asarray(S[k]); p=np.c_[(p[:,0]+205)*10,(68-p[:,1])*10].astype(np.int32)
    hm=np.zeros(A.shape,np.uint8); cv2.fillPoly(hm,[p],1); hm=cv2.erode(hm,np.ones((41,41),np.uint8))
    x,y,ww,hh=cv2.boundingRect(p); pad=60; sl=(slice(y-pad,y+hh+pad),slice(x-pad,x+ww+pad))
    T=cv2.GaussianBlur((B*hm)[sl],(0,0),3).astype(np.float32); I=cv2.GaussianBlur(A[sl].astype(np.float32),(0,0),3)
    cc,M=cv2.findTransformECC(T,I,np.eye(2,3,dtype=np.float32),cv2.MOTION_TRANSLATION,(3,300,1e-6),hm[sl],5)
    cc2,M2=cv2.findTransformECC(T,I,np.eye(2,3,dtype=np.float32),cv2.MOTION_EUCLIDEAN,(3,300,1e-6),hm[sl],5)
    res[k]=[float(M[0,2]),float(M[1,2])]
    print(k,'trans px',np.round(M[:,2],2),'cc',round(cc,3),'| euclid rot deg',round(np.degrees(np.arctan2(M2[1,0],M2[0,0])),3),'t',np.round(M2[:,2],2))
json.dump(res,open('face_shift_v2.json','w'))
