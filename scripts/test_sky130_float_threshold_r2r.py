"""Test full-float-derived microvolt thresholds through the transistor R-2R DAC."""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import numpy as np

from test_sky130_sc_physical_accumulation import COMMON, RES, BENCH

ROOT = Path(__file__).resolve().parents[1]
N = 1 << 24
VCM = 0.9
VSPAN = 0.05
HEADROOM = 0.30
TRACE = ROOT / "artifacts/analog_asic/model_reference/float_patch_trace.npz"


def run_codes(codes: list[int], name: str) -> tuple[int, list[float], str]:
    slot_us = 20
    stop_us = slot_us * len(codes) + 5
    lines = [f"SKY130 float threshold DAC calibration {name}", COMMON,
             '.include "../../../asic/analog/sky130_ms_r2r24.spice"',
             "Vdd vdd 0 1.8", f"Vhi vhi 0 {VCM+VSPAN:.12f}", f"Vlo vlo 0 {VCM:.12f}",
             "Rload out vcm 1Meg", f"Vcm vcm 0 {VCM:.12f}"]
    for bit in range(24):
        points = [f"0 {((codes[0] >> bit) & 1)*1.8:g}"]
        for j in range(1, len(codes)):
            t = j * slot_us
            points += [f"{t}u {((codes[j-1] >> bit) & 1)*1.8:g}",
                       f"{t}.001u {((codes[j] >> bit) & 1)*1.8:g}"]
        points.append(f"{stop_us}u {((codes[-1] >> bit) & 1)*1.8:g}")
        lines.append(f"Vb{bit} b{bit} 0 PWL(" + " ".join(points) + ")")
    pins = " ".join(f"b{i}" for i in range(23, -1, -1))
    data_name = f"sky130_float_threshold_r2r_{name}.dat"
    lines += [f"Xdac out {pins} vhi vlo vdd 0 r2r_dac_u24", ".control",
              "set wr_singlescale", "set wr_vecnames", f"tran 20n {stop_us}u",
              f"wrdata ../results/{data_name} v(out)", "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_float_threshold_r2r_{name}.cir"
    data = RES / data_name
    deck.write_text("\n".join(lines)+"\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{ROOT/'artifacts/analog_asic'}:/workspace/artifacts/analog_asic", "--workdir",
           "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=75)
    (RES/f"sky130_float_threshold_r2r_{name}.log").write_text(run.stdout+run.stderr, encoding="utf-8")
    rows=[]
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try: rows.append([float(x) for x in line.split()])
            except ValueError: pass
    values=[]
    if rows:
        for j in range(len(codes)):
            t=(10+slot_us*j)*1e-6
            values.append(min(rows,key=lambda x:abs(x[0]-t))[1]-VCM)
    return run.returncode if len(values)==len(codes) else 1, values, run.stdout+run.stderr


def main() -> int:
    archive = np.load(TRACE)
    stage = "final_fuse__standard"
    threshold = archive[f"threshold__{stage}"].astype(np.float64)
    candidate = archive[f"candidate__{stage}"].astype(np.float64)
    candidate_absmax = float(np.max(np.abs(candidate)))
    targets = [float(np.min(threshold)) / candidate_absmax * HEADROOM,
               float(np.median(threshold)) / candidate_absmax * HEADROOM,
               float(np.max(threshold)) / candidate_absmax * HEADROOM]
    cal_codes=[0,1024,2048,3072,4096,5120,6144]
    rc_cal, cal_values, _ = run_codes(cal_codes,"cal")
    slope, intercept = np.polyfit(np.asarray(cal_codes,dtype=float),np.asarray(cal_values,dtype=float),1)
    predicted_codes=[max(0,min(N-1,round((v-intercept)/slope))) for v in targets]
    search_codes=sorted({max(0,min(N-1,pred+step)) for pred in predicted_codes for step in range(-256,257,16)})
    rc_search, search_values, _ = run_codes(search_codes,"search")
    corrected_codes=[]
    selected_search=[]
    for target in targets:
        index=min(range(len(search_codes)),key=lambda i:abs(search_values[i]-target))
        corrected_codes.append(search_codes[index])
        selected_search.append({"code":search_codes[index],"predicted_output_uv":search_values[index]*1e6,
                                "prevalidation_error_uv":(search_values[index]-target)*1e6})
    rc_val, measured_values, log = run_codes(corrected_codes,"validate")
    (RES/"sky130_float_threshold_r2r.log").write_text(log,encoding="utf-8")
    report={"test":"sky130_float_threshold_r2r24_transistor_switch_screen","simulation_completed":rc_cal==0 and rc_search==0 and rc_val==0,
            "return_code":max(rc_cal,rc_search,rc_val),"float_checkpoint":"best_validation_epoch58_seed17","qat_or_quantized_model_used":False,
            "stage":stage,"candidate_headroom_v":HEADROOM,"candidate_absmax_model_units":candidate_absmax,
            "threshold_model_value_range":[float(np.min(threshold)),float(np.median(threshold)),float(np.max(threshold))],
            "dac_rails_v":{"vlo":VCM,"vhi":VCM+VSPAN},"calibration_codes":cal_codes,
            "calibration_offsets_uv":[v*1e6 for v in cal_values],
            "fitted_transfer":{"offset_uv":intercept*1e6,"slope_nv_per_code":slope*1e9,"ideal_slope_nv_per_code":VSPAN/N*1e9},
            "local_search_candidate_count":len(search_codes),"local_search_selected_codes":selected_search,
            "scope":"ideal digital bit controls, PDK nfet/pfet transmission-gate switches and ideal 1k/2k R-2R resistors; global affine trim only; no resistor mismatch, parasitic extraction, noise, or membrane load"}
    if report["simulation_completed"]:
        result=[]
        for target,code,measured in zip(targets,corrected_codes,measured_values):
            result.append({"threshold_offset_target_uv":target*1e6,"calibrated_u24_configuration_code":code,
                           "measured_offset_uv":measured*1e6,"error_uv":(measured-target)*1e6})
        report["codes_and_transfer"]=result
        report["max_abs_error_uv"]=max(abs(x["error_uv"]) for x in result)
    (RES/"sky130_float_threshold_r2r.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__=="__main__":
    raise SystemExit(main())
