"""
Sheet 5 -- LED Array (64x Luminus SST-10-DR-B130-K660, 660nm deep red).

**Topology (not specified by the BOM table itself -- derived and flagged
for review):** 64 LEDs split 32/32 across the two driver channels from
sheet 4. Each channel's 32 LEDs are arranged as 8 parallel strings of 4
LEDs in series (not one long series string -- at ~2.1V Vf per LED, a
32-LED series string would need ~67V, far above this design's ~14-17V
(4S Li-ion) rail; 4-in-series keeps each string's forward voltage
(~8.4V) comfortably under the buck driver's input with headroom for the
switch/inductor). At LM3409HV's typical ~100mV current-sense threshold
over R4/R5's 0.02ohm sense resistor, total channel current is ~5A, i.e.
~625mA per string/per LED -- within the SST-10 family's high-power rating
but **flagged**: exact string count/current split and total ~74W-class
power budget need real verification against the Luminus datasheet's
max-current and thermal-derating curves, not just this default split.

Reference designators: D5-D36 = channel A (8 strings x 4 series),
D37-D68 = channel B, matching the brief's D5-D68 range exactly.

**Footprint**: no 3-pad "3535" LED footprint exists in KiCad's stock
libraries (only 2-pad or 4-pad PLCC parts under that body-size name).
Built a custom 3-pad footprint (libs/red-light-panel.pretty/
LUMINUS_SST-10-3535.kicad_mod: anode / center thermal-only pad / cathode)
from the datasheet's mechanical drawing dimensions found during sourcing
research (~3.45x3.45mm body, three ~2.7x1.0mm pad rows). The center
thermal pad is left unconnected (NC) here -- if it should be tied to a
ground/thermal plane on the real board, that's a PCB-layout decision
beyond this schematic-generation pass.

J4/J5 are simple pass-through connectors on the same LED_A+/LED_A-
(LED_B+/LED_B-) nets -- representing "this is where the array cable
plugs in" rather than a separate electrical node, since a mated connector
doesn't create a new net.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kicad_gen.builder import build_schematic, add_part, add_pwr_flag, write_and_upgrade, Part

PROJECT = "red-light-panel"
SHEET = "5"

LED_MPN = "SST-10-DR-B130-K660"
LED_MANUF = "Luminus Devices"
LED_DK = "1462-SST-10-DR-B130-K660-ND (verify exact reel/tape SKU)"
LED_DS = "https://download.luminus.com/datasheets/Luminus_SST-10-DR_Datasheet.pdf"
LED_FP = "red-light-panel:LUMINUS_SST-10-3535"


def build():
    sch = build_schematic("LED Array", "05_led_array")
    embedded = set()

    def P(**kw):
        kw.setdefault("sheet", SHEET)
        return Part(**kw)

    parts = []
    next_ref = 5  # D5..D68

    def build_channel(ch_letter, x0, y0, plus_net, minus_net):
        nonlocal next_ref
        for string_i in range(8):
            x = x0 + string_i * 12
            prev_net = plus_net
            for pos_i in range(4):
                ref = f"D{next_ref}"
                next_ref += 1
                y = y0 + pos_i * 15
                is_last = pos_i == 3
                cathode_net = minus_net if is_last else f"LED_{ch_letter}_S{string_i}_N{pos_i}"
                parts.append(P(
                    ref=ref, lib_file="Device", entry_name="LED", nickname="Device",
                    value=LED_MPN, footprint=LED_FP,
                    pins={"1": cathode_net, "2": prev_net},
                    x=x, y=y, mpn=LED_MPN, manufacturer=LED_MANUF,
                    digikey_pn=LED_DK, datasheet=LED_DS,
                ))
                prev_net = cathode_net

    build_channel("A", 20, 20, "LED_A+", "LED_A-")
    build_channel("B", 150, 20, "LED_B+", "LED_B-")

    parts.append(P(ref="J4", lib_file="Connector_Generic", entry_name="Conn_01x02", nickname="Connector_Generic",
                   value="2-pin screw terminal / JST-PH-2", footprint="Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
                   pins={"1": "LED_A+", "2": "LED_A-"}, x=20, y=110,
                   mpn="B2B-PH-K-S(LF)(SN)", manufacturer="JST", digikey_pn="455-1728-ND",
                   datasheet="https://www.jst-mfg.com/product/pdf/eng/ePH.pdf"))
    parts.append(P(ref="J5", lib_file="Connector_Generic", entry_name="Conn_01x02", nickname="Connector_Generic",
                   value="2-pin screw terminal / JST-PH-2", footprint="Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
                   pins={"1": "LED_B+", "2": "LED_B-"}, x=150, y=110,
                   mpn="B2B-PH-K-S(LF)(SN)", manufacturer="JST", digikey_pn="455-1728-ND",
                   datasheet="https://www.jst-mfg.com/product/pdf/eng/ePH.pdf"))

    parts.append(P(ref="RT1", lib_file="Device", entry_name="Thermistor_NTC", nickname="Device",
                   value="NCP18XH103F03RB (10k NTC)", footprint="Resistor_SMD:R_0603_1608Metric",
                   pins={"1": "NTC_SENSE", "2": "GND"}, x=90, y=110,
                   mpn="NCP18XH103F03RB", manufacturer="Murata", digikey_pn="490-16279-1-ND",
                   datasheet="https://www.murata.com/-/media/webrenewal/support/library/catalog/products/thermistor/ntc/r44e.ashx"))

    for part in parts:
        add_part(sch, part, PROJECT, embedded)

    # NTC_SENSE needs a pull-up to 3V3 to form a voltage divider with RT1
    # (added, flagged -- required for the MCU's ADC to read a meaningful
    # voltage; not itemized as a separate BOM row).
    pullup = P(ref="R98", lib_file="Device", entry_name="R", nickname="Device",
               value="10k (added, flagged -- NTC divider pull-up)", footprint="Resistor_SMD:R_0603_1608Metric",
               pins={"1": "3V3", "2": "NTC_SENSE"}, x=90, y=95,
               mpn="", manufacturer="", digikey_pn="", datasheet="")
    add_part(sch, pullup, PROJECT, embedded)

    add_pwr_flag(sch, "GND", 60, 120, embedded)

    out = "/Users/lucaspoulos/kicad-projects/red-light-panel/05_led_array.kicad_sch"
    print(write_and_upgrade(sch, out))


if __name__ == "__main__":
    build()
