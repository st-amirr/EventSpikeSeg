"""Conditional native NF sharing ratio/plate budget against executed float beta inventory."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'gf180_nf_complete_cycle_ratio_inventory.json';assert not out.exists()
 bp=R/'gf180_executed_float_beta_inventory.json';cp=R/'gf180_resident_beta_nf_repeated_boundary.json';b=json.loads(bp.read_text());c=json.loads(cp.read_text())
 assert b['measurement_completed'] and c['audit_completed']
 for d in [b,c]:
  for name,h in d['sha256'].items():assert sha(ROOT/name)==h,name
 vals=[next(x['first_complete_cycle_slope'] for x in c['cases'] if x['seed']==0 and x['state_plates']==n) for n in [1,2]]
 unit=50.51842;ratios=[(1-v)/v for v in vals];fixed=unit*(2*ratios[1]-ratios[0])/(ratios[0]-ratios[1]);aux=ratios[0]*(unit+fixed)
 rows=[];total=0;state_sum=0;extra_aux_sum=0;below=0;gap=0
 for actor in b['actors']:
  per=actor['states_per_channel'];channels=[]
  for i,beta in enumerate(actor['beta']):
   state=max(unit,aux*beta/(1-beta)-fixed);needed=(state+fixed)*(1-beta)/beta;extra=max(0,needed-aux)
   assert abs((state+fixed)/(state+fixed+needed)-beta)<1e-12
   channels.append({'channel':i,'trained_beta':beta,'conditional_state_cap_fF':state,'conditional_extra_aux_cap_fF':extra})
   total+=per;state_sum+=state*per;extra_aux_sum+=extra*per
   if extra>1e-9:below+=per
   if 1e-9<extra<unit:gap+=per
  rows.append({'actor':actor['actor'],'states_per_channel':per,'channels':channels})
 assert total==30976000
 # Ideal capacitor area conversion omits fringe; geometry and gap rules not qualified.
 result={'analysis_completed':True,'resident_membranes':total,'fitted_two_point_diagnostic':{'native_one_plate_total_fF':unit,'slopes':vals,'fixed_state_equivalent_fF':fixed,'auxiliary_equivalent_fF':aux},'conditional_total_state_cap_fF':state_sum,'conditional_total_extra_aux_cap_fF':extra_aux_sum,'ideal2fF_per_um2_state_plate_sum_mm2':state_sum/2/1e6,'ideal2fF_per_um2_extra_aux_plate_sum_mm2':extra_aux_sum/2/1e6,'states_requiring_added_aux_cap':below,'states_with_extra_aux_below_minimum_MIM_unit':gap,'actors':rows,'scope':'Two measured nominal complete-cycle endpoint slopes including auxiliary recharge fitted by beta=(N*Cunit+Cfixed)/(N*Cunit+Cfixed+Caux). Cunit includes nominal50fF MIM plus extracted0.51842fF parallel plate fringe. Cfixed/Caux are diagnostic effective fits incorporating switching injection and C(V), NOT measured physical capacitances. Continuous target ratios only; no quantization/model edits.2fF/um2 hypothetical plate conversion omits routing, switch area, spacing, adaptation, actual fringe/minimum-geometry constraints and all service. Extra auxiliary below minimumMIM requires another physically qualified implementation; do not claim all1856 learned betas are implemented. This is a conditional architecture budget, not full-chip area or fundamental lower bound.','acceptance':{'learned_beta_coverage':False,'complete_PLIF':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),bp,cp]}}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ['actors','sha256']},indent=2))
if __name__=='__main__':main()
