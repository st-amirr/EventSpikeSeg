"""Matched single-packet transfer sweep for the passive SKY130 MIM cell."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"

COMMON = '''.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
'''


def main() -> int:
    import sys
    arg = lambda key, default: next((x.split("=", 1)[1] for x in sys.argv[1:] if x.startswith(key + "=")), str(default))
    cap = float(arg("--membrane-um", 20))
    packet = float(arg("--packet-um", 1))
    step_ns = float(arg("--tstep-ns", 2))
    amplitudes = [float(v) for v in arg("--steps-v", "0.005,0.01,0.025,0.05,0.1,0.18").split(",")]
    start = 50.0
    stop = 100.0
    cases = [(sign, amp, f"{sign}{i}") for i, amp in enumerate(amplitudes) for sign in ("p", "n")]
    lines = ["Matched passive SC packet transfer relative to zero-step switch control", COMMON,
             ".subckt packet_cell state init_level ptop conn conn_b init init_b rst rst_b vdd vcm params: cmem=20 cpacket=1",
             "Xmem state vcm membrane_mim w_um={cmem} l_um={cmem}",
             "Xpacket ptop pbot membrane_mim w_um={cpacket} l_um={cpacket}",
             "Xpacket_switch pbot state conn conn_b vdd 0 transmission_gate",
             "Xpacket_reset pbot vcm rst rst_b vdd 0 transmission_gate",
             "Xstate_init state init_level init init_b vdd 0 transmission_gate",
             "Rleak state vcm 1e15", ".ends packet_cell", "Vdd vdd 0 1.8", "Vcm vcm 0 0.9"]
    signals = [("z", 0.0, "p")]
    signals += [(name, amp, sign) for sign, amp, name in cases]
    for name, amp, sign in signals:
        level = 0.9 + (amp if sign == "p" else -amp) if amp else 0.9
        lines += [f"Vinit_{name} init_{name} 0 PWL(0 1.8 2.499u 1.8 2.5u 0 {stop:g}u 0)",
                  f"Vinitb_{name} initb_{name} 0 PWL(0 0 2.499u 0 2.5u 1.8 {stop:g}u 1.8)",
                  f"Vinitlvl_{name} initlvl_{name} 0 0.9",
                  f"Vconn_{name} conn_{name} 0 PWL(0 0 {start-0.901:.12g}u 0 {start-0.900:.12g}u 1.8 {start+1.899:.12g}u 1.8 {start+1.900:.12g}u 0 {stop:g}u 0)",
                  f"Vconnb_{name} conn_b_{name} 0 PWL(0 1.8 {start-0.901:.12g}u 1.8 {start-0.900:.12g}u 0 {start+1.899:.12g}u 0 {start+1.900:.12g}u 1.8 {stop:g}u 1.8)",
                  f"Vrst_{name} rst_{name} 0 PWL(0 0 {start-1.501:.12g}u 0 {start-1.500:.12g}u 1.8 {start-1.101:.12g}u 1.8 {start-1.100:.12g}u 0 {start+2.099:.12g}u 0 {start+2.100:.12g}u 1.8 {start+2.599:.12g}u 1.8 {start+2.600:.12g}u 0 {stop:g}u 0)",
                  f"Vrstb_{name} rst_b_{name} 0 PWL(0 1.8 {start-1.501:.12g}u 1.8 {start-1.500:.12g}u 0 {start-1.101:.12g}u 0 {start-1.100:.12g}u 1.8 {start+2.099:.12g}u 1.8 {start+2.100:.12g}u 0 {start+2.599:.12g}u 0 {start+2.600:.12g}u 1.8 {stop:g}u 1.8)",
                  f"Vpacket_{name} ptop_{name} 0 PWL(0 0.9 {start-0.001:.12g}u 0.9 {start:.12g}u {level:.12g} {start+1.999:.12g}u {level:.12g} {start+2.000:.12g}u 0.9 {stop:g}u 0.9)",
                  f"Xcell_{name} state_{name} initlvl_{name} ptop_{name} conn_{name} conn_b_{name} init_{name} initb_{name} rst_{name} rst_b_{name} vdd vcm packet_cell cmem={cap:g} cpacket={packet:g}"]
    lines += [".control", "set numdgt=15", f"tran {step_ns:g}n {stop:g}u uic"]
    for name, _, _ in signals:
        lines += [f"meas tran m_{name}_early find v(state_{name}) at=55u",
                  f"meas tran m_{name}_late find v(state_{name}) at=99u"]
        if name in {"z", "p3"}:
            lines += [f"meas tran dbg_{name}_pre find v(state_{name}) at=49u",
                      f"meas tran dbg_{name}_state find v(state_{name}) at=50.5u",
                      f"meas tran dbg_{name}_pbot find v(pbot_{name}) at=50.5u",
                      f"meas tran dbg_{name}_ptop find v(ptop_{name}) at=50.5u",
                      f"meas tran dbg_{name}_conn find v(conn_{name}) at=50.5u"]
    lines += ["quit", ".endc", ".end"]
    tag = f"m{cap:g}_c{packet:g}_steps{'-'.join(f'{x:g}' for x in amplitudes)}_t{step_ns:g}n_matched_state_reset"
    deck = BENCH / f"sky130_passive_sc_packet_transfer_{tag}.cir"
    deck.write_text("\n".join(lines) + "\n")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{OUT}:/workspace/artifacts/analog_asic", "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=135)
    log = proc.stdout + proc.stderr
    (RES / f"sky130_passive_sc_packet_transfer_{tag}.log").write_text(log)
    vals = {k: float(v) for k, v in re.findall(r"(?im)^\s*m_([\w]+)\s*=\s*([-+0-9.eE]+)", log)}
    done = proc.returncode == 0 and len(vals) == 2 * len(signals)
    result = {"simulation_completed": done, "return_code": proc.returncode, "membrane_cap_side_um": cap,
              "packet_cap_side_um": packet, "topplate_steps_v": amplitudes,
              "packet_bottom_reset": "sample_current_membrane_state_before_packet",
              "matched_control": "same_initialization_and_TG_switching_with_zero_topplate_step",
              "max_transient_step_ns": step_ns, "measurements": {},
              "scope": "Isolated one-packet physical SKY130 MIM/TG screen at nominal TT; control subtracts the same init and switch sequence with zero packet amplitude; no threshold/readout, DAC, mismatch, noise, PVT, extraction or network feedback."}
    if done:
        for sign, amp, name in cases:
            for phase in ("early", "late"):
                result["measurements"].setdefault(f"{sign}_step_{amp:g}v", {})[f"matched_{phase}_change_uv"] = (vals[f"{name}_{phase}"] - vals[f"z_{phase}"]) * 1e6
        result["simulation_completed"] = True
    out = RES / f"sky130_passive_sc_packet_transfer_{tag}.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if done else 2


if __name__ == "__main__":
    raise SystemExit(main())
