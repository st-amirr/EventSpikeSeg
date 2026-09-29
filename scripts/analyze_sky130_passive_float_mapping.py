from __future__ import annotations
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/'artifacts/analog_asic/model_reference'; RES=ROOT/'artifacts/analog_asic/results'
TRACE=REF/'float_patch_trace.json'; PARAM=REF/'eventspikeseg140k_float_parameters.npz'
OUT=RES/'sky130_passive_float_mapping_screen.json'

def conv2d(x: np.ndarray, w: np.ndarray, output_hw: tuple[int,int] | None=None,
           groups: int=1, dilation: tuple[int,int]=(1,1),
           padding: tuple[int,int] | None=None) -> np.ndarray:
    # NCHW, same padding, infer the model convolution stride from output shape.
    t,cin,h,ww=x.shape; cout,_,kh,kw=w.shape
    oh,ow=output_hw or (h,w); sy=max(1,round(h/oh)); sx=max(1,round(ww/ow))
    assert kh%2==1 and kw%2==1 and cin%groups==0 and cout%groups==0 and cin//groups==w.shape[1]
    dy,dx=dilation
    py,px=padding if padding is not None else (dy*(kh//2),dx*(kw//2))
    xp=np.pad(x,((0,0),(0,0),(py,py),(px,px)))
    out=np.zeros((t,cout,oh,ow),dtype=np.float32)
    for iy in range(kh):
        for ix in range(kw):
            patch=xp[:,:,iy*dy:iy*dy+oh*sy:sy,ix*dx:ix*dx+ow*sx:sx]
            for group in range(groups):
                ci=slice(group*(cin//groups),(group+1)*(cin//groups))
                co=slice(group*(cout//groups),(group+1)*(cout//groups))
                out[:,co] += np.tensordot(w[co,:,iy,ix],patch[:,ci],axes=([1],[1])).transpose(1,0,2,3)
    return out

def replay(current: np.ndarray, beta: np.ndarray, threshold: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    state=np.zeros_like(current[0]); spikes=[]; states=[]
    for ti in range(current.shape[0]):
        proposal=beta*state+current[ti]
        fired=proposal>=threshold[ti]
        state=proposal-fired.astype(np.float32)*threshold[ti]
        spikes.append(fired); states.append(state.copy())
    return np.stack(spikes),np.stack(states)

def main():
    trace_path=Path(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--trace-meta=')),str(TRACE)))
    parameter_path=Path(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--params=')),str(PARAM)))
    trace=json.loads(trace_path.read_text(encoding='utf-8'))
    archive_path=Path(trace['trace_archive'])
    arrays=np.load(archive_path if archive_path.is_absolute() else trace_path.parent/archive_path)
    params=np.load(parameter_path)
    parameter_meta=json.loads((REF/'eventspikeseg140k_float_reference.json').read_text(encoding='utf-8'))
    conv_meta={x['name']:x for x in parameter_meta['effective_folded_weight_and_neuron_parameters']}
    trace_rows={r['name']:r for r in trace['sampled_stages']}; rows=[]
    gain=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--gain-v-per-v=')),str(8.93255e-3)))
    membrane_cap_um=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--membrane-cap-um=')),'10'))
    packet_cap_um=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--packet-cap-um=')),'1'))
    max_step_v=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--max-step-v=')),'0.512'))
    dac_step_v=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--dac-step-v=')),'0'))
    dac_bits=int(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--dac-bits=')),'0'))
    layer_scaled_dac='--layer-scaled-dac' in sys.argv
    floor_uv=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--minimum-step-uv=')),'0'))
    output_path=Path(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--output=')),str(OUT)))
    headrooms=tuple(float(v) for v in next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--headrooms=')),'0.15,0.30,0.60').split(','))
    # Continuous full-float weights; no QAT or quantized minimum step.
    gains={membrane_cap_um:gain}
    for key in params.files:
        if not key.startswith('weight__'): continue
        name=key.removeprefix('weight__'); trace_name=name.replace('__','.')
        if trace_name not in trace_rows: continue
        row=trace_rows[trace_name]; meta=row['candidate_before_threshold_and_reset']
        cand_max=max(abs(float(meta['min'])),abs(float(meta['max'])))
        w=params[key].astype(np.float32); aw=np.abs(w)
        x=arrays['presynaptic_input__'+name].astype(np.float32)
        cand=arrays['candidate__'+name].astype(np.float32)
        thr=arrays['threshold__'+name].astype(np.float32)
        beta=params['beta__'+name].astype(np.float32).reshape(1,-1,1,1)
        ref_spike=arrays['spikes__'+name].astype(bool)
        ref_mem=arrays['membrane__'+name].astype(np.float32)
        ref_current=arrays['current__'+name].astype(np.float32)
        baseline_spike,baseline_state=replay(ref_current,beta,thr)
        baseline_mismatch=float(np.mean(baseline_spike!=ref_spike))
        conv_info=conv_meta[trace_name]
        geom={k:tuple(conv_info[k]) for k in ('conv_dilation','conv_padding')}
        conv_baseline=conv2d(x,w,cand.shape[-2:],groups=conv_info['conv_groups'],
                             dilation=geom['conv_dilation'],padding=geom['conv_padding']).reshape(cand.shape)
        stage={'layer':trace_name,'float_conv_reconstruction_max_abs_error_model_units':float(np.max(np.abs(conv_baseline-ref_current))),'weight_count':int(w.size),'candidate_abs_max_model_units':cand_max,
          'weight_abs_quantiles_p0p1_p1_p50_p99_max':[float(v) for v in np.quantile(aw,[.001,.01,.5,.99,1])],
          'candidate_margin_abs_q0p1_q1_model_units':row['candidate_minus_threshold_margin_model_units']['abs_percentiles_0p1_1_10_50_90'][:2], 'screens':[]}
        for cm,gain in gains.items():
            for headroom in headrooms:
                vpu=headroom/cand_max; req=aw*vpu; max_delta=gain*max_step_v; min_delta=floor_uv*1e-6
                under=req<min_delta; over=req>max_delta
                effective_dac_step_v=dac_step_v
                if dac_bits>0:
                    dac_full_scale_v=max_step_v
                    if layer_scaled_dac:
                        dac_full_scale_v=min(max_step_v,float(np.max(req/gain)))
                    effective_dac_step_v=2*dac_full_scale_v/(2**dac_bits)
                if effective_dac_step_v>0:
                    max_codes=np.floor(max_step_v/effective_dac_step_v)
                    dac_v=np.minimum(np.rint((req/gain)/effective_dac_step_v),max_codes)*effective_dac_step_v
                    got=np.where(under,0.0,np.minimum(req,dac_v*gain))
                else:
                    dac_v=np.zeros_like(req)
                    got=np.where(under,0.0,np.minimum(req,max_delta))
                mapped=np.sign(w)*got/vpu
                current=conv2d(x,mapped,cand.shape[-2:],groups=conv_info['conv_groups'],
                               dilation=geom['conv_dilation'],padding=geom['conv_padding']).reshape(cand.shape)
                spike,state_trace=replay(current,beta,thr)
                cerr=np.abs(current-ref_current); merr=np.abs(state_trace-ref_mem)
                active_counts=conv2d(x,np.ones_like(w),cand.shape[-2:],groups=conv_info['conv_groups'],
                                     dilation=geom['conv_dilation'],padding=geom['conv_padding']).ravel(); active_counts=active_counts[active_counts>0]
                screens={'membrane_cap_side_um':cm,'measured_delta_per_topplate_volt_v_per_v':gain,'measured_delta_at_max_measured_step_uv':gain*max_step_v*1e6,
                  'candidate_headroom_v':headroom,'volts_per_model_unit':vpu,'median_threshold_uv':float(np.median(thr)*vpu*1e6),
                  'fraction_weights_below_continuous_analog_floor':float(under.mean()),
                  'fraction_weights_quantized_to_zero':float(np.mean(got==0.0)),
                  'uniform_topplate_dac_step_v':effective_dac_step_v if effective_dac_step_v>0 else None,
                  'fraction_weights_above_0p512V_measured_packet_range':float(over.mean()),'fraction_weights_represented':float((~under&~over).mean()),
                  'required_topplate_step_quantiles_v_p0p1_p1_p50_p99_max':[float(v) for v in np.quantile(req/gain,[.001,.01,.5,.99,1])],
                  'mapped_current_error_abs_model_units_p50_p90_p99':[float(v) for v in np.quantile(cerr,[.5,.9,.99])],
                  'mapped_state_error_abs_model_units_p50_p90_p99_max':[float(v) for v in (np.quantile(merr,[.5,.9,.99]).tolist()+[float(merr.max())])],
                  'baseline_float_current_replay_spike_mismatch_fraction':baseline_mismatch,
                  'baseline_float_current_state_error_abs_model_units_p99':float(np.quantile(np.abs(baseline_state-ref_mem),.99)),
                  'spike_mismatch_fraction_vs_full_float_trace':float(np.mean(spike!=ref_spike)),
                  'spike_rate_full_float_vs_mapped':[float(ref_spike.mean()),float(spike.mean())],
                  'active_destinations_event_count_p50_p90_p99_max':[float(v) for v in np.percentile(active_counts,[50,90,99,100])],
                  'serialized_packet_service_us_p50_p90_p99_max_at_2p5us':[float(v*2.5) for v in np.percentile(active_counts,[50,90,99,100])]}
                stage['screens'].append(screens)
        rows.append(stage)
    report={'test':'sky130_passive_mim_float_weight_mapping_sensitivity','checkpoint_sha256':trace['checkpoint_sha256'],'checkpoint_epoch':trace['checkpoint_epoch'],'qat_or_quantized_reference_used':False,
      'measured_transfer_basis':{'membrane_cap_um':membrane_cap_um,'packet_cap_um':packet_cap_um,'per_topplate_volt_v_per_v':gain,
        'topplate_step_sweep_v':[0.033],'max_packet_topplate_step_v':max_step_v,
        'minimum_event_floor_uv':floor_uv,'uniform_topplate_dac_step_v':dac_step_v if dac_step_v>0 else None,
        'dac_bits':dac_bits if dac_bits>0 else None,'layer_scaled_dac_full_scale':layer_scaled_dac,
        'read_buffer_device_scale':0.25,'method':'5ms passive packet event minus matched no-event membrane difference at 33mV packet step; permanent 0.25x read buffer; 50ns maximum transient step'},
      'layers':rows,'scope':'Local per-layer replay on three sampled 64x64 DSEC patches from one full-float checkpoint using the physically measured 10um passive-cap transfer slope over signed top-plate steps through 512mV. Analog weight contributions are continuous with no QAT/quantization floor; weights outside the demonstrated voltage range are clipped. The float input spikes are held fixed, thresholds come from the recorded float trace, and peer-inhibition state feedback is not recomputed; baseline float-current replay mismatch is reported separately to expose this limitation. Assumes ideal continuous analog weight drive. No analog noise/mismatch/PVT, nonlinear state-dependent calibration, comparator kick, area or task accuracy; this is not closed-loop full-network inference.'}
    output_path.parent.mkdir(parents=True,exist_ok=True); output_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(output_path),'layers':[{ 'layer':r['layer'],'screens':r['screens']} for r in rows]},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
