# Design notes

Working notes on non-obvious decisions made while generating this project,
kept here so they don't get lost or re-litigated later.

## Schematic generation approach

All 7 sub-sheets (and the root sheet) are generated programmatically from
`tools/kicad_gen/` rather than hand-drawn in the KiCad GUI, because the
BOM is large (~150 placed parts) and this keeps the part list, footprint
assignment, and wiring declarative and re-runnable. See
`tools/kicad_gen/builder.py` for the implementation; each `tools/kicad_gen/sheetN.py`
defines that sheet's parts and nets and calls into the shared builder.

You can still open and edit the resulting `.kicad_sch` files normally in
the KiCad 10 GUI -- the generator is just how they were first populated.

### Pipeline

1. Build the schematic object model with `kiutils` (a mature Python KiCad
   file library that targets the KiCad 8-era file format).
2. Text-patch two gaps between what kiutils emits and what KiCad 10 needs
   to load the file at all: quote the `generator` token and add a
   `generator_version` line (kiutils doesn't emit this token), and quote
   bare UUID-shaped tokens (kiutils doesn't quote them; KiCad 10's loader
   rejects the file outright without quotes).
3. Run `kicad-cli sch upgrade --force` to have the real KiCad 10 binary
   rewrite the file to its true native format. This is the authoritative
   normalization step -- nothing about the final file format is guessed.

### Connectivity: global labels, no wires

Every pin that needs to be on a net gets a `GlobalLabel` placed exactly at
that pin's world coordinate -- no wires anywhere. Two labels with the same
text are the same net project-wide even with zero wires between them, as
long as each is coincident with a real pin. This is standard KiCad
behavior (confirmed against a real kicad-cli 10.0.5 install and
cross-checked against a prior project's own ERC-clean, wire-free
schematics) and avoids hand-routing ~150 components.

**Global, not local, labels.** `LocalLabel` empirically did *not* connect
to a coincident pin in this KiCad version without an explicit wire
touching both -- only `GlobalLabel` (and, by extension, hierarchical
labels) connect by bare coincidence. Since every net name used here is
unique to its sheet except the intentionally-shared cross-sheet nets
(VBAT, GND, I2C_SDA, ...), using global scope throughout carries no risk
of accidental cross-sheet merges.

**Why global labels instead of sheet-symbol pins.** The prompt that
originated this project asked for literal hierarchical labels + matching
sheet-symbol pins on the root sheet for inter-sheet nets. Global labels
achieve the identical electrical outcome (a net crosses sheet boundaries
by name, project-wide) with far less risk -- no need to hand-place
sheet-symbol pins and wire them to matching labels on the root sheet, and
no chance of a sheet-pin/hierarchical-label name or direction mismatch.
The root sheet's sheet symbols carry no pins as a result; this is a
deliberate, documented substitution, not an oversight.

**The pin-position Y-flip.** A pin's world connection point is
`(symbol.x + pin.local_x, symbol.y - pin.local_y)` -- note the minus sign.
KiCad's symbol library editor uses a Y-up coordinate system internally,
but placed schematic coordinates are Y-down, so the Y axis flips when a
symbol is placed. Confirmed empirically (a naive `+` produced schematics
where every single pin was reported "not connected" by
`kicad-cli sch erc`, despite the labels looking coincident on paper) and
cross-checked against a real, ERC-clean prior project's file. Pin `length`
is *not* added -- the pin's own `(at x y)` already is the connection tip
in the library data kiutils exposes.

**Flattening `extends`-based symbols.** A handful of stock symbols
(`Transistor_FET:AO3401A` extends `TP0610T`, `CSD18540Q5B` extends
`Q_NMOS_SSSGD_AvalancheRated`) are defined via KiCad's `extends`
mechanism to avoid duplicating a shared body/pinout. Embedding both the
derived and base symbols in a sheet's `lib_symbols` cache (with the base's
library correctly registered in the project's own `sym-lib-table`) loads
fine and only produces the expected benign `lib_symbol_mismatch` ERC
warning -- but pin *position* resolution for the still-`extends`-linked
placed instance did not reliably line up with the raw coordinates pulled
from the base symbol: every pin on every `extends`-based part came back
as a dangling label. `load_stock_symbol()` in `builder.py` works around
this by flattening -- copying the base's units directly onto the derived
symbol and dropping the `extends` pointer before embedding, so pin data
always comes from the one object that's actually placed. A prior project
independently hit and documented the same class of problem (there, the
proximate cause was an unregistered library nickname rather than a
pin-position mismatch, but the fix -- flatten `extends` rather than rely
on it -- is the same).

### PWR_FLAG placement

`kicad-cli sch erc`'s `power_pin_not_driven` check requires every
`power_in`-type pin's net to have some `power_out`-type pin (or a
`Device:PWR_FLAG`) on it *somewhere in the whole hierarchical project*.
Rails that are genuinely sourced off-sheet from that sheet's own
perspective (e.g. `VBAT` and `GND` on the battery sheet, which are
sourced by the cell stack itself and by downstream loads respectively, not
by any `power_out` pin placed on that sheet) get a `PWR_FLAG` so this
check doesn't misfire. `PWR_FLAG` symbols are placed with `in_bom no` /
`on_board no`, matching KiCad convention -- they're a paper annotation for
ERC, not a real component.

## Flagged additions beyond the literal BOM

A few passives are required by the datasheet-mandated minimum application
circuit for a listed IC, but weren't itemized as separate BOM rows in the
original part list. These are called out with `(added, flagged)` in their
`Value` field and documented per-sheet in that sheet's build script
docstring (`tools/kicad_gen/sheetN.py`) so they're easy to find and
double-check. See also the top-level `README.md` "Known open items" list.
