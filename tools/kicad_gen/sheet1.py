"""
Sheet 1 -- Battery Pack & Protection.

Topology notes (flagged where it deviates from / extends the literal BOM
table in the project prompt):

- 4S2P pack, series taps bottom->top: STACK_NEG - TAP1 - TAP2 - TAP3 - VBAT.
  BT1/BT2 parallel across STACK_NEG..TAP1, BT3/BT4 across TAP1..TAP2,
  BT5/BT6 across TAP2..TAP3, BT7/BT8 across TAP3..VBAT.
- U1 (BQ76920PW) VC0..VC4 sense the 4 taps; VC5 tied to VC4 (top) per TI's
  datasheet convention for <5S configurations. BAT/REGSRC = VBAT (top).
- R1 (current-sense shunt) sits between STACK_NEG and GND -- so BQ76920 can
  coulomb-count return current -- while the two protection FETs (Q1/Q2)
  sit HIGH-SIDE, in series between VBAT and VBAT_PROT, per the brief's own
  net map (VBAT and VBAT_PROT are both positive rails; GND is the one
  common ground). SRP=STACK_NEG (battery side), SRN=GND (system side).
- Q1 (DSG) and Q2 (CHG) are wired classic back-to-back / shared-source:
  Q1 D=VBAT, S=FET_MID; Q2 D=VBAT_PROT, S=FET_MID. Body diodes oppose,
  so either FET alone blocks one current direction when off.
- Q3 (AO3401A) is a P-FET "ideal diode" reverse-polarity guard right after
  the pack connector J2: S=PACK_RAW (from J2/F1), D=VBAT, G pulled to VBAT
  through added R90 so it self-biases on once VBAT is established -- same
  validated technique as a prior project's Q1 reverse-polarity circuit.
- FLAGGED ADDITIONS (not itemized as separate BOM rows in the prompt, but
  required for the listed ICs to actually function per their own
  datasheets -- see docs/design_notes.md):
    C90 1uF  0603  -- U1 REGOUT decoupling (BQ76920 datasheet typ. app. circuit)
    C91 0.1uF 0603 -- U1 CAP1 decoupling   (BQ76920 datasheet typ. app. circuit)
    R90 100k 0603  -- Q3 gate self-bias pull-up to VBAT (ideal-diode topology)
- U1 pins TS1 (no battery-pack thermistor in this BOM) and ALERT (not
  wired to an MCU GPIO in the given net map) are left as explicit
  no-connects, flagged for user awareness rather than silently guessed.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kicad_gen.builder import (
    build_schematic, add_part, add_pwr_flag, write_and_upgrade, Part,
)

PROJECT = "red-light-panel"
SHEET = "1"


def build():
    sch = build_schematic("Battery Pack & Protection", "01_battery_protection")
    embedded = set()

    def P(**kw):
        kw.setdefault("sheet", SHEET)
        return Part(**kw)

    parts = []

    # --- 4S2P cell stack ---
    cell_nets = [
        ("BT1", 20, "TAP1", "STACK_NEG"), ("BT2", 20, "TAP1", "STACK_NEG"),
        ("BT3", 40, "TAP2", "TAP1"), ("BT4", 40, "TAP2", "TAP1"),
        ("BT5", 60, "TAP3", "TAP2"), ("BT6", 60, "TAP3", "TAP2"),
        ("BT7", 80, "VBAT", "TAP3"), ("BT8", 80, "VBAT", "TAP3"),
    ]
    for i, (ref, col, plus, minus) in enumerate(cell_nets):
        x = 20 + col
        y = 20 if ref in ("BT1", "BT3", "BT5", "BT7") else 40
        parts.append(P(ref=ref, lib_file="Device", entry_name="Battery_Cell", nickname="Device",
                       value="INR18650-30Q", footprint="Battery:BatteryHolder_Keystone_1042_1x18650",
                       pins={"1": plus, "2": minus}, x=x, y=y,
                       mpn="Samsung INR18650-30Q", manufacturer="Samsung SDI",
                       digikey_pn="INR18650-30Q-B-ND",
                       datasheet="https://www.dnkpower.com/wp-content/uploads/2018/10/INR18650-30Q.pdf"))

    # --- protection AFE ---
    parts.append(P(ref="U1", lib_file="Battery_Management", entry_name="BQ76920PW", nickname="Battery_Management",
                   value="BQ76920PW", footprint="Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm",
                   pins={"1": "DSG_GATE", "2": "CHG_GATE", "3": "GND", "4": "I2C_SDA", "5": "I2C_SCL",
                         "6": "NC", "7": "U1_CAP1", "8": "U1_REGOUT", "9": "VBAT", "10": "VBAT",
                         "11": "NC", "12": "VBAT", "13": "VBAT", "14": "TAP3", "15": "TAP2",
                         "16": "TAP1", "17": "STACK_NEG", "18": "STACK_NEG", "19": "GND", "20": "NC"},
                   x=140, y=60, mpn="BQ7692000PWR", manufacturer="Texas Instruments",
                   digikey_pn="296-37299-1-ND", datasheet="http://www.ti.com/lit/ds/symlink/bq76920.pdf"))

    # --- protection FETs (high-side, back-to-back) ---
    parts.append(P(ref="Q1", lib_file="Transistor_FET", entry_name="CSD18540Q5B", nickname="Transistor_FET",
                   value="CSD18540Q5B", footprint="Package_TO_SOT_SMD:TDSON-8-1",
                   pins={"1": "FET_MID", "2": "FET_MID", "3": "FET_MID", "4": "DSG_GATE", "5": "VBAT"},
                   x=200, y=20, mpn="CSD18540Q5B", manufacturer="Texas Instruments",
                   digikey_pn="296-37312-1-ND", datasheet="http://www.ti.com/lit/gpn/csd18540q5b"))
    parts.append(P(ref="Q2", lib_file="Transistor_FET", entry_name="CSD18540Q5B", nickname="Transistor_FET",
                   value="CSD18540Q5B", footprint="Package_TO_SOT_SMD:TDSON-8-1",
                   pins={"1": "FET_MID", "2": "FET_MID", "3": "FET_MID", "4": "CHG_GATE", "5": "VBAT_PROT"},
                   x=200, y=45, mpn="CSD18540Q5B", manufacturer="Texas Instruments",
                   digikey_pn="296-37312-1-ND", datasheet="http://www.ti.com/lit/gpn/csd18540q5b"))

    # --- reverse-polarity ideal diode ---
    parts.append(P(ref="Q3", lib_file="Transistor_FET", entry_name="AO3401A", nickname="Transistor_FET",
                   value="AO3401A", footprint="Package_TO_SOT_SMD:SOT-23",
                   pins={"1": "Q3_GATE", "2": "PACK_RAW", "3": "VBAT"},
                   x=90, y=90, mpn="AO3401A", manufacturer="Alpha & Omega Semiconductor",
                   digikey_pn="AO3401A-DICT-ND", datasheet="http://www.aosmd.com/pdfs/datasheet/AO3401A.pdf"))
    parts.append(P(ref="R90", lib_file="Device", entry_name="R", nickname="Device",
                   value="100k", footprint="Resistor_SMD:R_0603_1608Metric",
                   pins={"1": "Q3_GATE", "2": "VBAT"}, x=110, y=90,
                   mpn="RC0603FR-07100KL", manufacturer="Yageo", digikey_pn="311-100KHRCT-ND",
                   datasheet=""))

    # --- current sense ---
    parts.append(P(ref="R1", lib_file="Device", entry_name="R", nickname="Device",
                   value="0.01R 1%", footprint="Resistor_SMD:R_Shunt_Vishay_WSK2512_6332Metric_T2.21mm",
                   pins={"1": "STACK_NEG", "2": "GND"}, x=140, y=100,
                   mpn="WSL2512R0100FEA", manufacturer="Vishay Dale", digikey_pn="541-2455-1-ND",
                   datasheet="https://www.vishay.com/docs/30112/wsl.pdf"))

    # --- bus TVS + fuse ---
    parts.append(P(ref="D1", lib_file="Diode", entry_name="SMAJ24CA", nickname="Diode",
                   value="SMAJ24CA", footprint="Diode_SMD:D_SMA",
                   pins={"1": "VBAT", "2": "GND"}, x=90, y=110,
                   mpn="SMAJ24CA", manufacturer="Littelfuse", digikey_pn="F5351CT-ND",
                   datasheet="https://www.littelfuse.com/media?resourcetype=datasheets&itemid=75e32973-b177-4ee3-a0ff-cedaf1abdb93&filename=smaj-datasheet"))
    parts.append(P(ref="F1", lib_file="Device", entry_name="Fuse", nickname="Device",
                   value="0.25A resettable", footprint="Fuse:Fuse_BelFuse_0ZRE0025FF_L9.6mm_W3.8mm",
                   pins={"1": "PACK_RAW_F", "2": "PACK_RAW"}, x=60, y=90,
                   mpn="0ZRE0025FF (corrected from placeholder MICROSMD250F/16-2 -- FLAG FOR REVIEW)",
                   manufacturer="Bel Fuse", digikey_pn="507-1677-1-ND",
                   datasheet="https://www.belfuse.com/resources/datasheets/circuitprotection/ds-cp-0zre-series.pdf"))

    # --- connectors ---
    parts.append(P(ref="J1", lib_file="Connector_Generic", entry_name="Conn_01x05", nickname="Connector_Generic",
                   value="JST B5B-XH-A", footprint="Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical",
                   pins={"1": "STACK_NEG", "2": "TAP1", "3": "TAP2", "4": "TAP3", "5": "VBAT"},
                   x=140, y=20, mpn="B5B-XH-A", manufacturer="JST", digikey_pn="455-1719-ND",
                   datasheet="https://www.jst-mfg.com/product/pdf/eng/eXH.pdf"))
    parts.append(P(ref="J2", lib_file="Connector_Generic", entry_name="Conn_01x02", nickname="Connector_Generic",
                   value="Molex 43045-0200", footprint="Connector_Molex:Molex_Micro-Fit_3.0_43045-0200_2x01_P3.00mm_Horizontal",
                   pins={"1": "PACK_RAW_F", "2": "STACK_NEG"}, x=20, y=90,
                   mpn="43045-0200", manufacturer="Molex", digikey_pn="WM1857-ND",
                   datasheet="https://www.molex.com/pdm_docs/sd/430450200_sd.pdf"))

    # --- flagged-added support passives (see module docstring) ---
    parts.append(P(ref="C90", lib_file="Device", entry_name="C", nickname="Device",
                   value="1uF (added, flagged)", footprint="Capacitor_SMD:C_0603_1608Metric",
                   pins={"1": "U1_REGOUT", "2": "GND"}, x=170, y=100,
                   mpn="", manufacturer="", digikey_pn="", datasheet=""))
    parts.append(P(ref="C91", lib_file="Device", entry_name="C", nickname="Device",
                   value="0.1uF (added, flagged)", footprint="Capacitor_SMD:C_0603_1608Metric",
                   pins={"1": "U1_CAP1", "2": "GND"}, x=185, y=100,
                   mpn="", manufacturer="", digikey_pn="", datasheet=""))

    for part in parts:
        add_part(sch, part, PROJECT, embedded)

    # Cross-sheet exposure: every pin already carries a GlobalLabel (see
    # add_part), and GlobalLabel scope is project-wide by definition, so
    # VBAT/VBAT_PROT/I2C_SDA/I2C_SCL/GND are already visible to every other
    # sheet that places a same-named label at one of ITS pins -- no extra
    # sheet-symbol pins or root-sheet wiring needed. See
    # docs/design_notes.md "Why global labels instead of sheet pins".

    # power flags so ERC's power_pin_not_driven doesn't fire on VBAT/GND
    # (no genuine power_out pin exists on this sheet's own parts for these
    # rails -- VBAT/GND are truly sourced off-sheet, at the cell stack
    # itself and downstream loads respectively)
    add_pwr_flag(sch, "VBAT", 260, 20, embedded)
    add_pwr_flag(sch, "GND", 260, 90, embedded)

    out = "/Users/lucaspoulos/kicad-projects/red-light-panel/01_battery_protection.kicad_sch"
    print(write_and_upgrade(sch, out))


if __name__ == "__main__":
    build()
