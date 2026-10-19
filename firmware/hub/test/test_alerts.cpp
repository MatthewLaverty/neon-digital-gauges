// Host test: g++ -std=c++17 -I.. test_alerts.cpp -o t && ./t
#include <cstdio>
#include <cassert>
#include "../alerts.h"
static int fails = 0;
#define CHECK(c, msg) do { if (!(c)) { printf("FAIL: %s\n", msg); fails++; } else printf("ok   %s\n", msg); } while (0)
static AlertInputs base(uint32_t t) { AlertInputs i{}; i.rpm = 2500; i.coolantF = 190; i.oilTempF = 220; i.volts = 14.1f; i.afr = 12.5f; i.oilPsi = 45;
  i.lastRpmMs = i.lastTempMs = i.lastVoltsMs = i.lastAfrMs = i.lastOilPMs = i.lastFuelMs = t; i.fuelRaw = 300; return i; }
int main() {
  { AlertState s; AlertOutputs o; uint32_t t = 0; int reds = 0, edges = 0; bool prev = false;
    for (; t < 5000; t += 10) { auto i = base(t); alertsUpdate(t, i, s, o); }
    for (; t < 5200; t += 10) { auto i = base(t); i.rpm = 8200; alertsUpdate(t, i, s, o); if (o.redOn && !prev) edges++; prev = o.redOn; }
    CHECK(o.flashing[G_TACH] && o.face[G_TACH] == FACE_ANY, "RPM 8200 flashes tach, no face switch");
    for (; t < 15000; t += 10) { auto i = base(t); alertsUpdate(t, i, s, o); if (o.redOn && !prev) edges++; prev = o.redOn; if (o.redOn) reds++; }
    CHECK(o.flashing[G_TACH], "0.2 s spike still flashing at 9.8 s (finish-burst)");
    for (; t < 15300; t += 10) { auto i = base(t); alertsUpdate(t, i, s, o); }
    CHECK(!o.flashing[G_TACH], "stops after the 10 s burst once clear");
    CHECK(edges == 30, "30 red flashes in 10 s (3 Hz)"); printf("     edges=%d\n", edges); }
  { AlertState s; AlertOutputs o; uint32_t t = 0;
    for (; t < 25000; t += 10) { auto i = base(t); i.coolantF = 255; alertsUpdate(t, i, s, o); }
    CHECK(o.flashing[G_TEMP] && o.face[G_TEMP] == FACE_TEMP_COOLANT, "coolant 255 F persists: repeats past 10 s, coolant face");
    for (; t < 26000; t += 10) { auto i = base(t); i.coolantF = 255; i.oilTempF = 310; alertsUpdate(t, i, s, o); }
    CHECK(o.face[G_TEMP] == FACE_TEMP_COOLANT, "coolant outranks oil temp on the shared gauge"); }
  { AlertState s; AlertOutputs o; uint32_t t = 0;
    for (; t < 2000; t += 10) { auto i = base(t); i.rpm = 0; i.oilPsi = 0; alertsUpdate(t, i, s, o); }
    CHECK(!o.flashing[G_SPEEDO], "key-on, engine off, 0 psi: no oil pressure alert");
    for (; t < 3000; t += 10) { auto i = base(t); i.rpm = 250; i.volts = 9.8f; alertsUpdate(t, i, s, o); }
    CHECK(!o.flashing[G_SPEEDO], "cranking at 9.8 V: no voltage alert");
    for (; t < 9000; t += 10) { auto i = base(t); i.rpm = 900; i.oilPsi = 8; alertsUpdate(t, i, s, o); }
    CHECK(o.flashing[G_SPEEDO] && o.face[G_SPEEDO] == FACE_SPEEDO_DATA, "running 8 psi: speedo data face flashes"); }
  { AlertState s; AlertOutputs o; uint32_t t = 0;
    for (; t < 3000; t += 10) { auto i = base(t); i.rpm = 4500; i.afr = 15.5f; i.decelCut = true; alertsUpdate(t, i, s, o); }
    CHECK(!o.flashing[G_SPEEDO], "AFR 15.5 during decel cut: no alert");
    for (; t < 4000; t += 10) { auto i = base(t); i.rpm = 2500; i.afr = 15.5f; alertsUpdate(t, i, s, o); }
    CHECK(!o.flashing[G_SPEEDO], "AFR 15.5 at 2500 rpm: no alert");
    for (; t < 5000; t += 10) { auto i = base(t); i.rpm = 4500; i.afr = 14.3f; alertsUpdate(t, i, s, o); }
    CHECK(o.flashing[G_SPEEDO], "AFR 14.3 at 4500 rpm: alert"); }
  { AlertState s; AlertOutputs o; uint32_t t = 0, onAt = 0; int chimeMs = 0;
    for (; t < 20000; t += 10) { auto i = base(t); i.fuelRaw = 60; alertsUpdate(t, i, s, o); if (o.lowFuelLamp && !onAt) onAt = t; if (o.buzzDutyPct) chimeMs += 10; }
    CHECK(onAt == 10000, "low fuel lamp on after 10 s below 1.6 gal"); CHECK(chimeMs == CHIME_T1 + CHIME_T2, "one chime");
    for (; t < 21000; t += 10) { auto i = base(t); i.fuelRaw = 66; alertsUpdate(t, i, s, o); }
    CHECK(o.lowFuelLamp, "1.75 gal: lamp stays on (hysteresis)");
    { auto i = base(t); i.fuelRaw = 69; alertsUpdate(t, i, s, o); }
    CHECK(!o.lowFuelLamp, "above 1.8 gal: off at once"); }
  { AlertState s; AlertOutputs o; uint32_t t = 0; int ms = 0;
    for (; t < 5000; t += 10) { auto i = base(t); i.cel = t > 1000; alertsUpdate(t, i, s, o); if (o.buzzDutyPct) ms += 10; }
    CHECK(o.celLamp && ms == CEL_BUZZ_MS, "check engine: lamp on, single 1 s buzz"); }
  printf(fails ? "\n%d FAILED\n" : "\nall passed\n", fails); return fails != 0;
}
