"""Bind full actor child provenance to actual checked boundary metal and report coverage."""
from pathlib import Path
import hashlib,json,re
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full_capacity_storage_gds_v2 import records,string
from gf180_compact_lvs_v2 import compact
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';D=B/'assembly/full25_shared_page1024_v8'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    out=D/'actor_compositional_wiring_qualification_v1.json';assert not out.exists();mf=D/'physical_assembly.json';m=read(mf);g=D/'eventspikeseg140k_shared_page1024_v7.gds';_,cells=cells_read(g.read_bytes());groups=read(D/'independent_actor_geometry_groups_v1.json')['geometry_groups'];sources=[];counts={};inputs=[Path(__file__),mf,g]
    for c in sorted({p['cell'] for a in m['actor_regions'] for p in a['modules']}):
        if c=='shared_reader_page1024_v1':
            p=B/'assembly'/c;ng=p/'shared_reader_page1024.gds';qp=p/'verification/native_parent_v1/parent_exact_connectivity_attempt.json';q=read(qp);assert q['independent_connectivity_accepted'];counts[c]=q['native_primitives'];inputs += [ng,qp]
        else:
            p=B/'layout'/c;ng=p/(c+'.gds');qp=p/'qualification.json';q=read(qp);assert q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and sha(ng)==q['sha256'][ng.name];sp=p/(c+'.spice');_,cq=compact(sp.read_text(),c);counts[c]=cq['primitive_devices'];inputs += [ng,qp,sp]
        _,original=cells_read(ng.read_bytes());tag=sha(ng)[:8];names={n:'N'+tag+'_'+hashlib.sha256(n.encode()).hexdigest()[:16] for n in original}
        for name,blob in original.items():
            expected=b''.join(string(t,names[v.rstrip(b'\0').decode()]) if t in [6,18] else b for t,dt,v,b in records(blob));assert cells[names[name]]==expected,(c,name)
        sources.append({'cell':c,'native_primitives':counts[c],'all_source_GDS_cells_byte_verified':True,'native_child_connectivity_accepted':True,'source_GDS_sha256':sha(ng)})
    reports=[]
    for gg in groups:
        ix=gg['representative_index'];pp=D/f'actor_{ix:02d}_complete_boundary_metal_proof_v{5 if ix in [0,12] else 4}.json';proof=read(pp);assert proof['incremental_metal_connectivity_accepted'];inputs.append(pp)
        signatures=[]
        for i in gg['actor_indices']:
            a=m['actor_regions'][i];body=b''.join(b for e in elements(cells[a['gds_cell']]) for t,dt,v,b in e);physical=sha_bytes(body)
            bindings=sorted((s,n['net']) for n in m['local_pin_nets'] if n['actor']==a['actor'] for s in n['endpoint_pins']);semantic=sha_bytes(json.dumps(bindings).encode());signatures.append((physical,semantic))
        assert len(set(signatures))==1
        reports.append({'representative_actor_index':ix,'covered_actor_indices':gg['actor_indices'],'complete_root_geometry_and_TEXT_equal':True,'source_terminal_binding_equal':True,'metal_boundary_proof':pp.relative_to(R).as_posix(),'native_primitives_per_actor':sum(counts[p['cell']] for p in m['actor_regions'][ix]['modules'])})
    control=B/'assembly/full25_shared_page1024_v7/actor_00_complete_boundary_metal_proof_v4.json';bad=read(control);assert not bad['incremental_metal_connectivity_accepted'] and len(bad['unintended_shorts'])==1;inputs.append(control)
    assert sum(len(row['covered_actor_indices']) for row in reports)==25
    o={'all25_actor_native_child_and_boundary_composition_accepted':True,'full_native_flat_parent_LVS_completed':False,'full_native_parent_RC_qualified':False,'full_chip_complete':False,'known_bad_native_short_control_rejected':True,'native_children':sources,'actor_groups':reports,'scope':'Every nativechildsourceGDS cell byteverified afternamespace mapping,withnativeLVS/exactchildproof. Complete originalandnewchildterminal boundaries checkedagainstactualmetal1..5,CAPM,via1..4 geometry;newpainttouchesonlydeclaredboundarycomponents. Fourexactrootgeometry+TEXT+terminalbinding groups cover25actors. This establishes composedsource circuit connectivity atchildboundaries,not a completed flatnative extraction orRC/transient/signoff. DRC stemerror/RMS128incomplete remainseparate;globalservice/graph/parameters remainunbound.','sha256':{p.relative_to(R).as_posix():sha(p) for p in inputs}}
    out.write_text(json.dumps(o,indent=2)+'\n')
    cov=read(D/'module_simulation_coverage_v1.json');cov['actor_compositional_wiring_qualification']=out.relative_to(R).as_posix();cov['latest_shared_page_integration']['all25_actor_boundary_composition_accepted']=True
    for row in cov['requirements']:
        if row['requirement']=='Analog bank access':row.update(status='shared1024page_parent_boundary_composition_qualified_global_binding_missing',evidence_and_gap='25shared1024pages/30400routedsites. AllnativechildGDS bytes/proofs+everyterminalmetal connectivity verified;all25actorgeometry/TEXT/bindings equaltofourtestedrepresentatives. ParentRC/loadedcycle andremaining865605plane globalservice unbound.')
        elif row['requirement']=='RMS128':row.update(status='actual128ROOT_parent_metal_and_native_composition_qualified_loaded_nominal_missing',evidence_and_gap='Allnine128actor ROOTjoins pass completechildboundarymetal check andprior896primitive native128composition. Loaded128RMS nominal/producerbindings remain missing.')
    cp=D/'module_simulation_coverage_v2.json';cp.write_text(json.dumps(cov,indent=2)+'\n')
    report=D/'delivery_report_v2.html';text=(D/'delivery_report_v1.html').read_text();text=text.replace('Newparent exactwiring proof incomplete.','All25actor nativechild/boundary composition verified. Flatnativeextraction andparentRC remain incomplete.').replace('module_simulation_coverage_v1.json','module_simulation_coverage_v2.json');text=text.replace('<h2>Stage: full physical integration</h2>','<h2>Stage: shared-page connections verified; global service in progress</h2><p><a href="actor_compositional_wiring_qualification_v1.json">Compositional wiring evidence</a>:all25actors covered;every nativechildGDS byte checked;all terminalmetal connections checked. Theverifier rejects the knownbadV7short. Largestcase2,724,428rectangles/2,364anchors completed31.41s under2GB. Nativeflat/hierarchicaltimeouts are retained;this is a separate geometric/compositional proof.</p>');report.write_text(text,encoding='utf8')
    note=('\n\n## All25actor sharedpage boundary composition verified - 2026-10-12\n\n'
          'Independent exactmetal/MIMcontact graph checksalloriginal/newmoduleterminal anchors. Fourexactgeometry+TEXT+sourcebinding groups cover25actors;every qualifiednativechildGDS cell byteverified afternamespace mapping. No shorts,opens,floatingadditions,unknownchildcontacts orrootporterrors. KnownbadV7control correctlydetects sixshortednets. GF180VIA4 withinCAPM contactsMIMtop75,notM4;earliernaive verifierinvalidated/retained. Streaminghierarchy avoids2GB exit137 fromexpandedcache;largestcase2724428rectangles/2364anchors completes31.41s. All25actor circuitboundary composition nowqualified,includingnineRMS128ROOTjoins. ThisisnotcompletedflatnativeLVS/RC/loadednominal. DRC15actorszero,stemoneerror,nineRMS128DRCincomplete remain. Nextglobalbankservice/graph/parameterbinding andmissingloadedmodulecoverage. Report:artifacts/analog_asic/assembly/full25_shared_page1024_v8/delivery_report_v2.html.\n')
    for name in ['RESULTS.md','PROGRESS.md']:
        p=R/'docs'/name;p.write_bytes(p.read_bytes()+note.encode())
    p=R/'docs/ACTIVE_TASKS.md';b=p.read_bytes();b=re.sub(rb'\| Full model \|[^\r\n]+',b'| Full model | V8preserves54630400states;25shared1024pages connect30400sites. All25actor nativechild/boundary composition verified;parentRC/loadedcycle open. DRC15zero,stem1error,9RMS128incomplete. Remaining865605plane banks/globalgraph/parameters unbound. |',b,count=1);b=re.sub(rb'\| Live jobs \|[^\r\n]+',b'| Live jobs | No process active. Sharedpage-to-compute boundary wiring verified across25actors;globalbankservice/graph/parameterbinding andmissingloadedmodulecoverage next. Fullnativeextracttimeouts retained;no repeatplanned. |',b,count=1);b=b.replace(b'artifacts/analog_asic/assembly/full25_shared_page1024_v8/delivery_report_v1.html',report.relative_to(R).as_posix().encode(),1);p.write_bytes(b+note.encode())
    p=R/'docs/DECISIONS.md';p.write_bytes(p.read_bytes()+b'\n\n## Nativechild andactualboundarymetal composition - 2026-10-12\n\nUse frozen nativechild LVS/exactproofs plusindependent actualmetal/via boundary connectivity forlargeparent integration whenflat/hierarchical extractionstalls. VerifyallchildGDSbytes,everyterminal,allnewpaintcontacts,nounintendedaliases/opens,andgeometry/TEXT/sourcebinding equivalence beforeextendingrepresentativecoverage. GF180MIM41cuts requireCAPM/CAPDEFclassification;rejectpartialmaskcases. Knownbadnative-extractionshort servespositivecontrol. KeepnativeflatLVS/RC flagsfalse untilthose specificrunsfinish. This qualifiedcomposition replaces repeatedlargeextractioncampaigns forarticle connectivitywork.\n')
    p=R/'docs/project_spec.yaml';b=p.read_bytes()
    for key,value in {'current_stage':'V8all25actor_child_boundary_wiring_qualified_global_service_and_loaded_modules_open','article_delivery_report':report.relative_to(R).as_posix(),'module_simulation_coverage':cp.relative_to(R).as_posix()}.items():b,n=re.subn(('  '+key+': ').encode()+rb'[^\r\n]+',('  '+key+': '+value).encode(),b,count=1);assert n==1
    b=re.sub(rb'  live_sessions: [^\r\n]+',b'  live_sessions: []',b,count=1);p.write_bytes(b)
    print(json.dumps({'all25_actor_boundary_composition_qualified':True,'primitive_counts_by_group':[r['native_primitives_per_actor'] for r in reports],'report':str(report),'full_chip_complete':False},indent=2))
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
if __name__=='__main__':main()
