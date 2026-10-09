"""Route and qualify a compact 3x4 SKY130 MIM state-bank PCell array."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/layout/sky130_mim_state_bank_square"
SOURCE = OUT / "square_flat.mag"
CELL = "mim_state_square_3x4_w30_l30"
MAGIC_RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"


def main() -> int:
    original = SOURCE.read_text(encoding="ascii")
    if original.count("<< end >>") != 1:
        raise RuntimeError("Unexpected flat Magic source structure")
    shapes = ["<< via3 >>"]
    xs, ys = (-12000, -5500, 1000), (-17000, -11000, -3000, 3000)
    for x in xs:
        for y in ys:
            shapes.append(f"rect {x-100} {y-100} {x+100} {y+100}")
    shapes.append("<< metal3 >>")
    for x in xs:
        shapes.append(f"rect {x-100} -17100 {x+100} 3100")
    shapes.append(f"rect {xs[0]-100} {ys[0]-100} {xs[-1]+100} {ys[0]+100}")
    shapes.append("<< metal5 >>")
    # The three column plate buses extend past via4 at y=6159; these stubs
    # connect to a top-level common M5 rail in the clear region above the array.
    for x in (-10344, -3622, 3080):
        shapes.append(f"rect {x-100} 6200 {x+100} 6400")
    shapes.append("rect -10444 6300 3080 6400")
    shapes.append("<< labels >>")
    shapes.extend(("rlabel metal5 s -100 6320 100 6380 4 MEM_P", "port 1 nsew",
                   "rlabel metal3 s -11100 -17040 -10900 -16960 4 MEM_N", "port 2 nsew"))
    routed = OUT / f"{CELL}.mag"
    routed.write_text(original.replace("<< end >>", "\n".join(shapes) + "\n<< end >>"),
                      encoding="ascii")
    tcl = "\n".join((f"load {CELL}", "drc check", "drc count", "extract all",
                     "ext2spice lvs", "ext2spice scale off", f"ext2spice -o {CELL}.spice",
                     f"gds write {CELL}.gds", "save", "quit -noprompt", ""))
    command = ["docker", "run", "--rm", "-i", "-v", f"{ROOT}:/workspace",
               "-e", "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root",
               "-w", "/workspace/artifacts/analog_asic/layout/sky130_mim_state_bank_square",
               "--entrypoint", "magic", "eventspikeseg:analog-layout", "-dnull", "-noconsole",
               "-rcfile", MAGIC_RC]
    proc = subprocess.run(command, input=tcl, text=True, capture_output=True, timeout=180, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (OUT / f"{CELL}_magic.log").write_text(log, encoding="utf-8")
    if proc.returncode or "Total DRC errors found: 0" not in log:
        raise RuntimeError(f"Routed square bank Magic check failed:\n{log[-5000:]}")
    spice = (OUT / f"{CELL}.spice").read_text(encoding="ascii")
    if not re.search(rf"\.subckt\s+{CELL}\s+MEM_P\s+MEM_N\b", spice, re.I):
        raise RuntimeError("Routed square bank does not extract with MEM_P/MEM_N pins")
    caps = re.findall(r"^X\S+\s+MEM_P\s+MEM_N\s+sky130_fd_pr__cap_mim_m3_2\b",
                      spice, re.M | re.I)
    if len(caps) != 12:
        raise RuntimeError(f"Expected12 connected MIM units, found {len(caps)}")
    ref = OUT / "mim_square_reference.spice"
    ref.write_text(".subckt mim_square_reference MEM_P MEM_N\n" +
                   "".join(f"X{i} MEM_P MEM_N sky130_fd_pr__cap_mim_m3_2 w=30 l=30\n"
                           for i in range(12)) + ".ends\n", encoding="ascii")
    lvs_cmd = ["docker", "run", "--rm", "-v", f"{ROOT}:/workspace", "-e",
               "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root", "-w",
               "/workspace/artifacts/analog_asic/layout/sky130_mim_state_bank_square",
               "--entrypoint", "netgen-lvs", "eventspikeseg:analog-layout", "-batch", "lvs",
               f"{CELL}.spice {CELL}", "mim_square_reference.spice mim_square_reference",
               "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl",
               "mim_square_lvs.out"]
    lvs = subprocess.run(lvs_cmd, text=True, capture_output=True, timeout=180, cwd=ROOT)
    lvs_log = lvs.stdout + lvs.stderr
    (OUT / f"{CELL}_netgen.log").write_text(lvs_log, encoding="utf-8")
    if lvs.returncode or "Circuits match uniquely." not in lvs_log:
        raise RuntimeError(f"Routed square bank LVS failed:\n{lvs_log[-4000:]}")

    inspect = OUT / "inspect_routed.rb"
    inspect.write_text(f"""include RBA
l=Layout.new
l.read('/workspace/artifacts/analog_asic/layout/sky130_mim_state_bank_square/{CELL}.gds')
c=l.cell('{CELL}')
b=c.bbox
puts \"bbox_um=#{{(b.width*l.dbu).round(4)}}x#{{(b.height*l.dbu).round(4)}}\"
""", encoding="ascii")
    klayout = subprocess.run(["docker", "run", "--rm", "-v", f"{ROOT}:/workspace", "-w",
                              "/workspace", "--entrypoint", "klayout", "eventspikeseg:analog-layout",
                              "-b", "-r", f"/workspace/{inspect.relative_to(ROOT).as_posix()}"],
                             text=True, capture_output=True, timeout=90, cwd=ROOT)
    geometry_log = klayout.stdout + klayout.stderr
    bbox_match = re.search(r"bbox_um=([0-9.]+)x([0-9.]+)", geometry_log)
    if klayout.returncode or not bbox_match:
        raise RuntimeError(f"KLayout could not inspect routed bank GDS:\n{geometry_log[-2000:]}")

    bench = ROOT / "artifacts/analog_asic/benches/mim_large_probe"
    old_cell = "membrane_state_mim_m3_2_w30_l30_m12"
    old_spice = f"/workspace/artifacts/analog_asic/benches/mim_large_probe/{old_cell}.spice"
    for deck_name in ("mim_bank_cv.cir", "mim_bank_hold_5ms.cir"):
        source_deck = (bench / deck_name).read_text(encoding="ascii")
        converted = source_deck.replace(old_spice,
            f"/workspace/artifacts/analog_asic/layout/sky130_mim_state_bank_square/{CELL}.spice")
        converted = converted.replace(old_cell, CELL)
        (OUT / deck_name.replace("mim_bank", "square_bank")).write_text(converted, encoding="ascii")
    sim_logs = {}
    for deck_name, timeout in (("square_bank_cv.cir", 180), ("square_bank_hold_5ms.cir", 300)):
        sim = subprocess.run(["docker", "run", "--rm", "--memory", "2g", "--cpus", "2",
                              "-v", f"{ROOT}:/workspace", "-w",
                              "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
                              "--entrypoint", "ngspice", "eventspikeseg:analog-ngspice36", "-b",
                              f"/workspace/artifacts/analog_asic/layout/sky130_mim_state_bank_square/{deck_name}"],
                             text=True, capture_output=True, timeout=timeout, cwd=ROOT)
        sim_log = sim.stdout + sim.stderr
        sim_logs[deck_name] = sim_log
        if sim.returncode or "ngspice-36 done" not in sim_log:
            raise RuntimeError(f"{deck_name} failed:\n{sim_log[-3000:]}")
    ceff_match = re.search(r"\bceff\s*=\s*([-+0-9.eE]+)", sim_logs["square_bank_cv.cir"], re.I)
    if not ceff_match:
        raise RuntimeError("Missing extracted-bank Ceff measurement")
    hold_values = {k.lower(): float(v) for k, v in re.findall(
        r"^(\w+_\w+)\s*=\s*([-+0-9.eE]+)", sim_logs["square_bank_hold_5ms.cir"], re.I | re.M)}
    holds = {}
    for bias, label in (("06", "0.6V"), ("12", "1.2V")):
        for switch in ("n_only", "p_only", "tg"):
            start, end = hold_values[f"{switch}_{bias}_start"], hold_values[f"{switch}_{bias}_end"]
            holds[f"{switch}_{label}"] = {"start_v": start, "end_v": end,
                                            "drift_mv": (end-start)*1e3}
    report = {"cell": CELL, "array": [3, 4], "unit_geometry_um": [30, 30],
              "unit_capacitor": "sky130_fd_pr__cap_mim_m3_2", "unit_count": 12,
              "drc_zero_errors": True, "netgen_unique_match": True,
              "gds_bbox_um": [float(bbox_match.group(1)), float(bbox_match.group(2))],
              "extracted_two_terminal_pin_order": ["MEM_P", "MEM_N"],
              "extracted_bank_ceff_f": float(ceff_match.group(1)),
              "hold_5ms_completed": True, "hold_drift": holds,
              "scope": "MIM bank array only; no switch, sensor, state-update or PLIF circuitry."}
    (OUT / f"{CELL}_qualification.json").write_text(json.dumps(report, indent=2) + "\n",
                                                   encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
