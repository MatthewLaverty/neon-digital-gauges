import numpy as np, cv2, json
from PIL import Image
M=np.asarray(Image.open('../scans/master_10pxmm.png').convert('L'))
cl=cv2.createCLAHE(3.0,(8,8))
sift=cv2.SIFT_create(nfeatures=40000)
km,dm=sift.detectAndCompute(cl.apply(M),None)
out={}
for n in ['IMG_7574','IMG_7575','IMG_7576','IMG_7577']:
    a=np.asarray(Image.open(n+'.png').convert('L'))
    s=0.6; a2=cv2.resize(a,None,fx=s,fy=s,interpolation=cv2.INTER_AREA)
    k,d=sift.detectAndCompute(cl.apply(a2),None)
    mt=cv2.BFMatcher().knnMatch(d,dm,k=2)
    good=[m for m,nn in mt if m.distance<0.75*nn.distance]
    src=np.float32([k[m.queryIdx].pt for m in good])/s; dst=np.float32([km[m.trainIdx].pt for m in good])
    H,inl=cv2.findHomography(src,dst,cv2.RANSAC,4.0,maxIters=20000,confidence=0.999)
    inl=inl.ravel()>0
    e=np.linalg.norm(cv2.perspectiveTransform(src[inl][None],H)[0]-dst[inl],axis=1)
    print(n,'matches',len(good),'inliers',inl.sum(),'rms px(master)',round(np.sqrt((e**2).mean()),2),'x-range',dst[inl,0].min().round(),dst[inl,0].max().round())
    out[n]=H.tolist()
json.dump(out,open('H_new_to_old.json','w'))
