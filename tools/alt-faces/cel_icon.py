"""Check-engine lamp for the fuel gauge (owner 2026-10-18, placeholder art until the owner supplies the final symbol).
Symbol: ISO 2575 F.01 'Engine' (application of ISO 7000-0640), traced from ISO 2575:2010 p.28 at 1200 dpi
(art/icons/engine_iso7000-0640_src.png). Rev 2026-10-18b (owner): moved ABOVE the pump icon
(below it the needle swept over it near F) and scaled 120 % (59 px wide = 1.2 x pump width); 8 px gap as before. On the
ethanol face it sits 8 px above the ethanol ring (the ring top is 6 px higher than the pump top). Hidden unless the Haltech CEL flag is on (0x3E4 byte 7 bit 7); lit in the low-fuel yellow.
Outputs art/faces/cel_icon_A8.png (480x480 alpha layer), art/faces/cel_icon.json, art/preview/fuel_cel_preview.png."""
import sys, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0,'tools/night'); import night_preview as npv
I=json.load(open('art/faces/fuel_icon.json')); Y=np.array(I['low_fuel_color_rgb'],float)
x0,y0,x1,y1=I['pump_bbox_px']; gap=round(I['gap_px'])
from PIL import ImageFilter
src=Image.open('art/icons/engine_iso7000-0640_src.png').convert('L')
src=src.filter(ImageFilter.MaxFilter(25))   # stroke ~40 -> ~64 src px, about 3 px at 49 px wide (closer to the pump glyph weight)
w=round(1.2*(x1-x0)); h=round(w*src.height/src.width)
icon=src.resize((w*4,h*4),Image.LANCZOS).resize((w,h),Image.LANCZOS)
cx=(x0+x1)/2; ix=round(cx-w/2); iy=y0-gap-h
E=json.load(open('art/faces/fuel_ethanol.json')); ring_top=E['ring_center_px'][1]-E['ring_radius_px']; iy_e=ring_top-gap-h
L=Image.new('L',(480,480),0); L.paste(icon,(ix,iy)); L.save('art/faces/cel_icon_A8.png')
LE=Image.new('L',(480,480),0); LE.paste(icon,(ix,iy_e)); LE.save('art/faces/cel_icon_ethanol_A8.png')
# checks: inside the visible hole, and clear of the needle over its whole sweep
from shapely.geometry import Polygon, box as sbox, LineString
FJ=json.load(open('art/faces/faces.json'))['gauges']; g=FJ['fuel']; S=json.load(open('hardware/overlay/overlay_mm.json'))['shapes']
hole=Polygon([((x-g['image_center_mm'][0])*g['px_per_mm']+240,240-(y-g['image_center_mm'][1])*g['px_per_mm']) for x,y in S['fuel']])
import math
piv=g['pivot_px']; tipR=math.hypot(224.5-piv[0],49.5-piv[1])
def needle_clear(b):
    best=1e9
    for a in np.linspace(E['needle_angle_E_deg'],E['needle_angle_F_deg'],400):
        r=math.radians(a); seg=LineString([piv,(piv[0]+tipR*math.sin(r),piv[1]-tipR*math.cos(r))]); best=min(best,seg.distance(b))
    return best
chk={}
for nm,yy in (('fuel',iy),('ethanol',iy_e)):
    b=sbox(ix,yy,ix+w,yy+h); chk[nm]=dict(bbox_px=[ix,yy,ix+w,yy+h],inside_hole=bool(hole.contains(b)),hole_margin_px=round(hole.exterior.distance(b),1),needle_centerline_clearance_px=round(needle_clear(b),1))
print(chk)
json.dump(dict(bbox_px=[ix,iy,ix+w,iy+h],bbox_px_ethanol=[ix,iy_e,ix+w,iy_e+h],scale_vs_pump_width=1.2,position='above the pump (fuel face) / above the ethanol ring, 8 px gap',checks=chk,layer_ethanol='cel_icon_ethanol_A8.png',symbol='ISO 2575 F.01 Engine (ISO 7000-0640), placeholder until owner art',
  color_rgb=list(map(int,Y)),visible='only while Haltech 0x3E4 byte 7 bit 7 (Check Engine Light) = 1; hub relays it in 0x6A3 byte 2 bit 1',
  faces='fuel level face and ethanol face',layer='cel_icon_A8.png',
  note='rev b: above the pump, clear of the needle sweep'),open('art/faces/cel_icon.json','w'),indent=1)
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
cases=[('day, check engine, needle at F',False,False,True,E['needle_angle_F_deg']),('night, check engine',True,False,True,-60),('day, low fuel + check engine',False,True,True,-108)]
import importlib.util, io, contextlib
spec=importlib.util.spec_from_file_location('eth','tools/alt-faces/ethanol_face.py'); eth=importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(eth)
def render_eth(night):
    im=np.asarray(eth.render(85,night)).astype(float); ce=np.asarray(LE).astype(float)/255
    return Image.fromarray(np.clip(im*(1-ce[...,None])+ce[...,None]*Y,0,255).astype(np.uint8))
out=Image.new('RGB',(4*490-10,480+34),(30,30,30)); d=ImageDraw.Draw(out)
for i,(t,nt,lo,ce,a) in enumerate(cases): out.paste(render(nt,lo,ce,a),(i*490,34)); d.text((i*490+6,10),t,fill=(220,220,220))
out.paste(render_eth(False),(3*490,34)); d.text((3*490+6,10),'ethanol face E85, check engine',fill=(220,220,220))
out.save('art/preview/fuel_cel_preview.png'); print('icon bbox',ix,iy,ix+w,iy+h)
