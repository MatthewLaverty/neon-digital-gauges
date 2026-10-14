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

Open question (Phase 0 gate): what the odometer physically is (mechanical drum vs electronic) and where it sits on the speedometer face. Searches did not turn up a reliable teardown. This decides how "keep my odometer" works (see section 4.4).

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

### 4.2d Silver overlay measurements (2026-10-13) — current, but skewed

> **TEMPORARY ASSETS (2026-10-13):** the faces and overlay were made from angled phone photos and carry a perspective skew. The tach tick ring is about 5% elliptical, with uneven tick spacing (13.7–14.9°); the speedo is about 1.3%. The overlay STL shares the same distortion. Use these for layout and firmware development only. Replace them with flatbed scans (600 dpi, needles removed, steel rule in frame) before printing final parts or art.

Source: the silver overlay photographed flat on the mat with the tape beside it (237.5 px/in; the tape scale varies 235–243 px/in across the frame, so treat sizes as about ±2 %). The bare face was registered to the installed-overlay photo, giving a hole-to-face registration error under 0.1 mm for temp, fuel and speedo. The tach needed a 1 mm correction. The frame origin is the speedo hole's arc center, with +y up.

| Hole | Size (W x H) | Needle pivot (mm) | Face image (480 px) covers | px/mm at 480 |
|---|---|---|---|---|
| Temp | 49.9 x 61.1 mm | (−121.9, 2.0) | 64.2 mm circle | 7.48 |
| Fuel | 48.6 x 60.7 mm | (−67.2, 0.6) | 63.6 mm circle | 7.55 |
| Speedo | arc r 50.8 mm (≈102 mm dia), flat bottom 37 mm below origin, plus trip-odometer notch | (−0.2, −2.0) | 108 mm circle centered on pivot | 4.44 |
| Tach | circle r 40.0 mm plus a knob lobe at lower left | (108.4, −6.2) | 87.6 mm circle centered on pivot | 5.48 |

Overall overlay: about 389 x 125 mm.

Needles: all four are the same design. They are about 2.4 mm wide at the hub, tapering to 1.8 mm. Temp, fuel and tach are about 37 mm from pivot to tip; speedo is about 47.5 mm.

Display-fit consequences (arithmetic from the nominal diagonals, not datasheet active areas):
- A 2.8 in round panel (about 71 mm) is smaller than the tach hole (80 mm) and the speedo arc (102 mm).
- A 3.4 in round panel (about 86 mm) covers the tach.
- The speedo needs about 4 in (about 102 mm) to fill the stock hole. Otherwise, use a smaller window and shrink the art.
- Round screens sized to the temp and fuel holes (64 mm each) would overlap each other by about 10 mm and overlap the speedo screen by about 5 mm. Default plan: one rectangular panel behind both small gauges. A 5 in 15:9 panel (about 108 x 65 mm nominal) spans both holes.
- The overlay window mode "circle"/"intersect" in `hardware/overlay/overlay.scad` resizes a stock window to a panel's real active diameter once the panels are chosen.

Assets: `art/` (faces, needles, previews, JSON metadata) and `hardware/overlay/` (parametric overlay). The pipeline scripts are in `tools/face-extract/`.

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
- Night mode: PWM backlight dimming driven by the hub's dimmer reading. An optional "lit" version of each face can mimic the stock backlighting.
- Behavior: sweep the needle on boot (classic cluster check). Smooth with a simple low-pass filter; RPM arrives at 50 Hz, but temperatures arrive at 5 Hz and need interpolation. If no CAN data arrives for 500 ms, park the needle and show a fault indicator. Never freeze on a stale value.
- Assets go into flash as C arrays through the LVGL image converter. 480x480 RGB565 is about 450 KB per face, which fits easily in 16 MB flash.

### 4.4 Odometer decision — RESOLVED: option A (stock odometer kept)

Teardown checks still needed (W0.2): (1) the odometer driver is on the cluster board that stays; (2) the odometer keeps counting with the speedometer movement unplugged or removed. If it stops, leave the movement connected and hidden behind the display; (3) the cluster's power, ignition, and ground pins stay connected; (4) clearance between the odometer window and the bottom edge of the speedo/tach displays.

Original options, kept for reference:

| Option | How | Pros | Cons |
|---|---|---|---|
| A. Keep the stock odometer mechanism | Stock cluster PCB or odometer module stays, driven by VSS; the speedo display sits above or around it | Original mileage stays authoritative | May collide physically with a round display that covers the full speedo face |
| B. Digital odometer on the speedo display | Hub counts VSS pulses and stores mileage in FRAM; the display renders a stock-styled odometer window | Clean packaging, includes a trip meter | You must seed it with the current mileage and protect it from corruption |
| C. Hybrid | Odometer module relocated to a small window below the displays | Keeps the stock mechanism | Fabrication-heavy |

Decide after the donor-cluster teardown (W0.2). If you choose B, write down and photograph the stock mileage before swapping, and look up current odometer disclosure rules for your situation.

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
- Gate 0: choose display sizes (2.8"/2.1" vs P4 upgrade). Odometer is resolved: stock, option A. Confirm the four teardown checks in section 4.4.

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
