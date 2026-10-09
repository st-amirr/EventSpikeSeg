"""Bounded external per-cell program metrology; not an autonomous on-chip servo."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cpath=BASE/'gf180_local_gain_timing_calibration.json';c=json.loads(cpath.read_text(encoding='utf-8'))
 target=[v*16 for v in c['base_model_state_voltage_increments_v']]
 pairs=[];inputs=[cpath]
 for p in BASE.glob('gf180_calibrated_local_gain_injection_*_srcffa4a1d7a2a4.json'):
  r=json.loads(p.read_text(encoding='utf-8'));a=r['settings']
  if a['mismatch_seed']==29 and not a['no_events'] and a['local_gain']==16 and a['pf_program_levels'] in ['2.69,2.71,2.7,2.7','2.68,2.706,2.7,2.7']:
   assert r['simulation_completed'];pairs.append(([float(x) for x in a['pf_program_levels'].split(',')][:2],[r['measurements'][f'eventstep_{i}'] for i in [0,1]]));inputs.append(p)
 assert len(pairs)==2
 rows=[]
 for iteration in range(4):
  x=[]
  for i in [0,1]:
   x0,y0=pairs[-2][0][i],pairs[-2][1][i];x1,y1=pairs[-1][0][i],pairs[-1][1][i]
   assert abs(y1-y0)>1e-10
   value=x1+(target[i]-y1)*(x1-x0)/(y1-y0)
   assert 2.66<=value<=2.73,value
   x.append(value)
  args=[sys.executable,str(ROOT/'scripts/screen_gf180_calibrated_local_gain_injection.py'),'--local-gain','16','--duration-offset-ns',str(c['common_duration_offset_ns']),'--base-widths-us',','.join(str(v) for v in c['base_command_widths_us']*2),'--sequence','pppp','--load-ff','500','--pf-program-levels',','.join(str(v) for v in x+[2.7,2.7]),'--pf-reference-levels','2.7,2.7,2.7,2.7','--cell-order','0,1,0,1','--precharge-v','2.9','--warmup-us','100','--mismatch-seed','29','--baseline-trim-v','-0.0007546']
  run=subprocess.run(args,capture_output=True,text=True,timeout=145)
  if run.returncode:raise RuntimeError(run.stdout[-1200:]+run.stderr[-1200:])
  p=Path(json.loads(run.stdout)['report']);r=json.loads(p.read_text(encoding='utf-8'));assert r['simulation_completed'];inputs.append(p)
  y=[r['measurements'][f'eventstep_{i}'] for i in [0,1]];pairs.append((x,y))
  errors=[(a-b)*1e6 for a,b in zip(y,target)]
  row={'iteration':iteration,'report':p.relative_to(ROOT).as_posix(),'program_v':x,'steps_uv':[v*1e6 for v in y],'targets_uv':[v*1e6 for v in target],'error_uv':errors};rows.append(row);print(json.dumps(row),flush=True)
  if max(abs(e) for e in errors)<.25:break
 out={'status':'external_nominal_seed29_metrology_completed','original_float_targets_unchanged':True,'iterations':rows,'scope':'Externally measured voltage increments and ideal bench program-reference settings through actual native writers; gates float after10us. No software correction of stored membrane, no automatic onchip measurement/controller/reference generator, no quantization or retraining. One mismatch seed and near-reset operating point only. Convergence criterion0.25uV first two increments is a diagnostic target, not model acceptance; repeated increments checked separately in boundary.','sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in inputs+[Path(__file__),ROOT/'scripts/screen_gf180_calibrated_local_gain_injection.py']},'weighted_charge_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False}
 p=BASE/'gf180_local_gain_programming_calibration.json';p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('REPORT '+str(p),flush=True)
if __name__=='__main__':main()
