"""Audit physical writer-memory integration and frozen comparisons without accepting storage."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    files={Path(__file__)}
    def verify(p):
        d=json.loads(p.read_text(encoding='utf-8'));files.add(p)
        for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
            for name,h in d.get(key,{}).items():
                item=p.parent/name if key=='sha256' and not name.startswith(('artifacts/','scripts/','docs/')) else ROOT/name
                assert sha(item)==h,str(item)
                files.add(item)
        return d
    physical=[]
    cells=['gf180_isolated_writer_resistor_network','gf180_isolated_memory_writer','gf180_writer_memory_characterization_preloaded','gf180_writer_memory_characterization_localpins']
    for cell in cells:
        p=BASE/'layout'/cell/'qualification.json';d=verify(p)
        assert d['magic_drc_count']==d['gds_roundtrip_drc_count']==0
        assert d['lvs_unique'] and d['gds_roundtrip_lvs_unique'] and not d['extraction_feedback']
        physical.append({'cell':cell,'report':p.relative_to(ROOT).as_posix(),'bbox_um':d['bbox_um'],'scope':d['scope']})
    abstracts=[]
    for cell in ['gf180_isolated_memory_characterization_fullroute',*cells[1:]]:
        p=BASE/'layout'/cell/'abstract_qualification.json';d=verify(p)
        assert d['physical_ports_and_size_verified'] and d['routing_obstructions_present'] and d['source_geometry_hashes_unchanged']
        abstracts.append({'cell':cell,'size_um':d['size_um'],'ports':len(d['ports'])})
    cases=[]
    patterns=['gf180_isolated_memory_routed_writer_*.json','gf180_writer_memory_parent_*.json','gf180_writer_memory_localpins_*.json']
    for pattern in patterns:
        for p in sorted((BASE/'results').glob(pattern)):
            d=verify(p);m=d['measurements'];assert d['simulation_completed'] and len(m)==45 and d['hold_interval_us']==5000
            assert not any(d[k] for k in ['physical_storage_accepted','original_float_accuracy_accepted','complete_PLIF_accepted','full_5ms_population_service_accepted','full_chip_accepted'])
            target=d['target_levels_v']
            cases.append({'report':p.relative_to(ROOT).as_posix(),'target_levels_v':target,'initial_target_error_v':{n:m[n+'_state_baseline']-v for n,v in target.items()},'max_initial_target_error_v':max(abs(m[n+'_state_baseline']-v) for n,v in target.items()),'max_hold_drift_v':max(abs(m[n+'_hold_error']) for n in target),'max_state_window_v':max(m[n+'_state_window_max']-m[n+'_state_window_min'] for n in target),'writer_memory_parent_layout_qualified':d['combined_writer_memory_layout_qualified']})
    assert len(cases)==4
    failed=BASE/'layout/gf180_writer_memory_characterization'
    for p in failed.iterdir():
        if p.is_file():files.add(p)
    for p in (BASE/'layout/gf180_writer_memory_characterization_preloaded').glob('*.failed_initial'):files.add(p)
    d={'audit_completed':True,'completed_transient_cases':len(cases),'cases':cases,'physical_modules':physical,'abstracts':abstracts,
       'decision':'Local diagnostic pins reduce parent bus variation4.52mV to1.23mV, but frozen initial target error remains5.13mV. Preserve both layouts; select local-pin structure for next physical calibration/readout study, not accepted precision or compact array.',
       'comparison_limit':'Local-pin variant also places modules closer and lowers global tracks; result isolates the routing package, not pin removal alone. Separate-module fixture has1ohm external BUS resistor; physical parent uses actual internal BUS. Calibration from schematic or separate modules does not transfer to assembled parent.',
       'scope':'Nominal deterministic full qualified cap-extracted parent performance. External references/clock stimuli/10mV column clamp, gate leakage and sampled noise unqualified, no RPEX/mismatch/PVT. Spacious characterization assemblies, not dense cells; no current decoder/range conversion or complete PLIF.',
       'next_action':'Freeze local-pin parent; measure calibration levels before one physical write-transfer correction and independent validation, then implement readout/range conversion. Evaluate measured errors against original float model and area/service budget before replication.',
       'physical_storage_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,
       'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
    p=BASE/'results/gf180_writer_memory_physical_boundary.json'
    assert not p.exists(),'Preserve prior audit'
    p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(p),'completed_cases':len(cases),'physical_modules':len(physical),'abstracts':len(abstracts),'comparisons':cases},indent=2))
if __name__=='__main__':main()
