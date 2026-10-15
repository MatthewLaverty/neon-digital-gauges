import numpy as np, json
exec(open('rectify.py').read().split("r0=resid(x0)")[0])
meta=json.load(open('../scans/master_meta.json')); K=237.5/25.4; Ox,Oy=meta['origin_px68']
Aff=np.array([[10/K,0,-10*(Ox/K-205)],[0,10/K,10*(68-Oy/K)],[0,0,1]])
TP=np.array([[1708,2390],[1943,2398],[2178,2406],[2414,2414],[2650,2424],[2889,2433],[3129,2444],[3370,2455]],float)
Q=np.c_[TP,np.ones(8)]@Aff.T; TP=Q[:,:2]/Q[:,2:]
def resid2(x,w):
    r=resid(x); h=x[:8]; Qt=apply(h,TP)*S0; d=np.hypot(*np.diff(Qt,axis=0).T)
    return np.r_[r, w*(d-d.mean())]
x=np.r_[x0]
for w in [0,1,3,10]:
    s=least_squares(lambda z: resid2(z,w),x0,x_scale='jac')
    r=resid(s.x); h=s.x[:8]; Qt=apply(h,TP)*S0; d=np.hypot(*np.diff(Qt,axis=0).T)
    print('w',w,'circle rms',round(np.sqrt((r[:-4]**2).mean()),3),'tape spacing',d.round(1), 'sd%',round(100*d.std()/d.mean(),2))
