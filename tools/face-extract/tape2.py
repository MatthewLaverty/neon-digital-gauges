import numpy as np, sys
from PIL import Image
from scipy import ndimage as nd
def run(n,Y0,Y1,thr=0.7,dark=120):
    a=np.asarray(Image.open(n+'.png').convert('RGB')).astype(float)[Y0:Y1]
    R,G,B=a[...,0],a[...,1],a[...,2]
    yel=(R-B>70)&(R>130)
    yel=nd.binary_closing(yel,np.ones((15,41)))
    lab,k=nd.label(yel); sz=nd.sum(yel,lab,range(1,k+1)); yel=lab==(1+np.argmax(sz))
    T=np.full(a.shape[1],np.nan); Bt=T.copy()
    for x in range(a.shape[1]):
        ys=np.nonzero(yel[:,x])[0]
        if len(ys)>60: T[x],Bt[x]=ys.min(),ys.max()
    ok=~np.isnan(T); xs_=np.arange(len(T))
    T=np.interp(xs_,xs_[ok],T[ok]); Bt=np.interp(xs_,xs_[ok],Bt[ok])
    T=nd.median_filter(T,101); Bt=nd.median_filter(Bt,101)
    res=np.zeros(len(T))
    for x in range(len(T)):
        t,b=int(T[x])+10,int(Bt[x])-10
        if b>t and ok[max(0,x-200):x+200].any(): res[x]=(R[t:b,x]<dark).mean()
    m=res>thr; lab,k=nd.label(m)
    xs=[float(np.average(np.nonzero(lab==i)[0],weights=res[lab==i])) for i in range(1,k+1)]
    return xs,T+Y0,Bt+Y0,np.median(Bt-T)
if __name__=='__main__':
    import sys
    xs,T,B,h=run(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]))
    print('h',h,len(xs),[round(x,1) for x in xs]); print(np.round(np.diff(xs),1))
