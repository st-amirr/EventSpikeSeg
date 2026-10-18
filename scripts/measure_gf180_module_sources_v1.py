"""Power characterization using independent copies of ideal fixture voltage sources.
This avoids added ideal-wire current constraints; native device/phase behavior is unchanged.
"""
from pathlib import Path
import json,re,time,subprocess,argparse,concurrent.futures
import measure_gf180_module_consumption_v1 as m
R=m.R;B=m.B;O=m.O
def prepare(j):
 src=R/j['deck'];s=m.unfold(src.read_text());report=R/j['source_report'] if j.get('source_report') else None
 if report:
  q=json.loads(report.read_text());assert q['sha256'].get(m.rel(src))==m.sha(src)
 defs={a[1].lower():a[2].split() for a in re.finditer(r'(?mi)^\.subckt\s+(\S+)\s+(.+)$',s)};tran=re.search(r'(?mi)^\.?tran\s+(.+)$',s)[1];j['expected_horizon_s']=m.scalar(tran.split()[1]);s=re.sub(r'(?mis)^\.control\s*\n.*?^\.endc\s*\n','',s);s=re.sub(r'(?mi)^\.(save|tran|end)\b.*\n?','',s)
 # Fixture cloning leaves native devices unchanged. Optional fast research solver is explicit.
 if j.get('fast'):
  s=re.sub(r'(?mi)^(\.options)(?![^\n]*\bklu\b)',r'\1 klu',s);s=re.sub(r'(?i)reltol=\S+','reltol=1e-4',s);s=re.sub(r'(?i)vntol=\S+','vntol=1e-7',s)
  bits=tran.split();mx=min(j['expected_horizon_s']/1000,50e-6)
  if len(bits)>=4:bits[3]=str(mx)
  else:bits+=['0',str(mx)]
  tran=' '.join(bits)
 level=0;sources={}
 for l in s.splitlines():
  if l.lower().startswith('.subckt'):level+=1
  if l.lower().startswith('.ends'):level-=1
  a=l.split()
  if level==0 and a and a[0][0].lower()=='v' and len(a)>=4:
   if a[2].lower() in ['0','gnd']:sources[a[1].lower()]={'name':a[0],'value':' '.join(a[3:])}
 target={v.lower() for v in j['targets']};lines=[];inst=[];seen=set();level=0
 for l in s.splitlines():
  if l.lower().startswith('.subckt'):level+=1
  if l.lower().startswith('.ends'):level-=1
  a=l.split()
  if level==0 and a and a[0].lower() in target:
   ports=defs[a[-1].lower()];nodes=a[1:-1];assert len(ports)==len(nodes);groups={};new=[];mi=len(inst)
   for port,node in zip(ports,nodes):
    key=node.lower()
    if key in sources:
     if key not in groups:
      ni=len(groups);name=f'Vcp_{mi}_{ni}';inner=f'cp_{mi}_{ni}';g={'ports':[],'external_node':node,'internal_node':inner,'meter':name,'source_value':sources[key]['value']};groups[key]=g;lines.append(f'{name} {inner} 0 '+g['source_value'])
     groups[key]['ports'].append(port);new.append(groups[key]['internal_node'])
    else:new.append(node)
   lines.append(' '.join([a[0],*new,a[-1]]));inst.append({'instance':a[0],'cell':a[-1],'source_groups':list(groups.values()),'unmeasured_ports':[{'port':p,'node':n} for p,n in zip(ports,nodes) if n.lower() not in sources and n.lower() not in ['0','gnd','vss']]});seen.add(a[0].lower())
  else:lines.append(l)
 assert seen==target,(j['tag'],seen,target)
 # Initial conditions on state outputs remain connected exactly as before.
 save=[]
 for a in inst:
  for g in a['source_groups']:save.extend(['v('+g['internal_node']+')','i('+g['meter']+')'])
 for g in inst:
  for p in g['unmeasured_ports']:save.append('v('+p['node']+')')
 lines+=['.save '+' '.join(dict.fromkeys(save)),'.tran '+tran,'.end'];d=O/(j['tag']+'_sources');d.mkdir(exist_ok=False);deck=d/'bench.spice';deck.write_text('\n'.join(lines)+'\n',encoding='utf-8');j.update(instances=inst,measurement_deck=m.rel(deck),source_deck_sha256=m.sha(src));return j,d

def run(j):
 j,d=prepare(j);start=time.monotonic();a=['docker','run','--rm','--network','none','--memory','1g','--cpus','1','--volume',str(R)+':/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','180','ngspice','-b','-r','/workspace/'+m.rel(d/'waveforms.raw'),'/workspace/'+j['measurement_deck']];r=subprocess.run(a,capture_output=True,text=True,timeout=195);(d/'ngspice.log').write_text(r.stdout+r.stderr,encoding='utf-8');out={'completed':False,'returncode':r.returncode,'elapsed_wall_s':time.monotonic()-start,'job':j,'supply_V':3.3,'temperature_C':27,'corner':'typical','scope':'Each measured module receives independent ideal fixture voltage sources with exactly the original waveforms/levels. Native devices, loads and topology unchanged. Fast jobs use KLU,reltol1e-4,vntol1e-7 and adaptive maximum step horizon/1000 capped50us; original input edges are retained. Other jobs retain original solver/tolerances. Source energy includes the module current only, excluding other instances and shared driver/reference generation. Energy at ports supplied by native phase drivers, external current-source masters and output/state ports is not included unless explicitly listed. Supply/input energy is not total internal dissipation. No full-chip extrapolation.','instances':[]};raw=d/'waveforms.raw'
 if raw.exists() and b'Binary:\n' in raw.read_bytes():
  w=m.Trace(raw);out.update(last_time_s=w.t[-1],points=len(w.t),completed=r.returncode==0 and abs(w.t[-1]-j['expected_horizon_s'])<1e-12 and 'aborted' not in (r.stdout+r.stderr).lower())
  if out['completed']:
   for a in j['instances']:
    supply=[0.0]*len(w.t);powers=[]
    for g in a['source_groups']:
     v=w.col('v('+g['internal_node']+')');i=w.col('i('+g['meter']+')');p=[-x*y for x,y in zip(v,i)];powers.append((g,p))
     if any(x.lower()=='vdd' for x in g['ports']):supply=[x+y for x,y in zip(supply,p)]
    e={'instance':a['instance'],'cell':a['cell'],'unmeasured_ports':a['unmeasured_ports'],'windows':[]}
    for name,lo,hi in j['windows']:
     lo=w.t[0] if lo is None else max(lo,w.t[0]);hi=w.t[-1] if hi is None else hi;dt=hi-lo;pe=[{'ports':g['ports'],'external_node':g['external_node'],'signed_source_energy_J':m.integral(w.t,p,lo,hi),'positive_source_energy_J':m.integral(w.t,p,lo,hi,True)} for g,p in powers];energy=m.integral(w.t,supply,lo,hi)
     e['windows'].append({'name':name,'start_s':lo,'end_s':hi,'duration_s':dt,'VDD_energy_J':energy,'VDD_mean_power_W':energy/dt,'measured_source_net_energy_J':sum(x['signed_source_energy_J'] for x in pe),'measured_source_positive_energy_J':sum(x['positive_source_energy_J'] for x in pe),'ports':pe})
    out['instances'].append(e)
 out['sha256']={m.rel(p):m.sha(p) for p in [R/j['measurement_deck'],d/'ngspice.log',raw] if p.exists()};(d/'consumption.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');return {'tag':j['tag'],'completed':out['completed'],'seconds':round(out['elapsed_wall_s'],2),'last_time_s':out.get('last_time_s')}
def main():
 p=argparse.ArgumentParser();p.add_argument('--only',nargs='+',required=True);p.add_argument('--workers',type=int,default=2);p.add_argument('--fast',action='store_true');args=p.parse_args();js=[j for j in m.jobs() if j['tag'] in args.only]
 for j in js:
  if args.fast:j['tag']+='_fast';j['fast']=True
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
  fs={ex.submit(run,j):j for j in js}
  for f in concurrent.futures.as_completed(fs):
   try:print(json.dumps(f.result()),flush=True)
   except Exception as e:print(json.dumps({'tag':fs[f]['tag'],'error':str(e)}),flush=True)
if __name__=='__main__':main()
