# Bench proof of concept: shopping list (rev 2026-10-14)

Goal: a hub, one gauge board (the 2.8" tach) and the control keypad, all running off fake Haltech CAN frames sent from a PC.

| Item | Qty | Approx. price | Link | Why |
|---|---|---|---|---|
| CANable 2.0 USB-to-CAN adapter (Makerbase) | 1 | $17 | https://makerbase3d.com/product/makerbase-canable-v2/ | PC stands in for the Haltech; later sniffs the real bus and sets up the keypad |
| Waveshare SN65HVD230 CAN board (3.3 V) | 2 (+1 spare) | $5 each | https://www.waveshare.com/sn65hvd230-can-board.htm | CAN transceiver for the hub and the tach |
| ESP32-S3-DevKitC-1 N16R8 | 1 | $10–15 single, $16–21 2-pack | https://www.amazon.com/DIYmall-ESP32-S3-DevKitC-1-N8R8-Development-ESP32-S3-WROOM-1-Module/dp/B0BSCXHB5S | The hub |
| Waveshare ESP32-S3-LCD-2.8C (non-touch is fine) | 1 | $33–40 | https://www.waveshare.com/esp32-s3-touch-lcd-2.8c.htm | The tach board (includes SH1.0 cables) |
| Blink Marine PKP-2300-SI 6-key CAN keypad | 1 | 204 EUR + VAT/shipping direct (https://shop.blinkmarine.com/product/pkp-2300-si/); $294.99 from a US dealer (https://www.murcal.com/PowerKey-PRO-PKP-2300-SI-Compact-Keypad) | see price | Gauge mode, overlay and trip-reset keys; replaces the stock stalk |
| Amphenol AT06-4S-KIT01 plug kit (plug, AW4S wedgelock, 4 socket contacts) | 1 (2 if you want a spare) | $9.87 | https://www.mouser.com/en/c/connectors/?number%20of%20positions=4%20Position&product=Kits | Mates the keypad's AT04-4P socket; not included with the keypad |
| 12 V DC bench supply (wall adapter, about 1 A) | 1 | $10–15 | any | Powers the keypad; check the supply range in the Blink manual |
| Breadboard, Dupont jumpers, 10k pot, about 1 m of twisted pair, 16–20 AWG wire for the keypad pigtail | 1 kit | $10–15 | any | Dimmer input and CAN wiring |
| 120 ohm resistors (only if termination is missing) | 2 | <$1 | any | Bus termination at the two ends |
| USB-C data cables | 3 | on hand | | Power and programming |

Estimated total: about $340–420, depending mainly on where the keypad comes from.

Tools: the AT contacts are solid size-16 crimp contacts; Amphenol's datasheet lists the CA-5D12 hand crimper (https://static.chipdip.ru/lib/144/DOC048144005.pdf).

Bring-up order:
1. PC -> CANable -> hub + tach at 1 Mbit/s; run `tools/bench/fake_haltech.py`.
2. Keypad alone on the CANable: change its bit rate from the default 125 kbit/s to 1 Mbit/s (object 2010h) and pick a node ID.
3. Put the keypad on the 1 Mbit/s bench bus; the hub reads key presses, drives the key LEDs, and broadcasts gauge modes in 0x6A1.

Bus: CANable -> twisted pair -> hub transceiver -> keypad -> tach transceiver. Terminate only the two ends; check about 60 ohm between CAN H and L with the power off.

Optional swap: use the Waveshare ESP32-P4 3.4C speedo board ($64.99, https://www.waveshare.com/esp32-p4-wifi6-touch-lcd-3.4c.htm) instead of the tach to prove the ESP32-P4 path first.
