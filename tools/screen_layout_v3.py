"""Layout v3 (2026-10-14): off-the-shelf boards; housing may be trimmed (frames may exceed the outline), visible areas must stay on the face.
Speedo: Waveshare ESP32-P4-WIFI6-Touch-LCD-3.4C (115x115, AA Ø87.6), art 0.86. Tach: 2.8in round ESP32-S3 (board assumed Ø95.86), AA Ø70.13, art 0.887.
Temp+fuel: Waveshare ESP32-S3-Touch-LCD-5 (127.7x87.45, AA 108x64.8 assumed centered), full-size art, shifted left for clearance."""
import json, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from shapely.geometry import Polygon as SP, Point, box
from shapely import affinity
g=json.load(open('hardware/overlay/overlay_mm.json')); S={k:np.array(v) for k,v in g['shapes'].items()}
f=json.load(open('art/faces/faces.json'))['gauges']; P={k:np.array(f[k]['pivot_mm']) for k in f}
outer=SP(S['outer']); face=outer.buffer(-3)
R=6.0  # speedo+tach moved right (mm) to centre the group
P0={k:v.copy() for k,v in P.items()}; P['speedo']=P['speedo']+[R,0]; P['tach']=P['tach']+[R,0]
def sq(c,w,h): return box(c[0]-w/2,c[1]-h/2,c[0]+w/2,c[1]+h/2)
sp_board=sq(P['speedo'],115,115); sp_aa=Point(*P['speedo']).buffer(43.8,256)
ta_board=Point(*P['tach']).buffer(95.86/2,256); ta_aa=Point(*P['tach']).buffer(70.13/2,256)
u=np.vstack([S['temp'],S['fuel']]); uc=(u.min(0)+u.max(0))/2
for sh in np.arange(0,20,0.25):
    tf=sq(uc-[sh,0],127.7,87.45)
    if tf.distance(sp_board)>=1.0: break
tf_aa=sq(uc-[sh,0],108,64.8)
sp_hole=affinity.translate(affinity.scale(SP(S['speedo']),0.86,0.86,origin=tuple(P0['speedo'])),R,0)
ta_hole=affinity.translate(affinity.scale(SP(S['tach']),0.887,0.887,origin=tuple(P0['tach'])),R,0)
tf_holes=[affinity.translate(SP(S[k]),-sh,0) for k in ('temp','fuel')]
print(f'temp/fuel shift left: {sh} mm')
print('gaps: speedo-tach board %.1f, speedo-5in board %.1f'%(sp_board.distance(ta_board),sp_board.distance(tf)))
for n,b in (('speedo board',sp_board),('tach board',ta_board),('5in board',tf)):
    bb=b.bounds; print(f'{n}: past outline {b.difference(outer).area:.0f} mm²; bounds x {bb[0]:.1f}..{bb[2]:.1f} y {bb[1]:.1f}..{bb[3]:.1f}')
for n,h in (('speedo hole (0.86)',sp_hole),('tach hole (0.887)',ta_hole),('temp hole',tf_holes[0]),('fuel hole',tf_holes[1])):
    print(f'{n}: inside face (3 mm in from outline) {face.contains(h)}; bounds {np.round(h.bounds,1)}')
print('5in active covers moved holes:',tf_aa.contains(tf_holes[0].union(tf_holes[1])),' speedo AA covers scaled hole:',round(sp_hole.difference(sp_aa).area,1),'mm² uncovered')
fig,ax=plt.subplots(figsize=(16,6.6),dpi=130)
ax.add_patch(Polygon(S['outer'],closed=True,fc='#202020',ec='#888'))
for h in [sp_hole,ta_hole,*tf_holes]:
    x,y=h.exterior.xy; ax.fill(x,y,c='#000'); ax.plot(x,y,c='#bbb',lw=0.8)
for k in ['temp','fuel','speedo','tach']:
    v=S[k]; ax.plot(*np.vstack([v,v[:1]]).T,c='#666',lw=0.6,ls=':')
for (o,a,c,n) in ((sp_board,sp_aa,'#4fc3f7',f'speedo (+{R:g} mm): Waveshare ESP32-P4 3.4C, 115 sq, Ø87.6 visible (86%)'),
                  (ta_board,ta_aa,'#ef5350',f'tach (+{R:g} mm): 2.8in round ESP32-S3, board ~Ø96, Ø70.1 visible (89%)'),
                  (tf,tf_aa,'#81c784',f'temp+fuel: Waveshare ESP32-S3 5in, 127.7x87.45, full size, moved {sh} mm left')):
    x,y=o.exterior.xy; ax.plot(x,y,c=c,lw=1.6,label=n); x,y=a.exterior.xy; ax.plot(x,y,c=c,lw=0.9,ls='--')
ax.set_aspect('equal'); ax.set_xlim(-215,195); ax.set_ylim(-68,68); ax.grid(alpha=0.15); ax.legend(loc='lower left',fontsize=7,framealpha=0.85)
ax.set_title('Off-the-shelf layout (mm). Solid = board, dashed = visible area, grey dotted = stock holes, white = new holes',fontsize=10)
fig.tight_layout(); fig.savefig('docs/layout/screen_layout_v3.png')
