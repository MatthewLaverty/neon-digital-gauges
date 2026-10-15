import json, numpy as np
geo=json.load(open('overlay_mm_v2.json')); p=json.load(open('/home/user/workspace/neon-digital-gauges/hardware/overlay/overlay_params.json'))
S=geo['shapes']
def arr(pts): return '['+','.join(f'[{x:.3f},{y:.3f}]' for x,y in pts)+']'
def v(a): return '['+','.join(f'{x:.3f}' for x in a)+']'
W=p['windows']; L=[]
L.append('''// 1999 Neon cluster replacement overlay -- parametric starting point
// Units mm. Origin = stock speedo hole arc center, +X right, +Y up (viewed from the driver).
// Geometry traced from a flat photo of the silver overlay (237.5 px/in tape scale, about +/-2%%).
// Measure a few real features with calipers and correct with scale_x / scale_y before trusting fit.
// Z: plate occupies 0..plate_thickness (front face at +Z); screen frames hang behind it (negative Z).
$fn = 128;

/* [Plate] */
plate_thickness = %.2f;
scale_x = %.4f;      // calipers / model for a known width
scale_y = %.4f;
outer_grow = %.2f;   // +/- grows the outer outline
include_lamp_holes = %s;
include_slots = %s;
include_mount_holes = %s;
mount_hole_d = %.2f;
''' % (p['plate_thickness'],p['scale_x'],p['scale_y'],p['outer_grow'],str(p['include_lamp_holes']).lower(),str(p['include_slots']).lower(),str(p['include_mount_holes']).lower(),p['mount_hole_d']))
L.append('/* [Gauge windows] mode: "stock" traced hole, "circle", "intersect" (stock AND circle), "union" */')
for k in ['temp','fuel','speedo','tach']:
    w=W[k]
    L.append(f'{k}_mode = "{w["mode"]}"; {k}_grow = {w["grow"]:.2f}; {k}_offset = {v(w["offset"])}; {k}_circle_d = {w["circle_d"]:.2f}; {k}_circle_center = {v(w["circle_center"])};')
L.append('\n/* [Rear screen frames]  shape 0 = circle (size[0] = glass OD), 1 = rect (size = [w,h]) */')
L.append('// [name, enabled, shape, center, size, clearance, wall, depth]')
fr=[]
for s in p['screens']:
    sz=s['size'] if len(s['size'])==2 else [s['size'][0],0]
    fr.append(f'  ["{s["name"]}", {str(s["enabled"]).lower()}, {0 if s["shape"]=="circle" else 1}, {v(s["center"])}, {v(sz)}, {s["clearance"]:.2f}, {s["wall"]:.2f}, {s["depth"]:.2f}]')
L.append('screens = [\n'+',\n'.join(fr)+'\n];\n')
L.append('/* [Hidden] traced geometry */')
for k,pts in S.items(): L.append(f'P_{k} = {arr(pts)};')
L.append(f'MOUNTS = {arr(geo["mount_holes"]["centers"])};')
L.append('''
module win(P, mode, grow, off, cd, cc) {
  translate(off) offset(r = grow) {
    if (mode == "stock") polygon(P);
    else if (mode == "circle") translate(cc) circle(d = cd);
    else if (mode == "intersect") intersection() { polygon(P); translate(cc) circle(d = cd); }
    else union() { polygon(P); translate(cc) circle(d = cd); }
  }
}
module outer2d() { offset(r = outer_grow) polygon(P_outer); }
module plate2d() {
  difference() {
    outer2d();
    win(P_temp, temp_mode, temp_grow, temp_offset, temp_circle_d, temp_circle_center);
    win(P_fuel, fuel_mode, fuel_grow, fuel_offset, fuel_circle_d, fuel_circle_center);
    win(P_speedo, speedo_mode, speedo_grow, speedo_offset, speedo_circle_d, speedo_circle_center);
    win(P_tach, tach_mode, tach_grow, tach_offset, tach_circle_d, tach_circle_center);
    if (include_slots) { polygon(P_slot_tl); polygon(P_oval_tl); polygon(P_slot_tr); polygon(P_oval_tr); }
    if (include_lamp_holes) { polygon(P_lamp_l1); polygon(P_lamp_l2); polygon(P_lamp_r1); polygon(P_lamp_r2); }
    if (include_mount_holes) for (m = MOUNTS) translate(m) circle(d = mount_hole_d, $fn = 32);
  }
}
module frame2d(s) {
  c = s[3]; sz = s[4]; cl = s[5]; wl = s[6];
  translate(c) difference() {
    if (s[2] == 0) circle(d = sz[0] + 2*cl + 2*wl, $fn = 256);
    else offset(delta = wl) square([sz[0] + 2*cl, sz[1] + 2*cl], center = true);
    if (s[2] == 0) circle(d = sz[0] + 2*cl, $fn = 256);
    else square([sz[0] + 2*cl, sz[1] + 2*cl], center = true);
  }
}
scale([scale_x, scale_y, 1]) {
  linear_extrude(height = plate_thickness) plate2d();
  for (s = screens) if (s[1])
    translate([0, 0, -s[7]]) linear_extrude(height = s[7] + 0.01) intersection() { frame2d(s); outer2d(); }
}
''')
open('/home/user/workspace/neon-digital-gauges/hardware/overlay/overlay.scad','w').write('\n'.join(L))
