# CAN Map

Bus: Haltech CAN, 1 Mbit/s, 11-bit IDs, big-endian. Termination 120 ohm at the Nexus and at the hub only.
Source: Haltech CAN Broadcast Protocol V2.35. Re-verify against the protocol version on your NSP firmware.

## Haltech broadcast (read-only for gauges)
| Channel | ID | Bytes | Type | Scaling | Rate | Used by |
|---|---|---|---|---|---|---|
| Engine RPM | 0x360 | 0-1 | u16 | 1 RPM | 50 Hz | TACH |
| Oil pressure | 0x361 | 2-3 | u16 | 0.1 kPa abs; gauge kPa = x/10 - 101.3; psi = kPa x 0.145038 | 50 Hz | SPEEDO data face (Oil) |
| Wideband Sensor 1 | 0x368 | 0-1 | u16 | lambda = x/1000; shown as AFR = lambda x 14.7 | 20 Hz | SPEEDO data face (Air) |
| Vehicle speed | 0x370 | 0-1 | u16 | 0.1 km/h | 20 Hz | SPEEDO (primary; VSS wired to the Haltech) and data face (Speed, mph) |
| Battery voltage | 0x372 | 0-1 | u16 | 0.1 V | 10 Hz | SPEEDO data face (Volts) |
| Coolant temp | 0x3E0 | 0-1 | u16 | 0.1 K; C = x/10 - 273.15 | 5 Hz | TEMP |
| Oil temp | 0x3E0 | 6-7 | u16 | 0.1 K | 5 Hz | TEMP (alt) |
| Ethanol % | 0x3E1 | 4-5 | u16 | 0.1 % | 5 Hz | FUEL (alt) |
| Fuel level | 0x3E2 | 0-1 | u16 | 0.1 L | 5 Hz | FUEL |
| Decel Cut Active | 0x3E4 | byte 1 bit 4 | flag | 1 = on | 5 Hz | HUB (blocks the AFR alert during fuel cut) |
| Check Engine Light | 0x3E4 | byte 7 bit 7 | flag | 1 = on | 5 Hz | HUB (1 s buzz on the rising edge) and FUEL (check-engine lamp, relayed in 0x6A3) |
| Trip Meter 1 | 0x6F6 | 4-7 | s32 | 1 m | 5 Hz | HUB (odometer + trip source) |

Byte positions for 0x3E0, 0x361, 0x368, 0x372 and both 0x3E4 flags were re-checked on 2026-10-18 against the [Haltech ECU Broadcast CAN Protocol PDF](https://support.haltech.com/portal/api/kbArticles/309315000127455298/locale/en/attachments/8whone12beb10b56646c7893d210fa06b2b86/content?portalId=edbsndab83bda6a605a18494b81368a73ed74e00f5941b9c7dc264955a9257f1b8067&inline=true). The broadcast carries the CEL flag, not the trouble codes themselves. Haltech's CEL setup has a "Haltech CAN Supported Dash" option that enables CEL display on a CAN dash ([Haltech: Check Engine Light Wiring](https://support.haltech.com/portal/en/kb/articles/cel-wiring)); enable it in NSP and confirm the bit toggles on the bench sniffer before relying on it.

Trip Meter 1 and the 0x370 speed scaling are confirmed in the [Haltech ECU Broadcast CAN Protocol v2.0](https://support.haltech.com/portal/en/kb/articles/haltech-can-ecu-broadcast-protocol) (big-endian; Nexus firmware 1.25 or later for full support). That document does not say whether Trip Meter 1 survives an ECU power cycle or when it resets, so the hub treats it as a counter that can restart at any time (see PLAN, odometer logic).

## Custom hub frames (proposed; confirm no ID collision on your bus)
Transmitted by the hub only. Supersedes the earlier 0x6A0 layout (speed from VSS), since speed now comes from 0x370.

0x6A0, 10 Hz: distances for the tach readout.
| Byte | Field | Scaling |
|---|---|---|
| 0-3 | Odometer | u32, 0.1 mi (shown without tenths) |
| 4-7 | Trip | u32, 0.1 mi, 0.0-9999.9 then wraps to 0 |

0x6A2, on event (PROPOSED, 2026-10-17): knob selector intents, transmitted by the knob only. The hub applies them exactly like keypad presses and answers with 0x6A1.
| Byte | Field | Scaling |
|---|---|---|
| 0 | Event | 1 = tap, 2 = hold (2 s) |
| 1 | Stop | 0 temp, 1 fuel, 2 tach, 3 ODO/TRIP, 4 speedo |
| 2 | Sequence | increments per event, so the hub ignores duplicates |

0x6A1, 10 Hz and on change: gauge states. The speedo data face takes its four values straight from the Haltech frames above (owner, 2026-10-17); the hub only sends which face is shown and the order.
| Byte | Field | Scaling |
|---|---|---|
| 0 | Mode bits | bit0 temp = oil, bit1 fuel = ethanol, bit2 tach = boost, bit3 speedo alternate face, bit4 readout shows TRIP (else ODO) |
| 1 | Brightness | 0-255 |
| 2 | Lighting / power | bit0 park lamps on (night palette, `firmware/hub/park_lamp.h`); bit1 shutdown: fade to black (2026-10-22); bit2 startup art go (2026-10-22) |
| 3 | Speedo data face order | 0-3 = index of the value on top in the cycle Air, Oil, Speed, Volts; the rest follow in cycle order |
| 4 | Selection cue (PROPOSED 2026-10-22) | stop index in `select_order` being cued, 0xFF = none (`docs/BEHAVIOR.md` section 1) |
| 5 | Cue sequence | increments on every cue change, so screens restart the pulse together |

0x6A4, at boot and 1 Hz (PROPOSED, 2026-10-22): display settings from `config/cluster-config.md`. Screens keep the last values in their own flash, so they are right at the next power-up even before the hub speaks.
| Byte | Field | Scaling |
|---|---|---|
| 0 | Peak brightness, tach | 0-255 |
| 1 | Peak brightness, speedo | 0-255 |
| 2 | Peak brightness, 5" (temp + fuel) | 0-255 |
| 3 | Peak brightness, knob | 0-255 |
| 4 | Startup art length | 0.1 s (20 = 2.0 s); 0 = no art |
| 5 | Startup to gauges | 0.1 s |
| 6 | Shutdown fade | 0.1 s |
| 7 | Knob sleep | 1 s (15) |

Still to place (needs a second frame or byte reuse): center_gauge (speedo/tach), startup_art_screen, cue_pulse_ms. 0x6A4 is full at 8 bytes, so these go in a 0x6A5 settings frame when the hub firmware is written.

0x6A3, 10 Hz and on every change (PROPOSED, 2026-10-18): alerts and lamps, transmitted by the hub only. The hub evaluates every rule in `firmware/hub/alerts_config.h`, forces the face in 0x6A1, and sends one shared flash phase so all gauges and the buzzer flash together.
| Byte | Field | Scaling |
|---|---|---|
| 0 | Flashing gauges | bit0 temp, bit1 fuel, bit2 speedo, bit3 tach |
| 1 | Flash phase | bit0 = 1: paint the background red now (3 Hz, sent on every edge) |
| 2 | Lamps | bit0 low fuel (pump + arrow yellow), bit1 check engine (engine icon yellow) |
| 3 | Rule bits | bit i = rule i in ALERT_RULES tripped (diagnostics) |
| 4 | Sequence | increments per frame |
