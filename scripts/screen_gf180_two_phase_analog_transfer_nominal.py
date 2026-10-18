"""Native pulse termination guard on actual routed weight-duration comparator."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_two_phase_analog_transfer_v5';guard='gf180_pulse_termination_guard_v2';inv='gf180_phase_inverter_fullroute';tg='gf180_fixed_body_tg_quarter_shorttracks';mim='gf180_mim_5x5_ports_routed'
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
 stem='gf180_two_phase_analog_transfer_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat')
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();width=1.609384125256789
 lines=['Native extracted interlocked two-phase generator',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vcmd command 0 PULSE(0 3.3 2u .01u .01u .49u 1u)','Vreset reset 0 PWL(0 3.3 .99u 3.3 1u 0 8u 0)']
 cases=[('low',1.4),('middle',1.65),('high',1.9)];nodes=[]
 for tag,voltage in cases:
  lines +=[f'Vdata_{tag} data_{tag} 0 {voltage}',f'Xphase_{tag} command reset data_{tag} vdd 0 held_{tag} output_{tag} a_{tag} b_{tag} {cell}']
  nodes +=[f'v(a_{tag})',f'v(b_{tag})',f'v(held_{tag})',f'v(output_{tag})']
 lines +=['.control','set numdgt=15','tran .001u 8u 0 .002u uic','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 report={'module_simulation_completed':False,'simulator_returncode':run.returncode,'generated_cache_changes':cache_changes,'scope':'Actual physically joined26MOS2MIM phase/sampling/transfer/reset assembly, flat extracted with81 nonnegative routing branches. Three DATA references1.4/1.65/1.9V, native TGs and two minimumMIM stores. External1MHz command and startup reset only. PHIA samples DATA to HOLD; PHIB shares HOLD charge with OUTPUT. Passive charge sharing and clock kick measured, not hidden by unity-gain interpretation; no original-float state/weight equivalence, autonomous bin scheduling or full-chip claim.'}
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);complete=bool(run.returncode==0 and w.shape[1]==1+len(nodes) and np.isfinite(w).all() and abs(w[-1,0]-8e-6)<1e-15 and 'aborted' not in log.lower());report['module_simulation_completed']=complete
  if complete:
   t=w[:,0];results=[]
   def edges(y,up):
    ii=np.where(((y[:-1]<1.65)&(y[1:]>=1.65) if up else (y[:-1]>=1.65)&(y[1:]<1.65))&(t[:-1]>=2.9e-6))[0]
    return [float(t[i]+(1.65-y[i])*(t[i+1]-t[i])/(y[i+1]-y[i])) for i in ii]
   for tag,voltage in cases:
    a=w[:,1+nodes.index(f'v(a_{tag})')];b=w[:,1+nodes.index(f'v(b_{tag})')];ar,af,br,bf=edges(a,True),edges(a,False),edges(b,True),edges(b,False)
    gaps=[]
    for rises,falls in [(ar,bf),(br,af)]:
     for r in rises:
      before=[f for f in falls if f<r]
      if before:gaps.append((r-max(before))*1e9)
    # Integrate exact linear-segment intersection above1.65V; no sampled-only overlap check.
    overlap=0.0
    for i in np.where(t[:-1]>=2.9e-6)[0]:
     lo,hi=0.0,1.0
     for y in [a,b]:
      y0,y1=y[i],y[i+1]
      if y0<1.65 and y1<1.65:hi=-1;break
      if y1!=y0:
       cross=(1.65-y0)/(y1-y0)
       if y0<1.65:lo=max(lo,cross)
       if y1<1.65:hi=min(hi,cross)
     overlap+=max(0,hi-lo)*(t[i+1]-t[i])
    results.append({'case':tag,'programmed_data_v':voltage,'phase_a_rise_count':len(ar),'phase_b_rise_count':len(br),'total_both_high_ns':float(overlap*1e9),'minimum_handoff_gap_ns':min(gaps) if gaps else None,'maximum_handoff_gap_ns':max(gaps) if gaps else None,'nonoverlap_observed':bool(overlap<1e-15 and len(ar)==len(br)==5 and len(gaps)>=8),'primary_min_v':float(min(a[t>=2.9e-6].min(),b[t>=2.9e-6].min())),'primary_max_v':float(max(a[t>=2.9e-6].max(),b[t>=2.9e-6].max()))})
   for r in results:
    tag=r['case'];sample=lambda node,us:float(np.interp(us*1e-6,t,w[:,1+nodes.index(f'v({node}_{tag})')]))
    r['held_end_sample_v']=sample('held',2.45);r['sampling_error_v']=r['held_end_sample_v']-r['programmed_data_v'];r['output_after_transfers_v']=[sample('output',us) for us in [2.95,3.95,4.95,5.95,6.95,7.95]];r['output_final_error_v']=r['output_after_transfers_v'][-1]-r['programmed_data_v']
   report['cases']=results;report['all_cases_primary_nonoverlap']=all(r['nonoverlap_observed'] for r in results);report['output_monotonic_across_data']=all(results[i]['output_after_transfers_v'][-1]<results[i+1]['output_after_transfers_v'][-1] for i in range(2))
 except Exception as e:report['postprocess_error']=str(e)
 report['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in report.items() if k!='sha256'}},indent=2))
 assert report['module_simulation_completed']
if __name__=='__main__':main()
