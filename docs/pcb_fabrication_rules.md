# PCB fabrication rules — 2-layer, 1oz/1oz, JLCPCB standard service + margin

This board is configured as a standard (non-advanced/non-HDI) 2-layer
JLCPCB build, with every constraint set comfortably above JLCPCB's
published minimum capability rather than at the limit. Two places hold
the actual rule values:

- **`red-light-panel.kicad_pro`** (`board.design_settings.rules` and
  `net_settings.classes`) — board-wide minimums, edited in KiCad's own
  "Board Setup > Design Rules > Constraints" schema.
- **`red-light-panel.kicad_dru`** — net-specific overrides for
  high-current traces (KiCad auto-loads this because its filename
  matches the project name; no separate registration needed).

## Stackup

`red-light-panel.kicad_pcb`'s `(setup (stackup ...))`:

| Layer | Spec |
|---|---|
| F.Cu / B.Cu | 1oz (0.035mm) copper, both outer layers |
| Core | 1.53mm FR4 core, er=4.6, loss tangent 0.02 (JLCPCB's commonly published 2-layer 1.6mm-stackup core) |
| Overall thickness | 1.6mm (standard, matches `general.thickness`) |
| Surface finish | **ENIG**, not JLCPCB's HASL default |

**Surface finish flag**: this design has fine-pitch QFN parts (BQ25792
at 0.4mm pitch, TPS25751 also 0.4mm pitch) where HASL's uneven surface
is a real solder-bridging risk. ENIG is still a standard JLCPCB service
option (not an "advanced" surcharge tier), just a deliberate upgrade
from their default. Flip back to HASL if cost is a bigger concern than
that risk for your build.

## Board-wide DRC minimums (`kicad_pro` → `design_settings.rules`)

| Rule | JLCPCB standard-service minimum | Set here | Margin |
|---|---|---|---|
| Track width | 0.09mm (3.5mil) | **0.15mm (6mil)** | ~1.7x |
| Clearance (track/pad-to-track/pad) | 0.09mm (3.5mil) | **0.15mm (6mil)** | ~1.7x |
| Copper-to-board-edge | ~0.3mm | **0.5mm** (kept from KiCad's own default, already exceeds target) | ~1.7x |
| Hole-to-copper clearance | ~0.13mm | **0.3mm** | ~2.3x |
| Hole-to-hole spacing | ~0.25mm | **0.5mm** | 2x |
| Through-hole (PTH) diameter | ~0.2-0.3mm (board-thickness dependent) | **0.3mm** | at/above min |
| Via diameter (pad) | ~0.45mm | **0.5mm** floor / **0.6mm** preferred (net class) | modest, more via the preferred-vs-floor gap |
| Via drill | ~0.2mm | **0.3mm** (net class default) | 1.5x |
| Silk line width | ~0.1mm (4mil) | **0.15mm (6mil)** | 1.5x |
| Silk clearance | not separately specified | **0.15mm** | -- |
| Min text height | 0.8mm (legibility floor) | **1.0mm** | -- |
| Solder mask expansion | ~0.05mm typical default | **0.05mm** | matches typical, not pushed to 0 |

6mil track/clearance (not JLCPCB's bare 3.5mil minimum) is a
widely-used "PCB house safe default" across the industry generally, not
just JLCPCB-specific — it's tight enough to still be practical for this
board's finer-pitch parts, while leaving real headroom over the absolute
floor.

**Known tension, flagged rather than silently loosened**: JLCPCB's
0.4mm/0.5mm-pitch QFN parts (BQ25792, TPS25751, LM3409HV) may need
tighter local escape-routing clearance than this board-wide 0.15mm floor
allows once layout begins — that's a normal, expected situation handled
with a small *local* net-class exception for just those specific escape
traces when routing, not by loosening the global minimum for the whole
board. Not resolved here since layout hasn't started.

## Net-specific high-current overrides (`kicad_dru`)

The board-wide 0.15mm minimum is nowhere near adequate for actual
current-carrying traces — this is a real physical/thermal constraint,
not a fabrication-capability one, and needed handling regardless of the
DRC-minimum discussion above. Per `docs/power_budget.md`'s ~5A/channel
LED current and comparable pack-level current estimates, 1oz copper at
~20°C rise wants meaningfully wider traces than logic-signal minimums:

| Net group | Track width | Rationale |
|---|---|---|
| `VBAT`, `VBAT_PROT`, `GND`, `USB_VBUS`, `PD_PP_OUT` | 1.5mm (opt), 1mm (min) | Pack-level current, worst case ~5-6A |
| `LED_A+/-`, `LED_B+/-` | 1.5mm (opt), 1mm (min) | ~625mA/string x up to 8 parallel strings ≈ 5A/channel |
| `U4_SW`, `U3_SW1`, `U3_SW2` | 1mm (opt), 0.8mm (min) | Buck/charger switching nodes -- also keep these short/direct once routed, wide alone doesn't fix switching-noise loop area |

These widths are a safe starting point sized off the power-budget
estimate already flagged as needing real verification (see
`docs/power_budget.md`) — recheck once the exact target LED current is
locked in, not just before fab.

## Current DRC status

The board currently has all 153 footprints imported from the schematic
but **not yet placed or routed** (this project's stated scope stopped at
schematic + BOM — see `README.md`). Running `kicad-cli pcb drc` right
now reports several hundred violations, essentially all attributable to
that: overlapping default-import footprint placement (`shorting_items`,
`clearance`, `silk_overlap`/`silk_over_copper`), no board outline
(`invalid_outline`), and pad nets not yet synced from the schematic
(`net_conflict` under schematic-parity). None of that is caused by the
rule values above — it's expected for an unplaced/unrouted board and
will clear as layout progresses.

One **real, useful finding** the new rules did catch: **U2's WQFN-38
footprint** (`Package_DFN_QFN:Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4`)
has small thermal-relief vias in its exposed pad drilled at 0.2mm,
which is below this board's 0.3mm minimum through-hole diameter. This
is the same footprint already flagged in `README.md` as having a
pad-count-mismatch caveat from sourcing — worth resolving both issues
together when this footprint gets a closer look (either accept 0.2mm
thermal vias as a deliberate, JLCPCB-capable-but-tighter-than-our-margin
exception for just that footprint, or rebuild the thermal pad via array
at 0.3mm).
