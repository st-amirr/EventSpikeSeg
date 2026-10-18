"""Fresh GDS DRC then proven fast native flat connectivity extraction for corrected service."""
from pathlib import Path
import json,re,hashlib,struct,subprocess
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full_capacity_storage_gds_v2 import records,rec
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';D=B/'assembly/shared_reader_page1024_v1';Q=D/'verification/native_parent_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not Q.exists();Q.mkdir(parents=True);mf=D/'physical_partition.json';m=json.loads(mf.read_text());a=m['actor_regions'][0];root=a['gds_cell'];flat=root+'_flat';gds=D/'shared_reader_page1024.gds';prefix,cells=cells_read(gds.read_bytes());refs={n:{v.rstrip(b'\0').decode() for t,dt,v,b in records(blob) if t==18} for n,blob in cells.items()};needed=set()
 def visit(n):
  if n in needed:return
  needed.add(n)
  for c in refs[n]:visit(c)
 visit(root);subset=Q/'actor_00_native_geometry.gds';subset.write_bytes(prefix+b''.join(cells[n] for n in sorted(needed))+rec(4,0));labels=[]
 for e in elements(cells[root]):
  if e[0][0]!=12:continue
  name=next(v.rstrip(b'\0').decode() for t,dt,v,b in e if t==25);labels.append(name)
 assert len(labels)==len(set(labels)) and len(labels)==1056
 pinmap={(e.split('.',1)[0],e.split('.',1)[1]):net['net'] for net in m['local_pin_nets'] if net['actor']==a['actor'] for e in net['endpoint_pins']};pinmap.update({tuple(s.split('__',1)):s for s in labels if '__' in s});definitions=[];seen=set();inputs={Path(__file__),mf,gds,subset};qualified={}
 for p in a['modules']:
  c=p['cell']
  if c in seen:continue
  seen.add(c);d=B/'layout'/c;qp=d/'qualification.json';q=json.loads(qp.read_text());ng=d/(c+'.gds');sp=d/(c+'.spice');assert sha(ng)==q['sha256'][ng.name];qualified[c]=q;ns={v.rstrip(b'\0').decode():'N'+sha(ng)[:8]+'_'+hashlib.sha256(v.rstrip(b'\0')).hexdigest()[:16] for t,dt,v,b in records(ng.read_bytes()) if t==6};s=sp.read_text()
  for old in sorted(ns,key=len,reverse=True):s=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(old)+r'(?![A-Za-z0-9_])',ns[old],s)
  definitions.append(s);inputs.update([qp,ng,sp])
 reference='\n'.join(definitions)+'\n.subckt reference '+' '.join(labels)+'\n'
 for p in a['modules']:
  c=p['cell'];ng=B/'layout'/c/(c+'.gds');cn='N'+sha(ng)[:8]+'_'+hashlib.sha256(c.encode()).hexdigest()[:16];nodes=[pinmap.get((p['instance'],pin),'internal__'+p['instance']+'__'+pin) for pin in qualified[c]['ports']];reference+='X'+p['instance']+' '+' '.join(nodes)+' '+cn+'\n'
 reference+='.ends\n';rp=Q/'reference.spice';rp.write_text(reference);inputs.add(rp)
 t='drc off\ngds read /workspace/'+subset.relative_to(R).as_posix()+'\nload '+root+'\nputs "PHASE GDS imported"\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nputs "PHASE source DRC complete"\ndrc off\nflatten -dotoplabels '+flat+'\nload '+flat+'\nsave '+flat+'\nputs "PHASE flat saved"\nextract no capacitance\nextract no coupling\nextract no adjust\nextract no resistance\nextract all\nfeedback save parent.feedback\nputs "PHASE extraction complete"\next2spice lvs\next2spice hierarchy off\next2spice subcircuit top on\next2spice scale off\next2spice -o parent.spice\nputs "PHASE SPICE complete"\nquit -noprompt\n';tp=Q/'native_check.tcl';tp.write_text(t);inputs.add(tp);pd=B/'pdk/gf180_open_pdks_source/gf180mcu/gf180mcuD'
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','-i','--volume',f'{R}:/workspace','--workdir','/workspace/'+Q.relative_to(R).as_posix(),'--entrypoint','timeout','eventspikeseg:analog-gf180-layout','120','magic','-dnull','-noconsole','-rcfile','/workspace/'+(pd/'libs.tech/magic/gf180mcuD.magicrc').relative_to(R).as_posix()],input=t,capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=Q/'native_parent_check.log';lp.write_text(log);inputs.add(lp);drc=re.search(r'Total DRC errors found:\s*(\d+)',log)
 o=dict(actor=a['actor'],top_cell=flat,parent_native_command_returncode=run.returncode,parent_native_command_completed=run.returncode==0 and 'PHASE SPICE complete' in log,full_parent_drc_count=int(drc[1]) if drc else None,flat_drc_rerun=False,parent_native_extraction_written=(Q/'parent.spice').exists(),independent_connectivity_accepted=False,parent_nominal_simulation_completed=False,parasitic_capacitance_extraction_enabled=False,full_chip_layout_complete=False,scope='Shared1024state page actualGDS:sourcefullDRC thenflatten-dotoplabels,save and nativeconnectivity-only extraction.Actualimportedpartitionrootports,noportmutation. DATAconnections attach to qualified existingleftescapedDATA M4/M5 spines,not rawbankpads. NativeMOS/MIM/R allretained;parasiticC/coupling/adjust/resistance disabled. No redundantflatDRC after sourcefullDRC;prior methodtimings retained. Complete7847primitive reference graph proof stillrequired. Parentanalog/fullC and wholechipaccuracy/service remainopen.',sha256={p.relative_to(R).as_posix():sha(p) for p in inputs});(Q/'qualification_attempt.json').write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k!='sha256'},indent=2))
if __name__=='__main__':main()
