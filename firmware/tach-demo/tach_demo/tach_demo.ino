// Neon tach demo for the Waveshare ESP32-S3-LCD-2.8C (480x480 round, ST7701 RGB panel).
// Standalone: no hub, no CAN. Real tach face art + rotating needle, day or night, with a frames-per-second counter.
// BOOT button:  click        = day / night
//               double-click = mode: DRIVE (simulated driving) -> SWEEP (continuous 0-8000-0) -> HOLD (needle still)
//               long press   = sweep speed: 2 s -> 1 s -> 0.5 s -> 0.25 s per 0-8000 pass
// FPS is shown at the bottom of the screen and printed to the Serial Monitor (115200) once a second.
// Display, IO-expander and I2C files are Waveshare's (from the ESP32-S3-LCD-2.8C demo), unchanged except for removing LVGL
// and using two frame buffers.
// Speed (2026-10-25): panel clock lowered to about 60 Hz, needle drawn by firmware/gauge/needle_render.h (spans, fixed point,
// art in internal RAM), frames synced to the panel, frame-rate lock (default 30). Settings are just below.
#include <Arduino.h>
#include <math.h>
#include "Display_ST7701.h"
#include "TCA9554PWR.h"
#include "I2C_Driver.h"
#include "tach_art.h"
#include "needle_render.h"   // copy of firmware/gauge/needle_render.h (tools/sync_shared.sh)
#include <AnimatedGIF.h>      // Library Manager: "AnimatedGIF" by Larry Bank
#include "startup_gif.h"      // owner-supplied startup animation (firmware/tach-demo/startup.gif)

// Startup sequence (owner 2026-10-26, power-on only, never repeated): fade the GIF in, play it ONCE centred at native
// size (480 x 360; the round screen clips the corners, nothing is scaled). The GIF is cut before the white "neon" card
// (ends on the white car "Hi." frame, 6.27 s); after its last frame it fades quickly to black, then the face fades up
// within 1 s.
// Set STARTUP_GIF 0 to skip it. Needs Tools > Partition Scheme > Custom (uses partitions.csv in this folder).
#define STARTUP_GIF 1
#define STARTUP_FADEIN_MS 500
#define STARTUP_FADEOUT_MS 300            // quick fade to black after the last GIF frame
#define FACE_FADEIN_MS 1000

struct Box { int x0, y0, x1, y1; };      // x1/y1 exclusive

// ---------------- settings ----------------
// Backlight 0-100 (Waveshare scale: 100 = fully on, as in Waveshare's own demo; 80 was about 78 % duty).
#define BACKLIGHT_PCT 100
// Panel pixel clock. Waveshare ships 30 MHz (about 108 Hz refresh), which spends most of the PSRAM bandwidth and CPU
// feeding the screen. 16.7 MHz gives about 60 Hz. The Serial Monitor prints the measured refresh ("panel Hz").
#define PCLK_HZ 16700000
// Frame-rate lock: 30 (default), 60, or 0 = unlocked (as fast as it can draw, still synced to the panel).
#define FPS_LOCK 30
// Print time per step (restore / needle / wait) once a second: 1 = on.
#define TIMING_PRINTS 1
// -------------------------------------------

static const int W = 480, H = 480, BTN_BOOT = 0;
static uint16_t *faceDay, *faceNight;     // decoded faces in PSRAM
static uint16_t *fb[2];                   // the panel's two frame buffers
static int back = 1;
static uint32_t faceFadeStart = 0;          // millis() when the face fade-up began; 0 = done
static AnimatedGIF gif;
static SemaphoreHandle_t frameDone;       // given by the driver when a frame buffer is no longer being read
static volatile uint32_t panelFrames = 0;
static bool night = false, nightPrev = true;
enum Mode { DRIVE, SWEEP, HOLD };
static Mode mode = DRIVE;
static float sweepPassS[] = {2.0f, 1.0f, 0.5f, 0.25f}; static int sweepIdx = 0;

float rpmToAngle(float rpm) { return -115.6f + rpm * 0.02885f; }   // 0 = up, + = clockwise (same as the art tools)

void decodeRLE(const uint16_t *r, size_t n, uint16_t *dst) {
  for (size_t i = 0; i < n; i += 2) { uint16_t c = r[i], v = r[i + 1]; while (c--) *dst++ = v; }
}

// ---- tiny 3x5 digit font for the FPS readout
static const uint16_t DIG[10] = {0x7B6F,0x2C97,0x73E7,0x73CF,0x5BC9,0x79CF,0x79EF,0x7249,0x7BEF,0x7BCF};
void drawNum(uint16_t *dst, int x, int y, int v, int s, uint16_t col) {
  char b[8]; snprintf(b, sizeof b, "%d", v);
  for (int k = 0; b[k]; k++) {
    uint16_t m = DIG[b[k] - '0'];
    for (int r = 0; r < 5; r++) for (int c = 0; c < 3; c++) if (m & (1 << (14 - (r * 3 + c))))
      for (int yy = 0; yy < s; yy++) for (int xx = 0; xx < s; xx++) dst[(y + r * s + yy) * W + x + k * 4 * s + c * s + xx] = col;
  }
}
static const Box FPS_BOX = {222, 446, 258, 461};
void restoreBox(uint16_t *dst, const uint16_t *face, Box b) {
  for (int y = b.y0; y < b.y1; y++) memcpy(dst + y * W + b.x0, face + y * W + b.x0, (b.x1 - b.x0) * 2);
}

// ---- needle/hub art copied to internal RAM (fast), renderer shared with the gauge firmware
template <typename T> T *toInternal(const T *src, size_t n) {
  T *d = (T *)heap_caps_malloc(n * sizeof(T), MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
  if (!d) return (T *)src;                                   // fall back to flash if internal RAM is short
  memcpy(d, src, n * sizeof(T)); return d;
}
static nr::Art needleDay, needleNight, hubArt;
static nr::Renderer<480, 480, 2> R;

// ---- simulated rpm
float driveRpm(uint32_t ms) {
  float t = fmodf(ms / 1000.0f, 20.0f);
  if (t < 4) return 850 + 30 * sinf(ms / 90.0f);                                   // idle
  if (t < 5) return 850 + (t - 4) * 3000;                                           // blip
  if (t < 6) return 3850 - (t - 5) * 3000;
  if (t < 7) return 850 + 30 * sinf(ms / 90.0f);
  float p = t - 7;                                                                  // pull through the gears
  float g[4][2] = {{2500, 7800}, {5200, 7800}, {5600, 7800}, {5900, 7000}}; float seg = 2.8f;
  int k = min(3, (int)(p / seg)); float f = fminf(1, (p - k * seg) / (seg - 0.3f));
  if (p >= 4 * seg) return 850 + 30 * sinf(ms / 90.0f);
  return g[k][0] + (g[k][1] - g[k][0]) * f;
}
float sweepRpm(uint32_t ms) {
  float pass = sweepPassS[sweepIdx] * 1000.0f, ph = fmodf(ms, 2 * pass) / pass;     // 0..2
  return 8000.0f * (ph < 1 ? ph : 2 - ph);
}

// ---- BOOT button: click / double-click / long press
int buttonEvent() {   // 0 none, 1 click, 2 double, 3 long
  static bool was = false; static uint32_t downAt = 0, upAt = 0; static int clicks = 0; static bool longDone = false;
  bool down = digitalRead(BTN_BOOT) == LOW; uint32_t now = millis();
  if (down && !was) { downAt = now; longDone = false; }
  if (down && !longDone && now - downAt > 800) { longDone = true; clicks = 0; was = down; return 3; }
  if (!down && was && !longDone && now - downAt > 30) { clicks++; upAt = now; }
  was = down;
  if (clicks && !down && now - upAt > 300) { int c = clicks; clicks = 0; return c >= 2 ? 2 : 1; }
  return 0;
}

static bool IRAM_ATTR onFrameDone(esp_lcd_panel_handle_t, const esp_lcd_rgb_panel_event_data_t *, void *) {
  BaseType_t woken = pdFALSE; panelFrames++;
  xSemaphoreGiveFromISR(frameDone, &woken); return woken == pdTRUE;
}

static void present(uint16_t *dst) {          // show a full frame buffer and wait until the other one is free
  xSemaphoreTake(frameDone, 0);
  esp_lcd_panel_draw_bitmap(panel_handle, 0, 0, W, H, dst);
  xSemaphoreTake(frameDone, pdMS_TO_TICKS(50));
  back ^= 1;
}

static void startupBacklight(uint32_t el, uint32_t fadeAt) {   // fadeAt = 0 until the last frame has been shown
  static int last = -1; int pct;
  if (fadeAt && el >= fadeAt) pct = el >= fadeAt + STARTUP_FADEOUT_MS ? 0 : BACKLIGHT_PCT - BACKLIGHT_PCT * (el - fadeAt) / STARTUP_FADEOUT_MS;
  else if (el < STARTUP_FADEIN_MS) pct = BACKLIGHT_PCT * el / STARTUP_FADEIN_MS;
  else pct = BACKLIGHT_PCT;
  if (pct != last) { Set_Backlight(pct); last = pct; }
}

static void playStartup() {
  memset(fb[0], 0, W * H * 2); memset(fb[1], 0, W * H * 2);
  gif.begin(GIF_PALETTE_RGB565_LE);
  if (!gif.open((uint8_t *)startup_gif, STARTUP_GIF_LEN, nullptr)) { Serial.println("startup gif: open failed"); return; }
  const int cw = gif.getCanvasWidth(), ch = gif.getCanvasHeight();
  // canvas: 8-bit indices (cw*ch) followed by the composited RGB565 frame (cw*ch*2), kept between frames
  uint8_t *buf = (uint8_t *)heap_caps_malloc(cw * ch * 3 + cw * 2, MALLOC_CAP_SPIRAM);
  if (!buf) { gif.close(); Serial.println("startup gif: no PSRAM"); return; }
  memset(buf, 0, cw * ch * 3 + cw * 2);
  gif.setDrawType(GIF_DRAW_COOKED); gif.setFrameBuf(buf);
  const uint16_t *rgb = (const uint16_t *)(buf + cw * ch);
  // centre at native size; crop (never scale) if the GIF is larger than the screen
  const int dx = (W - cw) / 2, dy = (H - ch) / 2;
  const int sx0 = dx < 0 ? -dx : 0, sy0 = dy < 0 ? -dy : 0, ox = dx < 0 ? 0 : dx, oy = dy < 0 ? 0 : dy;
  const int cpw = min(cw - sx0, W - ox), cph = min(ch - sy0, H - oy);
  const uint32_t t0 = millis(); uint32_t due = t0; int frames = 0;
  for (;;) {                                                     // play once; never loops
    int delayMs = 0; int r = gif.playFrame(false, &delayMs);
    if (r < 0) { Serial.printf("startup gif: decode error %d\n", gif.getLastError()); break; }
    uint16_t *dst = fb[back];
    for (int y = 0; y < cph; y++) memcpy(dst + (oy + y) * W + ox, rgb + (sy0 + y) * cw + sx0, cpw * 2);
    while ((int32_t)(millis() - due) < 0) { startupBacklight(millis() - t0, 0); delay(1); }
    startupBacklight(millis() - t0, 0);
    present(dst); frames++;
    due += delayMs > 0 ? delayMs : 60;
    if ((int32_t)(millis() - due) > 200) due = millis();       // decoding fell behind: resync instead of racing
    if (r == 0) break;                                           // that was the last frame
  }
  // hold the last frame for its delay, then fade quickly to black
  while ((int32_t)(millis() - due) < 0) { startupBacklight(millis() - t0, 0); delay(1); }
  const uint32_t fadeAt = millis() - t0;
  while (millis() - t0 < fadeAt + STARTUP_FADEOUT_MS) { startupBacklight(millis() - t0, fadeAt); delay(1); }
  Set_Backlight(0);
  gif.close(); heap_caps_free(buf);
  Serial.printf("startup gif: %d frames in %lu ms\n", frames, (unsigned long)(millis() - t0));
}

void setup() {
  Serial.begin(115200);
  pinMode(BTN_BOOT, INPUT_PULLUP);
  I2C_Init();
  // The TCA9554 expander powers up with every output latch HIGH (TI datasheet: Output Port default 1111 1111), and
  // EXIO8 drives the board's onboard buzzer. Set the latch with the buzzer off BEFORE making the pins outputs, so it
  // never sounds. (Waveshare's own demo turns EXIO8 off in setup; the first version of this sketch missed it.)
  Set_EXIOS(0x7F);                            // writes the output latch: EXIO8 (bit 7) low = buzzer off; EXIO1-7 keep their high default
  TCA9554PWR_Init(0x00);                      // all EXIO pins outputs
  Set_EXIO(EXIO_PIN8, Low);                   // and once more, explicitly
  Backlight_Init(); Set_Backlight(STARTUP_GIF ? 0 : BACKLIGHT_PCT);   // dark until the startup sequence fades in
  LCD_Init();
  if (!psramFound()) { Serial.println("PSRAM MISSING: set Tools > PSRAM > OPI PSRAM"); }
  faceDay = (uint16_t *)heap_caps_malloc(W * H * 2, MALLOC_CAP_SPIRAM);
  faceNight = (uint16_t *)heap_caps_malloc(W * H * 2, MALLOC_CAP_SPIRAM);
  decodeRLE(face_day_rle, sizeof(face_day_rle) / 2, faceDay);
  decodeRLE(face_night_rle, sizeof(face_night_rle) / 2, faceNight);
  void *f0 = nullptr, *f1 = nullptr;
  esp_lcd_rgb_panel_get_frame_buffer(panel_handle, 2, &f0, &f1); fb[0] = (uint16_t *)f0; fb[1] = (uint16_t *)f1;
  esp_lcd_rgb_panel_set_pclk(panel_handle, PCLK_HZ);
  frameDone = xSemaphoreCreateBinary();
  esp_lcd_rgb_panel_event_callbacks_t cbs = {};
  cbs.on_frame_buf_complete = onFrameDone;
  esp_lcd_rgb_panel_register_event_callbacks(panel_handle, &cbs, nullptr);
  const size_t NN = NEEDLE_W * NEEDLE_H, HN = HUB_W * HUB_H;
  needleDay = {toInternal(needle_day_rgb, NN), toInternal(needle_day_a, NN), NEEDLE_W, NEEDLE_H, NEEDLE_PIVOT_X, NEEDLE_PIVOT_Y};
  needleNight = {toInternal(needle_night_rgb, NN), toInternal(needle_night_a, NN), NEEDLE_W, NEEDLE_H, NEEDLE_PIVOT_X, NEEDLE_PIVOT_Y};
  hubArt = {toInternal(hub_rgb, HN), toInternal(hub_a, HN), HUB_W, HUB_H, 0, 0};
  R.begin(FACE_PIVOT_X, FACE_PIVOT_Y, &hubArt);
  Serial.printf("tach demo ready: fb %p %p\n", f0, f1);
#if STARTUP_GIF
  playStartup();                                // power-on only; loop() then fades the face up
  faceFadeStart = millis(); if (!faceFadeStart) faceFadeStart = 1;
#endif
}

void loop() {
  static uint32_t frames = 0, fpsT = 0, nextUs = 0, lastPanel = 0; static int fps = 0; static float holdRpm = 3000;
  static uint32_t tRestore = 0, tNeedle = 0, tWait = 0, tPace = 0;
  int e = buttonEvent();
  if (e == 1) night = !night;
  if (e == 2) { mode = (Mode)((mode + 1) % 3); Serial.printf("mode %s\n", mode == DRIVE ? "DRIVE" : mode == SWEEP ? "SWEEP" : "HOLD"); }
  if (e == 3) { sweepIdx = (sweepIdx + 1) % 4; Serial.printf("sweep pass %.2f s\n", sweepPassS[sweepIdx]); }

  uint32_t t0 = micros();
  if (FPS_LOCK > 0) {                                        // pace to the lock rate
    const uint32_t period = 1000000UL / FPS_LOCK;
    if ((int32_t)(t0 - nextUs) < 0) delayMicroseconds(nextUs - t0);
    uint32_t now = micros();
    nextUs = ((int32_t)(now - nextUs) > (int32_t)period) ? now + period : nextUs + period;
  }
  uint32_t t1 = micros(); tPace += t1 - t0;

  uint32_t now = millis();
  float rpm = mode == DRIVE ? driveRpm(now) : mode == SWEEP ? sweepRpm(now) : holdRpm;
  if (mode != HOLD) holdRpm = rpm;

  uint16_t *dst = fb[back]; const uint16_t *face = night ? faceNight : faceDay;
  static bool full[2] = {true, true};
  if (night != nightPrev) { full[0] = full[1] = true; nightPrev = night; }
  if (full[back]) { memcpy(dst, face, W * H * 2); full[back] = false; for (int y = 0; y < H; y++) R.dirty[back][y] = {0, 0}; }
  else { R.restore(dst, face, back); restoreBox(dst, face, FPS_BOX); }
  uint32_t t2 = micros(); tRestore += t2 - t1;
  R.draw(dst, night ? needleNight : needleDay, rpmToAngle(rpm), back);
  drawNum(dst, FPS_BOX.x0 + 2, FPS_BOX.y0, fps, 3, night ? 0xFB20 : 0x8410);
  uint32_t t3 = micros(); tNeedle += t3 - t2;

  xSemaphoreTake(frameDone, 0);                              // clear a stale signal
  esp_lcd_panel_draw_bitmap(panel_handle, 0, 0, W, H, dst);  // dst is a frame buffer: the panel switches to it
  xSemaphoreTake(frameDone, pdMS_TO_TICKS(50));              // wait until the old buffer is no longer on screen
  back ^= 1;
  tWait += micros() - t3;
  if (faceFadeStart) {                           // face fade-up after the startup animation (face is already drawn)
    uint32_t el = millis() - faceFadeStart;
    if (el >= FACE_FADEIN_MS) { Set_Backlight(BACKLIGHT_PCT); faceFadeStart = 0; }
    else Set_Backlight(BACKLIGHT_PCT * el / FACE_FADEIN_MS);
  }

  frames++;
  if (now - fpsT >= 1000) {
    uint32_t dt = now - fpsT; fps = frames * 1000 / dt;
    uint32_t pf = panelFrames; int panelHz = (pf - lastPanel) * 1000 / dt; lastPanel = pf;
    Serial.printf("fps %d  panel Hz %d  rpm %.0f  mode %d  %s\n", fps, panelHz, rpm, mode, night ? "night" : "day");
    if (TIMING_PRINTS && frames) Serial.printf("  per frame (ms): pace %.1f  restore %.1f  needle %.1f  wait-for-panel %.1f\n",
        tPace / 1000.0f / frames, tRestore / 1000.0f / frames, tNeedle / 1000.0f / frames, tWait / 1000.0f / frames);
    frames = 0; fpsT = now; tRestore = tNeedle = tWait = tPace = 0;
  }
}
