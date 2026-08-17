"""
Sheet 7 -- HMI (buttons + status LED).

- SW1-4 wired as active-high buttons: 3V3 -> switch -> BTN_x -> pull-down
  resistor (R9-R12) -> GND. Reads high when pressed, low (via pull-down)
  when released.
- **D8 is single-color** (per your decision -- the original BOM MPN,
  APTD1608LSECK/J4-PRV, doesn't match any real bi-color datasheet; the
  closest confirmed real part under that family name,
  APT1608LSECK/J4-PRV, is a single-color 605nm orange 2-pin LED). Wired
  as: 3V3 -> R13 (current limit) -> D8 anode; D8 cathode -> STAT_LED_R,
  which is BQ25792's open-collector STAT output (sheet 2) -- classic
  active-low open-drain LED drive (STAT sinks to light the LED when
  charging is active).
- **R13 value**: ~1k placeholder per the BOM's own note ("calc exact vs
  Vf/If") -- at 3.3V supply, ~2V Vf (605nm), ~2mA target If:
  R = (3.3-2.0)/0.002 = 650ohm, rounded up to 680ohm for a safety margin
  on LED current. FLAG FOR REVIEW against the real part's exact Vf/If
  datasheet curve.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kicad_gen.builder import build_schematic, add_part, add_pwr_flag, write_and_upgrade, Part

PROJECT = "red-light-panel"
SHEET = "7"


def build():
    sch = build_schematic("HMI (Buttons + Status)", "07_hmi")
    embedded = set()

    def P(**kw):
        kw.setdefault("sheet", SHEET)
        return Part(**kw)

    buttons = [
        ("SW1", "R9", "BTN_PWR"), ("SW2", "R10", "BTN_DIMP"),
        ("SW3", "R11", "BTN_DIMM"), ("SW4", "R12", "BTN_MODE"),
    ]
    parts = []
    for i, (sw_ref, r_ref, net) in enumerate(buttons):
        x = 20 + i * 30
        parts.append(P(ref=sw_ref, lib_file="Switch", entry_name="SW_Push", nickname="Switch",
                       value="Omron B3U-1000P", footprint="Button_Switch_SMD:SW_SPST_B3U-1000P",
                       pins={"1": "3V3", "2": net}, x=x, y=20,
                       mpn="B3U-1000P", manufacturer="Omron", digikey_pn="SW1020CT-ND",
                       datasheet="https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3u.pdf"))
        parts.append(P(ref=r_ref, lib_file="Device", entry_name="R", nickname="Device",
                       value="10k", footprint="Resistor_SMD:R_0603_1608Metric",
                       pins={"1": net, "2": "GND"}, x=x, y=45,
                       mpn="RC0603FR-0710KL", manufacturer="Yageo", digikey_pn="311-10.0KHRCT-ND", datasheet=""))

    parts.append(P(ref="R13", lib_file="Device", entry_name="R", nickname="Device",
                   value="680R (calc vs Vf/If, flag)", footprint="Resistor_SMD:R_0603_1608Metric",
                   pins={"1": "3V3", "2": "D8_A"}, x=160, y=20,
                   mpn="RC0603FR-07680RL", manufacturer="Yageo", digikey_pn="311-680HRCT-ND", datasheet=""))
    parts.append(P(ref="D8", lib_file="Device", entry_name="LED", nickname="Device",
                   value="APT1608LSECK/J4-PRV (single-color, corrected per your decision)",
                   footprint="LED_SMD:LED_0603_1608Metric",
                   pins={"1": "STAT_LED_R", "2": "D8_A"}, x=175, y=20,
                   mpn="APT1608LSECK/J4-PRV", manufacturer="Kingbright", digikey_pn="754-1552-1-ND",
                   datasheet="https://www.kingbrightusa.com/images/catalog/SPEC/APT1608LSECK-J4-PRV.pdf"))

    for part in parts:
        add_part(sch, part, PROJECT, embedded)

    add_pwr_flag(sch, "GND", 20, 60, embedded)

    out = "/Users/lucaspoulos/kicad-projects/red-light-panel/07_hmi.kicad_sch"
    print(write_and_upgrade(sch, out))


if __name__ == "__main__":
    build()
