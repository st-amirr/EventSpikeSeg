"""Check a physically held MIM gate driving the membrane-scale PFET for 5 ms."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
SCALE_CELL = "gf180_sampled_weight_current_cell_fullroute_complete_guarded"
INV_CELL = "gf180_phase_inverter_fullroute"
SCALE_GATE_VALUES = [
    ("minimum", 8.23e-5, 2.9509),
    ("median", 0.01536, 2.7528),
    ("maximum", 1.0, 2.5741),
]
NAME = "gf180_membrane_scale_direct_mim_gate_v3"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extracted_cell(cell: str) -> tuple[str, dict[str, Path]]:
    folder = BASE / "layout" / cell
    qpath = folder / "qualification.json"
    q = json.loads(qpath.read_text(encoding="utf-8"))
    assert q["magic_drc_count"] == q["gds_roundtrip_drc_count"] == 0
    assert q["lvs_unique"] and q["gds_roundtrip_lvs_unique"]
    cap = folder / f"{cell}_cap.spice"
    text = cap.read_text(encoding="utf-8")
    files = {"qualification": qpath, "cap_netlist": cap}
    for key in ("sha256", "input_sha256", "gds_roundtrip_sha256"):
        for rel, expected in q.get(key, {}).items():
            path = folder / rel if key == "sha256" else ROOT / rel
            assert sha(path) == expected, f"qualified source changed: {path}"
            files[f"{key}:{path.relative_to(ROOT).as_posix()}"] = path
    children = re.findall(r"(?mi)^\.subckt\s+(\S+)", text)
    for child in children:
        if child != cell:
            text = re.sub(r"(?<![A-Za-z0-9_])" + re.escape(child) + r"(?![A-Za-z0-9_])", cell + "__" + child, text)
    return text, files


def main() -> None:
    source, sources = extracted_cell(SCALE_CELL)
    inverter, inverter_sources = extracted_cell(INV_CELL)
    sources.update(inverter_sources)
    model_dir = BASE / "pdk/gf180_primitive_source/models/ngspice"
    sources.update({f"model:{p.relative_to(ROOT).as_posix()}": p for p in model_dir.rglob("*.spice")})
    model_prefix = "/workspace/" + model_dir.relative_to(ROOT).as_posix()
    scale_prefix = SCALE_CELL + "__"
    lines = [
        f".include {model_prefix}/design.spice",
        f".lib {model_prefix}/sm141064.spice typical",
        f".lib {model_prefix}/sm141064.spice mimcap_typical",
        ".param sw_stat_global=0 sw_stat_mismatch=0", ".temp 27",
        ".options method=gear reltol=1e-6 abstol=1e-19 vntol=1e-10 gmin=1e-18",
        source, inverter, ".global VSUBS", "Vsub VSUBS 0 0", "Vdd vdd 0 3.3", "Vcm vcm 0 1.65",
        "Vwrite write_cmd 0 PWL(0 0 1u 0 2u 3.3 4.9u 3.3 5.9u 0 5.1m 0)",
        "Xwriteb write_cmd writeb vdd 0 gf180_phase_inverter_fullroute",
    ]
    for label, _, gate in SCALE_GATE_VALUES:
        lines.extend([
            f"Vprogram_{label} program_{label} 0 {gate:.8f}",
            f"Xgatecap_{label} program_{label} weight_{label} write_cmd writeb 0 vdd {scale_prefix}gf180_fixed_body_tg_fullroute_half",
            f"Xmim_{label} weight_{label} vcm 0 {scale_prefix}gf180_mim_bank_7x7_n9",
            f"Vdrain_{label} drain_{label} 0 1.65",
            f"Vmeter_{label} out_{label} drain_{label} 0",
            f"Mscale_{label} out_{label} weight_{label} vdd vdd pfet_03v3 w=0.42u l=10u",
            f".ic v(weight_{label})={gate:.8f}",
        ])
    lines += [".control", "set numdgt=15", "tran 20n 5.1m 0 20n uic"]
    sample_times = {"program_release": 9e-6, "100us": 100e-6, "1ms": 1e-3, "5ms": 5e-3}
    for label, _, _ in SCALE_GATE_VALUES:
        for suffix, time_s in sample_times.items():
            lines.append(f"meas tran gate_{label}_{suffix.replace('us','us')} find v(weight_{label}) at={time_s:.9g}")
            lines.append(f"meas tran current_{label}_{suffix.replace('us','us')} find i(Vmeter_{label}) at={time_s:.9g}")
    lines += ["quit", ".endc", ".end", ""]
    deck = BASE / "benches" / f"{NAME}.spice"
    log_path = BASE / "results" / f"{NAME}.log"
    report_path = BASE / "results" / f"{NAME}.json"
    assert not any(path.exists() for path in (deck, log_path, report_path)), "preserve earlier artifacts"
    deck.write_text("\n".join(lines), encoding="utf-8")
    sources[f"bench:{deck.relative_to(ROOT).as_posix()}"] = deck
    run = subprocess.run([
        "docker", "run", "--rm", "--network", "none", "--memory", "2g", "--cpus", "2",
        "--volume", f"{ROOT}:/workspace", "--workdir", "/workspace", "--entrypoint", "timeout",
        "eventspikeseg:analog-ngspice47", "120", "ngspice", "-b", "/workspace/" + deck.relative_to(ROOT).as_posix(),
    ], capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    log_path.write_text(log, encoding="utf-8")
    sources[f"log:{log_path.relative_to(ROOT).as_posix()}"] = log_path
    measurements = {f"{metric}_{label}_{when}": float(value) for metric, label, when, value in re.findall(
        r"(?mi)^(gate|current)_(minimum|median|maximum)_(program_release|100us|1ms|5ms)\s*=\s*([-+0-9.eE]+)", log
    )}
    complete = run.returncode == 0 and len(measurements) == 24 and "timestep too small" not in log.lower()
    ratios = {}
    if complete:
        for when in ("program_release", "100us", "1ms", "5ms"):
            imin = measurements[f"current_minimum_{when}"]
            imid = measurements[f"current_median_{when}"]
            imax = measurements[f"current_maximum_{when}"]
            ratios[when] = {"min_to_median": imid / imin, "median_to_max": imax / imid, "min_to_max": imax / imin}
    targets = {"min_to_median": 0.01536 / 8.23e-5, "median_to_max": 1 / 0.01536, "min_to_max": 1 / 8.23e-5}
    errors = {when: {key: 100 * (ratio[key] / targets[key] - 1) for key in targets} for when, ratio in ratios.items()}
    report = {
        "simulation_completed": complete,
        "returncode": run.returncode,
        "simulator": "ngspice47, GF180 typical 27C; extracted 9-MIM weight hold bank and extracted writer TG/inverter drive an external scale PFET",
        "targets": {"normalized_scale": {label: magnitude for label, magnitude, _ in SCALE_GATE_VALUES}, "ratios": targets},
        "gate_programming_v": {label: gate for label, _, gate in SCALE_GATE_VALUES},
        "measurements": measurements,
        "measured_ratios": ratios,
        "ratio_error_percent": errors,
        "scope": "The sampled 9-MIM bank and writer transistor are extracted; the membrane-scale PFET is a GF180 model device without new macro layout. Gate programmed by an ideal source, writer releases at5us, current/gate are sampled through5ms. This checks scale-control retention and current transfer only; no current multiplier, signed weight sum, membrane state update, original-float inference, PVT/noise, or population5ms service is qualified.",
        "sha256": {path.relative_to(ROOT).as_posix(): sha(path) for path in sorted(set(sources.values()))},
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "completed": complete, "measurements": measurements,
                      "ratios": ratios, "errors": errors}, indent=2))
    if not complete:
        raise RuntimeError(f"screen incomplete rc={run.returncode}:\n{log[-2500:]}")


if __name__ == "__main__":
    main()


