"""
Sheet 4 -- LED Drivers (2 channels, A & B).

Each LM3409HVMY channel follows TI's standard PFET-buck constant-current
topology: VIN -> P-FET (source) -> P-FET (drain) -> SW node -> inductor ->
LED string -> current-sense resistor -> GND, with the Schottky catching
freewheel current into the SW node when the FET is off, and CSP/CSN
sensing across the sense resistor to regulate LED current.

- **Q4/Q5 30V margin**: the brief flags "verify 30V margin, not 20V" for
  the external buck-switch FET. AO3401A is rated -30V Vds (confirmed via
  its own datasheet, already used elsewhere in this project) -- it
  already satisfies this without substitution.
- **EN <- PWM_A/PWM_B** (cross-sheet from the MCU, per the brief's own net
  map) drives on/off PWM dimming. **IADJ tied directly to VCC** (fixed
  max analog current set by RSNS, since dimming here is PWM-only via EN --
  no separate analog-dimming net was specified in the brief).
- **Flagged additions** (required by LM3409HV's own datasheet application
  circuit, not itemized as separate BOM rows):
    R94/R96 COFF timing resistor (VIN->COFF), C94/C95 COFF timing cap
      (COFF->GND) -- sets switching off-time; needs a real frequency calc
      against L2/L3's chosen inductance, not just a default value here.
    R95/R97 UVLO pull-up (VIN->UVLO) -- simple always-on tie, not a
      calculated threshold divider; flag if a specific UVLO threshold
      matters for your application.
    DAP (thermal pad) tied to GND per datasheet.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kicad_gen.builder import build_schematic, add_part, add_pwr_flag, write_and_upgrade, Part

PROJECT = "red-light-panel"
SHEET = "4"


def build():
    sch = build_schematic("LED Drivers (2 channels)", "04_led_drivers")
    embedded = set()

    def P(**kw):
        kw.setdefault("sheet", SHEET)
        return Part(**kw)

    def channel(ch, x0, u_ref, q_ref, d_ref, l_ref, r_ref, c_vcc1, c_vcc2, c_out,
                r_coff, c_coff, r_uvlo, pwm_net, led_p, led_n):
        sw = f"U{ch}_SW"
        gate = f"U{ch}_PGATE"
        vcc = f"U{ch}_VCC"
        coff = f"U{ch}_COFF"
        uvlo = f"U{ch}_UVLO"
        csn = f"U{ch}_CSN"
        return [
            P(ref=u_ref, lib_file="PROJECT", entry_name="LM3409HVMY_NOPB", nickname="red-light-panel",
              value="LM3409HVMY/NOPB", footprint="Package_SO:HVSSOP-10-1EP_3x3mm_P0.5mm_EP1.83x1.89mm",
              pins={"1": uvlo, "2": vcc, "3": pwm_net, "4": coff, "5": "GND", "6": gate,
                    "7": csn, "8": led_n, "9": vcc, "10": "VBAT_PROT", "11": "GND"},
              x=x0, y=20, mpn="LM3409HVMY/NOPB", manufacturer="Texas Instruments",
              digikey_pn="296-30489-1-ND", datasheet="https://www.ti.com/lit/ds/symlink/lm3409hv.pdf"),

            P(ref=q_ref, lib_file="Transistor_FET", entry_name="AO3401A", nickname="Transistor_FET",
              value="AO3401A (30V Vds, satisfies brief's margin flag)", footprint="Package_TO_SOT_SMD:SOT-23",
              pins={"1": gate, "2": "VBAT_PROT", "3": sw}, x=x0 + 30, y=20,
              mpn="AO3401A", manufacturer="Alpha & Omega Semiconductor", digikey_pn="AO3401A-DICT-ND",
              datasheet="http://www.aosmd.com/pdfs/datasheet/AO3401A.pdf"),

            P(ref=d_ref, lib_file="Device", entry_name="D_Schottky", nickname="Device",
              value="SS54", footprint="Diode_SMD:D_SMA",
              pins={"1": sw, "2": "GND"}, x=x0 + 30, y=45,
              mpn="SS54", manufacturer="onsemi/Diodes Inc (generic SS54)", digikey_pn="SS54-E3/57TCT-ND",
              datasheet="https://www.diodes.com/assets/Datasheets/ds30051.pdf"),

            P(ref=l_ref, lib_file="Device", entry_name="L", nickname="Device",
              value="IHLP2525CZERR10M01 (0.10uH)", footprint="Inductor_SMD:L_Vishay_IHLP-2525",
              pins={"1": sw, "2": led_p}, x=x0 + 60, y=20,
              mpn="IHLP2525CZERR10M01", manufacturer="Vishay Dale", digikey_pn="541-2724-1-ND",
              datasheet="https://www.vishay.com/docs/34037/ihlp2525cz.pdf"),

            P(ref=r_ref, lib_file="Device", entry_name="R", nickname="Device",
              value="0.02R 1%", footprint="Resistor_SMD:R_Shunt_Vishay_WSK2512_6332Metric_T2.21mm",
              pins={"1": led_n, "2": csn}, x=x0, y=70,
              mpn="WSL2512R0200FEA", manufacturer="Vishay Dale", digikey_pn="541-2456-1-ND",
              datasheet="https://www.vishay.com/docs/30112/wsl.pdf"),

            P(ref=c_vcc1, lib_file="Device", entry_name="C", nickname="Device",
              value="0.1uF", footprint="Capacitor_SMD:C_0603_1608Metric",
              pins={"1": vcc, "2": "GND"}, x=x0, y=45,
              mpn="CC0603KRX7R9BB104", manufacturer="Yageo", digikey_pn="311-1367-1-ND", datasheet=""),
            P(ref=c_vcc2, lib_file="Device", entry_name="C", nickname="Device",
              value="0.1uF", footprint="Capacitor_SMD:C_0603_1608Metric",
              pins={"1": vcc, "2": "GND"}, x=x0 + 15, y=45,
              mpn="CC0603KRX7R9BB104", manufacturer="Yageo", digikey_pn="311-1367-1-ND", datasheet=""),
            P(ref=c_out, lib_file="Device", entry_name="C", nickname="Device",
              value="10uF", footprint="Capacitor_SMD:C_1206_3216Metric",
              pins={"1": led_p, "2": led_n}, x=x0 + 60, y=45,
              mpn="CC1206KKX7R8BB106", manufacturer="Yageo", digikey_pn="311-4622-1-ND", datasheet=""),

            P(ref=r_coff, lib_file="Device", entry_name="R", nickname="Device",
              value="100k (added, flagged -- COFF timing, calc vs L freq)", footprint="Resistor_SMD:R_0603_1608Metric",
              pins={"1": "VBAT_PROT", "2": coff}, x=x0 + 90, y=20,
              mpn="", manufacturer="", digikey_pn="", datasheet=""),
            P(ref=c_coff, lib_file="Device", entry_name="C", nickname="Device",
              value="100pF (added, flagged -- COFF timing, calc vs L freq)", footprint="Capacitor_SMD:C_0603_1608Metric",
              pins={"1": coff, "2": "GND"}, x=x0 + 90, y=35,
              mpn="", manufacturer="", digikey_pn="", datasheet=""),
            P(ref=r_uvlo, lib_file="Device", entry_name="R", nickname="Device",
              value="100k (added, flagged -- UVLO always-on pull-up, no set threshold)",
              footprint="Resistor_SMD:R_0603_1608Metric",
              pins={"1": "VBAT_PROT", "2": uvlo}, x=x0 + 90, y=50,
              mpn="", manufacturer="", digikey_pn="", datasheet=""),
        ]

    parts = []
    parts += channel(5, 20, "U5", "Q4", "D3", "L2", "R4", "C8", "C9", "C12",
                      "R94", "C94", "R95", "PWM_A", "LED_A+", "LED_A-")
    parts += channel(6, 150, "U6", "Q5", "D4", "L3", "R5", "C10", "C11", "C13",
                      "R96", "C95", "R97", "PWM_B", "LED_B+", "LED_B-")

    for part in parts:
        add_part(sch, part, PROJECT, embedded)

    # VBAT_PROT's only project-wide source is sheet 1's protection FET
    # drain pin, which is typed "passive" (not power_out) -- so unlike
    # VBAT/3V3, VBAT_PROT has no genuine power_out driver anywhere and
    # does need a flag. GND likewise always needs one.
    add_pwr_flag(sch, "GND", 20, 85, embedded)
    add_pwr_flag(sch, "VBAT_PROT", 35, 85, embedded)

    out = "/Users/lucaspoulos/kicad-projects/red-light-panel/04_led_drivers.kicad_sch"
    print(write_and_upgrade(sch, out))


if __name__ == "__main__":
    build()
