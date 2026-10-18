"""Resolve original ASIC artifact provenance paths after the move-only cleanup."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
def resolve_artifact(value):
 s=str(value).replace('\\','/')
 if s.startswith('/workspace/'):s=s[len('/workspace/'):]
 prefix=ROOT.as_posix()+'/'
 if s.lower().startswith(prefix.lower()):s=s[len(prefix):]
 original=ROOT/s
 if original.exists():return original
 idx=json.loads((ROOT/'artifacts/asic_artifact_index.json').read_text())
 if s in idx['retained_path_map']:return ROOT/idx['retained_path_map'][s]
 for old,new in idx['archived_root_prefixes'].items():
  if s==old or s.startswith(old+'/'):return ROOT/(new+s[len(old):])
 return original
if __name__=='__main__':
 p=resolve_artifact(sys.argv[1]);print(p)
 if not p.exists():raise SystemExit('Artifact unavailable at resolved path.')
