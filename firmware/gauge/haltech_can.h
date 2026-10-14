// Haltech CAN Broadcast Protocol V2.35 decoders (verify on bench, W1.5)
// Bus: 1 Mbit/s, 11-bit IDs, big-endian.
#pragma once
#include <stdint.h>

static inline uint16_t be16(const uint8_t *d) { return (uint16_t)((d[0] << 8) | d[1]); }

struct HaltechData {
  float rpm = 0, coolantC = 0, oilTempC = 0, ethanolPct = 0, fuelLiters = 0, speedKph = 0;
  uint32_t lastRpmMs = 0, lastTempMs = 0, lastFuelMs = 0, lastEthMs = 0;
};

// Call from the TWAI receive loop. Returns true if the frame was used.
static inline bool haltechDecode(uint32_t id, const uint8_t *d, uint8_t len, uint32_t nowMs, HaltechData &h) {
  if (len < 8) return false;
  switch (id) {
    case 0x360: h.rpm = be16(&d[0]); h.lastRpmMs = nowMs; return true;
    case 0x370: h.speedKph = be16(&d[0]) / 10.0f; return true;
    case 0x3E0: h.coolantC = be16(&d[0]) / 10.0f - 273.15f;
                h.oilTempC = be16(&d[6]) / 10.0f - 273.15f; h.lastTempMs = nowMs; return true;
    case 0x3E1: h.ethanolPct = be16(&d[4]) / 10.0f; h.lastEthMs = nowMs; return true;
    case 0x3E2: h.fuelLiters = be16(&d[0]) / 10.0f; h.lastFuelMs = nowMs; return true;
  }
  return false;
}
