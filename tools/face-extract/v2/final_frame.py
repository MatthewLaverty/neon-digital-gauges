import numpy as np, json
exec(open('rectify2.py').read().split("x=np.r_[x0]")[0])
s=least_squares(lambda z: resid2(z,3),x0,x_scale='jac'); h=s.x[:8]; q=s.x[8:]
G=np.append(h,1).reshape(3,3); Tn=np.array([[1/S0,0,-N0[0]/S0],[0,1/S0,-N0[1]/S0],[0,0,1]]); Gp=np.linalg.inv(Tn)@G@Tn; Gp/=Gp[2,2]
Qt=apply(h,TP)*S0; d=np.hypot(*np.diff(Qt,axis=0).T); sc=254.0/d.mean()
def ap(H,P): P=np.atleast_2d(P); Q=np.c_[P,np.ones(len(P))]@H.T; return Q[:,:2]/Q[:,2:]
o=ap(Gp,[2050,680])[0]
Hf=np.array([[1,0,2050],[0,1,680],[0,0,1]])@np.diag([sc,sc,1])@np.array([[1,0,-o[0]],[0,1,-o[1]],[0,0,1]])@Gp
Hf/=Hf[2,2]
# gauge centers from fit (normalized -> old px -> via scale)
j=0; cent={}
for name in ('tach','speedo'):
    cx,cy,Ro,Ri,t0,dt=q[j:j+6]; j+=6
    c_rectpx=den([[cx,cy]])[0]
    c_new=(c_rectpx-o)*sc+[2050,680]
    cent[name]={'center_px':c_new.tolist(),'center_mm':[c_new[0]/10-205,68-c_new[1]/10],'R_tip_mm':Ro*S0*sc/10,'R_inner_mm':Ri*S0*sc/10,'theta0_deg_imgYdown':float(np.degrees(t0)),'step_deg':float(np.degrees(dt))}
for k in ('temp','fuel'):
    cx,cy,R=q[j:j+3]; j+=3; c_new=(den([[cx,cy]])[0]-o)*sc+[2050,680]
    cent[k]={'arc_center_px':c_new.tolist(),'arc_center_mm':[c_new[0]/10-205,68-c_new[1]/10],'arc_R_mm':R*S0*sc/10}
print('scale',round(sc,5)); print(json.dumps(cent,indent=0))
json.dump({'Hf_old_to_new':Hf.tolist(),'scale':sc,'fit':cent},open('final_frame.json','w'),indent=1)
