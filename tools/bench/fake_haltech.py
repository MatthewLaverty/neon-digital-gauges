"""Fake Haltech Nexus CAN stream for bench testing (CANable 2.0, slcan firmware).
pip install python-can pyserial ; python fake_haltech.py COM5   (or /dev/tty.usbmodemXXXX)
IDs and scaling follow docs/PLAN.md. VERIFY them against the Haltech CAN protocol doc before trusting the gauges.
Big-endian, 1 Mbit/s."""
import sys, time, math, struct, can
port = sys.argv[1] if len(sys.argv) > 1 else 'COM5'
bus = can.interface.Bus(interface='slcan', channel=port, bitrate=1000000)
def send(i, data): bus.send(can.Message(arbitration_id=i, data=data.ljust(8, b'\0'), is_extended_id=False))
t0 = time.time()
while True:
    t = time.time() - t0
    rpm = int(1500 + 6000 * (0.5 + 0.5 * math.sin(t * 0.8)))   # sweeps 1500-7500
    kph10 = int(10 * 120 * (0.5 + 0.5 * math.sin(t * 0.3)))      # 0-120 km/h, x0.1
    clt_k10 = int(10 * (273.15 + 60 + 40 * (0.5 + 0.5 * math.sin(t * 0.1))))  # coolant, K x0.1
    fuel10 = int(10 * 100 * (0.5 + 0.5 * math.sin(t * 0.05)))   # fuel level, x0.1
    cel = 0x80 if int(t) % 10 < 2 else 0                       # 0x3E4 bit 7, on 2 s of every 10
    send(0x360, struct.pack('>H', rpm))
    send(0x370, struct.pack('>H', kph10))
    send(0x3E0, struct.pack('>H', clt_k10))
    send(0x3E2, struct.pack('>H', fuel10))
    send(0x3E4, bytes([cel]))
    time.sleep(0.02)                                           # 50 Hz
