#!/usr/bin/env python3
"""
Regenerate bom/red-light-panel-bom.csv from the schematic hierarchy.

This is a thin, documented wrapper around `kicad-cli sch export bom`
rather than a hand-rolled CSV parser -- kicad-cli already reads the full
hierarchical netlist (including the custom MPN/Manufacturer/DigiKey_PN/
Sheet fields set on every symbol) and has built-in grouping support, so
there's no need to reimplement that.

Grouping key is (MPN, Value, Footprint) rather than just MPN: several
"added, flagged" support passives (see docs/design_notes.md) share an
empty MPN field since they're not sourced from a specific vendor SKU, and
grouping on MPN alone would incorrectly merge e.g. a 100pF cap with a
2.2nF cap just because both have MPN="". Grouping on all three fields
still correctly collapses genuinely-identical parts (e.g. every 0.1uF
0603 decoupling cap project-wide, which all share the same real MPN)
into one row with a combined reference list and summed quantity.

Usage:
    python3 bom/generate_bom.py
"""
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
ROOT_SCH = PROJECT_DIR / "red-light-panel.kicad_sch"
OUTPUT = Path(__file__).resolve().parent / "red-light-panel-bom.csv"

FIELDS = "Reference,Value,MPN,Manufacturer,DigiKey_PN,QUANTITY,Sheet"
LABELS = "Reference,Value,MPN,Manufacturer,DigiKey_PN,Qty,Sheet"
GROUP_BY = "MPN,Value,Footprint"


def main():
    cmd = [
        "kicad-cli", "sch", "export", "bom", str(ROOT_SCH),
        "--fields", FIELDS,
        "--labels", LABELS,
        "--group-by", GROUP_BY,
        "--ref-range-delimiter", "",  # "D5,D6,D7" not "D5-D7" -- clearer for a hand-review pass
        "--output", str(OUTPUT),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    stderr = "\n".join(
        line for line in result.stderr.splitlines() if "Fontconfig" not in line
    )
    print(result.stdout, end="")
    if stderr:
        print(stderr, file=sys.stderr)
    if result.returncode != 0:
        sys.exit(result.returncode)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
