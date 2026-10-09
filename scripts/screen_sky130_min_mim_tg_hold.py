"""Measure 5 ms retention of the routed minimum MIM pair through routed TGs."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "artifacts/analog_asic/benches"
RESULTS = ROOT / "artifacts/analog_asic/results"
PAIR = "/workspace/artifacts/analog_asic/layout/sky130_differential_trim_cap_pair/sky130_differential_trim_cap_pair_pex.spice"
TG = "/workspace/artifacts/analog_asic/layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"
LIB = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice"


def run(corner: str, temp_c: int, reduced_mim: bool = False, tie_substrate: bool = False,
        stacked_tg: bool = False, ngspice47: bool = False, gmin: float | None = None) -> dict:
    if gmin is not None and not 0 < gmin <= 1e-12:
        raise ValueError("diagnostic gmin must be in (0, 1e-12]")
    version = "47" if ngspice47 else "36"
    if (corner, temp_c) not in (("tt", 27), ("ss", 0), ("ff", 85)):
        raise ValueError("supported corners: tt/27, ss/0, ff/85")
    stem = (f"sky130_min_mim_pair_pex_tg_hold_{corner}_temp{temp_c}"
            + ("_reducedmim" if reduced_mim else "")
            + ("_subground" if tie_substrate else "")
            + ("_stackedtg" if stacked_tg else "")
            + (f"_ngspice{version}" if ngspice47 else ""))
    if gmin is not None:
        stem += f"_gmin{gmin:g}"
    pair_include = PAIR
    if reduced_mim or tie_substrate:
        # Diagnostic only: preserve the physical PEX couplings, but collapse
        # the PDK's sub-femtosecond internal capacitor ESR to its nominal C.
        pair_source = (ROOT / PAIR.removeprefix("/workspace/")).read_text(encoding="ascii")
        if reduced_mim:
            pair_source = re.sub(
                r"(?m)^X([01]) (TRIM_[PN]) (STATE_[PN]) sky130_fd_pr__cap_mim_m3_2 l=2e\+06u w=2e\+06u$",
                lambda match: f"Cunit{match.group(1)} {match.group(2)} {match.group(3)} 9.52f",
                pair_source,
            )
            if "sky130_fd_pr__cap_mim_m3_2" in pair_source or "Cunit0" not in pair_source or "Cunit1" not in pair_source:
                raise RuntimeError("reduced MIM replacement missed a PEX device")
        if tie_substrate:
            if "VSUBS" not in pair_source or pair_source.count(".ends") != 1:
                raise RuntimeError("unexpected substrate PEX topology")
            pair_source = pair_source.replace(".ends", "Vsubstrate VSUBS 0 0\n.ends")
        reduced_path = BENCH / ("sky130_min_mim_pair_pex_reducedmim" if reduced_mim else "sky130_min_mim_pair_pex_standard")
        if tie_substrate:
            reduced_path = reduced_path.with_name(reduced_path.name + "_subground")
        reduced_path = reduced_path.with_suffix(".spice")
        BENCH.mkdir(parents=True, exist_ok=True)
        reduced_path.write_text(pair_source, encoding="ascii")
        pair_include = f"/workspace/{reduced_path.relative_to(ROOT).as_posix()}"
    lines = [
        "* Routed 2x2um MIM pair and routed TG 5ms hold; ideal switch control",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2",
        f'.lib "{LIB}" {corner}',
        f'.include "{pair_include}"', f'.include "{TG}"',
        f".temp {temp_c}",
        "Vcm vcm 0 0.9", "Vdd vdd 0 1.8", "Vlow low 0 0.6", "Vhigh high 0 1.2",
        "Ven en 0 PWL(0 1.8 0.9u 1.8 1u 0 5.01m 0)",
        "Venb enb 0 PWL(0 0 0.9u 0 1u 1.8 5.01m 1.8)",
        ".model ideal_init SW(Ron=10 Roff=1e30 Vt=0.9 Vh=0.1)",
        "Xpair_tg vcm state_tg_low vcm state_tg_high sky130_differential_trim_cap_pair",
        *( ["Xtg_low_a low mid_low en enb vdd 0 sky130_transmission_gate_raw",
            "Xtg_low_b mid_low state_tg_low en enb vdd 0 sky130_transmission_gate_raw",
            "Xtg_high_a high mid_high en enb vdd 0 sky130_transmission_gate_raw",
            "Xtg_high_b mid_high state_tg_high en enb vdd 0 sky130_transmission_gate_raw"]
           if stacked_tg else ["Xtg_low low state_tg_low en enb vdd 0 sky130_transmission_gate_raw",
                               "Xtg_high high state_tg_high en enb vdd 0 sky130_transmission_gate_raw"]),
        "Xpair_ideal vcm state_ideal_low vcm state_ideal_high sky130_differential_trim_cap_pair",
        "Sideal_low low state_ideal_low en 0 ideal_init",
        "Sideal_high high state_ideal_high en 0 ideal_init",
        ".control", "set numdgt=15", "tran 1u 5m",
    ]
    for kind in ("tg", "ideal"):
        for side in ("low", "high"):
            lines += [f"meas tran {kind}_{side}_start find v(state_{kind}_{side}) at=2u",
                      f"meas tran {kind}_{side}_end find v(state_{kind}_{side}) at=5m"]
    lines += ["quit", ".endc", ".end", ""]
    if gmin is not None:
        lines.insert(2, f".options gmin={gmin:g}")
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = BENCH / f"{stem}.cir"
    path.write_text("\n".join(lines), encoding="ascii")
    command = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
               "--env", "NGSPICE_MEAS_PRECISION=15", "--volume", f"{ROOT}:/workspace", "--workdir",
               "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
               "--entrypoint", "timeout", f"eventspikeseg:analog-ngspice{version}", "180", "ngspice", "-b",
               f"/workspace/{path.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=195, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (RESULTS / f"{stem}.log").write_text(log, encoding="utf-8")
    values = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*((?:tg|ideal)_(?:low|high)_(?:start|end))\s*=\s*([-+0-9.eE]+)", log)}
    complete = proc.returncode == 0 and f"ngspice-{version} done" in log and len(values) == 8
    report = {
        "test": "sky130_minimum_routed_mim_pair_routed_tg_5ms_hold",
        "corner": corner.upper(), "temperature_c": temp_c,
        "simulator": f"ngspice-{version}",
        "gmin_siemens_requested": gmin,
        "simulation_completed": complete, "return_code": proc.returncode,
        "source_mim": "DRC0/LVS unique routed 2x2um MIM differential trim pair used as two state capacitors",
        "source_tg": "DRC0/LVS unique routed 1/2um NFET/PFET TG PEX",
        "reduced_mim_internal_series_rc": reduced_mim,
        "extracted_substrate_node_tied_to_ground": tie_substrate,
        "two_series_routed_tgs_per_state": stacked_tg,
        "measurements_v": values,
        "limitations": "Two isolated state nodes at0.6/1.2V around0.9V VCM, one 5ms bin, no event injector, readout, reset noise, mismatch, full-float operation or full-chip service. The PEX VSUBS node is not a subcircuit pin; subground mode adds an internal ideal ground to represent the physical substrate and is diagnostic until the extracted interface is repaired. Reduced-MIM mode replaces PDK internal ESR/subnodes with nominal C but keeps PEX coupling. Compare ideal-switch control before interpreting drift.",
    }
    if complete:
        report["hold"] = {
            side: {
                "tg_drift_mv": (values[f"tg_{side}_end"] - values[f"tg_{side}_start"]) * 1e3,
                "ideal_control_drift_mv": (values[f"ideal_{side}_end"] - values[f"ideal_{side}_start"]) * 1e3,
                "tg_minus_ideal_drift_mv": ((values[f"tg_{side}_end"] - values[f"tg_{side}_start"])
                                            - (values[f"ideal_{side}_end"] - values[f"ideal_{side}_start"])) * 1e3,
            } for side in ("low", "high")
        }
    (RESULTS / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    argv = [arg for arg in sys.argv[1:] if arg not in ("--reduced-mim", "--tie-substrate", "--stacked-tg", "--ngspice47")]
    gmin = None
    if "--gmin" in argv:
        index = argv.index("--gmin")
        gmin = float(argv[index + 1])
        del argv[index:index + 2]
    corner = argv[0].lower() if len(argv) > 0 else "ss"
    temp = int(argv[1]) if len(argv) > 1 else {"ss": 0, "tt": 27, "ff": 85}[corner]
    raise SystemExit(0 if run(corner, temp, "--reduced-mim" in sys.argv[1:],
                              "--tie-substrate" in sys.argv[1:],
                              "--stacked-tg" in sys.argv[1:],
                              "--ngspice47" in sys.argv[1:], gmin)["simulation_completed"] else 2)
