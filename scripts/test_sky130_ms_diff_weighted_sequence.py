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
 headroom=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--headroom-v=')), '0.30'))
 cap=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--membrane-cap-um=')), '20'))
 cm_g=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--cm-servo-s=')), '0'))
 balance='--charge-balance' in sys.argv[1:]
 tr=json.loads((REF/'float_patch_trace_all.json').read_text()); arc=np.load(REF/tr['trace_archive']); params=np.load(REF/'eventspikeseg140k_float_parameters.npz'); meta=json.loads((REF/'eventspikeseg140k_float_reference.json').read_text()); import runpy
 fn=runpy.run_path(str(ROOT/'scripts/analyze_sky130_passive_float_mapping.py'))['conv2d']
 x=arc['presynaptic_input__final_fuse__standard'].astype(np.float32); w=params['weight__final_fuse__standard'].astype(np.float32); cand=arc['candidate__final_fuse__standard']; cur=arc['current__final_fuse__standard']; thr=arc['threshold__final_fuse__standard']; geom=next(z for z in meta['effective_folded_weight_and_neuron_parameters'] if z['name']=='final_fuse.standard')
 active=fn(x,np.ones_like(w),cand.shape[-2:],groups=geom['conv_groups'],dilation=tuple(geom['conv_dilation']),padding=tuple(geom['conv_padding']))
 site_rank=int(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--site-rank=')), '0'))
 if site_rank<0 or site_rank>=active.size: raise ValueError('site rank is outside the active-output array')
 site_order=np.argsort(-active.reshape(-1),kind='stable'); ni,oi,yy,xx=np.unravel_index(int(site_order[site_rank]),active.shape); count=int(active[ni,oi,yy,xx]); contrib=[]; pad_y,pad_x=geom['conv_padding']; dy,dx=geom['conv_dilation']
 for o in [oi]:
  for ic in range(w.shape[1]):
   for ky in range(w.shape[2]):
    for kx in range(w.shape[3]):
     iy=yy*max(1,round(x.shape[-2]/cand.shape[-2]))+ky*dy-pad_y; ix=xx*max(1,round(x.shape[-1]/cand.shape[-1]))+kx*dx-pad_x
     if 0<=iy<x.shape[-2] and 0<=ix<x.shape[-1]:
      n=int(x[ni,ic,iy,ix]); val=float(w[o,ic,ky,kx]);
      for _ in range(n):
       if abs(val)>0: contrib.append(val)
 chosen_current=float(cur.reshape(30,16,64,64)[ni,oi,yy,xx]); cmax=float(np.max(np.abs(cand))); vpu=headroom/cmax
 calname='sky130_ms_diff_gate_amplitude_c20_w10.5n_pg0.72_ng0.6_wp1.5_wn1_l10_d0v_cm0.9v_t200u_n46_fr0.1-1_h1b6c16181e_step2n.json' if cap==20 else 'sky130_ms_diff_gate_amplitude_c10_w10.5n_pg0.72_ng0.6_wp1.5_wn1_l10_t200u_fr0-0.05-0.1-0.15-0.2-0.25-0.3-0.35-0.4-0.45-0.5-0.55-0.6-0.65-0.7-0.75-0.8-0.85-0.9-0.95-1_step0.5n.json'; calpath=RES/calname; cal=json.loads(calpath.read_text()); pts=cal['event_transfer_by_gate_magnitude']; fs=sorted({float(r['gate_magnitude_fraction']) for r in pts if r['polarity']=='p' and float(r['gate_magnitude_fraction'])>0}); ds=[]
 for f in fs:
  p=next(r for r in pts if r['polarity']=='p' and float(r['gate_magnitude_fraction'])==f); n=next(r for r in pts if r['polarity']=='n' and float(r['gate_magnitude_fraction'])==f); ds.append((abs(p['final_differential_change_mv'])+abs(n['final_differential_change_mv']))*0.5e-3)
 ds=np.maximum.accumulate(ds); gate=lambda val: float(np.interp(abs(val)*vpu*gain,ds,fs))
 if balance:
  if cap!=20: raise ValueError('charge balance is calibrated only for the 20um pair')
  balance_calpath=RES/'sky130_ms_diff_gate_amplitude_c20_w10.5n_pg0.72_ng0.6_wp1.5_wn1_l10_d0v_cm0.9v_t200u_n23_fr0.1-1_h0abd11cedc_step2n.json'
  balance_pts=json.loads(balance_calpath.read_text())['event_transfer_by_gate_magnitude']
  branch_curves={}
  for sign in ('p','n'):
   rows=sorted((r for r in balance_pts if r['polarity']==sign),key=lambda r:float(r['gate_magnitude_fraction']))
   fractions=np.array([float(r['gate_magnitude_fraction']) for r in rows])
   d=np.array([float(r['final_differential_change_mv'])*1e-3 for r in rows])
   cm=np.array([float(r['final_common_mode_change_mv'])*1e-3 for r in rows])
   p_charge=cm+(d/2 if sign=='p' else -d/2)
   n_charge=(d/2-cm if sign=='p' else -d/2-cm)
   branch_curves[sign]=(fractions,np.maximum.accumulate(p_charge),np.maximum.accumulate(n_charge))
  def balanced_gate(val):
   fractions,p_charge,n_charge=branch_curves['p' if val>0 else 'n']
   half_target=abs(val)*vpu*gain/2
   return (float(np.interp(half_target,p_charge,fractions)),float(np.interp(half_target,n_charge,fractions)))
 seq=[]
 for v in contrib:
  fp,fn=balanced_gate(v) if balance else (gate(v),gate(v))
  seq.append((v,fp,fn))
 seq.sort(key=lambda z:(1 if z[0]>0 else -1,abs(z[0])))
 shuffle_seed=int(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--shuffle-seed=')), '140'))
 order_policy=next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--order-policy=')), 'shuffle')
 if order_policy=='shuffle':
  rng=random.Random(shuffle_seed); scheduled=list(seq); rng.shuffle(scheduled); random_name=f'random_seed{shuffle_seed}'
 elif order_policy=='neutral':
  remaining=list(seq); scheduled=[]; running=0.; total=sum(v for v,_,_ in seq)
  for i in range(len(seq)):
   target=total*(i+1)/len(seq)
   j=min(range(len(remaining)),key=lambda k:(abs(running+remaining[k][0]-target),-abs(remaining[k][0])))
   item=remaining.pop(j); scheduled.append(item); running+=item[0]
  random_name='neutral_schedule'
 else: raise ValueError('order-policy must be shuffle or neutral')
 seqs={'forward':seq,'reverse':list(reversed(seq)),random_name:scheduled}
 period_default=4900/max(len(seq)-1,1); period_us=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--event-period-us=')),str(period_default))); pulse_ns=10.5; first_us=50.; last_us=first_us+period_us*(len(seq)-1)
 def gate_wave(sq, gate, pol):
  off=1.8 if gate=='p' else 0.; pts=[f'0 {off:.12g}'];
  for i,(v,fp,fn) in enumerate(sq):
   if (v>0)!=(pol=='p'): continue
   f=fp if gate=='p' else fn
   t=first_us+i*period_us; active=(1.8-f*1.08) if gate=='p' else f*.6; pts += [f'{t-.001:.12g}u {off:.12g}',f'{t:.12g}u {active:.12g}',f'{t+pulse_ns/1000:.12g}u {active:.12g}',f'{t+pulse_ns/1000+.001:.12g}u {off:.12g}']
  pts += [f'5100u {off:.12g}']; return 'PWL('+' '.join(pts)+')'
 # write a clean deck from scratch
 deck_lines=['SKY130 full-float weighted event-sequence direct MOS accumulation',COMMON,'.subckt diff_inject vp vn pp np pn nn vdd vss params: wp=1.5 wn=1 l=10','Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}','Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w={wn} l={l}','Xp_neg vn pn vdd vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}','Xn_pos vp np vss vss sky130_fd_pr__nfet_01v8 w={wn} l={l}','.ends diff_inject','Vdd vdd 0 1.8','Vcm vcm 0 0.9',
 f'Xmem_pf vpf vcm membrane_mim w_um={cap:g} l_um={cap:g}',f'Xmem_nf vnf vcm membrane_mim w_um={cap:g} l_um={cap:g}','.ic v(vpf)=0.9','.ic v(vnf)=0.9','.ic v(xmem_pf.xmim.a)=0.9','.ic v(xmem_nf.xmim.a)=0.9',
 f'Xmem_pr vpr vcm membrane_mim w_um={cap:g} l_um={cap:g}',f'Xmem_nr vnr vcm membrane_mim w_um={cap:g} l_um={cap:g}','.ic v(vpr)=0.9','.ic v(vnr)=0.9','.ic v(xmem_pr.xmim.a)=0.9','.ic v(xmem_nr.xmim.a)=0.9',
 f'Xmem_pq vpq vcm membrane_mim w_um={cap:g} l_um={cap:g}',f'Xmem_nq vnq vcm membrane_mim w_um={cap:g} l_um={cap:g}','.ic v(vpq)=0.9','.ic v(vnq)=0.9','.ic v(xmem_pq.xmim.a)=0.9','.ic v(xmem_nq.xmim.a)=0.9',
 f'Xmem_pz vpz vcm membrane_mim w_um={cap:g} l_um={cap:g}',f'Xmem_nz vnz vcm membrane_mim w_um={cap:g} l_um={cap:g}','.ic v(vpz)=0.9','.ic v(vnz)=0.9','.ic v(xmem_pz.xmim.a)=0.9','.ic v(xmem_nz.xmim.a)=0.9',
 'Xinj_f vpf vnf pp_f np_f pn_f nn_f vdd 0 diff_inject wp=1.5 wn=1 l=10','Xinj_r vpr vnr pp_r np_r pn_r nn_r vdd 0 diff_inject wp=1.5 wn=1 l=10','Xinj_q vpq vnq pp_q np_q pn_q nn_q vdd 0 diff_inject wp=1.5 wn=1 l=10',
 'Vpp_z pp_z 0 1.8','Vnp_z np_z 0 0','Vpn_z pn_z 0 1.8','Vnn_z nn_z 0 0','Xinj_z vpz vnz pp_z np_z pn_z nn_z vdd 0 diff_inject wp=1.5 wn=1 l=10']
 for name,sq in seqs.items():
  suff={'forward':'f','reverse':'r',random_name:'q'}[name]
  for gn,gate,pol in [('pp','p','p'),('nn','n','p'),('pn','p','n'),('np','n','n')]:
   deck_lines.append(f'V{gn}_{suff} {gn}_{suff} 0 {gate_wave(sq,gate,pol)}')
 if cm_g>0:
  for suf,vp,vn in [('f','vpf','vnf'),('r','vpr','vnr'),('q','vpq','vnq'),('z','vpz','vnz')]:
   deck_lines += [f'Bcm_p_{suf} {vp} 0 I={{{cm_g:g}*((v({vp})+v({vn}))/2-v(vcm))}}',f'Bcm_n_{suf} {vn} 0 I={{{cm_g:g}*((v({vp})+v({vn}))/2-v(vcm))}}']
 deck_lines += ['.control','set numdgt=15','tran 2n 5.1m uic','let df=v(vpf)-v(vnf)','let dr=v(vpr)-v(vnr)','let cmf=(v(vpf)+v(vnf))/2','let cmr=(v(vpr)+v(vnr))/2','let dq=v(vpq)-v(vnq)','let cmq=(v(vpq)+v(vnq))/2','let dz=v(vpz)-v(vnz)','let cmz=(v(vpz)+v(vnz))/2','meas tran f_diff find df at=5m','meas tran r_diff find dr at=5m','meas tran q_diff find dq at=5m','meas tran z_diff find dz at=5m','meas tran f_cm find cmf at=5m','meas tran r_cm find cmr at=5m','meas tran q_cm find cmq at=5m','meas tran z_cm find cmz at=5m','quit','.endc','.end']
 tag=f'fullfloat_n{len(seq)}_rank{site_rank}_idx{ni}_o{oi}_y{yy}_x{xx}_H{headroom:g}_c{cap:g}_densecal_w10.5n_l10_g{gain:g}_p{period_us*1000:g}n_qseed{shuffle_seed}_order{order_policy}_cm{cm_g:g}_bal{int(balance)}_s2n_pwl12_refcmp'; deck=BENCH/f'sky130_ms_diff_weighted_sequence_{tag}.cir'; deck.write_text('\n'.join(deck_lines)+'\n')
 cmd=['docker','run','--rm','--memory','8g','--cpus','2','--volume',f'{ROOT}:/workspace:ro','--volume',f'{OUT}:/workspace/artifacts/analog_asic','--workdir','/workspace/artifacts/analog_asic/benches','--entrypoint','timeout','eventspikeseg:analog-ngspice36','240','ngspice','-b',deck.name]; proc=subprocess.run(cmd,capture_output=True,text=True,timeout=255); log=proc.stdout+proc.stderr; out=RES/f'sky130_ms_diff_weighted_sequence_{tag}.log'; out.write_text(log)
 vals={k:float(v) for k,v in re.findall(r'(?im)^\s*(f_diff|r_diff|q_diff|z_diff|f_cm|r_cm|q_cm|z_cm)\s*=\s*([-+0-9.eE]+)',log)}; done=proc.returncode==0 and len(vals)==8
 ideal=chosen_current*vpu; result={'simulation_completed':done,'return_code':proc.returncode,'selected_site_rank_by_active_fanin':site_rank,'selected_time_index':int(ni),'selected_output_channel':int(oi),'selected_yx':[int(yy),int(xx)],'fan_in_events':len(seq),'ideal_full_float_current_model_units':chosen_current,'candidate_headroom_v':headroom,'volts_per_model_unit':vpu,'ideal_target_event_sum_v':ideal,'event_gain_correction':gain,'membrane_cap_square_width_um':cap,'common_mode_servo_transconductance_s':cm_g,'charge_balanced_gate_mapping':balance,'event_order_policy':order_policy,'random_order_seed':shuffle_seed if order_policy=='shuffle' else None,'event_time_range_us':[first_us,last_us],'event_spacing_us':period_us,'pulse_width_ns':pulse_ns,'timestep_ns':2,'sequence_order_comparison':{},'scope':f'One final_fuse output location with actual frozen full-float weights and presynaptic counts expanded into {pulse_ns:g} ns physical gate pulses. Events are serialized at the commanded spacing inside a 5ms hold interval. Direct differential MOS TT schematic with ideal gate values; charge balance uses separately interpolated pMOS/nMOS fractions from isolated-event TT calibration, still ideal gate sources. Neutral scheduling uses advance knowledge of all signed contributions and is an ideal controller upper bound. Any behavioral common-mode servo is an upper-bound experiment, not a transistor-level implementation. No per-weight programming circuit, noise/mismatch/PVT/layout or closed-loop network.'}
 if done:
  inc={k:vals[k]-vals['z_diff'] for k in ('f_diff','r_diff','q_diff')}
  result['sequence_order_comparison']={'forward_final_diff_v':inc['f_diff'],'reverse_final_diff_v':inc['r_diff'],f'{random_name}_final_diff_v':inc['q_diff'],'matched_no_event_final_diff_v':vals['z_diff'],'forward_raw_final_diff_v':vals['f_diff'],'reverse_raw_final_diff_v':vals['r_diff'],f'{random_name}_raw_final_diff_v':vals['q_diff'],'ideal_diff_v':ideal,'forward_relative_error':(inc['f_diff']-ideal)/max(abs(ideal),1e-15),'reverse_relative_error':(inc['r_diff']-ideal)/max(abs(ideal),1e-15),f'{random_name}_relative_error':(inc['q_diff']-ideal)/max(abs(ideal),1e-15),'order_difference_v':inc['f_diff']-inc['r_diff'],'matched_no_event_common_mode_v':vals['z_cm'],'forward_common_mode_v':vals['f_cm'],'reverse_common_mode_v':vals['r_cm'],f'{random_name}_common_mode_v':vals['q_cm'],'forward_common_mode_shift_v':vals['f_cm']-vals['z_cm'],'reverse_common_mode_shift_v':vals['r_cm']-vals['z_cm'],f'{random_name}_common_mode_shift_v':vals['q_cm']-vals['z_cm']}
 dest=RES/f'sky130_ms_diff_weighted_sequence_{tag}.json'; dest.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2)); return 0 if done else 2
if __name__=='__main__': raise SystemExit(main())




