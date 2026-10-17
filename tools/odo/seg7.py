"""7-segment LCD readout in the style of the late-90s Dodge Dakota odometer (owner reference, 2026-10-16).
Odometer and trip share one field on the tach face, anchored where the F of the old 'FUEL DOOR' began (x=150, y 398-418
on the 480 px tach), digit height = that lettering's height. Odometer: 6 digits, no tenths. Trip: tenths (999.9), with
the decimal point in the inter-digit gap so both read in the same cells. Both are left-aligned so they start at the same point. Colour: the night printing orange pushed to full saturation, used day and night."""
import colorsys, json, numpy as np
from PIL import Image, ImageDraw
P=json.load(open('art/night_palette.json'))
h,s,v=colorsys.rgb_to_hsv(*[c/255 for c in P['printing_orange']])
ODO_RGB=[round(c*255) for c in colorsys.hsv_to_rgb(h,1.0,1.0)]
GEOM=dict(w=0.62,t=0.19,g=0.012,pitch=0.78,dp=0.16,tip=0.0)   # upright, no slant; bold segments like the Dakota       # in digit heights
FIELD=dict(xc=240,yc=408,h=24,cells=6)   # tach 480 px: centred directly under RPMX1000 (x 173-307, centre 240); 21 px FUEL DOOR height +15 %
SEG={'0':'abcdef','1':'bc','2':'abged','3':'abgcd','4':'fgbc','5':'afgcd','6':'afgedc','7':'abc','8':'abcdefg','9':'abcdfg',' ':'','-':'g'}
def seg_polys(w,t,g):
    d=GEOM['tip']*t/2          # tip truncation: flat bar ends with 45-degree chamfers, keeps the inter-segment gaps
    def hseg(yc):
        x0=t/2+g; x1=w-t/2-g
        return [(x0+d,yc-d),(x0+t/2,yc-t/2),(x1-t/2,yc-t/2),(x1-d,yc-d),(x1-d,yc+d),(x1-t/2,yc+t/2),(x0+t/2,yc+t/2),(x0+d,yc+d)]
    def vseg(xc,y0,y1):
        return [(xc-d,y0+d),(xc+d,y0+d),(xc+t/2,y0+t/2),(xc+t/2,y1-t/2),(xc+d,y1-d),(xc-d,y1-d),(xc-t/2,y1-t/2),(xc-t/2,y0+t/2)]
    m=0.5
    return {'a':hseg(t/2),'g':hseg(m),'d':hseg(1-t/2),
            'f':vseg(t/2,t/2+g,m-g),'b':vseg(w-t/2,t/2+g,m-g),'e':vseg(t/2,m+g,1-t/2-g),'c':vseg(w-t/2,m+g,1-t/2-g)}
def render_text(text,H,ss=8):
    """text like '169048' or '123.4'; returns alpha mask (H x width) using fixed cells, '.' lights the DP after the previous cell."""
    G=GEOM; cells=[]; dps=[]
    for ch in text:
        if ch=='.': dps.append(len(cells)-1)
        else: cells.append(ch)
    W=int(np.ceil(((len(cells)-1)*G['pitch']+G['w'])*H))+2
    im=Image.new('L',(W*ss,H*ss),0); d=ImageDraw.Draw(im); polys=seg_polys(G['w'],G['t'],G['g'])
    for i,ch in enumerate(cells):
        ox=i*G['pitch']
        for sg in SEG[ch]: d.polygon([((ox+x)*H*ss,y*H*ss) for x,y in polys[sg]],fill=255)
    for i in dps:
        cx=(i*G['pitch']+G['w']+(G['pitch']-G['w'])/2)*H; r=G['dp']/2*H
        d.rectangle([(cx-r)*ss,(H-2*r)*ss,(cx+r)*ss,H*ss],fill=255)
    return np.asarray(im.resize((W,H),Image.LANCZOS)).astype(float)/255
def field_text(kind,value):
    n=FIELD['cells']
    if kind=='odo': s=str(int(value))[-n:]               # centred under RPMX1000
    else:
        s=f'{value%1000:.1f}'                               # up to 999.9, centred the same way
    return s
# Legend ('ODO' / 'TRIP') in the Toyota LCD style (owner reference, 2026-10-16). Typeface: Roboto Regular, the closest
# installed match to the traced Toyota 'ODO' legend (tools/odo/legend_extract.py; width ratio 1.01, ink ratio 1.00, IoU 0.78).
# Cap height 0.47 x digit height and gap 0.24 x digit height, both measured off the Toyota ODO frame. Centred on the readout.
# Colour: the gauge-light (night printing) orange, day and night.
LEGEND=dict(font='/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Regular.ttf',cap_ratio=0.47,gap_ratio=0.24,
            rgb=list(P['printing_orange']),text={'odo':'ODO','trip':'TRIP'})
def render_legend(word,cap,ss=8):
    from PIL import ImageFont
    ft=ImageFont.truetype(LEGEND['font'],100*ss); top,bot=ft.getbbox('H')[1],ft.getbbox('H')[3]  # shared cap line + baseline
    l,_,r,_=ft.getbbox(word); im=Image.new('L',(r-l+4*ss,bot-top),0)
    ImageDraw.Draw(im).text((-l+2*ss,-top),word,font=ft,fill=255)
    W=max(1,round(im.width*cap/im.height)); m=np.asarray(im.resize((W,cap),Image.LANCZOS)).astype(float)/255
    xs=np.where(m.max(0)>0.02)[0]; return m[:,xs.min():xs.max()+1]
def _blend(img,m,x0,y0,rgb):
    h,w=m.shape; reg=img[y0:y0+h,x0:x0+w]; img[y0:y0+h,x0:x0+w]=reg*(1-m[...,None])+m[...,None]*np.array(rgb,float)
def draw_field(img,kind,value,rgb=ODO_RGB,legend=True):
    m=render_text(field_text(kind,value),FIELD['h']); h,w=m.shape
    x0=int(round(FIELD['xc']-w/2)); y0=int(round(FIELD['yc']-h/2)); _blend(img,m,x0,y0,rgb)
    if legend:
        cap=round(LEGEND['cap_ratio']*FIELD['h']); gap=round(LEGEND['gap_ratio']*FIELD['h'])
        lm=render_legend(LEGEND['text'][kind],cap); _blend(img,lm,int(round(FIELD['xc']-lm.shape[1]/2)),y0-gap-cap,LEGEND['rgb'])
    return img
if __name__=='__main__':
    for ch in '0123456789-':
        Image.fromarray((render_text(ch,64)*255).astype(np.uint8),'L').save(f'art/glyphs/seg7/{ch if ch!="-" else "minus"}_64.png')
    for k,wd in LEGEND['text'].items():
        c=round(LEGEND['cap_ratio']*FIELD['h']); Image.fromarray((render_legend(wd,c)*255).astype(np.uint8),'L').save(f'art/glyphs/seg7/legend_{wd}.png')
        Image.fromarray((render_legend(wd,64)*255).astype(np.uint8),'L').save(f'art/glyphs/seg7/legend_{wd}_64.png')
    json.dump(dict(GEOM=GEOM,FIELD=FIELD,LEGEND=LEGEND,color_rgb=ODO_RGB,segments=SEG,odo='up to 6 digits, no tenths, centred under RPMX1000',trip='up to 999.9, DP in the gap, centred under RPMX1000'),open('art/glyphs/seg7/seg7.json','w'),indent=1)
    print('ODO colour',ODO_RGB)
