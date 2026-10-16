"""Tach-face mock of the odometer / trip readout, day and night (and the boost tach)."""
import sys, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0,'tools/night'); sys.path.insert(0,'tools/odo'); sys.path.insert(0,'tools/alt-faces')
import night_preview as npv, seg7
def tach(night,kind,val,ang=-60):
    im=np.asarray(npv.compose('tach',ang,night).convert('RGB')).astype(float)
    return Image.fromarray(seg7.draw_field(im,kind,val).astype(np.uint8))
cases=[('day: ODO 123456',False,'odo',123456),('day: TRIP 287.4',False,'trip',287.4),('day: TRIP after reset 0.0',False,'trip',0.0),
       ('night: ODO 123456',True,'odo',123456),('night: TRIP 287.4',True,'trip',287.4),('night: TRIP 0.0',True,'trip',0.0)]
out=Image.new('RGB',(3*490-10,2*(480+30)),(30,30,30)); d=ImageDraw.Draw(out)
for i,(t,nt,k,v) in enumerate(cases):
    x=(i%3)*490; y=(i//3)*510; out.paste(tach(nt,k,v),(x,y+30)); d.text((x+6,y+10),t,fill=(220,220,220))
out.save('art/preview/odo_trip_preview.png')
z=tach(False,'odo',123456).crop((130,370,350,440)).resize((660,210),Image.LANCZOS); z.save('art/preview/odo_zoom.png'); print('ok')
