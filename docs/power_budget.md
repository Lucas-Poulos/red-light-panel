# Power budget notes

Placeholder — rough, back-of-envelope numbers derived while generating
the schematic (see `tools/kicad_gen/sheet4.py` and `sheet5.py` docstrings
for the full reasoning). **Not a substitute for a real power budget
pass** — flagged throughout as needing verification against the actual
Luminus SST-10-DR datasheet current/thermal-derating curves and your
real target runtime.

## LED load

- 64x Luminus SST-10-DR-B130-K660, split into 2 channels (LM3409HV
  drivers) x 8 parallel strings x 4 series LEDs.
- ~2.1V Vf per LED (typ., 660nm deep red) → ~8.4V per string.
- LM3409HV/R4-R5 sense resistor (0.02ohm, ~100mV typ. threshold) sets
  ~5A total channel current → ~625mA per string/per LED.
- Per-channel: ~8.4V x 5A ≈ 42W. Two channels ≈ **84W** -- in the same
  ballpark as the brief's own "~74W LED load" figure but not an exact
  match; needs reconciling against your actual target (adjust the sense
  resistor value or string count to dial in the real target current).

## Battery pack

- 4S2P 18650 (e.g. Samsung INR18650-30Q, ~3000mAh/cell) → ~6000mAh pack
  capacity at nominal 14.4V (3.6V/cell) → **~86Wh** pack energy.
- At ~84W LED load alone (both channels, ignoring MCU/driver overhead),
  that's roughly **~1 hour** of runtime at full brightness/both channels
  -- worth checking against your actual intended treatment-session
  duration and duty cycle (PWM dimming via EN on the LM3409HV channels
  will reduce average draw well below this worst-case number in normal
  use).

## Charging

- BQ25792 buck-boost charger, USB-C PD input via TPS25751. Real charge
  current depends on the PD contract negotiated (not modeled here) and
  the ILIM_HIZ/PROG resistor values (R91/R92, flagged as placeholders in
  `sheet2.py` -- calculate against your real target charge current).
