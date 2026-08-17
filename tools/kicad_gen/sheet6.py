"""
Sheet 6 -- MCU & Control.

**GPIO assignment** (not specified by the BOM -- derived and flagged):
STM32G031K8Tx's stock KiCad symbol pin table doesn't literally spell out
"NRST"/"VDDA" as separate names for this 32-pin package (only one VDD/VSS
pair is exposed, and reset shares pin 6 as "PF2" -- ST's own datasheet
names this same physical pin "PF2-NRST" on this package, i.e. GPIO+reset
shared). PA13/PA14 = SWDIO/SWCLK is fixed on every STM32 part (not a
package-specific choice). Everything else below (I2C on PB6/PB7, PWM on
PA6/PA7, buttons on PA0-PA3, NTC ADC on PA4) is a reasonable but
UNVERIFIED-against-the-reference-manual pin choice -- flag for review
against the STM32G031 datasheet's actual alternate-function table before
finalizing firmware/pinout.

- **VDDA bypass (C18)**: this package has no separate VDDA pin in the
  stock symbol (ties internally to VDD) -- C18 is wired to the same
  VDD/GND nets as the other decoupling, as a larger bulk cap for analog
  noise immunity, per the BOM's own description of its purpose.
- **D6** (ESD array, exposed digital lines): wired across the 4 HMI
  button inputs (BTN_PWR/DIMP/DIMM/MODE) -- the lines most exposed to
  user/enclosure-edge ESD.
- **D7** (ESD array, SWD lines/J7 breakout): wired across SWDIO/SWCLK/
  NRST; its 4th channel is left NC (3V3/GND on the J7 breakout don't need
  transient protection the same way signal lines do).
- **STAT_LED_R** does NOT touch this sheet -- per the brief's own net map
  ("Sheet 6 MCU *or* Sheet 2 charger STAT pins -> Sheet 7"), this design
  drives it directly from BQ25792's STAT pin (sheet 2), so no MCU GPIO is
  reserved for it.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kicad_gen.builder import build_schematic, add_part, add_pwr_flag, write_and_upgrade, Part

PROJECT = "red-light-panel"
SHEET = "6"


def build():
    sch = build_schematic("MCU & Control", "06_mcu_control")
    embedded = set()

    def P(**kw):
        kw.setdefault("sheet", SHEET)
        return Part(**kw)

    parts = [
        P(ref="U7", lib_file="MCU_ST_STM32G0", entry_name="STM32G031K8Tx", nickname="MCU_ST_STM32G0",
          value="STM32G031K8T6", footprint="Package_QFP:LQFP-32_7x7mm_P0.8mm",
          pins={"1": "NC", "2": "NC", "3": "NC", "4": "3V3", "5": "GND", "6": "NRST",
                "7": "BTN_PWR", "8": "BTN_DIMP", "9": "BTN_DIMM", "10": "BTN_MODE",
                "11": "NTC_SENSE", "12": "NC", "13": "PWM_A", "14": "PWM_B",
                "15": "NC", "16": "NC", "17": "NC", "18": "NC", "19": "NC",
                "20": "NC", "21": "NC", "22": "NC", "23": "NC", "24": "SWDIO",
                "25": "SWCLK", "26": "NC", "27": "NC", "28": "NC", "29": "NC",
                "30": "I2C_SCL", "31": "I2C_SDA", "32": "NC"},
          x=100, y=40, mpn="STM32G031K8T6", manufacturer="STMicroelectronics",
          digikey_pn="497-STM32G031K8T6TR-ND",
          datasheet="https://www.st.com/resource/en/datasheet/stm32g031k8.pdf"),

        P(ref="C14", lib_file="Device", entry_name="C", nickname="Device",
          value="0.1uF", footprint="Capacitor_SMD:C_0603_1608Metric",
          pins={"1": "3V3", "2": "GND"}, x=60, y=20,
          mpn="CC0603KRX7R9BB104", manufacturer="Yageo", digikey_pn="311-1367-1-ND", datasheet=""),
        P(ref="C15", lib_file="Device", entry_name="C", nickname="Device",
          value="0.1uF", footprint="Capacitor_SMD:C_0603_1608Metric",
          pins={"1": "3V3", "2": "GND"}, x=75, y=20,
          mpn="CC0603KRX7R9BB104", manufacturer="Yageo", digikey_pn="311-1367-1-ND", datasheet=""),
        P(ref="C16", lib_file="Device", entry_name="C", nickname="Device",
          value="0.1uF", footprint="Capacitor_SMD:C_0603_1608Metric",
          pins={"1": "3V3", "2": "GND"}, x=90, y=20,
          mpn="CC0603KRX7R9BB104", manufacturer="Yageo", digikey_pn="311-1367-1-ND", datasheet=""),
        P(ref="C17", lib_file="Device", entry_name="C", nickname="Device",
          value="0.1uF", footprint="Capacitor_SMD:C_0603_1608Metric",
          pins={"1": "3V3", "2": "GND"}, x=105, y=20,
          mpn="CC0603KRX7R9BB104", manufacturer="Yageo", digikey_pn="311-1367-1-ND", datasheet=""),
        P(ref="C18", lib_file="Device", entry_name="C", nickname="Device",
          value="4.7uF", footprint="Capacitor_SMD:C_1206_3216Metric",
          pins={"1": "3V3", "2": "GND"}, x=120, y=20,
          mpn="CC1206KKX7R8BB475", manufacturer="Yageo", digikey_pn="311-4646-1-ND", datasheet=""),

        P(ref="R6", lib_file="Device", entry_name="R", nickname="Device",
          value="10k", footprint="Resistor_SMD:R_0603_1608Metric",
          pins={"1": "3V3", "2": "I2C_SDA"}, x=180, y=20,
          mpn="RC0603FR-0710KL", manufacturer="Yageo", digikey_pn="311-10.0KHRCT-ND", datasheet=""),
        P(ref="R7", lib_file="Device", entry_name="R", nickname="Device",
          value="10k", footprint="Resistor_SMD:R_0603_1608Metric",
          pins={"1": "3V3", "2": "I2C_SCL"}, x=195, y=20,
          mpn="RC0603FR-0710KL", manufacturer="Yageo", digikey_pn="311-10.0KHRCT-ND", datasheet=""),
        P(ref="R8", lib_file="Device", entry_name="R", nickname="Device",
          value="10k", footprint="Resistor_SMD:R_0603_1608Metric",
          pins={"1": "3V3", "2": "NRST"}, x=210, y=20,
          mpn="RC0603FR-0710KL", manufacturer="Yageo", digikey_pn="311-10.0KHRCT-ND", datasheet=""),

        P(ref="J6", lib_file="Connector", entry_name="Conn_ARM_JTAG_SWD_10", nickname="Connector",
          value="Cortex Debug 10-pin", footprint="Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD",
          pins={"1": "3V3", "2": "SWDIO", "3": "GND", "4": "SWCLK", "5": "GND",
                "6": "NC", "7": "NC", "8": "NC", "9": "GND", "10": "NRST"},
          x=60, y=70, mpn="FTSH-105-01-F-DV-K (footprint substituted, flag)", manufacturer="Samtec",
          digikey_pn="SAM8199-ND", datasheet="https://suddendocs.samtec.com/prints/ftsh-1xx-xx-xxx-dv-x-mkt.pdf"),

        P(ref="J7", lib_file="Connector_Generic", entry_name="Conn_01x05", nickname="Connector_Generic",
          value="Debug breakout (SWDIO,SWCLK,NRST,3.3V,GND)", footprint="Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical",
          pins={"1": "SWDIO", "2": "SWCLK", "3": "NRST", "4": "3V3", "5": "GND"},
          x=100, y=70, mpn="PREC005SAAN-RC", manufacturer="Sullins", digikey_pn="S7036-ND",
          datasheet="https://www.sullinscorp.com/media/UserFiles/document/PREC005SAAN-RC.pdf"),

        P(ref="D6", lib_file="PROJECT", entry_name="TPD4E001DBVR", nickname="red-light-panel",
          value="TPD4E001DBVR (corrected from BOM's TPD4E001DZDR -- flag)", footprint="Package_TO_SOT_SMD:SOT-23-6",
          pins={"1": "BTN_PWR", "2": "GND", "3": "BTN_DIMP", "4": "BTN_DIMM", "5": "BTN_MODE", "6": "3V3"},
          x=140, y=70, mpn="TPD4E001DBVR", manufacturer="Texas Instruments",
          digikey_pn="296-TPD4E001DBVRCT-ND", datasheet="https://www.ti.com/lit/ds/symlink/tpd4e001.pdf"),

        P(ref="D7", lib_file="PROJECT", entry_name="TPD4E001DBVR", nickname="red-light-panel",
          value="TPD4E001DBVR (corrected from BOM's TPD4E001DZDR -- flag)", footprint="Package_TO_SOT_SMD:SOT-23-6",
          pins={"1": "SWDIO", "2": "GND", "3": "SWCLK", "4": "NRST", "5": "NC", "6": "3V3"},
          x=175, y=70, mpn="TPD4E001DBVR", manufacturer="Texas Instruments",
          digikey_pn="296-TPD4E001DBVRCT-ND", datasheet="https://www.ti.com/lit/ds/symlink/tpd4e001.pdf"),
    ]

    for part in parts:
        add_part(sch, part, PROJECT, embedded)

    # 3V3's genuine driver lives on sheet 3; GND still needs a flag here
    # since this sheet has power_in pins on it (U7 VSS) and no local
    # power_out source.
    add_pwr_flag(sch, "GND", 60, 90, embedded)

    out = "/Users/lucaspoulos/kicad-projects/red-light-panel/06_mcu_control.kicad_sch"
    print(write_and_upgrade(sch, out))


if __name__ == "__main__":
    build()
