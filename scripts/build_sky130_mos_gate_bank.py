"""Build and qualify a ten-unit SKY130 MOS gate-cap bank from explicit geometry copies."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAME = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                    if arg.startswith("--source-dir-name=")), "sky130_moscap_pcell_probe")
UNIT_W = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                     if arg.startswith("--unit-w=")), "100"))
UNIT_L = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                     if arg.startswith("--unit-l=")), "10"))
OUT_NAME = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                 if arg.startswith("--output-dir-name=")), f"sky130_mos_gate_bank_{UNIT_W:g}x{UNIT_L:g}_nf10")
CELL = f"mos_gate_bank_{UNIT_W:g}x{UNIT_L:g}_nf10".replace(".", "p")
SOURCE_DIR = ROOT / "artifacts/analog_asic/layout" / SOURCE_NAME
OUT = ROOT / "artifacts/analog_asic/layout" / OUT_NAME
UNIT_MAG = SOURCE_DIR / "moscap_pcell_probe.mag"
MAGIC_RC = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc"
PDK = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A"
MODEL = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
SIM_IMAGE = "eventspikeseg:analog-ngspice36"
LAYOUT_IMAGE = "eventspikeseg:analog-layout"
COUNT = 10
PITCH = 2400


def docker(image: str, argv: list[str], *, input_text: str | None = None,
           workdir: str | None = None, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    cmd = ["docker", "run", "--rm"]
    if input_text is not None:
        cmd.append("-i")
    cmd += ["-v", f"{ROOT}:/workspace", "-e", "PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root"]
    if workdir:
        cmd += ["-w", workdir]
    cmd += ["--entrypoint", argv[0], image, *argv[1:]]
    return subprocess.run(cmd, input=input_text, text=True, capture_output=True,
                          timeout=timeout, cwd=ROOT)


def make_layout() -> None:
    text = UNIT_MAG.read_text(encoding="ascii")
    layers: dict[str, list[str]] = {}
    current = ""
    for line in text.splitlines():
        if line.startswith("<< ") and line.endswith(" >>"):
            current = line[3:-3]
            if current not in ("end", "labels"):
                layers.setdefault(current, [])
        elif current and line.startswith("rect "):
            layers[current].append(line)
    small_geometry = UNIT_W <= 20 and UNIT_L <= 2
    out = ["magic", "tech sky130A", f"magscale 1 {1 if small_geometry else 2}", "timestamp 0"]
    for layer, rects in layers.items():
        out.append(f"<< {layer} >>")
        for index in range(COUNT):
            dx = index * PITCH
            for rect in rects:
                _, *coords = rect.split()
                x1, y1, x2, y2 = map(int, coords)
                out.append(f"rect {x1+dx} {y1} {x2+dx} {y2}")
    out += ["<< metal1 >>"]
    if small_geometry:
        x_tie = round(5 * UNIT_W + 26)
        gate_y1 = round(500 * UNIT_L + 20)
        gate_y2 = gate_y1 + 30
        bulk_x = round(-(5 * UNIT_W + 70))
        bulk_y = round(500 * UNIT_L + 70)
        out += [f"rect {-x_tie} -8 {PITCH*(COUNT-1)+x_tie} 8",
                f"rect -40 {gate_y1} {PITCH*(COUNT-1)+40} {gate_y2}"]
        vss_y1, vss_y2 = -8, 8
        gate_x1, gate_x2, vss_x1, vss_x2 = -40, PITCH*(COUNT-1)+40, -20, 20
        bulk = f"rlabel psubdiff s {bulk_x} {bulk_y} {bulk_x + 30} {bulk_y + 10} 4 BULK"
    else:
        out += [f"rect 91 157 {PITCH*(COUNT-1)+2195} 169",
                f"rect 147 79 {PITCH*(COUNT-1)+2139} 125",
                f"rect 147 20189 {PITCH*(COUNT-1)+2139} 20235"]
        gate_y1, gate_y2, vss_y1, vss_y2 = 79, 125, 157, 169
        gate_x1, gate_x2, vss_x1, vss_x2 = 500, 700, 1000, 1200
        bulk = "rlabel psubdiff s -17 100 17 200 4 BULK"
    out += ["<< labels >>",
            f"rlabel metal1 s {gate_x1} {gate_y1} {gate_x2} {gate_y2} 4 GATE", "port 1 nsew",
            f"rlabel metal1 s {vss_x1} {vss_y1} {vss_x2} {vss_y2} 4 VSS", "port 2 nsew",
            bulk, "port 3 nsew", "<< end >>", ""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{CELL}.mag").write_text("\n".join(out), encoding="ascii")


def main() -> int:
    if not UNIT_MAG.exists():
        raise RuntimeError("First generate the single-device labeled MOSCAP with probe_sky130_moscap_pcell.py")
    make_layout()
    workdir = f"/workspace/artifacts/analog_asic/layout/{OUT.name}"
    tcl = "\n".join([f"load {CELL}", "drc check", "drc count", "extract all",
                      "ext2spice lvs", "ext2spice scale off", f"ext2spice -o {CELL}.spice",
                      f"gds write {CELL}.gds", "save", "quit -noprompt", ""])
    magic = docker(LAYOUT_IMAGE, ["magic", "-dnull", "-noconsole", "-rcfile", MAGIC_RC],
                   input_text=tcl, workdir=workdir)
    magic_log = magic.stdout + magic.stderr
    (OUT / "magic_build.log").write_text(magic_log, encoding="utf-8")
    if magic.returncode or "Total DRC errors found: 0" not in magic_log:
        raise RuntimeError(f"Ten-unit MOS gate bank Magic/DRC failed:\n{magic_log[-5000:]}")
    spice = (OUT / f"{CELL}.spice").read_text(encoding="ascii")
    ref = OUT / "mos_gate_bank_reference.spice"
    ref.write_text(".subckt mos_gate_bank_reference GATE VSS BULK\n" +
                   "".join(f"X{i} VSS GATE VSS BULK sky130_fd_pr__nfet_01v8 w={UNIT_W:g} l={UNIT_L:g}\n"
                           for i in range(COUNT)) + ".ends\n", encoding="ascii")
    lvs = docker(LAYOUT_IMAGE, ["netgen-lvs", "-batch", "lvs",
                 f"{CELL}.spice {CELL}", "mos_gate_bank_reference.spice mos_gate_bank_reference",
                 f"{PDK}/libs.tech/netgen/sky130A_setup.tcl", "mos_gate_bank_lvs.out"],
                 workdir=workdir)
    lvs_log = lvs.stdout + lvs.stderr
    (OUT / "netgen_lvs.log").write_text(lvs_log, encoding="utf-8")
    if lvs.returncode or "Result: Circuits match uniquely." not in lvs_log:
        raise RuntimeError(f"Ten-unit MOS gate bank LVS failed:\n{lvs_log[-5000:]}")
    fet_count = len(re.findall(r"^X\S+\s+.*sky130_fd_pr__nfet_01v8\b", spice, re.M | re.I))
    if fet_count != COUNT:
        raise RuntimeError(f"Expected {COUNT} extracted MOS devices, found {fet_count}")
    deck = OUT / "mos_gate_bank_ac.cir"
    deck.write_text(f'''* Explicitly tiled, extracted SKY130 MOS gate bank
.include "{PDK}/libs.tech/ngspice/parameters/invariant.spice"
.lib "{PDK}/libs.tech/ngspice/sky130.lib.spice" tt
.include "/workspace/artifacts/analog_asic/layout/{OUT.name}/{CELL}.spice"
Vgate gate 0 dc 0.9 ac 1
Vcm vcm 0 dc 0.9 ac 0
Xcap gate vcm 0 {CELL}
.control
set noaskquit
set numdgt=15
ac lin 1 1meg 1meg
let cgate=abs(imag(i(Vgate)))/(2*pi*frequency)
print cgate
quit
.endc
.end
''', encoding="ascii")
    sim = docker(SIM_IMAGE, ["ngspice", "-b", f"/workspace/artifacts/analog_asic/layout/{OUT.name}/{deck.name}"],
                 workdir=f"{PDK}/libs.tech/ngspice", timeout=180)
    sim_log = sim.stdout + sim.stderr
    (OUT / "ngspice_ac.log").write_text(sim_log, encoding="utf-8")
    c_match = re.search(r"\bcgate\s*=\s*([-+0-9.eE]+)", sim_log, re.I)
    if sim.returncode or not c_match:
        raise RuntimeError(f"Ten-unit MOS gate bank AC simulation failed:\n{sim_log[-4000:]}")
    noise_deck = OUT / "mos_gate_bank_noise.cir"
    noise_deck.write_text(f'''* Extracted-layout MOS gate bank with SKY130 reset-switch device noise
.option scale=1u
.temp 27
.include "{MODEL}/models/parameters/invariant.spice"
.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"
.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "{MODEL}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "/workspace/artifacts/analog_asic/layout/{OUT.name}/{CELL}.spice"
Vdd vdd 0 1.8
Vdrive drive 0 0.9 AC 1
Vcm vcm 0 0.9
Ven en 0 1.8
Venb enb 0 0
.subckt tg a b en enb vdd vss
Xn a en b vss sky130_fd_pr__nfet_01v8 w=1 l=0.15
Xp a enb b vdd sky130_fd_pr__pfet_01v8 w=2 l=0.15
.ends tg
Xreset drive state en enb vdd 0 tg
Xcap state vcm 0 {CELL}
.control
set numdgt=15
noise v(state) Vdrive dec 20 10 100meg
print onoise_total
print inoise_total
quit
.endc
.end
''', encoding="ascii")
    noise_sim = docker(SIM_IMAGE, ["ngspice", "-b",
        f"/workspace/artifacts/analog_asic/layout/{OUT.name}/{noise_deck.name}"],
        workdir="/workspace", timeout=180)
    noise_log = noise_sim.stdout + noise_sim.stderr
    (OUT / "ngspice_noise.log").write_text(noise_log, encoding="utf-8")
    noise_match = re.search(r"(?im)^\s*onoise_total\s*=\s*([-+0-9.eE]+)", noise_log)
    if noise_sim.returncode or not noise_match or "ngspice-36 done" not in noise_log:
        raise RuntimeError(f"Extracted MOS gate bank noise simulation failed:\n{noise_log[-4000:]}")
    hold_deck = OUT / "mos_gate_bank_hold_5ms.cir"
    hold_lines = [
        "* Extracted-layout MOS gate bank with schematic SKY130 TG, TT/27C",
        ".option scale=1u", ".temp 27",
        f'.include "{MODEL}/models/parameters/invariant.spice"',
        f'.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"',
        f'.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
        f'.include "{MODEL}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        f'.include "/workspace/artifacts/analog_asic/layout/{OUT.name}/{CELL}.spice"',
        "Vdd vdd 0 1.8",
        "Vcm vcm 0 0.9",
        ".subckt tg a b en enb vdd vss",
        "Xn a en b vss sky130_fd_pr__nfet_01v8 w=1 l=0.15",
        "Xp a enb b vdd sky130_fd_pr__pfet_01v8 w=2 l=0.15", ".ends tg",
    ]
    hold_cases = {"low": 0.45, "mid": 0.9, "high": 1.35}
    for tag, bias in hold_cases.items():
        hold_lines += [f"Vprogram_{tag} src_{tag} 0 {bias:g}",
                       f"Von_{tag} on_{tag} 0 PWL(0 1.8 1u 1.8 1.001u 0 5.01m 0)",
                       f"Voff_{tag} off_{tag} 0 PWL(0 0 1u 0 1.001u 1.8 5.01m 1.8)",
                       f"Xsw_{tag} src_{tag} state_{tag} on_{tag} off_{tag} vdd 0 tg",
                       f"Xcap_{tag} state_{tag} vcm 0 {CELL}"]
    hold_lines += [".control", "set numdgt=15", "tran 1u 5.01m 0 1u"]
    for tag in hold_cases:
        hold_lines += [f"meas tran start_{tag} find v(state_{tag}) at=1.9u",
                       f"meas tran five_ms_{tag} find v(state_{tag}) at=5m"]
    hold_lines += ["quit", ".endc", ".end", ""]
    hold_deck.write_text("\n".join(hold_lines), encoding="ascii")
    hold_sim = docker(SIM_IMAGE, ["ngspice", "-b",
        f"/workspace/artifacts/analog_asic/layout/{OUT.name}/{hold_deck.name}"],
        workdir="/workspace", timeout=180)
    hold_log = hold_sim.stdout + hold_sim.stderr
    (OUT / "ngspice_hold_5ms.log").write_text(hold_log, encoding="utf-8")
    hold_values = {name.lower(): float(value) for name, value in re.findall(
        r"(?im)^\s*(start_(?:low|mid|high)|five_ms_(?:low|mid|high))\s*=\s*([-+0-9.eE]+)", hold_log)}
    expected_hold_values = {f"{name}_{tag}" for name in ("start", "five_ms") for tag in hold_cases}
    if hold_sim.returncode or "ngspice-36 done" not in hold_log or set(hold_values) != expected_hold_values:
        raise RuntimeError(f"Extracted MOS gate bank hold simulation failed:\n{hold_log[-4000:]}")
    inspect = OUT / "inspect_bank.rb"
    inspect.write_text(f"""include RBA
l=Layout.new
l.read('/workspace/artifacts/analog_asic/layout/{OUT.name}/{CELL}.gds')
c=l.cell('{CELL}')
b=c.bbox
puts "bbox_um=#{{(b.width*l.dbu).round(4)}}x#{{(b.height*l.dbu).round(4)}}"
""", encoding="ascii")
    klayout = docker(LAYOUT_IMAGE, ["klayout", "-b", "-r",
                         f"/workspace/artifacts/analog_asic/layout/{OUT.name}/inspect_bank.rb"],
                     workdir="/workspace", timeout=90)
    geometry_log = klayout.stdout + klayout.stderr
    bbox_match = re.search(r"bbox_um=([0-9.]+)x([0-9.]+)", geometry_log)
    if klayout.returncode or not bbox_match:
        raise RuntimeError(f"KLayout could not inspect MOS gate bank GDS:\n{geometry_log[-2000:]}")
    c_f = float(c_match.group(1))
    report = {
        "cell": CELL, "unit_devices_requested": COUNT, "unit_devices_extracted": fet_count,
        "explicit_geometry_replication": True, "unit_w_um": UNIT_W, "unit_l_um": UNIT_L,
        "layout_pitch_internal_units": PITCH,
        "gds_bbox_um": [float(bbox_match.group(1)), float(bbox_match.group(2))],
        "pins": ["GATE", "VSS", "BULK"], "source_drain_bused_in_metal": True,
        "gate_buses_in_metal": True, "magic_drc_zero": True,
        "netgen_lvs_unique_match": True, "ac_gate_bias_v": 0.9,
        "ac_channel_bias_v": 0.9, "ac_gate_minus_channel_v": 0.0,
        "ac_frequency_hz": 1e6, "extracted_cgate_f": c_f,
        "single_ended_ktc_noise_rms_v_at_300k": (1.380649e-23*300/c_f)**0.5,
        "integrated_pdk_reset_noise_rms_v": float(noise_match.group(1)),
        "integrated_pdk_reset_noise_band_hz": [10, 100_000_000],
        "hold_bias_v": {tag: bias for tag, bias in hold_cases.items()},
        "hold_channel_bias_v": 0.9,
        "hold_drift_uv": {tag: (hold_values[f"five_ms_{tag}"] - hold_values[f"start_{tag}"]) * 1e6
                          for tag in hold_cases},
        "hold_duration_ms": 5, "access_switch": "schematic SKY130 TG, then off",
        "tt_device_model_ac_only": True,
        "limitations": ["reset TG held continuously on during small-signal noise analysis",
                        "hold access TG is schematic and not parasitic-extracted",
                        "no transient noise or mismatch/PVT", "no full PLIF or complete inference"]
    }
    (OUT / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
