"""Check the extracted control hierarchy using characterized sticky-join contracts.
This is logical composition evidence; it does not simulate transistor timing.
"""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_global_bin_barrier26_v2';d=BASE/'layout'/cell;files={Path(__file__)}
 for fn in ['qualification.json','flat_cap_qualification.json','abstract_qualification.json']:
  p=d/fn;q=json.loads(p.read_text());files.add(p)
  for n,h in q['sha256'].items():
   f=d/n if fn=='qualification.json' else ROOT/n
   if f.suffix!='.ext':assert sha(f)==h,n
 for i in range(3):
  p=BASE/'results'/f'gf180_bin_completion_join2_case{i}_src1863eea8e515.json';r=json.loads(p.read_text());assert r['module_simulation_completed'] and r['all_join_cases_pass'];files.add(p)
  for n,h in r['sha256'].items():
   if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
 p=d/(cell+'.spice');files.add(p);s=p.read_text().replace('\n+',' ')
 def sub(name):return re.search(r'(?ms)^\.subckt\s+'+name+r'\s+([^\n]+)\n(.*?)^\.ends',s).groups()
 pins,body=sub('gf180_bin_completion_join2_v1');pins=pins.split();topports,body=sub(cell);rows=[x.split() for x in body.splitlines() if x.startswith('X')];assert len(rows)==25 and all(x[-1]=='gf180_bin_completion_join2_v1' for x in rows)
 joins={x[0]:dict(zip(pins,x[1:-1])) for x in rows};assert all(len(x)==len(pins)+2 for x in rows)
 leaves=[f'ACTOR_DONE{i}' for i in range(25)]+['QUEUE_DRAINED'];drivers={j['COMPLETE']:k for k,j in joins.items()};assert len(drivers)==25 and 'COMPLETE' in drivers
 def sources(net,stack=()):
  if net in leaves:return [net],0
  assert net in drivers and net not in stack,net
  j=joins[drivers[net]];a,da=sources(j['TOKEN_A'],stack+(net,));b,db=sources(j['TOKEN_B'],stack+(net,));return a+b,1+max(da,db)
 coverage,depth=sources('COMPLETE');assert sorted(coverage)==sorted(leaves) and depth==5
 def run(tag,events,checks):
  seen={k:[False,False] for k in joins};inputs={n:False for n in leaves};clear=True;trace=[]
  for tick in range(max(checks)+1):
   for n,v in events.get(tick,{}).items():
    if n=='CLEAR':clear=v
    else:inputs[n]=v
   previous={j['COMPLETE']:all(seen[k]) and not clear for k,j in joins.items()};nextseen={}
   for k,j in joins.items():
    nextseen[k]=[False,False] if clear else [seen[k][i] or inputs.get(j[p],previous.get(j[p],False)) for i,p in enumerate(['TOKEN_A','TOKEN_B'])]
   seen=nextseen;complete=all(seen[drivers['COMPLETE']]) and not clear
   if tick in checks:trace.append({'capture_cycle':tick,'complete':complete,'expected':checks[tick],'pass':complete==checks[tick]})
  return {'case':tag,'checks':trace,'pass':all(t['pass'] for t in trace)}
 # Three bounded protocol records; cycles are abstract captures, not measured seconds.
 e={2:{'CLEAR':False},3:{n:True for n in leaves[:-1]},12:{'QUEUE_DRAINED':True},22:{n:False for n in leaves},23:{'CLEAR':True},26:{'CLEAR':False},27:{n:True for n in leaves}}
 cases=[run('late_queue_then_clear_then_second_bin',e,{1:False,10:False,18:True,24:False,25:False,33:True,40:True})]
 e={2:{'CLEAR':False},3:{n:True for n in leaves if n!='ACTOR_DONE17'},20:{'ACTOR_DONE17':True}}
 cases.append(run('one_missing_actor_blocks_complete',e,{1:False,15:False,19:False,26:True,32:True}))
 e={2:{'CLEAR':False},3:{'QUEUE_DRAINED':True}}
 for i,n in enumerate(reversed(leaves[:-1])):e[4+i]={n:True}
 cases.append(run('queue_first_reverse_actor_arrival',e,{8:False,27:False,34:True,40:True}))
 passed=all(c['pass'] for c in cases)
 rp=BASE/'results/gf180_global_bin_barrier26_v2_characterized_join_composition.json';assert not rp.exists()
 r={'control_composition_completed':True,'all_logical_composition_checks_pass':passed,'simulation_level':'extracted_hierarchical_connectivity_with_characterized_join_contract','native_join_count':25,'covered_leaves':coverage,'maximum_join_depth':depth,'cases':cases,'scope':'Actual qualified extracted parent connectivity composed using the sticky seen-A/seen-B and CLEAR contract supported by three existing native92MOS join transient cases. All26 leaves occur exactly once. Three abstract capture-cycle protocol records; not transistor or RC simulation, not calibrated clock timing, and not native startup/clock-distribution/metastability proof. Preserves the2300MOS native layout; does not replace analog numerical state with digital state. Full native parent transient remains incomplete after bounded timeout and failed switch-simulator startup attempts.','native_SPICE_transient_completed':False,'full_5ms_population_service_accepted':False,'full_chip_layout_complete':False,'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='sha256'},indent=2));assert passed
if __name__=='__main__':main()
