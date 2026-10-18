"""Native pulse termination guard on actual routed weight-duration comparator."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_bin_commit_controller_v1';phase='gf180_nonoverlap_phase_pair_v2';guard='gf180_pulse_termination_guard_v2';inv='gf180_phase_inverter_fullroute';tg='gf180_fixed_body_tg_quarter_shorttracks';mim='gf180_mim_5x5_ports_routed'
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
 stem='gf180_bin_commit_controller_case'+str(case_index)+'_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat')
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();width=1.609384125256789
 lines=['Native extracted interlocked two-phase generator',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vcmd command_source 0 PULSE(0 3.3 .2u .01u .01u .49u 1u)']
 lines +=[f'Xclockb command_source commandb vdd 0 {inv}',f'Xclock commandb command vdd 0 {inv}']
 request='PWL(0 0 1.29u 0 1.3u 3.3 1.79u 3.3 1.8u 0 14u 0)'
 reset='PWL(0 3.3 .99u 3.3 1u 0 14u 0)'
 abort='PWL(0 3.3 .99u 3.3 1u 0 4.99u 0 5u 3.3 5.99u 3.3 6u 0 14u 0)'
 complete='PWL(0 0 6.29u 0 6.3u 3.3 14u 3.3)'
 cases=[('idle','0',reset,'0'),('wait_then_complete',request,reset,complete),('reset_while_waiting',request,abort,complete)][case_index:case_index+1];nodes=[]
 for tag,req,rst,done in cases:
  for name,wave in [('start',req),('reset',rst),('complete',done)]:lines +=[f'V{name}_{tag} {name}_source_{tag} 0 {wave}',f'X{name}b_{tag} {name}_source_{tag} {name}b_{tag} vdd 0 {inv}',f'X{name}_{tag} {name}b_{tag} {name}_{tag} vdd 0 {inv}']
  lines +=[f'Xseq_{tag} command reset_{tag} start_{tag} complete_{tag} vdd 0 ready_{tag} age_{tag} beta_{tag} accum_{tag} detect_{tag} resetstate_{tag} inhibit_{tag} adapt_{tag} done_{tag} {cell}']
  nodes +=[f'v({p}_{tag})' for p in ['ready','age','beta','accum','detect','resetstate','inhibit','adapt','done']]
 lines +=['.control','set numdgt=15','tran .001u 14u 0 .002u uic','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 report={'module_simulation_completed':False,'simulator_returncode':run.returncode,'generated_cache_changes':cache_changes,'scope':'Actual306MOS native bin-control sequencer, flat extracted1615 nonnegative routing branches. One native-driver case per bounded run: idle, holdACCUM untilCOMPLETE, synchronous reset while waiting.1MHz control clock, common fixed solver tolerances. Order AGE,BETA,ACCUM,DETECT,RESET_STATE,INHIBIT,ADAPT,DONE follows original-float forward contract. ACCUM is a held level; other outputs are mutually exclusive strobes. COMPLETE is an external already-matched-bin upstream token: this module does not implement DAG join or bin-ID matching. No connected analog beta/energy/adaptation/inhibition modules or population5ms/full-chip acceptance.'}
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);complete=bool(run.returncode==0 and w.shape[1]==1+len(nodes) and np.isfinite(w).all() and abs(w[-1,0]-14e-6)<1e-15 and 'aborted' not in log.lower());report['module_simulation_completed']=complete
  if complete:
   t=w[:,0];results=[];sample=lambda n,us:float(np.interp(us*1e-6,t,w[:,1+nodes.index(n)]))
   def edges(y,up):
    ii=np.where(((y[:-1]<1.65)&(y[1:]>=1.65) if up else (y[:-1]>=1.65)&(y[1:]<1.65))&(t[:-1]>=1e-6))[0]
    return [float(t[i]+(1.65-y[i])*(t[i+1]-t[i])/(y[i+1]-y[i])) for i in ii]
   for tag,_,_,_ in cases:
    phases=['age','beta','accum','detect','resetstate','inhibit','adapt','done'];ys=[w[:,1+nodes.index(f'v({p}_{tag})')] for p in phases];rr=[edges(y,True) for y in ys];ff=[edges(y,False) for y in ys];counts=[len(r) for r in rr];wanted=[0]*8 if tag=='idle' else [1,1,1,0,0,0,0,0] if tag=='reset_while_waiting' else [1]*8
    overlap=0.
    for i in np.where(t[:-1]>=1e-6)[0]:
     cuts=[0.,1.]
     for k,y in enumerate(ys):
      if k==2:continue
      if y[i+1]!=y[i]:
       c=(1.65-y[i])/(y[i+1]-y[i])
       if 0<c<1:cuts.append(c)
     cuts=sorted(set(cuts))
     for a,b in zip(cuts,cuts[1:]):
      mid=(a+b)/2
      if sum(y[i]+mid*(y[i+1]-y[i])>=1.65 for k,y in enumerate(ys) if k!=2)>1:overlap+=(b-a)*(t[i+1]-t[i])
    order=sorted([(r,p) for p,rises in zip(phases,rr) for r in rises]);expected_order=[] if tag=='idle' else phases[:3] if tag=='reset_while_waiting' else phases
    ready_end=sample(f'v(ready_{tag})',13.9)
    results.append({'case':tag,'strobe_rising_edges_s':dict(zip(phases,rr)),'strobe_falling_edges_s':dict(zip(phases,ff)),'strobe_counts':counts,'expected_counts':wanted,'observed_order':[p for _,p in order],'total_multiple_pulsed_controls_high_ns':float(overlap*1e9),'ready_end_v':ready_end,'accum_wait_level_v':sample(f'v(accum_{tag})',4.5),'detect_before_complete_v':sample(f'v(detect_{tag})',6.0),'sequencing_pass':bool(counts==wanted and [p for _,p in order]==expected_order and overlap<1e-15 and ready_end>2.9 and (tag=='idle' or sample(f'v(accum_{tag})',4.5)>2.9) and (tag!='wait_then_complete' or (len(rr[3])==1 and rr[3][0]>6.3e-6)) and sample(f'v(detect_{tag})',6.0)<.4)})
   report['cases']=results;report['all_sequencing_pass']=all(c['sequencing_pass'] for c in results)
 except Exception as e:report['postprocess_error']=str(e)
 report['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in report.items() if k!='sha256'}},indent=2))
 assert report['module_simulation_completed']
if __name__=='__main__':main()
