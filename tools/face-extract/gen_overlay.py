"""Generate the parametric replacement overlay: STL + SVG + DXF + OpenSCAD source.
Edit overlay_params.json (or the top of overlay.scad) and rerun."""
import json, os, sys, numpy as np
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
import trimesh
OUT='/home/user/workspace/neon-digital-gauges/hardware/overlay'
geo=json.load(open('overlay_mm.json')); faces=json.load(open('/home/user/workspace/neon-digital-gauges/art/faces/faces.json'))['gauges']
P=os.path.join(OUT,'overlay_params.json')
DEFAULT={
 "plate_thickness":2.0, "scale_x":1.0, "scale_y":1.0, "outer_grow":0.0,
 "include_lamp_holes":True, "include_slots":True, "include_mount_holes":True, "mount_hole_d":4.0,
 "windows":{
   "temp":  {"mode":"stock","grow":0.0,"offset":[0,0],"circle_d":62.0,"circle_center":faces['temp']['image_center_mm']},
   "fuel":  {"mode":"stock","grow":0.0,"offset":[0,0],"circle_d":62.0,"circle_center":faces['fuel']['image_center_mm']},
   "speedo":{"mode":"stock","grow":0.0,"offset":[0,0],"circle_d":104.0,"circle_center":faces['speedo']['pivot_mm']},
   "tach":  {"mode":"stock","grow":0.0,"offset":[0,0],"circle_d":82.0,"circle_center":faces['tach']['pivot_mm']}},
 "screens":[
   {"name":"speedo","shape":"circle","center":faces['speedo']['pivot_mm'],"size":[faces['speedo']['image_diameter_mm']],"clearance":0.4,"wall":1.6,"depth":3.0,"enabled":True},
   {"name":"tach","shape":"circle","center":faces['tach']['pivot_mm'],"size":[faces['tach']['image_diameter_mm']],"clearance":0.4,"wall":1.6,"depth":3.0,"enabled":True},
   {"name":"temp_fuel","shape":"rect","center":[-108.0,7.2],"size":[108.0,64.8],"clearance":0.4,"wall":1.6,"depth":3.0,"enabled":True}]
}
if not os.path.exists(P) or '--reset' in sys.argv: json.dump(DEFAULT,open(P,'w'),indent=1)
p=json.load(open(P))
S=geo['shapes']
def poly(k): return Polygon(S[k]).buffer(0)
def window(k):
    w=p['windows'][k]; st=poly(k)
    ci=Point(*w['circle_center']).buffer(w['circle_d']/2,resolution=128)
    g={'stock':st,'circle':ci,'intersect':st.intersection(ci),'union':st.union(ci)}[w['mode']]
    if w['grow']: g=g.buffer(w['grow'],join_style='round')
    return affinity.translate(g,*w['offset'])
outer=poly('outer')
if p['outer_grow']: outer=outer.buffer(p['outer_grow'])
cut=[window(k) for k in ['temp','fuel','speedo','tach']]
if p['include_slots']: cut+= [poly(k) for k in ['slot_tl','oval_tl','slot_tr','oval_tr']]
if p['include_lamp_holes']: cut+= [poly(k) for k in ['lamp_l1','lamp_l2','lamp_r1','lamp_r2']]
if p['include_mount_holes']: cut+= [Point(*c).buffer(p['mount_hole_d']/2,resolution=32) for c in geo['mount_holes']['centers']]
plate=outer.difference(unary_union(cut))
def sc(g): return affinity.scale(g,p['scale_x'],p['scale_y'],origin=(0,0))
plate=sc(plate)
# rear locating frames (z<0)
frames=[]
for s in p['screens']:
    if not s['enabled']: continue
    c=s['center']
    if s['shape']=='circle':
        r=s['size'][0]/2+s['clearance']; inner=Point(*c).buffer(r,resolution=180); outerr=Point(*c).buffer(r+s['wall'],resolution=180)
    else:
        w,h=s['size']; inner=box(c[0]-w/2-s['clearance'],c[1]-h/2-s['clearance'],c[0]+w/2+s['clearance'],c[1]+h/2+s['clearance'])
        outerr=inner.buffer(s['wall'],join_style='mitre')
    ring=sc(outerr.difference(inner)).intersection(sc(outer))
    frames.append((ring,s['depth']))
def extrude(g,h,z0):
    ms=[]
    geoms=[g] if g.geom_type=='Polygon' else list(g.geoms)
    for gg in geoms:
        if gg.area<1e-3: continue
        m=trimesh.creation.extrude_polygon(gg,h); m.apply_translation([0,0,z0]); ms.append(m)
    return ms
parts=extrude(plate,p['plate_thickness'],0)
for ring,d in frames: parts+=extrude(ring,d+0.01,-d)
mesh=trimesh.boolean.union(parts,engine='manifold') if len(parts)>1 else parts[0]
mesh.export(os.path.join(OUT,'neon_overlay.stl'))
print('watertight',mesh.is_watertight,'bounds',mesh.bounds.round(2).tolist(),'faces',len(mesh.faces))
# 2D outputs
def rings(g):
    gs=[g] if g.geom_type=='Polygon' else list(g.geoms)
    for gg in gs:
        yield np.array(gg.exterior.coords)
        for i in gg.interiors: yield np.array(i.coords)
minx,miny,maxx,maxy=plate.bounds
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{maxx-minx+4:.2f}mm" height="{maxy-miny+4:.2f}mm" viewBox="{minx-2:.2f} {-maxy-2:.2f} {maxx-minx+4:.2f} {maxy-miny+4:.2f}">',
     '<g fill="none" stroke="black" stroke-width="0.2">']
for r in rings(plate): svg.append('<polyline points="'+' '.join(f'{x:.3f},{-y:.3f}' for x,y in r)+'"/>')
for ring,_ in frames:
    for r in rings(ring): svg.append('<polyline stroke="blue" points="'+' '.join(f'{x:.3f},{-y:.3f}' for x,y in r)+'"/>')
svg.append('</g></svg>'); open(os.path.join(OUT,'neon_overlay_outline.svg'),'w').write('\n'.join(svg))
try:
    import ezdxf
    doc=ezdxf.new(); msp=doc.modelspace(); doc.layers.add('PLATE'); doc.layers.add('SCREEN_FRAMES',color=5)
    for r in rings(plate): msp.add_lwpolyline([tuple(v) for v in r],close=True,dxfattribs={'layer':'PLATE'})
    for ring,_ in frames:
        for r in rings(ring): msp.add_lwpolyline([tuple(v) for v in r],close=True,dxfattribs={'layer':'SCREEN_FRAMES'})
    doc.saveas(os.path.join(OUT,'neon_overlay_outline.dxf')); print('dxf ok')
except ImportError: print('no ezdxf')
