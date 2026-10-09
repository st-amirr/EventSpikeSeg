"""Audit physical-reference and matched stationary encoder-noise evidence."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    sources={Path(__file__)};cases=[]
    for pattern,script in [('gf180_encoder_current_reference_*.json','characterize_gf180_encoder_current_reference.py'),
                           ('gf180_shared_encoder_noise_*.json','characterize_gf180_shared_encoder_noise.py')]:
        for path in sorted((BASE/'results').glob(pattern)):
            r=json.loads(path.read_text());snapshot=ROOT/r['source_snapshot']
            if digest(snapshot)!=r['sha256']['scripts/'+script]:raise ValueError('Source snapshot mismatch')
            sources.update([path,snapshot])
            for name,expected in r['sha256'].items():
                if name=='scripts/'+script:continue
                p=ROOT/name
                if digest(p)!=expected:raise ValueError('Input provenance mismatch: '+name)
                sources.add(p)
            case={'evidence':path.relative_to(ROOT).as_posix(),'kind':'encoder_noise' if 'shared_encoder_noise' in pattern else 'reference',
                  'simulation_completed':r['simulation_completed'],'settings':r['command_arguments'],
                  'values':r['values'],'scope':r['scope']}
            if case['kind']=='encoder_noise':
                transient=ROOT/r['transient_evidence'];tr=json.loads(transient.read_text())
                case['reference_filter_mim_count']=tr['command_arguments'].get('reference_filter_mim_count',0)
                case['dc_minus_transient']=r['dc_minus_transient_comparison']
                case['bias_matches_transient_within_100uv']=r['bias_matches_transient_within_100uv']
                expected=BASE/'benches'/transient.with_suffix('.spice').name
                case['exact_shared_deck_present']=expected.relative_to(ROOT).as_posix() in r['sha256']
                case['stationary_encode_bias_evidence_valid']=r['simulation_completed'] and r['bias_matches_transient_within_100uv'] and case['exact_shared_deck_present']
            else:
                case['compliance_rows']=r['compliance_rows'];case['startup_analysis']=r.get('startup_analysis')
                case['output_current_noise_scope']='Ideal output voltage clamp; shunt capacitor cannot qualify floating reference-voltage filtering or startup.'
            cases.append(case)
    filtered_comparisons=[]
    valid=[c for c in cases if c['kind']=='encoder_noise' and c['stationary_encode_bias_evidence_valid']]
    for filtered in valid:
        if filtered['reference_filter_mim_count']!=1:continue
        settings=filtered['settings'];tr=json.loads((ROOT/settings['transient']).read_text());a=dict(tr['command_arguments']);a['reference_filter_mim_count']=0
        donors=[]
        for base in valid:
            br=json.loads((ROOT/base['settings']['transient']).read_text());b=dict(br['command_arguments']);b.setdefault('reference_filter_mim_count',0)
            if base['reference_filter_mim_count']==0 and b==a and base['settings']['input_current_na']==settings['input_current_na']:donors.append(base)
        if len(donors)==1:
            base=donors[0]
            filtered_comparisons.append({'filtered':filtered['evidence'],'unfiltered':base['evidence'],
                'enc_rms_uv':[base['values']['enc_rms']*1e6,filtered['values']['enc_rms']*1e6],
                'span_rms_uv':[base['values']['span_rms']*1e6,filtered['values']['span_rms']*1e6],
                'scope':'Matched zero-current stationary encode topology, differing by one actual CAL filter MIM. No sampling/inter-phase covariance or physical reference acceptance.'})
    report={'cases':cases,'case_count':len(cases),'simulations_completed':sum(c['simulation_completed'] for c in cases),
        'matched_filter_comparisons':filtered_comparisons,'source_and_input_provenance_verified':True,
        'physical_reference_accepted':False,'sampled_noise_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,
        'scope':'Audited component compliance/cold ramp/current-noise and shared encode stationary noise. Native reference macros separately routed; ideal root generators/supplies/clocks and absent switched-noise/combined-layout/RPEX/silicon leakage/model/5ms qualification remain.',
        'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
    target=BASE/'results/gf180_reference_noise_boundary.json';target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'report':str(target),'case_count':len(cases),'simulations_completed':report['simulations_completed'],'matched_filter_comparisons':len(filtered_comparisons)}))

if __name__=='__main__':main()
