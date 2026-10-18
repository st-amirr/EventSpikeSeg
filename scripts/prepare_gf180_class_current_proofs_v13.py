"""Version exact parent proof and top census for the added class-current service."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def main():
 p=R/'scripts/prove_gf180_adaptation_service_v12.py';s=p.read_text().replace('full25_adaptation_service_v12','full25_class_current_service_v13').replace('eventspikeseg140k_adaptation_service_v12.gds','eventspikeseg140k_class_current_service_v13.gds')
 s=s.replace("m['adaptation_service_wrappers'][args.actor_index]","[m['class_current_service_wrapper']][args.actor_index]")
 s=s.replace('full25_membrane_service_v10/eventspikeseg140k_membrane_service_v10.gds','full25_adaptation_service_v12/eventspikeseg140k_adaptation_service_v12.gds').replace('gf180_adaptation_shared_state_io_v6','gf180_class_current_shared_io_v1')
 a=s.index(" res=next(p for p in w['modules']");b=s.index(' def compare(n):',a);s=s[:a]+s[b:]
 s=s.replace("p['instance'].endswith('_FOREST')","p['instance']=='FOREST'")
 a=s.index("'scope':'Exactparentmetal/contact");b=s.index(",'sha256':",a);s=s[:a]+"'scope':'Exact class-current parent metal/contact graph: existing native six-class readout, native120MOS8R48MIMIO and forest terminal field, all child geometry byte verified. Added wire/via contacts, every endpoint/root port, short/open/floating and opaque-forest intrusion checked independently. No parentRC/loading/fullpopulation timing or modelaccuracy acceptance.'"+s[b:]
 o=R/'scripts/prove_gf180_class_current_service_v13.py';assert not o.exists();o.write_text(s)
 s=(R/'scripts/audit_gf180_adaptation_service_inventory_v12.py').read_text().replace('full25_adaptation_service_v12','full25_class_current_service_v13').replace('eventspikeseg140k_adaptation_service_v12.gds','eventspikeseg140k_class_current_service_v13.gds')
 a=s.index(" for w in m['adaptation_service_wrappers']:");b=s.index(' @functools.lru_cache(None)',a)
 contract=""" w=m['class_current_service_wrapper'];forest=next(p for p in w['modules'] if p['instance']=='FOREST');plane=next(p for p in f['planes'] if p['state_kind']=='class_current');assert forest['cell']==plane['root_cell'];fm={p:'FOREST__'+p for p in forest['ports']};fm.update(VCM='STORAGE_REFERENCE',VDD='VDD',VSS='VSS',RECOV='RECOV');fm.update({f'DATA{k}':f'DATA{k}' for k in range(8)});assert forest['mapping']==fm
 rd=next(p for p in w['modules'] if p['instance']=='READOUT');rm={p:p for p in rd['ports']};rm['VRESET']='COMPUTE_REFERENCE';assert rd['mapping']==rm;io=next(p for p in w['modules'] if p['instance']=='IO');assert io['mapping']=={p:p for p in io['ports']}
 # Preserve every V12 compute/adaptation cell and auxiliary content except moving
 # the one existing readout reference to the new class wrapper.
 v12=R/'artifacts/analog_asic/assembly/full25_adaptation_service_v12';v12m=json.loads((v12/'physical_assembly.json').read_text());_,v12cells=cells_read((v12/'eventspikeseg140k_adaptation_service_v12.gds').read_bytes())
 for p in v12m['top_placements']:
  if p['kind'] not in ('parameter_protocol','class_current'):assert cells[p['cell']]==v12cells[p['cell']]
 aux=list(elements(v12cells['ESS_PARAMETER_PROTOCOL_RETAINED_V10']));ret=[e for e in aux if not any(t==18 and v.rstrip(b'\\0').decode()==rd['cell'] for t,d,v,b in e)];assert len(aux)-len(ret)==1;assert list(elements(cells['ESS_PARAMETER_PROTOCOL_RETAINED_V13']))==ret
"""
 s=s[:a]+contract+s[b:]
 a=s.index(' proofs=[');b=s.index(';bb=bbox(',a)
 s=s[:a]+" proof=json.loads((D/'actor_00_boundary_wiring_v2.json').read_text());wiring=proof['incremental_boundary_wiring_accepted'] and proof['sha256'][g.relative_to(R).as_posix()]==sha(g) and proof['sha256'][mf.relative_to(R).as_posix()]==sha(mf)"+s[b:]
 a=s.index(" o.pop('all25_boundary");b=s.index(" o['sha256'][pmf",a)
 s=s[:a]+""" o.pop('all25_boundary_wiring_proofs_accepted');o.update(class_current_boundary_wiring_proof_accepted=wiring,class_current_forest_readout_port_contract_verified=True,active_class_current_states_with_verified_boundary_compute_link=1689600 if wiring else 0,active_adaptation_states_with_inherited_V12_verified_boundary_compute_link=21964800,active_membrane_states_with_inherited_V10_verified_boundary_compute_link=30976000,parent_RC_or_loaded_nominal_qualified=False)
 @functools.lru_cache(None)
 def readouts(n):return int(n==rd['cell']) if n==rd['cell'] else sum(readouts(ch)*nx*ny for ch,x,y,nx,ny,dx,dy in parse(n)[0])
 assert readouts(m['top_cell'])==1;o['existing_native_readout_occurrences']=1
 o['scope']='Actual binary56forest roots/25actors/54130nativepages retained, existing six-class readout appears exactlyonce. New class plane/IO/readout port contracts independently checked; every V12 actor/adaptation top child unchanged, aux preserved except moving readout reference. New class boundary graph qualified, native parentRC/loading/globalfunctions/modelaccuracy/5ms unqualified. Spacious atlas is notcompactdie.'
"""+s[b:]
 o=R/'scripts/audit_gf180_class_current_inventory_v13.py';assert not o.exists();o.write_text(s)
if __name__=='__main__':main()
