"""Fake Haltech Nexus CAN stream for bench testing (CANable 2.0, slcan firmware).
pip install python-can pyserial
python fake_haltech.py COM5                    normal sweep, no alerts
python fake_haltech.py COM5 --scenario afr     forces one alert/lamp condition (list below)
Layouts follow the Haltech ECU Broadcast CAN Protocol (docs/CAN-MAP.md). Big-endian, 1 Mbit/s, all frames 8 bytes.
0x6F6 Trip Meter 1 (metres, s32, bytes 4-7, 5 Hz) is integrated from the fake speed, so the hub odometer and trip run
on the bench as they will from the real ECU. Fuel level 0x3E2 is 0.1 L.
Scenarios (firmware/hub/alerts_config.h thresholds):
  normal      sweeps everything inside the limits; CEL off
  rpm         rpm sweep peaks at 8200 (tach flashes above 7999)
  coolant     coolant 255 F            oiltemp   oil temp 305 F
  volts_low   10.6 V while running     volts_high 16.4 V
  afr         lambda 1.0 (AFR 14.7) above 3000 rpm, with decel-cut flag set on part of each sweep
  oilp        oil pressure 10 psi while running (engine-off key-on first 5 s: rpm 0)
  cel         check engine flag on from t = 5 s (single 1 s buzz)
  lowfuel     fuel 1.5 gal for 15 s, then 1.7 gal (lamp stays on), then 2.0 gal (lamp off)"""
import sys, time, math, struct, argparse, can
ap = argparse.ArgumentParser(); ap.add_argument('port', nargs='?', default='COM5'); ap.add_argument('--scenario', default='normal')
a = ap.parse_args(); sc = a.scenario
bus = can.interface.Bus(interface='slcan', channel=a.port, bitrate=1000000)
def send(i, data): bus.send(can.Message(arbitration_id=i, data=data.ljust(8, b'\0'), is_extended_id=False))
K = lambda f: int(10 * ((f - 32) / 1.8 + 273.15))           # deg F -> 0.1 K
t0 = time.time(); trip_m = 0.0; last = t0; n = 0
while True:
    t = time.time() - t0
    s = 0.5 + 0.5 * math.sin(t * 0.8)
    rpm = int(1500 + (6700 if sc == 'rpm' else 6000) * s)      # 1500-7500 (8200 in 'rpm')
    if sc == 'oilp' and t < 5: rpm = 0
    kph10 = int(10 * 120 * (0.5 + 0.5 * math.sin(t * 0.3)))
    clt_f = 255 if sc == 'coolant' else 150 + 60 * (0.5 + 0.5 * math.sin(t * 0.1))
    oil_f = 305 if sc == 'oiltemp' else 180 + 60 * (0.5 + 0.5 * math.sin(t * 0.1))
    fuel10 = int(10 * 47.3 * (0.5 + 0.5 * math.sin(t * 0.05)))
    if sc == 'lowfuel': fuel10 = 57 if t < 15 else 64 if t < 30 else 76   # 1.5 / 1.7 / 2.0 gal
    lam = 1.0 if sc == 'afr' else (0.82 + 0.1 * math.sin(t * 0.7) if rpm > 3000 else 1.0 + 0.05 * math.sin(t * 0.7))
    decel = sc == 'afr' and math.cos(t * 0.8) < -0.5          # decel-cut flag on the falling part of the sweep
    volts = 10.6 if sc == 'volts_low' else 16.4 if sc == 'volts_high' else 14.1 + 0.2 * math.sin(t * 0.3)
    oil_kpa = 69 if (sc == 'oilp' and rpm) else (0 if rpm == 0 else 100 + 250 * rpm / 7000)
    cel = sc == 'cel' and t > 5
    send(0x360, struct.pack('>H', rpm))
    send(0x370, struct.pack('>H', kph10))
    send(0x3E0, struct.pack('>HHHH', K(clt_f), 0, 0, K(oil_f)))                # coolant 0-1, oil temp 6-7
    send(0x3E2, struct.pack('>H', fuel10))
    send(0x3E4, bytes([0, 0x10 if decel else 0, 0, 0, 0, 0, 0, 0x80 if cel else 0]))  # byte1 bit4 decel cut, byte7 bit7 CEL
    send(0x361, struct.pack('>HH', 0, int(10 * (oil_kpa + 101.3))))
    send(0x368, struct.pack('>H', int(1000 * lam)))
    send(0x372, struct.pack('>H', int(10 * volts)))
    now = time.time(); trip_m += kph10 / 36.0 * (now - last); last = now
    n += 1
    if n % 10 == 0: send(0x6F6, struct.pack('>ii', 0, int(trip_m)))
    time.sleep(0.02)
