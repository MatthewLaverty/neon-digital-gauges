# Carrier board: requirements (rev 0, 2026-11-18)

Status: requirements only. Nothing here has been built or tested yet. The perfboard build in the car (step 3 of the in-car plan) checks these requirements before the KiCad rev A board is designed. Facts with a source carry a link. Everything else is a design choice or an inference, and is labelled as one.

## 1. Hard rules (owner)

- **No hand-modified cables.** Every cable between the carrier and a board is either an unmodified off-the-shelf cable or a harness crimped with the correct contacts into the correct housing. Any VBUS cut, power selection or signal routing happens in copper on the carrier PCB, never in a cable.
- **USB stays in the car permanently** for recovery (PLAN §4.8). Wi-Fi OTA is the normal update path (PLAN §4.7).
- **No 5 V from the laptop or the hub ever reaches a board.** The car's 5 V is never connected to the hub or the laptop.

## 2. Blocks on the board

| Block | Contents | Notes |
|---|---|---|
| 12 V input | fuse, reverse-polarity protection, load-dump TVS diode, bulk capacitor | Whether the 1999 Neon suppresses load dump is not verified. Assume it doesn't. |
| Power latch | relay (constant battery → 12 V switched), 2× 2N2222 driver, flyback 1N4148 | Same circuit as the breadboard: `docs/bench/POC-WIRING.md` "Power latch", `docs/bench/BREADBOARD-CAR-IO.md` |
| 5 V buck | Pololu D36V28F5 footprint (5 V, 3.2 A, 6–50 V input, reverse protection to −40 V, per [Pololu](https://www.pololu.com/product/3782)) | A module, not a discrete buck, for rev A |
| Car inputs | park-lamp and RUN/START sense (opto + 2.2k/10k), dimmer divider + RC filter (47k/10k/1 µF), buzzer driver | Values copied from the breadboard. A dummy load for the dimmer only if the car measurement says it's needed. |
| Hub MCU | ESP32-S3 (socketed DevKitC or a module footprint) | Choose before layout. A DevKitC socket is easier to repair. |
| Hub CAN | SN65HVD230 transceiver + 120 Ω termination (jumper) | The other boards keep their own transceiver boards next to each screen |
| USB service hub | 7-port hub IC, upstream access-port connector, one downstream port per board | Section 4 |
| Ground | single-point star at the carrier, one chassis ground lead | |

## 3. Power budget

| Load | Current at 5 V | Basis |
|---|---|---|
| Speedo 4C, tach 2.8C, 5", knob, hub | 0.3–0.5 A each, so 1.5–2.5 A total | Estimate. Measure each board with a USB power meter (in-car plan step 1) |
| Buck rating | 3.2 A | [Pololu](https://www.pololu.com/product/3782) |

At the high estimate, headroom is about 0.7 A. If the measured total is above about 2.6 A (80 % of the rating, a margin I chose), move to a larger buck or split the rail.

## 4. USB service bus

### Hub IC

Candidate: Microchip USB2517I. It has 7 downstream ports, needs a 3.3 V supply, and comes in a 64-pin 9 × 9 mm QFN ([Microchip datasheet](https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ProductDocuments/DataSheets/USB2517-USB2517i-Data-Sheet-00001598C.pdf)). Use the "I" part, rated −40 to +85 °C. The plain USB2517 is rated 0 to 70 °C only (same datasheet). The USB D+/D− terminations and pull-ups are inside the chip, so the downstream data pins connect straight to the connectors ([Microchip design checklist](https://ww1.microchip.com/downloads/en/DeviceDoc/USB2517-Hardware-Design-Checklist-00004211.pdf)). The QFN isn't practical to hand-solder, so plan on factory assembly for this part. Five ports are needed (hub, speedo, tach, 5", knob), which leaves two spare.

### Hub power

- The hub IC and its 3.3 V regulator are powered only from the upstream (laptop) VBUS. With no laptop connected, the hub is off.
- VBUS_DET goes to the upstream VBUS, per the datasheet's VBUS-detect pin, so the hub only attaches when a laptop is present.
- No copper connects the upstream VBUS to the car's 5 V rail.

### Per-port VBUS selection (replaces cable cutting)

Each downstream port has a footprint for a 0 Ω resistor or a solder jumper. It selects one of two options:

| Setting | Port VBUS pin | Used for |
|---|---|---|
| **OPEN** (default) | not connected | Boards powered from their own 5 V harness pin |
| **CAR 5V** | car 5 V rail through a resettable fuse (about 0.75–1 A hold, to be sized after measurement) | Boards whose only power input is the USB connector (the CrowPanel knob, and any board whose USB chip needs VBUS present to enumerate) |

In neither setting does the hub's or the laptop's VBUS reach a port. Any per-port power switch the hub IC asks for (PRTPWR) is not used for the CAR 5V setting.

### Connectors and cables (all off the shelf)

- **Access port:** an off-the-shelf panel-mount USB extension, from the lower dash or glovebox to the carrier's upstream header. The laptop always connects through the ADuM3160 isolator.
- **Downstream:** USB-A receptacles on the carrier. Each board connects with an unmodified, retail USB-A cable: USB-A to USB-C for the Waveshare boards and the hub DevKitC, and the stock Elecrow "MX1.25 to USB" cable for the knob.
- **Knob:** its MX1.25 plug carries both power and USB, so its port is set to **CAR 5V**. The stock cable then powers the knob and carries its data, with no changes. Meter-check the stock cable's pin order before the first plug-in; there is no standard.

### Bench checks before rev A (unverified until done)

1. Hub unpowered, boards on car 5 V: measure the 5 V current with and without each USB link, and confirm every board boots normally. Each board's D+ pull-up may leak a few mA into the unpowered hub. That's an inference, not verified.
2. For each board, with its port set to OPEN: plug in the laptop and confirm the board enumerates and accepts a flash. If one doesn't, set its port to CAR 5V.
3. Force download mode with BOOT + RESET on each board through the hub. My understanding is that a bad firmware can block automatic download mode; this isn't tested on these boards.

## 5. Harnesses (crimped, not modified)

| Harness | Wires | Connector |
|---|---|---|
| Carrier → each screen + its CAN transceiver | 5 V, GND, CAN H, CAN L | Positive-latching 4-way. Candidate: Molex Micro-Fit 3.0 (choice not verified for vibration) |
| Car → carrier | constant 12 V, ground, RUN/START, park lamp, dimmer | Sealed automotive connector. Candidate: Deutsch DT/DTM (choice not verified) |
| Knob CAN | knob 4-pin 1.25 mm I2C plug → LDO → CAN board #3 | Stock-style MX1.25 cable as in `docs/bench/POC-WIRING.md` |

## 6. Breadboard to carrier

| Breadboard item | Carrier equivalent |
|---|---|
| 5 A ATM fuse in CES-FHM12 inline holder | On-board fuse holder, plus the inline fuse at the battery tap |
| Bench 12 V supply | Car constant 12 V through the latch relay |
| VUPN7191 3.3/5 V module | Pololu D36V28F5 (5 V). The hub's own regulator supplies 3.3 V. |
| Pot standing in for the dimmer | Dimmer wire from the car |
| Powered USB hub + isolator on the bench | On-board USB2517I service hub (section 4) + the same isolator at the laptop |
| USB CAN adapter (fake Haltech) | Removed. The Haltech is on the bus. |

## 7. Open items

- Measure each board's current (sets the buck and fuse sizes).
- Choose the 5" board (Waveshare S3-Touch-LCD-5 with the R21 mod, or the Guition JC8048W550C).
- Confirm GPIO21 is free on the hub for the latch.
- Check each board's power input: a 5 V header pin, or USB-C only (that sets its port's VBUS setting).
- Check whether the car needs a dummy load on the dimmer circuit.
- Confirm the connector series and contacts before ordering.
- Pick the TVS diode and its rating once the car's charging system is known.
