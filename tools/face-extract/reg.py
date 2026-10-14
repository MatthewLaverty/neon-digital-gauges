import numpy as np, cv2, json
from PIL import Image
S9=5712/1238
a9=np.asarray(Image.open('IMG_7569.png').convert('RGB')); g9=cv2.cvtColor(a9,cv2.COLOR_RGB2GRAY)
def dark_blob(sx,sy,R=160,thr=None):
    X,Y=int(sx*S9),int(sy*S9); p=cv2.GaussianBlur(g9[Y-R:Y+R,X-R:X+R],(0,0),2)
    t,_=cv2.threshold(p,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    m=(p<t).astype(np.uint8); n,lab=cv2.connectedComponents(m); L=lab[R,R]
    hm=(lab==L).astype(np.uint8); cs,_=cv2.findContours(hm,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); c=max(cs,key=cv2.contourArea)[:,0,:]+[X-R,Y-R]
    M=cv2.moments(c.astype(np.float32)); return np.array([M['m10']/M['m00'],M['m01']/M['m00']]),c
pts69={}
for k,(sx,sy,R) in {'lamp_l1':(98,548,160),'lamp_l2':(110,596,160),'lamp_r1':(1103,405,160),'lamp_r2':(1100,440,160),'slot_tl':(460,375,300),'slot_tr':(760,338,300),'oval_tr':(805,365,160)}.items():
    c,cont=dark_blob(sx,sy,R); pts69[k]=(c,cont); print(k,c.round(1),len(cont))
holes=json.load(open('holes_px.json'))
def cen(c):
    c=np.array(c,np.float32); M=cv2.moments(c); return np.array([M['m10']/M['m00'],M['m01']/M['m00']])
keys=list(pts69)
src=np.array([cen(holes[k]) for k in keys]); dst=np.array([pts69[k][0] for k in keys])
H,inl=cv2.findHomography(src,dst,0)
pr=cv2.perspectiveTransform(src.reshape(-1,1,2),H)[:,0]; print('centroid resid px',np.linalg.norm(pr-dst,axis=1).round(1))
# ICP refine on contours
from scipy.spatial import cKDTree
for it in range(15):
    S=[];D=[]
    for k in keys:
        s=np.array(holes[k],float)[::3]; ps=cv2.perspectiveTransform(s.reshape(-1,1,2),H)[:,0]
        t=pts69[k][1].astype(float); tr=cKDTree(t); d,i=tr.query(ps)
        ok=d<np.percentile(d,90); S.append(s[ok]); D.append(t[i[ok]])
    S=np.vstack(S);D=np.vstack(D); H,_=cv2.findHomography(S,D,0)
    ps=cv2.perspectiveTransform(S.reshape(-1,1,2),H)[:,0]
print('ICP rms px',np.sqrt(((ps-D)**2).sum(1).mean()).round(2))
np.save('H68to69.npy',H)
vis=a9.copy()
for k,v in holes.items():
    p=cv2.perspectiveTransform(np.array(v,float).reshape(-1,1,2),H)[:,0]; cv2.polylines(vis,[p.astype(np.int32)],True,(255,0,255),5)
Image.fromarray(vis).crop((0,1100,5712,3300)).resize((1904,733)).save('reg69_vis.jpg')
