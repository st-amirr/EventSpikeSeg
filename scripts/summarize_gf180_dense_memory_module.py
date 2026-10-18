"""Audit connected memory layout, bounded hold/read comparisons and write limitation."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    data=json.loads(path.read_text(encoding='utf-8'))
    for name,expected in data.get('sha256',{}).items():
        assert sha(ROOT/name)==expected,name
    return data

def main():
    source=Path(__file__)
    labels={
        'bank9_B_read':'gf180_dense_memory_feaf78d70c_srcb73c72b2da86.json',
        'minimum_B_read':'gf180_dense_memory_2fb798202e_srcb73c72b2da86.json',
        'minimum_B_no_read':'gf180_dense_memory_48a8d00f31_srcb73c72b2da86.json',
        'minimum_A_read':'gf180_dense_memory_writer_A_2fb798202e_src2bd56295f377.json',
        'connected_A_read':'gf180_dense_memory_connected_2fb798202e_srcf69a9392aaec.json',
        'connected_A_no_read':'gf180_dense_memory_connected_48a8d00f31_srcf69a9392aaec.json',
    }
    files={source}
    rows={}
    raw={}
    for label,name in labels.items():
        path=BASE/'results'/name
        data=read(path)
        assert data['simulation_completed'] and len(data['measurements'])==33
        assert data['hold_interval_us']==5000
        files.add(path)
        m=data['measurements']
        raw[label]=m
        rows[label]={'report':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'settings':data['settings'],
                     'levels':{n:{'write_release_error_uv':m[n+'_release_error']*1e6,
                                  'write_bus_rebias_step_uv':(m[n+'_state_baseline']-m[n+'_state_released'])*1e6,
                                  'uncompensated_baseline_error_uv':(m[n+'_state_baseline']-target)*1e6,
                                  'five_ms_hold_change_uv':m[n+'_hold_error']*1e6,
                                  'after_read_interval_change_uv':m[n+'_read_error']*1e6,
                                  'column_current_a':m[n+'_read_current'],
                                  'sense_drain_v':m[n+'_read_drain']}
                               for n,target in [('low',.75),('mid',1.65),('high',2.55)]},
                     'scope':data['scope']}
    qp=BASE/'layout/gf180_minimum_memory_characterization_fullroute/qualification.json'
    q=json.loads(qp.read_text(encoding='utf-8'))
    assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
    assert not q['extraction_feedback']
    for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
        for name,expected in q[key].items():
            p=qp.parent/name if key=='sha256' else ROOT/name
            assert sha(p)==expected,name
    abstract=qp.parent/'abstract_qualification.json'
    a=read(abstract)
    assert a['physical_ports_and_size_verified'] and a['routing_obstructions_present']
    assert set(a['ports'])==set(q['ports'])
    files.update([qp,abstract])
    x0,y0,x1,y1=q['bbox_um']
    area=(x1-x0)*(y1-y0)
    controls={}
    for n in ['low','mid','high']:
        controls[n]={
            'connected_after_interval_read_minus_no_read_v':raw['connected_A_read'][n+'_read_error']-raw['connected_A_no_read'][n+'_read_error'],
            'interpretation':'No resolved persistent extra read shift at this noise-disabled bench precision; not a physical precision guarantee. Temporary read disturbance and transfer nonlinearity remain.'}
    snapshot=BASE/'tools/source_snapshots'/('summarize_gf180_dense_memory_module_'+sha(source)+'.py')
    snapshot.write_bytes(source.read_bytes())
    files.add(snapshot)
    result={
        'audit_completed':True,'completed_transient_cases':6,'cases':rows,'matched_read_controls':controls,
        'physical_module':{'qualification':qp.relative_to(ROOT).as_posix(),'LEF_qualification':abstract.relative_to(ROOT).as_posix(),
                           'cell':q['cell'],'full_DRC':0,'LVS_unique':True,'GDS_readback_DRC':0,'GDS_readback_LVS_unique':True,
                           'native_mim_count':1,'mos_count':7,'size_um':a['size_um'],'footprint_um2':area,
                           'scope':'Reusable spacious characterization macro; not a packed array cell or minimum area. Real internal routing/cap extraction, no RPEX. External clock/bus/column links schematic.'},
        'decision':'Keep writer A orientation: worst release error falls from52.3763mV to7.38112mV in the matched child fixture. Connected extraction still has up to7.98977mV release error and39.506mV write-bus rebias step. Repair the write/representation contract and shared-bus coupling before array replication; low-disturbance current read alone is insufficient.',
        'hold_scope':'Exactly5000us deterministic interval with write bus serving other levels, typical27C, native gate leakage disabled and dielectric leakage/noise/PVT/mismatch unqualified. Max connected hold change96.2663uV is not qualified5ms retention.',
        'read_scope':'Ideal10mV external column clamp, real select/park TGs and NF sense transistor. Read currents are monotonic over three measured stored levels but no accurate current-to-state decoder or range conversion is implemented. Sense transistor is resident per stored state; density and standby/read power remain open.',
        'next_action':'Evaluate an actual physical low-feedthrough/compensated writer or a calibrated analog state representation with implemented conversion; verify on independent levels and bus sequences. Do not substitute ideal corrected state or fitted software subtraction for circuitry.',
        'physical_storage_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,
        'full_5ms_population_service_accepted':False,'full_chip_accepted':False,
        'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
    target=BASE/'results/gf180_dense_memory_module_boundary.json'
    assert not target.exists()
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(target),'completed_transients':6,'physical_module_size_um':a['size_um'],
                      'connected_levels':rows['connected_A_read']['levels']},indent=2))

if __name__=='__main__':
    main()
