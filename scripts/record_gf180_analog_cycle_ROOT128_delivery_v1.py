"""Publish completed imperfect analog cycle, native128 nominal and new ROOT connections."""
from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
OLD=B/'assembly/full25_external_bank_service_v5';D=B/'assembly/full25_shared_ROOT128_v6'
P=B/'assembly/external_service_control_partition_v1'

def main():
    sr=B/'results/gf180_external_service_control_partition_cycle_v1.json';s=json.loads(sr.read_text())
    assert s['completed'] and s['complete_analog_state_cycle_observed']
    ar=B/'results/gf180_adaptation_sum128_threshold_v2_native_primitives_nominal_src7b90b512583f.json';a=json.loads(ar.read_text())
    assert a['module_simulation_completed'] and not a['routing_capacitance_included']
    dr=D/'verification/actor_12_external_service_DRC_only_v1/qualification_attempt.json';q=json.loads(dr.read_text());assert q['full_parent_drc_count']==0
    mf=D/'physical_assembly.json';m=json.loads(mf.read_text());assert len(m['native128_ROOT_joins'])==9
    identity=D/'independent_resident_service_composition_v1.json';assert json.loads(identity.read_text())['all_resident_bank_identities_preserved_without_duplication']
    cov=json.loads((OLD/'module_simulation_coverage_v1.json').read_text())
    cov['current_assembly']=mf.relative_to(R).as_posix()
    cov['latest_composed_analog_service_cycle']=s
    cov['latest_full128_SUM_primitive_nominal']=a
    cov['latest_physical_ROOT128_join']={'actors':m['native128_ROOT_joins'],'representative_DRC':q,'composition_proof':m['shared_ROOT128_composition_proof'],'native_full_parent_connectivity_accepted':False,'nominal_128_RMS_accepted':False}
    for row in cov['requirements']:
        if row['requirement']=='Adaptation SUM128 and clipped threshold':
            row.update(status='completed_native_primitive_nominal_routingC_missing',evidence_and_gap='Full128 three-case40us nominal complete:sum10.464mV,clippedthreshold9.671mV errors. Native3099MOS512R1536MIM and source/GDS exact graph; routingC excluded. CompleteflatC qualification and resident producer binding remain open.')
        elif row['requirement']=='RMS128':
            row.update(status='physical_ROOT_join_and_exact_composition_nominal_missing',evidence_and_gap='Existing two64 current-summingROOT nodes physically joined in all9actual128 actors. Exact896primitive composition equals native128 reducer;new representativeDRC0. Full native parent wiring/loaded nominal still missing.')
        elif row['requirement']=='Learned beta/state update':
            row.update(status='completed_imperfect_composed_analog_cycle',evidence_and_gap='180us native analog physical partition completes with1832primitives/14365verified routingC. Beta step-26.900mV,positive event+143.160mV; categorical phases externally driven. Precision not accepted.')
        elif row['requirement']=='Decision and subtractive reset':
            row.update(status='completed_imperfect_composed_analog_cycle',evidence_and_gap='Spike3.294V and subtractive reset-6.467mV observed in completed180us externalstatecycle;writeback error-20.341mV. Native controller full-parent transient remains incomplete.')
    for row in cov['modules']:
        if row.get('cell')=='gf180_adaptation_sum128_threshold_v2':
            row.update(completed_nominal_report_found=True,routing_capacitance_included_in_latest_nominal=False)
            if ar.relative_to(R).as_posix() not in row.setdefault('reports',[]):row['reports'].append(ar.relative_to(R).as_posix())
    cp=D/'module_simulation_coverage_v1.json';assert not cp.exists();cp.write_text(json.dumps(cov,indent=2)+'\n')
    report=D/'delivery_report_v1.html';assert not report.exists();text=(OLD/'delivery_report_v1.html').read_text()
    text=text.replace('Stage: module integration and full-layout connections.','Stage: selected analog cycle complete; full-layout connections in progress.')
    text=text.replace('SUM128 final nominal, full RMS128 reduction and connected adaptation/readout functions remain.','SUM128 native primitive nominal now complete; routingC qualification remains. RMS128 ROOT joins now physically present; loaded nominal and connected adaptation/readout functions remain.')
    text=text.replace('Demonstrated in V4','Analog cycle demonstrated').replace('120us native roundtrip completed;34.63mV state change retained. V5 neuron-cycle status below.','180us composed analog update completed: restore,beta,event,spike,reset,writeback; measured imperfections retained.')
    latest='<h2>Latest connected case</h2><p><b>180µs analog state cycle completed in159.67s.</b> Native analog partition:1,832 primitives and14,365 verified routingC branches. Restore error8.38µV;beta step−26.90mV;positive weighted event+143.16mV;spike3.294V;subtractive reset−6.47mV;writeback error−20.34mV. Categorical phases are external native-inverter fixtures;the full V5/V6 layouts retain native controllers. Native full-controller cases remain partial. Pulse termination follows ARM release in this fixture;programmed pulse-width accuracy is unresolved.</p><p><a href="../external_service_control_partition_v1/analog_state_cycle.svg">Export SVG figure</a></p><img style="width:100%;height:auto" src="../external_service_control_partition_v1/analog_state_cycle.png" alt="Measured shared-storage analog state cycle">'
    text,n=re.subn(r'<h2>Latest connected case</h2>.*?(?=<h2>Current physical revision</h2>)',lambda _:latest,text,count=1,flags=re.S);assert n==1
    text=text.replace('V5 moves service escape wires into a clear left gutter after native V4 larger-actor extraction exposed signal/supply shorts. V5 larger-parent extraction remains incomplete; partial files are not connectivity passes.','V6 retains the V5 service-routing repair and physically joins ROOT nodes of the two existing64-channel RMS halves in all nine128-channel actors. Complete primitive graph equivalence matches the native128 reducer;new representative layout DRC0. New larger-parent exact extraction/loaded RMS nominal remain incomplete. All54,630,400analog state identities are independently preserved.')
    text=text.replace('eventspikeseg140k_external_bank_service_v5.gds','eventspikeseg140k_shared_ROOT128_v6.gds')
    text=text.replace('<h2>Area and timing scope</h2>','<h2>Full128 adaptation sum/threshold</h2><p>Three-case40µs native primitive nominal completes:maximumsum error10.46mV;clippedthreshold error9.67mV;local settling7.50µs to recorded final. Source/GDS topology is verified;route capacitance excluded. This is a completed module characterization with a documented RC limitation.</p><h2>Area and timing scope</h2>')
    text=text.replace('href="independent_actor_geometry_equivalence_v2.json"','href="../full25_external_bank_service_v5/independent_actor_geometry_equivalence_v2.json"')
    report.write_text(text,encoding='utf8')
    note=('\n\n## Completed analog cycle and128-channel integration - 2026-10-12\n\n'
          '180us analog physical partition completes159.67s wall:1832native primitives,14365complete verified routingC,DRC0/exact independentgraph. '
          'Only two categorical controllers removed from this characterization;fullASIC V6 retains them. Restore8.38uV,beta step-26.900mV,positiveevent+143.160mV,spike3.294V,reset-6.467mV,writeback error-20.341mV. '
          'Programmed pulse-width termination andprecision remain unaccepted; no ideal DATA/state orUIC/IC. '
          'Full128 SUM/threshold nativeprimitive40us threecase nominal completes:sum10.464mV,threshold9.671mV errors,localsettling7.503us. Source/GDS exact3099MOS512R1536MIM;routeC excluded andcompleteRC remains open. '
          'One240s extension justified by measured120s reaching22.1866us/40us,216.35s projection;no circuit/tolerance tuning. '
          'V6 actual9actor ROOT joins reuse existing two64halves;exact896primitive sharedROOT composition equals native128 reducer andnewrepresentativeDRC0. '
          'All54,630,400active identities preserved;globalbankservice/graph/parameter/producerbindings,loadedRMS128 andfullASIC remain incomplete. '
          'Report:'+report.relative_to(R).as_posix()+'.\n')
    for name in ['RESULTS.md','PROGRESS.md']:
        p=R/'docs'/name;p.write_bytes(p.read_bytes()+note.encode())
    p=R/'docs/DECISIONS.md';p.write_bytes(p.read_bytes()+('\n\n## Complete integration before precision refinement - 2026-10-12\n\nUse physical characterization partitions at categorical controller interfaces when fullnativecontroller transient stalls;verify the actual remaining device graph andfresh completeC before analogsimulation. Keep physicalcontrollers in fullASIC andretain separate failed fullparent results. This changes modeling scope,not analog numerical storage or network semantics. For missing full128 SUM nominal,qualified complete native primitive topology/MIM/resistors provides an initial simulation with routingC explicitly excluded; do not relabel it completeRC. Reuse existing current-summing ROOT networks for128channels:128kernels and128receivers shareROOT;no buffered RMS-voltage averaging or new sqrt block. Exact graph validation permits a symmetry-aware deterministic mapping only after everyprimitive,pin,node andedge is checked;failed unique-net method retained. Continue physicalbank/globalbindings instead of precision sweeps.\n').encode())
    p=R/'docs/ARCHITECTURE.md';p.write_bytes(p.read_bytes()+('\n\n## Shared native128-channel energy ROOT - 2026-10-12\n\nROOT of energy_mean_root64 is a native current-summing/root-feedback node with one receiver per channel. Joining two ROOT nodes while retaining all128 quadratic kernels and128receivers is exactly the existing energy_mean_root128 primitive topology. The complete896primitive graph proof is inverification/shared_ROOT128_composition_v2. V6 physically adds these joins to the9actual128channel actors using a reservedleftgutter M4spine and M5pad landings,without addedactive devices orchanged child transforms/stateidentities. RepresentativeDRC0;fullnativeparentconnectivity andloadednominal notyetqualified. VBASE/penalty/reference programming contracts andfullproducer/consumer bindings stillrequired.\n').encode())
    p=R/'docs/ACTIVE_TASKS.md';b=p.read_bytes()
    updates={
        'Shared access':'Composed180us analog physical cycle completes159.67s:restore,beta,event,spike,reset,writeback. Native1832primitives/14365verifiedC;external categorical phases. Writeback error20.34mV retained;fullnativecontroller cycle remains partial.',
        'RMS/adaptation':'Full64 nativeRC nominal complete. Full128 SUM/threshold nativeprimitive nominal now complete:sum10.46mV,threshold9.67mV;routeC excluded. Native128ROOT joins physically present in9actors,DRC0/exactcomposition;loaded nominal/producer bindings open.',
        'Full model':'V6 GDS preserves54,630,400states andadds9native128ROOT joins. Firstactor V5 geometry unchanged;DRC0/exact2362 parent andDRC0/exact1832 analog partition. 4800sites serviced;remaining866005plane banks/globalgraph/parameters unbound.'}
    for key,v in updates.items():
        b,n=re.subn(('\\| '+re.escape(key)+' \\|[^\\r\\n]+').encode(),('| '+key+' | '+v+' |').encode(),b,count=1);assert n==1,key
    b=b.replace(b'artifacts/analog_asic/assembly/full25_external_bank_service_v5/delivery_report_v1.html',report.relative_to(R).as_posix().encode(),1)
    b=b.replace(b'Full128 source/GDS layout and exact primitive connectivity are complete; the360s fresh flat extraction is truncated and rejected.',b'Full128 native primitive nominal is complete with10.46mV sum/9.67mV threshold errors;routeC excluded. The360s fresh flat extraction remains truncated and rejected.')
    p.write_bytes(b+note.encode())
    p=R/'docs/project_spec.yaml';b=p.read_bytes()
    changes={'current_stage':'selected_analog_statecycle_and_full128_primitive_nominal_complete_V6_ROOTjoins_globalbindings_open','full25_physical_candidate':mf.relative_to(R).as_posix(),'article_delivery_report':report.relative_to(R).as_posix(),'module_simulation_coverage':cp.relative_to(R).as_posix(),'evidence':sr.relative_to(R).as_posix()}
    for k,v in changes.items():
        b,n=re.subn(('  '+k+': [^\\r\\n]+').encode(),('  '+k+': '+v).encode(),b,count=1);assert n==1,k
    b,n=re.subn(rb'(  latest_experiment:\r?\n    report: )[^\r\n]+',lambda x:x[1]+sr.relative_to(R).as_posix().encode(),b,count=1);assert n==1
    b,n=re.subn(rb'(  latest_experiment:\r?\n    report: [^\r\n]+\r?\n    status: )[^\r\n]+',rb'\1composed_analog_cycle_complete180us_native128_SUM_nominal_complete_ROOT128_physically_joined',b,count=1);assert n==1
    p.write_bytes(b)
    print(json.dumps({'report':str(report),'analog_cycle_complete':True,'SUM128_native_primitive_nominal_complete':True,'full_chip_complete':False},indent=2))

if __name__=='__main__':main()
