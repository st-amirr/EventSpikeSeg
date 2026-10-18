"""Characterize four physical resident states on shared buses and one beta phase."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_resident_state_tile4_v2';d=BASE/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['magic_drc_count']==0 and q['gds_roundtrip_lvs_unique'] and f['flat_lvs_unique'] and not f['negative_aggregate_branches'];files={Path(__file__),qp,fp}
 for n,h in f['sha256'].items():
  if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
  files.add(ROOT/n)
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));pre='/workspace/'+models.relative_to(ROOT).as_posix();flat=d/(f['flat_subcircuit']+'_cap.spice');files.add(flat);stem=cell+'_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dp=BASE/'results'/(stem+'.dat')
 lines=['Four native resident states shared-bus fixture',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',flat.read_text(),'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vgnd VSS 0 0','Vcm VCM 0 1.2','Vauxref AUXREF 0 1.2','Vdata DATA 0 PWL(0 1.2 8.99u 1.2 9u .9 18.99u .9 19u 1.5 28.99u 1.5 29u 2.1 38.99u 2.1 39u 1.2 70u 1.2)','Vreset AUXRESET 0 PWL(0 3.3 44.99u 3.3 45u 0 70u 0)','Vbeta BETA 0 PWL(0 0 49.99u 0 50u 3.3 54.99u 3.3 55u 0 70u 0)']
 for i in range(4):
  points=[(0,3.3),(4.99,3.3),(5,0)]
  if i<3:points += [(9.99+10*i,0),(10+10*i,3.3),(11.99+10*i,3.3),(12+10*i,0)]
  points += [(70,0)]
  for net,invert in [('WRITE',False),('WRITEB',True)]:
   wave=' '.join((str(t)+'u' if t else '0')+' '+str(3.3-v if invert else v) for t,v in points);lines += [f'V{net}{i} {net}{i} 0 PWL({wave})']
 lines += ['Xtile '+' '.join(q['ports'])+' '+f['flat_subcircuit'],'.control','set numdgt=15','tran .005u 70u 0 .02u','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+dp.relative_to(ROOT).as_posix()+' '+' '.join(f'v({p}{i})' for i in range(4) for p in ['STATE','AUX']),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);lp=BASE/'results'/(stem+'.log');log=run.stdout+run.stderr;lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native16MOS4MIM2x2 resident tile with actual extracted shared DATA/VCM/AUXRESET/BETA/AUXREF supplies, distinct permanent STATE/AUX nodes and individual WRITE/WRITEB. All four physically initialized1.2V through writers; three selective writes .9/1.5/2.1V while fourth holds; shared data rebiases1.2, auxiliary reset releases then one common beta phase. Ideal complementary clock/reference voltage fixtures; no ideal state correction or digital numerical state. Typical27C deterministic70us fixture, not5ms retention/noise/PVT or trained-beta acceptance. Original representative leaf auxiliary overlap retained; array routing changes capacitance, so previous beta calibration does not transfer. Footprint is representative integration geometry, not final optimized dense array or full-chip area.','full_chip_layout_complete':False,'original_float_accuracy_accepted':False,'full_5ms_population_service_accepted':False}
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);ok=bool(run.returncode==0 and w.shape[1]==9 and np.isfinite(w).all() and abs(w[-1,0]-70e-6)<1e-12 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda i,t:float(np.interp(t*1e-6,w[:,0],w[:,1+2*i]));rows=[]
   for i,target in enumerate([.9,1.5,2.1,1.2]):
    before=sample(i,49.5);after=sample(i,69.5);rows.append({'state':i,'target_v':target,'before_beta_v':before,'after_beta_v':after,'post_beta_step_v':after-before,'apparent_beta_after_complete_phase':(after-1.2)/(before-1.2) if abs(before-1.2)>.01 else None,'selective_write_on_v':sample(i,11.5+10*i) if i<3 else None})
   r['cases']=[{'case':'initialize_four_select_three_rebias_update_once','states':rows}];r['unwritten_state_max_shift_before_beta_v']=float(np.max(np.abs(w[(w[:,0]>=5.5e-6)&(w[:,0]<=49.5e-6),7]-1.2)));r['native_independent_state_tile_observed']=bool(rows[0]['before_beta_v']<rows[1]['before_beta_v']<rows[2]['before_beta_v'] and abs(rows[3]['before_beta_v']-1.2)<.05 and rows[0]['post_beta_step_v']>0 and rows[2]['post_beta_step_v']<0)
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='sha256'},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
