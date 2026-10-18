"""Use the extracted held 9-MIM gate and charge reader with a higher-current scale PFET."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
SOURCE = "gf180_membrane_scale_current_cell_v6"
READER = "gf180_active_charge_reader_fullroute_guarded"
INVERTER = "gf180_phase_inverter_fullroute"
CASES = [("zero", 0.0, 3.30000), ("minimum", 8.23e-5, 2.9509),
         ("median", 0.01536, 2.7528), ("maximum", 1.0, 2.5741)]
NAME = "gf180_membrane_scale_mim_gate_reader_v4"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def physical_cell(name: str) -> tuple[str, dict[str, Path]]:
    folder = BASE / "layout" / name
    qpath = folder / "qualification.json"
    q = json.loads(qpath.read_text(encoding="utf-8"))
    assert q["magic_drc_count"] == q["gds_roundtrip_drc_count"] == 0
    assert q["lvs_unique"] and q["gds_roundtrip_lvs_unique"]
    cap = folder / f"{name}_cap.spice"
    text = cap.read_text(encoding="utf-8")
    files = {"qualification": qpath, "cap_netlist": cap}
    for group in ("sha256", "input_sha256", "gds_roundtrip_sha256"):
        for rel, expected in q.get(group, {}).items():
            path = folder / rel if group == "sha256" else ROOT / rel
            assert sha(path) == expected, f"qualified view changed: {path}"
            files[f"{group}:{path.relative_to(ROOT).as_posix()}"] = path
    for child in re.findall(r"(?mi)^\.subckt\s+(\S+)", text):
        if child != name:
            text = re.sub(r"(?<![A-Za-z0-9_])" + re.escape(child) + r"(?![A-Za-z0-9_])", name + "__" + child, text)
    return text, files


def main() -> None:
    source, files = physical_cell(SOURCE)
    reader, extra = physical_cell(READER)
    files.update(extra)
    inverter, extra = physical_cell(INVERTER)
    files.update(extra)
    models = BASE / "pdk/gf180_primitive_source/models/ngspice"
    files.update({f"models:{p.relative_to(ROOT).as_posix()}": p for p in models.rglob("*.spice")})
    model_prefix = "/workspace/" + models.relative_to(ROOT).as_posix()
    lines = [
        f".include {model_prefix}/design.spice", f".lib {model_prefix}/sm141064.spice typical",
        f".lib {model_prefix}/sm141064.spice mimcap_typical",
        ".param sw_stat_global=0 sw_stat_mismatch=0", ".temp 27",
        ".options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18",
        source, reader, inverter, ".global VSUBS", "Vsub VSUBS 0 0",
        "Vdd vdd 0 3.3", "Vcm vcm 0 1.65", "Vbias bias 0 0.75", "Vncas ncas 0 1.1", "Vpcas pcas 0 2.2",
        "Vwrite write_cmd 0 PWL(0 0 1u 0 2u 3.3 4.9u 3.3 5.9u 0 5.1m 0)",
        "Vread read_cmd 0 PWL(0 0 4.999m 0 5.0m 3.3 5.001m 3.3 5.002m 0 5.1m 0)",
        "Vreset reset_cmd 0 PWL(0 3.3 4.990m 3.3 4.991m 0 5.1m 0)",
        "Xwriteb write_cmd writeb vdd 0 gf180_phase_inverter_fullroute",
        "Xreadb read_cmd readb vdd 0 gf180_phase_inverter_fullroute",
        "Xresetb reset_cmd resetb vdd 0 gf180_phase_inverter_fullroute",
    ]
    for tag, magnitude, gate in CASES:
        lines.extend([
            f"Vprogram_{tag} program_{tag} 0 {gate:.8f}",
            f"Vdummy_{tag} dummy_{tag} 0 1.65",
            f"Vmeter_{tag} out_{tag} sourceout_{tag} 0",
            f"Xscale_{tag} program_{tag} write_cmd writeb vcm ncas pcas vdd 0 out_{tag} weight_{tag} {SOURCE}",
            f"Xread_{tag} sourceout_{tag} vcm vcm readout_{tag} vdd 0 bias read_cmd readb reset_cmd resetb sum_{tag} cmp_{tag} {READER}",
            f"Cload_{tag} readout_{tag} 0 50f",
            f".ic v(weight_{tag})={gate:.8f} v(readout_{tag})=1.65 v(sum_{tag})=1.65",
        ])
    lines += [".control", "set numdgt=15", "tran 100n 5.1m 0 100n uic"]
    for tag, _, _ in CASES:
        lines.extend([
            f"meas tran gate_{tag}_9us find v(weight_{tag}) at=9u",
            f"meas tran gate_{tag}_5ms find v(weight_{tag}) at=5m",
            f"meas tran before_{tag} find v(readout_{tag}) at=4.998m",
            f"meas tran after_{tag} find v(readout_{tag}) at=5.01m",
            f"meas tran charge_{tag} integ i(Vmeter_{tag}) from=5m to=5.001m",
            f"meas tran avgcurrent_{tag} avg i(Vmeter_{tag}) from=5.0002m to=5.0008m",
        ])
    lines += ["quit", ".endc", ".end", ""]
    deck = BASE / "benches" / f"{NAME}.spice"
    log_path = BASE / "results" / f"{NAME}.log"
    report_path = BASE / "results" / f"{NAME}.json"
    assert not any(path.exists() for path in (deck, log_path, report_path)), "preserve earlier attempts"
    deck.write_text("\n".join(lines), encoding="utf-8")
    files[f"bench:{deck.relative_to(ROOT).as_posix()}"] = deck
    run = subprocess.run([
        "docker", "run", "--rm", "--network", "none", "--memory", "2g", "--cpus", "2",
        "--volume", f"{ROOT}:/workspace", "--workdir", "/workspace", "--entrypoint", "timeout",
        "eventspikeseg:analog-ngspice47", "120", "ngspice", "-b", "/workspace/" + deck.relative_to(ROOT).as_posix(),
    ], capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    log_path.write_text(log, encoding="utf-8")
    files[f"log:{log_path.relative_to(ROOT).as_posix()}"] = log_path
    values = {key: float(value) for key, value in re.findall(
        r"(?mi)^((?:gate_(?:zero|minimum|median|maximum)_(?:9us|5ms))|(?:(?:before|after|charge|avgcurrent)_(?:zero|minimum|median|maximum)))\s*=\s*([-+0-9.eE]+)", log
    )}
    complete = run.returncode == 0 and len(values) == 24 and "timestep too small" not in log.lower()
    fractions = {}
    if complete:
        for tag, magnitude, _ in CASES:
            charge = values[f"charge_{tag}"] - values["charge_zero"]
            avg = values[f"avgcurrent_{tag}"] - values["avgcurrent_zero"]
            fractions[tag] = {
                "target_scale_fraction": magnitude,
                "measured_zero_subtracted_charge_fraction": charge / (values["charge_maximum"] - values["charge_zero"]),
                "measured_zero_subtracted_current_fraction": avg / (values["avgcurrent_maximum"] - values["avgcurrent_zero"]),
                "held_gate_9us_v": values[f"gate_{tag}_9us"],
                "held_gate_5ms_v": values[f"gate_{tag}_5ms"],
                "readout_change_v": values[f"after_{tag}"] - values[f"before_{tag}"],
            }
    report = {
        "simulation_completed": complete, "returncode": run.returncode,
        "simulator": "ngspice47; GF180 typical 27C; extracted 9-MIM writer/current cell and charge reader, with the layout-qualified extracted parent scale cell including routed parasitics",
        "cases": fractions, "raw_measurements": values,
        "scope": "The extracted parent macro combines the held 9-MIM writer/current cell and physically routed scale PFET. It feeds the extracted charge reader for one 1us event after a 5ms hold. Gate values use the prior nominal map; routed parent parasitics are included. No scale-weight multiplier, membrane-state update, original-float replay, PVT/noise/mismatch, or full-population5ms service is qualified.",
        "sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(files.values()))},
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "completed": complete, "cases": fractions, "raw_measurements": values}, indent=2))
    if not complete:
        raise RuntimeError(f"scale screen incomplete rc={run.returncode}:\n{log[-2500:]}")


if __name__ == "__main__":
    main()

