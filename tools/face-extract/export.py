import numpy as np, cv2, json, os
from PIL import Image
OUT='/home/user/workspace/neon-digital-gauges/art'; os.makedirs(OUT+'/faces',exist_ok=True); os.makedirs(OUT+'/preview',exist_ok=True)
face=np.asarray(Image.open('face_clean_10pxmm.png'))
SH={'temp':(0.79,0.19),'fuel':(-0.16,0.06),'speedo':(-0.43,0.14),'tach':(-8.08,-6.41)}  # ECC: face px = hole-frame px + t
g=json.load(open('overlay_mm.json')); S=g['shapes']
def m2p(p): p=np.asarray(p,float); return np.c_[(p[:,0]+205)*10,(68-p[:,1])*10]
pv={'temp':(832,660,73),'fuel':(1378,674,71),'speedo':(2048,700,93),'tach':(3126,736,73)}
meta={'source_scale_px_per_mm':10,'notes':'pivot_px = needle rotation center in the 480x480 image; mm frame origin = speedo hole arc center, +y up','gauges':{}}
for k in ['temp','fuel','speedo','tach']:
    hp=m2p(S[k]); px,py,hr=pv[k]; t=np.array(SH[k]); px,py=px-t[0],py-t[1]
    if k in ('speedo','tach'):
        mm=np.asarray(S[k]); keep=np.ones(len(mm),bool)
        if k=='speedo': keep=~((mm[:,0]>30)&(mm[:,1]<-25))
        d=np.hypot(hp[keep,0]-px,hp[keep,1]-py)
        if k=='tach':
            d=np.sort(d); dmax=np.percentile(d,90)
        else: dmax=d.max()
        cx,cy,Rr=px,py,dmax+10
    else:
        (cx,cy),r=cv2.minEnclosingCircle(hp.astype(np.float32)); Rr=r+10
    Rr=float(np.ceil(Rr)); s=480/(2*Rr)
    M=np.array([[s,0,240-s*(cx+t[0])],[0,s,240-s*(cy+t[1])]])
    Mh=np.array([[s,0,240-s*cx],[0,s,240-s*cy]])
    # pre-blur for downsampling then warp
    sig=max(0,0.5/s-0.5) if s<1 else 0
    src=cv2.GaussianBlur(face,(0,0),0.45/s) if s<1 else face
    img=cv2.warpAffine(src,M,(480,480),flags=cv2.INTER_LINEAR,borderValue=(0,0,0))
    hh=(np.c_[hp,np.ones(len(hp))]@Mh.T); hm=np.zeros((480,480),np.uint8); cv2.fillPoly(hm,[np.round(hh).astype(np.int32)],255)
    hm=cv2.GaussianBlur(cv2.dilate(hm,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(int(6*s*10)|1,)*2)),(0,0),2)/255.0
    img=(img*hm[...,None]).astype(np.uint8)
    Image.fromarray(img).save(f'{OUT}/faces/{k}_480.png')
    # preview with hole outline
    pr=img.copy()
    cv2.polylines(pr,[np.round(hh).astype(np.int32)],True,(255,0,255),1,cv2.LINE_AA)
    pvx,pvy=s*px+Mh[0,2],s*py+Mh[1,2]
    cv2.drawMarker(pr,(int(round(pvx)),int(round(pvy))),(0,255,0),cv2.MARKER_CROSS,12,1)
    Image.fromarray(pr).save(f'{OUT}/preview/{k}_480_holecheck.png')
    meta['gauges'][k]={'px_per_mm':round(s*10,4),'image_diameter_mm':round(2*Rr/10,2),
        'image_center_mm':[round(cx/10-205,2),round(68-cy/10,2)],
        'pivot_mm':[round(px/10-205,2),round(68-py/10,2)],
        'pivot_px':[round(pvx,1),round(pvy,1)],'hub_radius_mm':round(hr/10,2),
        'hole_bbox_mm':[round(v,2) for v in [*np.asarray(S[k]).min(0),*np.asarray(S[k]).max(0)]]}
    if k=='speedo':
        def r2(x0,y0,x1,y1): a=np.array([[x0,y0],[x1,y1]],float); b=a*s+M[:,2]; return [round(v,1) for v in b.ravel()]
        meta['gauges'][k]['odometer_window_px']=r2(1860,955,2170,1015)
        meta['gauges'][k]['trip_window_mm']=[2400/10-205,68-1040/10,2700/10-205,68-975/10]
    print(k,meta['gauges'][k])
json.dump(meta,open(OUT+'/faces/faces.json','w'),indent=1)
Image.fromarray(face).save(OUT+'/faces/cluster_master_10pxmm.png')
