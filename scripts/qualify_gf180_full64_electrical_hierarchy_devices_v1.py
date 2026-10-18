"""Exact device proof for native hierarchical C expansion; no flat-C equivalence claim."""
from pathlib import Path
import hashlib,json
from gf180_compact_lvs_v2 import compact
from compare_gf180_exact_hierarchy_graph_v2 import parse,graph,component_compare
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(t):return '\n'.join('X'+l[1:].lower() if l.startswith(('x','X')) else l.lower() for l in t.splitlines())
def main():
 cell='gf180_full64_rms_frontend_v1';d=B/'layout'/cell;source=d/(cell+'.spice');ep=d/'electrical_hierarchy_expanded_cap_v2.spice';eq=ep.with_suffix('.json');e=json.loads(eq.read_text());assert e['passive_nonnegative_branch_network'] and not e['unresolved_hierarchical_names']
 st,_=compact(source.read_text(),cell);g=graph(parse(norm(st)),cell);h=graph(parse(norm(ep.read_text())),cell+'_electrical');ok,mapping,stats=component_compare(g,h);assert ok
 comparison=B/'results/gf180_hierarchical_cap_expansion_independent_flat_comparison_v3.json';r=json.loads(comparison.read_text());assert r['exact_primitive_graph_equivalent'] and not r['cap_matrix_matches_within_export_rounding']
 out=d/'electrical_hierarchy_qualification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(cell=cell,electrical_subcircuit=cell+'_electrical',exact_primitive_graph_equivalent=True,stats=stats,linear_branch_count=e['aggregate_cap_branch_count'],negative_aggregate_branches={},electrical_netlist=ep.relative_to(R).as_posix(),geometric_flat_extraction_completed=False,independent_flat_cap_equivalence_accepted=False,
  scope='Native hierarchical parasitic model with all signed child/parent corrections resolved and summed; actual device graph exactly matches independently source-qualified parent. All90640 aggregate branches nonnegative; no unresolved slash aliases. Independent full64 baseline geometric-flat comparison shows capacitance-model differences, including3.84pF ROOT-ground and45.52pF VDD-ground under one exact device-net bijection; not within export rounding. This native hierarchical model is exploratory and does not replace geometric-flat qualification. Preserve differences; no whole-model accuracy,5ms or fullchip claims.',
  sha256={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),source,ep,eq,comparison,R/'scripts/expand_gf180_hierarchical_capacitance_v2.py']}),indent=2)+'\n');print(out)
if __name__=='__main__':main()
