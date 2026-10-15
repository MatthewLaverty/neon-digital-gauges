import numpy as np, cv2, json
from PIL import Image
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
A='/home/user/workspace/neon-digital-gauges/art'; O='/home/user/workspace/neon-digital-gauges/hardware/overlay'
F=json.load(open(A+'/faces/faces.json'))['gauges']; geo=json.load(open('../scans2/overlay_mm_v2.json')); p=json.load(open(O+'/overlay_params.json'))
R=5; X0,Y1=-205,68; W,H=400*R,136*R
def m2p(pts): pts=np.asarray(pts); return np.c_[(pts[:,0]-X0)*R,(Y1-pts[:,1])*R]
can=np.zeros((H,W,3),np.float32)
for k in ['temp','fuel','speedo','tach']:
    im=np.asarray(Image.open(f'{A}/preview/{k}_480_with_needle.png').convert('RGB')).astype(np.float32)
    s=R/F[k]['px_per_mm']; cx,cy=F[k]['image_center_mm']
    M=np.array([[s,0,(cx-X0)*R-240*s],[0,s,(Y1-cy)*R-240*s]])
    yy,xx=np.mgrid[0:480,0:480]; circ=(np.hypot(xx-239.5,yy-239.5)<=240).astype(np.float32)
    w=cv2.warpAffine(im,M,(W,H)); m=cv2.warpAffine(circ,M,(W,H))
    can=can*(1-m[...,None])+w*m[...,None]
# plate mask
S=geo['shapes']
cut=[Polygon(S[k]) for k in ['temp','fuel','speedo','tach','slot_tl','oval_tl','slot_tr','oval_tr','lamp_l1','lamp_l2','lamp_r1','lamp_r2']]
pm=np.zeros((H,W),np.uint8); cv2.fillPoly(pm,[np.round(m2p(S['outer'])).astype(np.int32)],255)
for c in cut: cv2.fillPoly(pm,[np.round(m2p(np.array(c.exterior.coords))).astype(np.int32)],0)
for c in geo['mount_holes']['centers']: cv2.circle(pm,tuple(np.round(m2p([c])[0]).astype(int)),int(2*R),0,-1)
pm=cv2.GaussianBlur(pm,(3,3),0)/255.0
rng=np.random.default_rng(1); tex=158+rng.normal(0,9,(H,W)); tex=cv2.GaussianBlur(tex.astype(np.float32),(0,0),0.8)
silver=np.dstack([tex,tex+2,tex+6])
out=can*(1-pm[...,None])+silver*pm[...,None]
# lamp/slot holes: dark tinted
out=np.clip(out,0,255).astype(np.uint8)
dash=out.copy()
for s in p['screens']:
    c=m2p([s['center']])[0]
    if s['shape']=='circle': cv2.circle(dash,tuple(np.round(c).astype(int)),int(round(s['size'][0]/2*R)),(0,200,255),2,cv2.LINE_AA)
    else:
        w,h=s['size']; cv2.rectangle(dash,(int(c[0]-w/2*R),int(c[1]-h/2*R)),(int(c[0]+w/2*R),int(c[1]+h/2*R)),(0,200,255),2,cv2.LINE_AA)
Image.fromarray(out).save(A+'/preview/cluster_mockup.png')
Image.fromarray(dash).save(A+'/preview/cluster_mockup_screen_outlines.png')
