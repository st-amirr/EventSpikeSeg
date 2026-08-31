from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_fakeram_liberty_and_lef_parser(tmp_path: Path) -> None:
    path = ROOT / "scripts/generate_asap7_fakeram_catalog.py"
    spec = util.spec_from_file_location("asap7_fakeram_catalog", path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    platform = tmp_path / "asap7"
    liberty = platform / "lib/NLDM/fakeram7_256x32.lib"
    lef = platform / "lef/fakeram7_256x32.lef"
    liberty.parent.mkdir(parents=True)
    lef.parent.mkdir(parents=True)
    liberty.write_text(
        """library(x) {
cell(fakeram7_256x32) {
  area : 412.5;
  memory() {
    address_width : 8;
    word_width : 32;
  }
  pin(clk) {
    min_period : 0.157;
  }
  cell_leakage_power : 12.25;
}}
""",
        encoding="utf-8",
    )
    lef.write_text(
        """VERSION 5.7 ;
MACRO fakeram7_256x32
  SIZE 12.5 BY 33.0 ;
END fakeram7_256x32
""",
        encoding="utf-8",
    )
    macro = module.parse_macro(liberty, lef, platform)
    assert macro["name"] == "fakeram7_256x32"
    assert macro["ports"] == "1RW"
    assert macro["word_bits"] == 32
    assert macro["depth"] == 256
    assert macro["area_um2"] == 412.5
    assert macro["leakage_uW"] == 12.25
    assert macro["minimum_clock_period_ns"] == 0.157
