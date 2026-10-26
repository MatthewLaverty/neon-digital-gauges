// Host test: the fast renderer matches a straightforward float reference, and restore() returns the exact face.
#include "../needle_render.h"
#include "../../tach-demo/tach_demo/tach_art.h"
#include <cstdio>
#include <cstdlib>
#include <vector>
static const int W = 480, H = 480;
static void decode(const uint16_t *r, size_t n, uint16_t *d) { for (size_t i = 0; i < n; i += 2) for (int c = 0; c < r[i]; c++) *d++ = r[i + 1]; }
static int ch(uint16_t p, int k) { return k == 0 ? (p >> 11) << 3 : k == 1 ? ((p >> 5) & 63) << 2 : (p & 31) << 3; }
static void reference(uint16_t *dst, float ang) {         // plain float bilinear alpha, whole bounding square
  float a = ang * 3.14159265f / 180, c = cosf(a), s = sinf(a);
  for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) {
    float dx = x + .5f - FACE_PIVOT_X, dy = y + .5f - FACE_PIVOT_Y;
    float u = dx * c + dy * s + NEEDLE_PIVOT_X - .5f, v = -dx * s + dy * c + NEEDLE_PIVOT_Y - .5f;
    int iu = (int)floorf(u), iv = (int)floorf(v);
    if (iu < 0 || iv < 0 || iu >= NEEDLE_W - 1 || iv >= NEEDLE_H - 1) continue;
    float fu = u - iu, fv = v - iv; int k = iv * NEEDLE_W + iu; const uint8_t *A = needle_day_a;
    float al = (A[k] * (1 - fu) + A[k + 1] * fu) * (1 - fv) + (A[k + NEEDLE_W] * (1 - fu) + A[k + NEEDLE_W + 1] * fu) * fv;
    if (al < 1) continue;
    int kc = k + (fu < .5f ? 0 : 1) + (fv < .5f ? 0 : NEEDLE_W);
    dst[y * W + x] = nr::blend565(dst[y * W + x], needle_day_rgb[kc], (uint32_t)al);
  }
  int hx = (int)(FACE_PIVOT_X - HUB_W / 2.0f), hy = (int)(FACE_PIVOT_Y - HUB_H / 2.0f);
  for (int y = 0; y < HUB_H; y++) for (int x = 0; x < HUB_W; x++) { uint8_t al = hub_a[y * HUB_W + x];
    if (al) dst[(hy + y) * W + hx + x] = nr::blend565(dst[(hy + y) * W + hx + x], hub_rgb[y * HUB_W + x], al); }
}
int main() {
  std::vector<uint16_t> face(W * H), a(W * H), b(W * H);
  decode(face_day_rle, sizeof(face_day_rle) / 2, face.data());
  nr::Art n{needle_day_rgb, needle_day_a, NEEDLE_W, NEEDLE_H, NEEDLE_PIVOT_X, NEEDLE_PIVOT_Y}, hub{hub_rgb, hub_a, HUB_W, HUB_H, 0, 0};
  static nr::Renderer<W, H, 2> R; R.begin(FACE_PIVOT_X, FACE_PIVOT_Y, &hub);
  int fails = 0, checks = 0; uint32_t maxVisited = 0;
  // buffer 0 starts as the face (as after the first full copy)
  a = face; R.restore(a.data(), face.data(), 0);
  for (float ang = -115.6f; ang <= 116; ang += 7.3f) {
    checks++;
    R.restore(a.data(), face.data(), 0);
    uint32_t v = R.draw(a.data(), n, ang, 0); if (v > maxVisited) maxVisited = v;
    b = face; reference(b.data(), ang);
    int worst = 0, bad = 0;
    for (int i = 0; i < W * H; i++) for (int k = 0; k < 3; k++) { int d = abs(ch(a[i], k) - ch(b[i], k)); if (d > worst) worst = d; if (d > 24) bad++; }
    if (bad > 40) { printf("FAIL angle %.1f: %d channel values differ by >24 (worst %d)\n", ang, bad, worst); fails++; }
  }
  R.restore(a.data(), face.data(), 0);
  bool same = memcmp(a.data(), face.data(), W * H * 2) == 0; if (!same) { printf("FAIL restore did not return the clean face\n"); fails++; }
  printf("max pixels visited per frame %u (whole screen %d)\n", maxVisited, W * H);
  if (fails) printf("FAILED\n"); else printf("needle_render: %d angle checks + restore check pass\n", checks); return fails;
}
