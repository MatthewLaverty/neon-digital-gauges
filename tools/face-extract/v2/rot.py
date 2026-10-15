import numpy as np, json, cv2
ANG=2.17  # deg, CCW visual (text measured 2.05-2.30 cw, mean 2.17)
R=np.vstack([cv2.getRotationMatrix2D((2050,680),ANG,1.0),[0,0,1]])
def ap(P): P=np.atleast_2d(np.asarray(P,float)); Q=np.c_[P,np.ones(len(P))]@R.T; return Q[:,:2]
ff=json.load(open('bak_v2a/final_frame.json')); ff['Hf_old_to_new']=(R@np.array(ff['Hf_old_to_new'])).tolist(); ff['level_rotation_deg_ccw']=ANG
for k in ('tach','speedo'):
    c=ap(ff['fit'][k]['center_px'])[0]; ff['fit'][k]['center_px']=c.tolist(); ff['fit'][k]['center_mm']=[c[0]/10-205,68-c[1]/10]; ff['fit'][k]['theta0_deg_imgYdown']-=ANG
for k in ('temp','fuel'):
    c=ap(ff['fit'][k]['arc_center_px'])[0]; ff['fit'][k]['arc_center_px']=c.tolist(); ff['fit'][k]['arc_center_mm']=[c[0]/10-205,68-c[1]/10]
json.dump(ff,open('final_frame.json','w'),indent=1)
fv=json.load(open('bak_v2a/fit_v2.json'))
for k in ('tach','speedo'): fv[k]['center_px']=ff['fit'][k]['center_px']; fv[k]['theta0_deg_imgYdown']=ff['fit'][k]['theta0_deg_imgYdown']
for k in ('temp','fuel'):
    fv[k]['arc_center_px']=ff['fit'][k]['arc_center_px']; fv[k]['tick_pivot_px']=ap(fv[k]['tick_pivot_px'])[0].tolist()
json.dump(fv,open('fit_v2.json','w'),indent=1)
mk=json.load(open('bak_v2a/masks_v2.json'))
circ=[]
for x,y,r in mk['circles']:
    if [x,y]==[3329,862]: x,y,r=3326,862,19      # tach 8 stop pin: tighter, clears the numeral
    c=ap([x,y])[0]; circ.append([float(c[0]),float(c[1]),r])
mk['circles']=circ; mk['polys']=[ap(P).round(1).tolist() for P in mk['polys']]
mk['bushings']=[[*ap(c)[0].tolist(),82] for c in [(836.5,650.5),(1385.5,668.5),(2053.5,692.5),(3110.5,726.5)]]
json.dump(mk,open('masks_v2.json','w'),indent=1)
print('done', ff['fit']['tach']['center_px'], ff['fit']['speedo']['center_px'])
