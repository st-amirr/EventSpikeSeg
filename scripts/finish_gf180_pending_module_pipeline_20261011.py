"""Finish already authorized bounded pending module work and record only actual completion."""
from pathlib import Path
import subprocess,json,time,hashlib,re
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def run(args,timeout=180):
 p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=timeout);return {'args':args,'returncode':p.returncode,'output':p.stdout+p.stderr}
def main():
 log=B/'results/gf180_pending_module_pipeline_20261011.json';assert not log.exists();steps=[]
 args=['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:torch2.2.2-cpu-verification-guarded','120','python','scripts/compare_gf180_exact_hierarchy_graph_v2.py','--source','artifacts/analog_asic/layout/gf180_scheduled_rms_resident_write_v1/source_compact.spice','--other','artifacts/analog_asic/layout/gf180_scheduled_rms_resident_write_v1/flat_exact_graph_comparison.spice','--report','artifacts/analog_asic/layout/gf180_scheduled_rms_resident_write_v1/flat_exact_graph_v2_qualification.json'];steps.append(run(args,140))
 if steps[-1]['returncode']==0:steps.append(run(['python','scripts/qualify_gf180_completed_flat_graph_v2.py','--cell','gf180_scheduled_rms_resident_write_v1','--graph-report','artifacts/analog_asic/layout/gf180_scheduled_rms_resident_write_v1/flat_exact_graph_v2_qualification.json']))
 qualified=steps[-1]['returncode']==0
 # Preserve one native SPICE at a time; observe original job, never restart it.
 end=time.monotonic()+160
 while time.monotonic()<end:
  p=subprocess.run(['docker','inspect','99bd2136d42b'],capture_output=True)
  if p.returncode:break
  time.sleep(2)
 else:qualified=False;steps.append({'status':'original_SPICE_still_live_no_second_SPICE_started'})
 if qualified:steps.append(run(['python','scripts/screen_gf180_scheduled_rms_resident_write_nominal.py'],150))
 for cell,script,stem,role,gate in [('gf180_formatted_energy64_v3','screen_gf180_formatted64_flat_transient.py','_three_transient_src','full64_native_candidate_penalty_formatting_energy_root','native_full_channel_energy_transient_observed'),('gf180_scheduled_rms_resident_write_v1','screen_gf180_scheduled_rms_resident_write_nominal.py','_one_native_sequence_src','native_controller_driven_analog_RMS_capture_write','native_controller_driven_capture_write_observed')]:
  h=hashlib.sha256((R/'scripts'/script).read_bytes()).hexdigest()[:12];report=B/'results'/(cell+stem+h+'.json')
  if not report.exists():continue
  result=json.loads(report.read_text())
  if not result.get('module_simulation_completed'):continue
  rev=max(int(p.stem.rsplit('v',1)[1]) for p in (B/'assembly').glob('article_module_catalog_v*.json'))+1
  steps.append(run(['python','scripts/publish_gf180_characterization_assembly_20261011.py','--cell',cell,'--revision',str(rev),'--report',report.relative_to(R).as_posix(),'--role',role,'--gate',gate,'--note','Native nominal fixture completed; precision/loaded full-population5ms and full-chip layout remain incomplete. Exact graph connectivity proofs and all measured limitations retained.']))
 log.write_text(json.dumps({'steps':steps,'full_chip_layout_complete':False,'original_float_accuracy_accepted':False,'full_5ms_population_service_accepted':False},indent=2)+'\n');p=R/'docs/ACTIVE_TASKS.md';b=p.read_bytes();b=re.sub(rb'\| Job status \|[^\r\n]+',b'| Job status | Bounded pending-module pipeline terminal; inspect artifacts/analog_asic/results/gf180_pending_module_pipeline_20261011.json for actual results. Full-chip assembly remains incomplete. |',b,count=1);p.write_bytes(b);p=R/'docs/project_spec.yaml';b=p.read_bytes();h,t=b.split(b'\ndocument:',1);h=re.sub(rb'  live_sessions: [^\r\n]+',b'  live_sessions: []',h,count=1);p.write_bytes(h+b'\ndocument:'+t);print(log)
if __name__=='__main__':main()
