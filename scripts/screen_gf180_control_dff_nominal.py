"""Native pulse termination guard on actual routed weight-duration comparator."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_control_dff_v1';phase='gf180_nonoverlap_phase_pair_v2';guard='gf180_pulse_termination_guard_v2';inv='gf180_phase_inverter_fullroute';tg='gf180_fixed_body_tg_quarter_shorttracks';mim='gf180_mim_5x5_ports_routed'
 files={Path(__file__)};texts=[];cache_changes=[]
 for name in [cell,phase]:
  folder=BASE/'layout'/name;qp=folder/'qualification.json';q=json.loads(qp.read_text());files.add(qp)
  assert q['magic_drc_count']==0 and q['lvs_unique']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    p=folder/n if key=='sha256' else ROOT/n;actual=sha(p)
    if actual!=h:
     assert p.suffix=='.ext',n
     cache_changes.append({'path':p.relative_to(ROOT).as_posix(),'qualified_sha256':h,'current_sha256':actual,'reason':'Generated hierarchical extraction cache rewritten by parent extraction; not a consumed simulation source. Geometry, GDS, device/cap netlists and flat qualification verified separately.'})
    files.add(p)
  if name in [cell,phase]:
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
 stem='gf180_control_dff_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat')
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();width=1.609384125256789
 lines=['Native extracted interlocked two-phase generator',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vcmd command 0 PULSE(0 3.3 2u .01u .01u .49u 1u)']
 lines +=[f'Xphase command vdd 0 a ab b bb {phase}']
 cases=[('zero','0'),('one','3.3'),('pattern','PWL(0 0 2.19u 0 2.2u 3.3 3.19u 3.3 3.2u 0 4.19u 0 4.2u 3.3 5.19u 3.3 5.2u 0 6.19u 0 6.2u 3.3 7.19u 3.3 7.2u 0 8u 0)')];nodes=[]
 for tag,wave in cases:
  lines +=[f'Vdata_{tag} d_{tag} 0 {wave}',f'Xdff_{tag} d_{tag} a ab b bb vdd 0 q_{tag} qb_{tag} {cell}']
  nodes +=[f'v(d_{tag})',f'v(q_{tag})',f'v(qb_{tag})']
 lines +=['.control','set numdgt=15','tran .001u 8u 0 .002u uic','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 report={'module_simulation_completed':False,'simulator_returncode':run.returncode,'generated_cache_changes':cache_changes,'scope':'Actual16MOS static native TG master/slave control flip-flop, flat extracted57 routing branches. Native18MOS nonoverlap phase pair drives three zero/one/toggling D cases at1MHz. Modules schematic-connected here. Control-state storage only; no digital membrane or quantized weights. No reset built in; known D sampled under clock initializes Q. Native capture and closed-slave hold measured; autonomous sequencer layout not yet built.'}
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);complete=bool(run.returncode==0 and w.shape[1]==1+len(nodes) and np.isfinite(w).all() and abs(w[-1,0]-8e-6)<1e-15 and 'aborted' not in log.lower());report['module_simulation_completed']=complete
  if complete:
   sample=lambda n,us:float(np.interp(us*1e-6,w[:,0],w[:,1+nodes.index(n)]))
   results=[]
   for tag,_ in cases:
    wanted=[0]*6 if tag=='zero' else [1]*6 if tag=='one' else [1,0,1,0,1,0]
    after=[sample(f'v(q_{tag})',us) for us in [2.95,3.95,4.95,5.95,6.95,7.95]]
    # During PHIA, toggling D must not propagate through closed slave.
    hold=[sample(f'v(q_{tag})',us) for us in [3.4,4.4,5.4,6.4,7.4]]
    hold_wanted=wanted[:-1]
    correct=lambda vals,bits:all(v>2.9 if b else v<.4 for v,b in zip(vals,bits))
    results.append({'case':tag,'expected_captured_bits':wanted,'q_after_handoffs_v':after,'q_during_next_master_phase_v':hold,'capture_pass':correct(after,wanted),'closed_slave_hold_pass':correct(hold,hold_wanted)})
   report['cases']=results;report['all_capture_hold_pass']=all(c['capture_pass'] and c['closed_slave_hold_pass'] for c in results)
 except Exception as e:report['postprocess_error']=str(e)
 report['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in report.items() if k!='sha256'}},indent=2))
 assert report['module_simulation_completed']
if __name__=='__main__':main()
