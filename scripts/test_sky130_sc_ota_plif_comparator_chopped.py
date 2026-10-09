"""Test two-phase input chopping to cancel late OTA comparator baseline offset."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import COMMON, RES, BENCH, cell
from characterize_sky130_sensor_vth_mismatch import PDK_MODEL, make_variant

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    args = sys.argv[1:]
    seq = next((a.split("=", 1)[1] for a in args if a.startswith("--sequence=")), "np")
    max_step = float(next((a.split("=", 1)[1] for a in args if a.startswith("--max-step-ns=")), "100"))
    pre = float(next((a.split("=", 1)[1] for a in args if a.startswith("--precharge-v=")), "0.8845"))
    noise_na_uv = float(next((a.split("=", 1)[1] for a in args if a.startswith("--noise-na-uv=")), "0"))
    noise_nt_ns = float(next((a.split("=", 1)[1] for a in args if a.startswith("--noise-nt-ns=")), "10"))
    offset_uv = float(next((a.split("=", 1)[1] for a in args if a.startswith("--offset-uv=")), "0"))
    trim_uv = float(next((a.split("=", 1)[1] for a in args if a.startswith("--trim-uv=")), "0"))
    isolated_sample = "--isolated-sample" in args
    sample_cap_um = float(next((a.split("=", 1)[1] for a in args if a.startswith("--sample-cap-um=")), "100"))
    phase_us = float(next((a.split("=", 1)[1] for a in args if a.startswith("--phase-us=")), "1"))
    reset_gap_us = float(next((a.split("=", 1)[1] for a in args if a.startswith("--reset-gap-us=")), "1"))
    cmp_cap_pf = float(next((a.split("=", 1)[1] for a in args if a.startswith("--cmp-cap-pf=")), "0"))
    state_diff_uv = next((float(a.split("=", 1)[1]) for a in args if a.startswith("--state-diff-uv=")), None)
    pdk_vth_mismatch = "--pdk-vth-1sigma" in args
    swap_mismatch = "--swap-mismatch" in args
    output_precharge = "--output-precharge" in args
    output_reset_only = "--output-reset-only" in args
    seed = int(next((a.split("=", 1)[1] for a in args if a.startswith("--seed=")), "1729"))
    if seq not in ("pp", "nn", "pn", "np") or not 5 <= max_step <= 100 or not 0.5 <= phase_us <= 45 or not 0.2 <= reset_gap_us <= 10:
        raise ValueError("sequence pp/nn/pn/np; timestep 5..100ns; isolated phase 0.5..45us; reset gap 0.2..10us")
    tag = f"{seq}_s{max_step:g}n" + (f"_d{state_diff_uv:g}uv" if state_diff_uv is not None else "") + (f"_isolated_c{sample_cap_um:g}u" if isolated_sample else "") + (f"_ph{phase_us:g}u" if isolated_sample and phase_us != 1 else "") + (f"_gap{reset_gap_us:g}u" if isolated_sample and output_precharge and reset_gap_us != 1 else "") + (f"_cc{cmp_cap_pf:g}p" if cmp_cap_pf else "") + ("_pdkvth1sigma_swap" if pdk_vth_mismatch and swap_mismatch else ("_pdkvth1sigma" if pdk_vth_mismatch else "")) + ("_opre" if output_precharge else ("_oreset" if output_reset_only else "")) + (f"_off{offset_uv:g}uv" if offset_uv else "") + (f"_trim{trim_uv:g}uv_bal" if trim_uv else "") + (f"_trnoise{noise_na_uv:g}uv_nt{noise_nt_ns:g}n_seed{seed}" if noise_na_uv > 0 else "")
    lines = [f"SKY130 TT physical PLIF OTA chopped comparator {tag}", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", f"Vgatecm gatecm 0 {pre:.9f}"]
    if state_diff_uv is None:
        lines += cell(f"s_{seq}", 0.90, seq, long_bin=True)
        lines += cell(f"r_{seq}", 0.90, None, long_bin=True)
    else:
        lines += cell(f"s_{seq}", 0.90 + state_diff_uv * 0.5e-6, None, long_bin=True)
        lines += cell(f"r_{seq}", 0.90 - state_diff_uv * 0.5e-6, None, long_bin=True)
    if isolated_sample:
        lines += [f"Xsample_sig sig_gate vcm membrane_mim w_um={sample_cap_um:g} l_um={sample_cap_um:g}",
                  f"Xsample_ref ref_gate vcm membrane_mim w_um={sample_cap_um:g} l_um={sample_cap_um:g}"]
    lines += [
        f"Vreset reset 0 PWL(0 1.8 4.8999m 1.8 4.900m 0 4.9031m 0 4.9032m 1.8 5.005m 1.8)",
        f"Vresetb resetb 0 PWL(0 0 4.8999m 0 4.900m 1.8 4.9031m 1.8 4.9032m 0 5.005m 0)",
        f"Vsample sample 0 PWL(0 0 4.8999m 0 4.900m 1.8 4.9031m 1.8 4.9032m 0 5.005m 0)",
        f"Vsampleb sampleb 0 PWL(0 1.8 4.8999m 1.8 4.900m 0 4.9031m 0 4.9032m 1.8 5.005m 1.8)",
        "VselA sela 0 PWL(0 0 4.900m 0 4.9001m 1.8 4.9014m 1.8 4.9015m 0 5.005m 0)",
        "VselAb selab 0 PWL(0 1.8 4.900m 1.8 4.9001m 0 4.9014m 0 4.9015m 1.8 5.005m 1.8)",
        "VselB selb 0 PWL(0 0 4.9014m 0 4.9015m 1.8 4.9029m 1.8 4.903m 0 5.005m 0)",
        "VselBb selbb 0 PWL(0 1.8 4.9014m 1.8 4.9015m 0 4.9029m 0 4.903m 1.8 5.005m 1.8)",
        f"Xgr_{seq} ref_gate gatecm reset resetb vdd 0 transmission_gate",
        f"Xgs_{seq} sig_gate gatecm reset resetb vdd 0 transmission_gate",
        f"Xmr_{seq} out_r_{seq} ref_gate sample sampleb vdd 0 transmission_gate",
        f"Xms_{seq} out_s_{seq} sig_gate sample sampleb vdd 0 transmission_gate",
        "Xpa ref_gate cmp_p sela selab vdd 0 transmission_gate",
        "Xpb sig_gate cmp_p selb selbb vdd 0 transmission_gate",
        "Xna sig_gate cmp_n sela selab vdd 0 transmission_gate",
        "Xnb ref_gate cmp_n selb selbb vdd 0 transmission_gate",
        "Vbn vbnn 0 0.65", "Vbp vbpp 0 0.75", "Rout cmpout vcm 1Meg",
        "Xota cmp_p cmp_n cmpout vbnn vbpp vdd 0 sky130_sc_ota win=0.5 wn3=2 wp3=27.8 cc=100f",
    ]
    if isolated_sample:
        a_on_ms = 4.9004
        a_off_ms = a_on_ms + phase_us / 1000.0
        b_on_ms = a_off_ms + reset_gap_us / 1000.0
        b_off_ms = b_on_ms + phase_us / 1000.0
        a_measure_s = (a_off_ms - 0.0002) * 1e-3
        b_measure_s = (b_off_ms - 0.0002) * 1e-3
        after_measure_s = (b_off_ms + 0.0002) * 1e-3
        def phase_pair(prefix: str, on_ms: float, off_ms: float) -> tuple[str, str]:
            en = f"V{prefix} {prefix.lower()} 0 PWL(0 0 {on_ms-0.0001:.7f}m 0 {on_ms:.7f}m 1.8 {off_ms-0.0001:.7f}m 1.8 {off_ms:.7f}m 0 5.005m 0)"
            inv = f"V{prefix}b {prefix.lower()}b 0 PWL(0 1.8 {on_ms-0.0001:.7f}m 1.8 {on_ms:.7f}m 0 {off_ms-0.0001:.7f}m 0 {off_ms:.7f}m 1.8 5.005m 1.8)"
            return en, inv
        for i, line in enumerate(lines):
            if line.startswith("Vreset reset "):
                lines[i] = "Vreset reset 0 PWL(0 1.8 4.8999m 1.8 4.900m 0 5.005m 0)"
            elif line.startswith("Vresetb resetb "):
                lines[i] = "Vresetb resetb 0 PWL(0 0 4.8999m 0 4.900m 1.8 5.005m 1.8)"
            elif line.startswith("Vsample sample "):
                lines[i] = "Vsample sample 0 PWL(0 0 4.90004m 0 4.90005m 1.8 4.90015m 1.8 4.90016m 0 5.005m 0)"
            elif line.startswith("Vsampleb sampleb "):
                lines[i] = "Vsampleb sampleb 0 PWL(0 1.8 4.90004m 1.8 4.90005m 0 4.90015m 0 4.90016m 1.8 5.005m 1.8)"
            elif line.startswith("VselA sela "):
                lines[i], _ = phase_pair("sela", a_on_ms, a_off_ms)
                lines[i] = lines[i].replace("Vsela sela", "VselA sela")
            elif line.startswith("VselAb selab "):
                _, lines[i] = phase_pair("sela", a_on_ms, a_off_ms)
                lines[i] = lines[i].replace("Vselab selab", "VselAb selab")
            elif line.startswith("VselB selb "):
                lines[i], _ = phase_pair("selb", b_on_ms, b_off_ms)
                lines[i] = lines[i].replace("Vselb selb", "VselB selb")
            elif line.startswith("VselBb selbb "):
                _, lines[i] = phase_pair("selb", b_on_ms, b_off_ms)
                lines[i] = lines[i].replace("Vselbb selbb", "VselBb selbb")
    else:
        a_measure_s, b_measure_s, after_measure_s = 4.9013e-3, 4.9028e-3, 4.9033e-3
    if output_precharge:
        reset2_on = a_off_ms + 0.0001
        reset2_off = b_on_ms - 0.0002
        bias2_on = b_on_ms - 0.0001
        for i, line in enumerate(lines):
            if line == "Vbn vbnn 0 0.65":
                lines[i] = (f"Vbn vbnn 0 PWL(0 0 4.90029m 0 4.90030m 0.65 {reset2_on:.7f}m 0.65 "
                            f"{reset2_on+0.0001:.7f}m 0 {bias2_on:.7f}m 0 {b_on_ms:.7f}m 0.65 5.005m 0.65)")
            elif line == "Vbp vbpp 0 0.75":
                lines[i] = (f"Vbp vbpp 0 PWL(0 1.8 4.90029m 1.8 4.90030m 0.75 {reset2_on:.7f}m 0.75 "
                            f"{reset2_on+0.0001:.7f}m 1.8 {bias2_on:.7f}m 1.8 {b_on_ms:.7f}m 0.75 5.005m 0.75)")
        reset_on_a = a_off_ms + 0.0003
        reset_off_b = b_off_ms + 0.0001
        reset_pwl = (f"PWL(0 1.8 4.90029m 1.8 4.90030m 0 {reset_on_a:.7f}m 0 "
                     f"{b_on_ms-0.0001:.7f}m 1.8 {b_on_ms:.7f}m 0 "
                     f"{b_off_ms:.7f}m 0 {reset_off_b:.7f}m 1.8 5.005m 1.8)")
        resetb_pwl = (f"PWL(0 0 4.90029m 0 4.90030m 1.8 {reset_on_a:.7f}m 1.8 "
                      f"{b_on_ms-0.0001:.7f}m 0 {b_on_ms:.7f}m 1.8 "
                      f"{b_off_ms:.7f}m 1.8 {reset_off_b:.7f}m 0 5.005m 0)")
        lines += [f"Vcmpreset compreset 0 {reset_pwl}",
                  f"Vcmpresetb compresetb 0 {resetb_pwl}",
                  "Xcmpout_reset cmpout vcm compreset compresetb vdd 0 transmission_gate",
                  "Xcmpp_reset cmp_p gatecm compreset compresetb vdd 0 transmission_gate",
                  "Xcmpn_reset cmp_n gatecm compreset compresetb vdd 0 transmission_gate"]
    elif output_reset_only and isolated_sample:
        reset_start_gap = a_off_ms + 0.0001
        reset_end_gap = b_on_ms - 0.0001
        out_reset_pwl = (f"PWL(0 1.8 4.90029m 1.8 4.90030m 0 {reset_start_gap:.7f}m 0 "
                         f"{reset_start_gap+0.0001:.7f}m 1.8 {reset_end_gap:.7f}m 1.8 "
                         f"{b_on_ms:.7f}m 0 {b_off_ms:.7f}m 0 {b_off_ms+0.0001:.7f}m 1.8 5.005m 1.8)")
        out_resetb_pwl = (f"PWL(0 0 4.90029m 0 4.90030m 1.8 {reset_start_gap:.7f}m 1.8 "
                          f"{reset_start_gap+0.0001:.7f}m 0 {reset_end_gap:.7f}m 0 "
                          f"{b_on_ms:.7f}m 1.8 {b_off_ms:.7f}m 1.8 {b_off_ms+0.0001:.7f}m 0 5.005m 0)")
        lines += [f"Voutreset outreset 0 {out_reset_pwl}", f"Voutresetb outresetb 0 {out_resetb_pwl}",
                  "Xcmpout_reset cmpout vcm outreset outresetb vdd 0 transmission_gate"]
    if cmp_cap_pf > 0:
        lines += [f"Ccmp_p cmp_p vcm {cmp_cap_pf:g}p", f"Ccmp_n cmp_n vcm {cmp_cap_pf:g}p"]
    applied_offset_uv = offset_uv
    if noise_na_uv > 0 or applied_offset_uv != 0:
        noise_source = (f"Vinput_noise cmp_n_noise cmp_n DC {applied_offset_uv:g}u TRNOISE({noise_na_uv:g}u {noise_nt_ns:g}n 0 0)"
                        if noise_na_uv > 0 else f"Vinput_offset cmp_n_noise cmp_n DC {applied_offset_uv:g}u")
        lines.insert(lines.index("Xota cmp_p cmp_n cmpout vbnn vbpp vdd 0 sky130_sc_ota win=0.5 wn3=2 wp3=27.8 cc=100f"),
                     noise_source)
        lines.insert(lines.index("Xota cmp_p cmp_n cmpout vbnn vbpp vdd 0 sky130_sc_ota win=0.5 wn3=2 wp3=27.8 cc=100f"),
                     "Rnoise_dc cmp_n_noise 0 1e12")
        lines[lines.index("Xota cmp_p cmp_n cmpout vbnn vbpp vdd 0 sky130_sc_ota win=0.5 wn3=2 wp3=27.8 cc=100f")] = "Xota cmp_p cmp_n_noise cmpout vbnn vbpp vdd 0 sky130_sc_ota win=0.5 wn3=2 wp3=27.8 cc=100f"
    if trim_uv != 0:
        for i, line in enumerate(lines):
            if line.startswith("Xota "):
                parts = line.split()
                original_p, original_n = parts[1], parts[2]
                parts[1:3] = ["cmp_p_trim", "cmp_n_trim"]
                lines[i] = " ".join(parts)
                lines += [f"Vtrim_p cmp_p_trim {original_p} DC {trim_uv*0.5:g}u",
                          f"Vtrim_n cmp_n_trim {original_n} DC {-trim_uv*0.5:g}u"]
                break
    if pdk_vth_mismatch:
        BENCH.mkdir(parents=True, exist_ok=True)
        model_source = PDK_MODEL.read_text(encoding="ascii")
        plus = make_variant(model_source, "plus", -1 if swap_mismatch else 1)
        minus = make_variant(model_source, "minus", 1 if swap_mismatch else -1)
        (BENCH / "nfet_vthsigma_plus.spice").write_text(plus, encoding="ascii")
        (BENCH / "nfet_vthsigma_minus.spice").write_text(minus, encoding="ascii")
        lines += [".include \"diff_sensor_probe/nfet_vthsigma_plus.spice\"",
                  ".include \"diff_sensor_probe/nfet_vthsigma_minus.spice\"",
                  ".subckt sky130_sc_ota_vthsigma inp inn out vbiasn vbiasp vdd vss",
                  "+ params: win=10 wload=20 wtail=4 wn3=20 wp3=20 cc=500f",
                  "Xn1 n1 inp ntail vss nfet_vthsigma_plus w={win} l=1",
                  "Xn2 n2 inn ntail vss nfet_vthsigma_minus w={win} l=1",
                  "Xntail ntail vbiasn vss vss sky130_fd_pr__nfet_01v8 w={wtail} l=2",
                  "Xp1 n1 n1 vdd vdd sky130_fd_pr__pfet_01v8 w={wload} l=1",
                  "Xp2 n2 n1 vdd vdd sky130_fd_pr__pfet_01v8 w={wload} l=1",
                  "Xn3 out n2 vss vss sky130_fd_pr__nfet_01v8 w={wn3} l=0.5",
                  "Xp3 out vbiasp vdd vdd sky130_fd_pr__pfet_01v8 w={wp3} l=0.5",
                  "Ccomp n2 out {cc}", ".ends sky130_sc_ota_vthsigma"]
        for i, line in enumerate(lines):
            if line.startswith("Xota "):
                lines[i] = line.replace("sky130_sc_ota ", "sky130_sc_ota_vthsigma ")
                break
    data_name = f"sky130_sc_ota_plif_comparator_chopped_{tag}.dat"
    data = RES / data_name
    vectors = [f"v(out_s_{seq})", f"v(out_r_{seq})", "v(ref_gate)", "v(sig_gate)",
               "v(cmp_p)", "v(cmp_n)", "v(cmpout)"]
    if trim_uv != 0:
        vectors += ["v(cmp_p_trim)", "v(cmp_n_trim)"]
    lines += [".control", f"setseed {seed}", "set wr_singlescale", "set wr_vecnames", f"tran {max_step:g}n 5.005m uic",
              f"wrdata ../results/{data_name} " + " ".join(vectors), "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_ota_plif_comparator_chopped_{tag}.cir"
    deck.write_text("\n".join(lines)+"\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{ROOT / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic", "--workdir",
           "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "180", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=195)
    (RES / f"sky130_sc_ota_plif_comparator_chopped_{tag}.log").write_text(run.stdout+run.stderr, encoding="utf-8")
    rows = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(v) for v in line.split()])
            except ValueError:
                continue
    if isolated_sample:
        scope = f"TT schematic; {sample_cap_um:g}um MIM temporary sample caps isolate the membrane before two-phase OTA comparison; "
        scope += ("PDK-based deterministic ±1σ input NFET Vth realization; ideal balanced differential trim is applied at the OTA inputs after phase selection." if pdk_vth_mismatch and trim_uv else ("PDK-based deterministic ±1σ input NFET Vth realization." if pdk_vth_mismatch else ("ideal balanced differential trim is applied at the OTA inputs after phase selection." if trim_uv else ("deterministic OTA-pin offset stress, not transistor mismatch." if applied_offset_uv else "no mismatch/noise/extraction."))))
    elif noise_na_uv > 0:
        scope = "TT schematic; physical MIM pair; TRNOISE is externally injected equivalent input voltage calibrated to a separate PDK .noise spectrum; it does not simulate transistor noise internally; no mismatch/extraction."
    elif applied_offset_uv != 0:
        scope = "TT schematic; physical MIM pair; deterministic DC offset/trim source in series with one OTA input; stress probe, not transistor mismatch; no extraction."
    else:
        scope = "TT schematic; physical MIM pair; same OTA compares the sampled differential in both polarities to cancel static output baseline; no mismatch/noise/extraction."
    report = {"test": "sky130_tt_physical_membrane_chopped_OTA_comparator", "sequence": seq,
              "max_timestep_ns": max_step, "gate_precharge_v": pre, "simulation_completed": run.returncode == 0 and len(rows)>10,
              "injected_comparator_input_offset_uv": offset_uv,
              "ideal_post_switch_differential_trim_uv": trim_uv,
              "applied_comparator_input_dc_uv": applied_offset_uv,
              "programmed_state_diff_uv": state_diff_uv,
              "pdk_input_vth_mismatch_1sigma": pdk_vth_mismatch,
              "pdk_mismatch_swapped": swap_mismatch if pdk_vth_mismatch else None,
              "equivalent_input_transient_noise_na_v":noise_na_uv*1e-6,
              "transient_noise_sample_interval_s":noise_nt_ns*1e-9 if noise_na_uv > 0 else None,
              "transient_noise_seed":seed if noise_na_uv > 0 else None,
              "return_code": run.returncode,
              "isolated_sample": isolated_sample,
              "sample_cap_um": sample_cap_um if isolated_sample else None,
              "comparison_phase_duration_us": phase_us if isolated_sample else None,
              "output_precharge": output_precharge,
              "output_reset_only": output_reset_only,
              "comparator_input_capacitance_pf_per_leg": cmp_cap_pf,
              "scope": scope}
    if report["simulation_completed"]:
        at=lambda t:min(range(len(rows)),key=lambda i:abs(rows[i][0]-t))
        a,sample,b,c=rows[at(4.89e-3)],rows[at(4.90016e-3)],rows[at(a_measure_s)],rows[at(b_measure_s)]
        d0=a[1]-a[2]; dA=b[1]-b[2]; dB=c[1]-c[2]
        cmp_p_idx, cmp_n_idx = (8, 9) if trim_uv != 0 else (5, 6)
        report.update({"state_diff_before_readout_uv":d0*1e6,"state_diff_phaseA_uv":dA*1e6,"state_diff_phaseB_uv":dB*1e6,
                       "sampled_gate_diff_uv":(sample[4]-sample[3])*1e6,
                       "ota_input_diff_phaseA_uv":(b[cmp_p_idx]-b[cmp_n_idx])*1e6,
                       "ota_input_diff_phaseB_uv":(c[cmp_p_idx]-c[cmp_n_idx])*1e6,
                       "raw_mux_input_diff_phaseA_uv":(b[5]-b[6])*1e6,
                       "raw_mux_input_diff_phaseB_uv":(c[5]-c[6])*1e6,
                       "state_diff_after_readout_uv":(rows[at(after_measure_s)][1]-rows[at(after_measure_s)][2])*1e6,
                       "state_diff_disturbance_uv":(rows[at(after_measure_s)][1]-rows[at(after_measure_s)][2]-d0)*1e6,
                       "output_phaseA_v":b[7],"output_phaseB_v":c[7],"chopped_output_delta_mv":(b[7]-c[7])*1e3,
                       "decision_sign_matches_state":((b[7]-c[7])>0)==(dA>0)})
    (RES/f"sky130_sc_ota_plif_comparator_chopped_{tag}.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
