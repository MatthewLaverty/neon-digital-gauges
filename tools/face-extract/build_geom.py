import numpy as np, cv2, json
from scipy.ndimage import gaussian_filter1d
PX_PER_IN=237.5; PX_PER_MM=PX_PER_IN/25.4
holes=json.load(open('holes_px.json'))
outer=np.array(json.load(open('outer_px.json')),float)
Z=np.array([(800,75),(640,90),(480,108),(300,135),(200,160),(140,182),(105,203),(82,232),(70,270),(64,300),(64,400),(68,470),(105,470),(105,495),(76,495),(78,560),(115,562),(115,598),(82,600),(82,665),(150,672),(155,700),(160,735),(175,746),(260,749),(480,750),(800,752)],float)
Zf=np.c_[100+1.5*Z[:,0],1150+1.5*Z[:,1]]
# outer: keep grabcut points x>=1300, insert digitized
keep=outer[:,0]>=1300
# find the chain of kept points as contiguous run (contour is closed); rotate so the gap is at end
idx=np.nonzero(keep)[0]
# rotate array so that it starts right after the removed segment
d=np.diff(np.r_[keep,keep[0]].astype(int))
start=(np.nonzero(d==1)[0][0]+1)%len(outer)
o=np.roll(outer,-start,axis=0); k=np.roll(keep,-start)
chain=o[:k.sum()] if k[:k.sum()].all() else o[k]
# chain goes from one end to the other; decide which end is top
a,b=chain[0],chain[-1]
left = Zf if a[1]>b[1] else Zf[::-1]  # want to append from chain end to chain start
# chain ends at b; append digitized from b-side to a-side
if np.linalg.norm(left[0]-b)>np.linalg.norm(left[-1]-b): left=left[::-1]
outer2=np.vstack([chain,left])
def smooth(c,s):
    c=np.asarray(c,float); return np.c_[gaussian_filter1d(c[:,0],s,mode='wrap'),gaussian_filter1d(c[:,1],s,mode='wrap')]
def simplify(c,eps):
    return cv2.approxPolyDP(c.astype(np.float32).reshape(-1,1,2),eps,True)[:,0,:].astype(float)
hull_set={'temp','fuel','oval_tl','oval_tr','lamp_l1','lamp_l2','lamp_r1','lamp_r2'}
geo={}
# origin: speedo arc circle center computed below
for k,c in holes.items():
    c=np.array(c,float)
    if k in hull_set: c=cv2.convexHull(c.astype(np.float32))[:,0,:].astype(float); c=simplify(c,0.8)
    else: c=simplify(smooth(c,3),1.0)
    geo[k]=c
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
pg=Polygon(smooth(outer,4)).buffer(0).intersection(box(1300,0,5000,5000))
pl=Polygon(Zf).buffer(0)
U=unary_union([pg,pl.buffer(0.5),pg.buffer(0.5)]).buffer(-0.5)
if U.geom_type!='Polygon': U=max(U.geoms,key=lambda g:g.area)
geo['outer']=simplify(np.array(U.exterior.coords)[:-1],1.2)
# speedo arc center: fit circle to top arc points of speedo (y above its bbox center)
sp=np.array(holes['speedo'],float); x,y,w,h=cv2.boundingRect(sp.astype(np.int32))
pts=sp[sp[:,1]<y+0.55*h]
A=np.c_[2*pts,np.ones(len(pts))]; bb=(pts**2).sum(1); cx,cy,cc=np.linalg.lstsq(A,bb,rcond=None)[0]; r=np.sqrt(cc+cx*cx+cy*cy)
print('speedo arc center px',cx,cy,'r mm',r/PX_PER_MM)
tp=np.array(holes['tach'],float); x2,y2,w2,h2=cv2.boundingRect(tp.astype(np.int32)); pts=tp[tp[:,1]<y2+0.6*h2]
A=np.c_[2*pts,np.ones(len(pts))]; bb=(pts**2).sum(1); tx,ty,tc=np.linalg.lstsq(A,bb,rcond=None)[0]; tr=np.sqrt(tc+tx*tx+ty*ty)
print('tach center px',tx,ty,'r mm',tr/PX_PER_MM)
O=np.array([cx,cy])
def tomm(c): c=(np.asarray(c)-O)/PX_PER_MM; return np.c_[c[:,0],-c[:,1]]
mm={k:tomm(v) for k,v in geo.items()}
small=[(3740,2000),(3765,2079),(3714,2140)]
mm_small=[tomm(np.array([p]))[0].tolist() for p in small]
out={'units':'mm','origin':'speedo arc center','px_per_in':PX_PER_IN,'shapes':{k:v.round(3).tolist() for k,v in mm.items()},'mount_holes':{'centers':mm_small,'d':4.0},
'speedo_center':[0,0],'speedo_arc_r':float(r/PX_PER_MM),'tach_center':tomm(np.array([[tx,ty]]))[0].tolist(),'tach_r':float(tr/PX_PER_MM)}
json.dump(out,open('overlay_mm.json','w'),indent=1)
for k,v in mm.items():
    print(f'{k:8s} pts {len(v):4d}  W {np.ptp(v[:,0]):6.1f}  H {np.ptp(v[:,1]):6.1f}  cx {v[:,0].mean():7.1f} cy {v[:,1].mean():6.1f}')
