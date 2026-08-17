# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added
- Initial repo scaffold: CERN-OHL-P v2 license, KiCad-appropriate
  `.gitignore`, README.
- KiCad 10 project scaffold (`red-light-panel.kicad_pro`/`.kicad_pcb`),
  project-scoped `sym-lib-table`/`fp-lib-table`.
- Programmatic schematic generator (`tools/kicad_gen/`) built on
  `kiutils`, used to populate all 7 hierarchical sub-sheets and the root
  sheet from declarative part lists.
- Full 7-sheet schematic hierarchy: Battery Pack & Protection, USB-C
  Charging Input, 3.3V Logic Rail, LED Drivers, LED Array, MCU & Control,
  HMI. 153 placed components, 0 ERC errors project-wide.
- Hand-built KiCad symbols for parts with no official downloadable source
  (`libs/red-light-panel.kicad_sym`): TPS25751DREFR, BQ25792RQMR,
  LM3409HVMY, TPD4S012DRYR, TPD4E001DBVR.
- Custom footprint for the Luminus SST-10-DR 3535-package LED
  (`libs/red-light-panel.pretty/`).
- BOM generation script (`bom/generate_bom.py`) and initial
  `bom/red-light-panel-bom.csv` (48 grouped rows).
- `docs/design_notes.md`, `docs/block_diagram.md`, `docs/power_budget.md`.

### Changed / corrected from the original part list
- `TPS25750DRYR` → `TPS25751DREFR` (NRND → active replacement).
- `TPD4S012DBVR` → `TPD4S012DRYR` (real part number for this device).
- `TPD4E001DZDR` → `TPD4E001DBVR` (real part number for this device).
- Placeholder fuse `MICROSMD250F/16-2` → Bel Fuse `0ZRE0025FF`.
- Status LED `APTD1608LSECK/J4-PRV` → confirmed single-color
  `APT1608LSECK/J4-PRV` (no real bi-color part exists under that name).
- Reference designators D6/D7/D8 renumbered to D69/D70/D71 (collided
  with the LED array's D5-D68 range).

See `README.md` "Known open items" for the full list of flagged
judgment calls still needing review.
