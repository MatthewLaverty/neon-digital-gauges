"""Night-mode preview using art/night_palette.json (sampled from the owner's stock-cluster night photo).
Day face layers -> night: white printing -> printing_orange; needle-orange ticks/digits (tach 6500+, 7, 8, H tick, E tick) -> red_ticks;
km/h blue and cold tick -> kmh_and_cold_blue; needles -> needles red; plus a soft halo around each hub.
Anti-aliasing is preserved by scaling the target colour by pixel brightness relative to the day reference colour."""
import json, colorsys, numpy as np
from PIL import Image, ImageDraw
F=json.load(open('art/faces/faces.json'))['gauges']; N=json.load(open('art/needles/needles.json'))
P=json.load(open('art/night_palette.json')); H=P['halo']
C={k:np.array(P[k],float) for k in ('printing_orange','kmh_and_cold_blue','red_ticks','needles')}
def hue_sat(a):
    mx=a.max(2); mn=a.min(2); d=mx-mn; sat=np.where(mx>0,d/np.maximum(mx,1),0)
    r,g,b=a[...,0],a[...,1],a[...,2]; dd=np.maximum(d,1e-6)
    h=np.where(mx==r,((g-b)/dd)%6,np.where(mx==g,(b-r)/dd+2,(r-g)/dd+4))*60
    return h,sat,mx
def night_face(rgb):
    a=rgb.astype(float); h,s,v=hue_sat(a); out=np.zeros_like(a)
    white=s<0.25; red=(~white)&((h<40)|(h>330)); blue=(~white)&(h>150)&(h<260)
    out[white]=(a[white].min(1)/255.0)[:,None]*C['printing_orange']
    out[red]=np.minimum(v[red]/232.0,1)[:,None]*C['red_ticks']
    out[blue]=np.minimum(v[blue]/223.0,1)[:,None]*C['kmh_and_cold_blue']
    return np.clip(out,0,255)
def halo(shape,c,r):
    yy,xx=np.mgrid[:shape[0],:shape[1]]; d=np.hypot(xx-c[0],yy-c[1])/r
    w=(H['outer_hub_radii']-H['inner_hub_radii'])/2.2
    g=np.where(d<H['inner_hub_radii'],1.0,np.exp(-((d-H['inner_hub_radii'])/w)**2))
    g[d>H['outer_hub_radii']*1.3]=0
    return g*H['peak_opacity']
def needle_img(path,night):
    nd=Image.open(path).convert('RGBA')
    if not night: return nd
    a=np.asarray(nd).astype(float); lum=a[...,:3].max(2)/232.0
    a[...,:3]=np.clip(lum[...,None],0,1)*C['needles']; return Image.fromarray(a.astype(np.uint8),'RGBA')
def compose(k,angle,night,face_png=None):
    g=F[k]; n=N['gauges'][k]; face=np.asarray(Image.open(face_png or f'art/faces/{k}_480.png').convert('RGB'))
    img=face.astype(float)
    if night:
        img=night_face(face); hc=C[H['color']]
        hm=halo(img.shape,g['pivot_px'],g['hub_radius_mm']*g['px_per_mm']); img=img*(1-hm[...,None])+hc*hm[...,None]
    im=Image.fromarray(img.astype(np.uint8)).convert('RGBA')
    nd=needle_img(f"art/needles/{n['needle_png']}",night); px,py=n['pivot_px']
    W=int(2*max(nd.size)+4); cv=Image.new('RGBA',(W,W)); cv.paste(nd,(int(W/2-px),int(W/2-py)))
    cv=cv.rotate(-angle,resample=Image.BICUBIC,center=(W/2,W/2)); cx,cy=g['pivot_px']
    im.alpha_composite(cv,(int(cx-W/2),int(cy-W/2)))
    hub=Image.open(f"art/needles/{n['hub_png']}").convert('RGBA'); im.alpha_composite(hub,(int(cx-hub.size[0]/2),int(cy-hub.size[1]/2)))
    return im.convert('RGB')
if __name__=='__main__':
    ang={'tach':-60,'speedo':-75,'temp':-100,'fuel':-80}
    out=Image.new('RGB',(480*4+30,480*2+70),(30,30,30)); d=ImageDraw.Draw(out)
    for i,k in enumerate(('temp','fuel','speedo','tach')):
        out.paste(compose(k,ang[k],False),(i*490,30)); out.paste(compose(k,ang[k],True),(i*490,520))
        compose(k,ang[k],True).save(f'art/preview/{k}_480_night.png')
    d.text((8,8),'Day (top) vs night (bottom), night palette sampled from stock-cluster night photo; halo to 1.65 hub radii',fill=(220,220,220))
    out.save('art/preview/night_mode_preview.png'); print('ok')
