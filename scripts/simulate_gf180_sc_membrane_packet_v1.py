"""Simulate a transistor-switched MIM charge packet into the native GF180 membrane state node."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_subckts(path):
 text=path.read_text(encoding='utf8',errors='replace'); chunks=re.split(r'(?im)(?=^\.subckt\s+)',text); found={}
 for c in chunks:
  m=re.match(r'(?im)^\.subckt\s+(\S+)',c)
  if not m:continue
  e=re.search(r'(?im)^\.ends(?:\s+\S+)?\s*$',c); assert e,(path,m.group(1)); found[m.group(1)]=c[:e.end()].strip()
 return found
def main():
 p=argparse.ArgumentParser();p.add_argument('--state-v',type=float,choices=[.75,1.65,2.55],required=True);p.add_argument('--polarity',choices=['p','n'],required=True);p.add_argument('--delta-v',type=float,default=.026);p.add_argument('--tag',default='screen');a=p.parse_args()
 paths=[BASE/'layout/gf180_nf_state_update_aux_overlap/gf180_nf_state_update_aux_overlap_cap.spice',BASE/'layout/gf180_mim_5x5_ports_routed/gf180_mim_5x5_ports_routed_cap.spice',BASE/'layout/gf180_fixed_body_tg_fullroute_half/gf180_fixed_body_tg_fullroute_half_cap.spice',BASE/'layout/gf180_phase_inverter_fullroute/gf180_phase_inverter_fullroute_cap.spice']
 qs=[BASE/'layout'/n/'qualification.json' for n in ['gf180_nf_state_update_aux_overlap','gf180_mim_5x5_ports_routed','gf180_fixed_body_tg_fullroute_half','gf180_phase_inverter_fullroute']]
 sources=set(paths+qs)
 for qpath in qs:
  q=json.loads(qpath.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'];assert ('gds_roundtrip_drc_count' not in q or q['gds_roundtrip_drc_count']==0) and ('gds_roundtrip_lvs_unique' not in q or q['gds_roundtrip_lvs_unique'])
  for k in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for f,h in q.get(k,{}).items():
    target=(qpath.parent/f if k=='sha256' else ROOT/f);assert sha(target)==h,target;sources.add(target)
 merged={}
 for path in paths:
  for n,body in read_subckts(path).items():
   if n in merged:assert re.sub(r'\s+',' ',merged[n])==re.sub(r'\s+',' ',body),n
   merged[n]=body
 mdir=BASE/'pdk/gf180_primitive_source/models/ngspice'; design=mdir/'design.spice';typ=mdir/'sm141064.spice'; sources.update([design,typ]);
 suffix='lo' if a.state_v<1 else 'hi' if a.state_v>2 else 'mid';stem=f'gf180_sc_membrane_packet_{suffix}_{a.polarity}_{a.tag}_{sha(Path(__file__))[:10]}';bench=BASE/'benches'/(stem+'.spice');logp=BASE/'results'/(stem+'.log');reportp=BASE/'results'/(stem+'.json');assert not any(x.exists() for x in [bench,logp,reportp])
 dv=a.delta_v if a.polarity=='p' else -a.delta_v
 lines=['Native membrane switched-capacitor packet diagnostic',f'.include /workspace/{design.relative_to(ROOT).as_posix()}',f'.lib /workspace/{typ.relative_to(ROOT).as_posix()} typical',f'.lib /workspace/{typ.relative_to(ROOT).as_posix()} mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*merged.values(),'Vdd vdd 0 3.3','Vss vss 0 0','Vcm vcm 0 1.65',f'Vdata data 0 {a.state_v}','Vwrite_cmd writecmd 0 PWL(0 3.3 9.99u 3.3 10u 0 5100u 0)','Vauxreset auxreset 0 PWL(0 3.3 1.99u 3.3 2u 0 5100u 0)','Vbeta beta_cmd 0 PWL(0 0 19u 0 20u 3.3 29u 3.3 30u 0 5100u 0)','Vpark_cmd parkcmd 0 PWL(0 3.3 39u 3.3 40u 0 129.99u 0 130u 3.3 140u 3.3 140.01u 0 5100u 0)','Vinj_cmd injcmd 0 PWL(0 0 109.99u 0 110u 3.3 115u 3.3 116u 0 5100u 0)',f'Vbottom pbottom 0 PWL(0 1.65 99.99u 1.65 100u {1.65+dv} 116.99u {1.65+dv} 117u 1.65 5100u 1.65)','Xb_write writecmd writeb vdd vss gf180_phase_inverter_fullroute','Xc_write writeb write vdd vss gf180_phase_inverter_fullroute','Xb_beta beta_cmd betab vdd vss gf180_phase_inverter_fullroute','Xc_beta betab beta vdd vss gf180_phase_inverter_fullroute','Xb_park parkcmd parkb vdd vss gf180_phase_inverter_fullroute','Xc_park parkb park vdd vss gf180_phase_inverter_fullroute','Xb_inj injcmd injb vdd vss gf180_phase_inverter_fullroute','Xc_inj injb inj vdd vss gf180_phase_inverter_fullroute',f'Xstate state aux data write writeb auxreset beta vcm vcm vss vdd gf180_nf_state_update_aux_overlap','Xpacket ptop pbottom vss gf180_mim_5x5_ports_routed','Xpark ptop state park parkb vss vdd gf180_fixed_body_tg_fullroute_half','Xinject ptop state inj injb vss vdd gf180_fixed_body_tg_fullroute_half',f'.ic v(state)={a.state_v} v(aux)=1.65 v(ptop)=1.65 v(pbottom)=1.65']
 lines += ['.control','set numdgt=15',f'tran 20n 5100u 0 20n uic','meas tran state_pre_beta find v(state) at=19u','meas tran state_post_beta find v(state) at=32u','meas tran state_pre_packet find v(state) at=109u','meas tran state_post_packet find v(state) at=125u','meas tran state_5ms find v(state) at=5100u','quit','.endc','.end',''];bench.write_text('\n'.join(lines),encoding='utf8');sources.add(bench)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','150','ngspice','-b','/workspace/'+bench.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=160)
 log=run.stdout+run.stderr;logp.write_text(log,encoding='utf8');sources.add(logp);vals={k:float(v) for k,v in re.findall(r'(?mi)^(state_[a-z0-9_]+)\s*=\s*([-+0-9.eE]+)',log)};keys=['state_pre_beta','state_post_beta','state_pre_packet','state_post_packet','state_5ms'];complete=run.returncode==0 and all(k in vals for k in keys) and 'timestep too small' not in log.lower()
 q={'simulation_completed':complete,'state_initial_v':a.state_v,'polarity':a.polarity,'packet_bottom_step_v':dv,'measurements_v':vals,'beta_delta_v':vals.get('state_post_beta',0)-vals.get('state_pre_beta',0),'packet_state_step_v':vals.get('state_post_packet',0)-vals.get('state_pre_packet',0),'postpacket_hold_drift_mv':(vals.get('state_5ms',0)-vals.get('state_post_packet',0))*1000,'scope':'Schematic composition using extracted routed native state/update cell, extracted routed 5um MIM capacitor, extracted TGs and inverter drivers. One ideal bottom-plate voltage step represents the weight driver. The packet top is reset to VCM, isolated while its bottom changes, connected to STATE for charge sharing, then disconnected. The actual full-cell interconnect is not yet routed; nominal TT27 only, one state and one event, no mismatch/noise/PVT or model replay. Not a complete PLIF/full-chip acceptance.','sha256':{f.relative_to(ROOT).as_posix():sha(f) for f in sorted(sources)}};reportp.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(reportp),'completed':complete,'step_v':q['packet_state_step_v'],'beta_delta_v':q['beta_delta_v'],'hold_drift_mv':q['postpacket_hold_drift_mv']},indent=2));
 if not complete:raise RuntimeError(log[-2000:])
if __name__=='__main__':main()
