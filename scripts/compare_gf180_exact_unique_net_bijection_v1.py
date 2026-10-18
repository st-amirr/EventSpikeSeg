"""Exact linear primitive/edge proof after a uniquely proposed net bijection."""
from pathlib import Path
import argparse,json,collections
from compare_gf180_exact_hierarchy_graph_deep_v2 import parse,graph,refine,sha

def compare(g,h):
 refine([g,h]);gs={};hs={}
 for graph1,dest in [(g,gs),(h,hs)]:
  for n in graph1:
   if n[0]=='net':
    c=graph1.nodes[n]['color'];assert c not in dest,'Ambiguous net color: method inapplicable, not accepted';dest[c]=n
 assert set(gs)==set(hs);mapping={gs[c]:hs[c] for c in gs};refs=collections.defaultdict(list)
 def pins(graph1,dev,nmap):
  out=collections.defaultdict(list)
  for pin in graph1[dev]:
   nets=[n for n in graph1[pin] if n[0]=='net'];assert len(nets)==1
   out[(graph1.nodes[pin]['base'],nmap[nets[0]])].append(pin)
  return out
 def sig(graph1,dev,nmap):
  ps=pins(graph1,dev,nmap);return (graph1.nodes[dev]['base'],tuple(sorted((k,len(v)) for k,v in ps.items())))
 identity={n:n for n in h if n[0]=='net'}
 for n in h:
  if n[0]=='device':refs[sig(h,n,identity)].append(n)
 for dev in g:
  if dev[0]!='device':continue
  key=sig(g,dev,mapping);assert refs[key],('Missing exact native primitive',key)
  other=refs[key].pop();mapping[dev]=other;ps=pins(g,dev,mapping);qs=pins(h,other,identity);assert set(ps)==set(qs)
  for key in ps:
   assert len(ps[key])==len(qs[key]);mapping.update(zip(ps[key],qs[key]))
 assert not any(refs.values());assert len(mapping)==len(set(mapping.values()))==len(g)==len(h)
 assert all(g.nodes[u]['base']==h.nodes[v]['base'] for u,v in mapping.items())
 assert len(g.edges)==len(h.edges) and all(h.has_edge(mapping[u],mapping[v]) for u,v in g.edges)
 return dict(exact_interface_connectivity_and_device_dimensions=True,source_graph_nodes=len(g),source_graph_edges=len(g.edges),unique_net_bijection=len(gs),complete_bijective_node_mapping_and_every_edge_verified=True)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--other',required=True);ap.add_argument('--report',required=True);a=ap.parse_args();p=Path(a.source);o=Path(a.other);rp=Path(a.report);assert not rp.exists();s=parse(p.read_text());t=parse(o.read_text());assert set(s)==set(t);checks=[]
 for name in sorted(s):
  assert set(s[name][0])==set(t[name][0]);r=compare(graph(s,name),graph(t,name));r['subcircuit']=name;r['source_instances']=len(s[name][1]);r['other_instances']=len(t[name][1]);checks.append(r)
 r=dict(all_subcircuits_compositionally_equivalent=True,checks=checks,method='Fixed named external ports, native primitive model/W/L/R/MIM dimensions and role-labeled pins.128round colors only propose a unique net mapping; ambiguity rejects this method. Then a complete primitive/pin/node bijection and every original edge plus base attribute are checked explicitly. Repeated indistinguishable device records paired by exact mapped-net/pin-role signatures. Hash agreement alone cannot accept. MOS D/S, resistor ends and MIM plates may permute per existing PDK LVS.',property_scope='Connectivity and device dimensions only; native area/perimeter remain unchanged in simulation. No independent fresh flat DRC, analog accuracy, noise, service or fullchip acceptance.',sha256={str(x):sha(x) for x in [p,o,Path(__file__),Path(__file__).with_name('compare_gf180_exact_hierarchy_graph_deep_v2.py')]});rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(checks))
if __name__=='__main__':main()
