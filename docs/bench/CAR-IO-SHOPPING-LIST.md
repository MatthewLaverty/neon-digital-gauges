# Neon cluster: car I/O shopping list

Covers four circuits: the park-lamp sense, the dimmer input, the power latch and the buzzer driver. The circuits are from `docs/bench/POC-WIRING.md` in the neon-digital-gauges repo (rev 2026-11-01). The counts are totals across all four circuits; the "Used in" column says where each part goes.

## Checklist

| ✓ | Qty | Part | Spec to ask for / check on the bin | Used in |
|---|---|---|---|---|
| ☐ | 4 | 1N4148 diode | Small-signal, glass, black stripe | Buzzer (1), park-lamp sense (1), latch relay coil (1), ignition sense (1) |
| ☐ | 3 | 2N2222 NPN transistor | TO-92 (S8050 is an OK substitute) | Buzzer driver (1), power latch (2) |
| ☐ | 2 | PC817 optocoupler | 4-pin DIP | Park-lamp sense (1), ignition sense (1) |
| ☐ | 4 | 10 kΩ resistor | 1/4 W | Park-lamp pull-up on GPIO2 (1), dimmer divider (1), latch NPN #1 base (1), ignition pull-up on GPIO7 (1) |
| ☐ | 2 | 2.2 kΩ resistor | 1/4 W | Park-lamp opto LED (1), ignition opto LED (1) |
| ☐ | 2 | 1 kΩ resistor | 1/4 W | Buzzer NPN base (1), latch NPN #2 base (1) |
| ☐ | 1 | 47 kΩ resistor | 1/4 W | Dimmer divider |
| ☐ | 1 | 1 µF capacitor | Ceramic or electrolytic, 16 V or higher (it only sees about 2.5 V) | Dimmer input smoothing, GPIO1 to GND |
| ☐ | 1 | 12 V automotive relay | Bosch-style, pins 30/85/86/87 (a 4- or 5-pin relay works) | Power latch |
| ☐ | 1 | Inline fuse holder + 5 A fuse | Blade type | Power latch, constant-battery feed |

All resistors are ordinary 1/4 W parts. The highest dissipation is the 2.2 kΩ on 14.5 V, at about 0.08 W.

## Only if the dimmer test calls for it

| ✓ | Qty | Part | When |
|---|---|---|---|
| ☐ | 1 | 100 Ω 5 W resistor, OR a 194 bulb + socket | Only if, with the stock cluster unplugged, the dimmer wire stops changing voltage (a series rheostat that needs a load). See step 4 of the dimmer section in `POC-WIRING.md`. |

## Already have

- **Star TMX-12S buzzer:** owned and bench tested.

## Not in the design docs (your call)

These aren't specified anywhere, but you'll likely want them to build the circuits:
- **Board:** perfboard or a small solderable breadboard.
- **Wire:** hookup wire.
- **Connectors:** a way to land the car wires (park-lamp feed, dimmer output, ignition RUN/START, constant battery, ground). Spade terminals, or a small terminal block, are typical.
- **Spares:** a few extra of each small part. They're cheap, and pin-bending mistakes happen.

## Before wiring

- **GPIO21** (the power latch "hold" output) isn't in the bench pin list yet. Confirm it's free on your N16R8 board.
- **Ignition feed:** use RUN/START, not ACC. ACC drops out while cranking.
- **Car wire colours:** the park-lamp, dimmer and ignition wire colours aren't verified. Find each one with a meter using the steps in `POC-WIRING.md`.
