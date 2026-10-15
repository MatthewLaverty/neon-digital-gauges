"""Oil-temperature alternate for the temp gauge: the coolant icon (ISO 7000-0246) is replaced by
ISO 2575 F.05 'Engine oil temperature' (ISO 7000-2426), extracted from the ISO 2575:2010 symbol table and sized to the stock icon.
Scale (C/H ticks, red hot tick, blue cold tick) is unchanged; only the firmware's temperature-to-angle calibration differs."""
import json, subprocess, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import importlib.util, sys
src='/home/user/workspace/iso/hi-32.png'   # pdftoppm -f 32 -l 32 -r 600 ISO-2575.pdf (page with Annex F)
im=Image.open(src).convert('L'); s=600/110
c=np.asarray(im.crop([int(v*s) for v in (200,815,312,895)])).astype(float); ink=(255-c)/255; m=ink>0.5
lab,n=ndimage.label(m,structure=np.ones((3,3))); sizes=ndimage.sum(m,lab,range(1,n+1))
keep=np.isin(lab,[i+1 for i,v in enumerate(sizes) if v>1000])          # symbol parts incl. oil drop; drops cell corner marks
ys,xs=np.where(keep); y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
sym=ink[y0:y1,x0:x1]*ndimage.binary_dilation(keep[y0:y1,x0:x1],iterations=3)
# embolden to the stock icon stroke weight (stock coolant icon ~6 px at 46 px tall): grow the strokes by ~4 px at 600 dpi
PAD=12; mm=np.pad(sym>0.5,PAD); sym=np.clip(4.5-ndimage.distance_transform_edt(~mm)+0.5,0,1)
Image.fromarray((sym*255).astype(np.uint8),'L').save('art/glyphs/iso7000-2426_oil_temp_hires.png')
face=np.asarray(Image.open('art/faces/temp_480.png').convert('RGB')).astype(float)
out=face.copy(); out[115:166,278:336]=0                                 # remove coolant icon (incl. its wave pieces)
H=54; W=round(sym.shape[1]*H/sym.shape[0])
icon=np.asarray(Image.fromarray((sym*255).astype(np.uint8),'L').resize((W,H),Image.LANCZOS)).astype(float)/255
cx,cy=318,144; xa,ya=int(cx-W/2),int(cy-H/2)
reg=out[ya:ya+H,xa:xa+W]; out[ya:ya+H,xa:xa+W]=np.maximum(reg,icon[...,None]*255)
Image.fromarray(np.clip(out,0,255).astype(np.uint8)).save('art/faces/temp_oil_480.png')
Image.fromarray((icon*255).astype(np.uint8),'L').save('art/glyphs/oil_temp_icon_46px.png')
# hole check
FJ=json.load(open('art/faces/faces.json'))['gauges']; g=FJ['temp']; S=json.load(open('hardware/overlay/overlay_mm.json'))['shapes']
from shapely.geometry import Polygon, box
hole=Polygon([((x-g['image_center_mm'][0])*g['px_per_mm']+240,240-(y-g['image_center_mm'][1])*g['px_per_mm']) for x,y in S['temp']])
b=box(xa,ya,xa+W,ya+H); print(f'icon {W}x{H} at x {xa}-{xa+W} y {ya}-{ya+H}; inside hole {hole.contains(b)}, margin {hole.exterior.distance(b):.1f}px')
