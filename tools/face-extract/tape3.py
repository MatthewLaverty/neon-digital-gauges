import numpy as np, sys
from PIL import Image
from scipy import ndimage as nd
from tape2 import run
def profile(n,Y0,Y1,off_top=4,band=14):
    xs,T,B,h=run(n,Y0,Y1)
    a=np.asarray(Image.open(n+'.png').convert('L')).astype(float)
    p=np.zeros(a.shape[1])
    for x in range(a.shape[1]):
        t=int(T[x])+off_top; p[x]=a[t:t+band,x].mean()
    return p,T,B
def local_period(p,c,half=600,lo=200,hi=280):
    s=p[c-half:c+half]; s=s-nd.uniform_filter1d(s,60); s=s*np.hanning(len(s))
    F=np.abs(np.fft.rfft(s,len(s)*16)); fr=np.fft.rfftfreq(len(s)*16)
    # search fundamental of 1/16 inch harmonics: inch period P; 1/16 => P/16
    best=None
    for P in np.arange(lo,hi,0.1):
        f=16/P; i=int(round(f*len(s)*16)); v=F[i]
        if best is None or v>best[1]: best=(P,v)
    return best
if __name__=='__main__':
    n=sys.argv[1]; Y0=int(sys.argv[2]); Y1=int(sys.argv[3])
    p,T,B=profile(n,Y0,Y1)
    ok=np.nonzero(~np.isnan(T))[0]
    for c in range(700,4032-600,300):
        print(c, local_period(p,c))
