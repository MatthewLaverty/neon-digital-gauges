"""Frame trim template (owner 2026-10-18): the 5" temp/fuel board gets room by trimming the frame -- the flange (green)
AND the surround outside it at the board's top-left corner. Trim = board outline + CLEAR mm, minus the face opening
(already free). Two cases, because the 5" position depends on the speedo choice:
  A  v3 layout, Waveshare 3.4C 115 mm speedo: 5" shifted 7 mm left of hole-centred
  B  bare 3.4" round speedo panel (~95 x 97 mm): 5" hole-centred
Outputs docs/frame/frame_trim.png, frame_trim.svg, frame_trim.dxf (mm, origin = speedo arc centre, +y up, front view).
Flange inner edge from the photo is +/-1 mm: cut to the scribed board outline on the part, not to this drawing alone."""
import json,pickle,numpy as np,matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import box,Polygon
import ezdxf
CLEAR=1.0
g=json.load(open('hardware/overlay/overlay_mm.json')); FACE=Polygon(g['shapes']['outer']); IN=Polygon(g['shapes']['frame_flange_inner'])
S={k:np.array(v) for k,v in g['shapes'].items()}; u=np.vstack([S['temp'],S['fuel']]); uc=(u.min(0)+u.max(0))/2
cases={'A':7.0,'B':0.0}; out={}
fig,axs=plt.subplots(1,2,figsize=(16,5.2))
doc=ezdxf.new(); msp=doc.modelspace(); svg=[]
def add(geom,layer):
    for gg in (geom.geoms if hasattr(geom,'geoms') else [geom]):
        if gg.is_empty or gg.area<1: continue
        msp.add_lwpolyline([tuple(p) for p in gg.exterior.coords],close=True,dxfattribs={'layer':layer})
        svg.append((layer,list(gg.exterior.coords)))
add(FACE,'FLANGE_OUTER'); add(IN,'FLANGE_INNER')
for ax,(k,sh) in zip(axs,cases.items()):
    tf=box(uc[0]-sh-63.85,uc[1]-43.725,uc[0]-sh+63.85,uc[1]+43.725); env=tf.buffer(CLEAR,join_style=2)
    fl=env.intersection(FACE).difference(IN); sur=env.difference(FACE)
    add(tf,f'BOARD_{k}'); add(fl,f'TRIM_FLANGE_{k}'); add(sur,f'TRIM_SURROUND_{k}')
    def depth(geom,ref):
        from shapely.geometry import Point
        pts=[p for gg in (geom.geoms if hasattr(geom,'geoms') else [geom]) if not gg.is_empty for p in gg.exterior.coords]
        return round(max([ref.exterior.distance(Point(p)) for p in pts if not ref.contains(Point(p))],default=0),1)
    out[k]=dict(board_bounds=[round(v,1) for v in tf.bounds],flange_trim_mm2=round(fl.area),surround_trim_mm2=round(sur.area),
                surround_max_depth_past_outer_mm=depth(env,FACE),surround_x_range=[round(sur.bounds[0],1),round(sur.bounds[2],1)] if not sur.is_empty else None)
    band=FACE.difference(IN)
    for geom,c in ((band,'#b9e89a'),(fl,'#f2a900'),(sur,'#ff3030')):
        for gg in (geom.geoms if hasattr(geom,'geoms') else [geom]):
            if not gg.is_empty and gg.area>0.5:
                x,y=gg.exterior.xy; ax.fill(x,y,color=c,lw=0)
                for h in gg.interiors: x,y=h.xy; ax.fill(x,y,color='white')
    x,y=FACE.exterior.xy; ax.plot(x,y,'k-',lw=1); x,y=tf.exterior.xy; ax.plot(x,y,'-',color='#2a9d4a',lw=1.5)
    ax.set_xlim(-210,-30); ax.set_ylim(-60,65); ax.set_aspect('equal'); ax.grid(alpha=.3)
    ax.set_title(f"Case {k}: {'Waveshare 3.4C speedo, 5in 7 mm left' if k=='A' else 'bare round speedo, 5in hole-centred'}\n"
                 f"flange trim {out[k]['flange_trim_mm2']} mm², surround trim {out[k]['surround_trim_mm2']} mm² (max {out[k]['surround_max_depth_past_outer_mm']} mm past the outer edge)",fontsize=9)
axs[0].fill([],[],color='#b9e89a',label='flange (kept)'); axs[0].fill([],[],color='#f2a900',label='trim: flange'); axs[0].fill([],[],color='#ff3030',label='trim: surround (outside the flange)')
axs[0].plot([],[],'-',color='#2a9d4a',label='5in board outline'); axs[0].legend(loc='center',fontsize=8)
fig.suptitle(f'Frame trim for the 5in temp/fuel board (front view, mm; board + {CLEAR} mm clearance). Photo-derived edges +/-1 mm: scribe from the part.',fontsize=10)
plt.tight_layout(); plt.savefig('docs/frame/frame_trim.png',dpi=110,bbox_inches='tight'); doc.saveas('docs/frame/frame_trim.dxf')
col={'FLANGE_OUTER':'#000','FLANGE_INNER':'#2a9d4a'}
lines=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-210 -65 400 130" width="400mm" height="130mm"><g transform="scale(1,-1)" fill="none" stroke-width="0.3">']
for layer,pts in svg:
    c=col.get(layer,'#f2a900' if 'FLANGE' in layer else '#ff3030' if 'SURROUND' in layer else '#1f77b4')
    lines.append(f'<polygon id="{layer}" stroke="{c}" points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)+'"/>')
open('docs/frame/frame_trim.svg','w').write('\n'.join(lines+['</g></svg>']))
json.dump(out,open('docs/frame/frame_trim.json','w'),indent=1); print(json.dumps(out,indent=1))
