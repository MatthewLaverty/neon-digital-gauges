# Bench proof of concept: shopping list (2026-10-14)

Goal: a hub and one gauge board (tach, 2.8") running off fake Haltech CAN frames sent from a PC.

| Item | Qty | Approx. price | Link |
|---|---|---|---|
| CANable 2.0 USB-to-CAN adapter (Makerbase) | 1 | $17 | https://makerbase3d.com/product/makerbase-canable-v2/ |
| Waveshare SN65HVD230 CAN board (3.3 V) | 2 (+1 spare) | $5 each | https://www.waveshare.com/sn65hvd230-can-board.htm |
| ESP32-S3-DevKitC-1 N16R8 (hub) | 1 (2-pack) | $15–20 | https://www.amazon.com/DIYmall-ESP32-S3-DevKitC-1-N8R8-Development-ESP32-S3-WROOM-1-Module/dp/B0BSCXHB5S |
| Waveshare ESP32-S3-LCD-2.8C (tach) | 1 | $33–40 | https://www.waveshare.com/esp32-s3-touch-lcd-2.8c.htm |
| Breadboard, Dupont jumpers, 2 tactile buttons, 10k pot, short twisted pair | 1 kit | $10–15 | any |
| 120 ohm resistors (only if termination is missing) | 2 | <$1 | any |
| USB-C data cables | 3 | on hand | |

Estimated total: $85–100.

Optional: swap the tach board for the Waveshare ESP32-P4 3.4C speedo board ($64.99, https://www.waveshare.com/esp32-p4-wifi6-touch-lcd-3.4c.htm) to prove the ESP32-P4 path first.

Bus: CANable -> twisted pair -> hub transceiver -> tach transceiver, 1 Mbit/s, terminated at both ends only.
PC side: `tools/bench/fake_haltech.py` (python-can, slcan) plus SavvyCAN or Cangaroo to watch the bus.
