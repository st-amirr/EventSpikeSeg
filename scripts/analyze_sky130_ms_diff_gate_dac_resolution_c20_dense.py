"""Map full-float final-fusion weights through measured MOS gate-amplitude pulses."""
from __future__ import annotations
import json,runpy
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; REF=ROOT/'artifacts/analog_asic/model_reference'; RES=ROOT/'artifacts/analog_asic/results'
CAL=RES/'sky130_ms_diff_gate_amplitude_c20_w10.5n_pg0.72_ng0.6_wp1.5_wn1_l10_d0v_cm0.9v_t200u_n46_fr0.1-1_h1b6c16181e_step2n.json'; CAL_FINE=CAL
TRACE=REF/'float_patch_trace_all.json'; PARAM=REF/'eventspikeseg140k_float_parameters.npz'
def main():
  m=runpy.run_path(str(ROOT/'scripts/analyze_sky130_passive_float_mapping.py')); conv2d=m['conv2d']; replay=m['replay']
  calib=json.loads(CAL.read_text()); fine=json.loads(CAL_FINE.read_text()); merged={float(p['gate_magnitude_fraction']):p for p in calib['event_transfer_by_gate_magnitude'] if p['polarity']=='p' and float(p['gate_magnitude_fraction'])>0}; merged.update({float(p['gate_magnitude_fraction']):p for p in fine['event_transfer_by_gate_magnitude'] if p['polarity']=='p' and float(p['gate_magnitude_fraction'])>0}); by_sign={(float(p['gate_magnitude_fraction']),p['polarity']):p for p in calib['event_transfer_by_gate_magnitude']}; by_sign.update({(float(p['gate_magnitude_fraction']),p['polarity']):p for p in fine['event_transfer_by_gate_magnitude']}); calib['event_transfer_by_gate_magnitude']=[q for f in sorted(merged) for q in [by_sign[(f,'p')],by_sign[(f,'n')]]]; trace=json.loads(TRACE.read_text()); arrays=np.load(REF/trace['trace_archive']); params=np.load(PARAM)
  row=next(r for r in trace['sampled_stages'] if r['name']=='final_fuse.standard'); convmeta=json.loads((REF/'eventspikeseg140k_float_reference.json').read_text()); ci=next(r for r in convmeta['effective_folded_weight_and_neuron_parameters'] if r['name']=='final_fuse.standard')
  w=params['weight__final_fuse__standard'].astype(np.float32); x=arrays['presynaptic_input__final_fuse__standard'].astype(np.float32); cand=arrays['candidate__final_fuse__standard'].astype(np.float32); thr=arrays['threshold__final_fuse__standard'].astype(np.float32); refmem=arrays['membrane__final_fuse__standard'].astype(np.float32); refsp=arrays['spikes__final_fuse__standard'].astype(bool); refcur=arrays['current__final_fuse__standard'].astype(np.float32); beta=params['beta__final_fuse__standard'].astype(np.float32).reshape(1,-1,1,1)
  candidate=row['candidate_before_threshold_and_reset']; cmax=max(abs(float(candidate['min'])),abs(float(candidate['max'])))
  # The measured final differential response at each gate magnitude is used
  # directly. The monotonic common curve is the mean of mirrored p and n.
  pts=calib['event_transfer_by_gate_magnitude']; fractions=sorted({float(p['gate_magnitude_fraction']) for p in pts if p['polarity']=='p' and float(p['gate_magnitude_fraction'])>0})
  deltas=[]
  for f in fractions:
    p=next(p for p in pts if p['polarity']=='p' and float(p['gate_magnitude_fraction'])==f)
    n=next(p for p in pts if p['polarity']=='n' and float(p['gate_magnitude_fraction'])==f)
    deltas.append((abs(float(p['final_differential_change_mv']))+abs(float(n['final_differential_change_mv'])))*0.5e-3)
  curve=np.maximum.accumulate(np.asarray(deltas,dtype=np.float64))
  nonzero=np.flatnonzero(curve>0)
  floor=float(curve[nonzero[0]]) if len(nonzero) else float('inf')
  maxdelta=float(curve[-1]); curve_x=np.r_[0.,curve[nonzero]]; curve_f=np.r_[0.,np.asarray(fractions)[nonzero]]
  curve_x,idx=np.unique(curve_x,return_index=True); curve_f=curve_f[idx]
  inputs=x; headrooms=[float(z) for z in _arg('--headrooms','0.15,0.30,0.60').split(',')]
  screens=[]
  for h in headrooms:
    vpu=h/cmax; req=np.abs(w)*vpu; represented=(req>=floor); realized=np.where(represented,np.minimum(req,maxdelta),0.0)
    widths_frac=np.interp(realized,curve_x,curve_f)
    dac_screens=[]
    for bits in (6,8,10,12,14):
      levels=(1<<bits)-1; fcode=np.rint(widths_frac*levels)/levels; qdelta=np.interp(fcode,np.asarray(fractions),curve[nonzero] if False else np.asarray(deltas)); qdelta=np.where(req<floor,0.0,qdelta); qweight=np.sign(w)*(qdelta/vpu); qcurrent=conv2d(inputs,qweight.astype(np.float32),cand.shape[-2:],groups=ci['conv_groups'],dilation=tuple(ci['conv_dilation']),padding=tuple(ci['conv_padding'])).reshape(cand.shape); qspikes,_=replay(qcurrent,beta,thr); dac_screens.append({'gate_control_bits':bits,'gate_fraction_lsb':1.0/levels,'spike_mismatch_fraction_vs_full_float':float(np.mean(qspikes!=refsp)),'current_error_abs_model_units_p50_p90_p99':[float(v) for v in np.quantile(np.abs(qcurrent-refcur),[.5,.9,.99])]})
    mapped=np.sign(w)*(realized/vpu)
    current=conv2d(inputs,mapped.astype(np.float32),cand.shape[-2:],groups=ci['conv_groups'],dilation=tuple(ci['conv_dilation']),padding=tuple(ci['conv_padding'])).reshape(cand.shape)
    spikes,state=replay(current,beta,thr)
    base_sp,base_state=replay(refcur,beta,thr)
    current_err=np.abs(current-refcur); state_err=np.abs(state-refmem)
    active=conv2d(inputs,np.ones_like(w),cand.shape[-2:],groups=ci['conv_groups'],dilation=tuple(ci['conv_dilation']),padding=tuple(ci['conv_padding'])).ravel(); active=active[active>0]
    screens.append({'candidate_headroom_v':h,'volts_per_model_unit':vpu,'minimum_measured_nonzero_event_delta_v':floor,'maximum_measured_event_delta_v':maxdelta,'fraction_static_weights_below_measured_transfer_floor':float(np.mean(req<floor)),'fraction_static_weights_above_measured_transfer_range':float(np.mean(req>maxdelta)),'required_gate_fraction_quantiles_p0p1_p1_p50_p99_max':[float(v) for v in np.quantile(widths_frac,[.001,.01,.5,.99,1])],'baseline_full_float_current_replay_mismatch_fraction':float(np.mean(base_sp!=refsp)),'spike_mismatch_fraction_vs_full_float_trace':float(np.mean(spikes!=refsp)),'spike_rate_full_float_vs_mapped':[float(refsp.mean()),float(spikes.mean())],'mapped_current_error_abs_model_units_p50_p90_p99':[float(v) for v in np.quantile(current_err,[.5,.9,.99])],'mapped_postreset_state_error_uv_p50_p90_p99_max':[float(v*1e6) for v in (np.quantile(state_err,[.5,.9,.99]).tolist()+[float(state_err.max())])],'active_fanin_p50_p90_p99_max':[float(v) for v in np.percentile(active,[50,90,99,100])],'gate_control_resolution_screens':dac_screens,'scope':'Ideal additive replay of the measured single-event gate-amplitude curve on the frozen final-fusion full-float inputs; omitted sub-floor and over-range weights are reported. Uses one threshold/reset per 5ms bin. No multi-event state nonlinearity, gate-DAC error/noise, peer feedback, task accuracy, PVT, mismatch, extraction, or physical weight storage.'})
  out={'test':'sky130_tt_direct_differential_mos_gate_amplitude_full_float_mapping_sensitivity','checkpoint_sha256':trace['checkpoint_sha256'],'checkpoint_epoch':trace['checkpoint_epoch'],'qat_or_quantized_reference_used':False,'calibration':{'source':[str(CAL.relative_to(ROOT)),str(CAL_FINE.relative_to(ROOT))], 'direct_differential_measurement':True,'membrane_cap_square_um':20,'pulse_width_ns':calib['pulse_width_ns'],'p_gate_full_v':calib['p_gate_full_magnitude_v'],'n_gate_full_v':calib['n_gate_full_magnitude_v'],'transfer_curve_gate_fraction':fractions,'measured_abs_differential_delta_v':deltas,'smallest_measured_nonzero_delta_v':floor,'scope':calib['scope']},'final_fuse_candidate_abs_max_model_units':cmax,'screens':screens,'scope':'Local replay of final_fuse.standard on three frozen 64x64 DSEC patches from the best full-float checkpoint. Weight magnitude is mapped to the measured fixed-width differential current-pulse gate-amplitude curve; no QAT or quantized weights. Multi-event transfer is only supported by separate equal-charge screens (100 events 7.1% low; 316/370 events within 2.7/1.1%), not by this per-weight replay. No complete network, readout/threshold kick, analog weight storage, gate DAC precision, PVT, mismatch, noise, extraction or task accuracy.'}
  dest=RES/'sky130_ms_diff_gate_dac_resolution_c20_dense_float_screen.json'; dest.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'output':str(dest),'screens':screens},indent=2)); return 0
def _arg(k,d):
 import sys
 return next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith(k+'=')),d)
if __name__=='__main__': raise SystemExit(main())

