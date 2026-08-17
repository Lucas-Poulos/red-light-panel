"""
Sheet 2 -- USB-C Charging Input.

Both U2 (TPS25751DREFR, PD sink controller + integrated power-path switch)
and U3 (BQ25792RQMR, buck-boost charger) are hand-built symbols (see
libs/*.kicad_sym and README.md "Known open items" -- the research that
sourced them flagged several individual pin-electrical-type judgment calls
on ambiguous datasheet entries). This sheet's own topology adds more
judgment calls of its own, all flagged here rather than silently guessed:

- **TPS25751 PPHV/DRAIN power path**: TI's datasheet is ambiguous about
  which side of the internal FET is which (both pin groups have entries
  flagged "N/A"/"I/O" by TI directly). Modeled here as: VBUS_IN (from the
  connector) -> internal switch -> PPHV/DRAIN tied together as one node
  "PD_PP_OUT" -> feeds BQ25792's VBUS. This is a best-effort interpretation,
  not confirmed against TI's own reference design -- FLAG FOR REVIEW.
- **TPS25751 PP5V tied to VBUS_IN**: assumes a fixed-5V/no-PD-negotiated
  bootstrap path for the controller's own bias rail. FLAG FOR REVIEW.
- **BQ25792 ACDRV1/ACDRV2/BTST1/BTST2 left NC**: TI's real BQ25792
  reference design needs external ACFET/RBFET1/RBFET2 ideal-diode MOSFETs
  driven from these pins -- NOT itemized in the original BOM. Rather than
  invent 2-3 more MOSFETs and their part numbers unprompted, these pins
  are left explicit no-connects and flagged here for the user to decide
  whether to add that front-end. **This means the charger's front-end
  reverse-blocking/ideal-diode stage is incomplete as generated.**
- **BQ25792 SW1/SW2 buck-boost inductor**: REQUIRED for the charger to
  function at all, but not itemized as a separate BOM row. Added as L90,
  flagged, placeholder 2.2uH/hand-wound-class footprint -- exact
  inductance/saturation-current needs a real calculation against your
  target charge current, not just default value here.
- **BQ25792 ILIM_HIZ / PROG resistors**: analog set-point pins, each need
  an external resistor per TI's design equations. Added as R91/R92,
  flagged, placeholder values.
- **BQ25792 CE/QON tied directly to GND**: always-enabled simplification
  (no MCU GPIO reserved for charge-enable in the given net map).
- **I2C bus assignment**: per the brief's own net map ("I2C_SDA, I2C_SCL
  ... Sheet 6 MCU -> Sheets 1 and 2, BQ76920 and BQ25792"), the MCU talks
  directly to BQ25792 over the shared I2C_SDA/I2C_SCL bus. TPS25751's
  *controller-facing* bus (I2Ct_SDA/SCL) is wired to that same shared bus;
  its *companion* bus (I2Cc_SDA/SCL/IRQ) is left NC since this design
  doesn't use a private PD-to-charger side channel.
- **D8 status LED is single-color** (per your decision -- the original BOM
  MPN wasn't a real bi-color part): only STAT_LED_R is used, driven from
  BQ25792's STAT pin, matching the brief's own net-map line.
- **J3 exact GCT USB4105 suffix**: plating/stake-length TBD (there is no
  "mount style" suffix -- confirmed by research, the whole series is one
  fixed SMT top-mount style). Defaulted to USB4105-GF-A (standard gold
  flash plating, 0.95mm stake) -- FLAG FOR REVIEW against your actual
  reel/tape spec.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kicad_gen.builder import build_schematic, add_part, add_pwr_flag, write_and_upgrade, Part

PROJECT = "red-light-panel"
SHEET = "2"


def build():
    sch = build_schematic("USB-C Charging Input", "02_usbc_charging")
    embedded = set()

    def P(**kw):
        kw.setdefault("sheet", SHEET)
        return Part(**kw)

    parts = []

    parts.append(P(ref="J3", lib_file="Connector", entry_name="USB_C_Receptacle_USB2.0_16P", nickname="Connector",
                   value="USB4105-GF-A (plating/stake length TBD, flag)",
                   footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
                   pins={"A1": "GND", "A4": "USB_VBUS", "A5": "CC1", "A6": "USB_DP", "A7": "USB_DN",
                         "A8": "NC", "A9": "USB_VBUS", "A12": "GND", "B1": "GND", "B4": "USB_VBUS",
                         "B5": "CC2", "B6": "USB_DP", "B7": "USB_DN", "B8": "NC", "B9": "USB_VBUS",
                         "B12": "GND", "SH": "GND"},
                   x=20, y=20, mpn="USB4105-GF-A", manufacturer="GCT",
                   digikey_pn="GCT USB4105-GF-A-ND (verify exact DigiKey SKU)",
                   datasheet="https://gct.co/files/drawings/usb4105.pdf"))

    parts.append(P(ref="D2", lib_file="PROJECT", project_symbol="TPD4S012DRYR", entry_name="TPD4S012DRYR", nickname="red-light-panel",
                   value="TPD4S012DRYR (corrected from BOM's TPD4S012DBVR -- flag)",
                   footprint="Package_SON:Texas_USON-6_1x1.45mm_P0.5mm_SMD",
                   pins={"1": "USB_DP", "2": "USB_DN", "3": "NC", "4": "GND", "5": "NC", "6": "USB_VBUS"},
                   x=60, y=20, mpn="TPD4S012DRYR", manufacturer="Texas Instruments",
                   digikey_pn="296-TPD4S012DRYRCT-ND", datasheet="https://www.ti.com/lit/ds/symlink/tpd4s012.pdf"))

    parts.append(P(ref="C1", lib_file="Device", entry_name="C", nickname="Device",
                   value="10uF", footprint="Capacitor_SMD:C_1206_3216Metric",
                   pins={"1": "USB_VBUS", "2": "GND"}, x=20, y=45,
                   mpn="CC1206KKX7R8BB106", manufacturer="Yageo", digikey_pn="311-4622-1-ND", datasheet=""))
    parts.append(P(ref="C2", lib_file="Device", entry_name="C", nickname="Device",
                   value="10uF", footprint="Capacitor_SMD:C_1206_3216Metric",
                   pins={"1": "USB_VBUS", "2": "GND"}, x=35, y=45,
                   mpn="CC1206KKX7R8BB106", manufacturer="Yageo", digikey_pn="311-4622-1-ND", datasheet=""))

    # --- U2 TPS25751DREFR: PD sink controller + integrated power path switch ---
    parts.append(P(ref="U2", lib_file="PROJECT", project_symbol="TPS25751DREFR", entry_name="TPS25751DREFR", nickname="red-light-panel",
                   value="TPS25751DREFR (active replacement for NRND TPS25750DRYR, per your decision)",
                   footprint="Package_DFN_QFN:Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4",
                   pins={"1": "U2_LDO_3V3", "2": "NC", "3": "NC", "4": "U2_LDO_1V5", "5": "NC", "6": "NC",
                         "7": "NC", "8": "I2C_SDA", "9": "I2C_SCL", "10": "NC", "11": "GND", "12": "GND",
                         "13": "NC", "14": "GND", "15": "PD_PP_OUT", "16": "NC", "17": "NC", "18": "NC",
                         "19": "NC", "20": "PD_PP_OUT", "21": "PD_PP_OUT", "22": "PD_PP_OUT",
                         "23": "USB_VBUS", "24": "USB_VBUS", "25": "USB_VBUS", "26": "USB_DP", "27": "USB_DN",
                         "28": "CC1", "29": "CC2", "30": "PD_PP_OUT", "31": "GND", "32": "PD_PP_OUT",
                         "33": "PD_PP_OUT", "34": "USB_VBUS", "35": "USB_VBUS", "36": "NC", "37": "NC",
                         "38": "3V3"},
                   x=110, y=20, mpn="TPS25751DREFR", manufacturer="Texas Instruments",
                   digikey_pn="296-TPS25751DREFR-ND (verify)", datasheet="https://www.ti.com/lit/ds/symlink/tps25751.pdf"))
    parts.append(P(ref="C3", lib_file="Device", entry_name="C", nickname="Device",
                   value="0.1uF", footprint="Capacitor_SMD:C_0603_1608Metric",
                   pins={"1": "U2_LDO_3V3", "2": "GND"}, x=110, y=50,
                   mpn="CC0603KRX7R9BB104", manufacturer="Yageo", digikey_pn="311-1367-1-ND", datasheet=""))
    parts.append(P(ref="C4", lib_file="Device", entry_name="C", nickname="Device",
                   value="0.1uF", footprint="Capacitor_SMD:C_0603_1608Metric",
                   pins={"1": "U2_LDO_1V5", "2": "GND"}, x=125, y=50,
                   mpn="CC0603KRX7R9BB104", manufacturer="Yageo", digikey_pn="311-1367-1-ND", datasheet=""))

    # --- U3 BQ25792RQMR: buck-boost charger ---
    parts.append(P(ref="U3", lib_file="PROJECT", project_symbol="BQ25792RQMR", entry_name="BQ25792RQMR", nickname="red-light-panel",
                   value="BQ25792RQMR",
                   footprint="Package_DFN_QFN:Texas_RQM0029A_VQFN-29_4x4mm_P0.4mm",
                   pins={"1": "STAT_LED_R", "2": "PD_PP_OUT", "3": "PD_PP_OUT", "4": "NC", "5": "U3_REGN",
                         "6": "USB_DP", "7": "USB_DN", "8": "NC", "9": "NC", "10": "NC", "11": "NC",
                         "12": "GND", "13": "GND", "14": "I2C_SCL", "15": "I2C_SDA", "16": "NC",
                         "17": "U3_ILIM_HIZ", "18": "VBAT", "19": "NC", "20": "U3_PROG", "21": "NC",
                         "22": "VBAT", "23": "VBAT", "24": "NC", "25": "NC", "26": "U3_SW2", "27": "GND",
                         "28": "U3_SW1", "29": "U3_PMID"},
                   x=190, y=20, mpn="BQ25792RQMR", manufacturer="Texas Instruments",
                   digikey_pn="296-BQ25792RQMR-ND (verify)", datasheet="https://www.ti.com/lit/ds/symlink/bq25792.pdf"))
    parts.append(P(ref="C5", lib_file="Device", entry_name="C", nickname="Device",
                   value="0.1uF", footprint="Capacitor_SMD:C_0603_1608Metric",
                   pins={"1": "U3_REGN", "2": "GND"}, x=190, y=50,
                   mpn="CC0603KRX7R9BB104", manufacturer="Yageo", digikey_pn="311-1367-1-ND", datasheet=""))

    # --- flagged-added support parts (see module docstring) ---
    parts.append(P(ref="L90", lib_file="Device", entry_name="L", nickname="Device",
                   value="2.2uH (added, flagged -- calc vs target charge current)",
                   footprint="Inductor_SMD:L_Vishay_IHLP-2525",
                   pins={"1": "U3_SW1", "2": "U3_SW2"}, x=210, y=50,
                   mpn="", manufacturer="", digikey_pn="", datasheet=""))
    parts.append(P(ref="R91", lib_file="Device", entry_name="R", nickname="Device",
                   value="10k (added, flagged -- ILIM_HIZ set resistor, calc per datasheet eqn)",
                   footprint="Resistor_SMD:R_0603_1608Metric",
                   pins={"1": "U3_ILIM_HIZ", "2": "GND"}, x=225, y=50,
                   mpn="", manufacturer="", digikey_pn="", datasheet=""))
    parts.append(P(ref="R92", lib_file="Device", entry_name="R", nickname="Device",
                   value="4.7k (added, flagged -- PROG set resistor, calc per datasheet eqn)",
                   footprint="Resistor_SMD:R_0603_1608Metric",
                   pins={"1": "U3_PROG", "2": "GND"}, x=240, y=50,
                   mpn="", manufacturer="", digikey_pn="", datasheet=""))
    parts.append(P(ref="C92", lib_file="Device", entry_name="C", nickname="Device",
                   value="1uF (added, flagged -- PMID bulk cap per typical app circuit)",
                   footprint="Capacitor_SMD:C_1206_3216Metric",
                   pins={"1": "U3_PMID", "2": "GND"}, x=190, y=65,
                   mpn="", manufacturer="", digikey_pn="", datasheet=""))
    for part in parts:
        add_part(sch, part, PROJECT, embedded)

    # USB_VBUS is externally sourced (the USB-C cable/charger), never
    # driven by a power_out pin anywhere in this design -- needs a flag.
    # GND likewise has no genuine power_out driver anywhere in the project.
    # VBAT and 3V3 are NOT flagged here: BQ25792's BAT pin (power_out) and
    # sheet 3's buck regulator VOUT pin are genuine drivers for those nets
    # project-wide, and PWR_FLAG conflicts with a genuine power_out pin on
    # the same net (confirmed empirically -- see docs/design_notes.md).
    add_pwr_flag(sch, "USB_VBUS", 20, 70, embedded)
    add_pwr_flag(sch, "GND", 40, 70, embedded)

    out = "/Users/lucaspoulos/kicad-projects/red-light-panel/02_usbc_charging.kicad_sch"
    print(write_and_upgrade(sch, out))


if __name__ == "__main__":
    build()
