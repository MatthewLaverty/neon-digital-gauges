#include "../dimmer.h"
#include <cstdio>
static float mv(float volts) { return volts / DIM_DIVIDER * 1000.0f; }
int main() { int f = 0; auto ck = [&](bool c, const char *m) { if (!c) { printf("FAIL %s\n", m); f++; } };
  { Dimmer d; ck(d.update(mv(4), 13.8f, false) == 255, "day ignores dimmer"); }
  { Dimmer d; ck(d.update(mv(0.95f * 13.8f), 13.8f, true) == 255, "night max"); }
  { Dimmer d; ck(d.update(mv(0.30f * 13.8f), 13.8f, true) == 20, "night min"); }
  { Dimmer d; ck(d.update(mv(0.10f * 13.8f), 13.8f, true) == 20, "below min clamps"); }
  { Dimmer d; uint8_t a = d.update(mv(0.6f * 12.4f), 12.4f, true); Dimmer e; uint8_t b = e.update(mv(0.6f * 14.4f), 14.4f, true);
    ck(a == b, "battery voltage compensated"); }
  { Dimmer d; d.update(mv(0.95f * 13.8f), 13.8f, true); uint8_t s = d.update(mv(0.30f * 13.8f), 13.8f, true);
    ck(s > 200, "step is smoothed"); for (int i = 0; i < 60; i++) s = d.update(mv(0.30f * 13.8f), 13.8f, true); ck(s <= 22, "settles"); }
  { Dimmer d; ck(d.update(mv(0.95f * 13.8f), 0, true) == 255, "no battery frame -> 13.8 V assumed"); }
  printf(f ? "FAILED\n" : "dimmer: 8 checks pass\n"); return f; }
