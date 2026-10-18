"""Three bounded native DC cases at the actual64/128-channel reduction widths."""
from pathlib import Path
import hashlib,json,subprocess,argparse
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 n=64;cell='gf180_formatted_energy64_v3';d=BASE/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['mos_count']==36*n and q['magic_drc_count']==0 and f['flat_lvs_unique'] and not f['negative_aggregate_branches'];files={Path(__file__),qp,fp}
 for name,h in f['sha256'].items():
  if Path(name).suffix!='.ext':assert sha(ROOT/name)==h,name
  files.add(ROOT/name)
 flat=d/(f['flat_subcircuit']+'_cap.spice');files.add(flat);models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();stem=cell+'_three_transient_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dps=[BASE/'results'/(stem+'.dat')];nodes=[]
 for p in q['ports']:
  nodes.append(('ca' if int(p[9:])<32 else 'cb') if p.startswith('CANDIDATE') else p)
 lines=['Actual native full-channel energy reduction',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',flat.read_text(),'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vgnd VSS 0 0','Vbase VBASE 0 .9','Vzero VZERO 0 1.2','Vpen PENALTY 0 1.2','Ireference BIAS 0 64u','Vca ca 0 PWL(0 1.2 1.99u 1.2 2u 2.0 6u 2.0)','Vcb cb 0 PWL(0 1.2 3.99u 1.2 4u 2.0 6u 2.0)','Xreduce '+' '.join(nodes)+' '+f['flat_subcircuit'],'.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .005u 6u 0 .01u','wrdata /workspace/'+dps[0].relative_to(ROOT).as_posix()+' v(ROOT) i(Vdd)','quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);lp=BASE/'results'/(stem+'.log');log=run.stdout+run.stderr;lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'simulation_level':'native_flat_extracted_transient','channel_count':n,'native_mos_count':36*n,'scope':'Actual64 candidate-minus-penalty native formatters and full64 energy/mean-root connected in one flat2304MOS2816R1024MIM parent with all nonnegative extracted routing-capacitance branches retained. Three sequential levels in6us: all candidates1.2V, half2V, all2V; shared penalty1.2V,VBASE.9,VZERO1.2,VDD3.3,64uA master,typical27C. No ideal internal candidate-minus-penalty arithmetic or formatted gate drive. Candidate/penalty sources remain external ideal buffered fixtures. Compare samples1.5/3.5/5.5us against independent frozen source-hierarchy DC report. Compositional exact source/GDS and flat-device graph qualification retained; failed historical Netgen matching logs are not treated as passing. No fitted correction, calibrated trained RMS/epsilon, noise/PVT, all-neuron5ms service or full-chip acceptance','complete_RMS_accepted':False,'full_chip_layout_complete':False,'full_5ms_population_service_accepted':False}
 try:
  w=np.loadtxt(dps[0],skiprows=1);files.update(dps);ok=bool(run.returncode==0 and w.shape[1]==3 and np.isfinite(w).all() and abs(w[-1,0]-6e-6)<1e-15 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   dc=BASE/'results'/'gf180_formatted_energy64_v3_native_hierarchy_dc_src06716ac6c5d8.json';ref=json.loads(dc.read_text());assert ref['module_simulation_completed'];files.add(dc)
   sample=lambda k,t:float(np.interp(t*1e-6,w[:,0],w[:,k]));r['cases']=[]
   for tag,count,us,target in zip(['zero','half_active','all_active'],[0,n//2,n],[1.5,3.5,5.5],[c['root_v'] for c in ref['cases']]):
    r['cases'].append({'case':tag,'active_channels':count,'sample_time_us':us,'root_v':sample(1,us),'frozen_DC_root_v':target,'DC_tracking_error_v':sample(1,us)-target,'last0p25us_root_change_v':sample(1,us)-sample(1,us-.25),'supply_current_a':-sample(2,us)})
   roots=[c['root_v'] for c in r['cases']];r['max_abs_root_DC_tracking_error_v']=max(abs(c['DC_tracking_error_v']) for c in r['cases']);r['native_full_channel_energy_transient_observed']=bool(roots[0]>roots[1]>roots[2] and r['max_abs_root_DC_tracking_error_v']<.01);r['zero_subtracted_half_over_full_root_signal_ratio']=(roots[0]-roots[1])/(roots[0]-roots[2]);r['ideal_half_over_full_RMS_ratio']=2**-.5

 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='sha256'},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
