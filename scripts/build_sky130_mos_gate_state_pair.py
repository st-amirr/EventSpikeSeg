"""Build and qualify a paired extracted SKY130 MOS gate-cap storage macro."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/analog_asic"
UNIT_W = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--unit-w=")), "100"))
UNIT_L = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--unit-l=")), "10"))
GEOM = f"{UNIT_W:g}x{UNIT_L:g}".replace(".", "p")
SOURCE = ART / f"layout/sky130_mos_gate_bank_{GEOM}_nf10/mos_gate_bank_{GEOM}_nf10.mag"
OUT = ART / f"layout/sky130_mos_gate_state_pair_{GEOM}_nf10"
CELL = f"mos_gate_state_pair_{GEOM}_nf10"
PDK = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A"
MODEL = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
LAYOUT_IMAGE = "eventspikeseg:analog-layout"
SIM_IMAGE = "eventspikeseg:analog-ngspice36"
PITCH = 24_000


def docker(image: str, argv: list[str], *, input_text: str | None = None,
           timeout: int = 180) -> subprocess.CompletedProcess[str]:
    cmd = ["docker", "run", "--rm"]
    if input_text is not None:
        cmd.append("-i")
    cmd += ["-v", f"{ROOT}:/workspace", "-e", "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root",
            "-w", f"/workspace/artifacts/analog_asic/layout/{OUT.name}", "--entrypoint", argv[0], image, *argv[1:]]
    return subprocess.run(cmd, input=input_text, text=True, capture_output=True,
                          timeout=timeout, cwd=ROOT)


def create_layout() -> None:
    text = SOURCE.read_text(encoding="ascii")
    layers: dict[str, list[str]] = {}
    section = ""
    for line in text.splitlines():
        if line.startswith("<< ") and line.endswith(" >>"):
            section = line[3:-3]
            if section not in ("end", "labels"):
                layers.setdefault(section, [])
        elif section and line.startswith("rect "):
            layers[section].append(line)
    header = [line for line in text.splitlines()[:3] if not line.startswith("timestamp")]
    out = header + ["timestamp 0"]
    small_geometry = UNIT_W <= 20 and UNIT_L <= 2
    if small_geometry:
        gate_y1 = round(500 * UNIT_L + 20)
        gate_y2 = gate_y1 + 30
        bulk_x = round(-(5 * UNIT_W + 70))
        bulk_y = round(500 * UNIT_L + 70)
        gate_rect = ("metal1", -40, gate_y1, 40, gate_y2)
        vcm_rect = ("metal1", -20, -8, 20, 8)
        bulk_rect = ("psubdiff", bulk_x, bulk_y, bulk_x + 30, bulk_y + 10)
    else:
        gate_rect = ("metal1", 500, 79, 700, 125)
        vcm_rect = ("metal1", 1000, 157, 1200, 169)
        bulk_rect = ("psubdiff", -17, 100, 17, 200)
    for layer, rects in layers.items():
        out.append(f"<< {layer} >>")
        for dx in (0, PITCH):
            for rect in rects:
                _, *coords = rect.split()
                x1, y1, x2, y2 = map(int, coords)
                out.append(f"rect {x1 + dx} {y1} {x2 + dx} {y2}")
        if layer == "metal1":
            # Join both channel-terminal buses and leave the two gate buses separate.
            _, x1, y1, x2, y2 = vcm_rect
            out.append(f"rect {x1} {y1} {PITCH + x2} {y2}")
    _, gx1, gy1, gx2, gy2 = gate_rect
    _, vx1, vy1, vx2, vy2 = vcm_rect
    _, bx1, by1, bx2, by2 = bulk_rect
    out += ["<< labels >>",
            f"rlabel metal1 s {gx1} {gy1} {gx2} {gy2} 4 GATEP", "port 1 nsew",
            f"rlabel metal1 s {PITCH+gx1} {gy1} {PITCH+gx2} {gy2} 4 GATEN", "port 2 nsew",
            f"rlabel metal1 s {vx1} {vy1} {vx2} {vy2} 4 VCM", "port 3 nsew",
            f"rlabel psubdiff s {bx1} {by1} {bx2} {by2} 4 BULK", "port 4 nsew",
            f"rlabel psubdiff s {PITCH+bx1} {by1} {PITCH+bx2} {by2} 4 BULK", "<< end >>", ""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{CELL}.mag").write_text("\n".join(out), encoding="ascii")


def main() -> int:
    if not SOURCE.exists():
        raise RuntimeError(f"qualified source bank missing: {SOURCE}")
    create_layout()
    tcl = "\n".join([f"load {CELL}", "drc check", "drc count", "extract all",
                      "ext2spice lvs", "ext2spice scale off", f"ext2spice -o {CELL}.spice",
                      f"gds write {CELL}.gds", "save", "quit -noprompt", ""])
    proc = docker(LAYOUT_IMAGE, ["magic", "-dnull", "-noconsole", "-rcfile",
                                  "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"],
                  input_text=tcl)
    log = proc.stdout + proc.stderr
    (OUT / "magic_build.log").write_text(log, encoding="utf-8")
    if proc.returncode or "Total DRC errors found: 0" not in log:
        raise RuntimeError(f"paired MOS cap DRC failed:\n{log[-5000:]}")

    ref = OUT / "reference.spice"
    rows = []
    for side, gate in (("P", "GATEP"), ("N", "GATEN")):
        rows.extend(f"X{side}{i} VCM {gate} VCM BULK sky130_fd_pr__nfet_01v8 w={UNIT_W:g} l={UNIT_L:g}\n" for i in range(10))
    ref.write_text(".subckt reference GATEP GATEN VCM BULK\n" + "".join(rows) + ".ends\n", encoding="ascii")
    lvs = docker(LAYOUT_IMAGE, ["netgen-lvs", "-batch", "lvs", f"{CELL}.spice {CELL}",
                                "reference.spice reference",
                                f"{PDK}/libs.tech/netgen/sky130A_setup.tcl", "lvs.out"])
    lvs_log = lvs.stdout + lvs.stderr
    (OUT / "netgen_lvs.log").write_text(lvs_log, encoding="utf-8")
    if lvs.returncode or "Result: Circuits match uniquely." not in lvs_log:
        raise RuntimeError(f"paired MOS cap LVS failed:\n{lvs_log[-5000:]}")
    spice = (OUT / f"{CELL}.spice").read_text(encoding="ascii")
    devices = re.findall(r"^X\S+\s+.*sky130_fd_pr__nfet_01v8\b", spice, re.M | re.I)
    if len(devices) != 20:
        raise RuntimeError(f"expected 20 extracted devices, found {len(devices)}")

    ac = OUT / "differential_ac.cir"
    offsets = (-0.45, -0.25, -0.10, -0.05, 0.0, 0.05, 0.10, 0.25, 0.45)
    deck = ["* Extracted paired MOS gate cap over the actual VCM-centered state range",
            ".option scale=1u",
            f'.include "{PDK}/libs.tech/ngspice/parameters/invariant.spice"',
            f'.lib "{PDK}/libs.tech/ngspice/sky130.lib.spice" tt',
            f'.include "/workspace/artifacts/analog_asic/layout/{OUT.name}/{CELL}.spice"']
    probes: list[tuple[str, float, str]] = []
    for index, offset in enumerate(offsets):
        for side in ("p", "n"):
            gp, gn, vcm = f"gp{index}{side}", f"gn{index}{side}", f"vcm{index}{side}"
            vgp, vgn = f"Vgp{index}{side}", f"Vgn{index}{side}"
            deck += [f"{vgp} {gp} 0 dc {0.9+offset:.9g} ac {1 if side == 'p' else 0}",
                     f"{vgn} {gn} 0 dc {0.9-offset:.9g} ac {1 if side == 'n' else 0}",
                     f"V{vcm} {vcm} 0 dc 0.9 ac 0",
                     f"X{index}{side} {gp} {gn} {vcm} 0 {CELL}"]
            probes.append((vgp if side == "p" else vgn, offset if side == "p" else -offset, side))
    deck += [".control", "set numdgt=15", "ac lin 1 1meg 1meg"]
    for index, (source, vgs, side) in enumerate(probes):
        deck += [f"let c{index}=abs(imag(i({source})))/(2*pi*frequency)", f"print c{index}"]
    deck += ["quit", ".endc", ".end", ""]
    ac.write_text("\n".join(deck), encoding="ascii")
    sim = docker(SIM_IMAGE, ["ngspice", "-b", f"/workspace/artifacts/analog_asic/layout/{OUT.name}/{ac.name}"], timeout=180)
    sim_log = sim.stdout + sim.stderr
    (OUT / "ngspice_ac.log").write_text(sim_log, encoding="utf-8")
    matches = {int(index): float(value) for index, value in re.findall(
        r"(?im)^\s*c(\d+)\s*=\s*([-+0-9.eE]+)", sim_log)}
    values = [matches[i] for i in range(len(probes)) if i in matches]
    if sim.returncode or len(values) != len(probes):
        raise RuntimeError(f"paired MOS cap AC simulation failed:\n{sim_log[-4000:]}")
    inspect = OUT / "inspect_pair.rb"
    inspect_lines = ["include RBA", "l=Layout.new",
                     f"l.read('/workspace/artifacts/analog_asic/layout/{OUT.name}/{CELL}.gds')",
                     f"c=l.cell('{CELL}')", "b=c.bbox",
                     f'puts "bbox_um=#{{(b.width*l.dbu).round(4)}}x#{{(b.height*l.dbu).round(4)}}"']
    inspect.write_text("\n".join(inspect_lines) + "\n", encoding="ascii")
    klayout = docker(LAYOUT_IMAGE, ["klayout", "-b", "-r",
                                     f"/workspace/artifacts/analog_asic/layout/{OUT.name}/inspect_pair.rb"],
                     timeout=90)
    geometry_log = klayout.stdout + klayout.stderr
    bbox_match = re.search(r"bbox_um=([0-9.]+)x([0-9.]+)", geometry_log)
    if klayout.returncode or not bbox_match:
        raise RuntimeError(f"KLayout could not inspect paired MOS cap GDS:\n{geometry_log[-2000:]}")
    zero_state_c = matches[8]
    k = 1.380649e-23
    report = {"cell": CELL, "unit_geometry_um": {"w": UNIT_W, "l": UNIT_L},
              "devices_per_rail": 10, "extracted_fet_count": len(devices),
              "gds_bbox_um": [float(bbox_match.group(1)), float(bbox_match.group(2))],
              "pins": ["GATEP", "GATEN", "VCM", "BULK"],
              "channel_terminals_tied_to_shared_vcm_in_layout": True,
              "gate_rails_separate": True, "magic_drc_zero": True,
              "netgen_lvs_unique_match": True, "gds_generated": (OUT / f"{CELL}.gds").exists(),
              "ac_frequency_hz": 1e6,
              "capacitance_sweep_vgs_v": [{"gate_minus_vcm_v": vgs, "active_rail": side,
                                             "capacitance_f": matches[i]}
                                            for i, (_, vgs, side) in enumerate(probes)],
              "zero_state_capacitance_f_per_rail": zero_state_c,
              "ideal_ktc_noise_rms_v_per_rail_at_300k": (k * 300 / zero_state_c) ** 0.5,
              "ideal_differential_ktc_noise_rms_v_at_300k": (2 * k * 300 / zero_state_c) ** 0.5,
              "pvt_hold_source": "single-rail bank hold screens; separately documented",
              "limitations": ["no access/restore TG in this layout macro", "no weight injector integration",
                              "no physical state sensor/readout", "no mismatch or transient noise",
                              "no routed population or service estimate"]}
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
