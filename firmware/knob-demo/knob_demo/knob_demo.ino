// Neon knob demo for the Elecrow / Meshnology CrowPanel 1.28" rotary display (ESP32-S3, GC9A01 240x240).
// Standalone: no hub, no CAN. Shows the selector UI with fixed sample values.
//   Turn the ring : carousel  temp -> fuel -> tach -> ODO/TRIP -> speedo (wraps)
//   Tap (press)   : slide up/down to that gauge's alternate face
//   Hold 2 s      : screen inverts 0.5 s IF that gauge has a hold action
//                   (ODO/TRIP: reset trip; speedo: rotate data order, only on the data face). Otherwise nothing.
// Needs: ESP32 Arduino core 3.x and the LovyanGFX library. Pins from Elecrow's examples (Lesson03-Rotate).
#include <LovyanGFX.hpp>
#include "knob_art.h"

static const int PIN_ENC_A = 45, PIN_ENC_B = 42, PIN_BTN = 41, PIN_BL = 46;
static const int PIN_PWR1 = 1, PIN_PWR2 = 2, PIN_PWR_LED = 40;
static const int W = 240;

class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_GC9A01 panel; lgfx::Bus_SPI bus;
 public:
  LGFX() {
    auto b = bus.config();
    b.spi_host = SPI2_HOST; b.freq_write = 80000000; b.freq_read = 20000000; b.spi_3wire = true;
    b.pin_sclk = 10; b.pin_mosi = 11; b.pin_miso = -1; b.pin_dc = 3;
    bus.config(b); panel.setBus(&bus);
    auto p = panel.config();
    p.pin_cs = 9; p.pin_rst = 14; p.memory_width = W; p.memory_height = W; p.panel_width = W; p.panel_height = W;
    p.invert = true; p.readable = false; p.bus_shared = false;
    panel.config(p); setPanel(&panel);
  }
};
LGFX gfx;
LGFX_Sprite canvas(&gfx);

// ---- faces: [gauge][0 = default, 1 = alternate]
enum { TEMP, FUEL, TACH, ODO, SPEEDO, N_GAUGES };
struct Img { const uint8_t *d; uint32_t n; LGFX_Sprite *s; };
#define IMG(x) { x, sizeof(x), nullptr }
Img faces[N_GAUGES][2] = {
  { IMG(img_temp), IMG(img_temp_oil) }, { IMG(img_fuel), IMG(img_fuel_e85) }, { IMG(img_tach), IMG(img_tach_boost) },
  { IMG(img_odo), IMG(img_trip) },      { IMG(img_speedo), IMG(img_speedo_data) } };
Img tripZero = IMG(img_trip_zero);
int cur = TACH; bool alt[N_GAUGES] = {false}; bool tripWasReset = false;

LGFX_Sprite *load(Img &im) {
  LGFX_Sprite *s = new LGFX_Sprite(&gfx); s->setPsram(true); s->setColorDepth(16); s->createSprite(W, W);
  s->fillScreen(TFT_BLACK); s->drawJpg(im.d, im.n, 0, 0); im.s = s; return s;
}
LGFX_Sprite *face(int g, bool a) { return (g == ODO && a && tripWasReset) ? tripZero.s : faces[g][a ? 1 : 0].s; }
void show(LGFX_Sprite *s) { s->pushSprite(0, 0); }

// slide: dx/dy = direction the old image leaves (-1/+1)
void slide(LGFX_Sprite *from, LGFX_Sprite *to, int dx, int dy) {
  const int STEPS = 10;
  for (int i = 1; i <= STEPS; i++) {
    float t = (float)i / STEPS; t = t * t * (3 - 2 * t);       // ease in/out
    int o = (int)(t * W);
    canvas.fillScreen(TFT_BLACK);
    from->pushSprite(&canvas, dx * o, dy * o);
    to->pushSprite(&canvas, dx * o - dx * W, dy * o - dy * W);
    canvas.pushSprite(0, 0);
  }
  show(to);
}

// ---- encoder (same quadrature table as Elecrow's example: 4 quarter-steps per detent)
const int8_t QT[16] = {0,-1,1,0, 1,0,0,-1, -1,0,0,1, 0,1,-1,0};
uint8_t encLast = 0; int8_t encQ = 0;
int readEncoder() {
  uint8_t s = (digitalRead(PIN_ENC_A) << 1) | digitalRead(PIN_ENC_B);
  encQ += QT[(encLast << 2) | s]; encLast = s;
  if (encQ >= 4) { encQ = 0; return 1; }
  if (encQ <= -4) { encQ = 0; return -1; }
  return 0;
}
#define REVERSE_ROTATION false        // set true if turning clockwise moves the wrong way

bool hasHoldAction(int g) { return g == ODO || (g == SPEEDO && alt[SPEEDO]); }
void holdAction(int g) {
  gfx.invertDisplay(false); delay(500); gfx.invertDisplay(true);   // panel normally runs inverted (invert = true)
  if (g == ODO) { tripWasReset = true; show(face(cur, alt[cur])); Serial.println("hold: trip reset"); }
  if (g == SPEEDO) Serial.println("hold: speedo data order rotated (on the main gauge)");
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_PWR_LED, OUTPUT); digitalWrite(PIN_PWR_LED, LOW);
  pinMode(PIN_PWR1, OUTPUT); pinMode(PIN_PWR2, OUTPUT); digitalWrite(PIN_PWR1, HIGH); digitalWrite(PIN_PWR2, HIGH);
  pinMode(PIN_ENC_A, INPUT); pinMode(PIN_ENC_B, INPUT); pinMode(PIN_BTN, INPUT_PULLUP);
  ledcAttach(PIN_BL, 5000, 8); ledcWrite(PIN_BL, 200);
  gfx.init(); gfx.fillScreen(TFT_BLACK);
  canvas.setPsram(true); canvas.setColorDepth(16); canvas.createSprite(W, W);
  for (int g = 0; g < N_GAUGES; g++) { load(faces[g][0]); load(faces[g][1]); }
  load(tripZero);
  encLast = (digitalRead(PIN_ENC_A) << 1) | digitalRead(PIN_ENC_B);
  show(face(cur, alt[cur]));
  Serial.printf("knob demo ready, PSRAM %s\n", psramFound() ? "ok" : "MISSING (set Tools > PSRAM > OPI PSRAM)");
}

uint32_t pressAt = 0; bool pressed = false, holdDone = false;
void loop() {
  int step = readEncoder();
  if (step) {
    if (REVERSE_ROTATION) step = -step;
    int nxt = (cur + step + N_GAUGES) % N_GAUGES;
    slide(face(cur, alt[cur]), face(nxt, alt[nxt]), -step, 0);
    cur = nxt;
  }
  bool down = digitalRead(PIN_BTN) == LOW;
  uint32_t now = millis();
  if (down && !pressed) { pressed = true; pressAt = now; holdDone = false; delay(20); }
  if (down && pressed && !holdDone && now - pressAt >= 2000) {
    holdDone = true;                                   // a hold with no action does nothing
    if (hasHoldAction(cur)) holdAction(cur);
  }
  if (!down && pressed) {
    pressed = false; delay(20);
    if (!holdDone && now - pressAt >= 30) {             // tap
      LGFX_Sprite *from = face(cur, alt[cur]); alt[cur] = !alt[cur];
      slide(from, face(cur, alt[cur]), 0, alt[cur] ? -1 : 1);
    }
  }
}
