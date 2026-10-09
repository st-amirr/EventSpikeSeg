"""Screen direct differential MIM state update using physical SKY130 switches."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic/results/sky130_differential_cap_packet"
IMAGE = "eventspikeseg:analog-ngspice36"
SEQ = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--sequence=")), "pn")
CMEM = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--cmem-um=")), "100")
CPKT = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--cpkt-um=")), "1")
STEP = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--step-v=")), "0.3")
DT = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--max-step-ns=")), "10")
CORNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--corner=")), "tt").lower()
TEMP = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--temp-c=")), {"tt": "27", "ss": "0", "ff": "85"}.get(CORNER, "27"))
T1 = float(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--event1-us=")), "500"))
T2 = float(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--event2-us=")), "4500"))
PHYSICAL_TG = "--physical-tg" in sys.argv
PHYSICAL_MIM_CAPS = "--physical-mim-caps" in sys.argv
STATE_RESET_TGS = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--state-reset-tgs=")), "10"))
STATE_BANK_COPIES = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--state-bank-copies=")), "1"))
PACKET_BANK_COPIES = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--packet-bank-copies=")), "1"))
PULSE_US = float(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--event-pulse-us=")), "1.7"))
CAL_PHASE = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--calibration-phase=")), "mid").lower()
TG_NETLIST = ROOT / "artifacts/analog_asic/layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"
MIM_STATE = ROOT / "artifacts/analog_asic/layout/sky130_mim_state_bank_square/mim_state_square_3x4_w30_l30.spice"
MIM_PACKET = ROOT / "artifacts/analog_asic/layout/sky130_mim_packet_2x2/packet_cap_mim_2x2um.spice"
TG_MODEL_BLOCK = ('.include "/workspace/artifacts/analog_asic/layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"\n'
                  '.subckt sky130_pex_tg a b en enb vdd vss\n'
                  'Xphysical a b en enb vdd vss sky130_transmission_gate_raw\n'
                  '.ends sky130_pex_tg') if PHYSICAL_TG else ""
STATE_RESET_BLOCK = (("Vstate_init state_init 0 PWL(0 1.8 1.9u 1.8 2u 0 5.005m 0)\n"
                      "Vstate_initb state_initb 0 PWL(0 0 1.9u 0 2u 1.8 5.005m 1.8)\n" +
                      "\n".join(f"Xstate_rstp{i} outp vcm state_init state_initb vdd 0 sky130_pex_tg\nXstate_rstn{i} outn vcm state_init state_initb vdd 0 sky130_pex_tg" for i in range(10))) if PHYSICAL_TG else
                      "* Reset release uses break-before-make gate timing to reduce switch injection.\n"
                      "Vstate_rstn state_rstn 0 PWL(0 1.8 1.9u 1.8 2u 0 5.005m 0)\n"
                      "Vstate_rstp state_rstp 0 PWL(0 0 2.0u 0 2.1u 1.8 5.005m 1.8)\n"
                      "Xstate_rstnp outp state_rstn vcm 0 sky130_fd_pr__nfet_01v8 w=10 l=0.15\n"
                      "Xstate_rstpp outp state_rstp vcm vdd sky130_fd_pr__pfet_01v8 w=20 l=0.15\n"
                      "Xstate_rstnn outn state_rstn vcm 0 sky130_fd_pr__nfet_01v8 w=10 l=0.15\n"
                      "Xstate_rstpn outn state_rstp vcm vdd sky130_fd_pr__pfet_01v8 w=20 l=0.15")
if not 1 <= STATE_RESET_TGS <= 10:
    raise ValueError("state-reset-tgs must be 1..10")
if PHYSICAL_TG:
    STATE_RESET_BLOCK = ("Vstate_init state_init 0 PWL(0 1.8 1.9u 1.8 2u 0 5.005m 0)\n"
                         "Vstate_initb state_initb 0 PWL(0 0 1.9u 0 2u 1.8 5.005m 1.8)\n" +
                         "\n".join(f"Xstate_rstp{i} outp vcm state_init state_initb vdd 0 sky130_pex_tg\n"
                                      f"Xstate_rstn{i} outn vcm state_init state_initb vdd 0 sky130_pex_tg"
                                      for i in range(STATE_RESET_TGS)))


def polarity(symbol: str, sign: int) -> float:
    event_sign = 1 if symbol == "p" else (-1 if symbol == "n" else 0)
    return 0.9 + sign * event_sign * float(STEP)


def pwi(sequence: str, sign: int) -> str:
    early, late = (polarity(symbol, sign) for symbol in sequence)
    return f"PWL(0 0.9 {T1-0.1:g}u 0.9 {T1:g}u {early:g} {T1+PULSE_US:g}u {early:g} {T1+PULSE_US+0.1:g}u 0.9 {T2-0.1:g}u 0.9 {T2:g}u {late:g} {T2+PULSE_US:g}u {late:g} {T2+PULSE_US+0.1:g}u 0.9 5005u 0.9)"


def gate_pwl(kind: str) -> str:
    inverse = kind.endswith("b")
    base = kind[:-1] if inverse else kind
    points = [(0.0, 0.0 if base in ("connect", "reset") else 1.8)]
    for event in (T1, T2):
        if base == "connect":
            points += [(event - 0.4, 0.0), (event - 0.3, 1.8),
                       (event + PULSE_US, 1.8), (event + PULSE_US + 0.1, 0.0)]
        elif base == "reset":
            points += [(event - 1.0, 0.0), (event - 0.9, 1.8),
                       (event - 0.5, 1.8), (event - 0.4, 0.0),
                       (event + PULSE_US + 0.3, 0.0), (event + PULSE_US + 0.4, 1.8),
                       (event + PULSE_US + 0.7, 1.8), (event + PULSE_US + 0.8, 0.0)]
    points.append((5005.0, points[-1][1]))
    if inverse:
        points = [(t, 1.8 - v) for t, v in points]
    return "PWL(" + " ".join(f"{t:g}u {v:g}" for t, v in points) + ")"


def main() -> None:
    if len(SEQ) != 2 or any(x not in "pnz" for x in SEQ):
        raise ValueError("sequence must be pp/nn/pn/np/pz/nz/zp/zn/zz")
    OUT.mkdir(parents=True, exist_ok=True)
    if CORNER not in ("tt", "ss", "ff"):
        raise ValueError("corner must be tt/ss/ff")
    if not 1 <= STATE_BANK_COPIES <= 8:
        raise ValueError("state-bank-copies must be 1..8")
    if not 1 <= PACKET_BANK_COPIES <= 16:
        raise ValueError("packet-bank-copies must be 1..16")
    if not 0.5 <= PULSE_US <= 10:
        raise ValueError("event-pulse-us must be 0.5..10")
    if CAL_PHASE not in ("mid", "end"):
        raise ValueError("calibration-phase must be mid or end")
    pulse_tag = f"_pw{PULSE_US:g}u".replace(".", "p") if PULSE_US != 1.7 else ""
    phase_tag = "_cend" if CAL_PHASE == "end" else ""
    tag = f"{SEQ}_{CORNER}_t{TEMP}_t1{T1:g}_t2{T2:g}_cm{CMEM}_cp{CPKT}_step{STEP}_s{DT}n{'_pextg_r'+str(STATE_RESET_TGS) if PHYSICAL_TG else ''}{'_physmim_b'+str(STATE_BANK_COPIES) if PHYSICAL_MIM_CAPS else ''}{'_pkt'+str(PACKET_BANK_COPIES) if PACKET_BANK_COPIES > 1 else ''}{pulse_tag}{phase_tag}"
    cap_includes = (f'.include "/workspace/{MIM_STATE.relative_to(ROOT).as_posix()}"\n'
                    f'.include "/workspace/{MIM_PACKET.relative_to(ROOT).as_posix()}"') if PHYSICAL_MIM_CAPS else ""
    mem_cap = ("mim_state_square_3x4_w30_l30" if PHYSICAL_MIM_CAPS else
               "sky130_fd_pr__cap_mim_m3_2")
    pkt_cap = ("packet_cap_mim_2x2um" if PHYSICAL_MIM_CAPS else
               "sky130_fd_pr__cap_mim_m3_2")
    mem_size = "" if PHYSICAL_MIM_CAPS else f"w={CMEM} l={CMEM} mf=1"
    pkt_size = "" if PHYSICAL_MIM_CAPS else f"w={CPKT} l={CPKT} mf=1"
    mem_instances = "\n".join(
        f"Xmemp{i} outp vcm {mem_cap} {mem_size}\nXmemn{i} outn vcm {mem_cap} {mem_size}"
        for i in range(STATE_BANK_COPIES))
    packet_instances = "\n".join(
        f"Xpktp{i} topp botp {pkt_cap} {pkt_size}\nXpktn{i} topn botn {pkt_cap} {pkt_size}"
        for i in range(PACKET_BANK_COPIES))
    deck = OUT / f"{tag}.cir"
    corner, temp = CORNER, TEMP
    deck.write_text(f'''* Direct differential switched-capacitor MIM state cell, SKY130 {corner.upper()}/{temp}C
.option scale=1u reltol=1e-4 abstol=1e-15 vntol=1e-8 numdgt=15
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "/workspace/asic/analog/modules.spice"
{TG_MODEL_BLOCK}
{cap_includes}
Vdd vdd 0 1.8
Vcm vcm 0 0.9
* Matched storage capacitors retain differential state about VCM.
{mem_instances}
Bdiff diff 0 V=V(outp)-V(outn)
* Matched packet capacitors are precharged to VCM, then top-plate stepped.
{packet_instances}
{STATE_RESET_BLOCK}
Vconn conn 0 {gate_pwl("connect")}
Vconnb connb 0 {gate_pwl("connectb")}
Vreset reset 0 {gate_pwl("reset")}
Vresetb resetb 0 {gate_pwl("resetb")}
Xconp botp outp conn connb vdd 0 {"sky130_pex_tg" if PHYSICAL_TG else "transmission_gate"}
Xconn botn outn conn connb vdd 0 {"sky130_pex_tg" if PHYSICAL_TG else "transmission_gate"}
Xrstp botp vcm reset resetb vdd 0 {"sky130_pex_tg" if PHYSICAL_TG else "transmission_gate"}
Xrstn botn vcm reset resetb vdd 0 {"sky130_pex_tg" if PHYSICAL_TG else "transmission_gate"}
Vtop_p topp 0 {pwi(SEQ,1)}
Vtop_n topn 0 {pwi(SEQ,-1)}
.ic v(outp)=0.9 v(outn)=0.9 v(botp)=0.9 v(botn)=0.9
.temp {temp}
.control
set noaskquit
tran {DT}n 5m uic
meas tran outp_1u find v(outp) at=1u
meas tran outn_1u find v(outn) at=1u
meas tran outp_10u find v(outp) at=10u
meas tran outn_10u find v(outn) at=10u
meas tran outp_100u find v(outp) at=100u
meas tran outn_100u find v(outn) at=100u
meas tran outp_400u find v(outp) at=400u
meas tran outn_400u find v(outn) at=400u
meas tran outp_pre find v(outp) at={max(T1-2.0,3.0):g}u
meas tran outn_pre find v(outn) at={max(T1-2.0,3.0):g}u
meas tran diff_pre find v(diff) at={max(T1-2.0,3.0):g}u
meas tran outp_mid find v(outp) at=2.5m
meas tran outn_mid find v(outn) at=2.5m
meas tran diff_mid find v(diff) at=2.5m
meas tran outp_post find v(outp) at=4.8m
meas tran outn_post find v(outn) at=4.8m
meas tran diff_post find v(diff) at=4.8m
meas tran outp_end find v(outp) at=5m
meas tran outn_end find v(outn) at=5m
meas tran diff_end find v(diff) at=5m
quit
.endc
.end
''', encoding="ascii")
    proc = subprocess.run(
        ["docker", "run", "--rm", "-v", f"{ROOT}:/workspace", "-w",
         "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models", "--entrypoint",
         "ngspice", IMAGE, "-b", f"/workspace/{deck.relative_to(ROOT).as_posix()}"],
        capture_output=True, text=True, timeout=240, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (OUT / f"{tag}.log").write_text(log, encoding="utf-8")
    vals = {k.lower(): float(v) for k, v in re.findall(
        r"(?im)^\s*(outp_1u|outn_1u|outp_10u|outn_10u|outp_100u|outn_100u|outp_400u|outn_400u|outp_pre|outn_pre|outp_mid|outn_mid|outp_post|outn_post|outp_end|outn_end)\s*=\s*([-+0-9.eE]+)", log)}
    direct = {k.lower(): float(v) for k,v in re.findall(
        r"(?im)^\s*(diff_pre|diff_mid|diff_post|diff_end)\s*=\s*([-+0-9.eE]+)", log)}
    if proc.returncode or len(vals) != 16 or len(direct) != 4 or "ngspice-36 done" not in log:
        raise RuntimeError(log[-3000:])
    points = {}
    for t in ("pre", "mid", "post", "end"):
        points[t] = {"outp_v": vals[f"outp_{t}"], "outn_v": vals[f"outn_{t}"],
                     "diff_v": vals[f"outp_{t}"] - vals[f"outn_{t}"],
                     "direct_diff_v": direct[f"diff_{t}"],
                     "cm_v": (vals[f"outp_{t}"] + vals[f"outn_{t}"]) / 2}
    report = {"test": "sky130_direct_differential_mim_packet_screen", "completed": True,
              "sequence": SEQ, "corner": CORNER.upper(), "temperature_c": float(TEMP),
              "membrane_cap_um": float(CMEM), "packet_cap_um": float(CPKT),
              "packet_top_step_v": float(STEP), "event_times_us": [T1, T2], "max_step_ns": float(DT),
              "state_reset_switch_widths_um": {"nfet": 10, "pfet": 20} if not PHYSICAL_TG else {"parallel_extracted_tgs": STATE_RESET_TGS},
              "reset_release": ("NMOS opens at 2.0us; PMOS opens at 2.1us" if not PHYSICAL_TG else
                                f"{STATE_RESET_TGS} parallel extracted TGs open together at 2.0us"),
              "startup_probe_v": {t: {"outp": vals[f"outp_{t}"], "outn": vals[f"outn_{t}"]} for t in ("1u", "10u", "100u", "400u")},
              "measurements": points,
              "expected_single_event_diff_delta_v_ideal_cap_ratio": (2 * float(STEP) * 9.30225e-15 / (21.83739e-12 * STATE_BANK_COPIES + 9.30225e-15)
                  if PHYSICAL_MIM_CAPS else 2 * float(STEP) * (float(CPKT) ** 2 / (float(CMEM) ** 2 + float(CPKT) ** 2))),
              "physical_layout_caps": PHYSICAL_MIM_CAPS,
              "state_bank_layout_copies_per_rail": STATE_BANK_COPIES,
              "packet_cap_layout_copies_per_rail": PACKET_BANK_COPIES,
              "event_pulse_width_us": PULSE_US,
              "calibration_phase": CAL_PHASE,
              "scope": "Two differential state capacitors with equal/opposite switched packet charge through the selected SKY130 TG model; one PVT corner per run over 5ms. When enabled, state and packet caps use individually extracted layout cell subcircuits; top-level interconnect, mismatch, noise, readout, threshold/reset/beta and population service are not included."}
    (OUT / f"{tag}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
