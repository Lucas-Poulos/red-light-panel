# red-light-panel

A battery-powered 660nm red light therapy panel. 4S2P 18650 Li-ion pack
(~74Wh-class), USB-C PD charging, ~74W LED load across two independently
PWM-dimmable channels, STM32-based control with a 4-button HMI.

KiCad 10 hardware project — schematic + BOM. PCB layout/routing is out of
scope for this pass (`red-light-panel.kicad_pcb` exists as a valid,
correctly-stacked-up empty board file, ready for layout).

## Architecture

Seven hierarchical sheets, numbered so KiCad's hierarchy navigator sorts
them in build/reading order:

| Sheet | Description |
|---|---|
| `01_battery_protection` | 4S2P 18650 pack, BQ76920 protection AFE, high-side dual-FET protection, reverse-polarity guard |
| `02_usbc_charging` | USB-C PD input (TPS25751), buck-boost charger (BQ25792), ESD protection |
| `03_power_rail_3v3` | TPS563201 buck regulator, 3.3V system logic rail |
| `04_led_drivers` | 2x LM3409HV PFET-buck constant-current LED driver channels |
| `05_led_array` | 64x Luminus SST-10-DR-B130-K660 660nm LEDs, 2 channels x 8 parallel x 4 series strings |
| `06_mcu_control` | STM32G031K8T6 MCU, SWD debug (Cortex Debug 10-pin + THT breakout), ESD arrays |
| `07_hmi` | 4 tactile buttons (power/dim+/dim-/mode), single-color status LED |

Connectivity uses `GlobalLabel`s throughout rather than wired
hierarchical sheet-symbol pins — see `docs/design_notes.md` for why. The
root sheet (`red-light-panel.kicad_sch`) contains only the 7 sheet
symbols, no components.

## Opening the project

Requires **KiCad 10**. Clone the repo and open `red-light-panel.kicad_pro`
— the project-local `sym-lib-table`/`fp-lib-table` register every stock
library this design uses (via `${KICAD10_SYMBOL_DIR}`/
`${KICAD10_FOOTPRINT_DIR}`, so they resolve on any machine with KiCad 10
installed) plus `libs/red-light-panel.kicad_sym` / `.pretty` for the
handful of parts not in KiCad's stock libraries. No global library setup
is required.

## Regenerating the schematics

The 7 sub-sheets and the root sheet are generated programmatically from
`tools/kicad_gen/` (a small `kiutils`-based builder), not hand-drawn —
see `docs/design_notes.md` "Schematic generation approach" for the full
pipeline and the non-obvious KiCad file-format details it works around.
To rebuild everything from the declarative part lists in
`tools/kicad_gen/sheet*.py`:

```
pip install kiutils sexpdata
python3 tools/kicad_gen/sheet1.py   # ... through sheet7.py
python3 tools/kicad_gen/root_sheet.py
python3 tools/kicad_gen/fix_instance_paths.py
```

## Regenerating the BOM

```
python3 bom/generate_bom.py
```

Wraps `kicad-cli sch export bom` (reads the full hierarchical netlist
including the custom `MPN`/`Manufacturer`/`DigiKey_PN`/`Sheet` fields set
on every symbol) grouped by `(MPN, Value, Footprint)` into
`bom/red-light-panel-bom.csv` — 48 rows, 153 total placed components.

## Current design status

**Verification**: full-hierarchy `kicad-cli sch erc` on
`red-light-panel.kicad_sch` reports **0 errors** (157 cosmetic
"endpoint off grid" warnings from the auto-placed layout, 3 expected
"lib_symbol_mismatch" warnings from stock parts whose KiCad-library
`extends` chain was flattened for pin-position reliability — see
`docs/design_notes.md`). Every one of the 153 placed components has a
linked footprint; zero duplicate reference designators.

### Known open items (flagged, need your review before fab)

**Corrections to the original BOM** (verified real part numbers/topology
fixes, not silent substitutions to different components):
- `TPD4S012DBVR` → **TPD4S012DRYR** (that BVR suffix/package doesn't
  exist for this part; TI only makes it in a 6-pin USON).
- `TPD4E001DZDR` → **TPD4E001DBVR** (same issue; the 4-channel device
  needs a 6-pin SOT-23, not the 4-pin DZD package).
- `TPS25750DRYR` → **TPS25751DREFR** (TPS25750 is TI-marked
  Not-Recommended-for-New-Designs; TPS25751 is the active replacement —
  your decision, see below).
- Fuse `MICROSMD250F/16-2` (originally a placeholder) → **Bel Fuse
  0ZRE0025FF** (0.25A hold current, matching the placeholder's own naming
  convention) — verify hold-current spec against your real current
  budget before finalizing.
- Status LED `APTD1608LSECK/J4-PRV` → confirmed **single-color**
  (`APT1608LSECK/J4-PRV`, no "D") — no real bi-color part exists under
  that family name. Per your decision, D71 (renumbered from D8, see
  below) is now a single-color status LED.
- Reference designators **D6/D7/D8 renumbered to D69/D70/D71**: the
  original BOM's own `D5-D68` (64 LED array elements) numerically
  collided with these three (sheet 6 ESD arrays, sheet 7 status LED).

**Needs your engineering review** (reasonable, documented, but
unverified-against-datasheet or genuinely open decisions):
- **BQ25792's front-end ideal-diode MOSFETs (ACFET/RBFET1/RBFET2) are not
  included** — TI's real reference design needs them on the
  ACDRV1/ACDRV2/BTST1/BTST2 pins, but they weren't itemized in the
  original BOM and weren't invented here unprompted. The charger's
  reverse-blocking front-end is incomplete as generated until you decide
  whether/how to add this.
- **TPS25751DREFR and BQ25792RQMR are hand-built symbols** (no official
  downloadable KiCad source exists for either — confirmed via TI/DigiKey/
  Ultra Librarian). Every pin was sourced from TI's own datasheet pin
  tables, but several individual pins have ambiguous datasheet electrical
  types (TI itself labels some pins as generic "P"/"I/O") — double-check
  before trusting blind, especially: TPS25751's `LDO_1V5`/`DRAIN`/`PPHV`/
  `VBUS_IN`; BQ25792's `BTST1`/`BTST2`/`VAC1`/`VAC2`/`BATP`/`BAT`/`PMID`.
- **TPS25751's power-path topology** (VBUS_IN → internal switch →
  PPHV/DRAIN → BQ25792) is a best-effort interpretation of TI's own
  ambiguous datasheet, not confirmed against a real TI reference design.
- **LED array topology** (8 parallel strings of 4 series LEDs per
  channel, ~625mA/string) is derived from Vf/rail-voltage math, not
  specified by the BOM — verify against the ~74W target power budget and
  the Luminus datasheet's thermal-derating curves.
- **STM32G031 GPIO assignment** (I2C on PB6/PB7, PWM on PA6/PA7, buttons
  on PA0-PA3, NTC ADC on PA4, NRST on PF2) is a reasonable but
  **unverified-against-the-reference-manual** pin choice.
- **Driver inductors** (L2/L3, Vishay IHLP2525CZERR10M01) and the 3.3V
  rail inductor (L1, Wurth 744031220) — values need a real switching-
  frequency calc against LM3409HV's/TPS563201's design equations, not
  just the default values used here.
- **L1's footprint** is a size-matched placeholder (no exact Wurth
  744031220 footprint exists in KiCad's stock libraries).
- **J3's exact GCT USB4105 suffix** (plating/stake length) — defaulted
  to `USB4105-GF-A`; there is no "mount style" suffix (confirmed via
  research — the whole series is one fixed SMT top-mount style).
- **J6's footprint** (generic 2x5 1.27mm SMD header) is electrically
  equivalent to but not the exact Samtec FTSH-105-01-F-DV-K footprint.
- **Calculated component values** flagged inline in their `Value` field
  wherever a real datasheet equation was used instead of an itemized BOM
  value: R3 (3.3V feedback divider bottom leg), R13 (status LED current
  limit), and every "(added, flagged)" support passive (COFF/UVLO
  networks, bootstrap caps, ILIM_HIZ/PROG set resistors, NTC pull-up) —
  see `tools/kicad_gen/sheet*.py` docstrings for the reasoning behind
  each.

None of the above are unresolved *nets* or missing pin connections —
every flagged item is a component-value/part-choice judgment call called
out for your review, consistent with a 0-error ERC pass.
