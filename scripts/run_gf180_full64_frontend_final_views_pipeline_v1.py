"""Finish only bounded authorized RMS assembly steps, with terminal evidence after each."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
cell='gf180_full64_rms_frontend_v1';d=B/'layout'/cell
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rp=B/'results/gf180_full64_frontend_final_views_pipeline_v1.json';assert not rp.exists()
 r={'pipeline_terminal':False,'stage':'waiting_for_original_physical_pipeline','steps':[],
    'full_chip_layout_complete':False,'original_float_accuracy_accepted':False,'full_5ms_population_service_accepted':False}
 def save():rp.write_text(json.dumps(r,indent=2)+'\n')
 def run(script,bound,extra=None):
  args=['python',script,*(extra or [])];p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=bound)
  r['steps'].append({'args':args,'returncode':p.returncode,'output':p.stdout+p.stderr});save();return p.returncode==0
 save()
 try:
  end=time.monotonic()+900;first=B/'results/gf180_full64_frontend_completion_pipeline_v1.json'
  while time.monotonic()<end:
   if first.exists() and json.loads(first.read_text()).get('pipeline_terminal'):break
   time.sleep(3)
  else:raise RuntimeError('Original physical/DC pipeline still pending; no second extraction or SPICE started.')
  physical=json.loads(first.read_text());assert physical['physical_qualification_complete'],physical
  assert (d/'abstract_qualification.json').exists()
  r['stage']='one_full_flat_capacitance_extraction_exact_graph';save()
  assert run('scripts/extract_gf180_full64_frontend_flat_exact_graph_v1.py',1980)
  r['stage']='one_three_level_native_extracted_transient';save()
  assert run('scripts/screen_gf180_full64_rms_frontend_flat_transient_v1.py',210)
  script=R/'scripts/screen_gf180_full64_rms_frontend_flat_transient_v1.py'
  native=B/'results'/(cell+'_three_transient_src'+sha(script)[:12]+'.json')
  nr=json.loads(native.read_text());assert nr['module_simulation_completed']
  r['stage']='publishing_completed_physical_and_native_artifacts';save()
  revision=max(int(p.stem.rsplit('v',1)[1]) for p in (B/'assembly').glob('article_module_catalog_v*.json'))+1
  assert run('scripts/publish_gf180_characterization_assembly_20261011_v2.py',150,
   ['--cell',cell,'--revision',str(revision),'--report',native.relative_to(R).as_posix(),
    '--role','full64_native_RMS_to_analog_clip_strength_connected_chain',
    '--gate','native_connected_RMS_frontend_transient_observed',
    '--note','Actual upstream64-channel analog ROOT drives the native frontend; external candidate/penalty/strength/reference fixtures remain. Completed nominal traces with known errors retained; accuracy and loaded5ms/full-chip acceptance remain incomplete. No repeated precision sweep.'])
  r['stage']='module_physical_and_nominal_artifacts_complete'
 except Exception as e:r['error']=repr(e)
 finally:
  r['pipeline_terminal']=True;save()
  p=R/'docs/ACTIVE_TASKS.md';b=p.read_bytes()
  b=__import__('re').sub(rb'\| Job status \|[^\r\n]+',b'| Job status | Full64 RMS/frontend final-view pipeline terminal; inspect artifacts/analog_asic/results/gf180_full64_frontend_final_views_pipeline_v1.json. Full-chip assembly remains incomplete. |',b,count=1);p.write_bytes(b)
  p=R/'docs/project_spec.yaml';b=p.read_bytes();h,t=b.split(b'\ndocument:',1);h=__import__('re').sub(rb'  live_sessions: [^\r\n]+',b'  live_sessions: []',h,count=1);p.write_bytes(h+b'\ndocument:'+t)
 print(rp)
if __name__=='__main__':main()
