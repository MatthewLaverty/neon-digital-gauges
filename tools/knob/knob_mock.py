"""Mock of the CrowPanel 1.28 knob selector UI (240x240 round), owner concept 2026-10-17.
Rotate: horizontal carousel of downscaled gauge faces, temp -> fuel -> tach -> speedo (wraps).
Tap: the selected gauge slides vertically to its alternate face (and the main gauge changes).
Hold 2 s: the knob screen inverts for 0.5 s and stays on that gauge's default face; the action runs on the main gauge."""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageOps
for p in ('tools/night','tools/alt-faces','tools/odo'): sys.path.insert(0,p)
import night_preview as npv, tach_boost_mock as tb, speedo_data_face as sd
import ethanol_face as ef
S=240
def rnd(im):
    im=im.convert('RGB').resize((S,S),Image.LANCZOS); m=Image.new('L',(S*4,S*4),0); ImageDraw.Draw(m).ellipse((0,0,S*4-1,S*4-1),fill=255)
    out=Image.new('RGB',(S,S),(0,0,0)); out.paste(im,(0,0),m.resize((S,S),Image.LANCZOS)); return out
def faces(night=False):
    vals=dict(air=14.7,oil=52,speed=123,volts=14.1)
    eth=ef.render(67,night); eth=eth if isinstance(eth,Image.Image) else Image.fromarray(np.clip(eth,0,255).astype(np.uint8))
    return {'temp':(npv.compose('temp',-100,night),npv.compose('temp',-100,night,'art/faces/temp_oil_480.png')),
            'fuel':(npv.compose('fuel',-60,night),eth),
            'tach':(tb.compose(3000,0,False,night),tb.compose(5500,0.10,True,night)),
            'speedo':(npv.compose('speedo',-40,night),sd.render(vals,[i['key'] for i in sd.ITEMS],night))}
def frames(night=False):
    F={k:(rnd(a),rnd(b)) for k,(a,b) in faces(night).items()}; order=['temp','fuel','tach','speedo']
    def strip(i0,i1,t):     # horizontal scroll from gauge i0 to i1, fraction t
        a,b=F[order[i0]][0],F[order[i1]][0]; c=Image.new('RGB',(S,S)); x=int(-t*S); c.paste(a,(x,0)); c.paste(b,(x+S,0)); return c
    def vslide(k,t):
        a,b=F[k]; c=Image.new('RGB',(S,S)); y=int(-t*S); c.paste(a,(0,y)); c.paste(b,(0,y+S)); return c
    return [('temp',F['temp'][0]),('rotate: temp to fuel',strip(0,1,0.5)),('fuel',F['fuel'][0]),('tap: fuel to ethanol',vslide('fuel',0.5)),
            ('fuel, alt (ethanol)',F['fuel'][1]),('tach',F['tach'][0]),('hold on tach: 0.5 s invert',rnd(ImageOps.invert(F['tach'][0]))),('speedo',F['speedo'][0])]
if __name__=='__main__':
    rows=[frames(False),frames(True)]; G=S+12
    out=Image.new('RGB',(8*G-12,2*(S+30)),(30,30,30)); d=ImageDraw.Draw(out)
    for r,fr in enumerate(rows):
        for i,(t,im) in enumerate(fr):
            out.paste(im,(i*G,r*(S+30)+28)); d.text((i*G+4,r*(S+30)+8),('night: ' if r else '')+t,fill=(220,220,220))
    out.save('art/preview/knob_ui_preview.png'); print('ok')
