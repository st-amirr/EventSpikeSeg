"""Audit limited original-float sensitivity to one targeted physical beta parent."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'gf180_trained_beta_task_boundary.json';assert not out.exists();files={Path(__file__)};cases=[];baselines={}
 names=[f'gf180_trained_beta_channel_record{record}_seed0_srceca74b24358d.json' for record in [8,64]]+['gf180_trained_beta_partition_record8_seed0_src759417075f74.json']+[f'gf180_trained_beta_secant_channel_record{record}_seed{seed}_src30c4dc11deb2.json' for record,seed in [(8,0),(64,0),(8,29)]]
 for name in names:
  rp=R/name;d=json.loads(rp.read_text());assert d['simulation_completed'] and d['baseline_reproduced'] and not d['qat_or_quantized_reference_used'];files.add(rp)
  for n,h in d['sha256'].items():assert sha(ROOT/n)==h,n
  key=d['record_index'];row=d['results'][0];signature=(d['input_sequence_sha256'],d['target_sha256'],row['prediction_sha256'],row['mean_iou'])
  if key in baselines:assert baselines[key]==signature
  baselines[key]=signature
  cases.append({'report':rp.relative_to(ROOT).as_posix(),'record_index':key,'native_seed':d['native_mismatch_seed'],'results':[{'policy':x['policy'],'mean_iou':x['mean_iou'],'iou_change_from_original':x['mean_iou']-row['mean_iou'],'pixel_change_fraction':x['pixel_change_fraction']} for x in d['results']]})
 result={'audit_completed':True,'cases':cases,'conclusion':'Single physically targeted detail_stem channel3 is sensitive primarily to switching offset/nonlinearity, not the observed beta slope error, on record8 diagnostic. Refined-reference fresh native curves give nominal IoU loss about0.00101/0.00100 on records8/64; seed29 record8 loss0.00140. Nominal prediction change1.49/1.22%, seed29 2.67%. Earlier native-curve changes7.60/7.10%. New reference and fresh sample levels both changed, so no strict matched-sample causal improvement claim. Continue with threshold/subtractive-reset interface; do not extrapolate one-channel tolerance to all states.','scope':'Two same-sequence reset heldouts and one-seed record8, one channel only; exact original baseline hashes reproduced,QAT off, ideal representation and first-cycle piecewise three-point transfer. Gaussian/native noise, repeated-cycle history, dielectric leakage, real refs/clocks/service and other hardware errors omitted. Diagnostic partitions are ideal controls, not hardware corrections.','acceptance':{'original_float_accuracy':False,'complete_PLIF':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'audit_completed':True,'cases':len(cases),'conclusion':result['conclusion']},indent=2))
if __name__=='__main__':main()
