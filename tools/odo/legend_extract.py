"""Extract the Toyota LCD legends 'ODO' and 'TRIP' (owner reference photos, 2026-10-16) as alpha masks.
Dark-on-amber LCD print -> darkness above local background, normalised, contrast-stretched, trimmed to ink bbox.
ODO: Toyota how-to video frame (legend ~35 px tall). TRIP: Corolla E120 trip-reset video frame (~18 px tall, softer;
it gets a stronger stretch so its stroke weight matches ODO)."""
import numpy as np
from PIL import Image, ImageFilter
A='art/glyphs/seg7/'
SRC={'ODO':(A+'ref_toyota_odo.jpg',(330,224,442,270),(0.30,0.75)),
     'TRIP':(A+'ref_toyota_trip.jpg',(774,389,836,416),(0.30,0.70))}
def extract(name,up=8):
    f,box,(lo,hi)=SRC[name]
    im=Image.open(f).convert('RGB').crop(box); W,H=im.size
    im=im.resize((W*up,H*up),Image.BICUBIC)
    a=np.asarray(im).astype(float); lum=a@[0.299,0.587,0.114]
    bg=np.asarray(Image.fromarray(lum.astype(np.uint8)).filter(ImageFilter.MaxFilter(up*6+1)).filter(ImageFilter.GaussianBlur(up*3))).astype(float)
    dk=np.clip(bg-lum,0,None); dk/=np.percentile(dk,99.7)
    m=np.clip((dk-lo)/(hi-lo),0,1)
    ys,xs=np.where(m>0.5); m=np.pad(m,up)[ys.min():ys.max()+2*up+1,xs.min():xs.max()+2*up+1]
    return m,(ys.max()-ys.min()+1)   # mask, cap height in upsampled px
if __name__=='__main__':
    for n in SRC:
        m,ch=extract(n); Image.fromarray((m*255).astype(np.uint8)).save(f'art/glyphs/seg7/ref_toyota_{n}_trace.png'); print(n,m.shape,ch)
