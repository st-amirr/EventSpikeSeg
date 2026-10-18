"""Bounded nominal simulation of five-module physically routed neuron parent."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_neuron_five_module_parent_v6';inv='gf180_phase_inverter_fullroute';tg='gf180_fixed_body_tg_quarter_shorttracks';mim='gf180_mim_5x5_ports_routed';nf='gf180_fixed_body_nf025_shorttracks'
 files={Path(__file__)};texts=[];cache_changes=[]
 for name in [cell,inv,tg,mim,nf]:
  folder=BASE/'layout'/name;qp=folder/'qualification.json';q=json.loads(qp.read_text());files.add(qp)
  assert q['magic_drc_count']==0 and q['lvs_unique']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    p=folder/n if key=='sha256' else ROOT/n;actual=sha(p)
    if actual!=h:
     assert p.suffix=='.ext',n
     cache_changes.append({'path':p.relative_to(ROOT).as_posix(),'qualified_sha256':h,'current_sha256':actual,'reason':'Generated hierarchical extraction cache rewritten by parent extraction; not a consumed simulation source. Geometry, GDS, device/cap netlists and flat qualification verified separately.'})
    files.add(p)
  if name==cell:
   fqpath=folder/'flat_cap_qualification.json';fq=json.loads(fqpath.read_text());files.add(fqpath);assert fq['flat_extraction_completed'] and not fq['negative_aggregate_branches']
   for n,h in fq['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
   txt=(folder/(fq['flat_subcircuit']+'_cap.spice')).read_text().replace(fq['flat_subcircuit'],cell)
  else:txt=(folder/(name+'_cap.spice')).read_text()
  for child in re.findall(r'(?m)^\.subckt (\S+)',txt):
   if child!=name:txt=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',name+'__'+child,txt)
  texts.append(txt)
 stem='gf180_five_module_parent_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat')
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();width=1.609384125256789
 calibration=BASE/'results/gf180_combined_v6_joint_reference_reset_calibration.json';cal=json.loads(calibration.read_text());files.add(calibration);assert cal['reference_calibration_completed'];width=cal['frozen_reset_width_us']
 lines=['Native physically joined five-module neuron parent',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vvcm vcm 0 1.65',f"Vauxref auxref 0 {cal['frozen_auxiliary_reference_v']:.16g}",'Vsensebias sensebias 0 .75','Vresetprogram resetprogram 0 .45','Vncas ncas 0 1.1','Vpcas pcas 0 2.2','Vpprogram pprogram 0 2.5','Vnprogram nprogram 0 .45','Iparkref parkbias 0 1u','Xparkref parkbias parkbias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u']
 phases={'holdout':'PWL(0 0 1042.99u 0 1043u 3.3 6050u 3.3)','write':'PWL(0 3.3 1009.99u 3.3 1010u 0 6050u 0)','auxreset':'PWL(0 3.3 1019.97u 3.3 1019.98u 0 1029.99u 0 1030u 3.3 6050u 3.3)','beta':'PWL(0 0 1019.99u 0 1020u 3.3 1020.49u 3.3 1020.5u 0 6050u 0)','az':'PWL(0 3.3 1004.99u 3.3 1005u 0 6050u 0)','sample':'PWL(0 0 1041.99u 0 1042u 3.3 1042.49u 3.3 1042.5u 0 6050u 0)','reset':f'PWL(0 0 1043.99u 0 1044u 3.3 {1044+width-.01}u 3.3 {1044+width}u 0 6050u 0)'}
 for ph,wave in phases.items():lines +=[f'V{ph} {ph}command 0 {wave}',f'Xb_{ph} {ph}command {ph}b vdd 0 {inv}',f'Xc_{ph} {ph}b {ph} vdd 0 {inv}']
 cases=[('near',1.67),('high',2.0),('low',1.64)];nodes=[]
 for tag,voltage in cases:
  st=f'state_{tag}';ref=f'ref_{tag}';out=f'out_{tag}';comp=f'comp_{tag}';park=f'park_{tag}'
  lines +=[f'Vtarget_{tag} target_{tag} 0 PWL(0 1.656875 1007.99u 1.656875 1008u {voltage} 6050u {voltage})',f'Xparent_{tag} {st} aux_{tag} target_{tag} write writeb auxreset beta auxref vcm 0 vdd {ref} sensebias {comp} holdout holdoutb az azb parkbias resetprogram ncas reset pprogram nprogram pcas 0 vdd 0 vdd sample sampleb spike_{tag} spikeb_{tag} {out} {park} {cell}',f'Xaz_{tag} {out} {ref} az azb 0 vdd {tg}',f'Xdummy_{tag} {ref} {ref} azb 0 {nf}',f'Xcomp_{tag} {out} {comp} 0 {mim}',f'.ic v({st})=1.656875 v(aux_{tag})=1.65 v({ref})=1.656875 v({out})=1.656875 v({park})=1.65']
  for k in range(9):lines.append(f'Xrefstore{k}_{tag} {ref} vcm 0 {mim}')
  nodes +=[f'v({st})',f'v({out})',f'v(spike_{tag})',f'v(spikeb_{tag})',f'v({park})',f'v({ref})',f'v(aux_{tag})']
 lines +=['.control','set numdgt=15','tran .005u 6050u 0 1u uic','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 report={'module_simulation_completed':False,'simulator_returncode':run.returncode,'generated_cache_changes':cache_changes,'frozen_reset_width_us':width,'frozen_aux_reference_v':cal['frozen_auxiliary_reference_v'],'scope':'Actual physically routed56MOS41MIM five-module parent, flat full DRC/LVS and726 nonnegative routing capacitor branches. Three independently initialized near/high/low arms with one beta/sample/reset cycle and5ms hold. Injection module continuously parked with no event during this baseline. Native external comparator autozero, dummy, reference and compensation MIM fixtures; external bias and phase commands. Original donor reference/reset width frozen; no state correction or new precision tuning. Characterization footprint not dense leaf or fullchip. No adaptation/inhibition/readout, autonomous phases/weight conversion, originalfloat accuracy or fullpopulation5ms claims.'}
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);complete=bool(run.returncode==0 and w.shape[1]==1+len(nodes) and np.isfinite(w).all() and abs(w[-1,0]-.00605)<1e-12 and 'aborted' not in log.lower());report['module_simulation_completed']=complete
  if complete:
   sample=lambda n,t:float(np.interp(t*1e-6,w[:,0],w[:,1+nodes.index(n)]))
   trained=.8818925023078918
   report['cases']=[{'case':tag,'target_v':v,'before_beta_v':sample(f'v(state_{tag})',1019),'before_sample_v':sample(f'v(state_{tag})',1041.5),'trained_beta_residual_v':sample(f'v(state_{tag})',1041.5)-1.65-trained*(sample(f'v(state_{tag})',1019)-1.65),'before_reset_v':sample(f'v(state_{tag})',1043.5),'after_reset_v':sample(f'v(state_{tag})',1049.5),'reset_interval_step_v':sample(f'v(state_{tag})',1049.5)-sample(f'v(state_{tag})',1043.5),'spike_before_reset_v':sample(f'v(spike_{tag})',1043.5),'spike_after_reset_v':sample(f'v(spike_{tag})',1049.5),'park_minus_state_before_reset_v':sample(f'v(park_{tag})',1043.5)-sample(f'v(state_{tag})',1043.5),'hold_drift_v':sample(f'v(state_{tag})',6049.5)-sample(f'v(state_{tag})',1049.5)} for tag,v in cases]

 except Exception as e:report['postprocess_error']=str(e)
 report['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in report.items() if k!='sha256'}},indent=2))
 assert report['module_simulation_completed']
if __name__=='__main__':main()
