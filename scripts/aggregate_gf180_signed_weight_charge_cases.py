from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 script=ROOT/'scripts/screen_gf180_signed_weight_charge_parent_v2_singlecase.py';h=sha(script)[:12];paths=[BASE/'results'/f'gf180_signed_weight_charge_parent_v2_case{i}_src{h}.json' for i in range(3)];reports=[json.loads(p.read_text()) for p in paths];assert all(r['module_simulation_completed'] for r in reports)
 cases=[r['cases'][0] for r in reports];r={'module_simulation_completed':True,'scope':'Actual routed70MOS4MIM guarded native magnitude-duration, real sign gates and bipolar injector. Three independently bounded sequential cases with fixed biases/tolerances and physical two-MIM state loads. Combined three-case job timed out; preserved. Nominal mechanism only, external programming/phases/bias/PARK; no original-float weight map, fullPLIF, population service or dense/full-chip acceptance.','cases':cases,'signed_response_observed':all(x['expected_sign_observed'] for x in reports),'larger_positive_weight_delivers_more_charge':cases[1]['net_charge_into_state_c']>cases[0]['net_charge_into_state_c'],'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in paths+[script,Path(__file__)]}}
 p=BASE/'results'/('gf180_signed_weight_charge_parent_v2_sequential_src'+sha(Path(__file__))[:12]+'.json');assert not p.exists();p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(p),**{k:v for k,v in r.items() if k!='sha256'}},indent=2))
if __name__=='__main__':main()
