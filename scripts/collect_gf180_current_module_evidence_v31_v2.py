"""Resolve nominal evidence against actual V9/V31 actor module versions."""
from pathlib import Path
import collections,json,hashlib
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';OUT=BASE/'assembly/full25_native_controls_v31'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    dest=OUT/'module_evidence_v2.json';assert not dest.exists();files={Path(__file__)}
    def read(p):files.add(p);return json.loads(p.read_text())
    source=BASE/'assembly/full25_page_forest_v9/physical_assembly.json';m=read(source);assert read(OUT/'independent_readback_v1.json')['readback_pass']
    counts=collections.Counter(p['cell'] for a in m['actor_regions'] for p in a['modules'])
    # Additional composed modules are retained by the independently byte-verified
    # V12/V13 hierarchy; this list identifies families, not repeated primitive counts.
    extras={'gf180_adaptation_shared_state_io_v6':15,'gf180_class_current_shared_io_v1':1,'gf180_six_class_readout_v3':1,'gf180_underplate_biased_bank8x8_v1':None}
    counts.update({k:v for k,v in extras.items() if v is not None});families=list(counts)+[k for k,v in extras.items() if v is None]
    aliases={'shared_reader_page1024_v1':'gf180_shared_reader_page1024_v1'}
    historical=read(BASE/'assembly/full25_class_current_service_v13/module_simulation_coverage_v1.json');catalog={r['cell']:r for r in historical['modules']}
    keys=('module_simulation_completed','simulation_completed','nominal_simulation_completed');rows=[]
    gate=BASE/'results/native_control_gates_v1/simulation.json'
    for cell in families:
        candidates=set((BASE/'results').glob(aliases.get(cell,cell)+'*.json'))
        for p in catalog.get(cell,{}).get('reports',[]):
            p=ROOT/p
            if p.exists():candidates.add(p)
        if cell in ('gf180_phase_inverter_fullroute','gf180_reset_select_and_fullroute'):candidates.add(gate)
        if cell=='gf180_fixed_body_tg_quarter_shorttracks':candidates.add(BASE/'results/native_transfer_gate_v1/simulation.json')
        reports=[]
        for p in sorted(candidates):
            r=read(p)
            if not any(r.get(k) is True for k in keys):continue
            changed=[]
            for ref,d in r.get('sha256',{}).items():
                target=ROOT/ref
                if target.suffix.lower() not in ('.spice','.gds'):continue
                if target.exists() and sha(target)!=d:changed.append(ref)
            reports.append(dict(report=p.relative_to(ROOT).as_posix(),completed=True,current_geometry_or_spice_hash_mismatches=changed,scope=r.get('scope',''),full_5ms_population_service_accepted=r.get('full_5ms_population_service_accepted',False)))
        valid=[r for r in reports if not r['current_geometry_or_spice_hash_mismatches']]
        rows.append(dict(cell=cell,actor_or_wrapper_instances=counts.get(cell),completed_nominal_reports=valid,stale_reports=[r for r in reports if r['current_geometry_or_spice_hash_mismatches']],completed_nominal_evidence_found=bool(valid),old_catalog_completed_flag=catalog.get(cell,{}).get('completed_nominal_report_found')))
    frontendp=BASE/'results/gf180_page1024_read_frontend_partition_v1_native_A_B_A.json';frontend=read(frontendp)
    assert frontend['module_simulation_completed'] and not frontend['full1024_connected_transient_completed']
    page_row=next(r for r in rows if r['cell']=='shared_reader_page1024_v1')
    page_row['partition_characterization']=dict(report=frontendp.relative_to(ROOT).as_posix(),completed=True,max_recovery_error_mV=frontend['max_recovery_error_v']*1000,full1024_connected_transient_completed=False,scope=frontend['scope'])
    tilep=BASE/'results/gf180_decoded_shared_compute_tile_v2_native_selected_row_cycle_v1.json';tile=read(tilep);assert tile['module_simulation_completed'];case=tile['cases'][0]
    bankp=BASE/'results/gf180_underplate_biased_bank8x8_v1_native_select_write_hold_read_srcaa37c91093be.json';bank=read(bankp);assert bank['module_simulation_completed']
    report=dict(current_module_evidence_collected=True,actual_actor_module_versions_source=source.relative_to(ROOT).as_posix(),families=rows,missing_completed_nominal=[r['cell'] for r in rows if not r['completed_nominal_evidence_found']],
                page1024_full_connected_transient_completed=False,compute_version_correction='Current compute is v2; the historical v1 incomplete flag is not current v2 coverage.',
                existing_selected_accumulation_witness=dict(source=tilep.relative_to(ROOT).as_posix(),horizon_us=230,selected_membrane='STATE70',selected_bank_change_mV=1000*(case['final_bank_state70_v']-case['bank_before_update_v']),compute_positive_pulse_step_mV=1000*case['positive_event_step_v'],writeback_error_mV=1000*case['writeback_error_vs_actual_column_v'],unselected_rows_max_change_mV=1000*tile['max_unselected_rows_change_v'],other_selected_row_columns_max_change_mV=1000*tile['max_other_columns_row7_change_v'],original_full_update_flag=tile['native_closed_loop_update_observed'],scope='One selected row/cell, positive-event/update sequence including beta and output phases. The full update flag fails reset behavior; positive charge and stored-state change are measured observations, not a complete signed/event-stream or5ms-population pass.'),
                native_bank_retention_witness=dict(source=bankp.relative_to(ROOT).as_posix(),states=len(bank['states']),minimum_hold_ms=5,max_hold_excursion_mV=1000*max(s['max_hold_excursion_v'] for s in bank['states']),scope=bank['scope']),
                full_architecture_layout_complete=False,connected_accumulation_retention_case_complete=False,accumulation_5ms_accepted=False,
                next_required_evidence='Focused connected selected-event accumulation/commit followed by5ms retention, with stated signed pulses/workload and row preservation. Existing separate positive-update and bank-retention cases do not prove that combined case or full-population5ms.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)})
    dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(families=len(rows),missing=report['missing_completed_nominal'],accumulation=report['existing_selected_accumulation_witness'],retention_excursion_mV=report['native_bank_retention_witness']['max_hold_excursion_mV'])),flush=True)
if __name__=='__main__':main()
