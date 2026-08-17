"""
One-time post-processing pass, run after the root sheet exists.

`kicad-cli sch upgrade --force` (used by write_and_upgrade() while each
sheet was generated/ERC'd standalone) silently drops the per-symbol
`(instances (project ...))` block down to an empty `(instances)` --
observed empirically, not something kiutils or this project's code ever
asked for. That's what `kicad-cli sch export bom` was flagging as
"schematic has annotation errors": every placed symbol's project-instance
bookkeeping (which reference/unit it represents, for the *specific*
sheet-instance it lives on in the real hierarchy) was empty. ERC itself
never flagged anything related to this (it uses raw geometry, not this
bookkeeping) -- but a real KiCad GUI session normally fills this in the
first time you save a child sheet under its parent, so we replicate that
here via direct text surgery (round-tripping an already-upgraded v10 file
back through kiutils was tried and rejected -- it silently drops the
majority of the file's content; kiutils' parser doesn't fully understand
the v10 format kicad-cli produces).

Simple line-based state machine: track the current symbol's Reference/
unit as we scan down through its properties, and replace its (empty)
`(instances)` line with a populated block once we reach it.
"""
import re
from kiutils.schematic import Schematic

PROJECT_DIR = "/Users/lucaspoulos/kicad-projects/red-light-panel"
PROJECT_NAME = "red-light-panel"

REF_RE = re.compile(r'^\t\t\(property "Reference" "([^"]+)"')
UNIT_RE = re.compile(r'^\t\t\(unit (\d+)\)')


def fix_file(path: str, new_sheet_path: str):
    with open(path) as f:
        lines = f.readlines()

    out = []
    cur_ref = None
    cur_unit = "1"
    n = 0
    for line in lines:
        if line == "\t(symbol\n":
            cur_ref, cur_unit = None, "1"
        m = REF_RE.match(line)
        if m:
            cur_ref = m.group(1)
        m = UNIT_RE.match(line)
        if m:
            cur_unit = m.group(1)
        if line == "\t\t(instances)\n" and cur_ref:
            out.append(
                f'\t\t(instances\n'
                f'\t\t\t(project "{PROJECT_NAME}"\n'
                f'\t\t\t\t(path "{new_sheet_path}"\n'
                f'\t\t\t\t\t(reference "{cur_ref}") (unit {cur_unit})\n'
                f'\t\t\t\t)\n'
                f'\t\t\t)\n'
                f'\t\t)\n'
            )
            n += 1
            continue
        out.append(line)

    with open(path, "w") as f:
        f.writelines(out)
    return n


def main():
    root = Schematic.from_file(f"{PROJECT_DIR}/red-light-panel.kicad_sch")
    root_uuid = root.uuid
    sheet_uuid_by_file = {s.fileName.value: s.uuid for s in root.sheets}

    for filename, sheet_uuid in sheet_uuid_by_file.items():
        path = f"{PROJECT_DIR}/{filename}"
        new_path = f"/{root_uuid}/{sheet_uuid}"
        n = fix_file(path, new_path)
        print(f"{filename}: populated {n} instance blocks -> {new_path}")


if __name__ == "__main__":
    main()
