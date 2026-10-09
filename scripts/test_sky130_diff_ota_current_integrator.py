"""Screen virtual-ground event-current integration and 5ms state hold."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
MODEL = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
SIM_IMAGE = "eventspikeseg:analog-ngspice36"
CASES = (("tt", 27), ("ss", 0), ("ff", 85))


def run(corner: str, temp: int, pulse_na: float, pulse_ns: float, cap_um: float, rdc_ohm: float, cc: str) -> dict:
    name = f"sky130_diff_ota_current_integrator_{corner}_i{pulse_na:g}n_w{pulse_ns:g}n_c{cap_um:g}u_r{rdc_ohm:g}_cc{cc}"
    deck = BENCH / f"{name}.cir"
    pulse_a = pulse_na * 1e-9
    pulse_s = pulse_ns * 1e-9
    init_s = 50e-6
    start_s = 300e-6
    stop_s = 5e-3
    width_us = pulse_ns / 1000
    edge_s = 200e-9
    lines = [
        f"* Differential OTA-C current integrator {corner.upper()}/{temp}C",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2",
        f".temp {temp}",
        f'.include "{MODEL}/models/parameters/invariant.spice"',
        f'.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        f'.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
        f'.include "{MODEL}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
        f'.include "{MODEL}/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
        '.include "/workspace/asic/analog/modules.spice"',
        '.include "/workspace/asic/analog/sky130_sc_charge_integrator.spice"',
        ".subckt membrane_mim state vcm params: w_um=100 l_um=100",
        "Xmim state vcm sky130_fd_pr__cap_mim_m3_2 w={w_um} l={l_um} mf=1",
        ".ends membrane_mim",
        "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", "Vbn_p vbnp 0 0.65", "Vbn_n vbnn 0 0.65",
        "Vbp_p vbpp 0 0.75", "Vbp_n vbpn 0 0.75",
        # Hold the init TG off. Initialize the OTA-C state directly so the
        # ideal TG's gate transition cannot dominate the solver convergence.
        "Vinit init 0 0", "Vinitb initb 0 1.8",
        # Smooth charge-preserving event envelope (the integral of the
        # difference of tanh edges is pulse_a*pulse_s); PWL slope corners
        # repeatedly caused ngspice timestep underflow at event termination.
        f"BEvent_p sum_p 0 I={{{pulse_a:.12g}*0.5*(tanh((time-{start_s:.12g})/{edge_s:.12g})-tanh((time-{start_s+pulse_s:.12g})/{edge_s:.12g}))}}",
        f"BEvent_n 0 sum_n I={{{pulse_a:.12g}*0.5*(tanh((time-{start_s:.12g})/{edge_s:.12g})-tanh((time-{start_s+pulse_s:.12g})/{edge_s:.12g}))}}",
        # Match the established OTA-C cell polarity (sum on inp). Increase
        # Miller compensation for the large 21.8pF feedback bank.
        f"Xota_p sum_p vcm out_p vbnp vbpp vdd 0 sky130_sc_ota cc={cc}",
        f"Xota_n sum_n vcm out_n vbnn vbpn vdd 0 sky130_sc_ota cc={cc}",
        f"Xcfb_p out_p sum_p membrane_mim w_um={cap_um:g} l_um={cap_um:g} mf=1",
        f"Xcfb_n out_n sum_n membrane_mim w_um={cap_um:g} l_um={cap_um:g} mf=1",
        # The capacitor alone opens the OTA feedback loop at DC. Keep a very
        # weak resistive path so the output common mode has a DC operating
        # point while retaining a long state time constant.
        f"Rdc_p out_p sum_p {rdc_ohm:g}", f"Rdc_n out_n sum_n {rdc_ohm:g}",
        # Seed all internal nodes from the converged TT operating point at
        # VCM=0.9V, VBN=0.65V, VBP=0.75V. The amplifier otherwise has a very
        # large start-up transient across the storage capacitor.
        ".ic v(out_p)=0.897776 v(sum_p)=0.898280 v(xota_p.n1)=0.821146 v(xota_p.ntail)=0.288607 v(xota_p.n2)=0.614234",
        ".ic v(out_n)=0.897776 v(sum_n)=0.898280 v(xota_n.n1)=0.821146 v(xota_n.ntail)=0.288607 v(xota_n.n2)=0.614234",
        ".control", "set noaskquit", "set numdgt=15",
        f"tran 100n {stop_s:g} 0 100n",
        "let diff=v(out_p)-v(out_n)", "let cm=(v(out_p)+v(out_n))/2",
        "meas tran sum_p_pre find v(sum_p) at=299u", "meas tran sum_n_pre find v(sum_n) at=299u",
        "meas tran out_p_pre find v(out_p) at=299u", "meas tran out_n_pre find v(out_n) at=299u",
        "meas tran sum_p_event find v(sum_p) at=301u", "meas tran sum_n_event find v(sum_n) at=301u",
        "meas tran out_p_event find v(out_p) at=301u", "meas tran out_n_event find v(out_n) at=301u",
        "meas tran diff_event find diff at=301u", "meas tran cm_event find cm at=301u",
        "meas tran out_p_5ms find v(out_p) at=5m", "meas tran out_n_5ms find v(out_n) at=5m",
        "meas tran diff_5ms find diff at=5m", "meas tran cm_5ms find cm at=5m",
        "quit", ".endc", ".end", "",
    ]
    deck.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace", "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", SIM_IMAGE, "180", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=195)
    log = proc.stdout + proc.stderr
    (RES / f"{name}.log").write_text(log, encoding="utf-8")
    vals = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*(sum_p_pre|sum_n_pre|sum_p_event|sum_n_event|out_p_pre|out_n_pre|out_p_event|out_n_event|out_p_5ms|out_n_5ms|diff_event|cm_event|diff_5ms|cm_5ms)\s*=\s*([-+0-9.eE]+)", log)}
    complete = proc.returncode == 0 and len(vals) == 14 and "ngspice-36 done" in log and "Timestep too small" not in log
    if not complete:
        (RES / f"{name}.json").write_text(json.dumps({
            "test": "sky130_differential_OTA_C_virtual_ground_current_integration",
            "simulation_completed": False, "corner": corner, "temperature_c": temp,
            "pulse_current_a": pulse_a, "pulse_width_s": pulse_s,
            "feedback_cap_nominal_f_each": 21.8e-12 * (cap_um / 100) ** 2,
            "dc_feedback_resistance_ohm": rdc_ohm,
            "deck": deck.name, "log": f"{name}.log",
            "ngspice_return_code": proc.returncode,
            "failure": "Transient aborted or required measurements are missing; ngspice return code alone is not treated as a pass.",
        }, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError(f"incomplete current-integrator transient at {corner}; see {name}.log")
    virtual_ground_error = max(abs(vals[k] - 0.9) for k in ("sum_p_pre", "sum_n_pre", "sum_p_event", "sum_n_event"))
    row = {"test": "sky130_differential_OTA_C_virtual_ground_current_integration",
           "simulation_completed": complete, "corner": corner, "temperature_c": temp,
           "pulse_current_a": pulse_a, "pulse_width_s": pulse_s,
           "feedback_cap_nominal_f_each": 21.8e-12 * (cap_um / 100) ** 2,
           "dc_feedback_resistance_ohm": rdc_ohm,
           "ota_compensation_capacitance": cc,
           "ideal_state_diff_step_v": 2 * pulse_a * pulse_s / (21.8e-12 * (cap_um / 100) ** 2),
           "measurements_v": vals,
           "summation_node_max_error_from_vcm_v": virtual_ground_error,
           "virtual_ground_pass_1mv": virtual_ground_error <= 1e-3,
           "scope": "Two schematic single-ended SKY130 OTAs in closed-loop MIM feedback; event current is forced directly into the low-impedance summing nodes. Ideal 0.9V initial state and gate drive. This checks virtual-ground behavior, signed charge update and output hold only; no internal CMFB, physical event-weight DAC, extracted OTA layout, noise, mismatch, threshold/reset/beta, or full float sequence.",
           "deck": deck.name}
    (RES / f"{name}.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
    return row


def main() -> int:
    pulse_na = float(next((a.split("=", 1)[1] for a in __import__("sys").argv if a.startswith("--pulse-na=")), "100"))
    pulse_ns = float(next((a.split("=", 1)[1] for a in __import__("sys").argv if a.startswith("--pulse-ns=")), "10"))
    cap_um = float(next((a.split("=", 1)[1] for a in __import__("sys").argv if a.startswith("--cap-um=")), "100"))
    rdc_ohm = float(next((a.split("=", 1)[1] for a in __import__("sys").argv if a.startswith("--rdc-ohm=")), "1e9"))
    cc = next((a.split("=", 1)[1] for a in __import__("sys").argv if a.startswith("--cc=")), "50p")
    corner_arg = next((a.split("=", 1)[1] for a in __import__("sys").argv if a.startswith("--corners=")), "tt,ss,ff")
    cases = {corner: temp for corner, temp in CASES}
    selected = [(corner, cases[corner]) for corner in corner_arg.split(",")]
    if not selected or any(corner not in cases for corner, _ in selected):
        raise ValueError("--corners must be a comma-separated subset of tt,ss,ff")
    if pulse_na < 0 or pulse_ns <= 0:
        raise ValueError("pulse current must be nonnegative and pulse width positive")
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    rows = [run(corner, temp, pulse_na, pulse_ns, cap_um, rdc_ohm, cc) for corner, temp in selected]
    summary = {"test": "sky130_differential_OTA_C_virtual_ground_current_integration_PVT",
               "simulation_completed": all(row["simulation_completed"] for row in rows),
               "pulse_current_na": pulse_na, "pulse_width_ns": pulse_ns, "cases": rows,
               "virtual_ground_pass_all_cases": all(row["virtual_ground_pass_1mv"] for row in rows),
               "full_analog_architecture_ready": False}
    (RES / f"sky130_diff_ota_current_integrator_i{pulse_na:g}n_w{pulse_ns:g}n_c{cap_um:g}u_r{rdc_ohm:g}_cc{cc}_{corner_arg.replace(',', '-')}.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
