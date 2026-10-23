# Neon cluster settings

All user-adjustable settings live in this one file (owner spec 2026-10-22). Edit the **Value** column only.

## How it gets into the car
- The hub reads this file at boot from its flash and sends the display settings to the screens over CAN (0x6A4).
- To change a setting:
  1. Edit this file.
  2. Copy it to the hub sketch's `data/` folder as `cluster-config.md`.
  3. In Arduino IDE 2, press Ctrl+Shift+P and run "Upload LittleFS to Pico/ESP8266/ESP32" (one-time install: the [arduino-littlefs-upload plugin](https://github.com/earlephilhower/arduino-littlefs-upload)). Close the Serial Monitor first.
- You don't need to re-upload the sketch to change a setting.
- **Errors:** a missing or unreadable value falls back to the built-in default. The hub lists every key it ignored on the Serial Monitor at boot.
- **Format:** every table row whose first cell is a known key is read. Everything else in the file is notes.
- **Status:** PROPOSED. The hub firmware that reads this file is not written yet. Until it is, the alert values below are mirrored in `firmware/hub/alerts_config.h`.

Units: ms = milliseconds, px = pixels on a 480 px face (scaled to each panel), brightness 0-255.

## Selection cue (knob -> cluster screens)

| Key | Value | Notes |
|---|---|---|
| select_order | temp, fuel, speedo, tach, odo | Knob stop order. Default is left to right across the cluster. odo = the ODO/TRIP readout on the tach screen. If the tach moves to the center, change this too |
| cue_width_max_px | 8 | Pulsing border, widest |
| cue_width_min_px | 4 | Pulsing border, narrowest |
| cue_pulse_ms | 1000 | One 8 -> 4 -> 8 cycle (owner: configurable, 1 s default) |
| cue_color | redline | redline = the active palette's redline tick colour (day 232,77,61; night 240,5,50). Or an R,G,B triple |
| cue_idle_timeout_ms | 5000 | No action after a selection: cue stops |
| cue_after_action_ms | 2000 | After a tap or hold commits: cue stops this long after |
| cue_resume_window_ms | 10000 | Knob use within this long of the cue ending resumes on that gauge; later starts at the first stop in select_order |
| cue_odo_corner_radius_px | 8 | Rounded rectangle around the ODO/TRIP readout and its legend |
| cue_odo_padding_px | 6 | Gap between the readout and the rectangle |

## Selector knob

| Key | Value | Notes |
|---|---|---|
| knob_startup_art | true | Knob mirrors the startup art at key-on |
| knob_sleep_no_use_ms | 15000 | After key-on: screen off if nothing is touched in this long |
| knob_sleep_after_use_ms | 15000 | Screen off this long after the last turn, tap or hold |
| knob_peak_brightness | 255 | |

## Screen brightness (per physical screen)
Night brightness follows the dash dimmer (`firmware/hub/dimmer.h`). Each screen scales it by its peak, so the screens can be matched. Colour balance per screen comes later (owner, 2026-10-22).

| Key | Value | Notes |
|---|---|---|
| peak_brightness_tach | 255 | |
| peak_brightness_speedo | 255 | |
| peak_brightness_5in | 255 | Temp + fuel board. The Waveshare 5" backlight is on/off only unless R21 is modded |
| day_brightness | 255 | Park lamps off |
| night_brightness_min | 20 | Dimmer at its lowest |
| dimmer_ratio_min | 0.30 | Measure: dimmer V / battery V at the lowest setting (placeholder) |
| dimmer_ratio_max | 0.95 | Measure: dimmer V / battery V at the highest setting (placeholder) |

## Startup and shutdown

| Key | Value | Notes |
|---|---|---|
| startup_art | true | false = straight to gauges |
| center_gauge | speedo | Which gauge sits in the center large screen: speedo or tach |
| startup_art_screen | center | Screen that plays the startup art. center = whichever gauge center_gauge names |
| startup_art_ms | 2000 | Logo sequence on the startup_art_screen (art in progress) |
| startup_to_gauges_ms | 2000 | Fade to black, then fade up to the gauges |
| shutdown_fade_ms | 1000 | All screens fade to black at key-off |
| shutdown_hold_ms | 1500 | Hub keeps power on this long after key-off (fade + state save), then releases the power latch |

## Alerts
Rule columns: enabled, channel, compare, low, high, min_rpm, running_ms, skip_cranking, skip_decel_cut, debounce_ms, gauge, face, priority.

| Key | Value | Notes |
|---|---|---|
| alert_rpm | true, rpm, above, 7999, 0, 0, 0, false, false, 0, tach, any, 0 | |
| alert_coolant | true, coolant_f, above, 250, 0, 0, 0, false, false, 1000, temp, coolant, 1 | |
| alert_oil_temp | true, oil_temp_f, above, 300, 0, 0, 0, false, false, 1000, temp, oil, 2 | |
| alert_voltage | true, volts, outside, 11.0, 16.0, 0, 0, true, false, 1000, speedo, data, 3 | |
| alert_afr | true, afr, above, 14.0, 0, 3000, 0, false, true, 300, speedo, data, 4 | |
| alert_oil_pressure | true, oil_psi, below, 15.0, 0, 0, 3000, false, false, 500, speedo, data, 5 | |
| alert_flash_hz | 3 | |
| alert_burst_ms | 10000 | |
| alert_finish_burst | true | |
| alert_restore_face | true | |
| alert_lock_controls | true | No face changes on a flashing gauge |
| alert_data_face_top | true | |
| alert_outline_px | 3 | |
| engine_running_rpm | 500 | |
| crank_holdoff_ms | 2000 | |
| low_fuel_on_gal | 1.6 | |
| low_fuel_off_gal | 1.8 | |
| low_fuel_delay_ms | 10000 | |

## Fuel

| Key | Value | Notes |
|---|---|---|
| tank_capacity_gal | 12.5 | Plan default (47.3 L); change for a future fuel cell |
