"""Screen layout v2 (2026-10-14): indicator lights removed; full-size 3.4in tach; temp+fuel shifted left 4.5 mm."""
import json, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from shapely.geometry import Polygon as SP, Point, box
g=json.load(open('hardware/overlay/overlay_mm.json')); S={k:np.array(v) for k,v in g['shapes'].items()}
f=json.load(open('art/faces/faces.json'))['gauges']; P={k:np.array(f[k]['pivot_mm']) for k in f}
DX=-4.5
outer=SP(S['outer']); wall=outer.buffer(-3)
u=np.vstack([S['temp'],S['fuel']]); uc=(u.min(0)+u.max(0))/2+[DX,0]
L={'speedo 4.0" round, bare (Ø105.3)':(Point(*P['speedo']).buffer(52.65,256),Point(*P['speedo']).buffer(50.76,256),'#4fc3f7'),
   'tach 3.4" round, bare (Ø94.9)':(Point(*P['tach']).buffer(47.45,256),Point(*P['tach']).buffer(43.8,256),'#ef5350'),
   f'temp+fuel 5" 800x480, bare, moved {abs(DX)} mm left':(box(uc[0]-60.35,uc[1]-37.9,uc[0]+60.35,uc[1]+37.9),box(uc[0]-54,uc[1]-32.4,uc[0]+54,uc[1]+32.4),'#81c784')}
WS={'Waveshare 4C board (126 sq)':box(P['speedo'][0]-63,P['speedo'][1]-63,P['speedo'][0]+63,P['speedo'][1]+63),
    'Waveshare 3.4C board (115 sq), tach moved 14 mm right':box(P['tach'][0]+14-57.5,P['tach'][1]-57.5,P['tach'][0]+14+57.5,P['tach'][1]+57.5)}
fig,ax=plt.subplots(figsize=(16,6.2),dpi=130)
ax.add_patch(Polygon(S['outer'],closed=True,fc='#202020',ec='#888'))
x,y=wall.exterior.xy; ax.plot(x,y,c='#888',lw=0.8,ls=':',label='outline minus 3 mm wall (assumed)')
for k in ['temp','fuel','speedo','tach']:
    v=S[k]+([DX,0] if k in ('temp','fuel') else [0,0]); ax.add_patch(Polygon(v,closed=True,fc='#000',ec='#bbb'))
for n,(o,a,c) in L.items():
    x,y=o.exterior.xy; ax.plot(x,y,c=c,lw=1.6,label=n); x,y=a.exterior.xy; ax.plot(x,y,c=c,lw=0.9,ls='--')
for n,b in WS.items():
    x,y=b.exterior.xy; ax.plot(x,y,c='#ff9800',lw=1,ls='-.',label=n+' (does not fit)')
ax.set_aspect('equal'); ax.set_xlim(-210,195); ax.set_ylim(-68,68); ax.grid(alpha=0.15); ax.legend(loc='lower left',fontsize=7,framealpha=0.85)
ax.set_title('Lights removed: bare 4.0" speedo + 3.4" tach + 5" temp/fuel inside the cluster outline (mm). Dashed = active area',fontsize=10)
fig.tight_layout(); fig.savefig('docs/layout/screen_layout_v2.png')
ks=list(L)
for n,(o,a,c) in L.items(): print(n,'outside outline',round(o.difference(outer).area),'mm²; outside 3mm wall',round(o.difference(wall).area),'mm²')
print('gaps: speedo-tach %.1f  speedo-5in %.1f'%(L[ks[0]][0].distance(L[ks[1]][0]),L[ks[0]][0].distance(L[ks[2]][0])))
holes=SP(S['temp']).union(SP(S['fuel'])); holes=__import__('shapely').affinity.translate(holes,DX,0)
print('5in active covers moved holes:',L[ks[2]][1].contains(holes)); print('tach active uncovered of stock hole',round(SP(S['tach']).difference(L[ks[1]][1]).area),'mm²')
for n,b in WS.items(): print(n,'outside outline',round(b.difference(outer).area),'mm²')
