"""Night-mode preview: white printing -> needle orange (A8-mask recolor), coloured layers unchanged,
plus a soft glow around the needle hub. Sampled from the owner's night photo (2026-10-14):
un-blown glyph edges ~RGB 235,54,40 ~= needle orange 232,77,61."""
import json, numpy as np
from PIL import Image, ImageDraw, ImageFont
F=json.load(open('art/faces/faces.json'))['gauges']; N=json.load(open('art/needles/needles.json'))
ORANGE=np.array(N['color_rgb'],float)
HALO=dict(inner=1.0, outer=2.3, peak=0.45)   # radii in hub radii, peak opacity
def night_face(rgb):
    a=rgb.astype(float); mx=a.max(2); mn=a.min(2); sat=(mx-mn)/np.maximum(mx,1)
    white=(sat<0.25)                                  # low-saturation pixels = white printing (incl. anti-aliasing)
    alpha=(mn/255.0)*white                            # A8 mask: brightness of the white print
    out=a.copy()
    out[white]=0
    out+=alpha[...,None]*ORANGE
    return np.clip(out,0,255), alpha
def halo(shape,c,r):
    yy,xx=np.mgrid[:shape[0],:shape[1]]; d=np.hypot(xx-c[0],yy-c[1])/r
    g=np.where(d<HALO['inner'],1.0,np.exp(-((d-HALO['inner'])/((HALO['outer']-HALO['inner'])/2.2))**2))
    g[d>HALO['outer']*1.3]=0
    return g*HALO['peak']
def compose(k,angle,night):
    g=F[k]; n=N['gauges'][k]; face=np.asarray(Image.open(f'art/faces/{k}_480.png').convert('RGB'))
    img=face.astype(float)
    if night:
        img,_=night_face(face)
        hr=g['hub_radius_mm']*g['px_per_mm']; h=halo(img.shape,g['pivot_px'],hr)
        img=img*(1-h[...,None])+ORANGE*h[...,None]
    im=Image.fromarray(img.astype(np.uint8)).convert('RGBA')
    nd=Image.open(f"art/needles/{n['needle_png']}").convert('RGBA'); px,py=n['pivot_px']
    W=int(2*max(nd.size)+4); canvas=Image.new('RGBA',(W,W)); canvas.paste(nd,(int(W/2-px),int(W/2-py)))
    canvas=canvas.rotate(-angle,resample=Image.BICUBIC,center=(W/2,W/2))
    cx,cy=g['pivot_px']; im.alpha_composite(canvas,(int(cx-W/2),int(cy-W/2)))
    hub=Image.open(f"art/needles/{n['hub_png']}").convert('RGBA'); im.alpha_composite(hub,(int(cx-hub.size[0]/2),int(cy-hub.size[1]/2)))
    return im.convert('RGB')
if __name__=='__main__':
    ang={'tach':40,'speedo':-30,'temp':-120,'fuel':-80}
    rows=[]
    for k in ('temp','fuel','speedo','tach'):
        rows.append((compose(k,ang[k],False),compose(k,ang[k],True)))
    W=480*4+30; out=Image.new('RGB',(W,480*2+70),(30,30,30)); d=ImageDraw.Draw(out)
    for i,(day,night) in enumerate(rows):
        out.paste(day,(i*490,30)); out.paste(night,(i*490,30+480+10))
    d.text((8,8),'Day (top) vs night (bottom): white printing -> needle orange, coloured layers and needles unchanged, hub halo',fill=(220,220,220))
    out.save('art/preview/night_mode_preview.png'); print('ok')
