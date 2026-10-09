"""Audit measured physical writeback gains and their extrapolated float sensitivity."""
import hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/analog_asic/results'
EXPECTED='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local(name):return ROOT/name.removeprefix('/workspace/')
def main():
 sources={Path(__file__)};cases=[]
 checkpoint=ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt'
 if digest(checkpoint)!=EXPECTED:raise ValueError('Original checkpoint differs')
 sources.add(checkpoint)
 for path in sorted(OUT.glob('analog_float_affine_restore_record*_all_neurons_full_*.json')):
  r=json.loads(path.read_text());physical_names=r.get('restore_source_sha256',{})
  if not physical_names or not all('gf180_encoder_writeback_' in name for name in physical_names):continue
  if r['checkpoint_sha256']!=EXPECTED or r['qat_or_quantized_reference_used'] or not r['full_frame'] or r['scope']!='all-neurons' or r['encoding']!='linear-clipped' or r['gains']!=[1.0] or r['noise_mode']!='none' or r['retention_law']!='none' or r['restore_offset_uv_in_0p9v_normalization']!=0:raise ValueError('Bounded gain-only sensitivity contract differs')
  snapshot=ROOT/r['replay_source_snapshot']
  if digest(snapshot)!=r['replay_source_sha256']:raise ValueError('Immutable replay source differs')
  sources.update([snapshot,path]);physical={}
  for name,sha in physical_names.items():
   p=local(name)
   if digest(p)!=sha:raise ValueError('Physical report differs')
   d=json.loads(p.read_text());sources.add(p)
   if not d['simulation_completed'] or d['settings']['input_na'] not in [-200,200]:raise ValueError('Physical signed input evidence differs')
   for n,h in d['sha256'].items():
    f=local(n)
    if digest(f)!=h:raise ValueError('Physical source/native inputs differ')
    sources.add(f)
   physical[d['settings']['input_na']]=d
  if set(physical)!={-200,200}:raise ValueError('Signed pair missing')
  def circuit(d):
   p=next(local(n) for n in d['sha256'] if '/benches/' in n and n.endswith('.spice'));return '\n'.join(x for x in p.read_text().splitlines() if not x.startswith('Iinput '))
  if circuit(physical[200])!=circuit(physical[-200]):raise ValueError('Signed physical benchmarks differ beyond input')
  for current,key in [(200,'restore_gain_positive'),(-200,'restore_gain_negative')]:
   a=physical[current]['analysis'];g=a['unity_readback_charge_fc']/a['first_beta_charge_fc']
   if not math.isclose(g,r[key],rel_tol=1e-12):raise ValueError('Replay coefficient differs from physical charge ratio')
  cases.append({'evidence':path.relative_to(ROOT).as_posix(),'record_index':r['record_index'],'baseline_present_class_mean_iou':r['baseline_present_class_mean_iou'],'baseline_labeled_pixel_accuracy':r['baseline_labeled_pixel_accuracy'],'restore_gain_positive':r['restore_gain_positive'],'restore_gain_negative':r['restore_gain_negative'],'trials':r['trials'],'scope':r['restore_scope'],'physical_evidence':physical_names})
 result={'checkpoint_sha256':EXPECTED,'qat_or_quantized_reference_used':False,'cases':cases,'case_count':len(cases),'physical_and_replay_source_hashes_verified':True,'physical_writeback_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'scope':'Measured signed charge-preservation ratios extrapolated as constant per-polarity gains to all actors and states after each post-reset bin. Two frames cannot qualify validation accuracy. Ideal per-record normalization/initialization, zero offset/noise/leakage, no actual weighted-event or threshold/reset/adaptation circuitry and no5ms service/combined layout qualification. Standalone native cells and diagnostic circuits are not accepted complete PLIF.','sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
 target=OUT/'gf180_writeback_gain_float_boundary.json';target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'report':str(target),'case_count':len(cases),'cases':cases},indent=2))
if __name__=='__main__':main()
