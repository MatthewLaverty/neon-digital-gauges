import numpy as np, cv2, json
from PIL import Image
A='/home/user/workspace/neon-digital-gauges/art'
F=json.load(open(A+'/faces/faces.json'))['gauges']; N=json.load(open(A+'/needles/needles.json'))['gauges']
demo={'temp':200,'fuel':150,'speedo':60,'tach':-15}
tiles=[]
for k in ['temp','fuel','speedo','tach']:
    face=Image.open(f'{A}/faces/{k}_480.png').convert('RGBA')
    nd=Image.open(f'{A}/needles/'+N[k]['needle_png']); px,py=N[k]['pivot_px']
    W,H=nd.size; pad=max(W,H)*2
    canvas=Image.new('RGBA',(pad,pad),(0,0,0,0)); canvas.paste(nd,(int(pad/2-px),int(pad/2-py)))
    rot=canvas.rotate(demo[k]-90,resample=Image.BICUBIC,center=(pad/2,pad/2))
    fx,fy=F[k]['pivot_px']; face.alpha_composite(rot,(int(round(fx-pad/2)),int(round(fy-pad/2)))) if False else None
    layer=Image.new('RGBA',face.size,(0,0,0,0)); layer.paste(rot,(int(round(fx-pad/2)),int(round(fy-pad/2))),rot)
    face=Image.alpha_composite(face,layer)
    hub=Image.open(f'{A}/needles/'+N[k]['hub_png']); D=hub.size[0]
    layer=Image.new('RGBA',face.size,(0,0,0,0)); layer.paste(hub,(int(round(fx-D/2)),int(round(fy-D/2))),hub)
    face=Image.alpha_composite(face,layer).convert('RGB'); face.save(f'{A}/preview/{k}_480_with_needle.png'); tiles.append(face)
c=Image.new('RGB',(1940,480),(40,40,40))
for i,t in enumerate(tiles): c.paste(t,(i*487,0))
c.save(f'{A}/preview/all_with_needles.png')
