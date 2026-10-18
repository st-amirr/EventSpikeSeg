"""Audit physical sub-minimum-MIM auxiliary capacitance and complete-cycle transfer."""
from pathlib import Path
import hashlib,json,re
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';R=BASE/'results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def caps(cell):
 p=BASE/'layout'/cell/(cell+'_cap.spice');txt=p.read_text().split('.subckt '+cell+' ')[1];out={}
 for a,b,v in re.findall(r'(?m)^C\S+ (\S+) (\S+) ([0-9.]+)f$',txt):out[tuple(sorted([a,b]))]=float(v)
 return out,p
def main():
 out=R/'gf180_aux_overlap_boundary.json';assert not out.exists();files={Path(__file__)};cases=[];geometries=[];base,bp=caps('gf180_nf_state_update_localnodes');files.add(bp)
 invp=R/'gf180_executed_float_beta_inventory.json';inventory=json.loads(invp.read_text());assert inventory['measurement_completed'];files.add(invp)
 for n,h in inventory['sha256'].items():assert sha(ROOT/n)==h,n
 for suffix,source,seeds,area in [('', '8a81aa374ddf',[0],100),('_small','6494b6dbf987',[0,29],8)]:
  cell='gf180_nf_state_update_aux_overlap'+suffix;c,cp=caps(cell);files.add(cp);qpath=cp.parent/'qualification.json';q=json.loads(qpath.read_text());files.add(qpath);assert q['magic_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and q['gds_roundtrip_drc_count']==0
  geometries.append({'cell':cell,'overlap_area_um2':area,'parent_AUX_AUXREF_cap_fF':c[('AUX','AUXREF')],'added_AUX_AUXREF_vs_baseline_fF':c[('AUX','AUXREF')]-base[('AUX','AUXREF')],'added_AUX_VSS_vs_baseline_fF':c[('AUX','VSS')]-base[('AUX','VSS')],'physical_DRC_LVS_GDS_passed':True})
  for mode,seed in [('baseline',0)]+[('check',x) for x in seeds]:
   rp=R/f'gf180_extracted_state_update_aux_overlap{suffix}_{mode}_seed{seed}_src{source}.json';d=json.loads(rp.read_text());files.add(rp);assert d['simulation_completed'] and d['simulator_returncode']==0
   for n,h in d['sha256'].items():assert sha(ROOT/n)==h,n
   w=np.loadtxt(rp.with_suffix('.dat'),skiprows=1);assert w.shape[1]==9 and np.isfinite(w).all() and np.all(np.diff(w[:,0])>=0) and abs(w[-1,0]-315e-6)<1e-12
   for key,v in d['measurements'].items():
    m=re.fullmatch(r'(low|mid|high)_c([0-2])_(state|aux)_(before|sharing|after|rearmed|late)',key);assert m;tag,k,node,phase=m.groups();idx=1+2*['low','mid','high'].index(tag)+['state','aux'].index(node);t=100*int(k)+dict(before=19,sharing=20.45,after=21.5,rearmed=31.5,late=99.5)[phase];assert abs(v-np.interp(t*1e-6,w[:,0],w[:,idx]))<6e-6
   observed=d['first_complete_cycle_slope'];nearest=min(({'actor':actor['actor'],'channel':i,'trained_beta':beta,'absolute_beta_difference':abs(beta-observed)} for actor in inventory['actors'] for i,beta in enumerate(actor['beta'])),key=lambda x:x['absolute_beta_difference'])
   cases.append({'report':rp.relative_to(ROOT).as_posix(),'cell':cell,'mode':mode,'seed':seed,'observed_complete_cycle_slope':observed,'frozen_comparator_slope':d['comparison_slope'],'aux_reference_v':d['frozen_auxiliary_reference_v'],'worst_three_cycle_residual_v':d['worst_cumulative_residual_v'],'nearest_inventory_beta_for_context_only':nearest,'primary_measures_verified':True})
 result={'audit_completed':True,'geometries':geometries,'cases':cases,'conclusion':'Real M4/M5 overlap provides sub50fF auxiliary increments and useful physical ratio tuning; includes increased auxiliary ground capacitance. Five bounded complete-cycle cases support geometry development. Nearest inventory beta is context only, not exact trained-beta implementation or accuracy tolerance. Each geometry has a separately frozen reference; common bank reference unqualified.','scope':'Full physical checks and extracted-cap transient,315us/3cycles100us period, nominal plus one seed for small overlap, external ideal reference/data and native inverter clocks. No RPEX, dielectric leakage/native sampled noise/PVT/yield,5ms retention, complete PLIF/accuracy/service/full-chip acceptance. Metal overlap area is inside a spacious existing fixture; not replicated dense-array area or the earlier MIM2fF/um2 area assumption.','acceptance':{'learned_beta_coverage':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'geometries':geometries,'checked_cases':len(cases)},indent=2))
if __name__=='__main__':main()
