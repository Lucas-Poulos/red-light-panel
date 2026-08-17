"""
Programmatic KiCad 10 schematic builder for the red-light-panel project.

Strategy (empirically validated against a real kicad-cli 10.0.5 install --
see docs/design_notes.md "Schematic generation approach"):

  1. Build the schematic with `kiutils` (targets KiCad 8-era format, which
     is what kiutils 1.4.8 emits reliably).
  2. Post-process the raw text for two kiutils gaps vs. the real format:
       - `(generator kiutils)` -> `(generator "eeschema")` +
         `(generator_version "8.0")` (kiutils doesn't emit this token at all)
       - bare `(uuid XXXXXXXX-...)` -> quoted `(uuid "XXXXXXXX-...")`
         (kiutils doesn't quote UUID-shaped tokens; KiCad 10's loader
         rejects the file outright without quotes)
  3. Run `kicad-cli sch upgrade --force` to have KiCad 10 itself rewrite
     the file to its true native format (version 20260306, generator_version
     "10.0" as of KiCad 10.0.5). This is the authoritative normalization
     step -- we never hand-guess the v10 format.

Connectivity uses the "flying label" technique: every pin that needs to be
on a net gets its own Local/Hierarchical/Global label placed at that pin's
exact world coordinate (symbol position + pin's local offset -- all parts
are placed unrotated/unmirrored, so no rotation transform is needed). Two
labels with the same text are the same net even with no wire between them,
as long as each is itself coincident with a real pin -- standard KiCad
connectivity semantics, avoids needing to hand-route ~150 components.
"""
import copy
import re
import subprocess
import uuid as uuidlib
from dataclasses import dataclass, field
from typing import Optional

from kiutils.symbol import SymbolLib, Symbol
from kiutils.schematic import (
    Schematic, SchematicSymbol, HierarchicalSheetInstance,
    SymbolProjectInstance, SymbolProjectPath, HierarchicalLabel, GlobalLabel,
    LocalLabel, HierarchicalSheet, HierarchicalPin, TitleBlock, NoConnect,
)
from kiutils.items.common import Position, Effects, Property, PageSettings

STOCK_SYM_DIR = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
PROJECT_LIBS_DIR = "/Users/lucaspoulos/kicad-projects/red-light-panel/libs"
_lib_cache: dict[str, SymbolLib] = {}


def _load_lib(lib_filename: str) -> SymbolLib:
    if lib_filename not in _lib_cache:
        _lib_cache[lib_filename] = SymbolLib.from_file(f"{STOCK_SYM_DIR}/{lib_filename}.kicad_sym")
    return _lib_cache[lib_filename]


def load_project_symbol(entry_name: str, nickname: str):
    """Same idea as load_stock_symbol() but for hand-built/downloaded
    symbols living in the single merged libs/red-light-panel.kicad_sym
    (project-local library, matching the project-local sym-lib-table
    entry)."""
    cache_key = "PROJECT:red-light-panel"
    if cache_key not in _lib_cache:
        _lib_cache[cache_key] = SymbolLib.from_file(f"{PROJECT_LIBS_DIR}/red-light-panel.kicad_sym")
    lib = _lib_cache[cache_key]
    sym = copy.deepcopy(next(s for s in lib.symbols if s.entryName == entry_name))
    sym.libraryNickname = nickname
    return sym, None


def load_stock_symbol(lib_filename: str, entry_name: str, nickname: str):
    """Returns (symbol_copy, base_copy_or_None). base_copy is the `extends`
    target (unprefixed nickname, resolves by bare name within the cache),
    or None if entry_name is fully self-contained.

    `extends`-based symbols (e.g. AO3401A extends TP0610T, CSD18540Q5B
    extends Q_NMOS_SSSGD_AvalancheRated) are FLATTENED here -- the base's
    units/graphics are copied directly onto the derived symbol and the
    `extends` pointer is dropped, rather than embedding two linked cache
    entries. This was empirically necessary: even with the base library
    correctly registered in the project's sym-lib-table (so the file loads
    fine and ERC only reports the expected benign "doesn't match copy in
    library" warning), kicad-cli's ERC pin-position resolution for a
    still-`extends`-linked placed instance did not reliably match the raw
    pin coordinates pulled from the base symbol -- every pin on every
    extends-based part came back as a dangling label. Flattening removes
    the ambiguity entirely (pin data then comes from the one object that's
    actually placed). Confirmed reproducible in this project; matches a
    prior project's independently-documented reason for the same fix."""
    lib = _load_lib(lib_filename)
    sym = copy.deepcopy(next(s for s in lib.symbols if s.entryName == entry_name))
    sym.libraryNickname = nickname
    if sym.extends:
        base = next(s for s in lib.symbols if s.entryName == sym.extends)
        sym.units = copy.deepcopy(base.units)
        for u in sym.units:
            u.entryName = entry_name  # child block names must match the parent's
        sym.extends = None
    return sym, None


def get_unit_pins(symbol: Symbol, base: Optional[Symbol] = None, unit: int = 1):
    """Union of pins across styleId 0 (shared-across-styles graphics) and
    styleId 1 (the only style we ever use) for the given electrical unit
    number. Looks at `base` too if the symbol itself carries no direct
    units (i.e. is an `extends`-only property-holder)."""
    pins = {}
    src = symbol if symbol.units else (base if base else symbol)
    for u in src.units:
        if u.unitId in (0, unit):
            for p in u.pins:
                pins[p.number] = p
    return pins


@dataclass
class Part:
    ref: str
    lib_file: str          # stock .kicad_sym filename (no extension), or "PROJECT"
    entry_name: str        # symbol name inside that library
    nickname: str          # sym-lib-table nickname to reference it by
    value: str
    footprint: str          # "Library:Footprint" (empty string => no footprint, flagged)
    pins: dict              # {pin_number: net_name}  -- net_name None/"" => leave unconnected (flagged if not intentional)
    x: float
    y: float
    mpn: str = ""
    manufacturer: str = ""
    digikey_pn: str = ""
    datasheet: str = ""
    sheet: str = ""
    unit: int = 1
    dnp: bool = False
    project_symbol: Optional[str] = None   # libs/<project_symbol>.kicad_sym filename, when lib_file=="PROJECT"


def _prop(key, value, x, y, hide=False, show_name=False):
    return Property(key=key, value=value, position=Position(x, y, 0), effects=Effects(hide=hide), showName=show_name)


def build_schematic(title: str, comment: str = "") -> Schematic:
    sch = Schematic(version="20231120", generator="eeschema")
    sch.uuid = str(uuidlib.uuid4())
    sch.paper = PageSettings(paperSize="A3")
    sch.titleBlock = TitleBlock(title=title, comments={1: comment} if comment else {})
    sch.libSymbols = []
    sch.schematicSymbols = []
    sch.hierarchicalLabels = []
    sch.globalLabels = []
    sch.labels = []
    sch.noConnects = []
    sch.sheets = []
    sch.sheetInstances = [HierarchicalSheetInstance(instancePath="/", page="1")]
    return sch


_embedded_lib_ids: set[str] = None  # set per-schematic by caller convention (see add_part)


def add_part(sch: Schematic, part: Part, project_name: str, embedded: set):
    """Adds `part`'s lib symbol(s) (if not already embedded) + a placed
    SchematicSymbol instance to `sch`. `embedded` tracks lib_ids already
    copied into sch.libSymbols so repeated part types aren't duplicated."""
    if part.lib_file == "PROJECT":
        sym, base = load_project_symbol(part.entry_name, part.nickname)
    else:
        sym, base = load_stock_symbol(part.lib_file, part.entry_name, part.nickname)

    lib_id = f"{part.nickname}:{part.entry_name}"
    if lib_id not in embedded:
        sch.libSymbols.append(sym)
        if base is not None:
            sch.libSymbols.append(base)
        embedded.add(lib_id)

    pins_def = get_unit_pins(sym, base, part.unit)
    pin_uuids = {num: str(uuidlib.uuid4()) for num in pins_def}

    props = [
        _prop("Reference", part.ref, part.x + 5, part.y - 6),
        _prop("Value", part.value, part.x + 5, part.y - 4),
        _prop("Footprint", part.footprint, part.x + 5, part.y - 2, hide=True),
        _prop("Datasheet", part.datasheet, part.x + 5, part.y, hide=True),
        _prop("MPN", part.mpn, part.x + 5, part.y + 2, hide=True, show_name=True),
        _prop("Manufacturer", part.manufacturer, part.x + 5, part.y + 4, hide=True, show_name=True),
        _prop("DigiKey_PN", part.digikey_pn, part.x + 5, part.y + 6, hide=True, show_name=True),
        _prop("Sheet", part.sheet, part.x + 5, part.y + 8, hide=True, show_name=True),
    ]

    sym_uuid = str(uuidlib.uuid4())
    inst = SchematicSymbol(
        libraryNickname=part.nickname,
        entryName=part.entry_name,
        position=Position(part.x, part.y, 0),
        unit=part.unit,
        inBom=(part.footprint != "" or True),
        onBoard=True,
        dnp=part.dnp,
        uuid=sym_uuid,
        properties=props,
        pins=pin_uuids,
        instances=[SymbolProjectInstance(
            name=project_name,
            paths=[SymbolProjectPath(sheetInstancePath="/", reference=part.ref, unit=part.unit)],
        )],
    )
    sch.schematicSymbols.append(inst)

    # flying labels: one per pin that has a net assigned. "NC" places an
    # explicit no-connect flag instead of a label (for intentionally-unused
    # pins -- avoids ERC "pin not connected" without inventing a fake net).
    #
    # Uses GlobalLabel (not LocalLabel) -- empirically confirmed (against a
    # real kicad-cli 10.0.5 install, cross-checked against a prior project's
    # ERC-clean, wire-free schematics) to connect directly to a coincident
    # pin with zero wires. This project's net names are unique per sheet
    # (except the intentionally-shared cross-sheet nets), so using "global"
    # scope throughout doesn't risk unintended merges -- and it means a net
    # crosses sheet boundaries by name alone, without needing separate
    # hierarchical sheet-symbol pins wired on the root sheet. See
    # docs/design_notes.md "Why global labels instead of sheet pins".
    #
    # IMPORTANT pin-position quirk (also confirmed empirically): KiCad's
    # symbol library editor uses a Y-up coordinate system, but placed
    # schematic coordinates are Y-down -- so a pin's world position is
    # (symbol.x + pin.local_x, symbol.y - pin.local_y), NOT a straight add.
    for num, net in part.pins.items():
        if not net:
            continue
        p = pins_def.get(num)
        if p is None:
            raise ValueError(f"{part.ref}: pin {num} not found on {lib_id} (available: {sorted(pins_def)})")
        wx, wy = part.x + p.position.X, part.y - p.position.Y
        if net == "NC":
            sch.noConnects.append(NoConnect(position=Position(wx, wy), uuid=str(uuidlib.uuid4())))
        else:
            lbl = GlobalLabel(text=net, shape="passive", position=Position(wx, wy, 0), uuid=str(uuidlib.uuid4()))
            sch.globalLabels.append(lbl)

    return pins_def


def add_hier_label(sch: Schematic, net: str, x: float, y: float, shape: str = "bidirectional"):
    sch.hierarchicalLabels.append(HierarchicalLabel(
        text=net, shape=shape, position=Position(x, y, 0), uuid=str(uuidlib.uuid4()),
    ))


def add_global_label(sch: Schematic, net: str, x: float, y: float, shape: str = "bidirectional"):
    sch.globalLabels.append(GlobalLabel(
        text=net, shape=shape, position=Position(x, y, 0), uuid=str(uuidlib.uuid4()),
    ))


def add_pwr_flag(sch: Schematic, net: str, x: float, y: float, embedded: set, nickname="power"):
    """Places a Device:PWR_FLAG on `net` to satisfy ERC's power_pin_not_driven
    check without needing a genuine power_out source pin. Excluded from BOM
    and board per KiCad convention for this symbol."""
    sym, base = load_stock_symbol("power", "PWR_FLAG", nickname)
    lib_id = f"{nickname}:PWR_FLAG"
    if lib_id not in embedded:
        sch.libSymbols.append(sym)
        embedded.add(lib_id)
    pins_def = get_unit_pins(sym, base, 1)
    sym_uuid = str(uuidlib.uuid4())
    inst = SchematicSymbol(
        libraryNickname=nickname, entryName="PWR_FLAG",
        position=Position(x, y, 0), unit=1, inBom=False, onBoard=False, dnp=False,
        uuid=sym_uuid,
        properties=[
            _prop("Reference", "#FLG", x + 3, y - 3),
            _prop("Value", "PWR_FLAG", x + 3, y - 1),
        ],
        pins={num: str(uuidlib.uuid4()) for num in pins_def},
        instances=[SymbolProjectInstance(name="red-light-panel", paths=[
            SymbolProjectPath(sheetInstancePath="/", reference="#FLG", unit=1)])],
    )
    sch.schematicSymbols.append(inst)
    for num, p in pins_def.items():
        wx, wy = x + p.position.X, y - p.position.Y
        sch.globalLabels.append(GlobalLabel(text=net, shape="passive", position=Position(wx, wy, 0), uuid=str(uuidlib.uuid4())))


def _normalize_text(raw: str) -> str:
    raw = raw.replace('(generator kiutils)', '(generator "eeschema")\n\t(generator_version "8.0")')
    raw = raw.replace('(generator eeschema)', '(generator "eeschema")\n\t(generator_version "8.0")')
    raw = re.sub(r'\(uuid ([0-9a-fA-F-]{36})\)', r'(uuid "\1")', raw)
    return raw


def write_and_upgrade(sch: Schematic, path: str):
    sch.to_file(path)
    with open(path) as f:
        content = f.read()
    content = _normalize_text(content)
    with open(path, "w") as f:
        f.write(content)
    result = subprocess.run(
        ["kicad-cli", "sch", "upgrade", "--force", path],
        capture_output=True, text=True,
    )
    out = result.stdout + result.stderr
    if "Successfully saved" not in out:
        raise RuntimeError(f"kicad-cli sch upgrade failed for {path}:\n{out}")
    return out
