// Park-lamp sense for night mode (2026-10-22). The hub reads the car's park-lamp feed through a PC817 optocoupler on
// GPIO2 and sets 0x6A1 byte 2 bit 0 (night palette) for every screen, including the knob.
// Wiring (docs/bench/POC-WIRING.md): park-lamp feed -> 2.2 kohm -> PC817 pin 1 (anode); pin 2 (cathode) -> chassis
// ground; 1N4148 across pins 1-2, cathode to pin 1 (reverse protection). Pin 4 (collector) -> GPIO2 with a 10 kohm
// pull-up to 3.3 V; pin 3 (emitter) -> hub GND. Lamps on = LED lit = GPIO2 LOW.
#pragma once
#include <stdint.h>

#ifndef PARK_LAMP_PIN
#define PARK_LAMP_PIN 2   // same pin as the bench headlamp switch (switch to GND = lamps on)
#endif
#define PARK_LAMP_DEBOUNCE_MS 300   // a lamp-switch change must hold this long; ignores flicker and cranking dips

struct ParkLamp {
  bool night = false;               // debounced state, as sent in 0x6A1 byte 2 bit 0
  bool raw = false; uint32_t since = 0;
  // Call every loop with the pin level (true = LOW = lamps on) and millis(). Returns true when `night` changes.
  bool update(bool lampsOnRaw, uint32_t nowMs) {
    if (lampsOnRaw != raw) { raw = lampsOnRaw; since = nowMs; }
    if (raw != night && nowMs - since >= PARK_LAMP_DEBOUNCE_MS) { night = raw; return true; }
    return false;
  }
};
// Use: pinMode(PARK_LAMP_PIN, INPUT);  (external 10 kohm pull-up)
//      if (lamp.update(digitalRead(PARK_LAMP_PIN) == LOW, millis())) send0x6A1Now();
