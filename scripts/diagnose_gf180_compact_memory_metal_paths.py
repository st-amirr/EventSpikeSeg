"""Read-only rectangle connectivity diagnosis of the two preserved compact prototypes."""
from pathlib import Path
import collections,json,re
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def main():
 cases=[]
 for version in [1,2]:
  cell=f'gf180_compact_analog_memory_4t_v{version}';p=B/'layout'/cell/(cell+'.mag');layer=None;boxes=[];pins={}
  for line in p.read_text().splitlines():
   if line.startswith('<< '):layer=line[3:-3]
   elif line.startswith('rect ') and layer in ['metal1','metal2','metal3','metal4','metal5','via1','via2','via3','via4']:
    b=list(map(int,line.split()[1:]));boxes.append((layer,b))
   elif line.startswith('rlabel '):
    t=line.split();pins[t[-1]]=(t[1],list(map(int,t[3:7])))
  def overlap(a,b):return min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])
  def metals(layer):return {layer} if layer.startswith('metal') else {'metal'+layer[-1],'metal'+str(int(layer[-1])+1)}
  adj=collections.defaultdict(set)
  for i,(a,aa) in enumerate(boxes):
   for j in range(i):
    b,bb=boxes[j]
    if metals(a)&metals(b) and overlap(aa,bb):adj[i].add(j);adj[j].add(i)
  targets={pin:[i for i,(lay,b) in enumerate(boxes) if pl in metals(lay) and overlap(pb,b)] for pin,(pl,pb) in pins.items()}
  paths=[]
  for a,b in [('STATE','WRITEB'),('STATE','VDD'),('VDD','READOUT')]:
   todo=collections.deque(targets[a]);parents={i:None for i in todo};end=None
   while todo:
    i=todo.popleft()
    if i in targets[b]:end=i;break
    for j in adj[i]:
     if j not in parents:parents[j]=i;todo.append(j)
   path=[]
   while end is not None:path.append(dict(layer=boxes[end][0],box=boxes[end][1]));end=parents[end]
   paths.append(dict(pins=[a,b],explicit_metal_overlap_path=list(reversed(path))))
  cases.append(dict(cell=cell,paths=paths))
 report=B/'results/gf180_compact_memory_metal_short_diagnosis_v1.json';assert not report.exists()
 report.write_text(json.dumps(dict(diagnosis_completed=True,cases=cases,
  scope='Exact positive-area overlap paths through explicitly painted metal/via rectangles only. Native implicit contacts, diffusion and substrate conduction are not modeled by this diagnostic; extraction remains authoritative. This is a routing-cause aid, not LVS.'),indent=2)+'\n');print(json.dumps(cases,indent=2))
if __name__=='__main__':main()
