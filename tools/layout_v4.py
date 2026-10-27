"""Layout v4 + new overlay v4 (owner 2026-10-26): speedo Waveshare ESP32-P4-WIFI6-Touch-LCD-4C (126 x 126 mm, display area
101.52 mm), tach Waveshare ESP32-S3-LCD-2.8C (board taken as O95.86, visible O70.13), temp+fuel Waveshare 5" (127.7 x 87.45,
active area 108 x 64.8 assumed centred). The stock overlay is not reused: the new one has only three openings, sized to
the screens. Temp+fuel share ONE rounded rectangle (owner). No lamp/telltale windows (owner removed the physical lamps).

Coordinates: mm, origin = stock speedo arc centre, +y up, front view (hardware/overlay/overlay_mm.json). The outline is
the stock face outline (= mounting-frame flange outer edge), confirmed by owner measurement 2026-10-26 (+0.55 % / +0.2 %).
Outputs:
  docs/layout/screen_layout_v4.png, docs/layout/layout_v4.json
  hardware/overlay_v4/neon_overlay_v4.stl / .svg / .dxf
  docs/frame/frame_trim_v4.png / .svg / .dxf / .json   (mounting-frame cuts for the boards, + 1 mm clearance)
"""
import json, os, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
import trimesh, ezdxf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda *p: os.path.join(ROOT, *p)
g = json.load(open(J('hardware/overlay/overlay_mm.json'))); S = {k: np.array(v) for k, v in g['shapes'].items()}
F = json.load(open(J('art/faces/faces.json')))['gauges']; P0 = {k: np.array(F[k]['pivot_mm'], float) for k in F}
FACE = Polygon(S['outer']).buffer(0); IN = Polygon(S['frame_flange_inner']).buffer(0); INSET = FACE.buffer(-3)

# ---------------- parameters ----------------
GROUP_SHIFT = 6.0          # speedo + tach move right (as layout v3)
BOARD_GAP = 1.0            # minimum board-to-board gap
HOLE_MARGIN = 0.75         # opening edge inside each screen's visible edge (assembly tolerance)
STOCK_HOLE_OFFSET = 1.55   # true stock hole edges are this far outside the traced ones (scale_check.json)
TF_CORNER_R = 6.0          # temp+fuel rounded rectangle corner radius
PLATE_T = 3.0              # owner spec: 3 mm at the flange
FRAME_WALL, FRAME_DEPTH, FRAME_CLEAR = 1.6, 3.0, 0.4   # rear locating lips around each board
TRIM_CLEAR = 1.0
SPEEDO = dict(w=126.0, vis_r=101.52 / 2)
TACH = dict(board_r=95.86 / 2, vis_r=70.13 / 2)
TF = dict(w=127.7, h=87.45, aa_w=108.0, aa_h=64.8)
# stock proportions (tick tips / true hole radius) -> recommended art scales
STOCK_TIPS = {'speedo': 49.6, 'tach': 38.4}
STOCK_HOLE_R = {'speedo': 50.55 + 1.70, 'tach': 39.31 + 1.41}
# --------------------------------------------

def sq(c, w, h): return box(c[0] - w / 2, c[1] - h / 2, c[0] + w / 2, c[1] + h / 2)

sp_c = P0['speedo'] + [GROUP_SHIFT, 0]
sp_board = sq(sp_c, SPEEDO['w'], SPEEDO['w'])
spread = next(s for s in np.arange(0, 20, 0.25)
              if sp_board.distance(Point(*(P0['tach'] + [GROUP_SHIFT + s, 0])).buffer(TACH['board_r'], 256)) >= BOARD_GAP)
ta_c = P0['tach'] + [GROUP_SHIFT + spread, 0]
ta_board = Point(*ta_c).buffer(TACH['board_r'], 256)
u = np.vstack([S['temp'], S['fuel']]); uc = (u.min(0) + u.max(0)) / 2
tf_shift = next(s for s in np.arange(0, 40, 0.25) if sq(uc - [s, 0], TF['w'], TF['h']).distance(sp_board) >= BOARD_GAP)
tf_c = uc - [tf_shift, 0]
tf_board = sq(tf_c, TF['w'], TF['h']); tf_aa = sq(tf_c, TF['aa_w'], TF['aa_h'])

# ---------------- openings ----------------
sp_hole = Point(*sp_c).buffer(SPEEDO['vis_r'] - HOLE_MARGIN, 256)
ta_hole = Point(*ta_c).buffer(TACH['vis_r'] - HOLE_MARGIN, 256)
stock_tf = unary_union([Polygon(S['temp']), Polygon(S['fuel'])]).buffer(STOCK_HOLE_OFFSET)
b = stock_tf.bounds
tf_rect = box(b[0] - tf_shift, b[1], b[2] - tf_shift, b[3]).intersection(tf_aa.buffer(-HOLE_MARGIN, join_style=2))
bx = tf_rect.bounds
tf_hole = box(bx[0] + TF_CORNER_R, bx[1] + TF_CORNER_R, bx[2] - TF_CORNER_R, bx[3] - TF_CORNER_R).buffer(TF_CORNER_R, 64)
holes = {'speedo': sp_hole, 'tach': ta_hole, 'temp_fuel': tf_hole}
mounts = [Point(*c).buffer(2.0, 32) for c in g['mount_holes']['centers']]
plate = FACE.difference(unary_union(list(holes.values()) + mounts))

# ---------------- checks ----------------
def past(board):                 # how far a board reaches beyond the face outline (mm) and where
    d = board.difference(FACE)
    if d.is_empty: return 0.0, 0.0, 0.0
    top = max(0.0, board.bounds[3] - max(y for x, y in FACE.exterior.coords if board.bounds[0] <= x <= board.bounds[2]))
    pts = [p for gg in (d.geoms if hasattr(d, 'geoms') else [d]) for p in gg.exterior.coords]
    far = max(FACE.exterior.distance(Point(p)) for p in pts)
    return round(d.area), round(far, 1), round(top, 1)
rep = dict(
    speedo=dict(board='Waveshare ESP32-P4-WIFI6-Touch-LCD-4C 126 sq', center=[round(v, 2) for v in sp_c], moved_mm=[GROUP_SHIFT, 0],
                hole_r=round(SPEEDO['vis_r'] - HOLE_MARGIN, 2), screen_vis_r=SPEEDO['vis_r']),
    tach=dict(board='Waveshare ESP32-S3-LCD-2.8C (O95.86 assumed)', center=[round(v, 2) for v in ta_c], moved_mm=[round(GROUP_SHIFT + spread, 2), 0],
              hole_r=round(TACH['vis_r'] - HOLE_MARGIN, 2), screen_vis_r=TACH['vis_r']),
    temp_fuel=dict(board='Waveshare 5in 127.7 x 87.45', center=[round(v, 2) for v in tf_c], moved_mm=[-tf_shift, 0],
                   hole_rect=[round(v, 1) for v in tf_hole.bounds], hole_size=[round(tf_hole.bounds[2] - tf_hole.bounds[0], 1), round(tf_hole.bounds[3] - tf_hole.bounds[1], 1)],
                   corner_r=TF_CORNER_R, aa=[round(v, 1) for v in tf_aa.bounds]),
    gaps=dict(speedo_tach=round(sp_board.distance(ta_board), 2), speedo_5in=round(sp_board.distance(tf_board), 2)),
    openings_inside_face_3mm={k: INSET.contains(h) for k, h in holes.items()},
    openings_inside_screen={'speedo': Point(*sp_c).buffer(SPEEDO['vis_r'], 256).contains(sp_hole),
                            'tach': Point(*ta_c).buffer(TACH['vis_r'], 256).contains(ta_hole), 'temp_fuel': tf_aa.contains(tf_hole)},
    boards_past_face_outline={k: dict(zip(('area_mm2', 'max_mm', 'top_mm'), past(bd))) for k, bd in (('speedo', sp_board), ('tach', ta_board), ('temp_fuel', tf_board))},
    stock_hole_offset_mm=STOCK_HOLE_OFFSET, hole_margin_mm=HOLE_MARGIN)
for k in ('speedo', 'tach'):
    r = holes[k].bounds[2] - holes[k].centroid.x
    rep[k]['art_scale_for_stock_look'] = round(STOCK_TIPS[k] / STOCK_HOLE_R[k] * r / STOCK_TIPS[k], 3)
    rep[k]['tick_tip_r_at_that_scale'] = round(STOCK_TIPS[k] / STOCK_HOLE_R[k] * r, 2)
os.makedirs(J('docs/layout'), exist_ok=True); json.dump(rep, open(J('docs/layout/layout_v4.json'), 'w'), indent=1)

# ---------------- overlay v4: STL / SVG / DXF ----------------
OUT = J('hardware/overlay_v4'); os.makedirs(OUT, exist_ok=True)
def extrude(geom, h, z0):
    ms = []
    for gg in (geom.geoms if hasattr(geom, 'geoms') else [geom]):
        if gg.area < 1e-3: continue
        m = trimesh.creation.extrude_polygon(gg, h); m.apply_translation([0, 0, z0]); ms.append(m)
    return ms
lips = []
for bd in (sp_board, ta_board, tf_board):
    inner = bd.buffer(FRAME_CLEAR, join_style=2 if bd.geom_type == 'Polygon' and len(bd.exterior.coords) == 5 else 1)
    ring = inner.buffer(FRAME_WALL, join_style=2 if len(bd.exterior.coords) == 5 else 1).difference(inner).intersection(FACE)
    lips.append(ring)
parts = extrude(plate, PLATE_T, 0)
for ring in lips: parts += extrude(ring, FRAME_DEPTH + 0.01, -FRAME_DEPTH)
mesh = trimesh.boolean.union(parts, engine='manifold') if len(parts) > 1 else parts[0]
mesh.export(os.path.join(OUT, 'neon_overlay_v4.stl'))
rep['stl'] = dict(watertight=bool(mesh.is_watertight), bounds=mesh.bounds.round(2).tolist(), volume_cm3=round(mesh.volume / 1000, 1))
def rings(geom):
    out = []
    for gg in (geom.geoms if hasattr(geom, 'geoms') else [geom]):
        if gg.is_empty: continue
        out.append(list(gg.exterior.coords)); out += [list(i.coords) for i in gg.interiors]
    return out
doc = ezdxf.new(); msp = doc.modelspace(); doc.layers.add('PLATE'); doc.layers.add('LOCATING_LIPS', color=5)
for r in rings(plate): msp.add_lwpolyline(r, close=True, dxfattribs={'layer': 'PLATE'})
for ring in lips:
    for r in rings(ring): msp.add_lwpolyline(r, close=True, dxfattribs={'layer': 'LOCATING_LIPS'})
doc.saveas(os.path.join(OUT, 'neon_overlay_v4.dxf'))
minx, miny, maxx, maxy = FACE.bounds
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{maxx-minx+4:.1f}mm" height="{maxy-miny+4:.1f}mm" viewBox="{minx-2:.2f} {-maxy-2:.2f} {maxx-minx+4:.2f} {maxy-miny+4:.2f}"><g fill="none" stroke="black" stroke-width="0.25">']
for r in rings(plate): svg.append('<polyline points="' + ' '.join(f'{x:.3f},{-y:.3f}' for x, y in r) + '"/>')
for ring in lips:
    for r in rings(ring): svg.append('<polyline stroke="blue" points="' + ' '.join(f'{x:.3f},{-y:.3f}' for x, y in r) + '"/>')
open(os.path.join(OUT, 'neon_overlay_v4.svg'), 'w').write('\n'.join(svg + ['</g></svg>']))

# ---------------- mounting-frame trim v4 ----------------
tdoc = ezdxf.new(); tmsp = tdoc.modelspace(); trim = {}; tsvg = []
def tadd(geom, layer):
    for gg in (geom.geoms if hasattr(geom, 'geoms') else [geom]):
        if gg.is_empty or gg.area < 0.5: continue
        tmsp.add_lwpolyline(list(gg.exterior.coords), close=True, dxfattribs={'layer': layer}); tsvg.append((layer, list(gg.exterior.coords)))
tadd(FACE, 'FLANGE_OUTER'); tadd(IN, 'FLANGE_INNER')
for k, bd in (('speedo', sp_board), ('tach', ta_board), ('temp_fuel', tf_board)):
    env = bd.buffer(TRIM_CLEAR, join_style=2 if len(bd.exterior.coords) == 5 else 1)
    fl = env.intersection(FACE).difference(IN); sur = env.difference(FACE)
    tadd(bd, f'BOARD_{k}'); tadd(fl, f'TRIM_FLANGE_{k}'); tadd(sur, f'TRIM_SURROUND_{k}')
    trim[k] = dict(flange_trim_mm2=round(fl.area), surround_trim_mm2=round(sur.area),
                   surround_y_range=[round(sur.bounds[1], 1), round(sur.bounds[3], 1)] if not sur.is_empty else None)
    trim[k]['below_face_max_mm'] = round(max(0, min(y for x, y in FACE.exterior.coords if env.bounds[0] <= x <= env.bounds[2]) - env.bounds[1]), 1) if not sur.is_empty else 0
tdoc.saveas(J('docs/frame/frame_trim_v4.dxf')); json.dump(trim, open(J('docs/frame/frame_trim_v4.json'), 'w'), indent=1)
col = {'FLANGE_OUTER': '#000', 'FLANGE_INNER': '#2a9d4a'}
lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-215 -75 420 150" width="420mm" height="150mm"><g transform="scale(1,-1)" fill="none" stroke-width="0.3">']
for layer, pts in tsvg:
    c = col.get(layer, '#f2a900' if 'TRIM_FLANGE' in layer else '#ff3030' if 'SURROUND' in layer else '#1f77b4')
    lines.append(f'<polygon id="{layer}" stroke="{c}" points="' + ' '.join(f'{x:.2f},{y:.2f}' for x, y in pts) + '"/>')
open(J('docs/frame/frame_trim_v4.svg'), 'w').write('\n'.join(lines + ['</g></svg>']))
rep['frame_trim'] = trim
json.dump(rep, open(J('docs/layout/layout_v4.json'), 'w'), indent=1)

# ---------------- drawings ----------------
def fill(ax, geom, **kw):
    for gg in (geom.geoms if hasattr(geom, 'geoms') else [geom]):
        if gg.is_empty: continue
        x, y = gg.exterior.xy; ax.fill(x, y, **kw)
        for h in gg.interiors: x, y = h.xy; ax.fill(x, y, color='white', lw=0)
def line(ax, geom, **kw):
    for gg in (geom.geoms if hasattr(geom, 'geoms') else [geom]):
        x, y = gg.exterior.xy; ax.plot(x, y, **kw)
fig, axs = plt.subplots(2, 1, figsize=(15, 11.5))
ax = axs[0]
fill(ax, plate, color='#2b2b2b', lw=0)
for bd, c, n in ((sp_board, '#4fc3f7', 'speedo 4C board 126 sq'), (ta_board, '#ffb74d', 'tach 2.8C board O95.9'), (tf_board, '#81c784', '5in board 127.7 x 87.45')):
    line(ax, bd, color=c, lw=1.6, label=n)
line(ax, Point(*sp_c).buffer(SPEEDO['vis_r'], 128), color='#4fc3f7', lw=0.8, ls='--')
line(ax, Point(*ta_c).buffer(TACH['vis_r'], 128), color='#ffb74d', lw=0.8, ls='--')
line(ax, tf_aa, color='#81c784', lw=0.8, ls='--', label='visible areas (dashed)')
for k0 in ('speedo', 'tach'): ax.plot(*P0[k0], 'x', color='#e8b04b', ms=7)
ax.plot(*sp_c, '+', color='w', ms=9); ax.plot(*ta_c, '+', color='w', ms=9)
line(ax, FACE, color='k', lw=1)
ax.set_title(f"Layout v4 + overlay v4 (front view, mm). Openings: speedo O{2*rep['speedo']['hole_r']:.1f}, tach O{2*rep['tach']['hole_r']:.1f}, "
             f"temp+fuel {rep['temp_fuel']['hole_size'][0]} x {rep['temp_fuel']['hole_size'][1]} R{TF_CORNER_R:g}\n"
             f"Moves vs stock: speedo +{GROUP_SHIFT:g}, tach +{GROUP_SHIFT+spread:.2f}, 5in -{tf_shift:g} mm. Board gaps: speedo-tach {rep['gaps']['speedo_tach']}, "
             f"speedo-5in {rep['gaps']['speedo_5in']} mm. x = stock pivots, + = new", fontsize=9)
ax.set_aspect('equal'); ax.set_xlim(-215, 200); ax.set_ylim(-75, 75); ax.grid(alpha=.25); ax.legend(loc='lower right', fontsize=7)
ax = axs[1]
fill(ax, FACE.difference(IN), color='#b9e89a', lw=0)
for k, bd in (('speedo', sp_board), ('tach', ta_board), ('temp_fuel', tf_board)):
    env = bd.buffer(TRIM_CLEAR, join_style=2 if len(bd.exterior.coords) == 5 else 1)
    fill(ax, env.intersection(FACE).difference(IN), color='#f2a900', lw=0); fill(ax, env.difference(FACE), color='#ff3030', lw=0)
    line(ax, bd, color='#1f77b4', lw=1)
line(ax, FACE, color='k', lw=1); line(ax, IN, color='#2a9d4a', lw=1)
ax.fill([], [], color='#b9e89a', label='flange (kept)'); ax.fill([], [], color='#f2a900', label='trim: flange')
ax.fill([], [], color='#ff3030', label='trim: frame/surround outside the face outline'); ax.plot([], [], color='#1f77b4', label='board outlines')
ax.set_title('Mounting-frame trim v4 (boards + 1 mm). ' + '; '.join(f"{k}: flange {v['flange_trim_mm2']} mm², outside {v['surround_trim_mm2']} mm²" for k, v in trim.items())
             + '\nPhoto-derived flange edges are +/-1 mm: scribe from the boards on the part.', fontsize=9)
ax.set_aspect('equal'); ax.set_xlim(-215, 200); ax.set_ylim(-75, 75); ax.grid(alpha=.25); ax.legend(loc='lower right', fontsize=7)
plt.tight_layout(); plt.savefig(J('docs/layout/screen_layout_v4.png'), dpi=110, bbox_inches='tight')
print(json.dumps(rep, indent=1))
