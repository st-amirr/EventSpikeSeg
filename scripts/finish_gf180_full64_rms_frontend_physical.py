"""Observe original extraction, recover its completed pass, then characterize native DC."""
from pathlib import Path
import hashlib,json,re,subprocess,time
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
cell='gf180_full64_rms_frontend_v1';d=B/'layout'/cell
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=B/'results/gf180_full64_frontend_completion_pipeline_v1.json';assert not report.exists()
 log=d/'first_pass_recovered.log';assert not log.exists()
 observer_start=time.monotonic();last=''
 while time.monotonic()-observer_start<900:
  p=subprocess.run(['docker','logs','2c61fcd49b71'],capture_output=True,text=True)
  if p.returncode==0:
   last=p.stdout+p.stderr
   if 'BBOX ' in last and (d/(cell+'.gds')).exists():break
  time.sleep(3)
 else:
  report.write_text(json.dumps({'pipeline_terminal':True,'source_observation_complete':False,'original_process_not_restarted':True,'last_log':last[-1800:],'full_chip_layout_complete':False},indent=2)+'\n');return
 log.write_text(last);assert re.search(r'Total DRC errors found:\s*0\b',last)
 # Reuse the audited no-restart recovery method; this is a new immutable execution source.
 original=R/'scripts/resume_gf180_scheduled_writer_completed_first_pass.py'
 source=original.read_text().replace('gf180_scheduled_rms_resident_write_v1',cell).replace('build_gf180_scheduled_rms_resident_write.py','build_gf180_full64_rms_frontend_v1.py').replace('8c787a7e02e5','2c61fcd49b71')
 source=source.replace("'300',*args", "'600',*args").replace('timeout=315','timeout=615').replace("'GDS_observation_bound_seconds':300","'GDS_observation_bound_seconds':600").replace('Native618MOS original source extraction completed after120s host observation; independent GDS readback given one300s bounded observation, native MIM devices retained.','Native2397MOS full64 RMS/frontend original source extraction exceeded120s host observation while actively processing the already qualified full64 child. Recover the original completed extraction; independent GDS readback gets one600s bound based on the observed full64 extraction cost. Native MIM devices retained.')
 recovery=R/'scripts/resume_gf180_full64_frontend_completed_first_pass.py';assert not recovery.exists();recovery.write_text(source)
 steps=[]
 def run(args,bound):
  p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=bound)
  steps.append({'args':args,'returncode':p.returncode,'output':p.stdout+p.stderr})
  report.write_text(json.dumps({'pipeline_terminal':False,'source_observation_complete':True,'original_process_not_restarted':True,'steps':steps,'full_chip_layout_complete':False},indent=2)+'\n')
  return p.returncode==0
 recovered=run(['python',str(recovery)],850)
 if recovered:
  run(['python','scripts/export_gf180_hierarchical_layout_abstract.py','--cell',cell],150)
  run(['python','scripts/screen_gf180_full64_rms_frontend_dc.py'],150)
 report.write_text(json.dumps({'pipeline_terminal':True,'source_observation_complete':True,'original_process_not_restarted':True,'physical_qualification_complete':(d/'qualification.json').exists(),'steps':steps,'full_chip_layout_complete':False,'sha256':{str(p.relative_to(R)):sha(p) for p in [Path(__file__),log,recovery]}},indent=2)+'\n')
 print(report)
if __name__=='__main__':main()
