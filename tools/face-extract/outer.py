import numpy as np, cv2, json, time
from PIL import Image
a=np.asarray(Image.open('IMG_7568.png').convert('RGB'))
f=2; sm=cv2.resize(a,(a.shape[1]//f,a.shape[0]//f),interpolation=cv2.INTER_AREA)
bgr=cv2.cvtColor(sm,cv2.COLOR_RGB2BGR)
H,W=sm.shape[:2]
mask=np.full((H,W),cv2.GC_PR_BGD,np.uint8)
g=cv2.medianBlur(cv2.cvtColor(sm,cv2.COLOR_RGB2GRAY),11)
ai=sm.astype(int)
yel=((ai[...,0]-ai[...,2])>60)&(ai[...,0]>120)
# rough FG: bright-ish in central band
rough=(g>130)&~yel
rough[:1150//f]=False; rough[2460//f:]=False
mask[rough]=cv2.GC_PR_FGD
mask[:1000//f]=cv2.GC_BGD; mask[2520//f:]=cv2.GC_BGD; mask[yel]=cv2.GC_BGD
mask[:, :120//f]=cv2.GC_BGD; mask[:,3950//f:]=cv2.GC_BGD
holes=json.load(open('holes_px.json'))
for k,c in holes.items():
    c=(np.array(c)//f).astype(np.int32); cv2.fillPoly(mask,[c],cv2.GC_BGD)
# definite FG: thin bands known to be overlay (webs between holes): erode hull band
for (x,y) in [(400,640),(560,520),(780,600),(1000,430),(150,500),(1150,560),(300,440),(800,700),(650,420),(540,680),(470,700)]:
    S=4032/1238; X,Y=int(x*S/f),int(y*S/f); cv2.circle(mask,(X,Y),6,cv2.GC_FGD,-1)
S=4032/1238
poly=np.array([(0,300),(330,300),(330,368),(200,383),(100,405),(48,445),(42,700),(0,700)],float)*S/f
cv2.fillPoly(mask,[poly.astype(np.int32)],cv2.GC_BGD)
for (x,y) in [(90,500),(85,620),(150,450),(120,680)]:
    cv2.circle(mask,(int(x*S/f),int(y*S/f)),6,cv2.GC_FGD,-1)
bgd=np.zeros((1,65),np.float64); fgd=np.zeros((1,65),np.float64)
t=time.time(); cv2.grabCut(bgr,mask,None,bgd,fgd,6,cv2.GC_INIT_WITH_MASK); print('gc',time.time()-t)
fg=((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD)).astype(np.uint8)
fg=cv2.morphologyEx(fg,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
n,lab,st,_=cv2.connectedComponentsWithStats(fg); i=1+np.argmax(st[1:,4]); fg=(lab==i).astype(np.uint8)
fg=cv2.morphologyEx(fg,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))
fgf=cv2.resize(fg,(a.shape[1],a.shape[0]),interpolation=cv2.INTER_LINEAR)
cs,_=cv2.findContours(fgf,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); c=max(cs,key=cv2.contourArea)
print('outer bbox',cv2.boundingRect(c))
json.dump(c[:,0,:].tolist(),open('outer_px.json','w'))
vis=a.copy(); cv2.drawContours(vis,[c],-1,(255,0,255),6)
for k,h in holes.items(): cv2.polylines(vis,[np.array(h,np.int32)],True,(0,255,0),5)
Image.fromarray(vis).crop((100,1050,4032,2550)).resize((1966,750)).save('outer_vis.jpg')
