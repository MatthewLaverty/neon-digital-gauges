"""Preview: fuel face with the moved door arrow; normal vs low-fuel (pump + arrow yellow), day and night."""
import sys, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0,'tools/night'); import night_preview as npv
I=json.load(open('art/faces/fuel_icon.json')); Y=np.array(I['low_fuel_color_rgb'],float)
layer=np.asarray(Image.open('art/faces/fuel_icon_A8.png')).astype(float)/255
base=np.asarray(Image.open('art/faces/fuel_base_480.png').convert('RGB'))
def render(night,low,ang):
    b=npv.night_face(base) if night else base.astype(float)
    col=Y if low else (npv.C['printing_orange'] if night else np.array([255.,255,255]))
    img=b*(1-layer[...,None])+layer[...,None]*col
    g=npv.F['fuel']; n=npv.N['gauges']['fuel']
    if night:
        hm=npv.halo(img.shape,g['pivot_px'],g['hub_radius_mm']*g['px_per_mm']); img=img*(1-hm[...,None])+npv.C[npv.H['color']]*hm[...,None]
    im=Image.fromarray(np.clip(img,0,255).astype(np.uint8)).convert('RGBA')
    nd=npv.needle_img(f"art/needles/{n['needle_png']}",night); px,py=n['pivot_px']
    W=int(2*max(nd.size)+4); cv=Image.new('RGBA',(W,W)); cv.paste(nd,(int(W/2-px),int(W/2-py)))
    cv=cv.rotate(-ang,resample=Image.BICUBIC,center=(W/2,W/2)); cx,cy=g['pivot_px']; im.alpha_composite(cv,(int(cx-W/2),int(cy-W/2)))
    hub=Image.open(f"art/needles/{n['hub_png']}").convert('RGBA'); im.alpha_composite(hub,(int(cx-hub.width/2),int(cy-hub.height/2)))
    return im.convert('RGB')
cases=[('day, normal',False,False,-60),('day, low fuel',False,True,-108),('night, normal',True,False,-60),('night, low fuel',True,True,-108)]
out=Image.new('RGB',(4*490-10,480+34),(30,30,30)); d=ImageDraw.Draw(out)
for i,(t,nt,lo,a) in enumerate(cases): out.paste(render(nt,lo,a),(i*490,34)); d.text((i*490+6,10),t,fill=(220,220,220))
out.save('art/preview/fuel_lowfuel_preview.png'); print('ok')
