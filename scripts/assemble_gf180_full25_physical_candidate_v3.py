"""Whole-model physical integration candidate; completion flags reflect remaining interfaces."""
from pathlib import Path
import json,hashlib,math,struct,re,csv,html,collections
from assemble_gf180_full_capacity_storage_gds_v2 import records,rec,string,begin,reference,real8
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';OUT=B/'assembly/full25_physical_candidate_v3'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Library:
 def __init__(self):self.cells=[];self.maps={};self.inputs=set();self.prefix=None
 def load(self,p):
  if p in self.maps:return self.maps[p]
  rs=list(records(p.read_bytes()));units=next(v for t,d,v,b in rs if t==3);assert abs(real8(units[8:])*1e6-.001)<1e-12
  names=[v.rstrip(b'\0').decode() for t,d,v,b in rs if t==6];assert len(names)==len(set(names));tag=sha(p)[:8];mapping={n:'N'+tag+'_'+hashlib.sha256(n.encode()).hexdigest()[:16] for n in names}
  first=next(i for i,(t,d,v,b) in enumerate(rs) if t==5)
  if self.prefix is None:self.prefix=b''.join(b for t,d,v,b in rs[:first])
  active=False;body=b''
  for t,d,v,b in rs:
   if t==5:active=True;body=b''
   if active:body+=string(t,mapping[v.rstrip(b'\0').decode()]) if t in [6,18] else b
   if t==7:self.cells.append(body);active=False
  self.maps[p]=mapping;self.inputs.add(p);return mapping
 def add(self,name,body):self.cells.append(begin(name)+body+rec(7,0));return name

def rect(layer,b):
 x1,y1,x2,y2=map(round,b);assert x1<x2 and y1<y2
 xy=[x1,y1,x2,y1,x2,y2,x1,y2,x1,y1]
 return rec(8,0)+rec(13,2,struct.pack('>h',layer))+rec(14,2,struct.pack('>h',0))+rec(16,3,struct.pack('>10i',*xy))+rec(17,0)
def label(name,x,y,layer=81):
 return rec(12,0)+rec(13,2,struct.pack('>h',layer))+rec(22,2,struct.pack('>h',10))+rec(16,3,struct.pack('>2i',round(x),round(y)))+string(25,name)+rec(17,0)
def via(m1,m2,cut,x,y):return rect(m1,(x-600,y-600,x+600,y+600))+rect(m2,(x-600,y-600,x+600,y+600))+rect(cut,(x-140,y-140,x+140,y+140))
def pinlist(d,c):
 s=(d/(c+'.mag')).read_text();result={}
 for layer,x1,y1,x2,y2,pin in re.findall(r'^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)$',s,re.M):result[pin]=(layer,(int(x1)+int(x2))*2.5,(int(y1)+int(y2))*2.5)
 return result

def main():
 assert not OUT.exists();OUT.mkdir();lib=Library();inputs={Path(__file__)}
 sp=B/'assembly/full_capacity_storage_gds_v2/capacity_assembly.json';pp=B/'assembly/float_parameter_capacity_v1/parameter_capacity_assembly.json';gp=B/'assembly/full25actor_analog_connectivity_v1.json';popfile=B/'assembly/full25actor_original_float_population_manifest_v1.json';cp=B/'assembly/article_module_catalog_v95.json'
 storage,params,graph,pop,cat=[json.loads(p.read_text()) for p in [sp,pp,gp,popfile,cp]];inputs.update([sp,pp,gp,popfile,cp]);assert storage['logical_active_analog_nodes']==54630400 and graph['actor_count']==25;assert len({x['checkpoint_sha256'] for x in [storage,params,graph,pop,cat]})==1
 bank='gf180_underplate_biased_bank8x8_v1';bp=B/'layout'/bank/(bank+'.gds');bankmap=lib.load(bp);bn=bankmap[bank];top=b'';planes=[];replaced=0
 for e in storage['planes']:
  c,h,w=e['shape_chw'];ny,nx=e['bank_grid_yx'];px,py=e['bank_pitch_dbu'];cx,cy=e['channel_pitch_dbu'];cols=e['channel_grid_cols'];body=b'';replacement=e['state_kind']=='membrane'
  for ch in range(c):
   x=(ch%cols)*cx+7220;y=(ch//cols)*cy+12200
   if ch==0 and replacement:
    if nx>1:body+=reference(bn,x+px,y,nx-1,1,px,py)
    if ny>1:body+=reference(bn,x,y+py,nx,ny-1,px,py)
    replaced+=1
   else:body+=reference(bn,x,y,nx,ny,px,py)
  name=lib.add('ESS_STATE_'+str(e['plane_index']).zfill(2),body);top+=reference(name,*e['origin_dbu']);planes.append(dict(e,candidate_cell=name,first_channel_first_bank_replaced_by_actor_compute_tile=replacement,storage_access_to_other_banks_connected=False))
 assert replaced==25
 pg=B/'assembly/float_parameter_capacity_v1/float_parameter_capacity_v1.gds';pm=lib.load(pg);parameter_origin=[145000000,0];top+=reference(pm['FLOAT_PARAMETER_CAPACITY_TOP'],*parameter_origin)
 selected={};instances=[];actorrows=[];localnets=[];selected_counts=collections.Counter();x=0;y=125000000;shelf=0;maxx=165000000
 tile='gf180_shared_analog_compute_tile_v3';commit='gf180_bin_commit_controller_v2';event='gf180_event_phase_sequencer_v1';duration='gf180_guarded_weight_duration_parent_v2';inv='gf180_phase_inverter_fullroute';gate='gf180_reset_select_and_fullroute';expiry='gf180_resident_adaptation_expiry_v3';energy='gf180_formatted_energy64_v3';inhibit='gf180_peer_inhibition_v1'
 def select(c):
  if c not in selected:
   d=B/'layout'/c;qf=d/'qualification.json';q=json.loads(qf.read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'];p=d/(c+'.gds');assert sha(p)==q['sha256'][p.name];mapping=lib.load(p);pins=pinlist(d,c);assert set(pins)==set(q['ports']);selected[c]=(mapping[c],q,pins);inputs.update([qf,d/(c+'.mag')])
  return selected[c]
 for ai,a in enumerate(pop['actors']):
  owner=a['actor'];mods=[('compute',tile),('commit',commit),('event',event),('duration',duration),('sign_inverse',inv),('positive',gate),('negative',gate),('write_inverse',inv),('arm_inverse',inv),('sample_inverse',inv)]
  if a['peer_inhibition_enabled']:mods.append(('peer',inhibit))
  if a['adaptation_enabled']:
   mods +=[('sum_threshold',f"gf180_adaptation_sum{a['channels']}_threshold_v2"),('adaptation_characterization',expiry)]
   mods += [('energy64_'+str(i),energy) for i in range(a['channels']//64)]
  # One geometry column and one reserved escape column: distinct M4 lanes
  # across every row avoid the cross-row shorts of naive shelf routing.
  totalpins=sum(len(select(c)[2]) for inst,c in mods);margin=totalpins*2000+100000
  placements=[];sy=0;body=b'';width=0;pinbase=0
  for inst,c in mods:
   native,q,pins=select(c);bb=[round(v*1000) for v in q['bbox_um']];w=bb[2]-bb[0];h1=bb[3]-bb[1]
   dx=margin-bb[0];dy=sy-bb[1];body+=reference(native,dx,dy)
   placements.append(dict(instance=inst,cell=c,origin_dbu=[dx,dy],bbox_dbu=[margin,sy,margin+w,sy+h1],escape_start_index=pinbase))
   pinbase+=len(pins);sy+=h1+100000;width=max(width,margin+w+100000);selected_counts[c]+=1
  height=sy;bindings={}
  def bind(net,*ends):
   for inst,pin in ends:
    assert (inst,pin) not in bindings;bindings[inst,pin]=net
  bind('BETA_PHASE',('commit','BETA'),('compute','C_BETA'))
  bind('SUBTRACTIVE_RESET_PHASE',('commit','RESET_STATE'),('compute','C_RESET'))
  bind('DETECT_PHASE',('commit','DETECT'),('compute','C_SAMPLE'),('sample_inverse','IN'))
  bind('DETECT_PHASE_B',('sample_inverse','OUT'),('compute','C_SAMPLEB'))
  bind('WEIGHT_SAMPLE',('event','SAMPLE'),('duration','WRITE'),('write_inverse','IN'))
  bind('WEIGHT_SAMPLE_B',('write_inverse','OUT'),('duration','WRITEB'))
  bind('WEIGHT_ARM',('event','ARM'),('duration','ARM'),('arm_inverse','IN'))
  bind('WEIGHT_ARM_B',('arm_inverse','OUT'),('duration','ARMB'))
  bind('WEIGHT_PULSE',('duration','PULSE'),('positive','A'),('negative','A'))
  bind('WEIGHT_SIGN',('sign_inverse','IN'),('negative','B'))
  bind('WEIGHT_SIGN_B',('sign_inverse','OUT'),('positive','B'))
  bind('POSITIVE_INJECTION',('positive','Y'),('compute','C_POS'))
  bind('POSITIVE_INJECTION_B',('positive','YB'),('compute','C_POSB'))
  bind('NEGATIVE_INJECTION',('negative','Y'),('compute','C_NEG'))
  bind('NEGATIVE_INJECTION_B',('negative','YB'),('compute','C_NEGB'))
  if a['peer_inhibition_enabled']:
   bind('POSTRESET_STATE',('compute','C_STATE'),('peer','STATE'))
   bind('OWN_SPIKE',('compute','C_SPIKE'),('peer','OWN_SPIKE'))
   bind('PEER_INHIBIT_PHASE',('commit','INHIBIT'),('peer','INHIBIT'))
  grouped=collections.defaultdict(list)
  for p in placements:
   native,q,pins=selected[p['cell']]
   for pi,(pin,(layer,lx,ly)) in enumerate(pins.items()):
    if p['instance']=='compute' and (re.fullmatch(r'STATE[0-7][0-7]',pin) or pin in ['C_AUX','C_SENSE_OUT','C_SENSE_COMP'] or (pin=='C_STATE' and (p['instance'],pin) not in bindings)):continue
    net=pin if pin in ['VDD','VSS'] else bindings.get((p['instance'],pin),p['instance']+'__'+pin);grouped[net].append((p,pin,pi,layer,lx,ly))
  track0=height+50000
  for ni,(net,ends) in enumerate(grouped.items()):
   ty=track0+ni*3200;xx=[];pins1=[]
   for p,pin,pi,layer,lx,ly in ends:
    dx,dy=p['origin_dbu'];px=round(dx+lx);py=round(dy+ly);ex=50000+2000*(p['escape_start_index']+pi);xx.append(ex);pins1.append(p['instance']+'.'+pin)
    assert layer in ['metal1','metal3','metal4','metal5'],(p['cell'],pin,layer)
    if layer=='metal1':body+=via(34,36,35,px,py)+via(36,42,38,px,py)
    if layer=='metal4':body+=via(42,46,40,px,py)
    lay=42 if layer in ['metal1','metal3','metal4'] else 81;body+=rect(lay,(min(ex,px)-200,py-200,max(ex,px)+200,py+200));body+=via(lay,46,40 if lay==42 else 41,ex,py)
    body+=rect(46,(ex-200,min(py,ty)-200,ex+200,max(py,ty)+200))+via(46,81,41,ex,ty)
   body+=rect(81,(min(xx)-1000,ty-300,max(xx)+1000,ty+300))+label(net[:180],min(xx)-900,ty)
   localnets.append(dict(actor=owner,net=net,endpoint_pins=pins1,externally_supplied_or_unconsumed=len(ends)==1 or net in ['VDD','VSS']))
  height=track0+len(grouped)*3200+100000
  if x+width>140000000:x=0;y+=shelf+200000;shelf=0
  aname=lib.add('ESS_ACTOR_'+str(ai).zfill(2),body);top+=reference(aname,x,y);row=dict(actor=owner,gds_cell=aname,origin_dbu=[x,y],bbox_dbu=[x,y,x+width,y+height],modules=placements,resident_membranes=a['resident_membranes'],representative_compute_tile_resident_membranes=64,remaining_membrane_banks_access_unconnected=math.ceil(a['height']/8)*math.ceil(a['width']/8)*a['channels']-1,compute_lane_replication_selected=False,trained_parameter_distribution_connected=False,full_actor_function_accepted=False);actorrows.append(row)
  for p in placements:instances.append(dict(actor=owner,**p))
  x+=width+200000;shelf=max(shelf,height)
 maxy=y+shelf;readout='gf180_six_class_readout_v3';rn,rq,rpins=select(readout);rbb=[round(v*1000) for v in rq['bbox_um']];readout_origin=[145000000-rbb[0],10000000-rbb[1]];top+=reference(rn,*readout_origin);selected_counts[readout]+=1
 # Routed protocol corridors terminate at explicit interface pads. Addressing,
 # multiplicity handling, arbiters and physical driver/receiver binding are unfinished.
 routebase=maxy+200000;edges=[];routes=b'';nodeindex={n['name']:i for i,n in enumerate(graph['nodes'])};nodeby={n['name']:n for n in graph['nodes']};track=0;column_map={}
 def col(key):
  if key not in column_map:column_map[key]=1000000+len(column_map)*3200
  return column_map[key]
 for ei,e in enumerate(graph['edges']):
  src=nodeby[e['source']];bits=math.ceil(math.log2(math.prod(src['shape_chw'])));fields=['event_valid','spike_payload','multiplicity0','multiplicity1','complete','ready']+[f'address{k}' for k in range(bits)]+[f'bin_tag{k}' for k in range(24)];wires=[]
  for bi,field in enumerate(fields):
   yy=routebase+track*3200;track+=1;sx=col(('source',e['source'],field));dx=col(('destination',ei,field));sy=routebase-100000;dy=routebase-50000
   routes+=rect(46,(sx-200,sy-200,sx+200,yy+200))+rect(46,(dx-200,dy-200,dx+200,yy+200));routes+=rect(81,(min(sx,dx)-300,yy-300,max(sx,dx)+300,yy+300))+via(46,81,41,sx,yy)+via(46,81,41,dx,yy);routes+=label(f'E{ei:02d}_{field}_SOURCE_INTERFACE',sx,sy,46)+label(f'E{ei:02d}_{field}_DEST_INTERFACE',dx,dy,46);wires.append(dict(field=field,source_pad_dbu=[sx,sy],destination_pad_dbu=[dx,dy],track_y_dbu=yy))
  edges.append(dict(edge_index=ei,**e,address_bits=bits,wires=wires,driver_receiver_and_address_protocol_bound=False,scope='Physical routing corridor between declared categorical interface pads only; not a connected event network.'))
 routecell=lib.add('ESS_PROTOCOL_CORRIDORS',routes);top+=reference(routecell,0,0);topname=lib.add('ESS140K_PHYSICAL_CANDIDATE_V3',top);output=lib.prefix+b''.join(lib.cells)+rec(4,0);gds=OUT/'eventspikeseg140k_physical_candidate_v3.gds';gds.write_bytes(output)
 # Independent binary hierarchy traversal counts reachable capacity; never flatten
 # the full model into native SPICE or pretend record checks are chip DRC/LVS.
 cells={};refs=collections.defaultdict(list);cur=None;item=None
 for t,dt,v,b in records(output):
  if t==6:cur=v.rstrip(b'\0').decode();assert cur not in cells;cells[cur]=True
  if t in [10,11]:item={'count':1}
  if t==18:item['child']=v.rstrip(b'\0').decode()
  if t==19:item['count']=math.prod(struct.unpack('>2h',v))
  if t==17 and item:refs[cur].append(item);item=None
 assert all(r['child'] in cells for rs in refs.values() for r in rs)
 def count(root,target,trail=()):
  assert root not in trail
  return 1 if root==target else sum(r['count']*count(r['child'],target,trail+(root,)) for r in refs[root])
 assert count(topname,bn)==storage['physical_bank_instances']-25
 tm=lib.maps[B/'layout'/tile/(tile+'.gds')];assert count(topname,tm[bank])==25
 assert count(topname,tm[tile])==25
 covered=sum(p['active_state_count'] for p in planes);assert covered==54630400
 inputs.update(lib.inputs);inputs.add(B/'pdk/gf180_open_pdks_source/gf180mcu/gf180mcuD/libs.tech/magic/gf180mcuD.tech')
 missing=['Storage banks beyond the first64membranes peractor lack connected decoder/read/write/compute service.','Adaptation AGE/AMPLITUDE plane access and producer-to-sum/RMS paths are not bound.','128channel RMS final reduction is absent; two64channel blocks are placed components only.','Threshold voltage-domain/autozero interface and same-threshold subtractive reset are incomplete.','Global graph corridors end at interface pads: categorical address/handshake/multiplicity/join/fanout operators and macro endpoint binding are unfinished.','Parameter banks are unprogrammed capacity with continuous float targets; calibrated distribution/refresh and weight/state scales unqualified.','Readout class-current plane scan/accumulation interface and50ms retention unqualified.','Clock/reset/power/bias distribution and padframe unimplemented at fullchip level.','Parent local routing has not yet undergone native DRC/LVS/extraction.','Fullcycle model accuracy and5ms population throughput remain unproven.']
 manifest=dict(physical_candidate_gds_written=True,full_chip_layout_complete=False,full_chip_functional_layout_complete=False,full_5ms_population_service_accepted=False,original_float_accuracy_accepted=False,top_level_native_DRC_completed=False,top_level_native_LVS_completed=False,checkpoint_sha256=pop['checkpoint_sha256'],top_cell=topname,db_unit_um=.001,actor_count=25,state_planes=planes,active_analog_state_identities=covered,bank_capacity_instances=storage['physical_bank_instances'],storage_only_bank_instances=count(topname,bn),compute_tile_bank_instances=count(topname,tm[bank]),parameter_values=params['stored_parameter_values'],parameter_bank_count=params['physical_bank_count'],native_macro_instances=dict(selected_counts),actor_regions=actorrows,local_pin_nets=localnets,logical_graph_edges=54,physical_protocol_corridor_wires=sum(len(e['wires']) for e in edges),protocol_edges=edges,protocol_endpoint_binding_complete=False,atlas_bbox_um=[0,0,maxx*.001,(routebase+track*3200+100000)*.001],footprint_is_not_dense_die_area=True,compute_tiles_cover_only_first64_membranes_per_actor=1600,missing_interfaces=missing,scope='Whole-model physical integration candidate, not completed functional ASIC. All54,630,400active identities and147,567parameter capacity values included.25original first-bank state allocations are moved into real connected shared64state compute tiles without duplicating those resident identities. Existing native device geometry preserved via unique namespace import. Resident STATE debug pads are not extended into top-level debug buses. Local event-duration-signed-injection and selected bin-phase nets physically routed to real module pins; parent DRC/LVS/simulation pending. All54graph edges have physical categorical bus corridors ending at explicitly unbound interface pads. Sparse characterization module placements are not dense area or selected lane replication. No fullmodel SPICE, QAT or numerical-state digitization.',sha256={p.relative_to(R).as_posix():sha(p) for p in inputs|{gds}})
 (OUT/'physical_assembly.json').write_text(json.dumps(manifest,indent=2)+'\n')
 with (OUT/'local_pin_bindings.csv').open('w',newline='') as f:
  wr=csv.writer(f);wr.writerow(['actor','net','endpoint_pins','external_or_unconsumed']);wr.writerows([r['actor'],r['net'],';'.join(r['endpoint_pins']),r['externally_supplied_or_unconsumed']] for r in localnets)
 overview(OUT,manifest,storage,params)
 print(json.dumps({'gds':gds.relative_to(R).as_posix(),'bytes':len(output),'actors':25,'state_identities':covered,'local_nets':len(localnets),'graph_corridor_wires':manifest['physical_protocol_corridor_wires'],'full_chip_functional_layout_complete':False,'missing_interfaces':missing},indent=2))

def overview(out,m,storage,params):
 width,height=m['atlas_bbox_um'][2:];scale=1000/width;vbheight=height*scale+100;s=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="'+str(round(vbheight+100))+'" viewBox="-40 -60 1200 '+str(vbheight+100)+'">','<rect x="-40" y="-60" width="1200" height="'+str(vbheight+100)+'" fill="#0c1423"/>','<text x="0" y="-30" fill="white" font-size="20">EventSpikeSeg140k: physical integration candidate</text>','<text x="0" y="-8" fill="#fbbf24" font-size="12">Complete resident capacity; functional interfaces and whole-chip verification unfinished</text>']
 def box(bb,color,title):
  x,y,x2,y2=bb;s.append(f'<rect x="{x*scale:.3f}" y="{y*scale:.3f}" width="{(x2-x)*scale:.3f}" height="{(y2-y)*scale:.3f}" fill="{color}" fill-opacity=".4" stroke="{color}" stroke-width=".6"><title>{html.escape(title)}</title></rect>')
 for p in m['state_planes']:box([v*.001 for v in p['bbox_dbu']],'#38bdf8' if p['state_kind']=='membrane' else '#a78bfa',p['actor']+' / '+p['state_kind'])
 for a in m['actor_regions']:
  bb=[v*.001 for v in a['bbox_dbu']];box(bb,'#34d399',a['actor']+' / representative compute/control cluster');s.append(f'<text x="{bb[0]*scale+3:.2f}" y="{bb[1]*scale+12:.2f}" fill="white" font-size="9">{html.escape(a["actor"])}</text>')
 for e in params['arrays']:
  x,y=e['origin_dbu'];box([(145000000+x)*.001,y*.001,(145000000+x+e['bank_columns']*151420)*.001,(y+e['bank_rows']*114400)*.001],'#fbbf24',e['array'])
 if m['protocol_edges']:
  for e in m['protocol_edges']:
   w=e['wires'][0];x=w['source_pad_dbu'][0]*.001*scale;dx=w['destination_pad_dbu'][0]*.001*scale;y=w['track_y_dbu']*.001*scale;s.append(f'<path d="M{x:.2f} {y:.2f} H{dx:.2f}" stroke="#fb7185" stroke-width=".6" opacity=".7"/>')
 s.append('</svg>');(out/'assembly_overview.svg').write_text(''.join(s))
if __name__=='__main__':main()
