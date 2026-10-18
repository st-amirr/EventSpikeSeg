"""Screen analog weight programming through the extracted GF180 cell and charge reader."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cap_netlist(cell: str) -> tuple[str, dict[str, Path]]:
    folder = BASE / "layout" / cell
    qpath = folder / "qualification.json"
    q = json.loads(qpath.read_text())
    assert q["magic_drc_count"] == q["gds_roundtrip_drc_count"] == 0
    assert q["lvs_unique"] and q["gds_roundtrip_lvs_unique"]
    files = {"qualification": qpath}
    for key in ("sha256", "input_sha256", "gds_roundtrip_sha256"):
        for name, expected in q.get(key, {}).items():
            path = folder / name if key == "sha256" else ROOT / name
            assert sha(path) == expected, f"qualified source changed: {path}"
            files[f"{key}:{path.relative_to(ROOT).as_posix()}"] = path
    path = folder / f"{cell}_cap.spice"
    text = path.read_text()
    files[f"cap_netlist:{path.relative_to(ROOT).as_posix()}"] = path
    # Keep each macro root callable under its qualified name while isolating child
    # subcircuits that are repeated in other extracted netlists.
    children = re.findall(r"(?mi)^\.subckt\s+(\S+)", text)
    for child in children:
        if child != cell:
            text = re.sub(
                r"(?<![A-Za-z0-9_])" + re.escape(child) + r"(?![A-Za-z0-9_])",
                cell + "__" + child,
                text,
            )
    return text, files


def main() -> None:
    source_cell = "gf180_sampled_weight_current_cell_fullroute_complete_guarded"
    reader_cell = "gf180_active_charge_reader_fullroute_guarded"
    inverter_cell = "gf180_phase_inverter_fullroute"
    source, sources = cap_netlist(source_cell)
    reader, reader_sources = cap_netlist(reader_cell)
    inverter, inverter_sources = cap_netlist(inverter_cell)
    sources.update(reader_sources)
    sources.update(inverter_sources)

    # Calibrated starting points from the schematic-source inverse transfer curve.
    # This screen asks whether physical gate storage and the physical source retain it.
    cases = [
        ("zero", 0.0, 3.30000),
        ("q1e5", 1e-5, 3.11940),
        ("q1e4", 1e-4, 3.07900),
        ("full", 1.0, 2.75000),
    ]
    stem = "gf180_physical_weight_amplitude_transfer_v17_hold_gate_during_read_src" + sha(Path(__file__))[:12]
    model_dir = BASE / "pdk/gf180_primitive_source/models/ngspice"
    model_files = sorted(model_dir.rglob("*.spice"))
    sources.update({f"model:{p.relative_to(ROOT).as_posix()}": p for p in model_files})
    model_prefix = "/workspace/" + model_dir.relative_to(ROOT).as_posix()
    lines = [
        "Physical sampled-weight source to extracted charge-reader diagnostic",
        f".include {model_prefix}/design.spice",
        f".lib {model_prefix}/sm141064.spice typical",
        f".lib {model_prefix}/sm141064.spice mimcap_typical",
        ".param sw_stat_global=0 sw_stat_mismatch=0",
        ".temp 27",
        ".options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18",
        source,
        reader,
        inverter,
        ".global VSUBS",
        "Vsub VSUBS 0 0",
        "Vdd vdd 0 3.3",
        "Vcm vcm 0 1.65",
        "Vbias bias 0 0.75",
        "Vncas ncas 0 1.1",
        "Vpcas pcas 0 2.2",
        # Sample all six gate values onto the actual nine-MIM storage macro,
        # then release the writer and measure a single 1 us read/integration event.
        "Vwrite write_cmd 0 PWL(0 0 1u 0 2u 3.3 4.9u 3.3 5.9u 0 20u 0)",
        "Vreset reset_cmd 0 PWL(0 3.3 8u 3.3 8.01u 0 20u 0)",
        "Vread read_cmd 0 PWL(0 0 9.9u 0 10u 3.3 11u 3.3 11.1u 0 20u 0)",
        "Xwriteb write_cmd writeb vdd 0 gf180_phase_inverter_fullroute",
        "Xreadb read_cmd readb vdd 0 gf180_phase_inverter_fullroute",
        "Xresetb reset_cmd resetb vdd 0 gf180_phase_inverter_fullroute",
    ]
    for tag, _, gate in cases:
        lines.extend(
            [
                f"Vprogram_{tag} program_{tag} 0 {gate:.8f}",
                f"Vmeter_{tag} out_{tag} sourceout_{tag} 0",
                f"Xweight_{tag} program_{tag} write_cmd writeb vcm out_{tag} ncas pcas vdd 0 weight_{tag} ni_{tag} pi_{tag} {source_cell}",
                f"Xreader_{tag} sourceout_{tag} vcm vcm readout_{tag} vdd 0 bias read_cmd readb reset_cmd resetb sum_{tag} cmp_{tag} {reader_cell}",
                f".ic v(readout_{tag})=1.65 v(sum_{tag})=1.65 v(weight_{tag})={gate:.8f}",
            ]
        )
    lines += [".control", "set numdgt=15", "tran 20n 20u 0 20n uic"]
    for tag, _, _ in cases:
        lines += [
            f"meas tran gate_{tag} find v(weight_{tag}) at=9u",
            f"meas tran gate_on_start_{tag} find v(weight_{tag}) at=10.2u",
            f"meas tran gate_on_end_{tag} find v(weight_{tag}) at=10.8u",
            f"meas tran gate_after_{tag} find v(weight_{tag}) at=11.5u",
            f"meas tran before_{tag} find v(readout_{tag}) at=9u",
            f"meas tran after_{tag} find v(readout_{tag}) at=15u",
            f"meas tran charge_{tag} integ i(Vmeter_{tag}) from=10u to=11u",
            f"meas tran avgcurrent_{tag} avg i(Vmeter_{tag}) from=10.2u to=10.8u",
        ]
    for tag, _, _ in cases:
        if tag != "zero":
            lines += [f"let netcharge_{tag}=charge_{tag}-charge_zero", f"print netcharge_{tag}"]
            lines += [f"let dcurrent_{tag}=avgcurrent_{tag}-avgcurrent_zero", f"print dcurrent_{tag}"]
    lines += ["quit", ".endc", ".end"]
    deck = BASE / "benches" / (stem + ".spice")
    deck.write_text("\n".join(lines) + "\n")
    sources[f"bench:{deck.relative_to(ROOT).as_posix()}"] = deck
    log_path = BASE / "results" / (stem + ".log")
    report_path = BASE / "results" / (stem + ".json")
    run = subprocess.run(
        [
            "docker", "run", "--rm", "--network", "none", "--memory", "3g",
            "--cpus", "3", "--volume", f"{ROOT}:/workspace", "--workdir", "/workspace",
            "--entrypoint", "timeout", "eventspikeseg:analog-ngspice47", "300",
            "ngspice", "-b", "/workspace/" + deck.relative_to(ROOT).as_posix(),
        ],
        capture_output=True,
        text=True,
        timeout=315,
    )
    log = run.stdout + run.stderr
    log_path.write_text(log)
    sources[f"log:{log_path.relative_to(ROOT).as_posix()}"] = log_path
    measurements = {}
    for tag, magnitude, gate in cases:
        for metric in ("gate", "gate_on_start", "gate_on_end", "gate_after", "before", "after", "charge", "avgcurrent"):
            m = re.search(rf"(?mi)^{metric}_{tag}\s*=\s*([-+0-9.eE]+)", log)
            if m:
                measurements[f"{metric}_{tag}"] = float(m.group(1))
    for tag, value in re.findall(r"(?mi)^netcharge_(\w+)\s*=\s*([-+0-9.eE]+)", log):
        measurements[f"netcharge_{tag}"] = float(value)
    for tag, value in re.findall(r"(?mi)^dcurrent_(\w+)\s*=\s*([-+0-9.eE]+)", log):
        measurements[f"dcurrent_{tag}"] = float(value)
    fractions = {}
    net_full_charge = measurements.get("netcharge_full", 0.0)
    if net_full_charge not in (None, 0.0):
        for tag, magnitude, _ in cases:
            before = measurements.get(f"before_{tag}")
            after = measurements.get(f"after_{tag}")
            charge = measurements.get(f"charge_{tag}")
            if before is not None and after is not None:
                fractions[tag] = {
                    "normalized_float_magnitude": magnitude,
                    "measured_charge_fraction_of_full_scale": (measurements.get(f"netcharge_{tag}", 0.0) / net_full_charge if tag != "zero" else 0.0),
                    "measured_settled_current_fraction_of_full_scale": (measurements.get(f"dcurrent_{tag}", 0.0) / measurements.get("dcurrent_full", 1.0) if tag != "zero" else 0.0),
                    "programmed_gate_voltage_at_9us_v": measurements.get(f"gate_{tag}"),
                    "target_fraction": magnitude,
                }
    complete = run.returncode == 0 and len(measurements) == (10 * len(cases) - 2) and "timestep too small" not in log.lower()
    report = {
        "simulation_completed": complete,
        "architecture": "One 1 us read event gates current from the physically sampled 9-MIM weight/current cell directly into the physically extracted active charge reader.",
        "settings": {"temp_c": 27, "max_step_ns": 20, "reltol": 1e-6, "abstol_a": 1e-16, "vntol_v": 1e-10, "gmin_s": 1e-18, "program_window_us": [0, 5], "event_window_us": [10, 11]},
        "cases": fractions,
        "measurements": measurements,
        "scope": "Bounded low-tail sample-and-hold validation using refined gate points, a slow1us write ramp and gate-voltage measurements before, during and after the read pulse to diagnose hold disturbance. Current differences are extracted from the same physical MIM-held instances; this is nominal TT27 only, with no mismatch/noise/PVT or model acceptance. The weight gate is programmed through the extracted writer and released; integrated current is zero-subtracted inside ngspice for numerical resolution. Weight is programmed through the extracted writer, WRITE is released before the 1 us read event, and held WEIGHT is measured at9us. Typical extracted macro composition with ideal supply, VCM, biases, gate programming source and phase timing. Physical current-source geometry, nine-MIM gate storage, writer TG, read TG, charge integrator and inverter macros are extracted. Charge is the primary transfer metric after subtracting the zero-weight case; output-voltage differences are below printed absolute precision. These near-aC charge differences are nominal simulator results, not a noise-floor or accuracy proof. No mismatch/noise/PVT, bias/reference distribution, external intermacro routes, original-float population replay, 5 ms actor scheduling, complete neuron, or chip acceptance.",
        "physical_source_layout_used": True,
        "physical_weight_cap_used": True,
        "per_weight_or_model_acceptance": False,
        "full_chip_acceptance": False,
        "sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(sources.values()))},
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(report_path), "simulation_completed": complete, "cases": fractions, "measurements": measurements}, indent=2))
    if not complete:
        raise RuntimeError(f"physical analog screen incomplete rc={run.returncode}:\n{log[-3000:]}")


if __name__ == "__main__":
    main()
