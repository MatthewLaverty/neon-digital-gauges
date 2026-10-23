# Cluster behaviour spec (owner, 2026-10-22)

Settings named in `code` live in `config/cluster-config.md`. Items marked ASSUMED are my reading of the owner's spec. Confirm or correct them.

## 1. Selection cue on the cluster screens
- **When:** the knob lands on a stop. The matching cluster screen draws a border in redline red (the active palette's redline tick colour: day 232,77,61, night 240,5,50). The border pulses between 8 px and 4 px wide (`cue_width_max_px`, `cue_width_min_px`, period `cue_pulse_ms`).
- **Where:**
  - Round gauges: just inside the visible aperture of the overlay, so the full ring is seen. ASSUMED: the border follows the overlay opening, not the panel edge.
  - Temp and fuel share the 5" board; each gets its own ring.
  - ODO/TRIP stop: a rounded rectangle around the readout and its ODO/TRIP legend on the tach screen (`cue_odo_corner_radius_px`, `cue_odo_padding_px`).
- **Stops:**
  - No action for 5 s after a selection (`cue_idle_timeout_ms`).
  - 2 s after a tap or hold commits (`cue_after_action_ms`).
  - Turning to another stop moves the cue and restarts its 5 s.
- **Resume:**
  - The knob is used again 10 s or less after the cue ended (`cue_resume_window_ms`): selection starts on the last gauge.
  - Otherwise it starts at the first stop in `select_order`.
  - ASSUMED: the first turn or press after a timeout only shows the cue on the starting stop and doesn't advance.
- **Order:** `select_order`. The default is left to right across the cluster: temp, fuel, speedo, tach, ODO/TRIP. This changes the knob demo's order (temp, fuel, tach, ODO/TRIP, speedo).
- **Knob screen:** the cue is not mirrored to the knob screen.
- **Alerts:** a gauge that is flashing an alert keeps its flash. ASSUMED: the cue is drawn over the flash, and face changes stay locked (`alert_lock_controls`).
- **CAN:** the hub drives the cue. 0x6A1 byte 4 = cued stop (0xFF = none), byte 5 = cue phase sequence.

## 2. State persists across restarts
- **What is saved:** the last-used configuration, saved in the hub's flash (NVS):
  - each gauge's face (coolant/oil, fuel/E85, rpm/boost, speedo/data)
  - the speedo data order
  - ODO vs TRIP on the readout
  - the trip offset
  - the last knob stop
- **When:** 2 s after the last change, and again during the shutdown hold. Rare writes, so flash wear isn't a concern.
- **Night mode:** not saved; it always comes from the park-lamp input.
- **Alerts:** a face forced by an alert is not saved. The pre-alert face is.

## 3. Settings file
`config/cluster-config.md` holds every user-adjustable setting: alerts, order, startup animation, timings, thresholds and brightness. It is plain Markdown tables. The hub reads it at boot and falls back to built-in defaults for anything missing.

## 4. Selector knob
- **Key-on:** mirrors the startup art (`knob_startup_art`).
- **Sleep:**
  - Screen off if there's no interaction within 15 s of key-on (`knob_sleep_no_use_ms`).
  - Screen off 15 s after the last interaction (`knob_sleep_after_use_ms`).
- **Wake:** any turn, tap or hold. ASSUMED: the waking input only wakes the knob and starts the cue; it doesn't also act.
- **Saving power:** asleep, the backlight is off. The knob keeps listening on CAN and to the encoder.

## 5. Brightness
- **Per-screen peak:** `peak_brightness_tach`, `peak_brightness_speedo`, `peak_brightness_5in` and `knob_peak_brightness` let the screens be matched. Sent in 0x6A4.
- **Night:** the dash dimmer sets it (`firmware/hub/dimmer.h`); each screen scales the dimmer value by its own peak.
- **Day:** `day_brightness`.
- **Colour balance:** per-screen colour balance is deferred (owner).
- **5" board caveat:** the Waveshare 5" backlight is on/off only. Without the R21 mod, or a board with PWM backlight, the 5" can't follow the dimmer or its peak.

## 6. Startup art (assets in progress)
On the tach screen, about 2 s total (`startup_art_ms`):
1. Fade up from black to the first-gen Neon logo.
2. The second-gen logo drops onto it and replaces it.
3. The third-gen logo drops on and replaces it.
4. Flare to a vignetted white.
5. Collapse back to the ACR logo over black.

Then fade to black and up to the gauges within about 2 s more (`startup_to_gauges_ms`). The knob mirrors the sequence. ASSUMED: the speedo and 5" screens stay black during the art, then fade up to the gauges together with the tach.

- **Sync:** the hub sends a start trigger (0x6A1 byte 2 bit 2) once it is up, so the tach and knob start together. A screen that hears nothing within 1.5 s of power-up starts on its own.
- **Skip:** `startup_art = false` goes straight to the gauges. ASSUMED: if the key is cycled during the shutdown fade, the screens fade straight back up without the art.

## 7. Shutdown
- **Fade:** no art; every screen fades to black over 1 s (`shutdown_fade_ms`).
- **Power:** this needs power management. If the cluster runs from an ignition-switched feed, power disappears the moment the key turns, before any fade or save.
- **Fix (proposed, see `docs/bench/POC-WIRING.md`, "Power latch"):**
  - Feed the cluster from constant battery through a relay.
  - The relay is held on by either the ignition feed or a hub "hold" pin.
  - The hub senses ignition on GPIO7 through an optocoupler.
- **Key-off sequence:**
  1. The hub sees key-off (100 ms debounce) and sends shutdown (0x6A1 byte 2 bit 1).
  2. The screens fade.
  3. The hub saves state and waits `shutdown_hold_ms` (1.5 s).
  4. The hub drops the hold pin.
- **Draw:** zero when off. It also keeps the screens from browning out if the ignition feed sags.
- **Software fallback:** if the latch isn't built, the hub can treat 0.5 s of CAN silence from the Haltech as key-off. But by then the screens may already have lost power, so the fade isn't guaranteed.
