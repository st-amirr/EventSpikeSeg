"""Build a routed 8-bit, four-bank SKY130 MIM comparator-trim array."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_cap_trim_weighted_array"
CELL = "sky130_cap_trim_weighted_array"
UNIT = "packet_cap_mim_2x2um"
IMAGE = "eventspikeseg:analog-layout"
RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
BANKS = ("COARSE_P", "COARSE_N", "FINE_P", "FINE_N")


def docker(entrypoint: str, args: list[str], *, stdin: str | None = None,
           timeout: int = 300, workdir: str | None = None) -> str:
    command = ["docker", "run", "--rm"]
    if stdin is not None:
        command.append("-i")
    command += ["-v", f"{ROOT}:/workspace", "-e",
                "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root"]
    if workdir:
        command += ["-w", workdir]
    command += ["--entrypoint", entrypoint, IMAGE, *args]
    result = subprocess.run(command, input=stdin, text=True, capture_output=True,
                            timeout=timeout, cwd=ROOT)
    log = result.stdout + result.stderr
    if result.returncode:
        raise RuntimeError(f"{entrypoint} failed ({result.returncode}):\n{log[-6000:]}")
    return log


def pin_name(kind: str, bank: str, bit: int) -> str:
    return f"{kind}_{bank}_B{bit}"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / "artifacts/analog_asic/layout/sky130_mim_packet_2x2" / f"{UNIT}.mag"
    sections: dict[str, list[tuple[int, int, int, int]]] = {}
    section = None
    for line in source.read_text(encoding="ascii").splitlines():
        if line.startswith("<< ") and line.endswith(" >>"):
            section = line[3:-3]
            continue
        if section and section not in {"labels", "end", "checkpaint", "properties"} and line.startswith("rect "):
            x1, y1, x2, y2 = map(int, line.split()[1:])
            sections.setdefault(section, []).append((x1, y1, x2, y2))

    # Each binary-weight group is a physical row. M4 carries the sample-side
    # pin; the MIM2 plate exits on M5, escapes above the lower-electrode M4
    # rail, then drops through a via stack to a separate M3 plate bus.
    x_pitch, y_pitch, bank_gap = 1200, 1100, 1500  # Magic coordinates, 0.005um units
    rows: list[tuple[str, int, int, int, int]] = []
    y0 = 0
    port = 1
    labels: list[str] = []
    for bank in BANKS:
        for bit in range(8):
            count = 1 << bit
            y = y0
            rows.append((bank, bit, count, y, port))
            width = (count - 1) * x_pitch + 1124
            state_label, plate_label = pin_name("STATE", bank, bit), pin_name("PLATE", bank, bit)
            labels += [f"rlabel metal4 s 10 {y+570} 100 {y+590} 4 {state_label}",
                       f"port {port} nsew", f"rlabel metal3 s 10 {y+810} 100 {y+890} 4 {plate_label}",
                       f"port {port+1} nsew"]
            port += 2
            y0 += y_pitch
        y0 += bank_gap

    custom_layers = {"metal3", "metal4", "metal5", "via3", "via4"}
    source_shapes = {layer: list(rects) for layer, rects in sections.items()}
    all_shapes: dict[str, list[tuple[int, int, int, int]]] = {
        layer: [] for layer in set(sections) | custom_layers}
    for bank, bit, count, y, _p in rows:
        for i in range(count):
            x = i*x_pitch
            for layer, rects in source_shapes.items():
                all_shapes.setdefault(layer, []).extend(
                    (x+x1, y+y1, x+x2, y+y2) for x1, y1, x2, y2 in rects)
            # MIM2 contact -> M5 access pad, routed clear of the cell's M4/M5
            # lower-plate via rail, then via4/via3 stack to the M3 row bus.
            all_shapes["metal5"].extend([(x+140, y+140, x+460, y+460),
                                         (x+280, y+300, x+320, y+850)])
            all_shapes["via4"].append((x+200, y+750, x+400, y+950))
            all_shapes["metal4"].append((x+200, y+750, x+400, y+950))
            all_shapes["via3"].append((x+200, y+750, x+400, y+950))
        width = (count-1)*x_pitch + 1124
        all_shapes["metal4"].append((0, y+565, width, y+600))
        all_shapes["metal3"].append((0, y+800, width, y+900))

    lines = ["magic", "tech sky130A", "magscale 1 2", "timestamp 0"]
    for layer, rects in all_shapes.items():
        if not rects:
            continue
        lines.append(f"<< {layer} >>")
        lines.extend(f"rect {x1} {y1} {x2} {y2}" for x1, y1, x2, y2 in rects)
    lines += ["<< labels >>", *labels, "<< end >>", ""]
    mag = OUT / f"{CELL}.mag"
    mag.write_text("\n".join(lines), encoding="ascii")

    # Validate distinct plate/state buses and unit count against a generated
    # reference netlist before detailed parasitic extraction.
    build = "\n".join([f"load {CELL}", "drc check", "drc count", "extract all", "ext2spice lvs",
                       "ext2spice scale off", f"ext2spice -o {CELL}.spice", f"gds write {CELL}.gds",
                       "save", "quit -noprompt", ""])
    log = docker("magic", ["-dnull", "-noconsole", "-rcfile", RC], stdin=build,
                 workdir=f"/workspace/{OUT.relative_to(ROOT).as_posix()}")
    (OUT / "magic_extract.log").write_text(log, encoding="utf-8")
    drc = re.search(r"Total DRC errors found: (\d+)", log)
    if not drc or drc.group(1) != "0":
        raise RuntimeError(f"Weighted trim array DRC failed:\n{log[-6000:]}")
    extracted_path = OUT / f"{CELL}.spice"
    extracted = extracted_path.read_text(encoding="ascii")
    header = re.search(rf"(?im)^\.subckt\s+{CELL}([^\n]*(?:\n\+[^\n]*)*)", extracted)
    expected_pins = [pin for row in rows for pin in
                     (pin_name("STATE", row[0], row[1]), pin_name("PLATE", row[0], row[1]))]
    pins = header.group(1).replace("+", " ").split() if header else []
    if pins != expected_pins:
        raise RuntimeError(f"Unexpected extracted array pins: got {len(pins)}, expected {len(expected_pins)}")
    caps = re.findall(r"(?im)^X\S+\s+\S+\s+\S+\s+sky130_fd_pr__cap_mim_m3_2\b", extracted)
    if len(caps) != 1020:
        raise RuntimeError(f"Expected 1020 extracted MIM unit devices, found {len(caps)}")

    ref_lines = [f".subckt {CELL} {' '.join(expected_pins)}"]
    idx = 0
    for bank, bit, count, _y, _p in rows:
        state, plate = pin_name("STATE", bank, bit), pin_name("PLATE", bank, bit)
        ref_lines.extend(f"XU{idx+i} {plate} {state} sky130_fd_pr__cap_mim_m3_2 w=2 l=2" for i in range(count))
        idx += count
    ref_lines.append(f".ends {CELL}")
    (OUT / "reference.spice").write_text("\n".join(ref_lines)+"\n", encoding="ascii")
    setup = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl"
    lvs = docker("netgen-lvs", ["-batch", "lvs", f"{CELL}.spice {CELL}", f"reference.spice {CELL}", setup, "lvs.out"],
                 workdir=f"/workspace/{OUT.relative_to(ROOT).as_posix()}")
    (OUT / "netgen_lvs.log").write_text(lvs, encoding="utf-8")
    if "Circuits match uniquely." not in lvs:
        raise RuntimeError(f"Weighted trim array LVS failed:\n{lvs[-5000:]}")

    pex = "\n".join([f"load {CELL}", "extract all", "ext2spice lvs", "ext2spice scale off",
                      "ext2spice cthresh 0", "ext2spice rthresh infinite",
                      f"ext2spice -o {CELL}_pex.spice", "quit -noprompt", ""])
    pex_log = docker("magic", ["-dnull", "-noconsole", "-rcfile", RC], stdin=pex,
                     workdir=f"/workspace/{OUT.relative_to(ROOT).as_posix()}")
    (OUT / "magic_pex.log").write_text(pex_log, encoding="utf-8")
    pex_text = (OUT / f"{CELL}_pex.spice").read_text(encoding="ascii")
    parasite_caps = len(re.findall(r"(?im)^C\S+\s", pex_text))

    ruby = OUT / "inspect_gds.rb"
    ruby.write_text("include RBA\nl=Layout.new\n"+
                    f"l.read('/workspace/{(OUT / (CELL + '.gds')).relative_to(ROOT).as_posix()}')\n"+
                    f"c=l.cell('{CELL}')\nb=c.bbox\n"+
                    'puts "bbox_um=#{(b.width*l.dbu).round(4)}x#{(b.height*l.dbu).round(4)}"\n', encoding="ascii")
    geom = docker("klayout", ["-b", "-r", f"/workspace/{ruby.relative_to(ROOT).as_posix()}"], timeout=120,
                  workdir="/workspace")
    (OUT / "klayout_geometry.log").write_text(geom, encoding="utf-8")
    bbox = re.search(r"bbox_um=([0-9.]+)x([0-9.]+)", geom)
    if not bbox:
        raise RuntimeError(f"KLayout geometry inspect failed:\n{geom[-2000:]}")
    report = {"cell": CELL, "banks": list(BANKS), "bits_per_bank": 8,
              "unit_mim_capacitance_f": 9.52e-15, "unit_count": 1020,
              "physical_binary_weights": {f"{b}_b{k}": 1 << k for b in BANKS for k in range(8)},
              "routed_plate_and_sample_buses": True, "external_plate_selectors_required": 96,
              "magic_drc_zero": True, "netgen_unique_match": True,
              "gds_written": (OUT / f"{CELL}.gds").is_file(),
              "gds_bbox_um": [float(bbox.group(1)), float(bbox.group(2))],
              "pex_capacitor_count": parasite_caps, "wire_resistance_extraction": False,
              "scope": "Four programmable binary-weighted differential coarse/fine banks with routed local state/plate buses; external 96 extracted TGs and their decoder are not in this GDS. MIM variation, mismatch/noise, latch integration and code calibration are separate gates."}
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
