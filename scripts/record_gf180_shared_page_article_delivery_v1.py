"""Publish qualified shared-page layout and scoped completed frontend simulation."""
from pathlib import Path
import hashlib, html, json, re
import numpy as np
R=Path(__file__).resolve().parents[1]; B=R/'artifacts/analog_asic'
D=B/'assembly/shared_reader_page1024_v1'; F=B/'assembly/page1024_read_frontend_partition_v1'
V=B/'assembly/full25_shared_ROOT128_v6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    out=D/'article_delivery_v1.json';assert not out.exists()
    full=B/'results/gf180_shared_reader_page1024_v1_native_two_row_A_B_A.json'
    sim=B/'results/gf180_page1024_read_frontend_partition_v1_native_A_B_A.json'
    s=read(sim);w=read(full)
    assert s['module_simulation_completed'] and s['page_selected_reader_A_B_A_observed']
    assert not w['module_simulation_completed']
    paths=[full,sim]
    for folder,n in [(D,7847),(F,359)]:
        q=folder/'verification/native_parent_v1/qualification_attempt.json'
        e=folder/'verification/native_parent_v1/parent_exact_connectivity_attempt.json'
        c=folder/'verification/native_fullcap_v1/qualification.json'
        assert read(q)['full_parent_drc_count']==0
        assert read(e)['independent_connectivity_accepted'] and read(e)['native_primitives']==n
        assert read(c)['full_cap_extraction_completed'] and read(c)['all_native_substrate_caps_verified']
        paths += [q,e,c]
    review={'whole_page_transient_completed':False,'observed_time_us':w['last_time_s']*1e6,
            'requested_time_us':34,'wall_s':w['elapsed_wall_s'],
            'diagnosis':'Progress stalls near first address transition at4us. Exact numerical bottleneck not established; no evidence of a wiring short from this timeout. First selected native row write precedes transition. Fullpage wiring proof and routingC extraction remain valid.',
            'runtime_extension_authorized':False,
            'method_change':'Characterize new page selection/readout with physically qualified359primitive partition and frozen measured native bank RAW outputs. Preserve all7847primitives in complete layout. Bank source impedance and coupled wholepage transient are outside partition evidence.',
            'frontend_nominal_completed':True,'frontend_max_recovery_error_v':s['max_recovery_error_v'],
            'next_action':'Bind shared page access into full25actor layout; reuse completed imperfect analog cycle and module simulations. Do not repeat fullpage transient or accuracy sweeps before integration.'}
    (D/'transient_method_review_v1.json').write_text(json.dumps(review,indent=2)+'\n')
    z=np.load(sim.with_suffix('.npz'));a=z['waveforms'];names=list(z['variables']);t=a[:,0]*1e6
    # Standalone vector figure; downsample only the exported drawing, retain raw trace.
    ids=np.unique(np.r_[np.arange(0,len(t),max(1,len(t)//1800)),len(t)-1]);x=lambda u:70+u/40*810;y=lambda v:350-(v-.8)/.8*260
    vals=a[:,names.index('v(recov)')]
    points=' '.join(f'{x(t[i]):.2f},{y(vals[i]):.2f}' for i in ids)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="450" viewBox="0 0 960 450"><rect width="960" height="450" fill="white"/><g font-family="Arial" fill="#17212b"><text x="70" y="30" font-size="21">Shared page reader: A → B → A</text><text x="70" y="55" font-size="13">Native frontend with routing capacitance; measured bank-output fixtures</text>']
    for v in [.8,1.,1.2,1.4,1.6]:svg.append(f'<path d="M70 {y(v)}H880" stroke="#ddd"/><text x="25" y="{y(v)+5}" font-size="13">{v:.1f}</text>')
    for u in [0,10,20,30,40]:svg.append(f'<text x="{x(u)-8}" y="375" font-size="13">{u}</text>')
    svg += [f'<polyline points="{points}" fill="none" stroke="#176ba0" stroke-width="2"/>','<text x="410" y="405" font-size="15">Time (µs)</text><text x="70" y="435" font-size="13">Recovery error ≤22.03 µV at sampled settled epochs; full1024-state transient remains incomplete.</text></g></svg>']
    (D/'shared_reader_A_B_A.svg').write_text(''.join(svg),encoding='utf8')
    o={'full_chip_complete':False,'layout_primitives':7847,'analog_states':1024,'shared_feedback_readers':1,
       'source_GDS_DRC_errors':0,'complete_exact_primitive_wiring':True,'fullpage_native_routing_C_branches':71802,
       'fullpage_transient_completed':False,'read_frontend_partition_transient_completed':True,
       'frontend_native_primitives':359,'frontend_native_routing_C_branches':9498,
       'frontend_max_recovery_error_v':s['max_recovery_error_v'],
       'layout_area_scope':'Deliberately spaced characterization layout; not a dense die-area estimate.',
       'scope':'Article evidence accepts completed imperfect results. Exact connectivity applies to fullpage. Transient evidence applies to separate physical frontend partition with frozen measured RAWfixtures; it does not establish fullpage initialization, retention, source impedance, global service or5ms.',
       'evidence':{p.relative_to(R).as_posix():sha(p) for p in paths}}
    out.write_text(json.dumps(o,indent=2)+'\n')
    cp=V/'module_simulation_coverage_v2.json';assert not cp.exists();cov=read(V/'module_simulation_coverage_v1.json')
    cov['shared1024_page_evidence']=o;cov['shared1024_page_delivery']=out.relative_to(R).as_posix()
    cov['completion_policy']='Retain measured imperfections and scoped simulation boundaries; prioritize missing physical connections. Accuracy and5ms are reported limitations, not reasons to repeat module tuning before article delivery.'
    cov['next_physical_task']='Connect shared1024page read/write service to25actor compute while preserving resident identities; then global bankservice and graph/operator/parameter endpoints.'
    cp.write_text(json.dumps(cov,indent=2)+'\n')
    report=D/'article_report_v1.html'
    report.write_text('''<!doctype html><meta charset="utf-8"><title>Shared analog state access</title><style>body{font:17px Arial;max-width:1000px;margin:40px auto;line-height:1.5}td,th{padding:10px;border-bottom:1px solid #ccc;text-align:left}img{width:100%}</style><h1>Shared analog state access</h1><p>Stage: module integration. Full-chip connectivity remains incomplete.</p><table><tr><th>Deliverable</th><th>Result</th></tr><tr><td>1,024-state layout, one shared reader</td><td>7,847 native primitives; DRC0; exact wiring proof;71,802 routing capacitance branches</td></tr><tr><td>Read selection A → B → A</td><td>Completed40µs native frontend simulation in36.41s; maximum sampled recovery error22.03µV</td></tr><tr><td>Whole-page transient</td><td>Incomplete:120s bound reached3.996µs of34µs. Failure retained; no repeated runtime campaign.</td></tr></table><img src="shared_reader_A_B_A.svg" alt="Shared page reader recovery waveform"><p>The frontend uses frozen outputs from a completed native bank simulation. It tests the new page selection and shared reader, but does not prove the coupled1,024-state transient. The complete layout preserves all native storage cells. Geometry is a spacious characterization fixture, not a compact full-chip area estimate.</p><h2>Continue toward article delivery</h2><p>Connect shared access to the full25actor layout, then finish global bankservice, graph/operator and parameter interfaces. Reuse completed module results, including20mV writeback error. No precision sweep is required before these missing connections.</p><p><a href="shared_reader_page1024.gds">Physical GDS</a> · <a href="article_delivery_v1.json">Evidence index</a> · <a href="transient_method_review_v1.json">Method review</a> · <a href="../full25_shared_ROOT128_v6/delivery_report_v1.html">Current full assembly</a></p>''',encoding='utf8')
    # Preserve catalog100; add both actual characterization assemblies in revision101.
    cat=read(B/'assembly/article_module_catalog_v100.json');cat['previous_catalog']='artifacts/analog_asic/assembly/article_module_catalog_v100.json';cat['revision']=101
    for folder,cell,mos,mim,sr in [(D,'shared_reader_page1024_v1',6818,1029,full),(F,'page1024_read_frontend_partition_v1',354,5,sim)]:
        views=[folder/'physical_partition.json',folder/'verification/native_parent_v1/parent_exact_connectivity_attempt.json',folder/'verification/native_fullcap_v1/qualification.json',sr]
        cat['characterization_assemblies'].append({'cell':cell,'role':'Shared1024state access' if folder==D else 'Shared page read frontend characterization partition','mos_count':mos,'native_mim_count':mim,'native_resistor_count':0,'module_layout_and_nominal_simulation_artifacts_complete':read(sr)['module_simulation_completed'],'complete_neuron_functionally_accepted':False,'views':{p.name:p.relative_to(R).as_posix() for p in views},'limitations':read(sr)['scope'],'sha256':{p.relative_to(R).as_posix():sha(p) for p in views}})
    dest=B/'assembly/article_module_catalog_v101.json';assert not dest.exists();dest.write_text(json.dumps(cat,indent=2)+'\n')
    note=('\n\n## Shared1024state page and completed reader partition - 2026-10-12\n\n'
          'Actual1024state page6818MOS1029MIM:sourceGDS DRC0,exact7847primitive graph,71802complete verifiedroutingC. Onefeedbackreader serves8bankpairs. Whole34us transient timedout120.59s at3.996us nearfirstaddressedge; retained,not a pass. '
          'New physical frontend partition354MOS5MIM preservesparentroutes/decoder/readTG/mux/reader:DRC0,exact359graph,9498verifiedC.40us A-B-A sequence completes36.41s;sampled recoveryerror22.03uVmax,Areturnchange2.514nV. Frozenmeasured nativebankRAW100ohmfixtures;notwholepage sourceimpedance/startup/retention/serviceproof. '
          'Continuefullphysicalbindings,retainimperfectresults,avoidprecision/runtimecampaigns. FullV6assembly unchanged;allmodelglobalservice stillincomplete. Catalog101:20modules86characterizationassemblies. Report:artifacts/analog_asic/assembly/shared_reader_page1024_v1/article_report_v1.html.\n')
    for name in ['RESULTS.md','PROGRESS.md']:
        p=R/'docs'/name;p.write_bytes(p.read_bytes()+note.encode())
    p=R/'docs/ACTIVE_TASKS.md';b=p.read_bytes().replace(b'84 characterization assemblies; catalog revision100',b'86 characterization assemblies; catalog revision101').replace(b'article_module_catalog_v100.json',b'article_module_catalog_v101.json')
    b,n=re.subn(rb'\| Live jobs \|[^\r\n]+',b'| Live jobs | No simulator active. Shared1024page physical qualification complete;40us frontend A-B-A completed36.41s,error22.03uV. Wholepage120s timeout retained. Next:full25actor sharedpage/access integration,then globalbank/graph/parameterbindings. |',b,count=1);assert n==1
    p.write_bytes(b+note.encode())
    p=R/'docs/DECISIONS.md';p.write_bytes(p.read_bytes()+b'\n\n## Article results before precision tuning - 2026-10-12\n\nUser confirms imperfect results are acceptable; completing layout and per-module simulations is the priority. Preserve measured errors and failed runs. Distinguish missing implementation from imperfect precision. Continue physicalintegration using completed scoped module evidence; do not require wholepage/fullchip SPICE or signoff before article assembly. Qualified physicalpartitions are valid module evidence with explicit boundaryfixtures; they do not establish fullcoupled behavior.\n')
    p=R/'docs/project_spec.yaml';b=p.read_bytes().replace(b'article_module_catalog_v100.json',b'article_module_catalog_v101.json')
    b=re.sub(rb'  live_sessions: [^\r\n]+',b'  live_sessions: []',b,count=1)
    b=re.sub(rb'  module_simulation_coverage: [^\r\n]+',('  module_simulation_coverage: '+cp.relative_to(R).as_posix()).encode(),b,count=1);p.write_bytes(b)
    print(json.dumps({'report':str(report),'max_recovery_error_uV':s['max_recovery_error_v']*1e6,'catalog':101,'characterization_assemblies':len(cat['characterization_assemblies']),'full_chip_complete':False},indent=2))
if __name__=='__main__':main()
