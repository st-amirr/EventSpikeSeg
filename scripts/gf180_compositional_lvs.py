"""Exact hierarchical graph LVS with native reference and explicit proof provenance."""
from pathlib import Path
import re,json,subprocess
import probe_gf180_mos_gate_cap as flow
ROOT=Path(__file__).resolve().parents[1]
def compare(source,reference,cell,tag):
 out=flow.OUT;copy=out/(tag+'_reference_graph.spice');text=reference.read_text();assert re.search(r'(?m)^\.subckt reference\s',text);text=re.sub(r'(?m)^\.subckt reference(?=\s)', '.subckt '+cell,text);assert not copy.exists();copy.write_text(text);report=out/(tag+'_exact_graph_qualification.json');assert not report.exists();cmd=['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:torch2.2.2-cpu-verification-guarded','120','python','scripts/compare_gf180_exact_hierarchy_graph.py','--source',source.relative_to(ROOT).as_posix(),'--other',copy.relative_to(ROOT).as_posix(),'--report',report.relative_to(ROOT).as_posix()];p=subprocess.run(cmd,capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=out/(tag+'_exact_graph.log');lp.write_text(log);assert p.returncode==0,log[-2000:];assert json.loads(report.read_text())['all_subcircuits_compositionally_equivalent'];return log,[copy,report,lp]
