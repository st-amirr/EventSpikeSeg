"""Native pulse termination guard on actual routed weight-duration comparator."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_sequenced_signed_injector_v2';guard='gf180_pulse_termination_guard_v2';inv='gf180_phase_inverter_fullroute';tg='gf180_fixed_body_tg_quarter_shorttracks';mim='gf180_mim_5x5_ports_routed'
 files={Path(__file__)};texts=[];cache_changes=[]
 for name in [cell,inv,tg,mim]:
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
   for n,h in fq['sha256'].items():
    p=ROOT/n;actual=sha(p)
    if actual!=h:
     assert p.suffix=='.ext',n
     cache_changes.append({'path':n,'qualified_sha256':h,'current_sha256':actual,'reason':'Generated extraction cache rewritten by subsequent qualified layout build; not consumed geometry or simulation netlist.'})
    files.add(p)
   txt=(folder/(fq['flat_subcircuit']+'_cap.spice')).read_text().replace(fq['flat_subcircuit'],name)
  else:txt=(folder/(name+'_cap.spice')).read_text()
  for child in re.findall(r'(?m)^\.subckt (\S+)',txt):
   if child!=name:txt=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',name+'__'+child,txt)
  texts.append(txt)
 case_index=int(sys.argv[1]);assert case_index in [0,1,2]
 stem='gf180_weight_low_end_10pct_v1'+str(case_index)+'_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat')
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();width=1.609384125256789
 lines=['Native request-to-signed-charge physical assembly',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vbias bias 0 .75','Vresetref resetref 0 1.0','Vrampbias rampbias 0 2.6','Vrampcas rampcas 0 2.2','Vvcm vcm 0 1.65','Vpprogram pprogram 0 2.5','Vnprogram nprogram 0 .613','Vpcas pcas 0 2.2','Vncas ncas 0 1.1','Vclk clock_source 0 PULSE(0 3.3 1000.2u .01u .01u 9.99u 20u)','Vreset reset_source 0 PWL(0 3.3 1029.99u 3.3 1030u 0 1134u 0)','Vrequest request_source 0 PWL(0 0 1034.99u 0 1035u 3.3 1050.99u 3.3 1051u 0 1134u 0)']
 for ph in ['clock','reset','request']:lines +=[f'Xb_{ph} {ph}_source {ph}b vdd 0 {inv}',f'Xc_{ph} {ph}b {ph} vdd 0 {inv}']
 cases=[('magnitude_1p04_positive',1.04)];nodes=[]
 for tag,voltage in cases:
  sign=3.3 if 'negative' in tag else 0
  lines +=[f'Vsign_{tag} sign_{tag} 0 {sign}',f'Vdata_{tag} data_{tag} 0 {voltage}',f'Xwrite_{tag} state_{tag} vcm reset resetb 0 vdd {tg}',f'Xstore0_{tag} state_{tag} 0 0 {mim}',f'Xstore1_{tag} state_{tag} 0 0 {mim}',f'Vmeter_{tag} state_{tag} tap_{tag} 0',f'Xjoined_{tag} clock reset request data_{tag} sign_{tag} tap_{tag} vcm pprogram nprogram pcas ncas bias resetref rampbias rampcas vdd 0 ready_{tag} sample_{tag} arm_{tag} recover_{tag} done_{tag} pulse_{tag} pos_{tag} neg_{tag} {cell}']
  nodes +=[f'v({p}_{tag})' for p in ['pulse','pos','neg','state','ready','sample','arm','recover','done']]+[f'i(Vmeter_{tag})']
 lines +=['.control','set numdgt=15','tran .01u 1134u 0 .05u uic','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','300','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=315)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 report={'module_simulation_completed':False,'simulator_returncode':run.returncode,'generated_cache_changes':cache_changes,'scope':'Actual230MOS4MIM physically joined sequencer and signed injector,1225 routing-capacitance branches. Fixed1ms power-on pre-bias before50kHz clock starts; request/reset shifted by same1ms. Native sequencer generates SAMPLE/ARM/RECOVER/DONE and phase complements; no external WRITE/ARM waveforms. One bounded300s signed-charge case at1.04V, corresponding to10% of the 1.0–1.4V per-tensor float magnitude mapping. Two nativeMIM state loads initialized through actual reset TG; external analog programming/bias/PARK remain. Short-startup parent pulse clipped toARM;1ms prebias diagnostic restored cutoff. This complete-event run includes final READY. Earlier180s complete-event run reached recovery at1110us but timed out beforeDONE. Fixed300s bound completes the same1134us window without circuit/solver changes. No per-weight calibration,quantization,ideal ramp or model-accuracy/population5ms/full-chip acceptance.'}
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);complete=bool(run.returncode==0 and w.shape[1]==1+len(nodes) and np.isfinite(w).all() and abs(w[-1,0]-.001134)<1e-12 and 'aborted' not in log.lower());report['module_simulation_completed']=complete
  if complete:
   sample=lambda n,t:float(np.interp(t*1e-6,w[:,0],w[:,1+nodes.index(n)]))
   results=[]
   for tag,v in cases:
    y=w[:,1+nodes.index(f'v(pulse_{tag})')];t=w[:,0];mask=(t>=1079e-6)&(t<=1095e-6)
    ii=np.where((y[:-1]<1.65)&(y[1:]>=1.65)&mask[:-1])[0];jj=np.where((y[:-1]>=1.65)&(y[1:]<1.65)&mask[:-1])[0]
    cross=lambda i:float(t[i]+(1.65-y[i])*(t[i+1]-t[i])/(y[i+1]-y[i]))
    rises=[cross(int(i)) for i in ii];falls=[cross(int(i)) for i in jj];width_us=(falls[0]-rises[0])*1e6 if len(rises)==len(falls)==1 else None
    results.append({'case':tag,'programmed_magnitude_v':v,'rising_edges_s':rises,'falling_edges_s':falls,'pulse_width_us':width_us,'pulse_late_v':sample(f'v(pulse_{tag})',1133),'state_before_v':sample(f'v(state_{tag})',1079),'state_after_v':sample(f'v(state_{tag})',1095),'state_step_v':sample(f'v(state_{tag})',1095)-sample(f'v(state_{tag})',1079),'net_charge_into_state_c':float(-np.trapezoid(w[(t>=1079e-6)&(t<=1095e-6),1+nodes.index(f'i(Vmeter_{tag})')],t[(t>=1079e-6)&(t<=1095e-6)]))})
   for r in results:
    tag=r['case'];r['ready_end_v']=sample(f'v(ready_{tag})',1133);r['ready_during_arm_v']=sample(f'v(ready_{tag})',1085);r['sequencer_strobe_counts']={}
    for ph in ['sample','arm','recover','done']:
     yy=w[:,1+nodes.index(f'v({ph}_{tag})')];r['sequencer_strobe_counts'][ph]=int(np.sum((yy[:-1]<1.65)&(yy[1:]>=1.65)&(t[:-1]>1031e-6)))
   report['cases']=results
   report['expected_sign_observed']=bool(results[0]['state_step_v']<0 if case_index==2 else results[0]['state_step_v']>0)


 except Exception as e:report['postprocess_error']=str(e)
 report['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in report.items() if k!='sha256'}},indent=2))
 assert report['module_simulation_completed']
if __name__=='__main__':main()
