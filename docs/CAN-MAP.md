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
| Check engine | 0x3E4 | byte 7 bit 7 | flag | 1 = on | 5 Hz | stretch |
| Trip Meter 1 | 0x6F6 | 4-7 | s32 | 1 m | 5 Hz | HUB (odometer + trip source) |

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
| 1 | Gauge | 0 temp, 1 fuel, 2 tach, 3 speedo |
| 2 | Sequence | increments per event, so the hub ignores duplicates |

0x6A1, 10 Hz and on change: gauge states. The speedo data face takes its four values straight from the Haltech frames above (owner, 2026-10-17); the hub only sends which face is shown and the order.
| Byte | Field | Scaling |
|---|---|---|
| 0 | Mode bits | bit0 temp = oil, bit1 fuel = ethanol, bit2 tach = boost, bit3 speedo alternate face, bit4 readout shows TRIP (else ODO) |
| 1 | Brightness | 0-255 |
| 2 | Lighting | bit0 headlamps on (night palette) |
| 3 | Speedo data face order | 0-3 = index of the value on top in the cycle Air, Oil, Speed, Volts; the rest follow in cycle order |
