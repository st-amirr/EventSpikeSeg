"""Native extracted sticky completion-join arrival and clear characterization."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_bin_completion_join2_v1';phase='gf180_nonoverlap_phase_pair_v2';guard='gf180_pulse_termination_guard_v2';inv='gf180_phase_inverter_fullroute';tg='gf180_fixed_body_tg_quarter_shorttracks';mim='gf180_mim_5x5_ports_routed'
 files={Path(__file__)};texts=[];cache_changes=[]
 for name in [cell,inv]:
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
 case_index=int(sys.argv[1]);assert case_index in [0,1,2]
 stem='gf180_bin_completion_join2_case'+str(case_index)+'_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat')
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();width=1.609384125256789
 lines=['Native extracted interlocked two-phase generator',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vcmd command_source 0 PULSE(0 3.3 .2u .01u .01u .49u 1u)']
 lines +=[f'Xclockb command_source commandb vdd 0 {inv}',f'Xclock commandb command vdd 0 {inv}']
 reset='PWL(0 3.3 .99u 3.3 1u 0 13u 0)'
 first='PWL(0 0 1.29u 0 1.3u 3.3 2.29u 3.3 2.3u 0 3.29u 0 3.3u 3.3 4.19u 3.3 4.2u 0 13u 0)'
 later='PWL(0 0 5.29u 0 5.3u 3.3 6.29u 3.3 6.3u 0 13u 0)'
 clear='PWL(0 3.3 .99u 3.3 1u 0 4.29u 0 4.3u 3.3 5.29u 3.3 5.3u 0 13u 0)'
 a_after_clear='PWL(0 0 1.29u 0 1.3u 3.3 2.29u 3.3 2.3u 0 9.29u 0 9.3u 3.3 10.29u 3.3 10.3u 0 13u 0)'
 b_after_clear='PWL(0 0 6.29u 0 6.3u 3.3 7.29u 3.3 7.3u 0 13u 0)'
 cases=[('A_then_B',first,later,reset),('B_then_A',later,first,reset),('clear_stale_arrival',a_after_clear,b_after_clear,clear)][case_index:case_index+1];nodes=[]
 for tag,wa,wb,wclear in cases:
  for name,wave in [('tokena',wa),('tokenb',wb),('clear',wclear)]:lines +=[f'V{name}_{tag} {name}_source_{tag} 0 {wave}',f'X{name}b_{tag} {name}_source_{tag} {name}b_{tag} vdd 0 {inv}',f'X{name}_{tag} {name}b_{tag} {name}_{tag} vdd 0 {inv}']
  lines +=[f'Xjoin_{tag} command clear_{tag} tokena_{tag} tokenb_{tag} vdd 0 seena_{tag} seenb_{tag} complete_{tag} {cell}']
  nodes +=[f'v({p}_{tag})' for p in ['seena','seenb','complete']]
 lines +=['.control','set numdgt=15','tran .001u 13u 0 .002u uic','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 report={'module_simulation_completed':False,'simulator_returncode':run.returncode,'generated_cache_changes':cache_changes,'scope':'Native92MOS sticky completion join with extracted interconnect and native input drivers. Three nominal cases individually bounded: A-before-B with duplicate A, reverse ordering, and CLEAR discarding an old one-sided arrival. Single in-flight semantic bin contract; inputs held through capture, all old-bin tokens withdrawn before clear release. No tag comparison, asynchronous CDC proof, graph-wide barrier, analog model state or population5ms/full-chip acceptance.'}
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);complete=bool(run.returncode==0 and w.shape[1]==1+len(nodes) and np.isfinite(w).all() and abs(w[-1,0]-13e-6)<1e-15 and 'aborted' not in log.lower());report['module_simulation_completed']=complete
  if complete:
   t=w[:,0];results=[];sample=lambda n,us:float(np.interp(us*1e-6,t,w[:,1+nodes.index(n)]))
   for tag,_,_,_ in cases:
    samples={str(us):{p:sample(f'v({p}_{tag})',us) for p in ['seena','seenb','complete']} for us in [1.1,2.9,4.1,4.5,5.9,8.5,12.5]}
    high=lambda us,p:samples[str(us)][p]>2.9
    low=lambda us,p:samples[str(us)][p]<.4
    if tag=='clear_stale_arrival':ok=high(2.9,'seena') and low(2.9,'seenb') and low(2.9,'complete') and all(low(5.9,p) for p in ['seena','seenb','complete']) and high(8.5,'seenb') and low(8.5,'seena') and low(8.5,'complete') and all(high(12.5,p) for p in ['seena','seenb','complete']) and low(4.5,'complete')
    else:
     firstp='seena' if tag=='A_then_B' else 'seenb';secondp='seenb' if tag=='A_then_B' else 'seena'
     ok=high(2.9,firstp) and low(2.9,secondp) and low(2.9,'complete') and high(4.1,firstp) and low(4.1,'complete') and all(high(8.5,p) and high(12.5,p) for p in ['seena','seenb','complete'])
    results.append({'case':tag,'samples_v':samples,'join_pass':bool(ok)})
   report['cases']=results;report['all_join_cases_pass']=all(c['join_pass'] for c in results)
 except Exception as e:report['postprocess_error']=str(e)
 report['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in report.items() if k!='sha256'}},indent=2))
 assert report['module_simulation_completed']
if __name__=='__main__':main()
