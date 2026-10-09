"""Screen bidirectional writes and broadcast disturb on the extracted diode state."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "artifacts/analog_asic/benches"
RESULTS = ROOT / "artifacts/analog_asic/results"
PAIR = BENCH / "sky130_min_mim_pair_pex_reducedmim_subground.spice"
MOSCAP = ROOT / "artifacts/analog_asic/layout/sky130_moscap_pcell_probe_10x1_nf1/moscap_pcell_probe.spice"
DIODE_DIR = ROOT / "artifacts/analog_asic/layout/sky130_diode_pd2nw_05v5_probe_1x1"
DIODE_PEX = DIODE_DIR / "diode_pd2nw_05v5_probe_pex.spice"
DIODE_QUAL = DIODE_DIR / "qualification.json"
LIB = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice"

def token(value: float) -> str:
    return f"{value:g}".replace("-", "neg").replace(".", "p")


def main() -> None:
    args = sys.argv[1:]
    version = "47" if "--ngspice47" in args else "36"
    high_bus_v = float(args[args.index("--high-bus-v") + 1]) if "--high-bus-v" in args else 2.2
    low_bus_v = float(args[args.index("--low-bus-v") + 1]) if "--low-bus-v" in args else -0.4
    if not 2.2 <= high_bus_v <= 4 or not -2 <= low_bus_v <= -0.4:
        raise ValueError("write buses outside bounded 2.2..4V / -2..-0.4V screen")
    stem = (f"sky130_diode_state_write_tt27_plus{token(high_bus_v)}_minus{token(low_bus_v)}_width20ns"
            + ("_ngspice47" if version == "47" else ""))
    qualification = json.loads(DIODE_QUAL.read_text(encoding="utf-8"))
    if not (qualification["magic_drc_zero"] and qualification["netgen_lvs_unique_match"]
            and qualification["ports_in_extracted_order"] == ["ANODE", "SUB", "CATHODE"]):
        raise RuntimeError("physical diode PEX is not qualified")
    well_area = qualification["estimated_nwell_area_um2_from_mag_rectangle"]
    well_perimeter = qualification["estimated_nwell_perimeter_um_from_mag_rectangle"]
    lines = [
        "* Physical diode PEX, extracted MIM/MOS gate-cap, bidirectional write and broadcast victim",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2",
        f'.lib "{LIB}" tt',
        f'.include "/workspace/{PAIR.relative_to(ROOT).as_posix()}"',
        f'.include "/workspace/{MOSCAP.relative_to(ROOT).as_posix()}"',
        f'.include "/workspace/{DIODE_PEX.relative_to(ROOT).as_posix()}"',
        ".temp 27", "Vcm vcm 0 0.9", "Vlow low 0 0.899", "Vhigh high 0 0.901",
        "Vinit init_en 0 PWL(0 1.8 0.99u 1.8 1u 0 5u 0)",
        ".model ideal_init SW(Ron=10 Roff=1e30 Vt=0.9 Vh=0.1)",
        f"Vplus_high plus_high 0 PWL(0 0 1.999u 0 2u {high_bus_v:g} 2.02u {high_bus_v:g} 2.021u 0 5u 0)",
        f"Vminus_low minus_low 0 PWL(0 1.8 1.999u 1.8 2u {low_bus_v:g} 2.02u {low_bus_v:g} 2.021u 1.8 5u 1.8)",
        f"Vplus_low plus_low 0 PWL(0 0 3.999u 0 4u {high_bus_v:g} 4.02u {high_bus_v:g} 4.021u 0 5u 0)",
        f"Vminus_high minus_high 0 PWL(0 1.8 3.999u 1.8 4u {low_bus_v:g} 4.02u {low_bus_v:g} 4.021u 1.8 5u 1.8)",
    ]
    for cell in ("selected", "broadcast_victim"):
        lo, hi = f"{cell}_low", f"{cell}_high"
        lines.append(f"Xpair_{cell} vcm {lo} vcm {hi} sky130_differential_trim_cap_pair")
        for side, state in (("low", lo), ("high", hi)):
            lines += [
                f"Sinit_{cell}_{side} {side} {state} init_en 0 ideal_init",
                f"Xcap_{cell}_{side} {state} 0 0 moscap_pcell_probe",
                f"Xplus_{cell}_{side} plus_{side} 0 {state} diode_pd2nw_05v5_probe",
                f"Xminus_{cell}_{side} {state} 0 minus_{side} diode_pd2nw_05v5_probe",
                f"Dwell_{cell}_{side} 0 {state} sky130_fd_pr__model__parasitic__diode_ps2nw area={well_area:g} pj={well_perimeter:g}",
            ]
    lines += [".control", "set numdgt=15", "tran 0.2n 5u"]
    for cell in ("selected", "broadcast_victim"):
        for side in ("low", "high"):
            for phase, at in (("before", "1.99u"), ("after_positive", "2.1u"),
                              ("before_negative", "3.99u"), ("after_negative", "4.1u")):
                lines.append(f"meas tran {cell}_{side}_{phase} find v({cell}_{side}) at={at}")
    for source, phase, at in (("Vplus_high", "positive", "2.01u"),
                              ("Vminus_low", "positive", "2.01u"),
                              ("Vplus_low", "negative", "4.01u"),
                              ("Vminus_high", "negative", "4.01u")):
        lines.append(f"meas tran {source.lower()}_current_{phase} find i({source}) at={at}")
        lines.append(f"meas tran {source.lower()}_voltage_{phase} find v({source[1:].lower()}) at={at}")
    lines += ["quit", ".endc", ".end", ""]
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace", "--workdir",
           "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
           "--entrypoint", "timeout", f"eventspikeseg:analog-ngspice{version}", "180", "ngspice", "-b",
           f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=195, cwd=ROOT)
    log = proc.stdout + proc.stderr
    log_path = RESULTS / f"{stem}.log"
    log_path.write_text(log, encoding="utf-8")
    values = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*((?:selected|broadcast_victim)_(?:low|high)_(?:before|after_positive|before_negative|after_negative))\s*=\s*([-+0-9.eE]+)", log)}
    currents = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*(v(?:plus|minus)_(?:low|high)_current_(?:positive|negative))\s*=\s*([-+0-9.eE]+)", log)}
    bus_voltages = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*(v(?:plus|minus)_(?:low|high)_voltage_(?:positive|negative))\s*=\s*([-+0-9.eE]+)", log)}
    complete = (proc.returncode == 0 and f"ngspice-{version} done" in log and len(values) == 16
                and len(currents) == 4 and len(bus_voltages) == 4)
    phases = {}
    if complete:
        for cell in ("selected", "broadcast_victim"):
            phases[cell] = {phase: {
                "low_v": values[f"{cell}_low_{phase}"],
                "high_v": values[f"{cell}_high_{phase}"],
                "differential_mv": (values[f"{cell}_high_{phase}"]
                                    - values[f"{cell}_low_{phase}"]) * 1e3,
            } for phase in ("before", "after_positive", "before_negative", "after_negative")}
    report = {
        "test": "sky130_diode_state_signed_write_and_broadcast_screen",
        "simulation_completed": complete, "return_code": proc.returncode,
        "corner": "TT", "temperature_c": 27,
        "simulator": f"ngspice-{version}",
        "pulse_high_bus_v": high_bus_v, "pulse_low_bus_v": low_bus_v,
        "pulse_width_ns": 20,
        "phases": phases,
        "source_currents_a": currents,
        "bus_voltages_v": bus_voltages,
        "source_sha256": {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (PAIR, MOSCAP, DIODE_PEX, DIODE_QUAL, deck, log_path)},
        "limitations": "Ideal initial programming and voltage-source charge pumps; one fixed large write pulse, TT only. Both state pairs intentionally share the same four update buses, so equal broadcast disturbance is expected rather than selective addressing. Diode PEX includes an explicit substrate port but not a well-to-substrate diode; the extra junction is a drawn-well geometry proxy. No routed state macro, safe half-select addressing, small-weight precision, noise/mismatch, full PLIF order or population service.",
    }
    out = RESULTS / f"{stem}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "simulation_completed": complete, "phases": phases,
                      "error_tail": log[-1500:] if not complete else None}, indent=2))
    if not complete:
        raise RuntimeError(f"diode write screen failed: {log[-1500:]}")


if __name__ == "__main__":
    main()
