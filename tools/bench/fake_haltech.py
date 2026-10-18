"""Fake Haltech Nexus CAN stream for bench testing (CANable 2.0, slcan firmware).
pip install python-can pyserial ; python fake_haltech.py COM5   (or /dev/tty.usbmodemXXXX)
IDs and scaling follow docs/PLAN.md. VERIFY them against the Haltech CAN protocol doc before trusting the gauges.
Big-endian, 1 Mbit/s.
0x6F6 Trip Meter 1 (metres, signed 32-bit, bytes 4-7, 5 Hz) is integrated from the fake speed, so the hub's odometer and
trip run on the bench exactly as they will from the real ECU. Fuel level 0x3E2 is 0.1 L and sweeps 0-47.3 L (12.5 gal)
so the 1.6 gal low-fuel point is crossed."""
import sys, time, math, struct, can
port = sys.argv[1] if len(sys.argv) > 1 else 'COM5'
bus = can.interface.Bus(interface='slcan', channel=port, bitrate=1000000)
def send(i, data): bus.send(can.Message(arbitration_id=i, data=data.ljust(8, b'\0'), is_extended_id=False))
t0 = time.time(); trip_m = 0.0; last = t0; n = 0
while True:
    t = time.time() - t0
    rpm = int(1500 + 6000 * (0.5 + 0.5 * math.sin(t * 0.8)))   # sweeps 1500-7500
    kph10 = int(10 * 120 * (0.5 + 0.5 * math.sin(t * 0.3)))      # 0-120 km/h, x0.1
    clt_k10 = int(10 * (273.15 + 60 + 40 * (0.5 + 0.5 * math.sin(t * 0.1))))  # coolant, K x0.1
    fuel10 = int(10 * 47.3 * (0.5 + 0.5 * math.sin(t * 0.05)))  # fuel level, 0.1 L (0-47.3 L)
    cel = 0x80 if int(t) % 10 < 2 else 0                       # 0x3E4 bit 7, on 2 s of every 10
    send(0x360, struct.pack('>H', rpm))
    send(0x370, struct.pack('>H', kph10))
    send(0x3E0, struct.pack('>H', clt_k10))
    send(0x3E2, struct.pack('>H', fuel10))
    send(0x3E4, bytes([cel]))
    # speedo data face inputs: oil pressure (0x361 bytes 2-3, 0.1 kPa abs), wideband 1 (0x368, lambda x1000), battery (0x372, 0.1 V)
    oil_kpa = 100 + 250 * rpm / 7000                                      # ~15-50 psi gauge, follows rpm
    send(0x361, struct.pack('>HH', 0, int(10 * (oil_kpa + 101.3))))
    send(0x368, struct.pack('>H', int(1000 * (1.0 + 0.12 * math.sin(t * 0.7)))))   # lambda 0.88-1.12
    send(0x372, struct.pack('>H', int(10 * (14.1 + 0.2 * math.sin(t * 0.3)))))
    now = time.time(); trip_m += kph10 / 36.0 * (now - last); last = now   # km/h x0.1 -> m/s = x/36
    n += 1
    if n % 10 == 0: send(0x6F6, struct.pack('>ii', 0, int(trip_m)))  # 5 Hz: fuel used cc (0), Trip Meter 1 m
    time.sleep(0.02)                                           # 50 Hz
