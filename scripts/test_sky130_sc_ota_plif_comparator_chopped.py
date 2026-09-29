"""Test two-phase input chopping to cancel late OTA comparator baseline offset."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import COMMON, RES, BENCH, cell

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    args = sys.argv[1:]
    seq = next((a.split("=", 1)[1] for a in args if a.startswith("--sequence=")), "np")
    max_step = float(next((a.split("=", 1)[1] for a in args if a.startswith("--max-step-ns=")), "100"))
    pre = float(next((a.split("=", 1)[1] for a in args if a.startswith("--precharge-v=")), "0.8845"))
    noise_na_uv = float(next((a.split("=", 1)[1] for a in args if a.startswith("--noise-na-uv=")), "0"))
    noise_nt_ns = float(next((a.split("=", 1)[1] for a in args if a.startswith("--noise-nt-ns=")), "10"))
    seed = int(next((a.split("=", 1)[1] for a in args if a.startswith("--seed=")), "1729"))
    if seq not in ("pp", "nn", "pn", "np") or not 5 <= max_step <= 100:
        raise ValueError("sequence must be pp/nn/pn/np; timestep 5..100ns")
    tag = f"{seq}_s{max_step:g}n" + (f"_trnoise{noise_na_uv:g}uv_nt{noise_nt_ns:g}n_seed{seed}" if noise_na_uv > 0 else "")
    lines = [f"SKY130 TT physical PLIF OTA chopped comparator {tag}", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", f"Vgatecm gatecm 0 {pre:.9f}"]
    lines += cell(f"s_{seq}", 0.90, seq, long_bin=True)
    lines += cell(f"r_{seq}", 0.90, None, long_bin=True)
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
    if noise_na_uv > 0:
        lines.insert(lines.index("Xota cmp_p cmp_n cmpout vbnn vbpp vdd 0 sky130_sc_ota win=0.5 wn3=2 wp3=27.8 cc=100f"),
                     f"Vinput_noise cmp_n_noise cmp_n DC 0 TRNOISE({noise_na_uv:g}u {noise_nt_ns:g}n 0 0)")
        lines.insert(lines.index("Xota cmp_p cmp_n cmpout vbnn vbpp vdd 0 sky130_sc_ota win=0.5 wn3=2 wp3=27.8 cc=100f"),
                     "Rnoise_dc cmp_n_noise 0 1e12")
        lines[lines.index("Xota cmp_p cmp_n cmpout vbnn vbpp vdd 0 sky130_sc_ota win=0.5 wn3=2 wp3=27.8 cc=100f")] = "Xota cmp_p cmp_n_noise cmpout vbnn vbpp vdd 0 sky130_sc_ota win=0.5 wn3=2 wp3=27.8 cc=100f"
    data_name = f"sky130_sc_ota_plif_comparator_chopped_{tag}.dat"
    data = RES / data_name
    lines += [".control", f"setseed {seed}", "set wr_singlescale", "set wr_vecnames", f"tran {max_step:g}n 5.005m uic",
              f"wrdata ../results/{data_name} v(out_s_{seq}) v(out_r_{seq}) v(ref_gate) v(sig_gate) v(cmp_p) v(cmp_n) v(cmpout)", "quit", ".endc", ".end"]
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
    report = {"test": "sky130_tt_physical_membrane_chopped_OTA_comparator", "sequence": seq,
              "max_timestep_ns": max_step, "gate_precharge_v": pre, "simulation_completed": run.returncode == 0 and len(rows)>10,
              "equivalent_input_transient_noise_na_v":noise_na_uv*1e-6,
              "transient_noise_sample_interval_s":noise_nt_ns*1e-9 if noise_na_uv > 0 else None,
              "transient_noise_seed":seed if noise_na_uv > 0 else None,
              "return_code": run.returncode,
              "scope": ("TT schematic; physical MIM pair; same OTA compares the sampled differential in both polarities. TRNOISE is an externally injected equivalent input voltage on one OTA input, calibrated to a separate PDK .noise spectrum; it does not simulate transistor noise internally, and no mismatch/extraction is included." if noise_na_uv > 0 else "TT schematic; physical MIM pair; same OTA compares the sampled differential in both polarities to cancel static output baseline; no mismatch/noise/extraction")}
    if report["simulation_completed"]:
        at=lambda t:min(range(len(rows)),key=lambda i:abs(rows[i][0]-t))
        a,b,c=rows[at(4.89e-3)],rows[at(4.9013e-3)],rows[at(4.9028e-3)]
        d0=a[1]-a[2]; dA=b[1]-b[2]; dB=c[1]-c[2]
        report.update({"state_diff_before_readout_uv":d0*1e6,"state_diff_phaseA_uv":dA*1e6,"state_diff_phaseB_uv":dB*1e6,
                       "state_diff_after_readout_uv":(rows[at(4.9033e-3)][1]-rows[at(4.9033e-3)][2])*1e6,
                       "state_diff_disturbance_uv":(rows[at(4.9033e-3)][1]-rows[at(4.9033e-3)][2]-d0)*1e6,
                       "output_phaseA_v":b[7],"output_phaseB_v":c[7],"chopped_output_delta_mv":(b[7]-c[7])*1e3,
                       "decision_sign_matches_state":((b[7]-c[7])>0)==(dA>0)})
    (RES/f"sky130_sc_ota_plif_comparator_chopped_{tag}.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
