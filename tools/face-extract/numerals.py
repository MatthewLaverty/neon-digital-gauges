import numpy as np, sys
from PIL import Image
from scipy import ndimage as nd
from tape2 import run
def numerals(n,Y0,Y1):
    xs,T,B,h=run(n,Y0,Y1)
    a=np.asarray(Image.open(n+'.png').convert('L')).astype(float)
    H,W=a.shape
    m=np.zeros((H,W),bool)
    yy=np.arange(H)[:,None]
    inside=(yy>T[None,:]+8)&(yy<B[None,:]-8)
    m=(a<110)&inside
    lab,k=nd.label(m)
    out=[]
    for i,s in enumerate(nd.find_objects(lab)):
        h=s[0].stop-s[0].start; w=s[1].stop-s[1].start; area=(lab[s]==i+1).sum()
        if 22<=h<=60 and w>=12 and area>250: out.append(((s[1].start+s[1].stop)/2,(s[0].start+s[0].stop)/2,w,h,area))
    return sorted(out)
if __name__=='__main__':
    o=numerals(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]))
    for r in o: print([round(v) for v in r])
