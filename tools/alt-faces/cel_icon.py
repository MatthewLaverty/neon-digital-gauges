"""Check-engine lamp for the fuel gauge (owner 2026-10-18, placeholder art until the owner supplies the final symbol).
Symbol: ISO 2575 F.01 'Engine' (application of ISO 7000-0640), traced from ISO 2575:2010 p.28 at 1200 dpi
(art/icons/engine_iso7000-0640_src.png). Placed directly under the fuel-pump icon, same width as the pump, same 8 px
gap as the pump-to-arrow gap. Hidden unless the Haltech CEL flag is on (0x3E4 byte 7 bit 7); lit in the low-fuel yellow.
Outputs art/faces/cel_icon_A8.png (480x480 alpha layer), art/faces/cel_icon.json, art/preview/fuel_cel_preview.png."""
import sys, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0,'tools/night'); import night_preview as npv
I=json.load(open('art/faces/fuel_icon.json')); Y=np.array(I['low_fuel_color_rgb'],float)
x0,y0,x1,y1=I['pump_bbox_px']; gap=round(I['gap_px'])
from PIL import ImageFilter
src=Image.open('art/icons/engine_iso7000-0640_src.png').convert('L')
src=src.filter(ImageFilter.MaxFilter(25))   # stroke ~40 -> ~64 src px, about 3 px at 49 px wide (closer to the pump glyph weight)
w=x1-x0; h=round(w*src.height/src.width)
icon=src.resize((w*4,h*4),Image.LANCZOS).resize((w,h),Image.LANCZOS)
cx=(x0+x1)/2; ix=round(cx-w/2); iy=y1+gap
L=Image.new('L',(480,480),0); L.paste(icon,(ix,iy)); L.save('art/faces/cel_icon_A8.png')
json.dump(dict(bbox_px=[ix,iy,ix+w,iy+h],symbol='ISO 2575 F.01 Engine (ISO 7000-0640), placeholder until owner art',
  color_rgb=list(map(int,Y)),visible='only while Haltech 0x3E4 byte 7 bit 7 (Check Engine Light) = 1; hub relays it in 0x6A3 byte 2 bit 1',
  faces='fuel level face; same position on the ethanol face (proposed)',layer='cel_icon_A8.png',
  note='needle passes over the icon between about 7/8 and F; needle is drawn on top'),open('art/faces/cel_icon.json','w'),indent=1)
pump=np.asarray(Image.open('art/faces/fuel_icon_A8.png')).astype(float)/255
cel=np.asarray(L).astype(float)/255
base=np.asarray(Image.open('art/faces/fuel_base_480.png').convert('RGB'))
def render(night,low,celon,ang):
    b=npv.night_face(base) if night else base.astype(float)
    norm=npv.C['printing_orange'] if night else np.array([255.,255,255])
    img=b*(1-pump[...,None])+pump[...,None]*(Y if low else norm)
    if celon: img=img*(1-cel[...,None])+cel[...,None]*Y
    g=npv.F['fuel']; n=npv.N['gauges']['fuel']
    if night:
        hm=npv.halo(img.shape,g['pivot_px'],g['hub_radius_mm']*g['px_per_mm']); img=img*(1-hm[...,None])+npv.C[npv.H['color']]*hm[...,None]
    im=Image.fromarray(np.clip(img,0,255).astype(np.uint8)).convert('RGBA')
    nd=npv.needle_img(f"art/needles/{n['needle_png']}",night); px,py=n['pivot_px']
    W=int(2*max(nd.size)+4); cv=Image.new('RGBA',(W,W)); cv.paste(nd,(int(W/2-px),int(W/2-py)))
    cv=cv.rotate(-ang,resample=Image.BICUBIC,center=(W/2,W/2)); cx_,cy_=g['pivot_px']; im.alpha_composite(cv,(int(cx_-W/2),int(cy_-W/2)))
    hub=Image.open(f"art/needles/{n['hub_png']}").convert('RGBA'); im.alpha_composite(hub,(int(cx_-hub.width/2),int(cy_-hub.height/2)))
    return im.convert('RGB')
cases=[('day, normal (lamp hidden)',False,False,False,-60),('day, check engine',False,False,True,-60),('night, check engine',True,False,True,-60),('day, low fuel + check engine',False,True,True,-108)]
out=Image.new('RGB',(4*490-10,480+34),(30,30,30)); d=ImageDraw.Draw(out)
for i,(t,nt,lo,ce,a) in enumerate(cases): out.paste(render(nt,lo,ce,a),(i*490,34)); d.text((i*490+6,10),t,fill=(220,220,220))
out.save('art/preview/fuel_cel_preview.png'); print('icon bbox',ix,iy,ix+w,iy+h)
