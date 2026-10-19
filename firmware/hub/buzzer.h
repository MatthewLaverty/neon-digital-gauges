// Buzzer output for the hub (Arduino-ESP32 core 3.x LEDC API). Feed it AlertOutputs.buzzHz / buzzDutyPct.
#pragma once
#include "alerts_config.h"
#ifdef ARDUINO
#include <Arduino.h>
static inline void buzzerBegin() { ledcAttach(BUZZER_PIN, BUZZER_FREQ_HZ, 10); ledcWrite(BUZZER_PIN, 0); }
static inline void buzzerApply(uint32_t hz, uint8_t dutyPct) {
  static uint32_t cur = 0;
  if (!BUZZER_SELF_DRIVE && hz != cur) { ledcChangeFrequency(BUZZER_PIN, hz, 10); cur = hz; }
  ledcWrite(BUZZER_PIN, (uint32_t)dutyPct * 1023u / 100u);   // 50 % = loudest square wave; 100 % = DC (self-drive)
}
#endif
