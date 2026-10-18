"""Archive exact seven operational documents before updating the live job line."""
from pathlib import Path
import argparse,datetime,hashlib,json,zipfile,re
R=Path(__file__).resolve().parents[1]
def main():
 a=argparse.ArgumentParser();a.add_argument('--stage',required=True);a.add_argument('--session',type=int);v=a.parse_args();docs=[R/'docs'/n for n in ['AGENTS.md','ACTIVE_TASKS.md','ARCHITECTURE.md','DECISIONS.md','RESULTS.md','PROGRESS.md','project_spec.yaml']];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');z=R/'artifacts/analog_asic/documentation_history'/('project_docs_before_job_status_'+stamp+'.zip')
 with zipfile.ZipFile(z,'x',zipfile.ZIP_DEFLATED) as out:
  for p in docs:out.writestr(p.relative_to(R).as_posix(),p.read_bytes())
 z.with_suffix('.json').write_text(json.dumps({'archive_sha256':sha(z),'files':{p.relative_to(R).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in docs}},indent=2)+'\n')
 p=R/'docs/ACTIVE_TASKS.md';b=p.read_bytes();b,n=re.subn(rb'\| Live jobs \|[^\r\n]+',('| Live jobs | '+v.stage+' |').encode(),b,count=1);assert n==1;p.write_bytes(b)
 p=R/'docs/project_spec.yaml';b=p.read_bytes();b,n=re.subn(rb'  live_sessions: [^\r\n]+',('  live_sessions: '+json.dumps([v.session] if v.session else [])).encode(),b,count=1);assert n==1;p.write_bytes(b);print(v.stage)
if __name__=='__main__':main()
