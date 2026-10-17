"""Oil-temp alternate temp face, day and night. Night uses the same mapping as every other face (tools/night):
white print (C, H letters, oil-temp icon) -> printing orange; red H tick -> red ticks; blue C tick -> night blue;
needle -> night needle red; hub halo as on the other gauges."""
import sys
from PIL import Image, ImageDraw
sys.path.insert(0,'tools/night'); import night_preview as npv
FACE='art/faces/temp_oil_480.png'
cases=[('day: coolant (stock)',False,None),('day: oil temp',False,FACE),('night: coolant (stock)',True,None),('night: oil temp',True,FACE)]
out=Image.new('RGB',(4*490-10,480+34),(30,30,30)); d=ImageDraw.Draw(out)
for i,(t,nt,f) in enumerate(cases):
    out.paste(npv.compose('temp',-100,nt,f),(i*490,34)); d.text((i*490+6,10),t,fill=(220,220,220))
out.save('art/preview/temp_oil_preview.png'); npv.compose('temp',-100,True,FACE).save('art/preview/temp_oil_480_night.png'); print('ok')
