"""Construct original-float executed signal graph and permanent analog-state selectors."""
from pathlib import Path
import ast,hashlib,json,math
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 popp=B/'assembly/full25actor_original_float_population_manifest_v1.json'
 refp=B/'model_reference/eventspikeseg140k_float_reference.json'
 arrp=B/'model_reference/eventspikeseg140k_float_parameters.npz'
 pop=json.loads(popp.read_text());ref=json.loads(refp.read_text());arr=np.load(arrp)
 assert pop['checkpoint_sha256']==ref['checkpoint_sha256']
 assert all(sha(R/n)==h for n,h in pop['sha256'].items())
 metadata={a['name']:a for a in ref['effective_folded_weight_and_neuron_parameters']}
 actors={a['actor']:a for a in pop['actors']};nodes={};edges=[]
 source=R/'src/eventspikeseg/model.py';components=R/'src/eventspikeseg/model_components.py'
 tree=ast.parse(source.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='EventSpikeSeg140k')
 forward=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
 # Pin the reviewed forward expressions and inherited block semantics to exact source.
 text=ast.unparse(forward)
 assert 'semantic = semantic + x1' in text
 assert 'torch.cat((d2, x2), dim=2)' in text and 'torch.cat((semantic, detail), dim=2)' in text
 assert 'output = torch.clamp(output + sequence, 0.0, 1.0)' in components.read_text()
 assert 'residual=True' in ast.unparse(tree)
 def node(name,kind,shape,**kw):
  assert name not in nodes;nodes[name]=dict(name=name,kind=kind,shape_chw=list(shape),**kw);return name
 def edge(src,dst,port,**kw):
  assert src in nodes and dst in nodes
  edges.append(dict(source=src,destination=dst,destination_port=port,**kw))
 def actor(name,src):
  a=actors[name];m=metadata[name];key=name.replace('.','__');w=arr['weight__'+key]
  assert list(w.shape)==a['synaptic_weight_shape_oihw']
  ci,hi,wi=nodes[src]['shape_chw'];co,cin,kh,kw=w.shape;groups=m['conv_groups']
  assert ci==cin*groups and co==a['channels']
  st=m['conv_stride'];pad=m['conv_padding'];di=m['conv_dilation']
  ho=(hi+2*pad[0]-di[0]*(kh-1)-1)//st[0]+1
  wo=(wi+2*pad[1]-di[1]*(kw-1)-1)//st[1]+1
  assert (ho,wo)==(a['height'],a['width'])
  node(name,'analog_PLIF_actor',(co,ho,wo),parameter_arrays=[n for n in arr.files if n.endswith('__'+key)],
   weight_array='weight__'+key,affine_gain_already_folded_into_weight=True,
   convolution=dict(groups=groups,stride=st,padding=pad,dilation=di,kernel_hw=[kh,kw],
    input_coordinate_expression='iy=oy*stride_y-padding_y+ky*dilation_y; ix=ox*stride_x-padding_x+kx*dilation_x',
    input_channel_expression='ic=(oc//(Cout/groups))*(Cin/groups)+local_ic',
    out_of_bounds='zero; generate no weighted event'),
   adaptation_enabled=a['adaptation_enabled'],peer_inhibition_enabled=a['peer_inhibition_enabled'],
   numerical_state='resident analog charge; parameters original float reference',
   commit_contract='age advance; beta once plus all signed contributions; pre-reset all-channel RMS; threshold; subtractive reset/inhibit; spike-qualified adaptation write')
  edge(src,name,'presynaptic_events',preserve_input_multiplicity=True)
  return name
 def block(name,src,residual):
  branch=src
  if name+'.standard' in actors:branch=actor(name+'.standard',branch)
  else:
   branch=actor(name+'.depthwise',branch);branch=actor(name+'.pointwise',branch)
  if not residual:return branch
  assert nodes[src]['shape_chw']==nodes[branch]['shape_chw']
  dst=node(name+'.residual','binary_residual_clamp',nodes[src]['shape_chw'],
   expression='clamp(branch_spike+skip_spike,0,1)',categorical_binary_OR_valid=True)
  edge(branch,dst,'branch');edge(src,dst,'skip');return dst
 def up(name,src,target):
  c,h,w=nodes[src]['shape_chw'];ht,wt=target
  assert ht%h==0 and wt%w==0
  dst=node(name,'nearest_spike_fanout',(c,ht,wt),scale_hw=[ht//h,wt//w],
   input_coordinate_expression='iy=floor(oy/scale_y); ix=floor(ox/scale_x)',
   value_change=False,interpolated_analog_values=False)
  edge(src,dst,'input');return dst
 def concat(name,left,right):
  cl,h,w=nodes[left]['shape_chw'];cr,hr,wr=nodes[right]['shape_chw'];assert (h,w)==(hr,wr)
  dst=node(name,'channel_address_concatenation',(cl+cr,h,w),analog_sum=False)
  edge(left,dst,'lower_channels',destination_channel_start=0,destination_channel_end_exclusive=cl)
  edge(right,dst,'upper_channels',destination_channel_start=cl,destination_channel_end_exclusive=cl+cr)
  return dst
 inp=node('raw_event_ingress','raw_event_multiplicity',(2,440,640),binary_saturation_allowed=False,bin_us=5000)
 detail=block('detail1',actor('detail_stem',inp),True)
 x1=block('enc1_extra',block('enc1',actor('stem',inp),True),True)
 x2=block('enc2_extra',block('enc2',block('down2',x1,False),True),True)
 x3=block('enc3_extra',block('enc3',block('down3',x2,False),True),True)
 deepest=block('context2',block('context1',x3,True),True)
 d2=up('project3.nearest',actor('project3',deepest),nodes[x2]['shape_chw'][1:])
 d2=actor('decoder2_fuse',concat('decoder2.concat',d2,x2))
 semantic=up('project2.nearest',actor('project2',d2),nodes[x1]['shape_chw'][1:])
 merge=node('semantic.skip_sum','coincident_spike_multiplicity_sum',nodes[x1]['shape_chw'],
  expression='project2_spike+x1_spike',output_multiplicity_values=[0,1,2],binary_OR_allowed=False,
  implementation_contract='deliver both signed-weight contributions to downstream accumulator before one threshold')
 edge(semantic,merge,'decoder');edge(x1,merge,'encoder')
 semantic=up('semantic.nearest',merge,(440,640))
 final=block('final_fuse',concat('final.concat',semantic,detail),False)
 head=node('head.synapse','analog_class_current_accumulator',(6,440,640),weight_array='weight__head_synapse',
  kernel_hw=[1,1],class_PLIF=False,record_bins=10,record_us=50000,output_scale=6.0/10,
  expression='0.6*sum_over10bins(sum_over16channels(weight*hidden_spike))')
 assert arr['weight__head_synapse'].shape==(6,16,1,1)
 edge(final,head,'presynaptic_events');out=node('segmentation_logits','analog_readout',(6,440,640));edge(head,out,'class_current')
 assert len(nodes)==43 and len(edges)==54
 assert {n for n,v in nodes.items() if v['kind']=='analog_PLIF_actor'}==set(actors)
 depth={}
 for name,n in nodes.items():
  parents=[e['source'] for e in edges if e['destination']==name]
  assert all(p in depth for p in parents)
  depth[name]=max([depth[p] for p in parents],default=0)+(n['kind']=='analog_PLIF_actor')
 assert depth[out]==23
 files=[Path(__file__),popp,refp,arrp,source,components]
 provenance={p.relative_to(R).as_posix():sha(p) for p in files}
 gp=B/'assembly/full25actor_analog_connectivity_v1.json';assert not gp.exists()
 graph=dict(connectivity_construction_completed=True,checkpoint_sha256=ref['checkpoint_sha256'],
  actor_count=25,node_count=43,edge_count=54,nodes=list(nodes.values()),edges=edges,
  PLIF_depth_by_node=depth,maximum_same_bin_serial_PLIF_depth=23,
  same_bin_stage_budget_us_ignoring_all_routing_readout_and_handoff=5000/23,
  eight_by_eight_single_lane_per_channel_per_site_budget_us_ignoring_other_costs=5000/(23*64),
  control_is_categorical_only=True,quantized_numerical_state=False,
  full_chip_layout_complete=False,full_5ms_population_service_accepted=False,
  scope='Exact executed signal hierarchy constructed from reviewed original140k forward, native block residual clamp semantics and original epoch58 float parameter shapes. Nine binary residual clamps are distinct from the unclipped project2+x1 multiplicity sum. Three nearest-neighbor fanouts and two channel-address concatenations add no numerical state. This logical wiring contract is an input to physical assembly, not routed full-chip GDS or a proof of model accuracy/service. Depth23 constrains within-bin sharing; no one-lane64-site timing assumption is accepted.',sha256=provenance)
 gp.write_text(json.dumps(graph,indent=2)+'\n')
 planes=[];offset=0;tile=8
 for a in pop['actors']:
  for kind in ['membrane']+(['adaptation_age','adaptation_amplitude'] if a['adaptation_enabled'] else []):
   c,h,w=a['channels'],a['height'],a['width'];count=c*h*w;ty,tx=math.ceil(h/tile),math.ceil(w/tile)
   covered=sum(min(tile,h-y*tile)*min(tile,w-x*tile)*c for y in range(ty) for x in range(tx));assert covered==count
   planes.append(dict(actor=a['actor'],state_kind=kind,shape_chw=[c,h,w],logical_start=offset,
    logical_end_exclusive=offset+count,active_state_count=count,spatial_tile_hw=[8,8],tile_grid_yx=[ty,tx],
    spatial_tile_count=ty*tx,padded_array_cells=ty*tx*tile*tile*c,
    permanent_identity_expression='(actor,state_kind,c,y,x)',
    logical_index_expression=f'{offset}+c*{h*w}+y*{w}+x',
    selector_expression=f'tile=(y//8)*{tx}+x//8; channel=c; site=(y%8)*8+x%8',
    inverse_selector_expression=f'y=8*(tile//{tx})+site//8; x=8*(tile%{tx})+site%8; c=channel',
    valid_site_expression=f'0<=c<{c} and 0<=y<{h} and 0<=x<{w}',
    address_bits_are_categorical_selectors=True,numerical_state_encoding='analog charge',
    compute_lane_sharing_selected=False,dense_physical_cell=None,physical_instance_map=None))
   offset+=count
 c,h,w=6,440,640;count=c*h*w
 planes.append(dict(actor='head.synapse',state_kind='class_current',shape_chw=[c,h,w],logical_start=offset,
  logical_end_exclusive=offset+count,active_state_count=count,record_us=50000,numerical_state_encoding='analog accumulated charge',
  dense_physical_cell=None,physical_instance_map=None));offset+=count
 assert offset==pop['minimum_logical_analog_state_nodes_excluding_auxiliary_and_parameters']
 assert all(a['logical_end_exclusive']==b['logical_start'] for a,b in zip(planes,planes[1:]))
 sp=B/'assembly/full25actor_permanent_analog_state_selectors_v1.json';assert not sp.exists()
 sp.write_text(json.dumps(dict(selector_map_construction_completed=True,checkpoint_sha256=ref['checkpoint_sha256'],
  logical_analog_nodes=offset,planes=planes,no_cross_actor_or_state_plane_aliasing=True,
  analog_numeric_state_not_digitized=True,compute_lane_allocation_selected=False,
  full_chip_layout_complete=False,full_5ms_population_service_accepted=False,
  scope='Complete disjoint CHW identity ranges for every membrane, adaptation age/amplitude and readout class-current state. Eight-by-eight spatial storage selectors have exact active coverage including partial boundary tiles; padded sites are inactive. This is categorical addressing of permanent analog cells, not QAT or numerical-state quantization. It does not choose64-site compute sharing, supply dense physical geometry, route interconnect, or claim any measured chip area.',
  connectivity=gp.relative_to(R).as_posix(),sha256={**provenance,gp.relative_to(R).as_posix():sha(gp)}),indent=2)+'\n')
 print(json.dumps({'graph':str(gp),'nodes':len(nodes),'edges':len(edges),'same_bin_PLIF_depth':depth[out],
  'state_map':str(sp),'logical_analog_nodes':offset,'state_planes':len(planes)},indent=2))
if __name__=='__main__':main()
