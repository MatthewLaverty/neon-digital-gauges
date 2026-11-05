# Car I/O breadboard build (rev 2026-11-04)

Layout: `breadboard_car_io.png` (from `tools/bench/breadboard_layout.py`). The circuits are the ones in `POC-WIRING.md`. Parts: `CAR-IO-SHOPPING-LIST.md`.

## Power setup
- **Bottom + rail (12 V):** 12 V supply + → 5 A ATM fuse (CES-FHM12) → this rail.
- **Grounds:** 12 V supply − goes to the bottom − rail. Add a wire at column 64 to tie the top − rail to the bottom − rail.
- **VUPN7191 module, bottom jumper:** OFF. Vetco publishes no specs for this module ([Vetco](https://vetco.net/collections/breadboards-and-breadboard-accessories)). I'm assuming it's the common MB102 style, where each side has a 3.3 V / OFF / 5 V jumper.
  - Before you connect the 12 V supply, power the module alone and meter the bottom + rail. It must read 0 V. If it doesn't, pull the module's bottom pins out of the rail. Otherwise 12 V would back-feed its regulator.
- **Module, top jumper:** 3.3 V for stage 1.
- **Rail continuity:** check that each rail is continuous from column 1 to column 65. Some long boards split their rails in the middle.

## Stage 1: no hub, meter only
| Test | Do | Expect |
|---|---|---|
| Park sense | PARK wire (col 7) into the 12 V rail | col 10 drops from 3.3 V to under 0.4 V |
| Ignition sense | IGN wire (col 16) into the 12 V rail | col 20 goes low, the relay clicks, col 60 reads 12 V |
| Hold | IGN in, jumper the top 3.3 V rail to col 48, pull IGN | relay stays on; remove the jumper and it drops |
| Dimmer | DIM wire (col 26) into the 12 V rail | col 30 reads about 2.1 V (12 × 10/57) |
| Buzzer | jumper the 3.3 V rail across to col 28 | buzzer clicks once (DC, no tone) |

## Stage 2: hub connected
- **Hub power:** move the module's top jumper to OFF, then run the hub's 3V3 pin to the top + rail. Never have two 3.3 V sources on that rail.
- **Hub wiring:** hub on USB, GND to the top − rail, signal wires as labeled on the layout. GPIO21 isn't in the bench pin list yet, so confirm it's free on your board first.

## Notes
- **Transistor pin order:** E-B-C order varies between parts. Check the datasheet for your part and rotate it so E, B and C land in the columns shown.
- **Optocoupler pin 1:** it's at the dot. NTE3222 is assumed to share the PC817 pinout, but that's not confirmed; check with a meter's diode test.
- **Off-board wiring:**
  - The relay's spade terminals need 0.25 in female spade connectors or the CES-BRS-006 socket, neither of which is on the list.
  - The fuse holder's 16 AWG leads need tinning or a short solid jumper soldered on to go into the breadboard.
- **Current:** the relay coil and buzzer each draw well under 1 A, so the breadboard is fine for this. Don't run cluster load current through it.
