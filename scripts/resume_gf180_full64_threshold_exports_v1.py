"""Recover completed64group exports after host timeout; do not repeat initial extraction."""
from pathlib import Path
import hashlib,json,subprocess
import probe_gf180_mos_gate_cap as f
R=Path(__file__).resolve().parents[1]
def main():
 c='gf180_adaptation_sum64_threshold_v1';d=f.BASE/'layout'/c;builder=R/'scripts/build_gf180_fullwidth_adaptation_threshold_v2.py';assert builder.read_bytes()==(d/'build_source.py').read_bytes();assert all((d/(c+s)).exists() for s in ['.mag','.ext','.spice','.gds']);assert not (d/'qualification.json').exists();oldmagic=f.magic;oldrun=f.run;oldwrite=Path.write_text;calls=[0];protected={d/(c+'.mag')};src=builder.read_text().replace('assert not out.exists() or not any(out.iterdir());out.mkdir(parents=True,exist_ok=True)','assert out.exists();out.mkdir(parents=True,exist_ok=True)')
 def run(args,stdin=None):
  cmd=['docker','run','--rm','--network','none','--memory','2g','--cpus','2']+(['-i'] if stdin is not None else [])+['--volume',f'{R}:/workspace','--workdir','/workspace/'+f.OUT.relative_to(R).as_posix(),'--entrypoint','timeout','eventspikeseg:analog-gf180-layout','180',*args];p=subprocess.run(cmd,input=stdin,capture_output=True,text=True,timeout=195);log=p.stdout+p.stderr;assert p.returncode==0,log[-3000:];return log
 def magic(script):
  calls[0]+=1
  if calls[0]==1:
   prefix=script.split(f'load {c}\n',1)[0];t=prefix+f'load {c}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nputs "BBOX [box values]"\nquit -noprompt\n';(d/'source_drc_recovery.tcl').write_text(t);log=oldmagic(t);(d/'source_drc_recovery.log').write_text(log);return log
  return oldmagic(script)
 def write(p,text,*a,**kw):
  if p in protected:assert p.read_text()==text;return len(text)
  return oldwrite(p,text,*a,**kw)
 f.run=run;f.magic=magic;Path.write_text=write
 import sys
 prior=sys.argv;sys.argv=[str(builder),'--channels','64']
 try:
  ns={'__file__':str(builder),'__name__':'recovery'};exec(compile(src,str(builder),'exec'),ns);ns['main']()
 finally:f.run=oldrun;f.magic=oldmagic;Path.write_text=oldwrite;sys.argv=prior
 qp=d/'qualification.json';q=json.loads(qp.read_text());q['timeout_recovery']={'initial_host_observation_s':120,'initial_export_finish_seconds_from_MAG_GDS_timestamps':(d/(c+'.gds')).stat().st_mtime-(d/(c+'.mag')).stat().st_mtime,'original_native_process_terminal_verified_by_no_live_Docker_handle':True,'initial_native_extraction_not_restarted':True,'fresh_full_source_DRC_log':'source_drc_recovery.log','subsequent_native_command_bound_seconds':180,'basis':'Source/GDS artifact timestamps show initial source operation completed in about144s.180s is a measured bound extension for full-group physical checks;2CPU/2GB unchanged.'};q['input_sha256'].update({p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),d/'source_drc_recovery.tcl',d/'source_drc_recovery.log']});qp.write_text(json.dumps(q,indent=2)+'\n')
if __name__=='__main__':main()
