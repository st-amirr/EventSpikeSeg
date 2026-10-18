"""Check one physical actor parent against independent native-child reference."""
from pathlib import Path
import argparse,json,hashlib,subprocess
from gf180_compact_lvs_v2 import compact
R=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--directory',required=True);ap.add_argument('--top',default='ESS_ACTOR_00');a=ap.parse_args();d=R/a.directory;out=d/'parent_exact_connectivity_attempt.json';assert not out.exists()
 source,sm=compact((d/'parent.spice').read_text(),a.top);reference,rm=compact((d/'reference.spice').read_text(),'reference')
 report=dict(native_primitives=sm['primitive_devices'],reference_primitives=rm['primitive_devices'],missing_native_ports=sorted(set(rm['port_order'])-set(sm['port_order'])),extra_native_ports=sorted(set(sm['port_order'])-set(rm['port_order'])),independent_connectivity_accepted=False)
 if not report['missing_native_ports'] and not report['extra_native_ports']:
  p=d/'exact_native.spice';q=d/'exact_reference.spice';assert not p.exists() and not q.exists();p.write_text(source.replace('.subckt '+a.top+' ','.subckt parent ',1));q.write_text(reference.replace('.subckt reference ','.subckt parent ',1));gp=d/'exact_connectivity.json';lp=d/'exact_connectivity.log'
  cmd=['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:torch2.2.2-cuda11.8','120','python','scripts/compare_gf180_exact_unique_net_bijection_v1.py','--source',p.relative_to(R).as_posix(),'--other',q.relative_to(R).as_posix(),'--report',gp.relative_to(R).as_posix()]
  run=subprocess.run(cmd,capture_output=True,text=True,timeout=135);lp.write_text(run.stdout+run.stderr);report.update(exact_graph_returncode=run.returncode,exact_graph_report=gp.relative_to(R).as_posix() if gp.exists() else None,independent_connectivity_accepted=run.returncode==0 and gp.exists() and json.loads(gp.read_text())['all_subcircuits_compositionally_equivalent'])
 report['scope']='Native extracted parent and separately composed original native child reference, all1191primitives and fixed named external/interface ports. No analog accuracy or whole-chip claim.';report['sha256']={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),d/'parent.spice',d/'reference.spice']};out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
