// Error alerts, low-fuel lamp, check-engine lamp and buzzer -- owner settings (spec 2026-10-18).
// Edit the numbers here. Set a rule's `enabled` to false to turn it off. Units are the ones on the gauges.
#pragma once
#include <stdint.h>

enum AlertChannel : uint8_t { CH_RPM, CH_COOLANT_F, CH_OILTEMP_F, CH_VOLTS, CH_AFR, CH_OILP_PSI };
enum AlertCmp     : uint8_t { ABOVE, BELOW, OUTSIDE };            // OUTSIDE = alert when value < lo OR value > hi
enum AlertGauge   : uint8_t { G_TEMP, G_FUEL, G_SPEEDO, G_TACH, G_COUNT };
enum AlertFace    : uint8_t { FACE_ANY, FACE_TEMP_COOLANT, FACE_TEMP_OIL, FACE_SPEEDO_DATA };

struct AlertRule {
  const char  *name;
  bool         enabled;
  AlertChannel ch;
  AlertCmp     cmp;
  float        lo, hi;           // ABOVE uses lo, BELOW uses lo, OUTSIDE uses lo and hi
  float        minRpm;           // armed only when RPM >= minRpm (0 = always)
  uint16_t     runningMs;        // armed only after the engine has run (RPM > ENGINE_RUNNING_RPM) this long (0 = always)
  bool         skipCranking;     // ignored while cranking (0 < RPM <= ENGINE_RUNNING_RPM) and CRANK_HOLDOFF_MS after
  bool         skipDecelCut;     // ignored while the Haltech reports Decel Cut Active (0x3E4 byte 1 bit 4)
  uint16_t     debounceMs;       // condition must hold this long before the gauge flashes (0 = instant)
  AlertGauge   gauge;            // gauge that flashes
  AlertFace    face;             // face that gauge is switched to (FACE_ANY = no switch)
  uint8_t      priority;         // lower wins when two rules want the same gauge on different faces
};

// Owner thresholds. The last four columns after `debounce` are routing; the gates (minRpm..decel) marked * are
// suggested additions, not part of the owner spec -- set them to 0/false to get the literal spec.
static const AlertRule ALERT_RULES[] = {
//  name            en    channel       cmp      lo      hi     minRpm  runMs* crank* decel* debounce* gauge     face               prio
  {"RPM",           true, CH_RPM,       ABOVE,   7999,   0,     0,      0,     false, false, 0,        G_TACH,   FACE_ANY,          0},
  {"Coolant temp",  true, CH_COOLANT_F, ABOVE,   250,    0,     0,      0,     false, false, 1000,     G_TEMP,   FACE_TEMP_COOLANT, 1},
  {"Oil temp",      true, CH_OILTEMP_F, ABOVE,   300,    0,     0,      0,     false, false, 1000,     G_TEMP,   FACE_TEMP_OIL,     2},
  {"Voltage",       true, CH_VOLTS,     OUTSIDE, 11.0,   16.0,  0,      0,     true,  false, 1000,     G_SPEEDO, FACE_SPEEDO_DATA,  3},
  {"Air/fuel",      true, CH_AFR,       ABOVE,   14.0,   0,     3000,   0,     false, true,  300,      G_SPEEDO, FACE_SPEEDO_DATA,  4},
  {"Oil pressure",  true, CH_OILP_PSI,  BELOW,   15.0,   0,     0,      3000,  false, false, 500,      G_SPEEDO, FACE_SPEEDO_DATA,  5},
};
static const uint8_t ALERT_RULE_COUNT = sizeof(ALERT_RULES) / sizeof(ALERT_RULES[0]);

// ---- Flash behaviour (owner: 3 flashes/s for 10 s, repeat while the error persists, stop at key-off or when clear)
#define ALERT_FLASH_HZ            3        // flashes per second (red half of each period)
#define ALERT_BURST_MS            10000    // one burst; re-checked at the end of each burst
#define ALERT_FINISH_BURST        true     // true: a burst always runs its full 10 s (a 0.2 s spike is still seen)
                                           // false: flashing stops the moment the value is back in range
#define ALERT_RESTORE_FACE        true     // after the alert ends, put the gauge back on the face it was showing
#define ALERT_LOCK_KEYPAD         true     // ignore keypad/knob face changes on a gauge while it is flashing
#define ALERT_DATA_FACE_TOP       true     // speedo data face: move the offending value to the top slot
#define ALERT_FLASH_R 255                  // background colour while "on" (day and night faces alike)
#define ALERT_FLASH_G 0
#define ALERT_FLASH_B 0
#define ENGINE_RUNNING_RPM        500
#define CRANK_HOLDOFF_MS          2000
#define CHANNEL_STALE_MS          1000     // a channel with no fresh frame this long cannot raise an alert

// ---- Low fuel lamp (final spec 2026-10-17): on after 10 s continuously below 1.6 gal, off above 1.8 gal at once
#define LOW_FUEL_ON_RAW           61       // 0x3E2 raw (0.1 L): on when raw < 61 (6.06 L = 1.6 gal)
#define LOW_FUEL_OFF_RAW          68       // off when raw > 68 (6.81 L = 1.8 gal)
#define LOW_FUEL_DELAY_MS         10000

// ---- Buzzer: Star TMX-12S magnetic transducer, low-side NPN on BUZZER_PIN (see docs/bench/POC-WIRING.md)
#define BUZZER_PIN                6
#define BUZZER_SELF_DRIVE         false    // true if bench test shows it beeps on plain DC (then drive on/off only)
#define BUZZER_FREQ_HZ            1000     // drive tone; sweep 800-3000 Hz on the bench and keep the loudest
#define BUZZER_VOLUME_PCT         100      // 100 = maximum (50 % PWM duty); lower = quieter
#define BUZZ_ON_ALERT             true     // buzzes with the red flash pattern
#define BUZZ_ON_LOW_FUEL          true     // chime when the low-fuel lamp comes on
#define BUZZ_ON_CEL               true     // single buzz when the check-engine flag goes on
#define CEL_BUZZ_MS               1000
// Low-fuel chime: two notes (Hz, ms), with a gap between them
#define CHIME_F1 1200
#define CHIME_T1 180
#define CHIME_GAP 70
#define CHIME_F2 900
#define CHIME_T2 380
