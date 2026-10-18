"""Publish native bias-mirror characterization while retaining measured ratio errors."""
from pathlib import Path
import argparse,datetime,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cell',required=True);ap.add_argument('--revision',type=int,required=True);ap.add_argument('--role',required=True);ap.add_argument('--pass-key',required=True);ap.add_argument('--reports',nargs=3,required=True);args=ap.parse_args()
 old=BASE/'assembly'/f'article_module_catalog_v{args.revision-1}.json';cp=BASE/'assembly'/f'article_module_catalog_v{args.revision}.json';assert not cp.exists()
 cat=json.loads(old.read_text());assert all(sha(ROOT/n)==h for n,h in cat['sha256'].items());assert args.cell not in [e['cell'] for e in cat['modules']]
 folder=BASE/'layout'/args.cell;qs=[folder/n for n in ['qualification.json','flat_cap_qualification.json','abstract_qualification.json']];q,fq,aq=[json.loads(p.read_text()) for p in qs]
 assert q['magic_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique']
 assert fq['flat_lvs_unique'] and not fq['negative_aggregate_branches'] and aq['physical_ports_and_size_verified']
 reports=[ROOT/n for n in args.reports];rs=[json.loads(p.read_text()) for p in reports]
 for r in rs:r['cases']=[{'case':f"master_current_{r['reference_current_a']}_A",'startup_at100us':r['startup_at100us']}]
 assert all(r['module_simulation_completed'] and r[args.pass_key] for r in rs)
 for r in [fq,aq,*rs]:
  for n,h in r['sha256'].items():
   if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
 files=[*qs,folder/(args.cell+'.gds'),folder/(args.cell+'.lef'),folder/(fq['flat_subcircuit']+'_cap.spice'),*reports]
 entry={'role':args.role,'cell':args.cell,'ports':q['ports'],'bbox_um':q['bbox_um'],'mos_count':q['mos_count'],'module_layout_and_nominal_simulation_artifacts_complete':True,'nominal_characterization_cases_complete':True,'views':{p.name:rel(p) for p in files},'limitations':q['scope']+' Three nominal cases completed. PMOS at100us gives1.018..1.037 times reference; short-channel NMOS gives2.217..3.317, so unity mirror accuracy is not accepted. Characterization geometry; do not replicate as dense storage area.'}
 cat['modules'].append(entry);cat['revision']=args.revision;cat['previous_catalog']=rel(old);cat['sha256'].update({rel(p):sha(p) for p in files});cat['next_assembly']='Complete graph-wide bin barrier/interconnect, shared references, analog adaptation/RMS/inhibition and class readout, then compact dense tile and full25actor layout. Local control checks do not establish analog model accuracy or population5ms service.'
 cp.write_text(json.dumps(cat,indent=2)+'\n')
 audit={'cell':args.cell,'catalog':rel(cp),'module_artifact_sets':len(cat['modules']),'characterization_assemblies':len(cat['characterization_assemblies']),'nominal_cases':[r['cases'][0] for r in rs],'all_nominal_characterization_cases_complete':True,'scope':entry['limitations'],'original_float_accuracy_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_layout_complete':False,'sha256':{rel(p):sha(p) for p in [cp,*files,Path(__file__)]}}
 rp=BASE/'results'/(args.cell+'_article_boundary.json');assert not rp.exists();rp.write_text(json.dumps(audit,indent=2)+'\n')
 docs=[ROOT/'docs'/n for n in ['AGENTS.md','ACTIVE_TASKS.md','ARCHITECTURE.md','DECISIONS.md','RESULTS.md','PROGRESS.md','project_spec.yaml']];stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');zp=BASE/'documentation_history'/('project_docs_before_'+args.cell+'_'+stamp+'.zip')
 with zipfile.ZipFile(zp,'x',zipfile.ZIP_DEFLATED) as z:
  for p in docs:z.writestr(rel(p),p.read_bytes())
 zp.with_suffix('.json').write_text(json.dumps({'archive_sha256':sha(zp),'files':{rel(p):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in docs}},indent=2)+'\n')
 def write(p,b):
  tmp=p.with_suffix('.tmp');tmp.write_bytes(b);tmp.replace(p)
 def insert(name,text):
  p=ROOT/'docs'/name;b=p.read_bytes();i=b.index(b'\n## ');write(p,b[:i]+text.encode('utf-8')+b[i:])
 n=len(cat['modules']);m=len(cat['characterization_assemblies']);cases=', '.join(r['cases'][0]['case'] for r in rs)
 insert('RESULTS.md',f"\n## {args.role} characterization milestone - 2026-10-10\n\n[Module boundary](../{rel(rp)}) records {args.cell}: {q['mos_count']} native MOS, full DRC0, source and GDS-reimport LVS, flat capacitive extraction and actual LEF. Nominal extracted direction/finite-output cases complete: {cases}. Catalog revision{args.revision} now contains{n} module artifact sets and{m} characterization assemblies.\n\n{entry['limitations']} Full-chip layout, analog accuracy and population5ms service remain incomplete.\n")
 insert('PROGRESS.md',f"\nLocal {args.role} milestone: {args.cell}, three native extracted cases pass, catalog revision{args.revision} ({n} modules/{m} characterization assemblies). Full goal incomplete. Exact prior docs archived at `{rel(zp)}`.\n")
 p=ROOT/'docs/ACTIVE_TASKS.md';b=p.read_bytes();b=b.replace(f'article_module_catalog_v{args.revision-1}.json'.encode(),cp.name.encode()).replace(f'catalog revision{args.revision-1}'.encode(),f'catalog revision{args.revision}'.encode());a=b.index(b'| Job status |');z=b.index(b'\n',a);b=b[:a]+f'| Job status | {args.cell} layout and three nominal characterization cases complete; {n} module sets/{m} assemblies; next remaining support and full assembly |'.encode()+b[z:]
 # Keep all historical paragraphs intact; update current summary rows and package count.
 import re
 b=re.sub(rb'\*\*Physical module completion and assembly\.\*\* [^\r\n]+',f'**Physical module completion and assembly.** {n} reusable GF180 module artifact sets and{m} routed characterization assemblies have physical checks and completed nominal simulations. Complete neuron functionality, dense arrays and full-chip layout remain unfinished.'.encode(),b,count=1)
 b=re.sub(rb'\| Latest evidence \|[^\r\n]+',f'| Latest evidence | {n} reusable module artifact sets and{m} characterization assemblies in catalog revision{args.revision}; known analog imperfections retained |'.encode(),b,count=1)
 b=re.sub(rb'1\. (?:Twelve|[0-9]+) reusable physical modules[^\r\n]+',f'1. {n} reusable physical modules and{m} characterization assemblies have layout checks and nominal extracted simulations recorded in catalog revision{args.revision}. Preserve measured imperfections; no repeated precision sweep.'.encode(),b,count=1);write(p,b)
 insert('ARCHITECTURE.md',f'\n## {args.role} physical interface - 2026-10-10\n\n{q["scope"]} Nominal local extracted cases now recorded in catalog revision{args.revision}; connected analog stages and global completion remain separate.\n')
 p=ROOT/'docs/project_spec.yaml';b=p.read_bytes();head,tail=b.split(b'\ndocument:',1);head=head.replace(old.name.encode(),cp.name.encode());head=head.replace(b'  evidence: artifacts/analog_asic/results/gf180_prebiased_autonomous_event_boundary.json',b'  evidence: '+rel(rp).encode());head=head.replace(b'    report: artifacts/analog_asic/results/gf180_prebiased_autonomous_event_boundary.json',b'    report: '+rel(rp).encode());head=re.sub(rb'  live_sessions: [^\r\n]+',b'  live_sessions: []',head,count=1);head=re.sub(rb'    status: [^\r\n]+',f'    status: {n}_modules_{m}_assemblies_latest_bias_mirror_cases_complete'.encode(),head,count=1);write(p,head+b'\ndocument:'+tail)
 print(json.dumps({'catalog':rel(cp),'boundary':rel(rp),'modules':n,'assemblies':m},indent=2))
if __name__=='__main__':main()
