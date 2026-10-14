import numpy as np, cv2, json, os
from PIL import Image
OUT='/home/user/workspace/neon-digital-gauges/art/needles'; os.makedirs(OUT,exist_ok=True)
soft=np.load('needle_soft.npy'); info=json.load(open('needles_meas.json'))
faces=json.load(open('/home/user/workspace/neon-digital-gauges/art/faces/faces.json'))['gauges']
OR=json.load(open('colors.json'))['ORANGE']
px,py,hr=3126,736,73
b=(soft>0.5).astype(np.uint8); n,lab,st,_=cv2.connectedComponentsWithStats(b,8)
comp=cv2.dilate((lab==info['tach']['comp']).astype(np.uint8),np.ones((5,5),np.uint8))
a=(soft*comp).astype(np.float32)
Rm=cv2.getRotationMatrix2D((px,py),-(90-info['tach']['angle_deg']),1.0)
# angle convention: rotate so direction 179.08 -> 90
Rm=cv2.getRotationMatrix2D((px,py),90-info['tach']['angle_deg'],1.0)
ar=cv2.warpAffine(a,Rm,(a.shape[1],a.shape[0]),flags=cv2.INTER_LINEAR)
L=int(np.ceil(info['tach']['len_px']))+6
crop=ar[py-L:py+1, px-30:px+31].copy()   # pivot at bottom-center (row L, col 30)
# check orientation
rows=np.nonzero(crop.max(1)>0.5)[0]; print('rows with needle',rows.min(),rows.max(),'of',crop.shape)
# extend base under hub: copy profile from just outside hub edge down to pivot
ref=crop[L-(hr+10)].copy()
for r in range(L-(hr+10),L+1): crop[r]=np.maximum(crop[r],ref)
# symmetrize (photo needle is symmetric by design) and clean
crop=np.maximum(crop,crop[:,::-1])*0.5+np.minimum(crop,crop[:,::-1])*0.5
crop=np.clip((crop-0.15)/0.7,0,1)
crop=cv2.GaussianBlur(crop,(0,0),0.6)
np.save('needle_master_10pxmm.npy',crop)
def save(alpha,name):
    rgba=np.zeros(alpha.shape+(4,),np.uint8); rgba[...,:3]=OR; rgba[...,3]=(alpha*255).round().astype(np.uint8)
    Image.fromarray(rgba,'RGBA').save(name)
save(crop,OUT+'/needle_master_10pxmm.png')
meta={'color_rgb':OR,'orientation':'points straight up; rotate about pivot_px','master':{'px_per_mm':10,'pivot_px':[30,L],'length_mm':info['tach']['len_mm']},'gauges':{}}
lens={'temp':info['temp']['len_mm'],'fuel':info['fuel']['len_mm'],'tach':info['tach']['len_mm'],'speedo':info['speedo']['len_mm']}
for k,f in faces.items():
    s=f['px_per_mm']/10.0
    ly=s*(lens[k]/info['tach']['len_mm']) if k=='speedo' else s   # speedo: stretch length only
    sx=s
    h,w=crop.shape
    W=int(np.ceil(w*sx))|1; Hh=int(np.ceil(h*ly))+2
    M=np.array([[sx,0,(W-1)/2-sx*30],[0,ly,(Hh-2)-ly*L]],np.float32)
    src=cv2.GaussianBlur(crop,(0,0),0.45/min(sx,ly))
    img=cv2.warpAffine(src,M,(W,Hh),flags=cv2.INTER_LINEAR)
    save(img,f'{OUT}/needle_{k}.png')
    # hub cap, supersampled
    r=f['hub_radius_mm']*f['px_per_mm']; D=int(np.ceil(2*r))+4; SS=8
    yy,xx=np.mgrid[0:D*SS,0:D*SS]/SS; c=(D-1)/2+0.5/SS*0; d=np.hypot(xx-D/2,yy-D/2)
    al=(d<=r).astype(np.float32); rim=((d<=r)&(d>r-max(1.2,0.06*r))).astype(np.float32)
    al=cv2.resize(al,(D,D),interpolation=cv2.INTER_AREA); rim=cv2.resize(rim,(D,D),interpolation=cv2.INTER_AREA)
    rgba=np.zeros((D,D,4),np.uint8); col=np.array([20,20,20])+rim[...,None]*np.array([28,28,28])
    rgba[...,:3]=col.astype(np.uint8); rgba[...,3]=(al*255).astype(np.uint8)
    Image.fromarray(rgba,'RGBA').save(f'{OUT}/hub_{k}.png')
    meta['gauges'][k]={'needle_png':f'needle_{k}.png','size_px':[W,Hh],'pivot_px':[(W-1)/2,Hh-2],'length_mm':round(lens[k] if k=='speedo' else info['tach']['len_mm'],2),
        'measured_photo_length_mm':round(lens[k],2),'px_per_mm':f['px_per_mm'],'hub_png':f'hub_{k}.png','hub_diameter_px':D,'hub_radius_mm':f['hub_radius_mm'],
        'rest_angle_deg_photo':round(info[k]['angle_deg'],2)}
    print(k,meta['gauges'][k]['size_px'],meta['gauges'][k]['pivot_px'])
json.dump(meta,open(OUT+'/needles.json','w'),indent=1)
