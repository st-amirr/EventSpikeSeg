"""Prove parent wiring by exact hierarchy equivalence and characterize native64-channel DC."""
from pathlib import Path
import re,json,hashlib,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def defs(text):
 return {n:(ports.split(),[l.split() for l in body.splitlines() if l.startswith('X')]) for n,ports,body in re.findall(r'(?ms)^\.subckt\s+(\S+)\s+([^\n]*)\n(.*?)^\.ends[^\n]*',text.replace('\n+',' '))}
def main():
 cell='gf180_formatted_energy64_v3';d=BASE/'layout'/cell;src=d/(cell+'.spice');ref=d/'reference.spice';s=defs(src.read_text());r=defs(ref.read_text());files={Path(__file__),src,ref,d/'drc_preflight.log',d/(cell+'.gds')};names=['gf180_product_gate_formatter_v3','gf180_energy_mean_root64_v1'];checks=[]
 for name in names:
  p=BASE/'layout'/name/(name+'.spice');q=BASE/'layout'/name/'qualification.json';qq=json.loads(q.read_text());assert sha(p)==qq['sha256'][p.name];own=defs(p.read_text());assert all(s[k]==v for k,v in own.items());checks.append({'child':name,'all_native_subcircuit_definitions_identical':True});files.update([p,q])
 assert s[cell][0]==r['reference'][0];expected={x[0]:x for x in r['reference'][1]};actual={x[0]:x for x in s[cell][1]};assert set(expected)==set(actual);mapping={p:p for p in s[cell][0]}
 for inst,a in actual.items():
  e=expected[inst];assert a[-1]==e[-1] and len(a)==len(e)
  for en,an in zip(e[1:-1],a[1:-1]):
   if en in mapping:assert mapping[en]==an,(inst,en,an,mapping[en])
   else:mapping[en]=an
 assert len(mapping)==len(set(mapping.values()));proof=BASE/'results/gf180_formatted_energy64_v3_exact_hierarchy_connectivity.json';assert not proof.exists();proof.write_text(json.dumps({'exact_parent_connectivity_pass':True,'qualified_children_identical':checks,'native_child_instances':len(actual),'bijective_parent_net_mapping':mapping,'scope':'Deterministic exact instance/model/ordered-pin comparison against separately built reference, with a bijective internal-net rename and fixed external ports. Every embedded native child definition equals its independently qualified original byte-token structure. This proves source hierarchy connectivity without accepting failed Netgen symmetry resolution. GDS readback, flat RC and full physical qualification remain incomplete.','netgen_full_flat_comparison_pass':False,'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files}},indent=2)+'\n');files.add(proof)
 stem=cell+'_native_hierarchy_dc_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();models=BASE/'pdk/gf180_primitive_source/models/ngspice';prefix='/workspace/'+models.relative_to(ROOT).as_posix();files.update(models.rglob('*.spice'));outputs=[BASE/'results'/(stem+'_'+tag+'.dat') for tag in ['zero','half','all']];ports=s[cell][0];nodes=[('ca' if int(p[9:])<32 else 'cb') if p.startswith('CANDIDATE') else p for p in ports];lines=['Native full candidate formatting and mean-root DC',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',src.read_text(),'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vbase VBASE 0 .9','Vzero VZERO 0 1.2','Vpen PENALTY 0 1.2','Iref BIAS 0 64u','Vca ca 0 1.2','Vcb cb 0 1.2','Xparent '+' '.join(nodes)+' '+cell,'.control','set numdgt=15','set wr_singlescale','set wr_vecnames']
 for i in range(3):
  if i==1:lines+=['alter Vca 2.0']
  if i==2:lines+=['alter Vcb 2.0']
  lines+=['op','wrdata /workspace/'+outputs[i].relative_to(ROOT).as_posix()+' v(ROOT) i(Vdd)']
 lines+=['quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp);result={'module_simulation_completed':False,'simulator_returncode':run.returncode,'full_physical_qualification_complete':False,'scope':'Actual64-channel native2304MOS2816resistor1024MIM source hierarchy, each candidate-minus-penalty formatter connected to its native energy kernel and all64 mean/root receivers. Three DC fixtures candidate1.2V for all,2.0V for half,2.0V for all; shared penalty1.2V,VBASE.9V,VZERO1.2V,VDD3.3V,64uA master. Source connectivity proven by exact hierarchy equivalence; source DRC0/GDS exists, but full flat Netgen ambiguity unresolved and GDS readback/flatRC qualification incomplete. DC omits linear routing capacitance, which does not affect operating points; not a transient or5ms/service/accuracy/full-chip result. Native device models, no fitted correction.','complete_RMS_accepted':False}
 try:
  rows=[np.loadtxt(p,skiprows=1).reshape(-1) for p in outputs];files.update(outputs);result['module_simulation_completed']=bool(run.returncode==0 and all(len(v)==3 and np.isfinite(v).all() for v in rows) and 'aborted' not in log.lower());result['cases']=[{'case':tag,'root_v':float(v[-2]),'supply_current_a':float(-v[-1]),'supply_power_w':float(-3.3*v[-1])} for tag,v in zip(['zero','half','all'],rows)]
 except Exception as e:result['postprocess_error']=str(e)
 result['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in files};rp.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='sha256'},indent=2));print(rp)
if __name__=='__main__':main()
