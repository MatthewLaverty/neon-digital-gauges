"""Mock of the error flash (owner 2026-10-18): the gauge background turns red during the 'on' half of each 3 Hz
flash, day or night. Approximation for review: dark background pixels (tach, night data face) or white background
pixels (day data face) are replaced with ALERT_FLASH red; printing, needles and values are left as they are."""
import numpy as np
from PIL import Image, ImageDraw
RED=np.array([255,0,0],float)
import scipy.ndimage as nd
def window(size=480):
    a=np.asarray(Image.open('art/preview/speedo_data_800_day.png').convert('L').resize((size,size))); return nd.binary_fill_holes(a>200)
def flash(path,day_white_bg=False,size=480,win=False):
    a=np.asarray(Image.open(path).convert('RGB').resize((size,size),Image.LANCZOS)).astype(float)
    b=np.clip((a.min(2)-190)/60,0,1) if day_white_bg else np.clip(1-a.max(2)/55,0,1)
    if win: b=b*window(size)
    return Image.fromarray(np.clip(a*(1-b[...,None])+RED*b[...,None],0,255).astype(np.uint8))
P='art/preview/'
cases=[('tach day, off phase',Image.open(P+'tach_480_with_needle.png')),('tach day, RED phase',flash(P+'tach_480_with_needle.png')),
       ('tach night, RED phase',flash(P+'tach_480_night.png')),('data face day, RED phase',flash(P+'speedo_data_800_day.png',True)),
       ('data face night, RED phase',flash(P+'speedo_data_800_night.png',win=True))]
out=Image.new('RGB',(5*490-10,514),(30,30,30)); d=ImageDraw.Draw(out)
for i,(t,im) in enumerate(cases): out.paste(im.convert('RGB').resize((480,480)),(i*490,34)); d.text((i*490+6,10),t,fill=(220,220,220))
out.save(P+'alert_flash_preview.png'); print('ok')
