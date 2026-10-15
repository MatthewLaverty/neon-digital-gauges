"""Screen-layout study (2026-10-14). Overlay frame mm: origin = speedo hole arc center, +y up."""
import json, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Polygon
from shapely.geometry import Polygon as SP, Point, box
g=json.load(open('hardware/overlay/overlay_mm.json')); S={k:np.array(v) for k,v in g['shapes'].items()}
f=json.load(open('art/faces/faces.json'))['gauges']
P={k:np.array(f[k]['pivot_mm']) for k in f}
union=np.vstack([S['temp'],S['fuel']]); ux0,uy0=union.min(0); ux1,uy1=union.max(0); uc=((ux0+ux1)/2,(uy0+uy1)/2)
def round_panel(c,od,tall,aa):  # circle of od + FPC tab region below (tall-od)
    return SP(Point(*c).buffer(od/2,256).union(box(c[0]-od*0.2,c[1]-od/2-(tall-od),c[0]+od*0.2,c[1]))), Point(*c).buffer(aa/2,256)
L={}
L['speedo 4.0" 720x720 (bare, 105.3x109.6)']=round_panel(P['speedo'],105.3,109.62,101.52)
L['tach 2.8" 480x480 (bare, ~73.0x76.5)']=round_panel(P['tach'],73.03,76.48,70.13)
o=box(uc[0]-60.35,uc[1]-37.9,uc[0]+60.35,uc[1]+37.9); a=box(uc[0]-54,uc[1]-32.4,uc[0]+54,uc[1]+32.4)
L['temp+fuel 5.0" 800x480 (bare, 120.7x75.8)']=(o,a)
alt={'tach 3.4" alt (bare, 94.9x96.95)':round_panel(P['tach'],94.9,96.95,87.6)}
wins={k:SP(S[k]) for k in S if k.startswith(('slot','oval','lamp'))}
holes={k:SP(S[k]) for k in ['temp','fuel','speedo','tach']}
rep=[]
allp={**L,**alt}
for n,(out,aa) in allp.items():
    for w,wp in wins.items():
        ar=out.intersection(wp).area
        if ar>0.5: rep.append(f'{n} outline overlaps {w} window: {ar:.0f} mm²')
names=list(L)
for i in range(len(names)):
    for j in range(i+1,len(names)):
        ar=L[names[i]][0].intersection(L[names[j]][0]).area
        if ar>0.5: rep.append(f'{names[i]} and {names[j]} outlines overlap {ar:.0f} mm² (only bezels; stagger depth)')
for n,(out,aa) in allp.items():
    if 'speedo' in n: h=holes['speedo']
    elif 'tach' in n: h=holes['tach']
    else: h=holes['temp'].union(holes['fuel'])
    un=h.difference(aa).area; rep.append(f'{n}: stock hole area not covered by active area {un:.0f} mm² of {h.area:.0f}')
    for k,hh in holes.items():
        if hh.intersection(aa).area>0 and hh is not h and not (k in ('temp','fuel') and 'fuel' in n):
            rep.append(f'{n}: active area reaches into {k} hole ({hh.intersection(aa).area:.0f} mm²)')
# FUEL DOOR / trip and odometer zones
tach_scale=round((70.13/2-1.0)/38.4,3)
fd=box(P['tach'][0]-15*tach_scale,P['tach'][1]-33.5*tach_scale,P['tach'][0]+19*tach_scale,P['tach'][1]-26.5*tach_scale)
odo=box(-16.8,-33.0,14.5,-26.4)
rep.append(f'tach art scale to fit 2.8" with 1 mm margin: {tach_scale}')
rep.append(f'odometer zone inside speedo active area: {L[names[0]][1].contains(odo)}; inside speedo hole: {holes["speedo"].contains(odo)}')
rep.append(f'trip zone (FUEL DOOR spot) inside tach active: {L[names[1]][1].contains(fd)}')
print('\n'.join(rep))
fig,ax=plt.subplots(figsize=(16,6.2),dpi=130)
ax.add_patch(Polygon(S['outer'],closed=True,fc='#202020',ec='#888',lw=1))
for k,v in S.items():
    if k=='outer': continue
    ax.add_patch(Polygon(v,closed=True,fc='#000' if k in holes else '#555',ec='#bbb' if k in holes else '#f0c040',lw=1))
cols=['#4fc3f7','#ef5350','#81c784']
for (n,(out,aa)),c in zip(L.items(),cols):
    x,y=out.exterior.xy; ax.plot(x,y,c=c,lw=1.6,label=n+' outline')
    x,y=aa.exterior.xy; ax.plot(x,y,c=c,lw=1,ls='--')
for n,(out,aa) in alt.items():
    x,y=out.exterior.xy; ax.plot(x,y,c='#ff9800',lw=1,ls=':',label=n)
for z,c,t in ((odo,'#ffffff','odometer'),(fd,'#ffffff','trip')):
    x,y=z.exterior.xy; ax.fill(x,y,c=c,alpha=0.35); ax.text(z.centroid.x,z.centroid.y,t,color='w',fontsize=7,ha='center',va='center')
for k,p in P.items(): ax.plot(*p,'+',c='w',ms=8)
ax.set_aspect('equal'); ax.set_xlim(-210,195); ax.set_ylim(-62,66); ax.legend(loc='lower left',fontsize=7,framealpha=0.8)
ax.set_title('Neon cluster screen layout, mm (solid = module outline, dashed = active area, yellow = indicator windows)',fontsize=10)
ax.grid(alpha=0.15); fig.tight_layout(); fig.savefig('docs/layout/screen_layout.png'); print('saved')
