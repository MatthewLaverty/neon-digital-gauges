"""Speedo alternate face: data screen (owner spec 2026-10-17).

Spec (owner): four Haltech values, Air / Oil / Speed / Volts. The top value is double height and gets 40 % of the height;
the other three split the remaining 60 %. A 4 px separator under the top value spans the centre 3/4 of the width.
Titles: regular weight, right-justified at 25 % of the width. Values: bold, centred in the remaining 75 %. Day: black on
white. Night: orange on black with a 4 px orange ring around the visible perimeter. Holding the speedo key (3) rotates the
order, scrolling up (the top value goes to the bottom, the next one moves up).

Geometry: the speedo is the Waveshare ESP32-P4 3.4C, 800x800 round (active Ø87.6 mm, 9.13 px/mm). The overlay hole
(stock hole x 0.86) is cut flat at the bottom, so the visible window is the panel circle above y = YB. All percentages
are measured on that window: width 800 px, height 0..YB.

Fitting (my choices, flagged in PLAN): in a circle, the top and bottom bands are too narrow at their outer edges for
titles right-justified at the 25 % line. So 'double height' applies to the values (titles are one size), and each band's
text block (title and value share a baseline) is placed as close to the band's centre as the circle allows. Sizes are the
largest that keep every title (with colon) and the widest value strings at least MARGIN px inside the window, in every
row position, since the rotation puts every value in every row."""
import json, numpy as np, sys
from PIL import Image, ImageDraw, ImageFont
P=json.load(open('art/night_palette.json'))
RF='/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/'
FONT_T, FONT_V = RF+'Roboto-Regular.ttf', RF+'Roboto-Bold.ttf'
W, YB, MARGIN, PAD, SEP, RING = 800, 660, 14, 10, 4, 4
TOP_FRAC, TITLE_X, VALUE_XC = 0.40, 0.25*W, (0.25*W+W)/2
TITLE_RATIO = 0.55          # title cap height / lower-row value cap height (labels read as labels)
ITEMS = [  # name, title, Haltech source, display conversion, format, widest string for fitting
  dict(key='air',  title='Air:',   can='0x368 bytes 0-1 Wideband Sensor 1, lambda = x/1000', show='AFR = lambda x 14.7 (gasoline scale)', fmt='{:.1f}', widest='00.0'),
  dict(key='oil',  title='Oil:',   can='0x361 bytes 2-3 Oil Pressure, kPa = x/10 - 101.3', show='psi = kPa x 0.145038, floor 0', fmt='{:.0f}', widest='000'),
  dict(key='speed',title='Speed:', can='0x370 bytes 0-1 Vehicle Speed, km/h = x/10', show='mph = km/h x 0.621371', fmt='{:.0f}', widest='000'),
  dict(key='volts',title='Volts:', can='0x372 bytes 0-1 Battery Voltage, V = x/10', show='V', fmt='{:.1f}', widest='00.0')]
def bands():
    t=round(TOP_FRAC*YB); r=(YB-t)/3; return [(0,t)]+[(t+i*r,t+(i+1)*r) for i in range(3)]
def xl(y): y=np.asarray(y,float); return 400-np.sqrt(np.maximum(0,400.0**2-(y-400)**2))
def xr(y): return W-xl(y)
_fc={}
def font(f,cap):
    k=(f,cap)
    if k not in _fc:
        sz=200; ft=ImageFont.truetype(f,sz); c=ft.getbbox('H'); n=max(4,round(sz*cap/(c[3]-c[1])))
        _fc[k]=ImageFont.truetype(f,n)
    return _fc[k]
def width(f,cap,s): b=font(f,cap).getbbox(s); return b[2]-b[0]
def row_ok(base,cv,ct,band):
    a,b=band; tv=base-cv; tt=base-ct
    if tv<a+PAD or base>b-PAD or base>YB-MARGIN: return False
    for it in ITEMS:
        w=width(FONT_V,cv,it['widest'])
        if VALUE_XC+w/2>min(xr([tv,base]))-MARGIN or VALUE_XC-w/2<max(xl([tv,base]))+MARGIN: return False
        wt=width(FONT_T,ct,it['title'])
        if TITLE_X-wt<max(xl([tt,base]))+MARGIN: return False
    return True
def place(cv,ct,band):
    a,b=band; ideal=(a+b)/2+cv/2; cands=sorted(np.arange(a,b+1),key=lambda y:abs(y-ideal))
    for y in cands:
        if row_ok(y,cv,ct,band): return int(y)
    return None
def fit():
    B=bands(); best=None
    for cs in range(30,140):
        cv=[2*cs,cs,cs,cs]; ct=round(TITLE_RATIO*cs); bl=[place(cv[i],ct,B[i]) for i in range(4)]
        if None in bl: break
        best=dict(value_cap=cv,title_cap=ct,baselines=bl)
    return best
L=None
def layout():
    global L
    if L is None: L=fit()
    return L
def window_mask(ss=4):
    im=Image.new('L',(W*ss,W*ss),0); d=ImageDraw.Draw(im); d.ellipse((0,0,W*ss-1,W*ss-1),fill=255)
    d.rectangle((0,YB*ss,W*ss,W*ss),fill=0); return im.resize((W,W),Image.LANCZOS)
def render(values,order,night=False):
    """values: dict key->number; order: list of the 4 keys top to bottom."""
    lay=layout(); fg=tuple(P['printing_orange']) if night else (0,0,0); bg=(0,0,0) if night else (255,255,255)
    ss=2; im=Image.new('RGB',(W*ss,W*ss),bg); d=ImageDraw.Draw(im); B=bands()
    t=B[0][1]; d.rectangle((W*ss/8,(t-SEP/2)*ss,W*ss*7/8-1,(t+SEP/2)*ss-1),fill=fg)
    it={i['key']:i for i in ITEMS}
    for r,k in enumerate(order):
        cv=lay['value_cap'][r]; ct=lay['title_cap']; base=lay['baselines'][r]
        ft=font(FONT_T,ct*ss); d.text((TITLE_X*ss,base*ss),it[k]['title'],font=ft,fill=fg,anchor='rs')
        fv=font(FONT_V,cv*ss); d.text((VALUE_XC*ss,base*ss),it[k]['fmt'].format(values[k]),font=fv,fill=fg,anchor='ms')
    if night:
        m=Image.new('L',(W*ss,W*ss),0); dm=ImageDraw.Draw(m); dm.ellipse((0,0,W*ss-1,W*ss-1),fill=255)
        dm.ellipse((RING*ss,RING*ss,(W-RING)*ss-1,(W-RING)*ss-1),fill=0); dm.rectangle((0,(YB-RING)*ss,W*ss,W*ss),fill=255)
        dm.rectangle((0,YB*ss,W*ss,W*ss),fill=0)
        # flat bottom: ring follows the cut, so remove the inner part of the band only inside the circle
        im.paste(fg,(0,0),m)
    im=im.resize((W,W),Image.LANCZOS)
    out=Image.new('RGB',(W,W),(0,0,0)); out.paste(im,(0,0),window_mask()); return out
def rotate_up(order): return order[1:]+order[:1]
if __name__=='__main__':
    lay=layout(); print(json.dumps(lay))
    json.dump(dict(spec=__doc__.split('\n\n')[1], window=dict(width_px=W,visible_bottom_y_px=YB,shape='800 px circle cut flat at y=YB by the overlay'),
        bands_px=bands(),separator=dict(thickness_px=SEP,x_px=[W/8,W*7/8]),title_right_x_px=TITLE_X,value_centre_x_px=VALUE_XC,
        fonts=dict(title='Roboto Regular',value='Roboto Bold'),layout=lay,night_ring_px=RING,
        colours=dict(day=dict(fg=[0,0,0],bg=[255,255,255]),night=dict(fg=P['printing_orange'],bg=[0,0,0])),
        items=ITEMS,default_order=[i['key'] for i in ITEMS],
        controls='key 3: tap = stock speedo / data face; hold 2 s on the data face = rotate up one step (top goes to the bottom); order saved in hub NVS'),
        open('art/faces/speedo_data.json','w'),indent=1)
    vals=dict(air=14.7,oil=52,speed=123,volts=14.1); order=[i['key'] for i in ITEMS]
    states=[order]; 
    for _ in range(3): states.append(rotate_up(states[-1]))
    S=400; out=Image.new('RGB',(4*(S+10)-10,2*(S+30)),(30,30,30)); d=ImageDraw.Draw(out)
    for row,nt in enumerate((False,True)):
        for i,o in enumerate(states):
            out.paste(render(vals,o,nt).resize((S,S),Image.LANCZOS),(i*(S+10),row*(S+30)+30))
            d.text((i*(S+10)+6,row*(S+30)+8),('night' if nt else 'day')+(' (default)' if i==0 else f' after {i} hold'+('s' if i>1 else '')),fill=(220,220,220))
    out.save('art/preview/speedo_data_preview.png')
    render(vals,order).save('art/preview/speedo_data_800_day.png'); render(vals,order,True).save('art/preview/speedo_data_800_night.png'); print('ok')
