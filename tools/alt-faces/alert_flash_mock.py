"""Mock of the error flash (owner 2026-10-18; rev b: needles and ticks outlined). During the 'on' half of each 3 Hz
flash the gauge background turns ALERT_FLASH red, day or night, EXCEPT a black keep-out outline OUTLINE_PX wide around
every printed element (ticks, numerals, legends, readouts) and around the needle and hub, so red ticks, red needles
and night-orange print stay readable against the red.
Firmware equivalent: each gauge keeps a pre-rendered 'flash' copy of its static face (red background with the black
keep-out already baked in) and swaps it in on the red phase; the needle sprite is drawn with a black outline
(OUTLINE_PX) on that phase. Approximation here: foreground = any pixel brighter than the dark background (or darker
than the white day data-face background), dilated by OUTLINE_PX."""
import json, numpy as np, scipy.ndimage as nd
from PIL import Image, ImageDraw
RED=np.array([255,0,0],float); OUTLINE_PX=3
def window(size=480):
    a=np.asarray(Image.open('art/preview/speedo_data_800_day.png').convert('L').resize((size,size))); return nd.binary_fill_holes(a>200)
def disk(r):
    y,x=np.mgrid[-r:r+1,-r:r+1]; return x*x+y*y<=r*r
def flash(path,day_white_bg=False,size=480,win=False,hub=None,outline=True):
    a=np.asarray(Image.open(path).convert('RGB').resize((size,size),Image.LANCZOS)).astype(float)
    if day_white_bg: bg=np.clip((a.min(2)-190)/60,0,1); fg=a.min(2)<150
    else: bg=np.clip(1-a.max(2)/55,0,1); fg=a.max(2)>=55
    if hub is not None:
        yy,xx=np.mgrid[:size,:size]; hm=np.hypot(xx-hub[0],yy-hub[1])<=hub[2]; fg|=hm; bg[hm]=0
    if outline: bg=bg*~nd.binary_dilation(fg,disk(OUTLINE_PX))
    if win: bg=bg*window(size)
    return Image.fromarray(np.clip(a*(1-bg[...,None])+RED*bg[...,None],0,255).astype(np.uint8))
g=json.load(open('art/faces/faces.json'))['gauges']['tach']; HUB=(g['pivot_px'][0],g['pivot_px'][1],g['hub_radius_mm']*g['px_per_mm']+1)
P='art/preview/'
cases=[('tach day, RED phase, no outline (rev a)',flash(P+'tach_480_with_needle.png',hub=HUB,outline=False)),
       ('tach day, RED phase, outlined',flash(P+'tach_480_with_needle.png',hub=HUB)),
       ('tach night, RED phase, outlined',flash(P+'tach_480_night.png',hub=HUB)),
       ('data face day, RED phase (black on red, no outline needed)',flash(P+'speedo_data_800_day.png',True,outline=False)),
       ('data face night, RED phase, outlined',flash(P+'speedo_data_800_night.png',win=True))]
out=Image.new('RGB',(5*490-10,514),(30,30,30)); d=ImageDraw.Draw(out)
for i,(t,im) in enumerate(cases): out.paste(im.convert('RGB').resize((480,480)),(i*490,34)); d.text((i*490+6,10),t,fill=(220,220,220))
out.save(P+'alert_flash_preview.png'); print('ok')
