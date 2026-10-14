import numpy as np, cv2, json, sys
from PIL import Image
alpha=np.load('alpha.npy'); lab=np.load('lab.npy'); cc=np.load('cc.npy')
col=json.load(open('colors.json')); OR=np.array(col['ORANGE'],float); BL=np.array(col['BLUE'],float)
RED_NUMERALS='--red-numerals' in sys.argv
for i in col['red_ids']: cc[i]=2
cls=cc[lab]
# fill alpha halo pixels (lab==0, alpha>0) with nearest component class
halo=(lab==0)&(alpha>0)
if halo.any():
    d,idx=cv2.distanceTransformWithLabels((lab==0).astype(np.uint8),cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
    ys,xs=np.nonzero(lab>0); lut=np.zeros(idx.max()+1,np.uint8)
    lut[idx[ys,xs]]=cls[ys,xs]; cls=np.where(lab>0,cls,lut[idx])
pal=np.array([[255,255,255],BL,OR],float)
out=(alpha[...,None]*pal[cls]).clip(0,255).astype(np.uint8)
Image.fromarray(out).save('face_clean_10pxmm.png')
Image.fromarray(out).resize((2000,680),Image.LANCZOS).save('face_clean_vis.jpg')
print({k:int((cls[alpha>0.5]==v).sum()) for k,v in [('white',0),('blue',1),('orange',2)]})
