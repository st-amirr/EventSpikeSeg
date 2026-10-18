"""At most two physical four-bank fits; one-bank slope is an initial predictor only."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cp=BASE/'gf180_autozero_parking_programming_calibration.json';c=json.loads(cp.read_text(encoding='utf-8'))
 bp=BASE/'gf180_autozero_tracking_park_fourbank_a74523e807_srcea4d8d629b44.json';b=json.loads(bp.read_text(encoding='utf-8'));assert b['simulation_completed']
 target=c['iterations'][-1]['targets_uv'];a=b['settings'];x=[float(v) for v in a['pf_program_levels'].split(',')][:2];y=[b['measurements'][f'eventstep_{i}']*1e6 for i in range(2)]
 previous,last=c['iterations'][-2:];slope=[(last['steps_uv'][i]-previous['steps_uv'][i])/(last['program_v'][i]-previous['program_v'][i]) for i in range(2)]
 generator=ROOT/'scripts/screen_gf180_autozero_tracking_park_fourbank.py';files=[cp,bp,Path(__file__),generator];rows=[];failure=None
 for iteration in range(2):
  nx=[x[i]+(target[i]-y[i])/slope[i] for i in range(2)];assert all(2.66<v<2.73 for v in nx)
  args=[sys.executable,str(generator),'5','--max-step-ns','10','--mismatch-seed','29','--preload-differential-v','0']
  for key in ['local_gain','duration_offset_ns','base_widths_us','sequence','load_ff','pf_reference_levels','cell_order','precharge_v','warmup_us','baseline_trim_v']:
   args.extend(['--'+key.replace('_','-'),str(a[key])])
  args.extend(['--pf-program-levels',','.join(map(str,nx+[2.7,2.7]))])
  run=subprocess.run(args,capture_output=True,text=True,timeout=145)
  try:
   parsed=json.JSONDecoder().raw_decode(run.stdout.lstrip())[0];rp=Path(parsed['report']);r=json.loads(rp.read_text(encoding='utf-8'));files.append(rp)
  except Exception:
   failure=run.stdout[-1500:]+run.stderr[-1500:];break
  if run.returncode or not r['simulation_completed']:
   failure='Physical calibration run incomplete; retained raw report.';break
  ny=[r['measurements'][f'eventstep_{i}']*1e6 for i in range(2)]
  row={'iteration':iteration,'report':rp.relative_to(ROOT).as_posix(),'program_v':nx,'steps_uv':ny,'targets_uv':target,'error_uv':[v-t for v,t in zip(ny,target)]};rows.append(row);print(json.dumps(row),flush=True)
  if max(map(abs,row['error_uv']))<=.25:break
  slope=[(ny[i]-y[i])/(nx[i]-x[i]) for i in range(2)];x,y=nx,ny
 out={'calibration_completed':bool(rows) and max(map(abs,rows[-1]['error_uv']))<=.25,'failure':failure,'iterations':rows,'scope':'Two selected original-float weights, native four-bank autozero tracking schematic, seed29, zero preload,10ns maximum step,5us settling. One-bank slope predicts only initial PROGRAM change; all fitted outputs are newly simulated four-bank increments. Ideal external metrology/program references; no on-chip controller, noise or accuracy qualification. Maximum two new fit runs; no output/state arithmetic correction.','sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files},'weighted_charge_accepted':False,'full_chip_accepted':False}
 rp=BASE/'gf180_fourbank_parking_programming_calibration.json';rp.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('REPORT '+str(rp),flush=True)
if __name__=='__main__':main()
