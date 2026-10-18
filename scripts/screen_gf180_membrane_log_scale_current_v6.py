"""Bounded nominal GF180 screen for an analog log-scale-to-current control element."""
import hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
MANIFEST=BASE/'results/gf180_membrane_scale_hardware_requirements_v1.json'
MODEL_DIR=BASE/'pdk/gf180_primitive_source/models/ngspice'
SCRIPT=Path(__file__)
NAME='gf180_membrane_log_scale_current_v6'
DECK=BASE/'benches'/(NAME+'.spice')
LOG=BASE/'results'/(NAME+'.log')
OUT=BASE/'results'/(NAME+'.json')
SCALE_V=[0.75,1.6973421760170977,2.55]
ALPHA=0.21278333333333333
VGATE_AT_MIN=2.94845

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not OUT.exists() and not DECK.exists() and not LOG.exists(), 'preserve any existing versioned artifacts'
 requirements=json.loads(MANIFEST.read_text())
 assert requirements['bank_count']==490240
 assert abs(requirements['all_bank_scale_v_per_model_unit']['dynamic_ratio']-12151.403233847937)<1e-6
 prefix='/workspace/'+MODEL_DIR.relative_to(ROOT).as_posix()
 deck='\n'.join([
  f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',
  f'.lib {prefix}/sm141064.spice res_typical',
  '.temp 27','.options method=gear reltol=1e-6 abstol=1e-19 vntol=1e-10 gmin=1e-18',
  '.param sw_stat_global=0 sw_stat_mismatch=0',
  'VDD vdd 0 3.3',
  'VLOG vlog 0 PWL(0 0.75 9.99u 0.75 10u 1.6973421760170977 19.99u 1.6973421760170977 20u 2.55 35u 2.55)',
  f'BVG gate 0 V={VGATE_AT_MIN}-{ALPHA}*(V(vlog)-0.75)',
  'Mscale out gate vdd vdd pfet_03v3 w=0.42u l=10u',
  'Vmeter out drain 0', 'Vdrain drain 0 1.65',
  '.control','set numdgt=15','tran 1n 30u 0 1n uic',
  'meas tran i_min find i(Vmeter) at=5u','meas tran i_mid find i(Vmeter) at=15u','meas tran i_max find i(Vmeter) at=25u',
  'meas tran vgate_min find v(gate) at=5u','meas tran vgate_mid find v(gate) at=15u','meas tran vgate_max find v(gate) at=25u',
  'quit','.endc','.end',''])
 DECK.write_text(deck,encoding='utf-8')
 cmd=['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+DECK.relative_to(ROOT).as_posix()]
 run=subprocess.run(cmd,capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;LOG.write_text(log,encoding='utf-8')
 vals={k:float(v) for k,v in re.findall(r'(?m)^(i_(?:min|mid|max)|vgate_(?:min|mid|max))\s*=\s*([-+0-9.eE]+)',log)}
 complete=run.returncode==0 and len(vals)==6 and all(vals[k]>0 for k in ['i_min','i_mid','i_max'])
 ratio=vals.get('i_max',0)/vals.get('i_min',1) if complete else None
 result={'simulation_completed':complete,'simulator_returncode':run.returncode,'test':'one nominal weak-inversion PFET control at three log-scale voltages','settings':{'temperature_c':27,'vdd_v':3.3,'drain_v':1.65,'scale_voltage_points_v':SCALE_V,'alpha_gate_attenuation':ALPHA,'gate_voltage_at_min_scale_v':VGATE_AT_MIN,'device':'pfet_03v3 w=0.42um l=10um','target_scale_current_ratio':requirements['all_bank_scale_v_per_model_unit']['dynamic_ratio']},'measurements':vals,'measured_current_ratio':ratio,'ratio_error_percent':(ratio/requirements['all_bank_scale_v_per_model_unit']['dynamic_ratio']-1)*100 if ratio else None,'scope':'Intrinsic current-control transfer only. No bank sample/hold, analog current multiplier, weight injector, membrane update, extracted layout, mismatch/noise/PVT, original-float replay or 5ms service. This is one nominal screen, not acceptance.','sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [SCRIPT,DECK,LOG,MANIFEST]}}
 OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'report':OUT.relative_to(ROOT).as_posix(),'completed':complete,'measured_ratio':ratio,'target_ratio':result['settings']['target_scale_current_ratio'],'ratio_error_percent':result['ratio_error_percent'],'measurements':vals},indent=2))
 if not complete:raise RuntimeError(log[-2500:])
if __name__=='__main__':main()





