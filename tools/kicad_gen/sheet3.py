"""
Sheet 3 -- 3.3V Logic Rail.

- EN tied directly to VBAT (always-enabled -- TPS563201 has an internal
  EN pull-up per datasheet, direct tie is a standard simplification).
- VFB divider: R2 (10k, per BOM's RC0603FR-0710KL) on top (3V3->FB), R3
  (3.01k, calculated) on bottom (FB->GND). TPS563201 Vref = 0.768V typ.
  per datasheet -> R3 = R2 * Vref/(Vout-Vref) = 10k * 0.768/(3.3-0.768)
  = ~3.03k, rounded to the nearest E96 value (3.01k). FLAG FOR REVIEW --
  double check against the exact datasheet Vref spec/tolerance before fab.
- C93 (added, flagged): VBST-to-SW bootstrap cap, required by the
  datasheet's typical application circuit for the high-side driver, not
  itemized as a separate BOM row. Typical value 2.2nF-10nF; using 2.2nF.
- L1 footprint: no exact Wurth 744031220 footprint exists in KiCad's
  stock libraries. Using a similarly-sized placeholder
  (Vishay IFSC-1515AH, 4x4mm vs. WE-TPC 4828's ~4.8x4.8mm) -- FLAG FOR
  REVIEW, build/source the real footprint before fab. Matches the
  brief's own pre-existing "confirm inductor value vs datasheet calc"
  open item.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kicad_gen.builder import build_schematic, add_part, add_pwr_flag, write_and_upgrade, Part

PROJECT = "red-light-panel"
SHEET = "3"


def build():
    sch = build_schematic("3.3V Logic Rail", "03_power_rail_3v3")
    embedded = set()

    def P(**kw):
        kw.setdefault("sheet", SHEET)
        return Part(**kw)

    parts = [
        P(ref="U4", lib_file="Regulator_Switching", entry_name="TPS563201", nickname="Regulator_Switching",
          value="TPS563201DDCR", footprint="Package_TO_SOT_SMD:SOT-23-6",
          pins={"1": "GND", "2": "U4_SW", "3": "VBAT", "4": "U4_FB", "5": "VBAT", "6": "U4_VBST"},
          x=100, y=20, mpn="TPS563201DDCR", manufacturer="Texas Instruments",
          digikey_pn="296-51654-1-ND", datasheet="https://www.ti.com/lit/ds/symlink/tps563201.pdf"),

        P(ref="L1", lib_file="Device", entry_name="L", nickname="Device",
          value="2.2uH (Wurth 744031220)", footprint="Inductor_SMD:L_Vishay_IFSC-1515AH_4x4x1.8mm",
          pins={"1": "U4_SW", "2": "3V3"}, x=130, y=20,
          mpn="744031220", manufacturer="Wurth Elektronik", digikey_pn="732-1801-1-ND",
          datasheet="https://www.we-online.com/components/products/datasheet/744031220.pdf"),

        P(ref="C6", lib_file="Device", entry_name="C", nickname="Device",
          value="10uF", footprint="Capacitor_SMD:C_1206_3216Metric",
          pins={"1": "VBAT", "2": "GND"}, x=80, y=45,
          mpn="CC1206KKX7R8BB106", manufacturer="Yageo", digikey_pn="311-4622-1-ND", datasheet=""),

        P(ref="C7", lib_file="Device", entry_name="C", nickname="Device",
          value="10uF", footprint="Capacitor_SMD:C_1206_3216Metric",
          pins={"1": "3V3", "2": "GND"}, x=150, y=45,
          mpn="CC1206KKX5R7BB106", manufacturer="Yageo", digikey_pn="311-4633-1-ND", datasheet=""),

        P(ref="R2", lib_file="Device", entry_name="R", nickname="Device",
          value="10k", footprint="Resistor_SMD:R_0603_1608Metric",
          pins={"1": "3V3", "2": "U4_FB"}, x=170, y=20,
          mpn="RC0603FR-0710KL", manufacturer="Yageo", digikey_pn="311-10.0KHRCT-ND", datasheet=""),

        P(ref="R3", lib_file="Device", entry_name="R", nickname="Device",
          value="3.01k (calc, flag)", footprint="Resistor_SMD:R_0603_1608Metric",
          pins={"1": "U4_FB", "2": "GND"}, x=170, y=45,
          mpn="RC0603FR-073K01L", manufacturer="Yageo", digikey_pn="311-3.01KHRCT-ND", datasheet=""),

        P(ref="C93", lib_file="Device", entry_name="C", nickname="Device",
          value="2.2nF (added, flagged -- VBST bootstrap cap)", footprint="Capacitor_SMD:C_0603_1608Metric",
          pins={"1": "U4_VBST", "2": "U4_SW"}, x=115, y=45,
          mpn="", manufacturer="", digikey_pn="", datasheet=""),
    ]

    for part in parts:
        add_part(sch, part, PROJECT, embedded)

    # TPS563201's SW pin is type "output", not "power_out" -- so despite
    # feeding 3V3 through L1, there's no genuine power_out pin on this net
    # anywhere in the project. 3V3 gets its one PWR_FLAG here (where the
    # rail originates). VBAT is not flagged: BQ25792's BAT pin (power_out,
    # sheet 2) is a genuine driver for it project-wide. GND's one
    # project-wide PWR_FLAG lives on sheet 1 (see docs/design_notes.md --
    # multiple PWR_FLAGs on the same merged net conflict with each other).
    add_pwr_flag(sch, "3V3", 80, 60, embedded, flag_id="3")

    out = "/Users/lucaspoulos/kicad-projects/red-light-panel/03_power_rail_3v3.kicad_sch"
    print(write_and_upgrade(sch, out))


if __name__ == "__main__":
    build()
