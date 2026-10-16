"""Ethanol-content alternate for the fuel gauge (owner spec 2026-10-14):
E -> 0, F -> 1, 1/2 stays at mid travel; the pump icon is replaced by a circled 'E' readout (EN 16942 style)
showing the integer ethanol % (E67); at 0 % it shows just 'E'. Needle travel is linear in ethanol fraction, E tick to F tick.
Glyphs come from the cluster's own typeface: E from the fuel face, digits from the tach face, 9 = 6 rotated 180 deg."""
import json, math, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import Polygon, Point
FJ=json.load(open('art/faces/faces.json'))['gauges']; NJ=json.load(open('art/needles/needles.json'))
def load(k):
    p='art/faces/source/fuel_480_stock.png' if k=='fuel' else f'art/faces/{k}_480.png'   # stock fuel art: no door arrow on the ethanol face
    return np.asarray(Image.open(p).convert('RGB')).astype(float)
fuel=load('fuel'); tach=load('tach')
def glyph(img,box):  # alpha mask (0..1) from brightness, colour-independent
    x0,y0,x1,y1=box; return img[y0:y1,x0:x1].max(2)/255.0
G={'E':glyph(fuel,(182,331,214,369)),'0':glyph(tach,(75,297,104,330)),'1':glyph(tach,(63,217,79,250)),
   '2':glyph(tach,(88,141,116,174)),'3':glyph(tach,(143,85,169,119)),'4':glyph(tach,(222,61,251,95)),
   '5':glyph(tach,(312,85,338,119)),'6':glyph(tach,(366,139,395,173)),'7':glyph(tach,(391,220,419,253)),
   '8':glyph(tach,(374,298,404,333))}
G['9']=np.rot90(G['6'],2)
for k,v in G.items(): Image.fromarray((v*255).astype(np.uint8),'L').save(f'art/glyphs/{k}.png')
def scaled(a,h):
    im=Image.fromarray((a*255).astype(np.uint8),'L'); w=max(1,round(im.width*h/im.height))
    return np.asarray(im.resize((w,h),Image.LANCZOS)).astype(float)/255
def stamp(dst,a,x,y):  # max-blend alpha mask, top-left at x,y
    h,w=a.shape; dst[y:y+h,x:x+w]=np.maximum(dst[y:y+h,x:x+w],a)
def text_mask(s,h,gap):
    gl=[scaled(G[c],h) for c in s]; W=sum(g.shape[1] for g in gl)+gap*(len(gl)-1)
    m=np.zeros((h,W)); x=0
    for g in gl: stamp(m,g,x,0); x+=g.shape[1]+gap
    return m
# ---- static layer: fuel face minus F, E, pump; plus 0, 1 and the ring
base=fuel.max(2)/255.0; red=(fuel[...,0]-fuel[...,2])>60
static=base.copy(); static[red]=0
for (x0,y0,x1,y1) in ((234,78,265,116),(182,331,214,369),(289,112,338,162)): static[y0-2:y1+2,x0-2:x1+2]=0
LH=38                                   # letter height of the stock E/F
one=scaled(G['1'],LH); zero=scaled(G['0'],LH)
stamp(static,one,int(249.5-one.shape[1]/2),78); stamp(static,zero,int(198-zero.shape[1]/2),331)
RING_C=(313,137); RING_R=31; RING_W=3.2
yy,xx=np.mgrid[:480,:480]; d=np.hypot(xx-RING_C[0],yy-RING_C[1])
ring=np.clip(RING_W/2+0.5-np.abs(d-RING_R+RING_W/2),0,1)
static=np.maximum(static,ring)
redlayer=np.where(red,fuel.max(2)/255.0,0)
# hole check: ring must sit inside the visible hole
g=FJ['fuel']; S=json.load(open('hardware/overlay/overlay_mm.json'))['shapes']
hole=Polygon([((x-g['image_center_mm'][0])*g['px_per_mm']+240,240-(y-g['image_center_mm'][1])*g['px_per_mm']) for x,y in S['fuel']])
print('ring inside hole, margin px: %.1f'%(hole.exterior.distance(Point(RING_C))-RING_R), hole.contains(Point(RING_C).buffer(RING_R)))
Image.fromarray((static*255).astype(np.uint8),'L').save('art/faces/fuel_ethanol_static_A8.png')
def readout(pct):
    s='E' if pct<=0 else f'E{int(pct)}'
    inner=2*(RING_R-RING_W)-8
    h=20; m=text_mask(s,h,2)
    while m.shape[1]>inner: h-=1; m=text_mask(s,h,2)
    return m
# ---- needle mapping: linear E tick -> F tick
piv=g['pivot_px']
def ang(px,py): return math.degrees(math.atan2(px-piv[0],-(py-piv[1])))
A_E=ang(117,385); A_F=ang(224.5,49.5); A_H=ang(109,198)
print(f'E tick {A_E:.1f} deg, F tick {A_F:.1f} deg, mid {((A_E+A_F)/2):.1f}, 1/2 tick {A_H:.1f}')
def angle_for(frac): return A_E+(A_F-A_E)*max(0,min(1,frac))
json.dump({'static_layer':'fuel_ethanol_static_A8.png','ring_center_px':RING_C,'ring_radius_px':RING_R,'readout':'E + int(pct); E alone at 0 %; text fit inside ring',
           'needle_angle_E_deg':round(A_E,2),'needle_angle_F_deg':round(A_F,2),'mapping':'linear ethanol fraction 0..1','glyphs':'art/glyphs/'},open('art/faces/fuel_ethanol.json','w'),indent=1)
# ---- previews
def render(pct,night):
    P=json.load(open('art/night_palette.json'))
    wc=np.array(P['printing_orange'] if night else [255,255,255],float); rc=np.array(P['red_ticks'] if night else [232,77,61],float)
    m=static.copy(); t=readout(pct); h,w=t.shape; stamp(m,t,int(RING_C[0]-w/2),int(RING_C[1]-h/2))
    img=m[...,None]*wc; img=img*(1-redlayer[...,None])+redlayer[...,None]*rc
    if night:
        H=P['halo']; r=g['hub_radius_mm']*g['px_per_mm']; dd=np.hypot(xx-piv[0],yy-piv[1])/r; wd=(H['outer_hub_radii']-1)/2.2
        hm=np.where(dd<1,1,np.exp(-((dd-1)/wd)**2))*H['peak_opacity']; hm[dd>H['outer_hub_radii']*1.3]=0
        img=img*(1-hm[...,None])+np.array(P['printing_orange'])*hm[...,None]
    im=Image.fromarray(np.clip(img,0,255).astype(np.uint8)).convert('RGBA')
    n=NJ['gauges']['fuel']; nd=Image.open(f"art/needles/{n['needle_png']}").convert('RGBA')
    if night:
        a=np.asarray(nd).astype(float); a[...,:3]=np.clip(a[...,:3].max(2)/232,0,1)[...,None]*np.array(P['needles']); nd=Image.fromarray(a.astype(np.uint8),'RGBA')
    px,py=n['pivot_px']; W=int(2*max(nd.size)+4); cv=Image.new('RGBA',(W,W)); cv.paste(nd,(int(W/2-px),int(W/2-py)))
    cv=cv.rotate(-angle_for(pct/100),resample=Image.BICUBIC,center=(W/2,W/2)); im.alpha_composite(cv,(int(piv[0]-W/2),int(piv[1]-W/2)))
    hub=Image.open(f"art/needles/{n['hub_png']}").convert('RGBA'); im.alpha_composite(hub,(int(piv[0]-hub.size[0]/2),int(piv[1]-hub.size[1]/2)))
    return im.convert('RGB')
if __name__=='__main__':
    cases=[(0,False),(67,False),(100,False),(0,True),(67,True),(100,True)]
    out=Image.new('RGB',(3*490-10,2*490+30),(30,30,30)); dr=ImageDraw.Draw(out)
    for i,(p,nt) in enumerate(cases):
        out.paste(render(p,nt),((i%3)*490,30+(i//3)*490))
    dr.text((8,8),'Ethanol mode on the fuel gauge: 0 %, 67 %, 100 % (day top, night bottom). Needle linear E->F; readout E / E67 / E100',fill=(220,220,220))
    out.save('art/preview/fuel_ethanol_preview.png'); print('ok')
