"""Frame fit check (2026-10-18): the cluster's dash-mounting frame (owner photo IMG_7629, front view, flange highlighted
green, tape for scale) against the v3 board layout.
Method: segment the green flange band; register the traced face outline (overlay_mm.json 'outer') to the band's outer
edge with a similarity fit (median residual 0.9 mm; scale 8.97 px/mm vs 8.86 from the tape, i.e. the flange sits about
1 % closer to the camera than the tape). The front-view fit is chosen over the mirrored one because the speedo hole's flat
bottom extension, the lamp slots and the right-end mount holes land on the matching frame features.
Result: the face outline is the flange's outer edge. The flange inner edge is stored as 'frame_flange_inner' in
overlay_mm.json. Accuracy: about +/-1 mm on edges (painted band edges, photo), +/-1 % on scale."""
import json, pickle, numpy as np, cv2, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import Polygon as SP, Point, box
REF='docs/frame/ref_frame_IMG_7629.jpg'
def segment():
    im=cv2.imread(REF); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); H,S,V=[hsv[...,i].astype(int) for i in range(3)]
    m=((H>28)&(H<55)&(S>90)&(V>110)).astype(np.uint8); m[2120:]=0; m[:700]=0
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8)); n,lab,st,_=cv2.connectedComponentsWithStats(m)
    band=(lab==1+np.argmax(st[1:,4])).astype(np.uint8); Hh,Ww=band.shape
    for d in range(11,301,20):
        bd=cv2.dilate(band,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(d,d))); ff=(1-bd).copy()
        cv2.floodFill(ff,np.zeros((Hh+2,Ww+2),np.uint8),(2085,1500),2); reg=ff==2
        if not (reg[0].any() or reg[-1].any() or reg[:,0].any() or reg[:,-1].any()): break
    reg=cv2.dilate(reg.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(d,d)))&(1-band)
    cs,_=cv2.findContours(reg,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); inner=max(cs,key=cv2.contourArea)[:,0,:].astype(float)
    full=cv2.morphologyEx(np.maximum(band,reg),cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
    cs,_=cv2.findContours(full,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); outer=max(cs,key=cv2.contourArea)[:,0,:].astype(float)
    return outer,inner
def register(outer_px,face):
    from scipy.spatial import cKDTree
    L=face.exterior; src=np.array([L.interpolate(d).coords[0] for d in np.arange(0,L.length,1.0)])*[1,-1]
    T=cKDTree(outer_px); s=225.1/25.4; c=(src.min(0)+src.max(0))/2
    A=np.eye(2)*s; t=np.array([(outer_px[:,0].min()+outer_px[:,0].max())/2,np.percentile(outer_px[:,1],50)])-s*c
    for _ in range(60):
        d,i=T.query(src@A.T+t); k=d<np.percentile(d,80); P,Q=src[k],outer_px[i[k]]
        mp,mq=P.mean(0),Q.mean(0); X,Y=P-mp,Q-mq; U,Sv,Vt=np.linalg.svd(Y.T@X/len(P)); D=np.eye(2)
        if np.linalg.det(U@Vt)<0: D[1,1]=-1
        sc=np.trace(np.diag(Sv)@D)/(X**2).sum()*len(P); A=sc*(U@D@Vt); t=mq-A@mp
    d,_=T.query(src@A.T+t); return A,t,float(np.median(d)/sc),float(sc)
def boards():
    g=json.load(open('hardware/overlay/overlay_mm.json')); S={k:np.array(v) for k,v in g['shapes'].items()}
    f=json.load(open('art/faces/faces.json'))['gauges']; P={k:np.array(f[k]['pivot_mm']) for k in f}
    P['speedo']=P['speedo']+[6,0]; P['tach']=P['tach']+[6,0]
    sq=lambda c,w,h: box(c[0]-w/2,c[1]-h/2,c[0]+w/2,c[1]+h/2)
    sp=sq(P['speedo'],115,115); ta=Point(*P['tach']).buffer(95.86/2,256)
    u=np.vstack([S['temp'],S['fuel']]); uc=(u.min(0)+u.max(0))/2
    for sh in np.arange(0,20,0.25):
        tf=sq(uc-[sh,0],127.7,87.45)
        if tf.distance(sp)>=1.0: break
    return {'speedo: Waveshare ESP32-P4 3.4C, 115 sq':sp,'tach: Waveshare 2.8in round, ~Ø96':ta,'temp+fuel: Waveshare 5in, 127.7x87.45':tf}
if __name__=='__main__':
    g=json.load(open('hardware/overlay/overlay_mm.json')); FACE=SP(g['shapes']['outer'])
    outer,inner=segment(); A,t,res,sc=register(outer,FACE); Ai=np.linalg.inv(A)
    IN=SP(((inner-t)@Ai.T)*[1,-1]).buffer(0).intersection(FACE.buffer(-1.0))
    IN=max(IN.geoms,key=lambda p:p.area) if IN.geom_type!='Polygon' else IN
    IN=IN.simplify(0.3)
    g['shapes']['frame_flange_inner']=[list(map(lambda v: round(v,3),p)) for p in IN.exterior.coords[:-1]]
    g['frame_fit']=dict(source=REF,residual_mm=round(res,2),scale_px_per_mm=round(sc,3),note='face outline = flange outer edge; frame_flange_inner = inner edge of the flange band (green), +/-1 mm')
    json.dump(g,open('hardware/overlay/overlay_mm.json','w'),indent=1)
    B=boards(); rep=[]
    fig,ax=plt.subplots(figsize=(16,6.4)); band=FACE.difference(IN)
    for geom in (band.geoms if hasattr(band,'geoms') else [band]):
        x,y=geom.exterior.xy; ax.fill(x,y,color='#7fd43b',alpha=0.55,lw=0)
        for h in geom.interiors: x,y=h.xy; ax.fill(x,y,color='white')
    x,y=FACE.exterior.xy; ax.plot(x,y,'k-',lw=1.2,label='flange outer edge = face outline (must remain)')
    x,y=IN.exterior.xy; ax.plot(x,y,'g-',lw=1.2,label='flange inner edge (inside it: free to trim)')
    cols=['#1f9bd7','#d43b3b','#2a9d4a']
    for (n,b),c in zip(B.items(),cols):
        x,y=b.exterior.xy; ax.plot(x,y,'-',color=c,lw=1.6,label=n)
        into=b.intersection(band); past=b.difference(FACE)
        for geom,colr in ((into,'#f2a900'),(past,'#ff0000')):
            for gg in (geom.geoms if hasattr(geom,'geoms') else [geom]):
                if not gg.is_empty and gg.area>0.5: x,y=gg.exterior.xy; ax.fill(x,y,color=colr,alpha=0.85,lw=0)
        def maxd(geom,ref):
            pts=[p for gg in (geom.geoms if hasattr(geom,'geoms') else [geom]) if not gg.is_empty for p in gg.exterior.coords]
            return max([ref.exterior.distance(Point(p)) for p in pts if not ref.contains(Point(p))],default=0)
        rep.append(dict(board=n,into_flange_mm2=round(into.area),max_into_flange_mm=round(maxd(b,IN),1),past_outer_mm2=round(past.area),max_past_outer_mm=round(maxd(b,FACE),1)))
    ax.fill([],[],color='#f2a900',label='board over the flange (trim needed)'); ax.fill([],[],color='#ff0000',label='board past the outer edge (not allowed)')
    ax.set_aspect('equal'); ax.grid(alpha=.25); ax.legend(loc='lower center',ncol=3,fontsize=8,bbox_to_anchor=(0.5,-0.32))
    ax.set_title('Mounting frame vs v3 boards (mm, front view). Frame from IMG_7629, registered to the face outline (residual %.1f mm)'%res,fontsize=10)
    plt.tight_layout(); plt.savefig('docs/frame/frame_fit.png',dpi=110,bbox_inches='tight')
    xs=[(x,IN.intersection(box(x-0.1,-80,x+0.1,80)).bounds) for x in range(-180,181,30)]
    json.dump(dict(report=rep,inner_bbox=[round(v,1) for v in IN.bounds],inner_height_at_x={str(x):[round(b[1],1),round(b[3],1)] for x,b in xs if b}),open('docs/frame/frame_fit.json','w'),indent=1)
    print(json.dumps(rep,indent=0)); print('inner bbox',np.round(IN.bounds,1))
