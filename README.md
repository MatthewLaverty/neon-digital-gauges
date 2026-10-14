# neon-digital-gauges

Stock-look round digital gauges for a 1999 Dodge Neon ACR running a Haltech Nexus S2.
Tach, speedometer (VSS + odometer), coolant/oil temp, and fuel/ethanol, on ESP32-S3 480x480 round displays with LVGL 8.3.

- Plan, parts list, budget, work items: `docs/PLAN.md`
- CAN channel map (Haltech broadcast + custom hub frame): `docs/CAN-MAP.md`
- Pinned toolchain versions: `docs/TOOLCHAIN.md`

## Layout
```
firmware/gauge    single codebase, GAUGE_TYPE = TACH | SPEEDO | TEMP | FUEL
firmware/hub      VSS, odometer (FRAM), buttons, dimmer, custom CAN TX
firmware/can-sim  bench Haltech frame simulator (ESP32-S3 DevKit)
assets/scans      raw 1200 dpi scans (Git LFS)
assets/faces      480x480 face PNGs + LVGL C arrays
assets/needles    needle PNGs + pivot notes
hardware          KiCad hub schematic, harness pinouts, BOM
mechanical        mounting plate CAD + STLs
tools             image conversion scripts
```

## Status
Phase 0: donor cluster teardown and measurement.
