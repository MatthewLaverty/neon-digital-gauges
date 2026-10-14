# Photo-to-asset pipeline (as run 2026-10-13)

The scripts use hard-coded paths from the working sandbox (`/home/user/workspace/scans`, `.../neon-digital-gauges`). Edit the paths before rerunning. Run order:
1. Scale: tape2.py, tape3.py, numerals.py
2. Overlay tracing: holes.py, outer.py, build_geom.py (makes overlay_mm.json)
3. Registration: reg.py, sift.py (homographies H*.npy)
4. Master and pivots: master.py, pivots.py (Hough values are hard-coded in later scripts)
5. Face cleanup: clean.py, art.py, comp.py, reg_face.py (per-gauge ECC correction), export.py
6. Needles and previews: needles.py, needle_art.py, mock.py, mockup.py
7. Overlay: gen_overlay.py (STL/SVG/DXF from overlay_params.json; `--reset` restores defaults), gen_scad.py (writes overlay.scad)

Dependencies: Python 3, numpy, opencv-python, pillow, pillow-heif, shapely, trimesh, manifold3d, ezdxf.
