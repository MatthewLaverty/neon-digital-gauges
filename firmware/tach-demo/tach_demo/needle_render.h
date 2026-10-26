// Needle renderer for the RGB-panel gauges (2026-10-25). Shared by the real gauge firmware and the tach demo
// (firmware/tach-demo/tach_demo/needle_render.h is a copy; tools/sync_shared.sh keeps it identical).
// Plain C++: no Arduino calls, so it is host-testable (firmware/gauge/test/test_needle_render.cpp).
//
// Speed-ups over the first demo:
//  - per-row spans: only pixels the rotated needle rectangle can cover are visited (the bounding box is mostly empty)
//  - 16.16 fixed-point stepping along each row, integer bilinear alpha
//  - dirty spans are remembered per frame buffer, so restoring the face copies only what the needle touched
//  - art pointers should be copies in internal RAM (see needleArtToInternal() in the demo); the face stays in PSRAM
// Angle: 0 = straight up, positive = clockwise (same as tools/alt-faces).
#pragma once
#include <stdint.h>
#include <string.h>
#include <math.h>

namespace nr {

struct Art {               // RGB565 + 8-bit alpha, row-major
  const uint16_t *rgb; const uint8_t *a; int w, h;
  float pivotX, pivotY;    // needle: rotation pivot inside the image; hub: unused (hub is centred on the face pivot)
};

static inline uint16_t blend565(uint16_t bg, uint16_t fg, uint32_t a) {   // a 0..255
  if (a >= 255) return fg;
  uint32_t b = ((bg & 0xF81F) | ((uint32_t)(bg & 0x07E0) << 16)), f = ((fg & 0xF81F) | ((uint32_t)(fg & 0x07E0) << 16));
  uint32_t a5 = (a + 4) >> 3;                                            // 0..32
  uint32_t r = (b + (((f - b) * a5) >> 5)) & 0x07E0F81F;
  return (uint16_t)(r | (r >> 16));
}

struct Span { int16_t x0, x1; };      // x1 exclusive; x0 >= x1 = empty

template <int W, int H, int NBUF>
struct Renderer {
  float faceX, faceY;                  // needle pivot on the face
  Span dirty[NBUF][H];                 // what the needle covered last time in each frame buffer
  int hubX = 0, hubY = 0;
  const Art *hub = nullptr;

  void begin(float fx, float fy, const Art *hubArt) {
    faceX = fx; faceY = fy; hub = hubArt;
    if (hub) { hubX = (int)(fx - hub->w / 2.0f); hubY = (int)(fy - hub->h / 2.0f); }
    for (int b = 0; b < NBUF; b++) markAll(b);
  }
  void markAll(int b) { for (int y = 0; y < H; y++) dirty[b][y] = {0, (int16_t)W}; }   // next restore copies everything

  // Copy back the face where buffer `b` was drawn on (last needle spans + the hub box).
  void restore(uint16_t *dst, const uint16_t *face, int b) {
    for (int y = 0; y < H; y++) {
      Span s = dirty[b][y];
      if (s.x1 > s.x0) memcpy(dst + y * W + s.x0, face + y * W + s.x0, (s.x1 - s.x0) * 2);
      dirty[b][y] = {0, 0};
    }
    if (hub) for (int y = 0; y < hub->h; y++)
      memcpy(dst + (hubY + y) * W + hubX, face + (hubY + y) * W + hubX, hub->w * 2);
  }

  // Draw the needle at `angDeg` and the hub on top. Returns pixels visited (for timing printouts).
  uint32_t draw(uint16_t *dst, const Art &n, float angDeg, int b) {
    const float a = angDeg * 3.14159265f / 180.0f, c = cosf(a), s = sinf(a);
    // vertical extent of the rotated rectangle
    float ys[4], xs[4]; const float cx[4] = {-n.pivotX, n.w - n.pivotX, n.w - n.pivotX, -n.pivotX};
    const float cy[4] = {-n.pivotY, -n.pivotY, n.h - n.pivotY, n.h - n.pivotY};
    float mny = 1e9f, mxy = -1e9f;
    for (int i = 0; i < 4; i++) { xs[i] = cx[i] * c - cy[i] * s; ys[i] = cx[i] * s + cy[i] * c;
      if (ys[i] < mny) mny = ys[i]; if (ys[i] > mxy) mxy = ys[i]; }
    int y0 = (int)floorf(faceY + mny) - 1, y1 = (int)ceilf(faceY + mxy) + 1;
    if (y0 < 0) y0 = 0; if (y1 > H) y1 = H;
    const float uMax = n.w - 1.0f, vMax = n.h - 1.0f;          // bilinear needs u+1, v+1
    const int32_t dU = (int32_t)lrintf(c * 65536.0f), dV = (int32_t)lrintf(-s * 65536.0f);
    uint32_t visited = 0;
    for (int y = y0; y < y1; y++) {
      const float dy = y + 0.5f - faceY;
      // u(x) = (x + 0.5 - faceX)*c + dy*s + pivotX - 0.5 ; v(x) = -(x + 0.5 - faceX)*s + dy*c + pivotY - 0.5
      const float uA = (0.5f - faceX) * c + dy * s + n.pivotX - 0.5f, vA = -(0.5f - faceX) * s + dy * c + n.pivotY - 0.5f;
      float lo = 0, hi = (float)W;
      auto clip = [&](float f0, float k, float fmax) {           // keep x where 0 <= f0 + k*x < fmax
        if (fabsf(k) < 1e-6f) { if (f0 < 0 || f0 >= fmax) { lo = 1; hi = 0; } return; }
        float xa = (0 - f0) / k, xb = (fmax - f0) / k; if (xa > xb) { float t = xa; xa = xb; xb = t; }
        if (xa > lo) lo = xa; if (xb < hi) hi = xb;
      };
      clip(uA, c, uMax); clip(vA, -s, vMax);
      int x0 = (int)floorf(lo) - 1, x1 = (int)ceilf(hi) + 1;
      if (x0 < 0) x0 = 0; if (x1 > W) x1 = W;
      if (x1 <= x0) continue;
      Span &d = dirty[b][y];
      if (d.x1 <= d.x0) d = {(int16_t)x0, (int16_t)x1};
      else { if (x0 < d.x0) d.x0 = x0; if (x1 > d.x1) d.x1 = x1; }
      int32_t U = (int32_t)lrintf((uA + c * x0) * 65536.0f), V = (int32_t)lrintf((vA - s * x0) * 65536.0f);
      uint16_t *row = dst + y * W;
      for (int x = x0; x < x1; x++, U += dU, V += dV) {
        visited++;
        if (U < 0 || V < 0) continue;
        const int iu = U >> 16, iv = V >> 16;
        if (iu >= n.w - 1 || iv >= n.h - 1) continue;
        const uint32_t fu = (U >> 8) & 255, fv = (V >> 8) & 255;
        const int k = iv * n.w + iu;
        const uint32_t top = n.a[k] * (256 - fu) + n.a[k + 1] * fu, bot = n.a[k + n.w] * (256 - fu) + n.a[k + n.w + 1] * fu;
        const uint32_t al = (top * (256 - fv) + bot * fv) >> 16;
        if (!al) continue;
        const int kc = k + (fu >= 128 ? 1 : 0) + (fv >= 128 ? n.w : 0);
        row[x] = blend565(row[x], n.rgb[kc], al);
      }
    }
    if (hub) for (int y = 0; y < hub->h; y++) {
      uint16_t *row = dst + (hubY + y) * W + hubX; const uint8_t *ha = hub->a + y * hub->w; const uint16_t *hc = hub->rgb + y * hub->w;
      for (int x = 0; x < hub->w; x++) if (ha[x]) row[x] = blend565(row[x], hc[x], ha[x]);
    }
    return visited;
  }
};

}  // namespace nr
