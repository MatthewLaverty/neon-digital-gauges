// Dash dimmer -> screen brightness (2026-10-22). The owner taps the dimmer output of the headlamp switch (wire colour
// to be found). The hub reads it on GPIO1 through a 47k/10k divider with a 1 uF filter cap and sends brightness in
// 0x6A1 byte 1. Works for either a variable-voltage (rheostat) or a PWM dimmer: the RC filter + EMA average PWM.
// Day (park lamps off): DIM_DAY_BRIGHTNESS. Night: dimmer position mapped between the calibration points below.
// The reading is taken as a ratio of battery voltage (Haltech 0x372), so 12.4 V vs 14.4 V doesn't shift brightness.
#pragma once
#include <stdint.h>

#define DIM_PIN 1
#define DIM_DIVIDER 5.7f            // (47k + 10k) / 10k: 14.5 V -> 2.54 V at the pin
// Calibration (owner measures in the car, dimmer at each end, engine running; ratio = dimmer V / battery V):
#define DIM_RATIO_MIN 0.30f         // dimmer at its lowest setting   (placeholder until measured)
#define DIM_RATIO_MAX 0.95f         // dimmer at its brightest setting (placeholder until measured)
#define DIM_NIGHT_MIN 20            // brightness at the lowest dimmer setting (never fully black)
#define DIM_NIGHT_MAX 255
#define DIM_DAY_BRIGHTNESS 255
#define DIM_EMA 0.1f                // per-sample smoothing at ~50 Hz sampling (about 0.2 s to settle)

struct Dimmer {
  float ratio = DIM_RATIO_MAX; bool primed = false;
  // pinMv: analogReadMilliVolts(DIM_PIN); batteryV: from 0x372 (use 13.8 if not yet received); night: park_lamp.h state.
  uint8_t update(float pinMv, float batteryV, bool night) {
    if (batteryV < 8.0f) batteryV = 13.8f;
    float r = pinMv / 1000.0f * DIM_DIVIDER / batteryV;
    ratio = primed ? ratio + DIM_EMA * (r - ratio) : r; primed = true;
    if (!night) return DIM_DAY_BRIGHTNESS;
    float t = (ratio - DIM_RATIO_MIN) / (DIM_RATIO_MAX - DIM_RATIO_MIN);
    if (t < 0) t = 0; if (t > 1) t = 1;
    return (uint8_t)(DIM_NIGHT_MIN + t * (DIM_NIGHT_MAX - DIM_NIGHT_MIN) + 0.5f);
  }
};
