"""Audit static readout diagnostics; do not interpret ideal replacements as hardware."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=BASE/'gf180_readout_mismatch_partition_boundary.json'
 assert not out.exists(),'Preserve completed audit'
 cases={};blocks={};files={Path(__file__)}
 for mode in ['native','ideal_ota','ideal_ota_current']:
  path=BASE/f'gf180_readout_mismatch_partition_{mode}_src17422d5ee350.json'
  d=json.loads(path.read_text());files.add(path)
  assert d['simulation_completed'] and d['simulator_returncode']==0 and len(d['points'])==13
  for name,digest in d['sha256'].items():
   f=ROOT/name;assert sha(f)==digest,name;files.add(f)
  dump=BASE/f'gf180_readout_mismatch_partition_{mode}_src17422d5ee350_instances.txt'
  assert sha(dump)==d['instance_dump_sha256']
  blocks[mode]=re.findall(r'BSIM4v5:.*?(?=\n\s*\n|\Z)',dump.read_text(),re.S)
  count=sum(len(re.search(r'delvto\s+([^\n]+)',x)[1].split()) for x in blocks[mode])
  assert count==150 and all('?????????' not in b for b in blocks[mode])
  lanes={}
  for lane in ['low','mid','high']:
   errors=[p[f'v(decoded_{lane})']-p[f'v(state_{lane})'] for p in d['points']]
   lanes[lane]={'min_error_v':min(errors),'max_error_v':max(errors),'max_abs_error_v':max(map(abs,errors)), 'swept':lane=='low'}
  cases[mode]={'report':path.relative_to(ROOT).as_posix(),'native_MOS_count':count,'errors_by_lane':lanes}
 assert blocks['native']==blocks['ideal_ota']==blocks['ideal_ota_current']
 for i,p in enumerate(json.loads((ROOT/cases['native']['report']).read_text())['points']):
  for mode in ['ideal_ota','ideal_ota_current']:
   q=json.loads((ROOT/cases[mode]['report']).read_text())['points'][i]
   for lane in ['low','mid','high']:
    assert abs(p[f'v(state_{lane})']-q[f'v(state_{lane})'])<1e-9
 report={'status':'completed_static_diagnostic_partition','cases':cases,
 'native_instance_parameter_comparison':{'identical_BSIM_blocks':True,'MOS_count':150,'parameters':['delvto','mulu0','l','w'],'precision_limit':'Printed dump precision; not binary full-precision identity. Model blocks and hierarchy/order also retained.'},
 'conclusion':'Amplifier-control idealization alone leaves up to114.253mV error; ideal exact current copy still leaves up to48.601mV across the examined lanes. Both loop offset and current-transfer mechanisms matter, with substantial residual resident/replica sense/select-path error. Errors are signed and can cancel; improvements must not be assigned additive percentages. Native OTA autozero alone is not a sufficient repair.',
 'next_action':'Evaluate a readout that avoids an unmatched resident-to-replica transistor transfer, or explicitly calibrates that transfer. Compare a shared voltage/charge-sampling interface before adding per-state calibration storage or replicating the current reader.',
 'scope':'Seed29,200mV reference, static writer/select ON. Only low lane swept13levels; other two lanes fixed. Ideal controls/current copy are diagnostic only. No acquisition/hold/settling/noise/yield/model-accuracy/5ms/full-chip qualification.',
 'acceptance':{'readout':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},
 'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'report':str(out),'cases':cases,'next_action':report['next_action']},indent=2))
if __name__=='__main__':main()
