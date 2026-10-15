import numpy as np, cv2, json
from scipy.optimize import least_squares
T=json.load(open('ticks_old.json')); tach=np.array(T['tach']); sp=np.array(T['speedo'])[:16]
lab=np.load('lab_mos.npy')
# arcs of fuel and temp: thin large components
n=lab.max()
arcs={}
for k,(x0,x1) in {'temp':(400,800),'fuel':(950,1300)}.items():
    sub=lab[250:850,x0:x1]; ids,cnt=np.unique(sub[sub>0],return_counts=True)
    i=ids[np.argmax(cnt)]; ys,xs=np.nonzero(lab==i); 
    P=np.c_[xs,ys].astype(float); P=P[::max(1,len(P)//400)]; arcs[k]=P
    print(k,'arc pts',len(P),'bbox',xs.min(),xs.max(),ys.min(),ys.max())
N0=np.array([2000.,700.]); S0=1000.
def nrm(P): return (np.asarray(P)-N0)/S0
def den(P): return np.asarray(P)*S0+N0
def apply(h,P):
    G=np.append(h,1).reshape(3,3); Q=np.c_[nrm(P),np.ones(len(P))]@G.T; return Q[:,:2]/Q[:,2:]
fixed=np.array([[3126,736],[2048,700.]])
def unpack(x):
    h=x[:8]; return h,x[8:]
def resid(x):
    h,q=unpack(x); r=[]; j=0
    for P in (tach,sp):
        cx,cy,Ro,Ri,t0,dt=q[j:j+6]; j+=6
        i=np.arange(len(P)); th=t0+i*dt
        for E,R in ((P[:,:2],Ro),(P[:,2:],Ri)):
            Q=apply(h,E); r.append((Q[:,0]-(cx+R*np.cos(th))));r.append((Q[:,1]-(cy+R*np.sin(th))))
    for k in ('temp','fuel'):
        cx,cy,R=q[j:j+3]; j+=3; Q=apply(h,arcs[k]); r.append(0.3*(np.hypot(Q[:,0]-cx,Q[:,1]-cy)-R))
    r.append(10*(apply(h,fixed)-nrm(fixed)).ravel())
    return np.concatenate(r)*S0
def init(P,c):
    c=nrm([c])[0]; E=nrm(P[:,:2]); I=nrm(P[:,2:])
    th=np.unwrap(np.arctan2(E[:,1]-c[1],E[:,0]-c[0])); 
    return [c[0],c[1],np.hypot(*(E-c).T).mean(),np.hypot(*(I-c).T).mean(),th[0],np.mean(np.diff(th))]
x0=np.r_[1,0,0,0,1,0,0,0, init(tach,(3126,736)), init(sp,(2048,700))]
for k,c in (('temp',(832,660)),('fuel',(1378,674))):
    A=nrm(arcs[k]); x0=np.r_[x0, nrm([c])[0], np.hypot(*(A-nrm([c])[0]).T).mean()]
r0=resid(x0); 
sol=least_squares(resid,x0,x_scale='jac')
r1=sol.fun
print('rms before',round(np.sqrt((r0[:-4]**2).mean()),2),'after',round(np.sqrt((r1[:-4]**2).mean()),2))
h,q=unpack(sol.x); G=np.append(h,1).reshape(3,3)
# convert to pixel-space homography
Tn=np.array([[1/S0,0,-N0[0]/S0],[0,1/S0,-N0[1]/S0],[0,0,1]]); Gp=np.linalg.inv(Tn)@G@Tn; Gp/=Gp[2,2]
print('G pixel',Gp.round(6).tolist())
# diagnostics per gauge
j=0
for name,P in (('tach',tach),('speedo',sp)):
    cx,cy,Ro,Ri,t0,dt=q[j:j+6]; j+=6
    Q=apply(h,P[:,:2]); rr=np.hypot(Q[:,0]-cx,Q[:,1]-cy)*S0
    th=np.unwrap(np.arctan2(Q[:,1]-cy,Q[:,0]-cx)); 
    print(name,'center',den([[cx,cy]])[0].round(1),'R_out px',round(Ro*S0,1),'R_in',round(Ri*S0,1),'step deg',round(np.degrees(dt),3),'radial resid sd',round(rr.std(),2),'angle step range',np.degrees(np.diff(th)).min().round(2),np.degrees(np.diff(th)).max().round(2))
    # before
    c0=init(P,(3126,736) if name=='tach' else (2048,700))
# ellipse check after
for name,P in (('tach',tach),('speedo',sp)):
    Q=den(apply(h,P[:,:2])).astype(np.float32); (ex,ey),(a,b),ang=cv2.fitEllipse(Q); print(name,'ellipse ratio after',round(min(a,b)/max(a,b),4))
    (ex,ey),(a,b),ang=cv2.fitEllipse(P[:,:2].astype(np.float32)); print(name,'ellipse ratio before',round(min(a,b)/max(a,b),4))
json.dump({'G_old_to_rect':Gp.tolist(),'q':q.tolist()},open('G.json','w'))
