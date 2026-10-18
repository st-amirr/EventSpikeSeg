"""Qualify one actor integration parent, never whole-model SPICE."""
from pathlib import Path
import re,json,hashlib,subprocess,struct
from assemble_gf180_full_capacity_storage_gds_v2 import records,rec
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';D=B/'assembly/full25_physical_candidate_v6';Q=D/'verification/actor_00_v4';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not Q.exists();Q.mkdir(parents=True);mf=D/'physical_assembly.json';m=json.loads(mf.read_text());a=m['actor_regions'][0];root=a['gds_cell'];gds=D/'eventspikeseg140k_physical_candidate_v6.gds';rs=list(records(gds.read_bytes()));first=next(i for i,(t,d,v,b) in enumerate(rs) if t==5);prefix=b''.join(b for t,d,v,b in rs[:first]);cells={};refs={};body=b'';name=None
 for t,d,v,b in rs[first:]:
  if t==5:body=b'';children=set()
  body+=b
  if t==6:name=v.rstrip(b'\0').decode()
  if t==18:children.add(v.rstrip(b'\0').decode())
  if t==7:cells[name]=body;refs[name]=children
 needed=set()
 def visit(n):
  if n in needed:return
  needed.add(n)
  for child in refs[n]:visit(child)
 visit(root);subset=Q/'actor_00_native_geometry.gds';subset.write_bytes(prefix+b''.join(cells[n] for n in sorted(needed))+rec(4,0))
 pinmap={(e.split('.',1)[0],e.split('.',1)[1]):net['net'] for net in m['local_pin_nets'] if net['actor']==a['actor'] for e in net['endpoint_pins']};labels=[];pos=None;istext=False
 for t,d,v,b in records(cells[root]):
  if t==12:istext=True
  if t==16 and istext:pos=struct.unpack('>2i',v)
  if t==25 and istext:labels.append((v.rstrip(b'\0').decode(),pos))
  if t==17:istext=False
 ports=[s for s,xy in labels];assert len(ports)==len(set(ports));pinmap.update({tuple(s.split('__',1)):s for s in ports if '__' in s});definitions='';seen=set();inputs={Path(__file__),mf,gds,subset}
 for p in a['modules']:
  c=p['cell']
  if c in seen:continue
  seen.add(c);d=B/'layout'/c;ng=d/(c+'.gds');sp=d/(c+'.spice');ns={v.rstrip(b'\0').decode():'N'+sha(ng)[:8]+'_'+hashlib.sha256(v.rstrip(b'\0')).hexdigest()[:16] for t,dt,v,b in records(ng.read_bytes()) if t==6};s=sp.read_text()
  for old in sorted(ns,key=len,reverse=True):s=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(old)+r'(?![A-Za-z0-9_])',ns[old],s)
  definitions+=s+'\n';inputs.update([sp,ng,d/'qualification.json'])
 reference=definitions+'.subckt reference '+' '.join(ports)+'\n'
 for p in a['modules']:
  c=p['cell'];d=B/'layout'/c;q=json.loads((d/'qualification.json').read_text());ng=d/(c+'.gds');cn='N'+sha(ng)[:8]+'_'+hashlib.sha256(c.encode()).hexdigest()[:16];nodes=[pinmap.get((p['instance'],pin),'internal__'+p['instance']+'__'+pin) for pin in q['ports']];reference+='X'+p['instance']+' '+' '.join(nodes)+' '+cn+'\n'
 reference+='.ends\n';rp=Q/'reference.spice';rp.write_text(reference);inputs.add(rp)
 pd=B/'pdk/gf180_open_pdks_source/gf180mcu/gf180mcuD';t='gds read /workspace/'+subset.relative_to(R).as_posix()+'\nload '+root+'\n'
 for i,(port,(x,y)) in enumerate(labels,1):t+=f'box values {x/1000:.3f}um {y/1000:.3f}um {x/1000:.3f}um {y/1000:.3f}um\nport make {i}\n'
 t+='drc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save parent.feedback\next2spice lvs\next2spice subcircuit top on\next2spice scale off\next2spice -o parent.spice\nquit -noprompt\n';tp=Q/'native_parent_check.tcl';tp.write_text(t);inputs.add(tp)
 cmd=['docker','run','--rm','--network','none','--memory','2g','--cpus','2','-i','--volume',f'{R}:/workspace','--workdir','/workspace/'+Q.relative_to(R).as_posix(),'--entrypoint','timeout','eventspikeseg:analog-gf180-layout','120','magic','-dnull','-noconsole','-rcfile','/workspace/'+(pd/'libs.tech/magic/gf180mcuD.magicrc').relative_to(R).as_posix()];p=subprocess.run(cmd,input=t,capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=Q/'native_parent_check.log';lp.write_text(log);inputs.add(lp);drc=re.search(r'Total DRC errors found:\s*(\d+)',log);report=dict(actor=a['actor'],top_cell=root,parent_native_command_returncode=p.returncode,parent_native_command_completed=p.returncode==0,full_parent_drc_count=int(drc[1]) if drc else None,parent_native_extraction_written=(Q/'parent.spice').exists(),independent_connectivity_accepted=False,parent_nominal_simulation_completed=False,full_chip_layout_complete=False,scope='One real native actor integration parent from combined physical candidate: first64resident membranes, event/bin controllers, signed duration/injection bindings and selected decision/reset/beta phases. No global capacity flattening or fullmodel SPICE. Child module results do not qualify the new parent.120s/2CPU/2GB first physical check. Every generated parent wire label declared as a fixed named debug/interface port only for independent connectivity comparison; no new geometry from port declarations.',sha256={p.relative_to(R).as_posix():sha(p) for p in inputs});(Q/'qualification_attempt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='sha256'},indent=2))
if __name__=='__main__':main()
