import numpy as np, cv2, json
from PIL import Image
d=json.load(open('overlay_mm.json'))
K=237.5/25.4
H78=np.load('H67to68.npy')
# origin px in 7568: speedo arc center
holes=json.load(open('holes_px.json'))
# recompute origin as in build_geom
sp=np.array(holes['speedo'],float); x,y,w,h=cv2.boundingRect(sp.astype(np.int32)); pts=sp[sp[:,1]<y+0.55*h]
A=np.c_[2*pts,np.ones(len(pts))]; bb=(pts**2).sum(1); Ox,Oy,_=np.linalg.lstsq(A,bb,rcond=None)[0]
R=10.0; Xmin,Xmax,Ymin,Ymax=-205,195,-68,68
W=int((Xmax-Xmin)*R); Hh=int((Ymax-Ymin)*R)
Aff=np.array([[R/K,0,-R*(Ox/K+Xmin)],[0,R/K,R*(Ymax-Oy/K)],[0,0,1]])
M=Aff@H78
a7=np.asarray(Image.open('IMG_7567.png').convert('RGB'))
mst=cv2.warpPerspective(a7,M,(W,Hh),flags=cv2.INTER_LANCZOS4)
Image.fromarray(mst).save('master_10pxmm.png')
json.dump({'R':R,'Xmin':Xmin,'Ymax':Ymax,'W':W,'H':Hh,'origin_px68':[Ox,Oy]},open('master_meta.json','w'))
vis=mst.copy()
def mm2m(p): p=np.asarray(p); return np.c_[(p[:,0]-Xmin)*R,(Ymax-p[:,1])*R]
for k,v in d['shapes'].items(): cv2.polylines(vis,[mm2m(v).astype(np.int32)],True,(255,0,255),3)
Image.fromarray(vis).resize((W//2,Hh//2)).save('master_vis.jpg')
print(W,Hh)
