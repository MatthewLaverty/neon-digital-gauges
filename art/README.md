# Gauge art (from photos, 2026-10-13)

> **TEMPORARY ASSETS (2026-10-13):** the faces and overlay were made from angled phone photos and carry a perspective skew. The tach tick ring is about 5% elliptical, with uneven tick spacing (13.7–14.9°); the speedo is about 1.3%. The overlay STL shares the same distortion. Use these for layout and firmware development only. Replace them with flatbed scans (600 dpi, needles removed, steel rule in frame) before printing final parts or art.

Extracted from IMG_7567 (export 150 mph face, housing off) and registered to the silver overlay (IMG_7568 flat, IMG_7569 installed). Shot at 2x on an iPhone 16 Pro Max.

## faces/
- `temp_480.png`, `fuel_480.png`, `speedo_480.png`, `tach_480.png`: 480x480 RGB.
  - Flat black (0,0,0) background, pure white printing.
  - Needle orange (232,77,61) for the temp H tick and the tach 6500–8000 ticks.
  - Photographed blue (147,200,223) for the km/h scale, TYPE AC and the blue dots.
  - Everything outside the stock hole plus 3 mm is black.
- `faces.json`: px/mm, the physical diameter each image covers, image center and pivot (in mm, overlay frame), `pivot_px` (needle rotation center in the image), hub radius, and hole bounding box.
  - The speedo entry also has `odometer_window_px` (the rectangle where a digital odometer can be drawn) and `trip_window_mm`.
- `cluster_master_10pxmm.png`: the whole cleaned face at 10 px/mm.
  - Pixel (u, v) maps to mm with x = u/10 − 205, y = 68 − v/10.
  - Use it to re-crop for a different panel size.

Image framing:
- Speedo and tach are centered on the needle pivot. Their radius is the farthest hole edge plus 1 mm bleed; the speedo trip notch is excluded.
- Temp and fuel are centered on the smallest circle around the hole, plus 1 mm. The pivot is off-center, at about (335, 286) px.

## needles/
- `needle_master_10pxmm.png`: the tach needle, pointing up, flat needle orange, with an anti-aliased alpha. Pivot at (30, 377).
- `needle_<gauge>.png`: sized for that gauge's face px/mm, pointing up. `needles.json` gives `pivot_px` in each PNG.
  - Temp and fuel use the tach needle at 1:1 physical size, because they measured the same: 37.1 and 36.8 mm vs 36.9 mm.
  - Speedo is stretched in length to 47.5 mm, with the width kept.
- `hub_<gauge>.png`: dark hub caps (RGB 20,20,20 with a lighter rim) at the measured hub radius. Draw them over the needle.
- In LVGL, set the image pivot to `pivot_px` and rotate. The needle is drawn pointing up, so angle 0 = 12 o'clock.

## preview/
- `*_holecheck.png`: each face with the overlay hole (magenta) and pivot (green).
- `*_with_needle.png` and `all_with_needles.png`: needles and hubs placed at demo angles.
- `cluster_mockup.png`: all four faces behind the overlay. `cluster_mockup_screen_outlines.png` adds the default screen frames from the STL.

## Needs redraw (hidden under the needles or knob in the photo)
- Temp: the "C" and the lowest ticks next to it are covered by the needle; only a fragment remains.
- Speedo: the "0" mph numeral and the "0" km/h label are partly covered.
- Tach: the area behind the trip-reset knob post is assumed blank.
- Odometer drums were removed. The window is black; draw digits there or leave it as a mask.

## Known limits
- Scale is about ±2 % (tape scale varies across the photo). Caliper one real hole and correct `scale_x`/`scale_y` in the overlay if needed.
- Printing edges come from a faded, photographed face at about 10 px/mm, so they're slightly soft. For final art, trace the masters to vector (Inkscape trace bitmap, or redraw the numerals in a matching font).
- Colors are flat fills by design (per the color rules above); photo color is used only to classify each element.
