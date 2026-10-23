# Bench proof of concept: shopping list (rev 2026-10-14)

Goal: a hub, one gauge board (the 2.8" tach) and the control keypad, all running off fake Haltech CAN frames sent from a PC.

| Item | Qty | Approx. price | Link | Why |
|---|---|---|---|---|
| CANable 2.0 USB-to-CAN adapter (Makerbase) | 1 | $17 | https://makerbase3d.com/product/makerbase-canable-v2/ | PC stands in for the Haltech; later sniffs the real bus and sets up the keypad |
| Waveshare SN65HVD230 CAN board (3.3 V) | 2 (+1 spare) | $5 each | https://www.waveshare.com/sn65hvd230-can-board.htm | CAN transceiver for the hub and the tach. Owner has 1 (2026-10-17): needs 1 more before the bench bus can run hub + tach |
| ESP32-S3-DevKitC-1 N16R8 | 1 | $10–15 single, $16–21 2-pack | https://www.amazon.com/DIYmall-ESP32-S3-DevKitC-1-N8R8-Development-ESP32-S3-WROOM-1-Module/dp/B0BSCXHB5S | The hub |
| Waveshare ESP32-S3-LCD-2.8C (non-touch is fine) | 1 | $33–40 | https://www.waveshare.com/esp32-s3-touch-lcd-2.8c.htm | The tach board (includes SH1.0 cables) |
| Blink Marine PKP-2300-SI 6-key CAN keypad | 1 | 204 EUR + VAT/shipping direct (https://shop.blinkmarine.com/product/pkp-2300-si/); $294.99 from a US dealer (https://www.murcal.com/PowerKey-PRO-PKP-2300-SI-Compact-Keypad) | see price | Gauge mode, overlay and trip-reset keys; replaces the stock stalk |
| Amphenol AT06-4S-KIT01 plug kit (plug, AW4S wedgelock, 4 socket contacts) | 1 (2 if you want a spare) | $9.87 | https://www.mouser.com/en/c/connectors/?number%20of%20positions=4%20Position&product=Kits | Mates the keypad's AT04-4P socket; not included with the keypad |
| 12 V DC bench supply (wall adapter, about 1 A) | 1 | $10–15 | any | Powers the keypad; check the supply range in the Blink manual |
| Breadboard, Dupont jumpers, 10k pot, about 1 m of twisted pair, 16–20 AWG wire for the keypad pigtail | 1 kit | $10–15 | any | Dimmer input and CAN wiring |
| 120 ohm resistors (only if termination is missing) | 2 | <$1 | any | Bus termination at the two ends |
| USB-C data cables | 3 | on hand | | Power and programming |
| Park-lamp sense: PC817 optocoupler, 2.2 kohm and 10 kohm resistors, 1N4148 diode | 1 each | <$1 (often in a starter kit) | any | Night mode from the park-lamp feed into hub GPIO2 (2026-10-22); car install, not needed on the bench |
| Dimmer input: 47 kohm and 10 kohm resistors, 1 uF capacitor; possible dummy load (194 bulb or 100 ohm 5 W resistor) | 1 each | <$2 | any | Night brightness from the headlamp-switch dimmer into hub GPIO1 (2026-10-22); the dummy load only if the dimmer is a series rheostat |
| Power latch: 12 V automotive relay (5-pin), 2x 2N2222, 1N4148, second PC817, 10 kohm, 1 kohm, 2.2 kohm, 5 A fuse | 1 set | about $8 | any | Keeps the cluster on about 1.5 s after key-off for the shutdown fade and state save (2026-10-22); car install |
| Buzzer driver: NPN transistor (2N2222 or S8050), 1N4148 diode, 1 kohm resistor | 1 each | <$1 (often in a starter kit) | any | Drives the owner's Star TMX-12S magnetic buzzer from hub GPIO6 at 12 V (2026-10-18) |
| Star TMX-12S buzzer | 1 | on hand | | Alert, low-fuel chime and check-engine buzz |

Estimated total: about $340–420, depending mainly on where the keypad comes from.

Tools: the AT contacts are solid size-16 crimp contacts; Amphenol's datasheet lists the CA-5D12 hand crimper (https://static.chipdip.ru/lib/144/DOC048144005.pdf).

Bring-up order (revised 2026-10-17: membrane keypad for the proof of concept; the Blink is deferred and the knob comes later):
1. PC -> CANable -> hub + tach at 1 Mbit/s; run `tools/bench/fake_haltech.py`.
2. Membrane keypad on hub GPIO8-15; the hub reads the keys (1 temp, 2 fuel, 3 speedo data face, A trip, B boost) and broadcasts gauge states in 0x6A1 and odometer/trip in 0x6A0.

Bus: CANable -> twisted pair -> hub transceiver -> tach transceiver. Terminate only the two ends; check about 60 ohm between CAN H and L with the power off.

Optional swap: use the Waveshare ESP32-P4 3.4C speedo board ($64.99, https://www.waveshare.com/esp32-p4-wifi6-touch-lcd-3.4c.htm) instead of the tach to prove the ESP32-P4 path first.

## Later phase: knob selector (ordered 2026-10-17)
The final selection device is the CrowPanel 1.28" HMI ESP32 rotary display (Meshnology L003045 on Amazon, $38.69), integrated after the keypad proof of concept. Still needed for it:
| Part | Qty | Purpose |
|---|---|---|
| SN65HVD230 3.3 V CAN transceiver board | 1 more | Knob on the CAN bus (I2C connector GPIO38/39 as TWAI TX/RX; verify pinout with a meter) |
| 12 V to 5 V buck, 1 A or more | 1 | Knob power (5 V / 1 A per Elecrow) |
| 3.3 V supply for the transceiver (e.g. a small 5 V to 3.3 V LDO board) | 1 | The knob's connectors carry 5 V, not 3.3 V |
| 1.25 mm 4-pin cable | 1 | Knob I2C connector to the transceiver |
