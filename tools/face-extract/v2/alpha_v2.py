import numpy as np, cv2
def graphics(rgb,t0=40,t1=100,k=41):
    V=rgb.max(2).astype(np.float32)
    bg=cv2.GaussianBlur(cv2.morphologyEx(V,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(k,k))),(0,0),8)
    d=V-bg; return np.clip((d-t0)/(t1-t0),0,1), d
