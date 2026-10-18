"""Bounded native C extraction from the already checked v4 flattened actor geometry."""
from pathlib import Path
import hashlib,json,re,shlex,subprocess
from resume_gf180_formatted64_completed_flat_v2 import branches_units
R=Path(__file__).resolve().parents[1]
B=R/'artifacts/analog_asic'
D=B/'assembly/full25_external_bank_service_v5/verification/actor_00_external_service_v5'
Q=D.parent/'actor_00_external_service_fullcap_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 prior=json.loads((D/'qualification_attempt.json').read_text());exact=json.loads((D/'parent_exact_connectivity_attempt.json').read_text())
 assert prior['full_parent_drc_count']==0 and exact['independent_connectivity_accepted']
 assert not Q.exists();Q.mkdir();root=prior['top_cell'];src=D/(root+'.mag');mag=Q/src.name;mag.write_bytes(src.read_bytes());assert not re.search(r'(?m)^use ',mag.read_text())
 t=f'drc off\nload {root}\nextract no resistance\nextract no adjust\nextract all\nputs "PHASE native C extracted"\next2spice lvs\next2spice hierarchy off\next2spice subcircuit top on\next2spice cthresh 0\next2spice scale off\next2spice -o parent_fullcap.spice\nputs "PHASE full C exported"\nquit -noprompt\n'
 tp=Q/'fullcap_extract.tcl';tp.write_text(t);pd=B/'pdk/gf180_open_pdks_source/gf180mcu/gf180mcuD'
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','-i','--volume',f'{R}:/workspace','--workdir','/workspace/'+Q.relative_to(R).as_posix(),'--entrypoint','timeout','eventspikeseg:analog-gf180-layout','120','magic','-dnull','-noconsole','-rcfile','/workspace/'+(pd/'libs.tech/magic/gf180mcuD.magicrc').relative_to(R).as_posix()],input=t,capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=Q/'native_fullcap.log';lp.write_text(log);dest=Q/'parent_fullcap.spice';ext=Q/(root+'.ext');complete=run.returncode==0 and 'PHASE full C exported' in log and dest.exists() and ext.exists()
 o=dict(native_command_returncode=run.returncode,full_cap_extraction_completed=complete,all_native_devices_and_ports_unchanged=False,all_native_substrate_caps_verified=False,parent_nominal_simulation_completed=False,full_chip_complete=False,scope='Fresh capacitance/coupling extraction from actual v4 saved flat GDS geometry. Reuses matching GDS full DRC and exact 2362-device connectivity; no repeated flat DRC. Resistance and device adjust disabled as in qualified connectivity view. No hierarchical or hand-fitted substitute. A partial export cannot qualify simulation.')
 if complete:
  tokens=lambda p:[l.split() for l in p.read_text().replace('\n+',' ').splitlines() if l.startswith('X') or l.lower().startswith('.subckt ')]
  same=tokens(dest)==tokens(D/'parent.spice');cs=branches_units(dest,root);expected={s[1]:float(s[3])*1e-18 for l in ext.read_text().splitlines() if l.startswith('node ') for s in [shlex.split(l)]};errs={n:[v,cs.get(tuple(sorted((n,'VSS'))),0)] for n,v in expected.items() if abs(cs.get(tuple(sorted((n,'VSS'))),0)-v)>max(5e-18,abs(v)*5e-5)}
  o.update(all_native_devices_and_ports_unchanged=same,all_native_substrate_caps_verified=not errs,substrate_mismatches=errs,linear_branch_count=len(cs),negative_capacitance_branches=sum(v<0 for v in cs.values()),native_primitives=exact['native_primitives'])
 o['sha256']={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),src,mag,tp,lp,D/'qualification_attempt.json',D/'parent_exact_connectivity_attempt.json']+([dest,ext] if complete else [])};(Q/'qualification.json').write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k!='sha256'},indent=2))
if __name__=='__main__':main()
