"""Audit three preselected fresh-record range64/comparator proxy replays."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    files={Path(__file__)};cases=[]
    for index in [16,24,32]:
        paths=list((BASE/'results').glob(f'gf180_range64_actual_threshold_error_record{index}_src*.json'))
        assert len(paths)==1
        p=paths[0];r=json.loads(p.read_text());files.add(p)
        assert r['simulation_completed'] and r['zero_offset_equation_control_exact'] and not r['qat_or_quantized_reference_used']
        assert r['checkpoint_sha256']=='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
        assert len(r['state_counts'])==25 and sum(r['state_counts'].values())==30976000
        for n,h in r['sha256'].items():assert sha(ROOT/n)==h,n
        rows=r['results'];assert len(rows)==5 and rows[0]['prediction_sha256']==rows[1]['prediction_sha256']
        cases.append({'record_index':index,'validation_record_id':r['validation_record_id'],'report':p.relative_to(ROOT).as_posix(),'policies':[{k:row[k] for k in ['policy','mean_iou','pixel_change_fraction','comparator_offset_proxy_v']} for row in rows]})
    means={row['policy']:sum(c['policies'][i]['mean_iou'] for c in cases)/len(cases) for i,row in enumerate(cases[0]['policies'])}
    result={'audit_completed':True,'cases':cases,'arithmetic_mean_record_iou_not_pooled_iou':means,'scope':'Three preselected fresh records from same validation sequence, each reset before ten-bin replay. Original float baseline and exact zero-error copied-equation controls; range64 is an unaccepted state saturation approximation. Uniform signed comparator error proxy derives from rising-ramp characterization at1.656875V; not pure offset, noise, resident-state loading or mismatch population. Positive and negative proxies are sensitivity controls. No joint beta/state transfer/error, real range/reference/conversion or throughput evidence. Three records cannot establish dataset-wide accuracy.','acceptance':{'range64_representation':False,'original_float_accuracy':False,'complete_PLIF':False,'full_5ms_population_service':False,'full_chip':False},'next_action':'Review actual-threshold error sensitivity, then characterize combined resident sensing and subtractive reset without selecting range64 as accepted. Keep original float model authoritative.','sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
    out=BASE/'results/gf180_range64_actual_threshold_error_boundary.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'report':str(out),'means':means}))
if __name__=='__main__':main()
