"""Prepare a versioned full population class-score assembly using proven routing."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def main():
 old=(R/'scripts/assemble_gf180_adaptation_forest_service_v12.py').read_text()
 header=old[:old.index('def main():')].replace("assembly/full25_membrane_service_v10","assembly/full25_adaptation_service_v12").replace('assembly/full25_adaptation_service_v12\'\n','assembly/full25_class_current_service_v13\'\n')
 # Explicit directory replacement avoids changing the V12 input directory.
 header=header[:header.index('R=Path')]+"R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';S=B/'assembly/full25_adaptation_service_v12';F=B/'assembly/full_population_page_forest_v2';D=B/'assembly/full25_class_current_service_v13'\n\ndef sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()\n"
 pre="""def main():
 assert not D.exists();D.mkdir();mf=S/'physical_assembly.json';m=json.loads(mf.read_text());ff=F/'physical_forest.json';f=json.loads(ff.read_text());sg=S/'eventspikeseg140k_adaptation_service_v12.gds';prefix,cells=cells_read(sg.read_bytes());io='gf180_class_current_shared_io_v1';dd=B/'layout'/io;qf=dd/'qualification.json';q=json.loads(qf.read_text());assert q['source_and_GDS_exact_device_graphs_accepted'] and q['magic_drc_count']==q['gds_roundtrip_drc_count']==0;ig=dd/(io+'.gds');assert sha(ig)==q['sha256'][ig.name];lib=Library();icell=lib.load(ig)[io];pins=pinlist(dd,io);iv={'cell':icell,'bbox_dbu':[round(v*1000) for v in q['bbox_um']],'ports':{p:{'pin':p,'layer':81,'xy_dbu':[round(pins[p][1]),round(pins[p][2])]} for p in q['ports']}};assert all(pins[p][0]=='metal5' for p in q['ports'])
 readout='gf180_six_class_readout_v3';rd=B/'layout'/readout;rq=json.loads((rd/'qualification.json').read_text());rg=rd/(readout+'.gds');rcell=lib.load(rg)[readout];assert rcell in cells;rpins=pinlist(rd,readout);rv={'cell':rcell,'bbox_dbu':[round(v*1000) for v in rq['bbox_um']],'ports':{p:{'pin':p,'layer':81,'xy_dbu':[round(rpins[p][1]),round(rpins[p][2])]} for p in rq['ports']}};assert all(rpins[p][0]=='metal5' for p in rq['ports'])
 for blob in lib.cells:
  n=next(v.rstrip(b'\\0').decode() for t,d,v,b in __import__('assemble_gf180_full_capacity_storage_gds_v2').records(blob) if t==6)
  if n in cells:assert cells[n]==blob
  else:cells[n]=blob
 plane=next(p for p in f['planes'] if p['state_kind']=='class_current');forest=f['templates'][plane['root_cell']];fm={p:'FOREST__'+p for p in forest['ports']};fm.update(VCM='STORAGE_REFERENCE',VDD='VDD',VSS='VSS',RECOV='RECOV');fm.update({f'DATA{k}':f'DATA{k}' for k in range(8)})
 rm={p:p for p in rv['ports']};rm['VRESET']='COMPUTE_REFERENCE'
 # Move the existing physical readout out of the auxiliary root exactly once.
 aux='ESS_PARAMETER_PROTOCOL_RETAINED_V10';ae=list(elements(cells[aux]));removed=[e for e in ae if any(t==18 and v.rstrip(b'\\0').decode()==rcell for t,d,v,b in e)];assert len(removed)==1
 newaux='ESS_PARAMETER_PROTOCOL_RETAINED_V13';cells[newaux]=begin(newaux)+b''.join(b''.join(z for t,d,v,z in e) for e in ae if e not in removed)+rec(7,0)
 wrappers=[]
 for ai,unused in enumerate([0]):
  entries=[('FOREST',forest,fm),('READOUT',rv,rm),('IO',iv,{n:n for n in iv['ports']})];body=[];mods=[];groups=collections.OrderedDict();row_y=0;maxright=0;row_escapes=[]
"""
 a=old.index('  for tag,v,mapping in entries:');b=old.index('\n assert len(wrappers)',a)
 routing=old[a:b];start=routing.index("root=f'ESS_ADAPT_SERVICE_")
 routing=routing[:start]+"root='ESS_CLASS_CURRENT_SERVICE_V13';cells[root]=begin(root)+b''.join(body)+rec(7,0);w={'cell':root,'actor':'head.synapse','kind':'class_current_service','bbox_dbu':[hx-220,0,maxright,gy+220],'ports':ports,'modules':mods,'nets':nets,'native_parent_wiring_qualified':False,'active_class_current_states':1689600};wrappers.append(w)\n"
 views=""" views=[]
 for p in m['top_placements']:
  if p['kind']=='class_current':assert p['cell']==plane['root_cell'];views.append(wrappers[0]);continue
  ox,oy=p['origin_dbu'];bb=p['bbox_dbu'];views.append({'cell':newaux if p['cell']==aux else p['cell'],'kind':p['kind'],'bbox_dbu':[bb[0]-ox,bb[1]-oy,bb[2]-ox,bb[3]-oy]})
"""
 pack=old[old.index(' free=[(0,0,3000000000'):old.index(" top='ESS140K_ADAPTATION_SERVICE_V12'")]
 tail=""" top='ESS140K_CLASS_CURRENT_SERVICE_V13';cells[top]=begin(top)+b''.join(body)+rec(7,0);reach={}
 def visit(n):
  if n in reach:return
  reach[n]=cells[n]
  for e in elements(cells[n]):
   for t,d,v,b in e:
    if t==18:visit(v.rstrip(b'\\0').decode())
 visit(top);dest=D/'eventspikeseg140k_class_current_service_v13.gds';dest.write_bytes(prefix+b''.join(reach.values())+rec(4,0));o=dict(m);o.update(top_cell=top,top_placements=placed,class_current_service_wrapper=wrappers[0],active_class_current_physical_access_paths_built=1689600,all_numeric_state_access_paths_built=True,class_current_parent_wiring_qualified=False,full_chip_functional_layout_complete=False,full_chip_layout_complete=False,scope='Actual class forest RECOV joins shared native upshift/sixrestoreTGs to existing six-class workingstates; existing OUTPUTs join onehot sixTGmux/shared downshift/eightanalogholds back to forest DATA. Existing readout moved exactlyonce, allV12 membrane/adaptation geometry preserved. Native IO and readout independent module proofs; newparent wiring/RC/loading, trained synapses, globalgraph/operators/parameters/sequencer and modelaccuracy/5ms incomplete. Spacious research atlas, notcompactdie.');o['sha256']={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),mf,ff,sg,qf,ig,rg,dest]};(D/'physical_assembly.json').write_text(json.dumps(o,indent=2)+'\\n');print(json.dumps({'gds':str(dest),'bytes':dest.stat().st_size,'class_current_states':1689600,'all_numeric_access_paths_built':True,'parent_wiring_qualified':False}))
if __name__=='__main__':main()
"""
 p=R/'scripts/assemble_gf180_class_current_service_v13.py';assert not p.exists();p.write_text(header+pre+routing+views+pack+tail);print(str(p))
if __name__=='__main__':main()
