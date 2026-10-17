"""Owner spec 2026-10-16: remove 'FUEL DOOR' + arrow from the tach (that space becomes the trip/odometer area);
move the arrow to the fuel face beside the pump icon, scaled to 3/4 of the pump icon height, with the same physical gap
it had after 'DOOR' on the tach. Pump icon + arrow become a separate A8 layer so firmware can turn them yellow below a
low-fuel threshold (TBD). Not applied to the ethanol alternate face."""
import json, numpy as np
from PIL import Image
from shapely.geometry import Polygon, box
FJ=json.load(open('art/faces/faces.json'))['gauges']
tach=np.asarray(Image.open('art/faces/source/tach_480_with_fuel_door.png').convert('RGB')).astype(float)
fuel=np.asarray(Image.open('art/faces/source/fuel_480_stock.png').convert('RGB')).astype(float)
ARROW_TACH=(322,398,343,418); DOOR_END_X=316; FUEL_DOOR_TEXT=(145,394,348,422)
PUMP=(289,112,338,162)
# 1) tach without FUEL DOOR
t2=tach.copy(); x0,y0,x1,y1=FUEL_DOOR_TEXT; t2[y0:y1,x0:x1]=0
Image.fromarray(t2.astype(np.uint8)).save('art/faces/tach_480.png')
# 2) arrow scaled to 3/4 of the pump height, gap = DOOR->arrow gap in mm
x0,y0,x1,y1=ARROW_TACH; arrow=tach[y0-1:y1+1,x0-1:x1+1].max(2)/255.0
gap_mm=(ARROW_TACH[0]-DOOR_END_X)/FJ['tach']['px_per_mm']; gap_px=gap_mm*FJ['fuel']['px_per_mm']
ph=PUMP[3]-PUMP[1]; H=round(0.75*ph); W=round(arrow.shape[1]*H/arrow.shape[0])
a=np.asarray(Image.fromarray((arrow*255).astype(np.uint8)).resize((W,H),Image.LANCZOS)).astype(float)/255
ax0=int(round(PUMP[2]+gap_px)); ay0=int(round((PUMP[1]+PUMP[3])/2-H/2))
layer=np.zeros((480,480)); px0,py0,px1,py1=PUMP
layer[py0:py1,px0:px1]=fuel[py0:py1,px0:px1].max(2)/255.0
layer[ay0:ay0+H,ax0:ax0+W]=np.maximum(layer[ay0:ay0+H,ax0:ax0+W],a)
base=fuel.copy(); base[py0:py1,px0:px1]=0                      # base face without the pump (it lives in the layer)
Image.fromarray(base.astype(np.uint8)).save('art/faces/fuel_base_480.png')
Image.fromarray((layer*255).astype(np.uint8),'L').save('art/faces/fuel_icon_A8.png')
day=np.maximum(base,layer[...,None]*255); Image.fromarray(day.astype(np.uint8)).save('art/faces/fuel_480.png')
g=FJ['fuel']; S=json.load(open('hardware/overlay/overlay_mm.json'))['shapes']
hole=Polygon([((x-g['image_center_mm'][0])*g['px_per_mm']+240,240-(y-g['image_center_mm'][1])*g['px_per_mm']) for x,y in S['fuel']])
ab=box(ax0,ay0,ax0+W,ay0+H)
info=dict(pump_bbox_px=PUMP,arrow_bbox_px=[ax0,ay0,ax0+W,ay0+H],arrow_height_ratio_to_pump=0.75,gap_mm=round(gap_mm,2),gap_px=round(gap_px,1),
          layer='fuel_icon_A8.png',base='fuel_base_480.png',low_fuel_color_rgb=[255,200,0],low_fuel_threshold=dict(gal=1.6,litres=6.06,can_0x3E2_raw_0p1L=61,rule='on when fuel remaining < 1.6 gal (owner 2026-10-16), from Haltech 0x3E2 fuel level (0.1 L)',proposed_filter='PROPOSED: on after 10 s continuously below; off above 1.8 gal (slosh hysteresis), tune in the car'),
          arrow_inside_hole=bool(hole.contains(ab)),arrow_margin_px=round(hole.exterior.distance(ab),1))
json.dump(info,open('art/faces/fuel_icon.json','w'),indent=1); print(info)
