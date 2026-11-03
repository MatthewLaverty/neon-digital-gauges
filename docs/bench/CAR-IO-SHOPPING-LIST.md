# Neon cluster: car I/O shopping list (Vetco SKUs)

Covers four circuits: the park-lamp sense, the dimmer input, the power latch and the buzzer driver. The counts are totals across all four circuits (circuits from `docs/bench/POC-WIRING.md`). SKUs and prices are from vetco.net as of 2026-11-03.

Vetco's site shows "Quantity selected exceeds current stock" on many small parts. That doesn't say whether the store bins are empty, so call before you go if a trip depends on it (425-641-7275, from the Vetco site).

## Checklist

| ✓ | Qty | Part | Vetco listing | SKU | Each | Line | Used in |
|---|---|---|---|---|---|---|---|
| ☐ | 4 | 1N4148 diode | [1N4148 / 1N4150 / 1N914 Si Diode - NTE519](https://vetco.net/products/nte519_1n4148_-_1n4150_-_1n914_si_diode_100v_2a_-_nte519) | NTE519 | $0.85 | $3.40 | Buzzer, park-lamp sense, relay coil, ignition sense |
| ☐ | 3 | 2N2222 NPN | [2N2222 NPN Transistor - NTE123A](https://vetco.net/collections/general-purpose-transistors) | NTE123A | $2.95 | $8.85 | Buzzer driver (1), power latch (2) |
| ☐ | 2 | Optocoupler, 4-pin DIP (PC817 role) | [Optoisolator with NPN Output 4-Pin DIP - NTE3222](https://vetco.net/products/nte3222_optoisolator_with_npn_output_4-pin_dip_-_nte3222) | NTE3222 | $1.98 | $3.96 | Park-lamp sense, ignition sense |
| ☐ | 4 | 10 kΩ 1/4 W | [10K Ohm 1/4 Watt Resistor](https://vetco.net/products/nte-qw310_10k_ohm_1-4_watt_resistor) | NTE-QW310 | $0.29 | $1.16 | GPIO2 and GPIO7 pull-ups, dimmer divider, latch NPN #1 base |
| ☐ | 2 | 2.2 kΩ 1/4 W | [2.2K Ohm 1/4 Watt Resistor](https://vetco.net/products/nte-qw222_2-2k_ohm_1-4_watt_resistor) | NTE-QW222 | $0.29 | $0.58 | One per optocoupler LED |
| ☐ | 2 | 1 kΩ 1/4 W | [1K Ohm 1/4 Watt Resistor](https://vetco.net/products/nte-qw210_1k_ohm_1-4_watt_resistor) | NTE-QW210 | $0.29 | $0.58 | Buzzer NPN base, latch NPN #2 base |
| ☐ | 1 | 47 kΩ 1/4 W | [47K Ohm 1/4 Watt Resistor](https://vetco.net/products/nte-qw347_47k_ohm_1-4_watt_resistor) | NTE-QW347 | $0.29 | $0.29 | Dimmer divider |
| ☐ | 1 | 1 µF capacitor | [1uF 50 Volt Electrolytic Capacitor](https://vetco.net/products/nte-vht1m50_1uf_50_volt_electrolytic_capacitor) | VUPN2589 | $0.79 | $0.79 | Dimmer smoothing, GPIO1 to GND (polarized: + to GPIO1, - to GND) |
| ☐ | 1 | 12 V automotive relay | [12VDC 40A SPDT Automotive Relay](https://vetco.net/collections/12v-dc-relays) | CES-SPDT40P | $6.39 | $6.39 | Power latch |
| ☐ | 1 | Inline mini blade fuse holder | [Inline Mini Blade Fuse Holder (ATM), Weatherproof](https://vetco.net/collections/fuse-blocks-holders) | CES-FHM12 | $2.99 | $2.99 | Power latch, constant-battery feed |
| ☐ | 1 | 5 A mini blade fuse | [ATM Mini Blade Fuse - 5A, 32V, Fast Blow](https://vetco.net/products/vupn1644_atm_mini_blade_fuse_-_5a_32v_fast_blow) | VUPN1644 | $1.19 | $1.19 | Goes in the holder above |

**Total: about $30.18** before tax.

## Optional

| ✓ | Qty | Part | Vetco listing | SKU | Each | When |
|---|---|---|---|---|---|---|
| ☐ | 1 | Relay socket with leads | [40A Automotive Relay Socket](https://vetco.net/collections/relay-sockets) | CES-BRS-006 | $4.99 | Saves crimping onto the relay's spade terminals |
| ☐ | 1 | 100 Ω power resistor | [100 Ohm 10 Watt Resistor](https://vetco.net/collections/10-watt-resistors) | NTE-10W110 | $1.45 | Only if the dimmer needs a dummy load (step 4 of the dimmer section). Vetco shows no 100 Ω 5 W part; 10 W is fine, just larger. |
| ☐ | 1 | Resistor kit instead of loose resistors | [1000 Resistors kit 25 Values E3 1/4W](https://vetco.net/products/vupn1858_1000_resistors_kit_25_values_e3_1-4w) | VUPN1858 | $19.95 | Has 40 each of 1K, 2.2K, 10K and 47K, among 25 values ([kit contents](https://vetco.net/products/vupn1858_1000_resistors_kit_25_values_e3_1-4w)). Worth it if the loose resistor bins are empty. |

## Substitutions to know

- **Optocoupler:** Vetco doesn't list a PC817. NTE3222 is their only single-channel 4-pin DIP with an NPN output. Its cross-reference list is PS2501-1 and SFH615A-1/-2/-3, not PC817 ([Vetco](https://vetco.net/products/nte3222_optoisolator_with_npn_output_4-pin_dip_-_nte3222)). Those parts generally use the same pinout as the PC817 (1 anode, 2 cathode, 3 emitter, 4 collector), but that's my inference: Vetco's page gives no pinout. Check the NTE3222 datasheet, or the pin 1 dot and a meter's diode test, before soldering.
- **Transistor:** VET123AP ($1.69) lists 2N3904 / BC547 / PN2222 / 2N4401 and is a cheaper option ([Vetco](https://vetco.net/collections/general-purpose-transistors)). Any of those is fine for these small loads. The catch is the pin order: it varies between these parts, so check the E/B/C order on the actual part before wiring.
- **Relay:** the CES-SPDT40P is listed as an automotive SPDT relay, but the page doesn't state the pin numbering. Look for 30/85/86/87 (and 87a) molded on the relay body before buying.
- **Fuse:** Vetco's blade fuses are all mini (ATM) size ([Vetco](https://vetco.net/collections/automotive-blade-fuses)). That's why the holder is the mini CES-FHM12, not the standard-size CES-FH12C.

## Already have

- **Star TMX-12S buzzer.**

## Not in the design docs (your call)

These aren't specified anywhere: perfboard, hookup wire, and terminals for the car wires (park-lamp feed, dimmer output, ignition RUN/START, constant battery, ground). Also worth grabbing a few spares of the small parts.

## Before wiring

- **GPIO21:** confirm it's free on your N16R8 board. It's the power latch "hold" output and isn't in the bench pin list yet.
- **Ignition feed:** use RUN/START, not ACC, which drops out while cranking.
- **Car wires:** find them with a meter using the steps in `POC-WIRING.md`. The colours aren't verified.
