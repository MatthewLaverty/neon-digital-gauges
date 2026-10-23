# Knob demo: how to load it over USB

This shows the knob's selector UI on the CrowPanel 1.28" knob by itself: no hub, no CAN, no other gauges. The values are fixed sample values.

## 1. Install the software (one time, about 15 minutes)

1. Install the **Arduino IDE 2** from arduino.cc/en/software.
2. Open it and go to **File > Preferences**. In "Additional boards manager URLs" paste:
   `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
3. Go to **Tools > Board > Boards Manager**, search **esp32**, and install **"esp32 by Espressif Systems"**. Version 3.3.x is tested; the install is large.
4. Go to **Tools > Manage Libraries**, search **LovyanGFX**, and install it (1.2.33 is tested).

## 2. Open the demo

Unzip `knob_demo.zip`. Open `knob_demo/knob_demo.ino` in the Arduino IDE. Keep `knob_art.h` in the same folder.

## 3. Set the board options (Tools menu)

| Setting | Value |
|---|---|
| Board | ESP32S3 Dev Module |
| USB CDC On Boot | Enabled |
| Flash Size | 16MB (128Mb) |
| PSRAM | OPI PSRAM |
| Port | the new COM port that appears when you plug in the knob |

Leave everything else at its default.

## 4. Upload

1. Plug the knob into the PC with its USB cable.
2. Click **Upload** (the right arrow).
3. If the port doesn't appear or the upload fails with "no serial data": hold **BOOT**, tap **RESET**, release BOOT, then upload again. Press RESET once when it finishes.

## 5. Use it

| Action | Result |
|---|---|
| Turn the ring | Carousel: temp, fuel, tach, ODO/TRIP, speedo (wraps around) |
| Tap | Slides to that gauge's alternate face (coolant/oil, fuel/E85, rpm/boost, odometer/trip, speedo/data) |
| Hold 2 s on ODO/TRIP | Screen inverts for 0.5 s; the trip resets to 0.0 |
| Hold 2 s on the speedo data face | Screen inverts for 0.5 s (rotates the data order on the real gauge) |
| Hold anywhere else | Nothing |
| BOOT button | Day / night (bench only; in the car the night palette follows the park lamps) |

If turning clockwise goes the wrong way, change `REVERSE_ROTATION` to `true` near the top of the sketch and upload again. **Tools > Serial Monitor** at 115200 shows status messages; it should say "PSRAM ok".

## Later: the 2.8" tach board

See `firmware/tach-demo/README.md` (also inside `tach_demo.zip`). It uses the same Arduino IDE and esp32 package, with no extra libraries.
