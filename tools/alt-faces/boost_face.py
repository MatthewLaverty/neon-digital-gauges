"""Boost (MPa) sub-dial for an alternate tach face, from the owner's Lamco TURBO gauge photo (IMG_7566).
- Ticks are redrawn synthetically from measured geometry: 26 ticks, 12 deg apart (0.01 MPa), -0.10 MPa at 151.1 deg
  (clockwise from 12 o'clock) to +0.15 at 91.1 deg; majors every 0.05 MPa.
- Labels (.05 .1 .15 -.05 -.1 MPa; TURBO removed per owner 2026-10-16) are lifted from the photo (top-hat filtered), white on black.
- The 0 hidden by the needle is rebuilt from the 0 of the upper '.05' and placed where the photo shows its top arc.
- No LAMCO logo, screws, hub or bezel ring; nothing outside the tick ring."""
import json, math, numpy as np
from PIL import Image
from scipy import ndimage
SRC='art/boost/ref_IMG_7566.jpg'; CROP=(1000,950,2500,2350)
a=np.asarray(Image.open(SRC).convert('RGB').crop(CROP)).astype(float); g=a.min(2)
bg=ndimage.median_filter(g[::4,::4],size=25); bg=np.kron(bg,np.ones((4,4)))[:g.shape[0],:g.shape[1]]; top=g-bg
C=np.array([722.8,717.5]); RO=561.0          # fitted dial centre and tick outer radius (photo px)
GEOM=dict(minor_in=485/RO, major_in=452/RO, minor_w=16/RO, major_w=32/RO, a0=151.1, step=12.0, n=26, needle_len=513/RO)
LABELS={'.05':(450,330,640,430),'.1':(860,330,960,430),'.15':(1020,680,1165,775),
        'MPa':(1010,805,1160,880),'-.05':(410,1000,630,1095),'-.1':(860,1000,985,1095)}
ZERO_SRC=(496,338,563,423); ZERO_CENTER=(333,703)
def label_alpha(box):
    x0,y0,x1,y1=box; t=top[y0:y1,x0:x1]; m=t>30
    m=ndimage.binary_opening(m,iterations=1); lab,n=ndimage.label(m)
    keep=np.zeros_like(m)
    for i in range(1,n+1):
        if (lab==i).sum()>120: keep|=lab==i
    keep=ndimage.binary_fill_holes(ndimage.binary_closing(keep,iterations=2)) if False else ndimage.binary_closing(keep,iterations=2)
    reg=ndimage.binary_dilation(keep,iterations=2)
    core=np.percentile(t[keep],90) if keep.any() else 1
    tn=ndimage.gaussian_filter(t,1.2)/core                     # normalise each label to full white
    al=np.clip((tn-0.40)/0.22,0,1)*reg
    return al
def build(Rpx, ss=4):
    """Return an alpha mask (2R+pad square) of the boost dial with tick outer radius Rpx; centre at the middle."""
    S=int(math.ceil(Rpx*2+8)); W=S*ss; k=Rpx*ss/RO; cx=cy=W/2
    yy,xx=np.mgrid[:W,:W]; dx=xx-cx; dy=yy-cy; r=np.hypot(dx,dy)/k
    ang=(np.degrees(np.arctan2(dx,-dy)))%360
    out=np.zeros((W,W))
    for p in range(GEOM['n']):
        major=p%5==0; ta=(GEOM['a0']+GEOM['step']*p)%360
        d=((ang-ta+180)%360)-180; perp=np.abs(np.radians(d))*r
        rin=GEOM['major_in' if major else 'minor_in']*RO; w=GEOM['major_w' if major else 'minor_w']*RO
        out=np.maximum(out,((r>=rin)&(r<=RO)&(perp<=w/2)&(np.abs(d)<30)).astype(float))
    def paste(al,cxp,cyp):   # al in photo px, centre at photo coords (cxp,cyp)
        im=Image.fromarray((al*255).astype(np.uint8)); w=max(1,round(im.width*k)); h=max(1,round(im.height*k))
        im=np.asarray(im.resize((w,h),Image.LANCZOS)).astype(float)/255
        x0=int(round(cx+(cxp-C[0])*k-w/2)); y0=int(round(cy+(cyp-C[1])*k-h/2))
        out[y0:y0+h,x0:x0+w]=np.maximum(out[y0:y0+h,x0:x0+w],im)
    for nm,b in LABELS.items(): paste(label_alpha(b),(b[0]+b[2])/2,(b[1]+b[3])/2)
    paste(label_alpha(ZERO_SRC),*ZERO_CENTER)
    m=Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8)).resize((S,S),Image.LANCZOS)
    return np.asarray(m).astype(float)/255
def angle_for(mpa): return (GEOM['a0']+(mpa+0.10)/0.01*GEOM['step'])
if __name__=='__main__':
    m=build(240); Image.fromarray((m*255).astype(np.uint8)).save('art/boost/boost_dial_A8_R240.png'); print('ok', m.shape)
    json.dump(dict(GEOM, units='MPa gauge', range=[-0.10,0.15], source=SRC, note='angles clockwise from 12 o\'clock; radii as fraction of tick outer radius'),open('art/boost/boost_dial.json','w'),indent=1)
