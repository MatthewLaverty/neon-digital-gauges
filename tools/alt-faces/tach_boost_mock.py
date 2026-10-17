"""Day and night mock: boost sub-dial (half the tach tick-ring radius) concentric with the tach; shortened boost needle
drawn beneath the tach needle so its hub hides under the tach hub.
Night: the boost print goes through the same night mapping as the tach print (white -> printing orange), both needles
use the night needle red, and the hub halo is the tach's. The odometer/trip readout is drawn as on the plain tach."""
import sys, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0,'tools/alt-faces'); sys.path.insert(0,'tools/night'); sys.path.insert(0,'tools/odo')
import boost_face as bf, night_preview as npv, seg7
F=json.load(open('art/faces/faces.json'))['gauges']['tach']; N=json.load(open('art/needles/needles.json'))['gauges']['tach']
TACH_RO=214.0; BOOST_RO=TACH_RO/2
def tach_angle(rpm): return -115.6+rpm*0.02885
face=np.asarray(Image.open('art/faces/tach_480.png').convert('RGB')).astype(float)
RPM_LABEL=(170,149,310,174)   # RPMX1000 bbox (x0,y0,x1,y1), removed in boost mode per owner 2026-10-16
boost_face=face.copy(); x0,y0,x1,y1=RPM_LABEL; boost_face[y0:y1,x0:x1]=0
dial=bf.build(BOOST_RO); S=dial.shape[0]; cx,cy=F['pivot_px']
def compose(rpm,mpa,with_boost=True,night=False,odo=('odo',123456)):
    img=(boost_face if with_boost else face).copy()
    if with_boost:
        x0=int(round(cx-S/2)); y0=int(round(cy-S/2))
        reg=img[y0:y0+S,x0:x0+S]; img[y0:y0+S,x0:x0+S]=np.maximum(reg,dial[...,None]*255)   # white print on the same black plane
    if night:
        img=npv.night_face(img.astype(np.uint8)); hm=npv.halo(img.shape,F['pivot_px'],F['hub_radius_mm']*F['px_per_mm'])
        img=img*(1-hm[...,None])+npv.C[npv.H['color']]*hm[...,None]
    if odo: img=seg7.draw_field(img,*odo)
    im=Image.fromarray(np.clip(img,0,255).astype(np.uint8)).convert('RGBA')
    nd=npv.needle_img(f"art/needles/{N['needle_png']}",night); px,py=N['pivot_px']
    def put(ndl,pv,ang):
        W=int(2*max(ndl.size)+4); cv=Image.new('RGBA',(W,W)); cv.paste(ndl,(int(W/2-pv[0]),int(W/2-pv[1])))
        cv=cv.rotate(-ang,resample=Image.BICUBIC,center=(W/2,W/2)); im.alpha_composite(cv,(int(cx-W/2),int(cy-W/2)))
    if with_boost:
        k=bf.GEOM['needle_len']*BOOST_RO/(N['size_px'][1]-(N['size_px'][1]-py))   # boost needle length / tach needle length
        bn=nd.resize((max(3,round(nd.width*k)),round(nd.height*k)),Image.LANCZOS)
        put(bn,(px*k,py*k),bf.angle_for(mpa))
    put(nd,(px,py),tach_angle(rpm))
    hub=Image.open(f"art/needles/{N['hub_png']}").convert('RGBA'); im.alpha_composite(hub,(int(cx-hub.width/2),int(cy-hub.height/2)))
    return im.convert('RGB')
if __name__=='__main__':
    cases=[('stock tach, 3000 rpm',3000,0,False),('idle: 850 rpm, -0.06 MPa',850,-0.06,True),('pull: 5500 rpm, +0.10 MPa',5500,0.10,True)]
    out=Image.new('RGB',(3*490-10,2*(480+34)),(30,30,30)); d=ImageDraw.Draw(out)
    for row,nt in enumerate((False,True)):
        for i,(t,r,b,w) in enumerate(cases):
            y=row*514; out.paste(compose(r,b,w,nt),(i*490,y+34)); d.text((i*490+6,y+10),('night: ' if nt else 'day: ')+t,fill=(220,220,220))
    out.save('art/preview/tach_boost_preview.png'); compose(5500,0.10).save('art/preview/tach_boost_480.png')
    compose(5500,0.10,night=True).save('art/preview/tach_boost_480_night.png'); print('ok')
