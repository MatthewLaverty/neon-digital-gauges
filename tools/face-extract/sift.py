import numpy as np, cv2, json
from PIL import Image
a7=np.asarray(Image.open('IMG_7567.png').convert('RGB')); a9=np.asarray(Image.open('IMG_7569.png').convert('RGB'))
g7=cv2.cvtColor(a7,cv2.COLOR_RGB2GRAY); g9=cv2.cvtColor(a9,cv2.COLOR_RGB2GRAY)
H89=np.load('H68to69.npy'); holes=json.load(open('holes_px.json'))
m9=np.zeros_like(g9)
for k in ['temp','fuel','speedo','tach']:
    c=np.array(holes[k],float); hull=cv2.convexHull(c.astype(np.float32))
    p=cv2.perspectiveTransform(hull.astype(float).reshape(-1,1,2),H89)[:,0]; cv2.fillPoly(m9,[p.astype(np.int32)],255)
m9=cv2.erode(m9,np.ones((25,25),np.uint8))
m7=np.zeros_like(g7); m7[1000:2350,150:3950]=255
sift=cv2.SIFT_create(nfeatures=20000)
k7,d7=sift.detectAndCompute(g7,m7); k9,d9=sift.detectAndCompute(g9,m9)
print(len(k7),len(k9))
bf=cv2.BFMatcher(); ms=bf.knnMatch(d7,d9,k=2)
good=[m for m,n in ms if m.distance<0.75*n.distance]
src=np.float32([k7[m.queryIdx].pt for m in good]); dst=np.float32([k9[m.trainIdx].pt for m in good])
H79,inl=cv2.findHomography(src,dst,cv2.RANSAC,4.0)
inl=inl.ravel().astype(bool); print('good',len(good),'inliers',inl.sum())
pr=cv2.perspectiveTransform(src[inl].reshape(-1,1,2),H79)[:,0]; print('rms',np.sqrt(((pr-dst[inl])**2).sum(1).mean()))
# distribution of inliers across gauges
H98=np.linalg.inv(H89)
p8=cv2.perspectiveTransform(dst[inl].reshape(-1,1,2).astype(float),H98)[:,0]
print('inlier x-range in 7568 px', np.percentile(p8[:,0],[0,10,50,90,100]).round())
np.save('H67to69.npy',H79)
H78=H98@H79; np.save('H67to68.npy',H78)
# warp 7567 into 7568 frame and overlay holes
w=cv2.warpPerspective(a7,H78,(4032,3024),flags=cv2.INTER_LANCZOS4)
Image.fromarray(w).save('face_in_68.png')
vis=w.copy()
for k,v in holes.items(): cv2.polylines(vis,[np.array(v,np.int32)],True,(255,0,255),4)
Image.fromarray(vis).crop((100,1100,4000,2450)).resize((1950,675)).save('face68_vis.jpg')
