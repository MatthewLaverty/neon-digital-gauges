# CAN Map

Bus: Haltech CAN, 1 Mbit/s, 11-bit IDs, big-endian. Termination 120 ohm at the Nexus and at the hub only.
Source: Haltech CAN Broadcast Protocol V2.35. Re-verify against the protocol version on your NSP firmware.

## Haltech broadcast (read-only for gauges)
| Channel | ID | Bytes | Type | Scaling | Rate | Used by |
|---|---|---|---|---|---|---|
| Engine RPM | 0x360 | 0-1 | u16 | 1 RPM | 50 Hz | TACH |
| Oil pressure | 0x361 | 2-3 | u16 | 0.1 kPa abs; gauge = x/10 - 101.3 | 50 Hz | stretch |
| Vehicle speed | 0x370 | 0-1 | u16 | 0.1 km/h | 20 Hz | SPEEDO cross-check |
| Battery voltage | 0x372 | 0-1 | u16 | 0.1 V | 10 Hz | stretch |
| Coolant temp | 0x3E0 | 0-1 | u16 | 0.1 K; C = x/10 - 273.15 | 5 Hz | TEMP |
| Oil temp | 0x3E0 | 6-7 | u16 | 0.1 K | 5 Hz | TEMP (alt) |
| Ethanol % | 0x3E1 | 4-5 | u16 | 0.1 % | 5 Hz | FUEL (alt) |
| Fuel level | 0x3E2 | 0-1 | u16 | 0.1 L | 5 Hz | FUEL |
| Check engine | 0x3E4 | byte 7 bit 7 | flag | 1 = on | 5 Hz | stretch |

## Custom hub frame (proposed; confirm no ID collision on your bus)
ID 0x6A0, 10 Hz, transmitted by hub only.
| Byte | Field | Scaling |
|---|---|---|
| 0-1 | Speed (from VSS) | 0.1 mph |
| 2-5 | Trip distance (optional) | 0.1 mi (u32) |
| 6 | Mode bits | bit0 TEMP alt (oil), bit1 FUEL alt (ethanol) |
| 7 | Brightness | 0-255 |
