# Tach demo: how to load it over USB

This runs on the Waveshare ESP32-S3-LCD-2.8C by itself: no hub, no CAN. It shows the real tach face with a moving needle and a frames-per-second (FPS) counter so you can see the refresh rate.

## 1. Software

Use the same setup as the knob: Arduino IDE 2 with "esp32 by Espressif Systems" 3.3.x installed. Install one library: **Sketch > Include Library > Manage Libraries**, search **AnimatedGIF** (by Larry Bank), and click Install. It plays the startup animation. Waveshare's screen driver files are already inside the sketch folder.

## 2. Open the demo

Unzip `tach_demo.zip` and open `tach_demo/tach_demo.ino`. Keep all the other files in that folder.

## 3. Board options (Tools menu)

| Setting | Value |
|---|---|
| Board | ESP32S3 Dev Module |
| USB CDC On Boot | Enabled |
| Flash Size | 16MB (128Mb) |
| PSRAM | OPI PSRAM |
| Partition Scheme | **Custom** (uses `partitions.csv` in the sketch folder; needed for the 5.9 MB startup animation) |
| Port | the new port that appears when you plug the board in |

Leave everything else at its default.

## 4. Upload

Plug the board in over USB-C and click **Upload**. The upload is about 6.5 MB, so it takes a minute or two. If the port doesn't appear or the upload fails: hold **BOOT**, tap **RESET**, release BOOT, then upload again. Press RESET once when it finishes.

## Startup animation

At power-on (or RESET), the screen fades in to the startup GIF, centred at its native 480 x 360 (the round screen clips the corners; it is not scaled). It plays once. The GIF is cut before the white "neon" card, so it ends on the white car "Hi." frame at about 6.3 s. It then fades quickly to black (0.3 s) and the tach face fades up over 1 s. It plays only at power-on. To skip it, set `#define STARTUP_GIF 0` at the top of `tach_demo.ino`; the fade times are the lines just below it. The uncut original is `startup_original.gif` in the repo (not in this zip).

## 5. Use it (BOOT button)

| Press | Result |
|---|---|
| Single click | Day / night face |
| Double click | Mode: DRIVE (simulated idle, blip and pulls through the gears), then SWEEP (continuous 0-8000-0), then HOLD (needle stays still) |
| Hold about 1 s | Sweep speed: 2 s, then 1 s, 0.5 s and 0.25 s per 0-8000 pass |

The **FPS number** is at the bottom of the screen. **Tools > Serial Monitor** at 115200 also prints the FPS, rpm and mode once a second.

## Speed settings (top of `tach_demo.ino`)

| Setting | Default | What it does |
|---|---|---|
| `FPS_LOCK` | 30 | Frame-rate lock: 30, 60, or 0 for unlocked (as fast as it can draw) |
| `PCLK_HZ` | 16700000 | The screen's pixel clock. 16.7 MHz is about 60 Hz refresh; Waveshare's 30 MHz is about 108 Hz and leaves little time for drawing |
| `TIMING_PRINTS` | 1 | Prints the time each step takes once a second |

The Serial Monitor (115200) prints two lines a second:
- `fps 30  panel Hz 60 ...`: the frames drawn per second, and the screen's measured refresh rate.
- `per frame (ms): pace 18.0  restore 0.6  needle 2.1  wait-for-panel 9.8`: where the time goes. "pace" is the idle time the 30 fps lock adds. If "needle" or "restore" is large, the drawing is the limit. If "wait-for-panel" is large, the screen's refresh is.

Things to try: set `FPS_LOCK` to 60 or 0 to see the top speed. If the picture jitters or shifts, lower `PCLK_HZ` (for example 14000000, about 50 Hz).

## Brightness

The backlight is set by `BACKLIGHT_PCT` near the top of `tach_demo.ino`, from 0 to 100. It defaults to 100 (fully on). Lower it and upload again to dim the screen.

## If something's wrong

- **The board's own buzzer sounds:** fixed in this version (2026-10-25). The first version didn't switch off the onboard buzzer, so it could start after the board lost power completely. Upload this version.

- **The screen stays black:** first run Waveshare's own demo to prove the board works. Download "ESP32-S3-LCD-2.8C Demo" from the **Resources** section of the Waveshare wiki page "ESP32-S3-LCD-2.8C" and follow the settings listed there; Waveshare uses its own board package. If their demo works and this one doesn't, note what the Serial Monitor says.
- **"PSRAM MISSING" in the Serial Monitor:** set PSRAM to OPI PSRAM.
- **"Sketch too big" when compiling:** set Partition Scheme to Custom, and make sure `partitions.csv` is in the sketch folder.
- **"AnimatedGIF.h: No such file":** install the AnimatedGIF library (step 1).
- **The picture shifts or jitters sideways:** this is a known effect on this style of screen. The sketch already uses Waveshare's anti-drift setting (bounce buffer); note the FPS and mode when it happens.

This sketch compiles but hasn't been run on the real board yet.
