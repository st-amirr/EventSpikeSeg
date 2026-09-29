"""Map full-float event magnitudes to pulse duration in the differential MOS cell."""
from __future__ import annotations
import json, random, re, subprocess, sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/analog_asic'; REF=OUT/'model_reference'; RES=OUT/'results'; BENCH=OUT/'benches'
COMMON='''.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
'''

def arg(key,default):
    return next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith(key+'=')),str(default))

def main():
    head=float(arg('--headroom-v',0.15)); gain=float(arg('--event-gain-correction',1.0))
    period=float(arg('--event-period-us',0.03)); cap=float(arg('--membrane-cap-um',20))
    calib_path=RES/arg('--calibration','sky130_ms_diff_pulse_width_c20_cm0.918v_w0.1-0.2-0.25-0.3-0.4-0.5-0.75-1-1.5-2-3-4-6-8-10-12-16-20-24-32-48-64_s0.02n.json')
    calib_obj=json.loads(calib_path.read_text()); calibration=calib_obj['same_phase_no_event_subtracted_transfer']['20']['points']
    p_on=float(calib_obj['p_gate_on_v']); n_on=float(calib_obj['n_gate_on_v'])
    widths=np.array([float(r['pulse_width_ns']) for r in calibration])
    curves={'p':np.maximum.accumulate(np.array([float(r['p_delta_v']) for r in calibration])),
            'n':np.maximum.accumulate(np.array([abs(float(r['n_delta_v'])) for r in calibration]))}
    tr=json.loads((REF/'float_patch_trace_all.json').read_text()); arc=np.load(REF/tr['trace_archive'])
    params=np.load(REF/'eventspikeseg140k_float_parameters.npz'); meta=json.loads((REF/'eventspikeseg140k_float_reference.json').read_text())
    conv=__import__('runpy').run_path(str(ROOT/'scripts/analyze_sky130_passive_float_mapping.py'))['conv2d']
    x=arc['presynaptic_input__final_fuse__standard'].astype(np.float32); w=params['weight__final_fuse__standard'].astype(np.float32)
    cand=arc['candidate__final_fuse__standard']; cur=arc['current__final_fuse__standard']
    geom=next(z for z in meta['effective_folded_weight_and_neuron_parameters'] if z['name']=='final_fuse.standard')
    active=conv(x,np.ones_like(w),cand.shape[-2:],groups=geom['conv_groups'],dilation=tuple(geom['conv_dilation']),padding=tuple(geom['conv_padding']))
    ti,oi,yy,xx=np.unravel_index(np.argmax(active),active.shape); pad_y,pad_x=geom['conv_padding']; dy,dx=geom['conv_dilation']; events=[]
    for ic in range(w.shape[1]):
      for ky in range(w.shape[2]):
       for kx in range(w.shape[3]):
        iy=yy*max(1,round(x.shape[-2]/cand.shape[-2]))+ky*dy-pad_y; ix=xx*max(1,round(x.shape[-1]/cand.shape[-1]))+kx*dx-pad_x
        if 0<=iy<x.shape[-2] and 0<=ix<x.shape[-1]:
         wt=float(w[oi,ic,ky,kx]); events.extend([wt]*int(x[ti,ic,iy,ix]))
    events=[v for v in events if v!=0]; cmax=float(np.max(np.abs(cand))); vpu=head/cmax
    mapped=[]; below=above=0
    for value in events:
        sign='p' if value>0 else 'n'; target=abs(value)*vpu*gain; curve=curves[sign]
        if target < curve[0]*0.5: width=0.; below+=1
        else:
            if target>curve[-1]: above+=1
            width=float(np.interp(np.clip(target,curve[0],curve[-1]),curve,widths))
            width=max(0.1,round(width/0.1)*0.1)
        mapped.append((value,width))
    required=max((w for _,w in mapped),default=0.)
    if period*1000 < required+2: raise ValueError(f'event spacing {period*1000:g}ns is shorter than max pulse {required:g}ns plus 2ns off gap')
    ordered=sorted(mapped,key=lambda z:(1 if z[0]>0 else -1,abs(z[0])))
    rng=random.Random(140); shuffled=list(ordered); rng.shuffle(shuffled)
    sequences={'forward':ordered,'reverse':list(reversed(ordered)),'random_seed140':shuffled}
    first=50.; last=first+period*(len(events)-1)
    def waveform(seq,which,event_sign):
        off=1.8 if which=='p' else 0.; on=p_on if which=='p' else n_on; pts=[f'0 {off:.12g}']
        for i,(v,width) in enumerate(seq):
            if width<=0 or ((v>0)!=(event_sign=='p')): continue
            t=first+i*period; end=t+width/1000
            pts += [f'{t-0.001:.12g}u {off:.12g}',f'{t:.12g}u {on:.12g}',f'{end:.12g}u {on:.12g}',f'{end+0.001:.12g}u {off:.12g}']
        pts += ['5100u '+f'{off:.12g}']; return 'PWL('+' '.join(pts)+')'
    lines=['SKY130 full-float differential pulse-duration-coded event sequence',COMMON,
      '.subckt diff_inject vp vn pp np pn nn vdd vss params: wp=1.5 wn=1 l=10',
      'Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}',
      'Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w={wn} l={l}',
      'Xp_neg vn pn vdd vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}',
      'Xn_pos vp np vss vss sky130_fd_pr__nfet_01v8 w={wn} l={l}','.ends diff_inject',
      'Vdd vdd 0 1.8','Vcm vcm 0 0.9']
    for name,seq in [*sequences.items(),('ref',[])]:
        a='vp_'+name; b='vn_'+name
        lines += [f'Xmem_p_{name} {a} vcm membrane_mim w_um={cap:g} l_um={cap:g}',f'Xmem_n_{name} {b} vcm membrane_mim w_um={cap:g} l_um={cap:g}',
          f'.ic v({a})=0.9',f'.ic v({b})=0.9',f'.ic v(xmem_p_{name}.xmim.a)=0.9',f'.ic v(xmem_n_{name}.xmim.a)=0.9']
        for port,which,event_sign in [('pp','p','p'),('nn','n','p'),('pn','p','n'),('np','n','n')]:
            value=('1.8' if which=='p' else '0') if name=='ref' else waveform(seq,which,event_sign)
            lines.append(f'V{port}_{name} {port}_{name} 0 {value}')
        lines.append(f'Xinj_{name} {a} {b} pp_{name} np_{name} pn_{name} nn_{name} vdd 0 diff_inject wp=1.5 wn=1 l=10')
    lines += ['.control','set numdgt=15','tran 2n 5.1m uic']
    for name in [*sequences,'ref']:
        lines += [f'let d_{name}=v(vp_{name})-v(vn_{name})',f'let c_{name}=(v(vp_{name})+v(vn_{name}))/2',f'meas tran d_{name} find d_{name} at=5m',f'meas tran c_{name} find c_{name} at=5m']
    lines += ['quit','.endc','.end']
    tag=f'n{len(events)}_idx{ti}_o{oi}_y{yy}_x{xx}_H{head:g}_c{cap:g}_duration_bias{p_on:g}-{n_on:g}_g{gain:g}_p{period*1000:g}n_s2n_pwl12_refcmp_signfix'
    deck=BENCH/f'sky130_ms_diff_weighted_duration_sequence_{tag}.cir'; deck.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    cmd=['docker','run','--rm','--memory','8g','--cpus','2','--volume',f'{ROOT}:/workspace:ro','--volume',f'{OUT}:/workspace/artifacts/analog_asic','--workdir','/workspace/artifacts/analog_asic/benches','--entrypoint','timeout','eventspikeseg:analog-ngspice36','240','ngspice','-b',deck.name]
    proc=subprocess.run(cmd,capture_output=True,text=True,timeout=255); log=proc.stdout+proc.stderr; (RES/f'sky130_ms_diff_weighted_duration_sequence_{tag}.log').write_text(log,encoding='utf-8')
    vals={k:float(v) for k,v in re.findall(r'(?im)^\s*(d_(?:forward|reverse|random_seed140|ref)|c_(?:forward|reverse|random_seed140|ref))\s*=\s*([-+0-9.eE]+)',log)}
    done=proc.returncode==0 and len(vals)==8; ideal=float(cur.reshape(30,16,64,64)[ti,0,yy,xx])*vpu
    result={'simulation_completed':done,'return_code':proc.returncode,'selected_time_index':int(ti),'selected_batch':0,'selected_output_channel':int(oi),'selected_yx':[int(yy),int(xx)],'event_count':len(events),'candidate_headroom_v':head,'event_gain_correction':gain,'calibration_initial_common_mode_v':0.918,'ideal_signed_sum_v':ideal,'pulse_width_mapping_ns_min_median_p99_max':[float(np.min([q for _,q in mapped])),float(np.median([q for _,q in mapped])),float(np.quantile([q for _,q in mapped],.99)),float(np.max([q for _,q in mapped]))],'weights_omitted_below_minimum_pulse':below,'weights_clipped_above_calibration':above,'event_period_ns':period*1000,'event_train_duration_us':last-first,'matched_no_event_final_diff_v':vals.get('d_ref'),'sequence_comparison':{},'scope':'One final-fusion output location, actual full-float weights and presynaptic counts; p/n pulse duration independently mapped from measured SKY130 TT 20um MIM transfer initialized at the observed no-event common mode. Pulses serialized at the commanded spacing and held to 5ms. Ideal gate drivers; no timing jitter, programmed weight storage, readout/threshold/reset, PVT, mismatch, noise, extraction or full-network feedback.'}
    if done:
        result['sequence_comparison']={name:{'raw_final_diff_v':vals['d_'+name],'event_increment_vs_no_event_v':vals['d_'+name]-vals['d_ref'],'relative_error':(vals['d_'+name]-vals['d_ref']-ideal)/max(abs(ideal),1e-15),'common_mode_v':vals['c_'+name],'common_mode_shift_vs_no_event_v':vals['c_'+name]-vals['c_ref']} for name in sequences}
        result['sequence_comparison']['order_difference_v']=vals['d_forward']-vals['d_reverse']
    out=RES/f'sky130_ms_diff_weighted_duration_sequence_{tag}.json'; out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result,indent=2)); return 0 if done else 2

if __name__=='__main__': raise SystemExit(main())
