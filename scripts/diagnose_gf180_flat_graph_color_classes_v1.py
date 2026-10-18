from pathlib import Path
import argparse,json,collections
from compare_gf180_exact_hierarchy_graph_deep_v2 import parse,graph,refine
ap=argparse.ArgumentParser();ap.add_argument('--cell',required=True);a=ap.parse_args();d=Path('artifacts/analog_asic/layout')/a.cell;top=a.cell+'_flat'
g=graph(parse((d/'exact_source.spice').read_text()),top);h=graph(parse((d/'exact_reference.spice').read_text()),top);refine([g,h]);out=[]
for graph1 in [g,h]:
 groups=collections.defaultdict(list)
 for n in graph1:
  if n[0]=='net':groups[graph1.nodes[n]['color']].append(n[1])
 amb=[v for v in groups.values() if len(v)>1]
 out.append(dict(nodes=len(graph1),net_count=sum(map(len,groups.values())),unique_net_colors=sum(len(v)==1 for v in groups.values()),ambiguous_net_classes=amb))
r=dict(source=out[0],reference=out[1],method_review='OriginalVF2 and focusedVF2++ each exceeded120s. Diagnose whether fixed-port refined net colors uniquely identify an exact deterministic net bijection before choosing any further comparison. No runtime/tolerance sweep.');p=d/'flat_graph_color_diagnosis_v1.json';assert not p.exists();p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
