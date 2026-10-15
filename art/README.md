# Gauge art — v2 (2026-10-14)

Built from IMG_7574–7577: the cluster with the needles removed, shot close to straight-on. Registered to the earlier overlay frame, then rectified. v1 (from angled photos with needles in place) had a perspective skew of about 5% on the tach; v2 replaces it.

## How v2 was rectified
- **Shape:** one homography was fit so that the tach (17) and speedo (16) tick tips and inner ends fall on true circles at even angular steps. The temp and fuel arcs were included as circles, and the tape lying flat beside the overlay (IMG_7568) was required to have even inch spacing. Fit error was 0.09 mm across 66 tick endpoints. Tape spacing varies 0.3% after the fit, vs 2.6% before.
  - Tach tick ring: ellipse ratio 0.948 → 0.993. Speedo: 0.971 → 0.994.
- **Absolute scale:** from that tape, about ±0.5%. The v1 frame was 1.1% too large.
- **Level:** the frame is rotated 2.17° CCW so the printed text is horizontal. Before, it measured 2.05–2.30° clockwise; now it reads 0.0° by projection profile. Tach and speedo sweeps are symmetric about vertical within −0.2° and +0.5°.
- **Pivots:**
  - Tach and speedo: the fitted tick-circle centers.
  - Fuel: its five ticks meet within 0.3 px.
  - Temp: four ticks meet within 0.4 mm, and agree with the shaft bushing to 0.3 mm. The temp arc itself is about 1.3 mm off-center from the pivot.
- **Face-to-hole alignment:** checked per gauge against the installed-overlay photo (IMG_7569). Temp, fuel and speedo agree within 0.1 mm. The tach needed a 1 mm shift, which is applied.

## Dial geometry (measured)
| | Tick tip radius | Step | Sweep |
|---|---|---|---|
| Tach | 38.4 mm | 14.41° per 500 rpm | 230.6° (0–8000) |
| Speedo | 49.6 mm | 15.43° per 10 mph | 231.4° (0–150) |
| Fuel | — | 21.6° per 1/4 tank | 86.4° (E–F) |

## Color rules
- Background flat black (0,0,0). All letters and numerals white, except tach 7 and 8.
- **Red** = needle orange-red (232,77,61), used for:
  - tach 6500, 7000, 7500 and 8000 ticks
  - tach numerals 7 and 8
  - temp H tick (not the letter)
  - fuel E tick (not the letter)
- **Blue** = photographed km/h blue (147,200,223), used for:
  - the km/h numerals and dots
  - "km/h"
  - "TYPE AC"
  - the temp C (cold) tick (not the letter)

## faces/
- `temp_480.png`, `fuel_480.png`, `speedo_480.png`, `tach_480.png`: 480x480 RGB. Everything outside the stock hole plus 3 mm is black.
- `faces.json`: px/mm, the physical diameter each image covers, image center and pivot (mm, overlay frame), `pivot_px` in each image, hub radius, and hole bounding box.
  - The speedo entry also has `odometer_window_px` and `trip_window_mm`.

| Gauge | px/mm | Image covers | pivot_px |
|---|---|---|---|
| Temp | 7.36 | 65.2 mm | (344.9, 272.5) |
| Fuel | 7.48 | 64.2 mm | (350.0, 271.8) |
| Speedo | 4.48 | 107.2 mm | (240.0, 240.0) |
| Tach | 5.57 | 86.2 mm | (240.0, 240.0) |

- `cluster_master_10pxmm.png`: the whole cleaned face at 10 px/mm. x_mm = u/10 − 205, y_mm = 68 − v/10.

## needles/
- `needle_master_10pxmm.png`: the tach needle (from IMG_7567, rectified), pointing up, flat red with an anti-aliased alpha.
- `needle_<gauge>.png`: one per gauge at that face's px/mm, pointing up.
  - Each is scaled lengthwise to its measured needle: tach 36.2, fuel 37.2, temp 37.9, speedo 47.2 mm (pivot to tip). Width stays the tach's (about 2.4 → 1.8 mm).
  - `needles.json` gives `pivot_px` for each PNG.
- `hub_<gauge>.png`: dark hub caps at the measured hub radius. Draw them over the needle.
- In LVGL, set the image pivot to `pivot_px` and rotate. Angle 0 = needle pointing to 12 o'clock.

## preview/
- `*_holecheck.png`: each face with the overlay hole (magenta) and pivot (green).
- `*_with_needle.png`, `all_with_needles.png`: needles and hubs at demo angles.
- `cluster_mockup.png`, `cluster_mockup_screen_outlines.png`: everything behind the overlay at true scale.

## Remaining limits
- Edges come from photos at about 15–17 px/mm (resampled to 10), so they're slightly soft. Trace to vector for final art if needed.
- The tach 0 tick is rebuilt from the 1000 rpm tick rotated back two steps, because the knob post hid its end. Other areas behind the knob are assumed blank. The odometer windows are black.
- The stock overlay holes sit very close to some ticks (tach 0, speedo 0, temp arc). That's how the stock parts are; it isn't a registration error.
