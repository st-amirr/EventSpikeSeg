"""Native formatted amplitude-times-triangle product voltage characterization."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_native_adaptation_product_v3';folder=BASE/'layout'/cell;qp=folder/'qualification.json';fp=folder/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'] and f['flat_lvs_unique'] and not f['negative_aggregate_branches'];files={Path(__file__),qp,fp}
 for n,h in f['sha256'].items():
  if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
  files.add(ROOT/n)
 flat=folder/(f['flat_subcircuit']+'_cap.spice');files.add(flat);model=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(model.rglob('*.spice'));prefix='/workspace/'+model.relative_to(ROOT).as_posix();stem=cell+'_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dp=BASE/'results'/(stem+'_dc.dat');tp=BASE/'results'/(stem+'_transient.dat')
 lines=['Native product gate formatter',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',flat.read_text().replace(f['flat_subcircuit'],cell),'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vbase base 0 .9','Vzero vzero 0 1.2','Vcom vcom 0 1.65','Ireference bias 0 1u','Vamp amplitude 0 PWL(0 1.2 14.99u 1.2 15u 1.4 29.99u 1.4 30u 1.8 50u 1.8)','Vtri triangle 0 PWL(0 1.6 14.99u 1.6 15u 1.4 29.99u 1.4 30u 1.6 50u 1.6)',f'Xproduct amplitude triangle base vzero vcom penalty bias vdd 0 {cell}','.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .005u 50u 0 .02u','wrdata /workspace/'+tp.relative_to(ROOT).as_posix()+' v(amplitude) v(triangle) v(penalty) v(bias)','quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native42MOS46R20MIM fully native voltage-format/current-product/linear-receiver chain, actual extracted wiring including ten additional physically routed22um native MIM compensation capacitors, typical27C. Three externally driven buffered amplitude/triangle fixtures; VZERO1.2,VBASE.9,VCOM1.65V and master1uA. No ideal gate arithmetic/product/receiver/output clamp inside circuit. Native formatter ratio1/8 scales each deviation; physical square-difference core drives feedback receiver. Resident storage and actual buffered age triangle not connected yet; trained amplitude/triangle normalization, all-channel reduction, noise/PVT and dense area remain unfinished. Raw offset and product nonlinearity retained. No full adaptation/model accuracy/population5ms/full-chip acceptance.','complete_adaptation_accepted':False,'product_precision_accepted':False}
 try:
  t=np.loadtxt(tp,skiprows=1);files.add(tp);ok=bool(run.returncode==0 and t.shape[1]==5 and np.isfinite(t).all() and abs(t[-1,0]-50e-6)<1e-15 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,t[:,0],t[:,k]));r['cases']=[];v=[sample(3,us) for us in [14.5,29.5,49.5]]
   for i,(tag,a,tr,us) in enumerate([('zero_amplitude',1.2,1.6,14.5),('equal_mid_inputs',1.4,1.4,29.5),('high_amplitude_triangle',1.8,1.6,49.5)]):
    r['cases'].append({'case':tag,'amplitude_v':a,'triangle_v':tr,'ideal_deviation_product_v2':(a-1.2)*(tr-1.2),'penalty_voltage_v':v[i],'penalty_increment_from_zero_v':v[i]-v[0],'bias_v':sample(4,us)})
   r['raw_zero_offset_from_vcom_v']=v[0]-1.65;r['high_to_mid_increment_ratio']=float((v[2]-v[0])/(v[1]-v[0]));r['ideal_high_to_mid_product_ratio']=6.;r['positive_native_product_observed']=bool(v[2]>v[1]>v[0]);r['last_0p5us_penalty_change_v']=[sample(3,us)-sample(3,us-.5) for us in [14.5,29.5,49.5]]
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
