from __future__ import annotations
import json,re,subprocess,random
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'artifacts/analog_asic'; REF=OUT/'model_reference'; RES=OUT/'results'; BENCH=OUT/'benches'
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
def main():
 import sys
 gain=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--event-gain-correction=')), '1.0'))
 tr=json.loads((REF/'float_patch_trace_all.json').read_text()); arc=np.load(REF/tr['trace_archive']); params=np.load(REF/'eventspikeseg140k_float_parameters.npz'); meta=json.loads((REF/'eventspikeseg140k_float_reference.json').read_text()); import runpy
 fn=runpy.run_path(str(ROOT/'scripts/analyze_sky130_passive_float_mapping.py'))['conv2d']
 x=arc['presynaptic_input__final_fuse__standard'].astype(np.float32); w=params['weight__final_fuse__standard'].astype(np.float32); cand=arc['candidate__final_fuse__standard']; cur=arc['current__final_fuse__standard']; thr=arc['threshold__final_fuse__standard']; geom=next(z for z in meta['effective_folded_weight_and_neuron_parameters'] if z['name']=='final_fuse.standard')
 active=fn(x,np.ones_like(w),cand.shape[-2:],groups=geom['conv_groups'],dilation=tuple(geom['conv_dilation']),padding=tuple(geom['conv_padding']))
 ni,oi,yy,xx=np.unravel_index(np.argmax(active),active.shape); count=int(active[ni,oi,yy,xx]); contrib=[]; pad_y,pad_x=geom['conv_padding']; dy,dx=geom['conv_dilation']
 for o in [oi]:
  for ic in range(w.shape[1]):
   for ky in range(w.shape[2]):
    for kx in range(w.shape[3]):
     iy=yy*max(1,round(x.shape[-2]/cand.shape[-2]))+ky*dy-pad_y; ix=xx*max(1,round(x.shape[-1]/cand.shape[-1]))+kx*dx-pad_x
     if 0<=iy<x.shape[-2] and 0<=ix<x.shape[-1]:
      n=int(x[ni,ic,iy,ix]); val=float(w[o,ic,ky,kx]);
      for _ in range(n):
       if abs(val)>0: contrib.append(val)
 chosen_current=float(cur.reshape(30,16,64,64)[ni,oi,yy,xx]); cmax=float(np.max(np.abs(cand))); vpu=.30/cmax
 calpath=RES/'sky130_ms_diff_gate_amplitude_c20_w10.5n_pg0.72_ng0.6_wp1.5_wn1_l10_d0v_cm0.9v_t200u_n46_fr0.1-1_h1b6c16181e_step2n.json'; cal=json.loads(calpath.read_text()); pts=cal['event_transfer_by_gate_magnitude']; fs=sorted({float(r['gate_magnitude_fraction']) for r in pts if r['polarity']=='p' and float(r['gate_magnitude_fraction'])>0}); ds=[]
 for f in fs:
  p=next(r for r in pts if r['polarity']=='p' and float(r['gate_magnitude_fraction'])==f); n=next(r for r in pts if r['polarity']=='n' and float(r['gate_magnitude_fraction'])==f); ds.append((abs(p['final_differential_change_mv'])+abs(n['final_differential_change_mv']))*0.5e-3)
 ds=np.maximum.accumulate(ds); gate=lambda val: float(np.interp(abs(val)*vpu*gain,ds,fs))
 seq=[]
 for v in contrib: seq.append((v,gate(v)))
 seq.sort(key=lambda z:(1 if z[0]>0 else -1,abs(z[0])))
 rng=random.Random(140); shuffled=list(seq); rng.shuffle(shuffled); seqs={'forward':seq,'reverse':list(reversed(seq)),'random_seed140':shuffled}
 period_us=4900/max(len(seq)-1,1); pulse_ns=10.5; first_us=50.; last_us=first_us+period_us*(len(seq)-1)
 def gate_wave(sq, gate, pol):
  off=1.8 if gate=='p' else 0.; pts=[f'0 {off:.12g}'];
  for i,(v,f) in enumerate(sq):
   if (v>0)!=(pol=='p'): continue
   t=first_us+i*period_us; active=(1.8-f*1.08) if gate=='p' else f*.6; pts += [f'{t-.001:.12g}u {off:.12g}',f'{t:.12g}u {active:.12g}',f'{t+pulse_ns/1000:.12g}u {active:.12g}',f'{t+pulse_ns/1000+.001:.12g}u {off:.12g}']
  pts += [f'5100u {off:.12g}']; return 'PWL('+' '.join(pts)+')'
 # write a clean deck from scratch
 deck_lines=['SKY130 full-float weighted event-sequence cascode-isolated differential MOS accumulation',COMMON,'.subckt diff_inject vp vn pp np pn nn vdd vss vbp vbn params: wp=1.5 wn=1 l=10','Xp_pos vp_mid pp vdd vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}','Xp_cas vp vbp vp_mid vdd sky130_fd_pr__pfet_01v8 w={2*wp} l={l}','Rbleed_pp vp_mid vdd 1Meg','Xn_neg vn_mid nn vss vss sky130_fd_pr__nfet_01v8 w={wn} l={l}','Xn_cas vn vbn vn_mid vss sky130_fd_pr__nfet_01v8 w={2*wn} l={l}','Rbleed_nn vn_mid vss 1Meg','Xp_neg vn_mid_n pn vdd vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}','Xp_cas_n vn vbp vn_mid_n vdd sky130_fd_pr__pfet_01v8 w={2*wp} l={l}','Rbleed_pn vn_mid_n vdd 1Meg','Xn_pos vp_mid_n np vss vss sky130_fd_pr__nfet_01v8 w={wn} l={l}','Xn_cas_n vp vbn vp_mid_n vss sky130_fd_pr__nfet_01v8 w={2*wn} l={l}','Rbleed_np vp_mid_n vss 1Meg','.ends diff_inject','Vdd vdd 0 1.8','Vcm vcm 0 0.9','Vbpc vbp 0 0.8','Vbnc vbn 0 0.7',
 'Xmem_pf vpf vcm membrane_mim w_um=20 l_um=20','Xmem_nf vnf vcm membrane_mim w_um=20 l_um=20','.ic v(vpf)=0.9','.ic v(vnf)=0.9','.ic v(xmem_pf.xmim.a)=0.9','.ic v(xmem_nf.xmim.a)=0.9',
 'Xmem_pr vpr vcm membrane_mim w_um=20 l_um=20','Xmem_nr vnr vcm membrane_mim w_um=20 l_um=20','.ic v(vpr)=0.9','.ic v(vnr)=0.9','.ic v(xmem_pr.xmim.a)=0.9','.ic v(xmem_nr.xmim.a)=0.9',
 'Xmem_pq vpq vcm membrane_mim w_um=20 l_um=20','Xmem_nq vnq vcm membrane_mim w_um=20 l_um=20','.ic v(vpq)=0.9','.ic v(vnq)=0.9','.ic v(xmem_pq.xmim.a)=0.9','.ic v(xmem_nq.xmim.a)=0.9',
 'Xinj_f vpf vnf pp_f np_f pn_f nn_f vdd 0 vbp vbn diff_inject wp=1.5 wn=1 l=10','Xinj_r vpr vnr pp_r np_r pn_r nn_r vdd 0 vbp vbn diff_inject wp=1.5 wn=1 l=10','Xinj_q vpq vnq pp_q np_q pn_q nn_q vdd 0 vbp vbn diff_inject wp=1.5 wn=1 l=10']
 for name,sq in seqs.items():
  suff={'forward':'f','reverse':'r','random_seed140':'q'}[name]
  for gn,gate,pol in [('pp','p','p'),('nn','n','p'),('pn','p','n'),('np','n','n')]:
   deck_lines.append(f'V{gn}_{suff} {gn}_{suff} 0 {gate_wave(sq,gate,pol)}')
 deck_lines += ['.control','set numdgt=15','tran 2n 5.1m uic','let df=v(vpf)-v(vnf)','let dr=v(vpr)-v(vnr)','let cmf=(v(vpf)+v(vnf))/2','let cmr=(v(vpr)+v(vnr))/2','let dq=v(vpq)-v(vnq)','let cmq=(v(vpq)+v(vnq))/2','meas tran f_diff find df at=5m','meas tran r_diff find dr at=5m','meas tran q_diff find dq at=5m','meas tran f_cm find cmf at=5m','meas tran r_cm find cmr at=5m','meas tran q_cm find cmq at=5m','quit','.endc','.end']
 tag=f'fullfloat_n{len(seq)}_idx{ni}_o{oi}_y{yy}_x{xx}_H0.3_c20_cascode_densecal_w10.5n_l10_g{gain:g}_s2n_pwl12'; deck=BENCH/f'sky130_ms_diff_cascode_weighted_sequence_{tag}.cir'; deck.write_text('\n'.join(deck_lines)+'\n')
 cmd=['docker','run','--rm','--memory','8g','--cpus','2','--volume',f'{ROOT}:/workspace:ro','--volume',f'{OUT}:/workspace/artifacts/analog_asic','--workdir','/workspace/artifacts/analog_asic/benches','--entrypoint','timeout','eventspikeseg:analog-ngspice36','240','ngspice','-b',deck.name]; proc=subprocess.run(cmd,capture_output=True,text=True,timeout=255); log=proc.stdout+proc.stderr; out=RES/f'sky130_ms_diff_cascode_weighted_sequence_{tag}.log'; out.write_text(log)
 vals={k:float(v) for k,v in re.findall(r'(?im)^\s*(f_diff|r_diff|q_diff|f_cm|r_cm|q_cm)\s*=\s*([-+0-9.eE]+)',log)}; done=proc.returncode==0 and len(vals)==6
 ideal=chosen_current*vpu; result={'simulation_completed':done,'return_code':proc.returncode,'selected_flat_batch':int(ni),'selected_output_channel':int(oi),'selected_yx':[int(yy),int(xx)],'fan_in_events':len(seq),'ideal_full_float_current_model_units':chosen_current,'candidate_headroom_v':.3,'volts_per_model_unit':vpu,'ideal_target_event_sum_v':ideal,'event_time_range_us':[first_us,last_us],'event_spacing_us':period_us,'pulse_width_ns':pulse_ns,'timestep_ns':2,'sequence_order_comparison':{},'scope':f'One final_fuse output location with actual frozen full-float weights and presynaptic counts expanded into {pulse_ns:g} ns physical gate pulses. Events are spread uniformly across a 5ms bin. Direct differential MOS TT schematic, ideal gate values, no per-weight programming circuit, no noise/mismatch/PVT/layout or closed-loop network.'}
 if done:
  result['sequence_order_comparison']={'forward_final_diff_v':vals['f_diff'],'reverse_final_diff_v':vals['r_diff'],'random_seed140_final_diff_v':vals['q_diff'],'ideal_diff_v':ideal,'forward_relative_error':(vals['f_diff']-ideal)/max(abs(ideal),1e-15),'reverse_relative_error':(vals['r_diff']-ideal)/max(abs(ideal),1e-15),'random_seed140_relative_error':(vals['q_diff']-ideal)/max(abs(ideal),1e-15),'order_difference_v':vals['f_diff']-vals['r_diff'],'forward_common_mode_v':vals['f_cm'],'reverse_common_mode_v':vals['r_cm'],'random_seed140_common_mode_v':vals['q_cm']}
 dest=RES/f'sky130_ms_diff_cascode_weighted_sequence_{tag}.json'; dest.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2)); return 0 if done else 2
if __name__=='__main__': raise SystemExit(main())





