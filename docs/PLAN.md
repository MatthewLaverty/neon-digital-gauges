# 1999 Neon ACR (Silver) — Stock-Look Digital Gauge Cluster

Project plan, architecture, parts list, budget, and work items.
Vehicle: silver 1999 Dodge Neon ACR (turbo), Haltech Nexus S2 EMS.
Status: Phase 0 (discovery). Prepared 2026-10-12. Rev 2: decisions log added (section 0).

---

## 0. Decisions Log

| Date | Decision |
|---|---|
| 2026-10-12 | Four gauge boards (one per gauge) plus one hub board. |
| 2026-10-12 | Stock PCM removed. Anything it used to supply (tach signal, VSS sensor power) comes from the Haltech. The digital tach uses CAN RPM, so a Haltech tach output is only a backup. |
| 2026-10-12 | Speed: use the stock VSS if practical; GPS is the fallback. |
| 2026-10-12 | Mode buttons are handled in ESP32 firmware (hub reads buttons, broadcasts mode). GCAN not required. |
| 2026-10-12 | Tank capacity is a stored setting, default 12.5 gal (47.3 L), changeable for a future fuel cell. |
| 2026-10-12 | Revised: digital odometer is acceptable if the display geometry requires it. Add a small info screen under the fuel/temp gauges (odometer/trip, flip to ECU fault page). Fidelity target: stock-inspired, not exact; 3D-printed masks and lathe trim pieces planned. |
| 2026-10-12 | Silver ACR cluster matches the measured car in layout and sizes. One difference: the speedo face art replicates the export-market cluster (150 mph scale) at the same physical size. |
| 2026-10-12 | Fuel/temp gauges may shift up slightly to make room for the info screen. |
| 2026-10-13 | Measurements redone from the silver overlay laid flat with tape (section 4.2d). They replace 4.2b, which underestimated the faces by about 30–40 %. |
| 2026-10-13 | Photo-derived faces/overlay found skewed (~5% on tach). Keep them as temporary assets; redo from flatbed scans later. |
| 2026-10-14 | The cluster can't be scanned non-destructively. v2 faces and overlay rebuilt from needle-free photos with geometric rectification (section 4.2d). |
| 2026-10-14 | Frame leveled: rotated 2.17° CCW. Printed text (RPMX1000, FUEL DOOR, MPH, km/h, TYPE AC, MI) measured 2.05–2.30° clockwise; it now reads 0.0°. Dial sweeps are within 0.5° of symmetric about vertical. Tach 0 tick rebuilt from the 1000 rpm tick (the knob post hid its end); the stop-pin mask by the 8 was tightened. |
| 2026-10-14 | Odometer goes digital (owner): the drum module is too large to keep (rear photos IMG_7579/7580/7582). Odometer is drawn in the bottom of the speedo face, trip meter where FUEL DOOR is printed on the tach. Exact stock text placement is not required. Speedo must stay stock size; the tach may shrink slightly. The white rear body will be trimmed to take the screens. |
| 2026-10-16 | Odometer/trip readout (owner): a 7-segment LCD readout styled after the late-90s Dodge Dakota odometer: upright (no slant), bold segments, hairline gaps. Digit height = the old FUEL DOOR lettering height (21 px on the 480 tach art); both readouts start where the F was (x 150, y 398-418), left-aligned, in a field up to 6 cells wide. Odometer: 6 digits, no tenths. Trip: 999.9, with the decimal point in the gap between cells. Colour: the night printing orange at full saturation, RGB 255,89,0, the same day and night. Trip key: tap toggles ODO/TRIP; hold 2 s resets the trip only (never the odometer), switching to TRIP if ODO is showing so 0.0 is visible. This replaces the separate trip-reset key; on the membrane pad it is key A (Blink key 4). Files: `tools/odo/seg7.py`, `tools/odo/odo_mock.py`, `art/glyphs/seg7/`, `art/preview/odo_trip_preview.png`. |
| 2026-10-16 | FUEL DOOR (owner): the words FUEL DOOR are removed from every tach face (that area becomes the trip/odometer readout). The arrow moves to the fuel face beside the pump icon at 3/4 of the pump height (40 x 38 px), with the same 1.08 mm gap it had after "DOOR"; it sits 2 mm inside the hole. Not on the ethanol face. The pump icon and arrow form a separate A8 layer (`art/faces/fuel_icon_A8.png`, base face `art/faces/fuel_base_480.png`) so the firmware can turn both yellow (placeholder RGB 255,200,0) below a low-fuel threshold still to be decided. Fuel face only, never the ethanol face; the yellow applies day and night. Stock sources are kept in `art/faces/source/`. Files: `tools/alt-faces/fuel_door_arrow.py`, `art/faces/fuel_icon.json`, `art/preview/fuel_lowfuel_preview.png`. |
| 2026-10-16 | Boost alternate tach face, MOCK (daylight only): a boost sub-dial from the owner's Lamco TURBO gauge photo (`art/boost/ref_IMG_7566.jpg`), MPa -0.10 to +0.15, 26 ticks 12 deg apart, -0.10 at 151.1 deg. The ticks are redrawn and the labels lifted from the photo; the hidden 0 is rebuilt from the 0 of ".05"; no logo, screws or outer ring. White on the same black plane, concentric with the tach, tick outer radius 107 px (half the tach's 214 px). The boost needle is the tach master needle scaled to 0.915 of the sub-dial radius, drawn under the tach needle so its hub is hidden. Owner 2026-10-16: TURBO removed from the sub-dial, and RPMX1000 removed from the tach face in boost mode. Files: `tools/alt-faces/boost_face.py`, `tools/alt-faces/tach_boost_mock.py`, `art/boost/`, `art/preview/tach_boost_preview.png`. |
| 2026-10-14 | Oil-temp alternate for the temp gauge: the coolant icon (ISO 7000-0246) is replaced by ISO 2575 F.05 "Engine oil temperature" (ISO 7000-2426), extracted from the ISO 2575:2010 Annex F table, emboldened toward the stock icon's stroke weight, and placed 74 x 54 px at the coolant icon position (44 px inside the hole). C/H, the red hot tick and the blue cold tick are unchanged; only the firmware calibration differs. Files: `tools/alt-faces/oil_temp_face.py`, `art/faces/temp_oil_480.png`, `art/preview/temp_oil_preview.png`. |
| 2026-10-14 | Controls (owner): the stock trip-reset stalk goes away with the cluster internals, so all functions move to one pad. PROPOSED: Blink Marine PKP-2300-SI 6-key CAN keypad (CANopen, 12 V, AT04-4P) on the Haltech bus at 1 Mbit/s, read by the hub. Keys: (1) temp slot coolant/oil, (2) fuel slot level/ethanol, (3) overlay toggle (AFR later), (4) trip reset (hold 2 s), (5-6) spare for the hub or the ECU via GCAN. The hub stores each gauge's function index and overlay bits in NVS and broadcasts them in frame 0x6A1; key LEDs show state. Before choosing the node ID, sniff the bus for collisions with the keypad's CANopen IDs (0x180/0x200/0x580/0x600/0x700 + node). The hub stays behind the cluster. |
| 2026-10-14 | Ethanol alternate for the fuel gauge (owner spec): E becomes 0, F becomes 1, and the 1/2 tick stays (it already sits at mid travel: -73.0 deg vs -72.7 deg midpoint). Needle angle is linear in ethanol fraction from the E tick (-115.9 deg) to the F tick (-29.4 deg). The pump icon is replaced by a ring with a live readout: "E" + integer ethanol % (E67); exactly "E" at 0 %; the text shrinks to fit for E100. Readout glyphs come from the cluster typeface (E from the fuel face, digits from the tach face, 9 = the 6 rotated 180 deg) in `art/glyphs/`. Files: `tools/alt-faces/ethanol_face.py`, `art/faces/fuel_ethanol_static_A8.png`, `art/faces/fuel_ethanol.json`, `art/preview/fuel_ethanol_preview.png`. The ring style borrows the EN 16942 petrol identifier (circle + "E" + ethanol %), a pump-label standard, not a dashboard symbol. |
| 2026-10-14 | Night mode (owner, revised): palette from the owner's stock-cluster night photo, stored in `art/night_palette.json`. White printing becomes orange RGB 250,100,20. The km/h scale and cold tick become blue 20,170,240. Needle-orange ticks and digits (tach 6500+, 7, 8, H tick, E tick) become red 240,5,50. Needles become red 230,5,25, replacing the earlier "needles unchanged". Applies to all four gauges. A slight hub halo (owner wants it even though stock has none): printing orange, from the hub edge to 1.65 hub radii (half the earlier width), peak opacity 0.315 (30% below the earlier 0.45). Implementation: per-color A8 mask layers recolored at runtime. Preview: `tools/night/night_preview.py` -> `art/preview/night_mode_preview.png`, `art/preview/*_480_night.png`. The colors come from a compressed video frame with unknown white balance, so they are a starting point to tune on the real screens. |
| 2026-10-14 | Owner: the cluster housing may be trimmed (there is clearance around the installed cluster). Only the visible areas must stay on the face. Owner prefers the off-the-shelf 86% speedo. Proposed off-the-shelf layout (`docs/layout/screen_layout_v3.png`, `tools/screen_layout_v3.py`): speedo Waveshare ESP32-P4-WIFI6-Touch-LCD-3.4C (115 x 115 mm, Ø87.6 visible, art at 0.86); tach 2.8" round ESP32-S3 board (Waveshare 2.8C or LilyGO T-RGB, Ø70.1 visible, art at 0.887); temp+fuel Waveshare ESP32-S3-Touch-LCD-5 (127.7 x 87.45 mm, full-size art). Speedo and tach move 6 mm right, temp/fuel 7 mm left; boards are 1.2–1.4 mm apart; all visible holes are 3 mm or more inside the face outline. The speedo glass corners extend about 3 mm past the top and bottom of the housing. The fuel-to-speedo hole gap grows from 6.3 to 26.7 mm (set by the 3.4C glass border). Unverified: the 2.8" board outline (assumed Ø95.86 round) and whether the 5" active area is centered on its board. |
| 2026-10-14 | Owner removing all physical indicator lamps. Revised proposal (drawing `docs/layout/screen_layout_v2.png`): bare 4.0" speedo + bare 3.4" tach at full size (6.8 mm gap) + bare 5" for temp/fuel, with the temp/fuel holes and art moved 4.5 mm left (1 mm clear of the speedo). All three fit inside the cluster outline. Against an assumed 3 mm wall, the speedo is 1.6 mm over at the bottom and the 5" corner 1.7 mm over at the top left. Waveshare 4C/3.4C dev boards do not fit (square glass taller than the cluster), even with the tach moved 14 mm. Tach on 3.4" needs a second ESP32-P4. |
| 2026-10-14 | Screen layout PROPOSED (section 4.2e): 4.0" round 720x720 speedo (ESP32-P4), 2.8" round 480x480 tach at about 89% art scale (ESP32-S3), one 5" 800x480 behind temp+fuel (ESP32-S3). Three display boards plus the hub. Pending owner approval. |
| 2026-10-14 | Odometer confirmed (owner): mechanical drum counter behind/below the speedo face plate, viewed through a window inside the speedo hole; trip drums in the lower-right notch. Geometry conflict with a full-size round speedo display recorded in 4.4. Option A vs B to be reconfirmed by the owner. |
| 2026-10-14 | Color rules updated: tach numerals 7 and 8 red like the 6500+ ticks; temp H tick red and C tick km/h blue (letters white); fuel E tick red (letter white). |
| 2026-10-13 | Face art rules: flat black background, pure white printing, tach 6500–8000 ticks and needles in the measured needle orange (RGB 232,77,61), km/h scale keeps the photographed blue (RGB 147,200,223). The tach needle is the master needle for all four gauges. |
| 2026-10-12 | Odometer (earlier): keep stock (option A). It sits at the bottom of the cluster, with room above for the displays. The stock cluster board stays powered and keeps reading VSS on G7. Digital odometer (FRAM) dropped. |

### 0.1 Speed source options (in preference order)
1. VSS into a Haltech digital input. The Haltech broadcasts vehicle speed (0x370, 20 Hz) and the speedo reads CAN. No signal conditioning on the ESP32 side; the Haltech's sensor supply can power the VSS (confirm the VSS works at that voltage).
2. VSS into the hub (opto/comparator input, pulse counter). Gives the most precise odometer counting; independent of the ECU.
3. GPS module on the hub (u-blox class, 10 Hz). Works anywhere with sky view; lags slightly and drops out in tunnels and garages.
Odometer: with option 1, the hub integrates CAN speed over time; with option 2, it counts pulses directly.

### 0.2 Mode buttons and behaviors
Buttons go to the hub's GPIOs. The hub debounces them and puts gauge mode bits in its custom CAN frame (0x6A0). Each gauge decides what to draw from those bits. Example behaviors, all firmware-only:
- Short press A: Temp gauge toggles Coolant / Oil.
- Short press B: Fuel gauge toggles Fuel level / Ethanol %.
- Long press: peak-hold recall, trip reset, or entering a settings menu.
Do not wire buttons to gauge GPIO0: it is a boot-strapping pin, so a pressed or stuck button at power-on puts the board in download mode.
GCAN is only needed if the buttons are wired to the Haltech instead of the hub.

### 0.3 Tank capacity and fuel calibration
- The Haltech converts sender resistance to liters through its own fuel-level calibration; it broadcasts liters (0x3E2).
- The fuel gauge computes fraction = liters / tank capacity. Capacity is stored in ESP32 flash (Arduino `Preferences`/NVS) and defaults to 47.3 L (12.5 gal).
- Change it through a USB-serial command at first; later through a button-combo settings menu or a Wi-Fi config page.
- A fuel cell swap means two changes: recalibrate the Haltech fuel table for the new sender, and set the new capacity on the gauge.

---

## 1. Goal and Scope

Replace the four stock analog gauges with round digital displays that look like the stock faces (bitmap background + rendered needle), reading as much as possible from the Haltech CAN bus.

| Gauge position | Primary mode | Alternate mode | Data source |
|---|---|---|---|
| Tachometer | Engine RPM | — | Haltech CAN (0x360) |
| Speedometer | Road speed + odometer | — | Existing vehicle speed sensor (VSS), hardwired |
| Coolant temp | Coolant temp | Oil temp | Haltech CAN (0x3E0) |
| Fuel level | Fuel level | Ethanol % | Haltech CAN (0x3E2 / 0x3E1) |

Out of scope (for now): warning-lamp replacement, touch UI, data logging, wireless config. These are listed as stretch items in section 9.

---

## 2. What the Stock Cluster Actually Does (Verified)

The 1999 Neon service manual (section 8E) describes a hardwired cluster, not a bus-driven one, which makes this project simpler ([1999 Neon service manual, via carmanualsonline](https://www.carmanualsonline.info/dodge-neon-1999-service-repair-manual/?srch=tachometer)):

- Speedometer and odometer: the VSS output goes through the harness directly to the cluster's speedometer circuitry.
- Tachometer: driven by a square-wave signal from the stock PCM (pin 73). With the Haltech, the tach will come from CAN instead.
- Coolant gauge: fed by a dedicated temperature-gauge sender (separate pin on the sensor connector), not the PCM's coolant sensor signal.
- Fuel gauge: fed by the tank sender, which is shared with the PCM. The manual cites roughly 50–1080 ohms across the range (confirm on your car with a meter).

Answered 2026-10-14 (owner, from the car): the odometer is a mechanical drum counter. It sits behind and below the speedo face plate and is seen through a window inside the speedo hole. A second drum set (trip) shows through the hole's lower-right notch. Measured window positions and their effect on display size are in section 4.4. What drives the drums is still unverified.

---

## 3. Haltech Side

### 3.1 Broadcast protocol (no GCAN needed for reading)

The Nexus already broadcasts a published, fixed set of frames on the Haltech CAN bus. Per the [Haltech CAN Broadcast Protocol V2.35](https://support.haltech.com/portal/api/kbArticles/309315000127455298/locale/en/attachments/8whone12beb10b56646c7893d210fa06b2b86/content?portalId=edbsndab83bda6a605a18494b81368a73ed74e00f5941b9c7dc264955a9257f1b8067&inline=true): 1 Mbit/s, 11-bit IDs, big-endian, temperatures in Kelvin x10.

| Channel | ID | Bytes | Scaling | Rate |
|---|---|---|---|---|
| Engine RPM | 0x360 | 0–1 | 1 RPM/bit | 50 Hz |
| Coolant temp | 0x3E0 | 0–1 | K x10 (°C = raw/10 − 273.15) | 5 Hz |
| Oil temp | 0x3E0 | 6–7 | K x10 | 5 Hz |
| Ethanol % (fuel composition) | 0x3E1 | 4–5 | 0.1 %/bit | 5 Hz |
| Fuel level | 0x3E2 | 0–1 | 0.1 L/bit | 5 Hz |
| Vehicle speed | 0x370 | 0–1 | 0.1 km/h/bit | 20 Hz |
| Oil pressure | 0x361 | 2–3 | 0.1 kPa/bit (gauge = raw/10 − 101.3) | 50 Hz |
| Battery voltage | 0x372 | 0–1 | 0.1 V/bit | 10 Hz |
| Check-engine flag | 0x3E4 | byte 7, bit 7 | flag | 5 Hz |

Verify every entry against the protocol version your NSP firmware actually runs before trusting it, and confirm on the bench with a CAN sniffer (work item W1.4).

Note: fuel level is broadcast in liters, not percent. Your gauge firmware needs the tank capacity to convert it (the Neon tank is about 12.5 gal; confirm).

### 3.2 Where GCAN helps

Haltech says GCAN (Generic CAN) lets the ECU receive and transmit custom CAN messages, with up to 16 user-configured definitions and 4 generic CAN inputs at no extra cost ([Haltech GCAN article](https://www.haltech.com/news-events/gcan-generic-can-for-haltech-ecus/)). You don't need it to read the gauges. It becomes useful if you want to:

- Put the gauge mode-toggle button on a spare Haltech input and broadcast its state, instead of wiring buttons to a separate board.
- Send something from the gauges back to the ECU (for example, hub-computed odometer or a "gauges alive" heartbeat).

### 3.3 Inputs the Haltech must have configured

| Input | Needed for | Likely Haltech input type | Action |
|---|---|---|---|
| Coolant temp | Temp gauge | Existing ECT | Already part of the EMS setup |
| Oil temp sensor | Temp gauge alt mode | AVI (analog) | Add sensor if not already planned |
| Flex fuel sensor | Ethanol % | DPI (frequency) | Add GM-style flex sensor if not already planned |
| Fuel tank sender | Fuel gauge | AVI with pull-up + calibration table | Confirm Nexus S2 AVI pull-up options in the manual; calibrate empty→full |
| VSS (optional) | CAN speed cross-check | DPI | Optional; the speedometer reads VSS directly |

Check the Nexus S2 manual for available AVI/DPI counts and pull-up options. This was not verified here.

---

## 4. Architecture

### 4.1 Recommended layout: four smart displays + one hub

```
                Haltech CAN bus (1 Mbit/s, twisted pair, 120 ohm each end)
 Nexus S2 ──┬───────────┬───────────┬───────────┬───────────┐
            │           │           │           │           │
         Tach        Speedo      Temp/Oil    Fuel/Eth      Hub (ESP32-S3)
       (listen)     (listen)     (listen)    (listen)     • VSS input (conditioned)
                                                          • Odometer storage (FRAM)
                                                          • Mode buttons, dimmer input
                                                          • Transmits one custom frame
                                                          • 120 ohm termination
 12 V switched ─► fuse ─► protection ─► 5 V automotive buck ─► all five boards
```

Each display is an ESP32-S3 board with its own 3.3 V CAN transceiver, running in listen-only mode so it can never disturb the ECU bus. The hub is the only device besides the Haltech that transmits. It reads the VSS, computes speed and odometer, reads buttons and the dimmer, and broadcasts one custom frame (for example 0x6A0: speed, odometer, gauge modes, brightness) that the displays also listen to.

Why this layout:

- Every display runs the same firmware with a config switch (`GAUGE_TYPE`). One codebase, four builds.
- Displays need only two free GPIOs (CAN TX/RX). The Waveshare round boards have very few free pins.
- All 12 V and VSS interfacing lives on one board you can build carefully and protect properly.
- It matches your "controller board + Arduino" expectation, but the controller is an ESP32-S3, because it has a built-in CAN controller (TWAI). A classic Arduino would need an extra CAN chip.

Simpler alternative (fewer boards): wire the VSS and mode button to the Haltech, let it broadcast speed (0x370) and the button state (via GCAN), and skip the hub. The drawback is that the odometer then has no natural home, so this only works if the stock odometer stays mechanical and VSS-driven.

### 4.2 Display selection

Both recommended Waveshare boards are 480x480 round IPS on an ESP32-S3 (8 MB PSRAM, 16 MB flash), with Arduino and LVGL v8.3.10 examples ([ESP32-S3-Touch-LCD-2.1 wiki](https://www.waveshare.com/wiki/ESP32-S3-Touch-LCD-2.1), [ESP32-S3-LCD-2.8C wiki](https://www.waveshare.com/wiki/ESP32-S3-LCD-2.8C)). Using the same resolution and chip for all four gauges means identical code; only the artwork differs.

| Board | Use | Outline | Notes |
|---|---|---|---|
| Waveshare ESP32-S3-LCD-2.8C (480x480) | Tach, speedo | 95.86 mm diameter module | No touch (not needed). Free GPIO: 43/44 (UART), 0 (BOOT, strapping pin) |
| Waveshare ESP32-S3-Touch-LCD-2.1 (480x480) | Coolant, fuel | Round module, about 75 mm | Touch included (unused). Free GPIO: 43/44 via header, 0 |
| Upgrade: Waveshare ESP32-P4 3.4" round (800x800) | Tach/speedo if 2.8" is too small | Larger | Different chip (ESP32-P4), mostly ESP-IDF. Use only if Phase 0 measurements require it |

Pin plan: TWAI TX/RX on GPIO43/44 (the ESP32 can route TWAI to any GPIO). Program over the native USB-C port, because the UART USB-C port uses the same pins. Prove this on the bench (W1.2) before buying all four.

Sunlight: these are standard IPS LCDs, not AMOLED. One open-source gauge author notes the LCD version is less readable in direct sun than their AMOLED option ([M-Gauge](https://github.com/Mr-Mika/M-Gauge)). The stock cluster hood helps. Test this in Phase 1 with one board in the car at noon before committing.

Operating temperature: Waveshare doesn't publish a rated operating range on these wiki pages. Dash temperatures in a parked car can be high. Treat this as a risk to check in validation (W7.5).

### 4.2b Photo measurements (2026-10-12) — SUPERSEDED by 4.2d

Note: the photos are of a different Neon. The user has confirmed the silver ACR's cluster has the same layout and sizes; only the speedo scale differs (150 mph export face).

These are lower bounds: the tape was in front of the faces, so the faces are probably 5–15 % larger. Confirm with calipers on the donor face, lens off.

| Gauge | Measured | Geometry notes |
|---|---|---|
| Speedometer | Face circle ~3.05 in (77 mm) | Flat bottom ~0.62 in below center; odometer window starts ~0.71 in below center |
| Tachometer | Face circle ~2.26 in (57 mm) | Flat bottom ~0.6 in below center; trip-reset knob (likely) edge ~0.95 in from center at lower-left |
| Fuel / Temp | Smallest circle around each face ~1.66 in (42 mm) | Face-to-face pitch ~1.54 in (39 mm); arc radius from pivot ~1.16 in |

Findings:
- Round dev boards are physically too big: the Waveshare 2.1 board is 75 mm across and the 2.8C is 95.86 mm, against 39 mm small-gauge pitch and a 77 mm speedo face.
- Any round display that covers the full speedo face (≥77 mm, radius ≥1.5 in) also covers the stock odometer window (0.71 in below center).
- A 2.1 in round active area on the tach reaches the likely trip-reset knob.
- Gate 0 now has to choose between: rectangular panels behind a printed black mask, bare round panels on custom carriers with scaled art, or revisiting the odometer decision.

Annotated image: `docs/neon-gauge-measurements.jpg`.

### 4.2d Overlay and face measurements — v2 (2026-10-14, rectified)

v1 (2026-10-13) had a perspective skew of about 5% on the tach. v2 uses needle-free photos (IMG_7574–7577) and a homography fit that makes the tach and speedo tick rings true, evenly spaced circles, with the tape beside the flat overlay as an even-spacing constraint. Fit error 0.09 mm. Scale is about ±0.5%; v1 was 1.1% too large. Method: `art/README.md`.

| Hole | Size (W x H) | Needle pivot (mm) | Face image (480 px) covers | px/mm |
|---|---|---|---|---|
| Temp | 50.6 x 62.3 mm | (-121.7, -1.5) | 65.2 mm | 7.36 |
| Fuel | 48.8 x 61.7 mm | (-66.9, -1.1) | 64.2 mm | 7.48 |
| Speedo | 119.8 x 85.8 mm (arc ≈100 mm dia + trip notch) | (0.2, -1.0) | 107.2 mm on pivot | 4.48 |
| Tach | 78.7 x 74.4 mm (+ knob lobe) | (107.1, -1.1) | 86.2 mm on pivot | 5.57 |

Overlay: about 392.3 x 118.8 mm, measured level. The pre-level v2 figure of 125 mm was the bounding box of the tilted outline.
- Dials: tach ticks 38.4 mm radius, 14.41°/500 rpm, 230.6° sweep. Speedo 49.6 mm, 15.43°/10 mph, 231.4° sweep (0–150). Fuel 21.6° per quarter.
- Needles: tach 36.2, fuel 37.2, temp 37.9, speedo 47.2 mm (pivot to tip). All about 2.4 → 1.8 mm wide.

Display-fit consequences (arithmetic from nominal diagonals, not datasheet active areas):
- A 2.8 in round panel (about 71 mm) is too small for the tach and speedo. A 3.4 in (about 86 mm) covers the tach. The speedo needs about 4 in, or a smaller window with shrunk art.
- Round screens sized to the temp and fuel holes would overlap each other and the speedo screen. Default: one rectangular panel behind both (a 5 in 15:9 panel, about 108 x 65 mm, spans both holes).

Assets: `art/` and `hardware/overlay/`. Pipeline scripts: `tools/face-extract/` (v1) and `tools/face-extract/v2/`.

### 4.2e Screen layout proposal (2026-10-14, pending approval)

Drawing: `docs/layout/screen_layout.png` (script `tools/screen_layout.py`; overlay frame mm). Bare panels, not dev boards with cover glass: Waveshare's ESP32-P4 4.0" round board is 126 x 126 mm and the 3.4" is 115 x 115 mm ([Waveshare](https://www.waveshare.com/esp32-p4-wifi6-touch-lcd-3.4c.htm)). Centered on the pivots, which are 106.9 mm apart, the two would collide by about 14 mm.

| Gauge | Panel | Active / outline | Fit result |
|---|---|---|---|
| Speedo | 4.0" round 720x720 MIPI, bare (e.g. [Raystar RFN04000A2A0YWMNN00](https://www.raystar-optronics.com/4.3-4.6-tft-lcd-display-module/720x720-tft.html)) | Ø101.52 / 105.3 x 109.62 x 2.3 mm | Stock size. Covers the hole except the old trip notch (333 mm², closed in the new overlay). Odometer band (31 x 6.6 mm) sits at the bottom inside the hole |
| Tach | 2.8" round 480x480 (ST7701, RGB), bare | Ø70.13 / about 73.0 x 76.5 mm ([Raystar round range](https://www.raystar-optronics.com/round-tft-lcd-display.htm)) | Art scaled 0.887 (tick tips 38.4 → 34.1 mm radius); the overlay's tach hole shrinks to match. Clears all indicator windows. Trip meter in the FUEL DOOR spot |
| Temp + fuel | 5.0" 800x480 RGB, bare (e.g. [EA TFT050-84AITP](https://www.displayvisions.us/eng/pdf/grafik/TFT050-84AITP.pdf)) | 108 x 64.8 / 120.7 x 75.8 mm | Covers both holes completely at full size |

Conflicts (from the drawing):
- The 5" frame overlaps the upper-left turn-signal slot (151 mm²), the upper-left oval window (123 mm²) and the two left lamp windows (45 and 97 mm²). Options: draw those telltales on the 5" screen (the oval window sits mostly over its active area), or light them from the side.
- The 5" and 4" frames overlap by 88 mm², bezel only and outside both visible holes. Stagger the depth by about 3 mm, or pick a 5" panel with a narrower right bezel.
- Alternative tach: a bare 3.4" round (Ø87.6 active, 94.9 x 96.95 mm, [DisplayModule](https://www.displaymodule.com/products/3-4-inch-800x800-tft-display-mipi-dm-tftr34-478)) keeps the tach at full size. It overlaps the upper-right oval (12 mm²), the slot (3 mm²) and both right lamp windows (43 and 34 mm²), and it needs a second ESP32-P4 because it is MIPI.

Electronics:
- Speedo on an ESP32-P4. Its MIPI DSI is 2-lane (Waveshare's 720x720 4C runs 2 lanes at 1.5 Gbps; [Waveshare repo](https://github.com/waveshareteam/ESP32-P4-WIFI6-Touch-LCD-XC)). The panel's driver must support 2-lane mode; some 4" panels are specified as 4-lane. It also needs an FPC adapter and a backlight driver. This is the main custom-hardware item. The ESP32-P4 has three TWAI controllers with listen-only mode ([Espressif datasheet](https://documentation.espressif.com/esp32-p4_datasheet_en.pdf)).
- Tach and temp+fuel on ESP32-S3 RGB-parallel, as before; one board drives both small gauges.
- The info screen (4.2c) is no longer needed for odometer/trip; it is optional for the ECU fault page.
- Pixel density: 720/101.52 = 7.09 px/mm (speedo), 6.84 (tach), 7.41 (5"). Re-export the art from the 10 px/mm master.

Open: depth behind the faces and the trim lines in the white body (IMG_7582) are not mapped yet; panel thickness is 2.1–4.3 mm before the boards behind.

### 4.2c Info screen under fuel/temp (~1 in working height)

| Candidate | Active area (W x H) | Board / module | Price | Notes |
|---|---|---|---|---|
| LilyGO T-Display-S3 (1.9" 170x320 IPS, ESP32-S3 onboard) | ~43 x 23 mm (calculated from diagonal) | 62 x 26 x 10 mm | $9.04 at LilyGO | Best fit: its own CAN node (add a transceiver), color |
| Waveshare ESP32-S3-LCD-1.9 (170x320) | same panel class | not checked | $15.99–19.99 | Alternative to the LilyGO |
| 2.42" 128x64 OLED (SSD1309) | 55.01 x 27.49 mm | glass 60.5 x 37 mm; PCB ~71 x 43.5 mm | ~$7–14 | Classic odometer look, mono; needs an MCU; PMOLED brightness is modest and burn-in is possible |
| 3.12" 256x64 OLED (SSD1322) | 76.78 x 19.18 mm | ~100 x 34 mm module | $29.95 | 16 grey levels; probably too wide for the space |

ECU data for the fault page (Haltech broadcast): Check Engine Light (0x3E4 bit 7:7); Engine Protection Reason as an OBD-II style code plus severity (0x6F3); Engine Limiting Active (0x36E); trigger error count (0x369); Trip Meter 1 in meters (0x6F6). The broadcast does not include a stored-DTC list, so a full list would need NSP or another method (unverified).
If the odometer goes digital: the hub counts VSS and stores mileage in FRAM. Re-add the FRAM to the BOM and seed it with the silver ACR's actual mileage, read from its own cluster at swap time.

### 4.2a Daylight-readable display options

| Option | Size / resolution | Brightness | Price per board | Fit with this plan |
|---|---|---|---|---|
| Baseline: Waveshare ESP32-S3 2.1 / 2.8C IPS | 2.1" and 2.8", 480x480 | Not published | $32.99 (2.1) | Drop-in, Arduino, LVGL 8.3 |
| Waveshare ESP32-S3-Touch-AMOLED-1.75 | 1.75", 466x466 | 700 cd/m² | $29.99–41.99 | Arduino-capable ESP32-S3; much smaller; small gauges only, if the dials allow |
| High-brightness round IPS panel, bare (700–1000 nits) | 2.8" 480x480, 3.4" 800x800 | 700–1000 nits | About $185 listed for a 700-nit 2.8" MIPI panel; others quote-only | Needs an ESP32-P4 or custom carrier board; a custom hardware project |

Sources: [Waveshare AMOLED 1.75](https://www.waveshare.com/esp32-s3-touch-amoled-1.75.htm?sku=31262), [Waveshare AMOLED family](https://www.waveshare.com/product/esp32-related/displays/amoled.htm), [Alibaba 700-nit 2.8" round listing](https://electronics.alibaba.com/product/sunlight-readable-touch), [Teamworks 3.4" 1000-nit round](https://www.teamworks-display.com/3-inch-tft-lcd-display-product/).
AMOLED caveat: static gauge faces are the worst case for OLED burn-in. Mitigate with dimming, a slow pixel shift, and blanking at key-off.

### 4.3 Graphics approach (stock look)

- Background: scan a donor cluster's faces on a flatbed at 1200 dpi, clean them up and redraw them in Inkscape/GIMP, then export each face at exactly 480x480. Remove the printed needle hub, and render the face without its pointer.
- Needle: a separate narrow PNG with alpha, rotated around its pivot by LVGL (`lv_img_set_pivot` / `lv_img_set_angle` in v8.3). Keep the needle image small, because rotating large images is the main performance cost on the ESP32-S3.
- Multi-purpose gauges: two backgrounds per gauge (Coolant/Oil, Fuel/Ethanol), swapped on mode change. Add a small mode legend, styled like the stock text, so you always know which mode is showing.
- Night mode: with the headlamps on, the white-printing mask is recolored orange (see the decisions log). PWM backlight dimming is driven by the hub's dimmer reading.
- Behavior: sweep the needle on boot (classic cluster check). Smooth with a simple low-pass filter; RPM arrives at 50 Hz, but temperatures arrive at 5 Hz and need interpolation. If no CAN data arrives for 500 ms, park the needle and show a fault indicator. Never freeze on a stale value.
- Assets go into flash as C arrays through the LVGL image converter. 480x480 RGB565 is about 450 KB per face, which fits easily in 16 MB flash.

### 4.4 Odometer: mechanical drum (confirmed 2026-10-14). Option A vs B to be reconfirmed

Status: the decisions log disagrees with itself. One entry (2026-10-12, "Odometer (earlier)") keeps the stock odometer (option A). A later entry the same day says a digital odometer is acceptable if the display geometry requires it, shown on the info screen. The geometry below shows the display does constrain it, so the owner needs to pick one.

What it is (owner, 2026-10-14): a mechanical drum counter that sits below the speedo face plate and is seen through a window in the face.

Measured positions, from the leveled v2 frame (mm; origin = speedo hole arc center, +y up; the speedo pivot is at (0.2, −1.0)):

| Window | x | y | Size | Distance from speedo pivot |
|---|---|---|---|---|
| Odometer (6 drums, "123416" in the photo) | −16.8 to 14.5 | −34.5 to −27.9 | 31.3 x 6.6 mm | 30.9 mm (nearest corner) to 37 mm |
| Trip (4 drums, in the hole's lower-right notch) | 36.8 to 67.5 | −35.0 to −27.5 | ≈31 x 7.5 mm | 45.5 to 75 mm |

Both are photo measurements (±0.5 mm scale, about 1 mm edge uncertainty). The trip window size is read by hand because its clear lens defeated automatic edge detection. Confirm with calipers at teardown.

Geometry conflict:
- Anything opaque centered on the speedo pivot that extends more than about 30.9 mm, whether active area, bezel or PCB, covers the odometer window. That limits a centered round speedo display to about 61 mm outside diameter.
- Filling the stock hole needs about 100 mm (tick tips at a 49.6 mm radius), and the full face image is 107.2 mm. The Waveshare 2.1" board (75 mm across) and the 2.8C (95.86 mm) would both cover the window.
- The trip window lies outside the speedo screen frame and clears the tach screen (center x 107.1, about Ø86), so it can stay visible with any of the planned speedo displays.

Options, revised with this geometry:

| Option | How | Pros | Cons |
|---|---|---|---|
| A. Keep the drums visible in place | The speedo display stays above y ≈ −27.9 mm, or has a cutout around the window. In practice that means a rectangular or notched panel behind a printed mask, or a smaller round panel mounted high | Original mileage stays authoritative; no seeding or disclosure issue | The speedo cannot fill its stock hole with a standard round panel; the lower ticks (0 and 150 mph at a 49.6 mm radius) fall beside or below the window band, so the panel shape is the hard part |
| B. Digital odometer | The drums are hidden behind the display. The hub counts VSS and stores mileage in FRAM; odometer and trip appear on the speedo screen (`odometer_window_px` is in `faces.json`) or on the info screen | Free choice of speedo display size; matches the 2026-10-12 "digital acceptable" entry | Seed and protect the mileage; record the stock reading with photos; check odometer disclosure rules |
| C. Relocate the drum module | The mechanical module moves to a window below the displays or near the info screen | Keeps the mechanical count and a full-size speedo | Fabrication-heavy; depends on how the drums are driven (see check 1) |

Teardown checks still open (W0.2):
1. What drives the drums: a motor on the cluster board fed from VSS, or a mechanical link to the speedometer movement. This is unverified and decides whether A or C is even possible without the stock movement.
2. Whether the drums keep counting with the speedometer movement unplugged or removed. If they stop, the movement stays connected and hidden.
3. The cluster's power, ignition, and ground pins that the drum driver needs.
4. Depth: how far the drum faces sit behind the face plate, and the lens-to-plate gap, for any display stacked in front.

If B is chosen: write down and photograph the stock mileage before the swap, re-add the FRAM to the BOM (section 4.3), and look up current odometer disclosure rules for your situation.

### 4.5 VSS interface (hub) — rev 3

The stock PCM is not needed. Per the 1999 Neon wiring diagram ([third-party upload of the factory diagram](https://www.scribd.com/document/314384581/Diagramas-Electricos-Dodge-Neon)), the PCM did three jobs for the VSS:
- 8 V supply on circuit K7 (orange, PCM cavity 44). On the 2.0L this same 8 V circuit also feeds the crank and cam sensors ([TroubleshootMyVehicle](https://troubleshootmyvehicle.com/chrysler/2000/cam-sensor-wiring-diagram)).
- Sensor ground on K4 (black/light blue).
- Received the signal on G7, which also goes directly to the cluster's speedometer/odometer on manual-trans cars.

To replace the PCM:
1. 8 V supply: if the Haltech harness already powers the crank and cam sensors from the old orange 8 V circuit, the VSS may already be powered. Measure at the VSS connector with the key on. If not, add a small 8 V automotive regulator on the hub. Check whether the Nexus S2 has an 8 V output (not verified).
2. Ground: use the Haltech sensor ground or the hub ground, not chassis ground.
3. Signal pull-up (unknown): a Hall sensor of this type usually only switches the signal low, and something else pulls it up. It's unverified whether that pull-up was in the PCM, the cluster, or both. With the PCM gone, back-probe G7 with the cluster connected while rolling the car. If it never rises, add a pull-up on the hub.
4. ESP32 input: high-impedance level shifting (resistor divider into a Schmitt-trigger buffer, or an optocoupler) into the pulse counter (PCNT). Never connect directly to a 3.3 V pin.
5. Shared signal: the cluster's odometer, the ESP32, and optionally a Haltech input can all listen to G7 as long as there is one pull-up and all inputs are high-impedance.
6. Calibration: pulses per mile are set in config and checked against GPS.

Keeping the stock odometer also means the stock cluster circuit board (its odometer driver) stays powered and connected. That is still a packaging question for Gate 0.

### 4.6 Power and protection

The 12 V circuit must be ignition-switched and fused, with reverse-polarity protection, a TVS diode for load dump and spikes, and an automotive-rated buck converter feeding a 5 V rail to all boards. The Pololu D36V28F5 (5 V, 3.2 A) lists a 6–50 V input range and reverse-voltage protection to −40 V ([Pololu](https://www.pololu.com/product/3782)). Budget about 0.3–0.5 A per display at full backlight (an estimate; measure in W1.3).

### 4.7 Updating firmware after install (Wi-Fi OTA, USB as recovery)

- Normal path: over-the-air (OTA) over Wi-Fi. With ArduinoOTA in the sketch, each board shows up in the Arduino IDE under Tools → Port → Network ports and uploads like USB ([Espressif-adjacent tutorial](https://blog.hirnschall.net/esp32-ota-update/)). The alternative is a browser upload page (`/update`) for a `.bin` file ([Arduino-ESP32 docs](https://docs.espressif.com/projects/arduino-esp32/en/latest/ota_web_update.html)), which works from a phone.
- Network: the car has no router. Use a phone or laptop hotspot with a fixed SSID, or have the hub act as the access point.
- Service mode: Wi-Fi stays off while driving. A long-press button combo makes the hub broadcast a "service" bit, and every board then joins Wi-Fi and starts its OTA listener. Each board shows its name and IP address on screen while in service mode.
- Partitioning: OTA needs two app slots plus otadata ([Espressif OTA docs](https://docs.espressif.com/projects/esp-idf/en/v5.1.3/esp32/api-reference/system/ota.html)). Pick a 16 MB scheme with OTA and confirm the firmware, including face images, fits in one slot. The first flash with that scheme must be over USB.
- Rollback: the official Arduino-ESP32 core ships with rollback enabled ([arduino-esp32 discussion](https://github.com/espressif/arduino-esp32/discussions/12350)), but by default it marks a new image valid early at boot ([core source](https://raw.githubusercontent.com/espressif/arduino-esp32/master/cores/esp32/esp32-hal-misc.c)). Override `verifyRollbackLater()` and only mark the image valid after display, CAN, and Wi-Fi are all confirmed working. A bad build then reverts on its own.
- USB is still required for: the first flash, partition-table changes, and recovery from a build that broke before rollback could catch it. Route a USB-C extension from each gauge (or a small USB hub) to an accessible spot behind the cluster or under the dash.
- Back-feed check: before plugging a laptop into a gauge that is also powered from the car's 5 V rail, check the board schematic for VBUS isolation, or unplug car power first.
- GitHub: a GitHub Actions job using `arduino-cli` builds one `.bin` per gauge type for each tagged release. Download the right file to your phone and upload it through the web OTA page.

---

## 5. Existing Open-Source Work to Use

All of these are community projects. They are useful references, but treat them as unvalidated until you've reproduced the behavior on your own bench. Check each license before copying code into your repo.

| Project | What it gives you | Caveats |
|---|---|---|
| [traviscea/center-cluster-esp32-p4](https://github.com/traviscea/center-cluster-esp32-p4) | ESP32-P4 round-display cluster that decodes the Haltech CAN broadcast; closest match to this project | ESP-IDF rather than Arduino; P4 platform. Use as a decoding and structure reference |
| [Mr-Mika/M-Gauge](https://github.com/Mr-Mika/M-Gauge) | Round CAN gauge with multiple ECU protocol options and a configurable UI | Haltech support is listed but may be lightly tested (community code). Check the license before reusing |
| [garagetinkering/Ultimate_Gauge_Board_PIO](https://deepwiki.com/garagetinkering/Ultimate_Gauge_Board_PIO/1-overview) | ESP32-S3 + ST7701 480x480 + TWAI + LVGL needle-image gauge on Arduino core / PlatformIO; same stack as the recommended boards | Uses LVGL 9.3 and 500 kbps CAN; you need LVGL 8.3 (Waveshare BSP) and 1 Mbit/s. License not stated |
| Waveshare demo code (wiki pages above) | Known-good display init, LVGL 8.3.10 port, and pin maps for the exact boards | Starting point for the gauge firmware; fork it |
| [handmade0octopus/ESP32-TWAI-CAN](https://github.com/handmade0octopus/ESP32-TWAI-CAN) | Simple Arduino wrapper for the ESP32 built-in CAN | Optional; the ESP-IDF TWAI driver works fine from Arduino too |
| [SavvyCAN](https://github.com/collin80/SavvyCAN) | Desktop CAN sniffer/replayer for bench work | Pair with a USB-CAN adapter |

Recommended approach: start from the Waveshare 2.1 demo for display/LVGL, follow the Ultimate Gauge Board for the needle-on-bitmap pattern, and use the Haltech protocol PDF plus the traviscea decoder for CAN. Don't fork the cluster projects wholesale. Pull ideas, not dependencies.

---

## 6. GitHub Workflow

- One repo (`neon-digital-gauges`) using the layout in this scaffold: `firmware/gauge` (single codebase, `GAUGE_TYPE` build flag), `firmware/hub`, `firmware/can-sim`, `assets/`, `hardware/`, `mechanical/`, `docs/`.
- Pin library versions. LVGL 8.3.10 and the ESP32 Arduino core version used by the Waveshare demos go in `docs/TOOLCHAIN.md`. LVGL version mismatches are the most common way these projects break. Moving from Arduino IDE to PlatformIO later makes builds reproducible, but it's optional at the start.
- Use Git LFS for scans and design files (`.tif`, `.psd`, `.xcf`, `.svg` masters). The provided `.gitattributes` handles this. Generated C-array images are committed normally.
- Use one GitHub Issue per work item below, with a Project board in phase columns. Tag firmware releases (`gauge-v0.1`) so you always know what is flashed in the car.
- Keep the repo private at first if you reuse code from projects with non-commercial or unclear licenses.

---

## 7. Work Items

Hour estimates are rough guesses for a hobbyist pace, not commitments. Each phase ends with a gate; don't buy the full display set until Gate 1 passes.

### Phase 0 — Discovery and measurement (about 6–10 h)
- W0.1 Buy a donor 1995–99 Neon cluster with a tach so the car stays drivable.
- W0.2 Tear down the donor: measure each dial's visible diameter, the needle pivot location, depth available behind the faces, the lens-to-PCB gap, and the odometer type and location. Photograph everything. Record in `docs/cluster-teardown.md`.
- W0.3 Map the cluster connector pins on your car: VSS, sender inputs, dimmer, ignition, ground, warning lamps.
- W0.4 Confirm the VSS type and supply voltage under the Haltech harness.
- Gate 0: choose display sizes (2.8"/2.1" vs P4 upgrade) together with the odometer option (A/B/C in section 4.4). The drum window caps a centered round speedo display at about 61 mm outside diameter unless B or C is chosen. Confirm the four teardown checks in section 4.4.

### Phase 1 — Bench proof of concept (about 10–15 h)
- W1.1 Buy one ESP32-S3-Touch-LCD-2.1, two SN65HVD230 modules, a USB-CAN adapter, and a spare ESP32-S3 DevKit.
- W1.2 Flash the Waveshare LVGL demo. Then move TWAI to GPIO43/44 and confirm display + CAN together while programming over native USB.
- W1.3 Measure current draw at full and minimum backlight.
- W1.4 Build `can-sim`: the DevKit transmits fake Haltech frames (0x360, 0x3E0, 0x3E1, 0x3E2) at the documented rates. Decode them on the display (text first, no graphics).
- W1.5 Connect to the real Nexus S2 on the bench (or in the car, engine off). Sniff with SavvyCAN and confirm IDs and scaling.
- W1.6 Noon sunlight test: hold the board behind the stock lens and hood.
- Gate 1: CAN decode is correct, the display is readable, and the pin plan works. Then order the remaining displays.

### Phase 2 — Gauge face artwork (about 12–25 h, the largest skill-learning chunk)
- W2.1 Scan all four faces at 1200 dpi, plus the needles.
- W2.2 Redraw the faces as vectors (Inkscape) for crisp output; export 480x480 PNGs, needle-less.
- W2.2a Speedo face: recreate the export-market 150 mph face, not the photographed 120 mph one. Get a flat, square-on scan or photo of an export face as the art reference, and record its start/end angles and tick spacing for the value-to-angle table.
- W2.3 Create the alternate faces: Oil Temp (scale to suit your oil sensor range) and Ethanol 0–100 %, matching stock fonts and style.
- W2.4 Create the needle PNG(s) with alpha and mark the pivot coordinates.
- W2.5 Convert to LVGL C arrays; document the pipeline in `tools/`.

### Phase 3 — Gauge firmware (about 20–35 h)
- W3.1 Common codebase with a `GAUGE_TYPE` build flag (TACH, SPEEDO, TEMP, FUEL).
- W3.2 Value-to-angle mapping tables, per gauge, measured from the stock face (stock scales are often non-linear; temp and fuel especially).
- W3.3 Smoothing, boot sweep, stale-data fault behavior, and a CAN listen-only guard.
- W3.4 Mode toggle (listen for the hub frame) with a background swap.
- W3.5 Brightness from the hub frame.
- W3.6 (dropped: stock odometer kept). Optional: a digital trip meter on the speedo face.
- W3.7 Service mode, ArduinoOTA plus web OTA, and delayed rollback validation. Test a deliberately broken build on the bench to prove rollback works.
- W3.8 GitHub Actions build of per-gauge `.bin` files on tagged releases.

### Phase 4 — Hub board (about 15–25 h)
- W4.1 Schematic (KiCad, committed to `hardware/`): fuse, reverse protection, TVS, buck, CAN transceiver + termination, VSS conditioning, button inputs, dimmer input divider.
- W4.2 Build on perfboard first; order a PCB later (optional).
- W4.3 Firmware: PCNT speed, GPS-calibrated pulses per mile, debounced buttons, custom CAN frame TX. (No odometer storage; the stock odometer is kept.)
- W4.4 Document the custom frame in `docs/CAN-MAP.md` and confirm that its ID doesn't collide with Haltech IDs.

### Phase 5 — Mechanical (about 15–30 h)
- W5.1a Lay out the info screen under fuel/temp; shift the fuel/temp openings up slightly if needed. Check clearance to the lens and housing.
- W5.1 Model a mounting plate in the stock cluster housing (Fusion/Onshape) that holds the four displays concentric to the original openings.
- W5.2 Print in ASA/PETG (PLA will deform in a hot dash). Add light seals between gauges.
- W5.3 Reuse the stock lens and face bezel; add an optional thin printed or vinyl mask to hide the display edges.
- W5.4 Check-fit, then the internal harness with strain relief.

### Phase 6 — Vehicle integration (about 8–15 h)
- W6.1 Haltech config: oil temp, flex, and fuel level inputs plus calibration; confirm broadcast on.
- W6.2 CAN harness: twisted pair, short stubs, termination at the Nexus and the hub only.
- W6.3 Power: ignition-switched fused feed and a good ground.
- W6.5 USB service pigtails routed to an accessible location.
- W6.4 Fuel sender: move it from the cluster to a Haltech AVI and calibrate by filling from empty in known increments.

### Phase 7 — Validation (about 6–12 h)
- W7.1 Speedometer against GPS at 30/45/60/75 mph.
- W7.2 Coolant/oil temp on the gauge against Haltech NSP live values.
- W7.3 Fuel level calibration against gallons added; ethanol against a tester.
- W7.4 Cranking brownout: displays must recover cleanly and the odometer must not corrupt.
- W7.5 Heat soak (parked in sun) and night dimming.
- W7.6 Vibration and loose-connector checks after a drive.

Total: roughly 90–170 hours. Phases 2 and 3 carry the widest uncertainty.

---

## 8. Parts List and Budget

Prices are list prices at time of research and change often. Items marked "est." are estimates without a checked listing.

### Core (required)

| Qty | Part | Unit | Ext. | Source / note |
|---|---|---|---|---|
| 2 | Waveshare ESP32-S3-LCD-2.8C (tach, speedo) | ~$33 | ~$66 | [Waveshare wiki](https://www.waveshare.com/wiki/ESP32-S3-LCD-2.8C); price est. |
| 2 | Waveshare ESP32-S3-Touch-LCD-2.1 (temp, fuel) | $32.99 | ~$66 | [Waveshare store](https://www.waveshare.com/esp32-s3-touch-lcd-2.1.htm) |
| 1 | ESP32-S3-DevKitC-1 N8R8 (hub) | ~$15 est. | $15 | |
| 1 | ESP32-S3 DevKit (bench CAN simulator) | ~$15 est. | $15 | Reused later as a spare |
| 6 | SN65HVD230 3.3 V CAN transceiver module | $4.99 | ~$30 | [Waveshare SN65HVD230 board](https://www.waveshare.com/sn65hvd230-can-board.htm) |
| 1 | Pololu D36V28F5 5 V 3.2 A buck | ~$25 est. | ~$25 | [Pololu](https://www.pololu.com/product/3782) |
| 1 | Protection: inline fuse + holder, TVS (e.g., SMBJ-series), P-FET or Schottky reverse protection, caps | | ~$15 est. | |
| 1 | VSS conditioning: optocoupler (e.g., 6N137/PC817 class), resistors, zener | | ~$8 est. | |
| 1 | Momentary buttons (mode toggles) | | ~$10 est. | Or use a Haltech input + GCAN |
| 1 | Connectors, wire, twisted pair, heat shrink, perfboard, headers | | $40–80 est. | |
| 1 | Donor 1995–99 Neon cluster (with tach) | | $30–80 est. | Junkyard / eBay |
| 1 | Filament (ASA/PETG) or print service | | $25–60 est. | |
|  | Core subtotal | | about $345–485 | |

### Tools (skip what you already own)

| Part | Est. | Note |
|---|---|---|
| USB-CAN adapter (CANable-class) | $30–50 | Bench sniffing with SavvyCAN |
| Logic analyzer (8-ch, cheap Saleae clone) | $15–20 | VSS pulse debugging |
| Bench power supply (adjustable, current-limited) | $40–80 | Strongly recommended for 12 V testing |

### Haltech sensors (only if not already planned for the EMS)

| Part | Est. |
|---|---|
| GM-style flex fuel sensor + connector + fittings | $80–150 |
| Oil temp sensor + adapter fitting | $30–60 |

### Optional upgrade

| Part | Est. | Note |
|---|---|---|
| 2x Waveshare ESP32-P4 3.4" round 800x800 (tach/speedo) | $64.99–74.99 each ([Waveshare](https://www.waveshare.com/product/esp32-related/boards-kits/esp32-p4-wifi6-touch-lcd-3.4c.htm)) | Only if Gate 0 shows 2.8" is too small; adds an ESP-IDF learning curve |

### Comparison
The Haltech iC-7 dash kit you were considering lists at about $1,265 ([Haltech iC-7](https://www.haltech.com/product/ht-067010-haltech-ic-7-digital-dash-kit/)). This DIY build lands around $400–700 all-in, including tools and spares, plus your time.

---

## 9. Risks and Walk-Away Criteria

| Risk | Signal | Mitigation / fallback |
|---|---|---|
| Displays don't fit the stock dial openings or depth | Gate 0 measurements | P4 3.4" upgrade, or reduce to three displays |
| Sunlight washout | W1.6 fails | Deeper hood, anti-glare film, AMOLED options; walk away if unreadable at noon |
| LVGL needle rotation too slow at 480x480 | Choppy tach during sweep tests | Smaller needle image, partial refresh, or a drawn-line needle |
| Odometer can't be preserved in a way you accept | Gate 0 | Option C, or revert to the stock speedometer movement |
| Heat damage to LCD or prints | W7.5 | ASA mounts, sunshade, verify the panel's rated temperature |
| CAN bus disruption to the ECU | Any error frames in NSP | Listen-only displays, single transmitter, correct termination |

Stretch items: warning-lamp emulation on the displays (CEL from 0x3E4), shift light on the tach face, peak-hold, and a Wi-Fi config page for calibration tables.
