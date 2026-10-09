"""Audit analog stored-weight/current-cell evidence without accepting full ASIC."""
import hashlib,json,math
import numpy as np
from decimal import Decimal,ROUND_CEILING
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 patterns=['gf180_loaded_baseline_readout_*_src5ea518c89f76.json','gf180_assembled_buffered_readout_*_src6acce212d6e7.json','gf180_readbuffer_noise_src*.json','gf180_paired_readbuffer_noise_src*.json']
 records=[]
 for pattern in patterns:
  for p in sorted((BASE/'results').glob(pattern)):
   r=json.loads(p.read_text())
   for n,h in r['sha256'].items():assert digest(ROOT/n)==h,n
   assert not any(r.get(k,False) for k in ['weighted_charge_accepted','complete_PLIF_accepted','original_float_accuracy_accepted','full_chip_accepted'])
   records.append({'report':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'completed':r['simulation_completed'],'settings':r.get('settings',{}),'measurements':r['measurements'],'simulator_returncode':r.get('simulator_returncode')})
 completed=sum(r['completed'] for r in records)
 assert len(records)==8 and completed==8,(len(records),completed)
 cell='gf180_buffered_baseline_readout_fullroute_spaced_guarded';folder=BASE/'layout'/cell
 physical={}
 for name in ['qualification.json','abstract_qualification.json']:
  p=folder/name;r=json.loads(p.read_text())
  for key,values in r.items():
   if 'sha256' in key and isinstance(values,dict):
    for n,h in values.items():
     target=ROOT/n if '/' in n else folder/n
     assert digest(target)==h,str(target)
  physical[name]={'sha256':digest(p),'checks':{k:v for k,v in r.items() if 'sha256' not in k}}
 q=physical['qualification.json']['checks']
 assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and q['extraction_feedback']==''
 paired=BASE/'results/gf180_paired_readbuffer_noise_src61268c7051f7.json';pn=json.loads(paired.read_text());spec=ROOT/pn['spectrum'];a=np.loadtxt(spec,skiprows=1);averaging=[]
 for t in [0,1e-6,4e-6,20e-6,100e-6,1e-3]:
  h=np.ones_like(a[:,0]) if t==0 else np.sinc(a[:,0]*t);rms=float(np.sqrt(np.trapezoid(a[:,1]**2*h**2,a[:,0])));averaging.append({'ideal_boxcar_duration_s':t,'band_limited_differential_noise_uv_rms':rms*1e6,'state_read_lane_lower_bound':int((Decimal(30976000)/Decimal("0.005")*Decimal(str(t))).to_integral_value(rounding=ROUND_CEILING)) if t else None})
 assert abs(averaging[0]['band_limited_differential_noise_uv_rms']/ (pn['measurements']['noise2.onoise_total']*1e6)-1)<.001
 report={'ideal_averaging_noise_and_read_lane_bounds':averaging,'stage':'buffered_readout_layout_works_deterministically_but_native_noise_requires_method_change','completed_diagnostics':completed,'incomplete_diagnostics':len(records)-completed,'all_provenance_hashes_match':True,'records':records,'physical_cell':physical,'findings':['Real extracted unity followers preserve nominal signed signals with50fF and500fF loads.','New combined9MOS/18MIM capture/buffer/compensation macro fully DRC/LVS/GDS-readback/LEF qualified; initial overlapped layout failedLVS and remains unqualified.','Assembled nominal500fF first positive buffered contribution16.5742uV; mismatchseed29 no-event buffered baseline-3.054mV requires recalibration.','Single buffer continuous output noise197.6755uV RMS1Hz-100MHz; actual paired shared-bias differential259.6113uV RMS, not sqrt2 extrapolation.','Ideal spectrum averaging calculation is not implemented filter/ADC and excludes sampled kT/C/storage/source/clock/reference-programmer noise. Long averaging carries substantial population service cost.'],'scope':'All new diagnostics completed. Physically extracted buffer/capture internal routing and output loads included; bank/pair/interfaces and physical bias/programmer/calibration control incomplete. Small-signal noise diagnostic ideal-drives capture inputs intentionally, only continuous buffer noise is measured. AC input-referred integrated noise is frequency-gain dependent, not a DC state-error assignment. Characterization668.5x379.57um geometry not chip-area acceptance. No sampled noise/globalPVT/RPEX/gate leakage/retention/5ms population service/model accuracy qualification.','next':'Investigate lower-noise or chopped/correlated analog readout and reference/calibration interface; characterize actual float tolerance and service cost before selecting readout/fullPLIF/dense assembly.','weighted_charge_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'live_sessions':[],'audit_source_sha256':digest(Path(__file__))}
 p=BASE/'results/gf180_buffered_readout_noise_boundary.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(p),'completed':completed,'incomplete':len(records)-completed,'physical_checks':True}))
if __name__=='__main__':main()
