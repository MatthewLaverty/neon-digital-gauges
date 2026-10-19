// Alert engine for the hub (header-only, no Arduino dependencies so it can be unit-tested on a PC).
// Call alertsUpdate() every loop (>= 50 Hz) with fresh inputs; it returns per-gauge flash state, the face each
// alerting gauge must show, lamp states and what the buzzer should do right now.
#pragma once
#include "alerts_config.h"

struct AlertInputs {                       // already converted to gauge units by the CAN decoder
  float rpm, coolantF, oilTempF, volts, afr, oilPsi;
  uint32_t lastRpmMs, lastTempMs, lastVoltsMs, lastAfrMs, lastOilPMs;
  bool decelCut;                           // 0x3E4 byte 1 bit 4
  bool cel;                                // 0x3E4 byte 7 bit 7
  uint16_t fuelRaw; uint32_t lastFuelMs;   // 0x3E2 bytes 0-1, 0.1 L
};
struct AlertOutputs {
  bool flashing[G_COUNT];                  // gauge is in an alert burst
  bool redOn;                              // shared flash phase: paint the background red now
  AlertFace face[G_COUNT];                 // face the hub must force (FACE_ANY = leave alone)
  int8_t topRule[G_COUNT];                 // rule index that owns each gauge, -1 = none
  bool lowFuelLamp, celLamp;
  uint32_t buzzHz; uint8_t buzzDutyPct;    // 0 duty = silent
  uint8_t ruleBits;                        // bit i = rule i currently tripped (diagnostics, 0x6A3 byte 3)
};

struct AlertState {
  uint32_t condSince[16] = {0}; bool cond[16] = {false};
  uint32_t burstStart[G_COUNT] = {0}; bool inBurst[G_COUNT] = {false}; int8_t owner[G_COUNT] = {-1,-1,-1,-1};
  uint32_t flashEpoch = 0; bool anyFlashPrev = false;
  uint32_t runningSince = 0; bool running = false; uint32_t crankSeenMs = 0; bool crankSeen = false;
  bool lowFuel = false; uint32_t belowSince = 0; bool below = false;
  bool celPrev = false; uint32_t celBuzzUntil = 0; bool celBuzz = false;
  bool chimeActive = false; uint32_t chimeStart = 0;
};

static inline float alertValue(const AlertInputs &in, AlertChannel c, uint32_t &last) {
  switch (c) {
    case CH_RPM:       last = in.lastRpmMs;   return in.rpm;
    case CH_COOLANT_F: last = in.lastTempMs;  return in.coolantF;
    case CH_OILTEMP_F: last = in.lastTempMs;  return in.oilTempF;
    case CH_VOLTS:     last = in.lastVoltsMs; return in.volts;
    case CH_AFR:       last = in.lastAfrMs;   return in.afr;
    default:           last = in.lastOilPMs;  return in.oilPsi;
  }
}

static inline void alertsUpdate(uint32_t now, const AlertInputs &in, AlertState &s, AlertOutputs &o) {
  // engine state for the gates
  bool fresh = (now - in.lastRpmMs) <= CHANNEL_STALE_MS;
  bool run = fresh && in.rpm > ENGINE_RUNNING_RPM;
  if (run && !s.running) s.runningSince = now;
  s.running = run;
  bool cranking = fresh && in.rpm > 0 && in.rpm <= ENGINE_RUNNING_RPM;
  if (cranking) { s.crankSeen = true; s.crankSeenMs = now; }
  bool inCrankHoldoff = cranking || (s.crankSeen && now - s.crankSeenMs < CRANK_HOLDOFF_MS);

  // 1. evaluate rules
  o.ruleBits = 0;
  bool tripped[16];
  for (uint8_t i = 0; i < ALERT_RULE_COUNT; i++) {
    const AlertRule &r = ALERT_RULES[i];
    uint32_t last; float v = alertValue(in, r.ch, last);
    bool c = r.enabled && (now - last) <= CHANNEL_STALE_MS;
    if (c) c = (r.cmp == ABOVE) ? v > r.lo : (r.cmp == BELOW) ? v < r.lo : (v < r.lo || v > r.hi);
    if (c && r.minRpm > 0) c = fresh && in.rpm >= r.minRpm;
    if (c && r.runningMs > 0) c = s.running && now - s.runningSince >= r.runningMs;
    if (c && r.skipCranking) c = !inCrankHoldoff;
    if (c && r.skipDecelCut) c = !in.decelCut;
    if (c && !s.cond[i]) s.condSince[i] = now;
    s.cond[i] = c;
    tripped[i] = c && now - s.condSince[i] >= r.debounceMs;
    if (tripped[i]) o.ruleBits |= (1u << i);
  }

  // 2. per gauge bursts
  bool anyFlash = false;
  for (uint8_t g = 0; g < G_COUNT; g++) {
    int8_t want = -1;
    for (uint8_t i = 0; i < ALERT_RULE_COUNT; i++)
      if (tripped[i] && ALERT_RULES[i].gauge == g && (want < 0 || ALERT_RULES[i].priority < ALERT_RULES[want].priority)) want = i;
    if (!s.inBurst[g]) {
      if (want >= 0) { s.inBurst[g] = true; s.burstStart[g] = now; s.owner[g] = want; }
    } else {
      if (now - s.burstStart[g] >= ALERT_BURST_MS) {
        if (want >= 0) { s.burstStart[g] = now; s.owner[g] = want; }   // still in error: repeat
        else { s.inBurst[g] = false; s.owner[g] = -1; }
      } else if (want < 0 && !ALERT_FINISH_BURST) { s.inBurst[g] = false; s.owner[g] = -1; }
      else if (want >= 0 && ALERT_RULES[want].priority < ALERT_RULES[s.owner[g]].priority) s.owner[g] = want;
    }
    o.flashing[g] = s.inBurst[g];
    o.topRule[g] = s.owner[g];
    o.face[g] = s.inBurst[g] ? ALERT_RULES[s.owner[g]].face : FACE_ANY;
    anyFlash |= s.inBurst[g];
  }
  if (anyFlash && !s.anyFlashPrev) s.flashEpoch = now;      // all gauges share one phase
  s.anyFlashPrev = anyFlash;
  // exact 3 Hz: half-periods counted in integer ms * 2 * Hz / 1000 (no 333 ms rounding drift)
  o.redOn = anyFlash && ((((uint64_t)(now - s.flashEpoch)) * 2u * ALERT_FLASH_HZ / 1000u) % 2u) == 0;

  // 3. low fuel lamp with delay + hysteresis; starts off at power-up
  bool fuelFresh = (now - in.lastFuelMs) <= CHANNEL_STALE_MS;
  if (fuelFresh && in.fuelRaw < LOW_FUEL_ON_RAW) { if (!s.below) { s.below = true; s.belowSince = now; } }
  else s.below = false;
  bool wasLow = s.lowFuel;
  if (!s.lowFuel && s.below && now - s.belowSince >= LOW_FUEL_DELAY_MS) s.lowFuel = true;
  if (s.lowFuel && fuelFresh && in.fuelRaw > LOW_FUEL_OFF_RAW) s.lowFuel = false;
  if (s.lowFuel && !wasLow && BUZZ_ON_LOW_FUEL) { s.chimeActive = true; s.chimeStart = now; }
  o.lowFuelLamp = s.lowFuel;

  // 4. check engine
  o.celLamp = in.cel;
  if (in.cel && !s.celPrev && BUZZ_ON_CEL) { s.celBuzz = true; s.celBuzzUntil = now + CEL_BUZZ_MS; }
  s.celPrev = in.cel;
  if (s.celBuzz && (int32_t)(now - s.celBuzzUntil) >= 0) s.celBuzz = false;

  // 5. buzzer arbitration: alert pattern > check-engine buzz > chime
  uint8_t duty = (uint8_t)(BUZZER_SELF_DRIVE ? 100 : BUZZER_VOLUME_PCT / 2);
  o.buzzHz = BUZZER_FREQ_HZ; o.buzzDutyPct = 0;
  if (BUZZ_ON_ALERT && anyFlash) { if (o.redOn) o.buzzDutyPct = duty; }
  else if (s.celBuzz) o.buzzDutyPct = duty;
  else if (s.chimeActive) {
    uint32_t t = now - s.chimeStart;
    if (t < CHIME_T1) { o.buzzHz = CHIME_F1; o.buzzDutyPct = duty; }
    else if (t < CHIME_T1 + CHIME_GAP) {}
    else if (t < CHIME_T1 + CHIME_GAP + CHIME_T2) { o.buzzHz = CHIME_F2; o.buzzDutyPct = duty; }
    else s.chimeActive = false;
  }
}
// 0x6A3 (proposed): byte0 flashing gauges (bit0 temp, bit1 fuel, bit2 speedo, bit3 tach), byte1 bit0 red phase,
// byte2 lamps (bit0 low fuel, bit1 check engine), byte3 rule bits, byte4 sequence. Send at 10 Hz and on every change.
static inline void alertsFrame(const AlertOutputs &o, uint8_t seq, uint8_t d[8]) {
  d[0] = 0; for (uint8_t g = 0; g < G_COUNT; g++) if (o.flashing[g]) d[0] |= 1u << g;
  d[1] = o.redOn; d[2] = (o.lowFuelLamp ? 1 : 0) | (o.celLamp ? 2 : 0); d[3] = o.ruleBits; d[4] = seq; d[5] = d[6] = d[7] = 0;
}
