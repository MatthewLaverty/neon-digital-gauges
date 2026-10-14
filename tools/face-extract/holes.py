import numpy as np, cv2, json
from PIL import Image
a=np.asarray(Image.open('IMG_7568.png').convert('RGB'))
g=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY)
gm=cv2.medianBlur(g,21); gm=cv2.medianBlur(gm,15)
cv2.imwrite('gm.png',gm)
S=4032/1238
seeds={'temp':(245,533),'fuel':(400,540),'speedo':(630,530),'tach':(940,560),
'slot_tl':(470,428),'oval_tl':(483,463),'slot_tr':(800,438),'oval_tr':(807,485),
'lamp_l1':(135,552),'lamp_l2':(145,595),'lamp_r1':(1093,585),'lamp_r2':(1083,628)}
res={}
vis=a.copy()
for k,(sx,sy) in seeds.items():
    X,Y=int(sx*S),int(sy*S)
    R=900 if k in('speedo','tach') else (700 if k in ('temp','fuel') else 350)
    x0,y0=max(0,X-R),max(0,Y-R); p=gm[y0:Y+R,x0:X+R]
    t,_=cv2.threshold(p,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    holem=(p<t).astype(np.uint8)
    n,lab=cv2.connectedComponents(holem)
    L=lab[Y-y0,X-x0]
    if L==0: print(k,'seed on overlay?'); continue
    hm=(lab==L).astype(np.uint8)
    hm=cv2.morphologyEx(hm,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))
    cs,_=cv2.findContours(hm,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    c=max(cs,key=cv2.contourArea)+np.array([x0,y0])
    touches = (c[:,0,0].min()<=x0+2) or (c[:,0,1].min()<=y0+2) or (c[:,0,0].max()>=x0+p.shape[1]-3) or (c[:,0,1].max()>=y0+p.shape[0]-3)
    x,y,w,h=cv2.boundingRect(c)
    print(k,'otsu',t,'bbox',x,y,w,h,'area',int(cv2.contourArea(c)),'LEAK' if touches else '')
    res[k]=c[:,0,:].tolist()
    cv2.drawContours(vis,[c],-1,(0,255,0),5)
json.dump(res,open('holes_px.json','w'))
Image.fromarray(vis).crop((150,1100,3950,2450)).resize((1900,675)).save('holes_vis.jpg')
