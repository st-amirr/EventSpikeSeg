"""Audit analog stored-weight/current-cell evidence without accepting full ASIC."""
import hashlib,json,math
import numpy as np
from decimal import Decimal,ROUND_CEILING
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 patterns=['gf180_source_follower_noise_srce129a998fb60.json','gf180_source_follower_noise_*_srced393c8aa839.json','gf180_follower_baseline_readout_*_srcd45e41184fff.json','gf180_assembled_follower_readout_*_src5c6d54b5b835.json','gf180_paired_follower_pex_noise_srcb0e8ea49667b.json','gf180_follower_transfer_src3597142321c2.json','gf180_pmos_follower_noise_*_srca627465bdf11.json','gf180_pmos_follower_transfer_*_srcc6587447d50e.json']
 records=[]
 for pattern in patterns:
  for p in sorted((BASE/'results').glob(pattern)):
   r=json.loads(p.read_text())
   for n,h in r['sha256'].items():assert digest(ROOT/n)==h,n
   assert not any(r.get(k,False) for k in ['weighted_charge_accepted','complete_PLIF_accepted','original_float_accuracy_accepted','full_chip_accepted'])
   records.append({'report':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'completed':r['simulation_completed'],'settings':r.get('settings',{}),'measurements':r['measurements'],'simulator_returncode':r.get('simulator_returncode')})
 completed=sum(r['completed'] for r in records)
 assert len(records)==11 and completed==11,(len(records),completed)
 cell='gf180_follower_baseline_readout_fullroute_guarded';folder=BASE/'layout'/cell
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
 comparison=[];comparison_sources={}
 names=['gf180_paired_readbuffer_noise_src61268c7051f7.json','gf180_source_follower_noise_srce129a998fb60.json','gf180_source_follower_noise_e731503eed_srced393c8aa839.json','gf180_source_follower_noise_1e9d9b13bc_srced393c8aa839.json','gf180_source_follower_noise_387b50f44c_srced393c8aa839.json','gf180_paired_follower_pex_noise_srcb0e8ea49667b.json','gf180_pmos_follower_noise_e731503eed_srca627465bdf11.json']
 for name in names:
  p=BASE/'results'/name;pn=json.loads(p.read_text())
  for n,h in pn['sha256'].items():assert digest(ROOT/n)==h,n
  comparison_sources[p.relative_to(ROOT).as_posix()]=digest(p)
  a=np.loadtxt(ROOT/pn['spectrum'],skiprows=1);points=[]
  for t in [0,1e-6,4e-6,20e-6,100e-6]:
   h=np.ones_like(a[:,0]) if t==0 else np.sinc(a[:,0]*t);rms=float(np.sqrt(np.trapezoid(a[:,1]**2*h**2,a[:,0])))
   cds=None if t==0 else float(np.sqrt(np.trapezoid(a[:,1]**2*h**2*(2*np.sin(np.pi*a[:,0]*2*t))**2,a[:,0])))*1e6
   points.append({'ideal_average_duration_s':t,'average_output_noise_uv_rms':rms*1e6,'ideal_two_sample_CDS_gap_2T_noise_uv_rms':cds})
  assert abs(points[0]['average_output_noise_uv_rms']/(pn['measurements']['noise2.onoise_total']*1e6)-1)<.001
  comparison.append({'report':name,'settings':pn.get('settings',{}),'integrated_noise':pn['measurements'],'ideal_filter_proxies':points})
 transfers=[]
 for name in ['gf180_follower_transfer_src3597142321c2.json','gf180_pmos_follower_transfer_e731503eed_srcc6587447d50e.json']:
  p=BASE/'results'/name;r=json.loads(p.read_text());a=np.loadtxt(ROOT/r['dc_transfer'],skiprows=1);g=np.gradient(a[:,1],a[:,0]);mid=int(np.argmin(abs(a[:,0]-1.65)));mask=(a[:,0]>=1.35-1e-8)&(a[:,0]<=1.95+1e-8);residual=a[:,1]-(a[mid,1]+g[mid]*(a[:,0]-a[mid,0]))
  transfers.append({'report':name,'sha256':digest(p),'input_range_v':[float(a[0,0]),float(a[-1,0])],'output_range_v':[float(a[0,1]),float(a[-1,1])],'local_gain_range':[float(g.min()),float(g.max())],'local_gain_at1p65':float(g[mid]),'max_sampled_local_linear_fit_error_uv':float(max(abs(residual)))*1e6,'central_input_range_v':[1.35,1.95],'central_gain_range':[float(g[mask].min()),float(g[mask].max())],'central_max_sampled_local_linear_fit_error_uv':float(max(abs(residual[mask])))*1e6,'supply_draw_range_a':[float(min(-a[:,3])),float(max(-a[:,3]))]})
 nominal=next(r for r in records if 'assembled_follower_readout' in r['report'] and r['settings']['mismatch_seed'] is None);gain=nominal['measurements']['buffered_step_0']/nominal['measurements']['eventstep_0'];equivalent=next(c for c in comparison if c['report']=='gf180_paired_follower_pex_noise_srcb0e8ea49667b.json')['ideal_filter_proxies'][2]['average_output_noise_uv_rms']/gain
 report={'dc_transfer_comparison':transfers,'nominal_initial_state_to_loaded_output_gain':gain,'conditional_4us_noise_referred_to_integrator_output_uv':equivalent,'noise_comparison':comparison,'comparison_report_sha256':comparison_sources,'stage':'lower_noise_source_follower_readout_physically_implemented','completed_diagnostics':completed,'incomplete_diagnostics':len(records)-completed,'all_provenance_hashes_match':True,'records':records,'physical_cell':physical,'findings':['Correlated sampling alone does not remove short-window white noise; ideal CDS estimates are conditional spectral operations, not implemented sample hardware.','Schematic source follower bias sizing explores1/10uA and1/4parallel NF80 devices; more gate width lowers output noise but adds input loading, so output-noise minimum alone is not selection criterion.','Physical4MOS/9MIM source-follower/clamp/capture macro and NF10/NF80 leaves fully qualified; no compensation bank required.','Extracted paired differential continuous noise87.6304uV RMS vs earlier259.6113uV, both1Hz-100MHz nominal driven input/500fF load; current reference10uA vs prior1uA.','Assembled nominal signed readout retains both signs but gain about0.6134 and common mode0.761V require calibration; mismatch seed29 buffered baseline753.054uV not cancelled.'],'scope':'Noise improvements are measured at readout outputs, not model-accuracy acceptance.4us boxcar and CDS are mathematical spectral weighting only, exclude sampled kT/C/storage/source/clock/reference noise, temporal nonstationarity/PVT/gate leakage/RPEX. Short2T sample gap is not5ms bin completion. Conditional equivalent input error divides ideal output average by nominal short-run transfer, not a measured all-state/noise distribution. Physical bias generator/programmer/calibration servo and full bank/pair interconnect unimplemented. Spacious660.3x376.57um geometry not dense tile/chip area acceptance.','next':'Physically qualify source-tied-body PMOS follower if isolation/headroom permit, characterize load/noise/transfer/calibration; evaluate original-float error tolerance then integrate fullPLIF/dense assembly.','weighted_charge_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'live_sessions':[],'audit_source_sha256':digest(Path(__file__))}
 p=BASE/'results/gf180_follower_readout_noise_boundary.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(p),'completed':completed,'incomplete':len(records)-completed,'physical_checks':True}))
if __name__=='__main__':main()
