"""Full-float replay through an idealized passive SC charge-sharing recurrence.

The single-event p/n coupling factors are anchored to one TT schematic test
(20um membrane, 2um packet, +/-50mV top-plate step). This evaluates state and
order nonlinearity for real final_fuse events; it does not model switch noise,
DAC error, readout, extraction or the full closed-loop network.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/'artifacts/analog_asic/model_reference'
RES=ROOT/'artifacts/analog_asic/results'
TRACE=REF/'float_patch_trace_all.json'
PARAM=REF/'eventspikeseg140k_float_parameters.npz'
ALPHA_P=0.438597179798661e-3/0.05
ALPHA_N=0.4898763560512442e-3/0.05

def main():
    meta=json.loads(TRACE.read_text()); arrays=np.load(REF/meta['trace_archive']); params=np.load(PARAM)
    p_name='weight__final_fuse__standard'; x=arrays['presynaptic_input__final_fuse__standard'].astype(np.float32)
    w=params[p_name].astype(np.float32); ref_current=arrays['current__final_fuse__standard'].astype(np.float32)
    ref_mem=arrays['membrane__final_fuse__standard'].astype(np.float32); ref_spike=arrays['spikes__final_fuse__standard'].astype(bool)
    thr=arrays['threshold__final_fuse__standard'].astype(np.float32)
    beta=params['beta__final_fuse__standard'].astype(np.float32).reshape(1,-1,1,1)
    # Three captured 64x64 patches are packed into the presynaptic trace axis.
    x=x.reshape(ref_mem.shape[0],ref_mem.shape[1],*x.shape[1:])
    cand_meta=next(r for r in meta['sampled_stages'] if r['name']=='final_fuse.standard')['candidate_before_threshold_and_reset']
    cand_max=max(abs(float(cand_meta['min'])),abs(float(cand_meta['max'])))
    weight_abs=np.abs(w)
    headrooms=[float(s) for s in _arg('--headrooms','0.15,0.30,0.60').split(',')]
    max_top=float(_arg('--max-top-step-v','0.30'))
    orders=_arg('--orders','forward,reverse').split(',')
    rows=[]
    for headroom in headrooms:
      vpu=headroom/cand_max
      requested_top=np.empty_like(w,dtype=np.float32)
      pos=w>=0
      requested_top[pos]=w[pos]*vpu/ALPHA_P
      requested_top[~pos]=w[~pos]*vpu/ALPHA_N
      clipped=np.clip(requested_top,-max_top,max_top)
      requested_dv=np.abs(w)*vpu
      delivered_initial=np.where(pos,ALPHA_P,ALPHA_N)*np.abs(clipped)
      weight_rows={
        'candidate_headroom_v':headroom,
        'volts_per_model_unit':vpu,
        'fraction_static_weights_exceeding_topplate_range':float(np.mean(np.abs(requested_top)>max_top)),
        'requested_topplate_step_abs_quantiles_v_p0p1_p1_p50_p99_max':[float(v) for v in np.quantile(np.abs(requested_top),[.001,.01,.5,.99,1])],
        'fraction_static_weights_with_over_10pct_initial_event_gain_error':float(np.mean(np.abs(delivered_initial-requested_dv)>0.1*np.maximum(requested_dv,1e-15))),
        'event_charge_coupling_factors_p_n':[ALPHA_P,ALPHA_N],
        'orders':[]}
      for order in orders:
        if order not in ('forward','reverse'):
          raise ValueError('orders must be forward and/or reverse')
        state=np.zeros((ref_mem.shape[1],w.shape[0],ref_mem.shape[-2],ref_mem.shape[-1]),dtype=np.float32)
        state_traces=[]; spike_traces=[]
        cin=w.shape[1]; kh,kw=w.shape[2:]
        ph,pw=kh//2,kw//2
        for ti in range(x.shape[0]):
          state*=beta.reshape(1,-1,1,1)
          xi=np.pad(x[ti],((0,0),(0,0),(ph,ph),(pw,pw)))
          taps=[(ci,iy,ix) for ci in range(cin) for iy in range(kh) for ix in range(kw)]
          if order=='reverse': taps.reverse()
          for ci,iy,ix in taps:
            counts=xi[:,ci,iy:iy+state.shape[-2],ix:ix+state.shape[-1]]
            if not np.any(counts): continue
            for co in range(w.shape[0]):
              coeff=w[co,ci,iy,ix]
              if coeff==0: continue
              alpha=ALPHA_P if coeff>=0 else ALPHA_N
              target=clipped[co,ci,iy,ix]
              decay=np.power(1.0-alpha,counts,dtype=np.float32)
              state[:,co]=target+(state[:,co]-target)*decay
          proposal=state.copy()
          thr_v=thr[ti]*vpu
          fired=proposal>=thr_v
          state=proposal-fired.astype(np.float32)*thr_v
          state_traces.append(state.copy()); spike_traces.append(fired)
        state_arr=np.stack(state_traces); spike_arr=np.stack(spike_traces)
        state_err=np.abs(state_arr-ref_mem*vpu)
        row={
          'event_order':order,
          'spike_mismatch_fraction_vs_full_float_trace':float(np.mean(spike_arr!=ref_spike)),
          'spike_rate_full_float_vs_sc_replay':[float(ref_spike.mean()),float(spike_arr.mean())],
          'postreset_state_error_uv_p50_p90_p99_max':[float(v*1e6) for v in (np.quantile(state_err,[.5,.9,.99]).tolist()+[float(state_err.max())])],
          'candidate_to_threshold_abs_margin_model_units_p0p1_p1':[float(v) for v in next(r for r in meta['sampled_stages'] if r['name']=='final_fuse.standard')['candidate_minus_threshold_margin_model_units']['abs_percentiles_0p1_1_10_50_90'][:2]],
          'baseline_reference_float_spike_replay_mismatch_fraction':float(np.mean(ref_spike!=arrays['spikes__final_fuse__standard'].astype(bool))),
          'estimated_serial_action_time_us_p50_p90_p99_max_at_2p5us':[float(v*2.5) for v in np.percentile(_fanin_counts(x,w),[50,90,99,100])],
          'full_float_current_abs_error_model_units_p50_p90_p99':[float(v) for v in np.quantile(np.abs(state_arr/vpu-ref_mem),[.5,.9,.99])],
          'scope':'Ideal capacitor charge-sharing recurrence, event amplitude proportional to full-float weight, one threshold and subtractive reset per bin. Frozen presynaptic spikes. No weight-DAC error/noise, switch injection, readout, PVT, mismatch, extraction, or peer feedback.'}
        weight_rows['orders'].append(row)
      rows.append(weight_rows)
    out={'test':'sky130_passive_sc_cap_sharing_full_float_final_fuse_sensitivity','checkpoint_sha256':meta['checkpoint_sha256'],'checkpoint_epoch':meta['checkpoint_epoch'],'qat_or_quantized_reference_used':False,
      'physical_transfer_anchor':{'membrane_cap_square_um':20,'packet_cap_square_um':2,'topplate_abs_step_v':0.05,'measured_single_event_state_change_v_p':0.438597179798661e-3,'measured_single_event_state_change_v_n':-0.4898763560512442e-3,'event_source_reports':['sky130_sc_physical_chopped_readout_pp_abba_rf3078_cm20_cp2_events1p_directread_ros1_s50n_matchota.json','sky130_sc_physical_chopped_readout_pp_abba_rf3078_cm20_cp2_events1n_directread_ros1_s50n_matchota.json']},
      'membrane_and_packet_cap_raw_area_um2':20*20+2*2,'per_layer_candidate_max_model_units':cand_max,'screens':rows,
      'scope':'Full-float final_fuse.standard local replay on three frozen 64x64 patches from the best checkpoint. The recurrence applies measured sign-specific one-event gain, ideal cap-sharing state dependence and fixed ±0.30V topplate range; weights remain continuous. Charge-transfer factors are assumed constant with voltage/state and calibrated from one sign/size operating point. Not closed-loop inference, a transistor-level replay, task accuracy, or a qualified analog mapping.'}
    RES.mkdir(parents=True,exist_ok=True); path=RES/'sky130_sc_cap_sharing_float_mapping_screen.json'; path.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(path),'layers':rows},indent=2)); return 0

def _fanin_counts(x,w):
    # Final-fuse input/event multiplicity is shared by all output channels.
    z=np.pad(x,((0,0),(0,0),(0,0),(1,1),(1,1)))
    counts=np.zeros((x.shape[0],x.shape[1],w.shape[0],x.shape[-2],x.shape[-1]),dtype=np.float32)
    for ci in range(w.shape[1]):
      for iy in range(w.shape[2]):
       for ix in range(w.shape[3]):
        counts+=z[:,:,ci,iy:iy+x.shape[-2],ix:ix+x.shape[-1]][:,:,None]
    v=counts[counts>0]
    return v

def _arg(k,d):
    import sys
    return next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith(k+'=')),d)
if __name__=='__main__': raise SystemExit(main())
