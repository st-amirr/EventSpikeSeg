"""Exact compositional device/ordered-interface graph comparison for GF180 extraction views."""
from pathlib import Path
from decimal import Decimal
import re,json,hashlib,argparse
import networkx as nx
from collections import Counter,defaultdict

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(text):
 text=text.replace('\n+',' ');out={}
 for name,ports,body in re.findall(r'(?ms)^\.subckt\s+(\S+)\s+([^\n]*)\n(.*?)^\.ends[^\n]*',text):
  out[name]=(ports.split(),[line.split() for line in body.splitlines() if line.startswith('X')])
 return out

def number(s):
 m=re.fullmatch(r'([0-9.eE+-]+)([munpf]?)',s);assert m,s
 return str((Decimal(m[1])*{'':Decimal(1),'m':Decimal('1e-3'),'u':Decimal('1e-6'),'n':Decimal('1e-9'),'p':Decimal('1e-12'),'f':Decimal('1e-15')}[m[2]]).normalize())

def graph(defs,top):
 ports,body=defs[top];g=nx.Graph()
 for p in ports:g.add_node(('net',p),base='PORT:'+p)
 for i,t in enumerate(body):
  k=next((j for j,v in enumerate(t[1:],1) if '=' in v),len(t));model=t[k-1];nodes=t[1:k-1];params=dict(v.split('=',1) for v in t[k:]);kind='HIER:'+model
  if model in defs:roles=defs[model][0];assert len(nodes)==len(roles)
  elif model in ['nfet_03v3','pfet_03v3']:
   assert len(nodes)==4;roles=['DS','G','DS','B'];kind=model+':'+json.dumps({p:number(params[p]) for p in ['w','l']},sort_keys=True)
   assert set(params)<=set(['w','l','ad','pd','as','ps','m']),params
   if 'm' in params:kind+=':m='+number(params['m'])
  elif model=='ppolyf_u_1k':
   assert len(nodes)==3;roles=['END','END','BODY'];kind=model+':'+json.dumps({p:number(params[p]) for p in ['r_width','r_length']},sort_keys=True);assert set(params)=={'r_width','r_length'}
  elif model=='cap_mim_2f0_m4m5_noshield':
   assert len(nodes)==2;roles=['PLATE','PLATE'];kind=model+':'+json.dumps({p:number(params[p]) for p in ['c_width','c_length']},sort_keys=True);assert set(params)=={'c_width','c_length'}
  else:raise AssertionError((top,model,params))
  dev=('device',i);g.add_node(dev,base='DEVICE:'+kind)
  for j,(n,role) in enumerate(zip(nodes,roles)):
   net=('net',n)
   if net not in g:g.add_node(net,base='INTERNAL_NET')
   pin=('pin',i,j);g.add_node(pin,base='PIN:'+role);g.add_edge(dev,pin);g.add_edge(pin,net)
 return g

def refine(gs):
 for g in gs:
  for n in g:g.nodes[n]['color']=hashlib.sha256(g.nodes[n]['base'].encode()).hexdigest()
 for _ in range(12):
  for g in gs:
   colors={n:hashlib.sha256((g.nodes[n]['color']+'|'+'|'.join(sorted(g.nodes[v]['color'] for v in g[n]))).encode()).hexdigest() for n in g}
   for n,c in colors.items():g.nodes[n]['color']=c

def component_compare(g,h):
 # Fixed external ports are matched by name, then their incident connections
 # are encoded in pin labels. This exact factorization avoids high-degree
 # supply nets dominating VF2 search; no edge is ignored in the final proof.
 pg={a['base']:n for n,a in g.nodes(data=True) if a['base'].startswith('PORT:')}
 ph={a['base']:n for n,a in h.nodes(data=True) if a['base'].startswith('PORT:')}
 if set(pg)!=set(ph):return False,{},{}
 sg=g.copy();sh=h.copy();mapping={pg[k]:ph[k] for k in pg}
 for graph,ports in [(sg,pg),(sh,ph)]:
  for name,n in ports.items():
   for pin in list(graph[n]):graph.nodes[pin]['base']+='|TO_'+name
  graph.remove_nodes_from(ports.values())
 refine([sg,sh]);groups=[]
 for graph in [sg,sh]:
  bucket=defaultdict(list)
  for cc in nx.connected_components(graph):
   key=tuple(sorted(Counter((graph.nodes[n]['base'],graph.nodes[n]['color']) for n in cc).items()))
   bucket[key].append(graph.subgraph(cc))
  groups.append(bucket)
 a,b=groups
 stats={'component_count':sum(len(v) for v in a.values()),'largest_component_nodes':max((len(c) for v in a.values() for c in v),default=0),'fixed_external_ports':len(pg)}
 if set(a)!=set(b):return False,{},stats
 for key,components in a.items():
  candidates=list(b[key])
  if len(components)!=len(candidates):return False,{},stats
  for component in components:
   found=False
   for j,other in enumerate(candidates):
    matcher=nx.algorithms.isomorphism.GraphMatcher(component,other,node_match=lambda a,b:a['base']==b['base'] and a['color']==b['color'])
    if matcher.is_isomorphic():mapping.update(matcher.mapping);candidates.pop(j);found=True;break
   if not found:return False,{},stats
 # Reconstruct and explicitly verify the complete original graph, including
 # all fixed-port edges, rather than treating component hashes as proof.
 if len(mapping)!=len(g) or len(set(mapping.values()))!=len(h) or len(g.edges)!=len(h.edges):return False,{},stats
 if not all(h.has_edge(mapping[u],mapping[v]) for u,v in g.edges):return False,{},stats
 if not all(g.nodes[u]['base']==h.nodes[v]['base'] for u,v in mapping.items()):return False,{},stats
 return True,mapping,stats

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--other',required=True);ap.add_argument('--report',required=True);a=ap.parse_args();p=Path(a.source);o=Path(a.other);rp=Path(a.report);assert not rp.exists();s=parse(p.read_text());t=parse(o.read_text());assert set(s)==set(t),(set(s)-set(t),set(t)-set(s));checks=[]
 for name in sorted(s):
  assert set(s[name][0])==set(t[name][0]);g=graph(s,name);h=graph(t,name);ok,mapping,stats=component_compare(g,h)
  if ok:
   assert len(mapping)==len(g)==len(h);assert all(h.has_edge(mapping[u],mapping[v]) for u,v in g.edges);assert len(g.edges)==len(h.edges)
  checks.append({'subcircuit':name,'exact_interface_connectivity_and_device_dimensions':ok,'component_factorization':stats,'source_instances':len(s[name][1]),'other_instances':len(t[name][1])});print(name,ok,flush=True)
 r={'all_subcircuits_compositionally_equivalent':all(x['exact_interface_connectivity_and_device_dimensions'] for x in checks),'checks':checks,'method':'Fixed external port identities are factored into incident pin labels to partition the search. An exact component isomorphism reconstructs a bijection and checks every edge in the entire original graph, including all supply/port connections. Each entire subcircuit graph is independently isomorphic with fixed named external ports, exact native model and W/L or passive dimensions, ordered named hierarchical interface pins. Resistor ends, capacitor plates and MOS source/drain may permute, as in PDK LVS. Bijective graph mapping and every edge are explicitly checked; iterative hashes only constrain the search, never determine success. Every referenced subcircuit is included and independently checked, proving the composed hierarchy.','property_scope':'MOS diffusion area/perimeter are not a connectivity/device-sizing LVS acceptance criterion, consistent with PDK LVS; native extracted simulation views retain them unchanged. No geometry or netlist edit. This comparison does not qualify flat RC, noise, transient, accuracy, service or full-chip layout.','sha256':{str(x):sha(x) for x in [p,o,Path(__file__)]}};rp.write_text(json.dumps(r,indent=2)+'\n');assert r['all_subcircuits_compositionally_equivalent']
if __name__=='__main__':main()
