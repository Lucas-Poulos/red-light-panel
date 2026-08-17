"""
Root sheet -- red-light-panel.kicad_sch.

Contains only sheet symbols (no components), one per sub-sheet, in build
order (numbered filenames sort correctly in KiCad's hierarchy navigator).

No hierarchical pins are placed on these sheet symbols: this project uses
GlobalLabel-based connectivity throughout (see docs/design_notes.md "Why
global labels instead of sheet pins"), so nets already cross sheet
boundaries by name without needing sheet-symbol pins wired here.
"""
import sys, os, uuid as uuidlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kicad_gen.builder import build_schematic, write_and_upgrade
from kiutils.schematic import HierarchicalSheet, HierarchicalSheetProjectInstance, HierarchicalSheetProjectPath
from kiutils.items.common import Position, Property, Effects, Stroke

PROJECT = "red-light-panel"

SHEETS = [
    ("Battery Pack & Protection", "01_battery_protection.kicad_sch"),
    ("USB-C Charging Input", "02_usbc_charging.kicad_sch"),
    ("3.3V Logic Rail", "03_power_rail_3v3.kicad_sch"),
    ("LED Drivers", "04_led_drivers.kicad_sch"),
    ("LED Array", "05_led_array.kicad_sch"),
    ("MCU & Control", "06_mcu_control.kicad_sch"),
    ("HMI", "07_hmi.kicad_sch"),
]


def build():
    sch = build_schematic("Red Light Therapy Panel", "Root sheet -- hierarchy overview")

    for i, (name, filename) in enumerate(SHEETS):
        x = 20 + (i % 4) * 65
        y = 20 + (i // 4) * 60
        sheet_uuid = str(uuidlib.uuid4())
        hsheet = HierarchicalSheet(
            position=Position(x, y, 0), width=55, height=40,
            fieldsAutoplaced=True,
            stroke=Stroke(width=0.1524, type="solid"),
            uuid=sheet_uuid,
            sheetName=Property(key="Sheetname", value=name,
                                position=Position(x, y - 1.5, 0), effects=Effects()),
            fileName=Property(key="Sheetfile", value=filename,
                               position=Position(x, y + 41.5, 0), effects=Effects()),
            instances=[HierarchicalSheetProjectInstance(
                name=PROJECT,
                paths=[HierarchicalSheetProjectPath(sheetInstancePath="/", page=str(i + 2))],
            )],
        )
        sch.sheets.append(hsheet)

    out = "/Users/lucaspoulos/kicad-projects/red-light-panel/red-light-panel.kicad_sch"
    print(write_and_upgrade(sch, out))


if __name__ == "__main__":
    build()
