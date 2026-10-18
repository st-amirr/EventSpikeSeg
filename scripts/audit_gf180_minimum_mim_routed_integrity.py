"""Audit the existing minimum-size MIM geometry and GDS port connectivity."""
import argparse,hashlib,json,re
from pathlib import Path
import probe_gf180_mos_gate_cap as flow

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report-name',default='gf180_minimum_mim_routed_gds_integrity.json');args=parser.parse_args()
 if not re.fullmatch(r'[A-Za-z0-9_]+\.json',args.report_name):raise ValueError('Expected report filename')
 source=Path(__file__);names=['gf180_mim_5x5_ports_routed'];sources={source};cases=[];target=flow.BASE/'results'/args.report_name
 if target.exists():raise ValueError('Preserve previous geometry audit')
 snapshot=flow.BASE/'tools/source_snapshots'/('audit_gf180_minimum_mim_integrity_'+digest(source)+'.py');snapshot.write_bytes(source.read_bytes());sources.add(snapshot)
 for cell in names:
  native=flow.BASE/'layout'/cell;qp=native/'qualification.json';q=json.loads(qp.read_text());sources.add(qp);before={native/n:sha for n,sha in q['sha256'].items()}
  if any(digest(f)!=sha for f,sha in before.items()):raise ValueError('Original physical-view provenance differs')
  sources.update(before);directory=flow.BASE/'verification/minimum_mim_integrity'/cell;directory.mkdir(parents=True,exist_ok=True);flow.OUT=directory
  preload=''
  for child in sorted(set(re.findall(r'^use\s+(\S+)\s+', (native/(cell+'.mag')).read_text(),re.M))):
   matches=[(flow.ROOT/n,h) for n,h in q.get('input_sha256',{}).items() if n.endswith('/'+child+'.mag')]
   if len(matches)!=1 or digest(matches[0][0])!=matches[0][1]:raise ValueError('Hierarchical child provenance differs')
   sources.add(matches[0][0]);preload+='load /workspace/'+matches[0][0].with_suffix('').relative_to(flow.ROOT).as_posix()+'\n'
  log=flow.magic(preload+'load /workspace/'+(native/cell).relative_to(flow.ROOT).as_posix()+'\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nquit -noprompt\n');lp=directory/'full_drc.log';lp.write_text(log);sources.add(lp);match=re.search(r'Total DRC errors found:\s*(\d+)',log)
  if not match:raise ValueError('Full DRC completion absent')
  oldlog=native/'extraction.log';export_problems=[]
  if oldlog.exists():sources.add(oldlog);export_problems=[int(n) for n in re.findall(r'(\d+) problems occurred',oldlog.read_text())]
  row={'cell':cell,'legacy_magic_drc_flag':q['magic_drc_count'],'full_cell_full_style_drc_count':int(match[1]),'legacy_export_problem_counts':export_problems,'gds_roundtrip_attempted':False,'gds_roundtrip_lvs_unique':False,'gds_roundtrip_drc_count':None,'original_views_preserved':False,'physical_layout_accepted':False}
  if not export_problems and not int(match[1]):
   row['gds_roundtrip_attempted']=True
   readlog=flow.magic('gds read /workspace/'+(native/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(directory/'readback.log').write_text(readlog);rdrc=re.search(r'Total DRC errors found:\s*(\d+)',readlog)
   lvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(native/(cell+'.spice')).relative_to(flow.ROOT).as_posix()+' '+cell,'/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out']);(directory/'netgen.log').write_text(lvs);sources.update(directory/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback'])
   row['gds_roundtrip_drc_count']=int(rdrc[1]) if rdrc else None;row['gds_roundtrip_lvs_unique']='Circuits match uniquely' in lvs;row['gds_roundtrip_extraction_feedback']=(directory/'roundtrip.feedback').read_text();row['physical_layout_accepted']=row['gds_roundtrip_drc_count']==0 and row['gds_roundtrip_lvs_unique'] and not row['gds_roundtrip_extraction_feedback']
   if cell.startswith('gf180_mim_5x5'):
    text=(directory/'roundtrip.spice').read_text();body=re.search(r'(?ms)^\.subckt\s+'+re.escape(cell)+r'\s+[^\n]*\n(.*?)^\.ends',text)
    caps=[line.split() for line in body[1].splitlines() if line.startswith('X') and 'cap_mim_2f0_m4m5_noshield' in line] if body else []
    connected=len(caps)==1 and set(caps[0][1:3])=={'P','M'}
    row['native_capacitor_exported_P_M_ports_connected_to_device']=connected
    row['physical_layout_accepted']=row['physical_layout_accepted'] and connected
  if any(digest(f)!=sha for f,sha in before.items()):raise ValueError('Original views changed during read-only integrity audit')
  row['original_views_preserved']=True;cases.append(row)
  result={'audit_completed':len(cases)==len(names),'imported_component_count':len(names),'audited_component_count':len(cases),'physical_layout_pass_count':sum(c['physical_layout_accepted'] for c in cases),'cases':cases,'legacy_presence_drc_lvs_flags_sufficient_for_physical_acceptance':False,'all_required_module_views_physically_qualified':False,'full_chip_accepted':False,'scope':'Full-cell selected-box drc(full) with catchup and actual exported GDS reimport DRC/LVS for candidates without known export errors. Existing MAG-level simulation/LEF import evidence retained, but it does not prove exported GDS connectivity. Failures require separate corrected views and new circuit simulations after parasitic changes. Does not qualify foundry signoff, routing resistance extraction, complete PLIF/model/5ms or chip assembly.','sha256':{f.relative_to(flow.ROOT).as_posix():digest(f) for f in sources}}
  target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(row),flush=True)
 print(json.dumps({'report':str(target),'audit_completed':True,'physical_layout_pass_count':result['physical_layout_pass_count'],'audited_component_count':len(cases)}),flush=True)
if __name__=='__main__':main()
