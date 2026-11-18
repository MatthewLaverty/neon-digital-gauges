# Bench checkout before connecting the Mac (rev 2026-11-18)

Goal: prove that no 12 V or 5 V can reach anything wired to a hub pin or a USB cable. Work through the steps in order. Don't move to the next step until every check in the current one passes. Column and row references are from `breadboard_car_io.png`.

## Step 0: check the parts before they go in
- **Resistors:** meter every resistor before inserting it. Expected readings:

  | Value | Should read |
  |---|---|
  | 10k | 9.9–10.1k |
  | 2.2k | 2.18–2.22k |
  | 1k | 0.99–1.01k |
  | 47k | 46.5–47.5k |

  1 % metal-film parts have 5 colour bands: 10k is brown-black-black-red, 2.2k red-red-black-brown, 1k brown-black-black-brown, 47k yellow-violet-black-red. Trust the meter over the bands.
- **Diodes:** in diode mode, red lead on the anode (no stripe), expect about 0.6–0.7 V. Reversed, it should read OL.
- **Transistors:** in diode mode, red lead on B, black on E, expect about 0.65 V. Red on B, black on C, also about 0.65 V. Every other pair should read OL. This also tells you which leg is B.
- **Optocouplers:** in diode mode, pin 1 (+) to pin 2 should read about 1.0–1.2 V, and OL reversed. That confirms which end is pin 1.

## Step 1: everything off, nothing connected
No supplies, no module power, hub wires unplugged. Pull out the PARK and IGN stand-in wires. Dimmer: the pot replaces the orange DIM wire (pot ends on the 12 V and GND rails, wiper in col 26). For this step, lift the pot's 12 V lead out of the rail. Otherwise the pot puts about 10k between 12 V and GND and gives the 12 V rail a path to col 30.

| Measure between | Expect | If wrong |
|---|---|---|
| 12 V rail and 3.3 V rail | OL (open) | **STOP:** a wire or part bridges the rails |
| 12 V rail and GND rail | OL or over 100k | short to ground |
| 3.3 V rail and GND rail | OL or over 100k | short to ground |
| 12 V rail and col 10, 20, 28, 30, 48 (each) | OL | **STOP:** 12 V can reach a hub pin |
| 3.3 V rail and col 10, 20 | 10k each (pull-ups) | wrong resistor or wrong column |
| col 30 and GND | climbs to 10k (the cap charges first) | 10k missing or misplaced |
| col 26 and col 30 | about 47k plus part of the pot (12 V lead lifted) | |
| col 28 and col 32 | 1k | |
| col 48 and col 51 | 1k | |
| relay 85 and 86 at the relay | coil resistance, tens of ohms | |
| top GND rail and bottom GND rail | 0 Ω (the column-64 tie) | |
| each rail, col 1 and col 65 | 0 Ω | the rail is split in the middle |

## Step 2: power on, no hub, no Mac
- **Pot:** put its 12 V lead back in the rail.
- **Supplies:** plug the power module into a phone charger, not the Mac. Turn on the 12 V supply. Meter everything to GND.
- **Rails:** top + should read 3.3 V (±0.1), bottom + 12 V. Module powered alone, before the 12 V supply is on: bottom + reads 0 V.
- **Signal columns:** they must stay between 0 and 3.4 V in every stand-in state. Anything above 3.4 V means **STOP**.

  | Column | Stand-in out | Stand-in in |
  |---|---|---|
  | 10 (GPIO2) | 3.3 V | under 0.4 V (PARK in) |
  | 20 (GPIO7) | 3.3 V | under 0.4 V (IGN in); relay clicks, col 60 = 12 V |
  | 30 (GPIO1) | pot at min: 0 V | pot at max: about 2.1 V; it should change smoothly in between |
  | 28 (GPIO6) | about 0 V | jumper 3.3 V to col 28: buzzer clicks |
  | 48 (GPIO21) | about 0 V | jumper 3.3 V to col 48 with IGN in, then pull IGN: relay holds |
- **Warm parts:** touch-test after a minute. The relay coil may be warm; nothing else should be.

## Step 3: CAN bus, powered off
- **CAN H to CAN L:** with all boards connected, expect about 60 Ω. About 120 Ω means one terminator is missing; about 40 Ω means a third terminator.
- **CAN H to GND and CAN L to GND:** should be well over 1k (no short).
- **Each CAN board's 3V3 pin to GND:** should not be a short.
- **Knob LDO:** power the knob from a charger and check that the LDO output reads 3.3 V before wiring it to CAN board #3's 3V3 pin. The knob connector carries 5 V, which would damage the transceiver.
- **TX/RX:** CTX goes to the ESP32's TX and CRX to its RX. These aren't crossed.

## Step 4: hub on a charger, then the Mac
- **Flash first:** flash each board with only its USB cable connected and nothing wired to it.
- **Charger run:** wire the hub to the breadboard, power it from a phone charger and repeat the Step 2 table. Stage 2: the module's top jumper is OFF and the hub's 3V3 feeds the top + rail.
- **Then the Mac:** connect through a USB isolator (ADuM4160-based; it supports 12 Mbps full speed). For the ESP32-S3, CANable and knob, its full-speed limit is fine. Without one, the Mac's ground is tied to the 12 V supply's ground through every USB cable.
