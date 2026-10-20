// Neon tach demo for the Waveshare ESP32-S3-LCD-2.8C (480x480 round, ST7701 RGB panel).
// Standalone: no hub, no CAN. Real tach face art + rotating needle, day or night, with a frames-per-second counter.
// BOOT button:  click        = day / night
//               double-click = mode: DRIVE (simulated driving) -> SWEEP (continuous 0-8000-0) -> HOLD (needle still)
//               long press   = sweep speed: 2 s -> 1 s -> 0.5 s -> 0.25 s per 0-8000 pass
// FPS is shown at the bottom of the screen and printed to the Serial Monitor (115200) once a second.
// Display, IO-expander and I2C files are Waveshare's (from the ESP32-S3-LCD-2.8C demo), unchanged except for removing LVGL
// and using two frame buffers.
#include <Arduino.h>
#include <math.h>
#include "Display_ST7701.h"
#include "TCA9554PWR.h"
#include "I2C_Driver.h"
#include "tach_art.h"

static const int W = 480, H = 480, BTN_BOOT = 0;
static uint16_t *faceDay, *faceNight;     // decoded faces in PSRAM
static uint16_t *fb[2];                   // the panel's two frame buffers
static int back = 1;
struct Box { int x0, y0, x1, y1; };       // inclusive-exclusive
static Box lastBox[2] = {{0,0,W,H},{0,0,W,H}};
static bool night = false, nightPrev = true;
enum Mode { DRIVE, SWEEP, HOLD };
static Mode mode = DRIVE;
static float sweepPassS[] = {2.0f, 1.0f, 0.5f, 0.25f}; static int sweepIdx = 0;

float rpmToAngle(float rpm) { return -115.6f + rpm * 0.02885f; }   // 0 = up, + = clockwise (same as the art tools)

void decodeRLE(const uint16_t *r, size_t n, uint16_t *dst) {
  for (size_t i = 0; i < n; i += 2) { uint16_t c = r[i], v = r[i + 1]; while (c--) *dst++ = v; }
}
static inline uint16_t blend(uint16_t bg, uint16_t fg, uint8_t a) {
  if (a == 255) return fg; if (a == 0) return bg;
  uint32_t rb = bg & 0xF81F, g = bg & 0x07E0, rf = fg & 0xF81F, gf = fg & 0x07E0;
  rb = (rb + (((rf - rb) * (a >> 3)) >> 5)) & 0xF81F; g = (g + (((gf - g) * (a >> 2)) >> 6)) & 0x07E0;
  return rb | g;
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

void restore(uint16_t *dst, const uint16_t *face, Box b) {
  for (int y = b.y0; y < b.y1; y++) memcpy(dst + y * W + b.x0, face + y * W + b.x0, (b.x1 - b.x0) * 2);
}
Box unite(Box a, Box b) { return {min(a.x0,b.x0), min(a.y0,b.y0), max(a.x1,b.x1), max(a.y1,b.y1)}; }

Box drawNeedle(uint16_t *dst, float angDeg) {
  const uint16_t *nrgb = night ? needle_night_rgb : needle_day_rgb; const uint8_t *na = night ? needle_night_a : needle_day_a;
  float a = angDeg * (float)M_PI / 180.0f, c = cosf(a), s = sinf(a);
  // bounding box of the rotated needle rectangle
  float xs[4] = {-NEEDLE_PIVOT_X, NEEDLE_W - NEEDLE_PIVOT_X, NEEDLE_W - NEEDLE_PIVOT_X, -NEEDLE_PIVOT_X};
  float ys[4] = {-NEEDLE_PIVOT_Y, -NEEDLE_PIVOT_Y, NEEDLE_H - NEEDLE_PIVOT_Y, NEEDLE_H - NEEDLE_PIVOT_Y};
  float mnx = 1e9, mny = 1e9, mxx = -1e9, mxy = -1e9;
  for (int i = 0; i < 4; i++) { float X = xs[i] * c - ys[i] * s, Y = xs[i] * s + ys[i] * c;
    mnx = fminf(mnx, X); mxx = fmaxf(mxx, X); mny = fminf(mny, Y); mxy = fmaxf(mxy, Y); }
  Box b = {max(0, (int)floorf(FACE_PIVOT_X + mnx) - 1), max(0, (int)floorf(FACE_PIVOT_Y + mny) - 1),
           min(W, (int)ceilf(FACE_PIVOT_X + mxx) + 2), min(H, (int)ceilf(FACE_PIVOT_Y + mxy) + 2)};
  for (int y = b.y0; y < b.y1; y++) {
    float dy = y + 0.5f - FACE_PIVOT_Y; uint16_t *row = dst + y * W;
    for (int x = b.x0; x < b.x1; x++) {
      float dx = x + 0.5f - FACE_PIVOT_X;
      float u = dx * c + dy * s + NEEDLE_PIVOT_X - 0.5f, v = -dx * s + dy * c + NEEDLE_PIVOT_Y - 0.5f;   // inverse rotation
      int iu = (int)floorf(u), iv = (int)floorf(v);
      if (iu < 0 || iv < 0 || iu >= NEEDLE_W - 1 || iv >= NEEDLE_H - 1) continue;
      float fu = u - iu, fv = v - iv; int k = iv * NEEDLE_W + iu;
      float al = (na[k] * (1 - fu) + na[k + 1] * fu) * (1 - fv) + (na[k + NEEDLE_W] * (1 - fu) + na[k + NEEDLE_W + 1] * fu) * fv;
      if (al < 1) continue;
      int kc = (fu < 0.5f ? 0 : 1) + (fv < 0.5f ? 0 : NEEDLE_W);
      row[x] = blend(row[x], nrgb[k + kc], (uint8_t)al);
    }
  }
  // hub on top
  int hx = (int)(FACE_PIVOT_X - HUB_W / 2.0f), hy = (int)(FACE_PIVOT_Y - HUB_H / 2.0f);
  for (int y = 0; y < HUB_H; y++) for (int x = 0; x < HUB_W; x++) {
    uint8_t al = hub_a[y * HUB_W + x]; if (al) dst[(hy + y) * W + hx + x] = blend(dst[(hy + y) * W + hx + x], hub_rgb[y * HUB_W + x], al);
  }
  return unite(b, {hx, hy, hx + HUB_W, hy + HUB_H});
}

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

void setup() {
  Serial.begin(115200);
  pinMode(BTN_BOOT, INPUT_PULLUP);
  I2C_Init(); TCA9554PWR_Init(0x00); Backlight_Init(); Set_Backlight(80);
  LCD_Init();
  if (!psramFound()) { Serial.println("PSRAM MISSING: set Tools > PSRAM > OPI PSRAM"); }
  faceDay = (uint16_t *)heap_caps_malloc(W * H * 2, MALLOC_CAP_SPIRAM);
  faceNight = (uint16_t *)heap_caps_malloc(W * H * 2, MALLOC_CAP_SPIRAM);
  decodeRLE(face_day_rle, sizeof(face_day_rle) / 2, faceDay);
  decodeRLE(face_night_rle, sizeof(face_night_rle) / 2, faceNight);
  void *f0 = nullptr, *f1 = nullptr;
  esp_lcd_rgb_panel_get_frame_buffer(panel_handle, 2, &f0, &f1); fb[0] = (uint16_t *)f0; fb[1] = (uint16_t *)f1;
  Serial.printf("tach demo ready: fb %p %p\n", f0, f1);
}

void loop() {
  static uint32_t frames = 0, fpsT = 0; static int fps = 0; static float holdRpm = 3000;
  int e = buttonEvent();
  if (e == 1) night = !night;
  if (e == 2) { mode = (Mode)((mode + 1) % 3); Serial.printf("mode %s\n", mode == DRIVE ? "DRIVE" : mode == SWEEP ? "SWEEP" : "HOLD"); }
  if (e == 3) { sweepIdx = (sweepIdx + 1) % 4; Serial.printf("sweep pass %.2f s\n", sweepPassS[sweepIdx]); }
  uint32_t now = millis();
  float rpm = mode == DRIVE ? driveRpm(now) : mode == SWEEP ? sweepRpm(now) : holdRpm;
  if (mode != HOLD) holdRpm = rpm;

  uint16_t *dst = fb[back]; const uint16_t *face = night ? faceNight : faceDay;
  static bool full[2] = {true, true};
  if (night != nightPrev) { full[0] = full[1] = true; nightPrev = night; }
  if (full[back]) { memcpy(dst, face, W * H * 2); full[back] = false; }
  else { restore(dst, face, lastBox[back]); restore(dst, face, FPS_BOX); }
  lastBox[back] = drawNeedle(dst, rpmToAngle(rpm));
  drawNum(dst, FPS_BOX.x0 + 2, FPS_BOX.y0, fps, 3, night ? 0xFB20 : 0x8410);
  esp_lcd_panel_draw_bitmap(panel_handle, 0, 0, W, H, dst);     // dst is a frame buffer: this swaps buffers
  back ^= 1;

  frames++;
  if (now - fpsT >= 1000) { fps = frames * 1000 / (now - fpsT); frames = 0; fpsT = now;
    Serial.printf("fps %d  rpm %.0f  mode %d  %s\n", fps, rpm, mode, night ? "night" : "day"); }
}
