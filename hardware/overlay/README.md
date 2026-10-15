# Replacement overlay (parametric starting point)

> **v2 (2026-10-14):** the geometry is rectified, so the v1 perspective skew is removed. The method and accuracy are described in `art/README.md`. Overall about 392.3 x 118.8 mm (level); scale about ±0.5% from the tape. Still worth checking one hole with calipers before printing.

- `overlay.scad`: OpenSCAD source. All traced polygons are embedded; parameters are at the top (Customizer-friendly).
- `neon_overlay.stl`: the default parameters, rendered.
  - Front plate: 2.0 mm thick, z 0..2.
  - Rear screen frames: 3 mm deep, z −3..0.
  - It matches the OpenSCAD render (same bounds; volume within 0.2 mm³).
- `neon_overlay_outline.svg` / `.dxf`: 2D outlines. DXF layers are PLATE and SCREEN_FRAMES.
- `overlay_params.json` + `../../tools/face-extract/gen_overlay.py`: Python path producing the same STL/SVG/DXF.
- `overlay_mm.json`: the traced geometry (mm, origin = speedo arc center, +y up).

## Parameters
- `plate_thickness`, `scale_x`, `scale_y`, `outer_grow`.
- Toggles: lamp holes, slots, mount holes; `mount_hole_d`.
- Per gauge window: `<g>_mode` (`stock` traced hole, `circle`, `intersect`, `union`), `<g>_grow` (mm, +/-), `<g>_offset` [dx,dy], `<g>_circle_d`, `<g>_circle_center`.
  - The circle centers default to the needle pivots (speedo, tach) or the face image centers (temp, fuel).
- `screens`: rear locating frames, given as [name, enabled, shape (0 circle / 1 rect), center, size, clearance, wall, depth].
  - The defaults are placeholders sized to the face images: speedo Ø107.2, tach Ø86.2, and one 108 x 64.8 rect behind temp+fuel.
  - Replace them with the measured glass or bezel outline of the panels you buy.

## Accuracy and caveats
- Holes match the installed-overlay photo; face-to-hole registration is under 0.1 mm (tach corrected by 1 mm).
- Absolute scale is about ±0.5% (tape) after rectification. Before printing in final material, print one 0.6 mm test layer and lay it on the stock overlay.
- The bottom edge, where the tape covered it, and the far left end (hand-digitized) are about ±1–2 mm.
- The three mount holes are the ones visible at the right end (Ø4.0). Other attachment features (tabs, clips) were not captured.
- The speedo trip-odometer notch is kept from stock, but no screen covers it in the default layout. Close it (edit P_speedo) or put something behind it.
- The temp/fuel rect frame and the speedo ring nearly touch near x ≈ −54 mm. Panel bezels will decide the real spacing.
