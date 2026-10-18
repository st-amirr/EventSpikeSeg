"""Three bounded native DC cases at the actual64/128-channel reduction widths."""
from pathlib import Path
import hashlib,json,subprocess,argparse
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--channels',type=int,choices=[64,128],required=True);a=ap.parse_args();n=a.channels;cell=f'gf180_energy_mean_root{n}_v1';d=BASE/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['mos_count']==7*n and q['magic_drc_count']==0 and f['flat_lvs_unique'] and not f['negative_aggregate_branches'];files={Path(__file__),qp,fp}
 for name,h in f['sha256'].items():
  if Path(name).suffix!='.ext':assert sha(ROOT/name)==h,name
  files.add(ROOT/name)
 flat=d/(f['flat_subcircuit']+'_cap.spice');files.add(flat);models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();stem=cell+'_three_dc_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dps=[BASE/'results'/(stem+'_'+tag+'.dat') for tag in ['zero','half_active','all_active']];nodes=[]
 for p in q['ports']:
  if p.startswith('IN_'):
   i=int(p[4:]);nodes.append(('plus' if p[3]=='P' else 'minus')+('a' if i<n//2 else 'b'))
  else:nodes.append(p)
 lines=['Actual native full-channel energy reduction',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',flat.read_text(),'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vgnd VSS 0 0','Vbase VBASE 0 .9','Vpa plusa 0 .9','Vna minusa 0 .9','Vpb plusb 0 .9','Vnb minusb 0 .9','Xreduce '+' '.join(nodes)+' '+f['flat_subcircuit'],'.control','set numdgt=15','set wr_singlescale','set wr_vecnames','op','wrdata /workspace/'+dps[0].relative_to(ROOT).as_posix()+' v(ROOT) i(Vdd)','alter Vpa 1.0','alter Vna .8','op','wrdata /workspace/'+dps[1].relative_to(ROOT).as_posix()+' v(ROOT) i(Vdd)','alter Vpb 1.0','alter Vnb .8','op','wrdata /workspace/'+dps[2].relative_to(ROOT).as_posix()+' v(ROOT) i(Vdd)','quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);lp=BASE/'results'/(stem+'.log');log=run.stdout+run.stderr;lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'simulation_level':'native_flat_extracted_DC_operating_points','channel_count':n,'native_mos_count':7*n,'scope':'Actual64/128-channel native energy kernel/current-sum and matched parallel diode mean/root receiver, flat native devices and extracted capacitance present. Three DC cases: all differential0, half channels plus/minus100mV, all channels plus/minus100mV, VBASE.9V,VDD3.3V,typical27C. External ideal gate-input fixtures common within each half; native candidate/penalty formatters and original-float scaling are not connected. DC establishes operating points, not loaded transient settling/5ms service or calibrated RMS/noise/epsilon. No fitted output correction. Full actual channel count/layout is present; no whole-model SPICE, model accuracy or full-chip acceptance.','complete_RMS_accepted':False,'full_chip_layout_complete':False,'full_5ms_population_service_accepted':False}
 try:
  rows=[np.loadtxt(p,skiprows=1).reshape(-1) for p in dps];files.update(dps);ok=bool(run.returncode==0 and all(len(v)==3 and np.isfinite(v).all() for v in rows) and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   r['cases']=[{'case':tag,'active_channels':count,'root_v':float(v[-2]),'root_vsg_v':3.3-float(v[-2]),'supply_current_a':float(-v[-1]),'nominal_DC_supply_power_w':float(-3.3*v[-1])} for tag,count,v in zip(['zero','half_active','all_active'],[0,n//2,n],rows)];roots=[c['root_v'] for c in r['cases']];r['native_full_channel_energy_reduction_observed']=bool(roots[0]>roots[1]>roots[2]);r['zero_subtracted_half_over_full_root_signal_ratio']=(roots[0]-roots[1])/(roots[0]-roots[2]);r['ideal_half_over_full_RMS_ratio']=2**-.5
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='sha256'},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
