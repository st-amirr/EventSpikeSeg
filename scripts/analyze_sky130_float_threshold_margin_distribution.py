"""Summarize original full-float final-fusion threshold margins in analog voltage units."""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"artifacts/analog_asic"
REF=OUT/"model_reference"
RES=OUT/"results"
VPU=6.521267959225942e-5

def summarize(a: np.ndarray) -> dict:
    a=np.abs(a.astype(np.float64,copy=False)).ravel()
    qs=[0,0.0001,0.001,0.01,0.05,0.1,0.25,0.5,0.9,1]
    values=np.quantile(a,qs)
    return {"count":int(a.size),"absolute_margin_quantiles_percent":{str(q*100):float(v) for q,v in zip(qs,values)},
            "absolute_margin_quantiles_mapped_uv":{str(q*100):float(v*VPU*1e6) for q,v in zip(qs,values)},
            "fraction_below_mapped_uv":{str(limit):float(np.mean(a*VPU*1e6<limit)) for limit in (0.1,0.25,0.5,1,2,5,10,50,100)}}

def main()->int:
    meta=json.loads((REF/"float_patch_trace_all.json").read_text(encoding="utf-8"))
    if meta["qat_or_quantized_reference_used"]: raise RuntimeError("QAT/quantized reference is forbidden")
    z=np.load(REF/"float_patch_trace_all.npz")
    candidate=z["candidate__final_fuse__standard"].astype(np.float32)
    threshold=z["threshold__final_fuse__standard"].astype(np.float32)
    spikes=z["spikes__final_fuse__standard"]>=0.5
    margin=candidate-threshold
    mapped_margin_uv=margin.astype(np.float64)*VPU*1e6
    erfc=np.vectorize(lambda x:0.5*math.erfc(abs(float(x))/math.sqrt(2)),otypes=[float])
    gaussian={}
    for sigma in (0.1,0.25,0.5,1,2,5,10,20):
        flip=erfc(mapped_margin_uv/sigma)
        gaussian[str(sigma)]={"independent_zero_mean_sigma_uv":sigma,"predicted_flip_fraction_all":float(np.mean(flip)),
          "predicted_flip_fraction_float_spikes":float(np.mean(flip[spikes])),"predicted_flip_fraction_float_nonspikes":float(np.mean(flip[~spikes])),
          "scope":"Analytical independent Gaussian decision perturbation on saved float candidates; not a transistor noise simulation or task-level accuracy estimate."}
    # Fit the two signed 5ms SKY130 buffered-readout probes at SS/27C, using
    # the extracted weighted MIM array and coarse/fine code 126/54. The latch
    # threshold is separately bracketed by its measured ±0.25uV decisions;
    # raw output sign is not used as a proxy for latch classification.
    probe_x=np.array([-0.537257883,0.537257883],dtype=np.float64)
    probe_error=np.array([-0.3670985526457165,-0.4718370909215627],dtype=np.float64)
    probe_y=probe_x+probe_error
    probe_gain=float((probe_y[1]-probe_y[0])/(probe_x[1]-probe_x[0]))
    probe_offset=float((probe_y[1]+probe_y[0])*0.5)
    bracket_x=np.array([-0.25,0.25],dtype=np.float64)
    bracket_error=np.array([-0.398663366337341,-0.441410891086602],dtype=np.float64)
    bracket_y=bracket_x+bracket_error
    latch_threshold_uv=float(np.mean(bracket_y))
    residual_threshold_uv=float((latch_threshold_uv-probe_offset)/probe_gain)
    mapped_readout_margin_uv=probe_gain*mapped_margin_uv+probe_offset-latch_threshold_uv
    readout_spikes=mapped_readout_margin_uv>=0
    readout_false_negative=spikes & ~readout_spikes
    readout_false_positive=(~spikes) & readout_spikes
    measured_probe_sensitivity={"process_corner":"SS","temperature_c":27,"bin_end_us":5000,
      "coarse_trim_code":126,"fine_trim_code":54,"probe_input_uv":probe_x.tolist(),
      "measured_input_referred_error_uv":probe_error.tolist(),"fitted_gain":probe_gain,
      "fitted_offset_uv":probe_offset,"threshold_bracket_input_uv":bracket_x.tolist(),
      "threshold_bracket_input_referred_error_uv":bracket_error.tolist(),"inferred_latch_threshold_input_referred_uv":latch_threshold_uv,
      "residual_threshold_in_original_float_mapping_uv":residual_threshold_uv,
      "predicted_wrong_decision_fraction_all":float(np.mean(readout_spikes!=spikes)),
      "predicted_false_negative_fraction_of_float_spikes":float(np.mean(readout_false_negative[spikes])),
      "predicted_false_positive_fraction_of_float_nonspikes":float(np.mean(readout_false_positive[~spikes])),
      "predicted_flip_fraction_of_all_float_spikes":float(np.mean(readout_false_negative)),
      "raw_transfer_zero_crossing_original_margin_uv":float(-probe_offset/probe_gain),
      "scope":"Affine transfer fitted to deterministic SS/27C extracted-MIM/PEX-trim 5ms circuit probes, with the physical latch threshold inferred from separate ±0.25uV 5ms bracket cases at the same trim code, applied to saved original-float final-fusion margins. Sensitivity extrapolation only: no neuron-by-neuron circuit trace, noise, mismatch, routed selector error or task-level validation."}
    report={"test":"original_float_final_fusion_threshold_margin_distribution","checkpoint_sha256":meta["checkpoint_sha256"],
      "qat_or_quantized_reference_used":False,"trace_shape":list(candidate.shape),"volts_per_model_unit":VPU,
      "mapping_scope":"Existing SKY130 fan-in exploratory scale only; these voltage values are an analog sensitivity mapping, not a selected or qualified circuit scale.",
      "all":summarize(margin),"spiking":summarize(margin[spikes]),"nonspiking":summarize(margin[~spikes]),"independent_gaussian_noise_sensitivity":gaussian,
      "measured_ss27_readout_affine_probe_sensitivity":measured_probe_sensitivity,
      "signed_margin_mapped_uv":{"minimum":float(margin.min()*VPU*1e6),"maximum":float(margin.max()*VPU*1e6)},
      "reference_consistency":bool(np.all((margin>=0)==spikes))}
    path=RES/"sky130_float_threshold_margin_distribution.json"
    path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"margin_summary":{k:{"fraction_below_uv":v["fraction_below_mapped_uv"],"q0p1_uv":v["absolute_margin_quantiles_mapped_uv"]["0.1"]} for k,v in (("all",report["all"]),("spiking",report["spiking"]),("nonspiking",report["nonspiking"]))},"measured_ss27_probe_sensitivity":measured_probe_sensitivity},indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
