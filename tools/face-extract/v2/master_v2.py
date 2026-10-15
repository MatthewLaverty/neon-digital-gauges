import numpy as np, cv2, json
from PIL import Image
Hn=json.load(open('H_new_to_old.json')); Hf=np.array(json.load(open('final_frame.json'))['Hf_old_to_new'])
W,Hh=4000,1360
src={'temp':'IMG_7575','fuel':'IMG_7574','speedo':'IMG_7576','tach':'IMG_7577'}
cuts=[(0,1100,'temp'),(1100,1500,'fuel'),(1500,2580,'speedo'),(2580,4000,'tach')]
warped={}
for g,n in src.items():
    a=np.asarray(Image.open(n+'.png').convert('RGB'))
    warped[g]=cv2.warpPerspective(a,Hf@np.array(Hn[n]),(W,Hh),flags=cv2.INTER_AREA)
mos=np.zeros((Hh,W,3),np.uint8)
for x0,x1,g in cuts: mos[:,x0:x1]=warped[g][:,x0:x1]
Image.fromarray(mos).save('master_v2.png')
for g in warped: Image.fromarray(warped[g]).save(f'warp_{g}.png')
# old overlay & old master/w69 into new frame
old=np.asarray(Image.open('../scans/master_10pxmm.png').convert('RGB')); Image.fromarray(cv2.warpPerspective(old,Hf,(W,Hh),flags=cv2.INTER_LINEAR)).save('oldmaster_v2.png')
w69=np.asarray(Image.open('../scans/w69.png').convert('RGB')); Image.fromarray(cv2.warpPerspective(w69,Hf,(W,Hh),flags=cv2.INTER_LINEAR)).save('w69_v2.png')
geo=json.load(open('../scans/overlay_mm.json'))
def mm2old(p): p=np.asarray(p,float); return np.c_[(p[:,0]+205)*10,(68-p[:,1])*10]
def ap(H,P): Q=np.c_[P,np.ones(len(P))]@H.T; return Q[:,:2]/Q[:,2:]
def px2mm(P): return np.c_[P[:,0]/10-205,68-P[:,1]/10]
ng=json.loads(json.dumps(geo))
for k,v in geo['shapes'].items(): ng['shapes'][k]=px2mm(ap(Hf,mm2old(v))).round(3).tolist()
ng['mount_holes']['centers']=px2mm(ap(Hf,mm2old(geo['mount_holes']['centers']))).round(3).tolist()
ng['mount_holes']['d']=round(4.0*json.load(open('final_frame.json'))['scale'],2)
for k in ['speedo_center','tach_center']: ng[k]=px2mm(ap(Hf,mm2old([geo[k]])))[0].round(3).tolist()
ng['speedo_arc_r']=geo['speedo_arc_r']*json.load(open('final_frame.json'))['scale']; ng['tach_r']=geo['tach_r']*json.load(open('final_frame.json'))['scale']
ng['origin']='speedo hole arc center (v1 frame), rectified v2 2026-10-14'; ng['px_per_in']=None
ng['rectification']='v1 geometry mapped through homography fit to circular, evenly spaced tach/speedo ticks + uniform 7568 tape spacing'
json.dump(ng,open('overlay_mm_v2.json','w'),indent=1)
vis=mos.copy()
for k,v in ng['shapes'].items():
    p=np.c_[(np.array(v)[:,0]+205)*10,(68-np.array(v)[:,1])*10]; cv2.polylines(vis,[p.astype(np.int32)],True,(255,0,255),3)
Image.fromarray(vis).resize((2000,680)).save('master_v2_vis.jpg')
for k in ['temp','fuel','speedo','tach']:
    a=np.array(ng['shapes'][k]); print(k,'W x H',np.ptp(a[:,0]).round(1),np.ptp(a[:,1]).round(1))
a=np.array(ng['shapes']['outer']); print('outer',np.ptp(a[:,0]).round(1),np.ptp(a[:,1]).round(1))
