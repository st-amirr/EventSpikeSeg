"""Audit ASAP7 analog prerequisites without launching an ORFS campaign.

Exit 2 means required circuit/layout evidence is missing or fails content checks.
Does not manufacture macro views from behavioral SPICE or reuse SKY130 results.
File presence alone never yields full_orfs_ready=true.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/analog_asic/asap7'
PDK = ROOT / 'artifacts/analog_asic/pdk/asap7/asap7_pdk_r1p7'

EXPECTED_STATES = 30_976_000
EXPECTED_ACTORS = 25
MIN_GDS_BYTES = 256
MIN_LEF_BYTES = 128
MIN_ORFS_TOP_BYTES = 64
MIN_SDC_BYTES = 32


def _sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _load_json(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def _validate_capacitor_qualification(doc) -> list[str]:
    blockers = []
    if doc is None:
        return ['capacitor_qualification_unreadable']
    if doc.get('decision') != 'B_mos_cgg_storage':
        blockers.append('capacitor_qualification_decision_not_option_b')
    topo = str(doc.get('topology', ''))
    if 'gate=state' not in topo or 'drain' not in topo.lower():
        blockers.append('capacitor_qualification_topology_missing_gate_storage')
    if doc.get('accepted_as_physical_mim') is True:
        blockers.append('capacitor_qualification_ falsely_claims_mim')
    if not doc.get('accepted_as_option_b_candidate'):
        blockers.append('capacitor_qualification_candidate_not_accepted')
    # Candidate acceptance must include retention, not only drain/adjust.
    if doc.get('accepted_as_option_b_candidate'):
        ret = doc.get('retention_5ms') or {}
        if not ret.get('provisional_0_02_unit_retention_pass'):
            blockers.append('capacitor_qualification_accepted_without_retention_pass')
        cv = doc.get('effective_capacitance') or {}
        ceff = cv.get('ceff_per_finger_fF')
        if not (isinstance(ceff, (int, float)) and ceff > 0):
            blockers.append('capacitor_qualification_accepted_without_positive_ceff')
        adj = doc.get('drain_adjust') or {}
        if not adj.get('pass_drain_and_adjust'):
            blockers.append('capacitor_qualification_accepted_without_drain_adjust')
        if doc.get('partial_run'):
            blockers.append('capacitor_qualification_accepted_from_partial_run')
    return blockers


def _validate_macro_views(doc) -> list[str]:
    blockers = []
    if doc is None:
        return ['macro_views_unreadable']
    macros = doc.get('macros')
    if not isinstance(macros, list) or not macros:
        return ['macro_views_empty']
    for i, m in enumerate(macros):
        if not isinstance(m, dict):
            blockers.append(f'macro_views_entry_{i}_not_object')
            continue
        for key in ('name', 'gds', 'lef'):
            if not m.get(key):
                blockers.append(f'macro_views_{m.get("name", i)}_missing_{key}')
        for key in ('gds', 'lef'):
            rel = m.get(key)
            if not rel:
                continue
            path = OUT / rel if not Path(rel).is_absolute() else Path(rel)
            if not path.is_file():
                blockers.append(f'macro_views_missing_file_{key}_{m.get("name", i)}')
            else:
                size = path.stat().st_size
                need = MIN_GDS_BYTES if key == 'gds' else MIN_LEF_BYTES
                if size < need:
                    blockers.append(f'macro_views_{key}_too_small_{m.get("name", i)}')
        # Empty-box / behavioral placeholders are not physical macros.
        if m.get('behavioral_only') or m.get('empty_box'):
            blockers.append(f'macro_views_placeholder_{m.get("name", i)}')
    if doc.get('sky130_reuse'):
        blockers.append('macro_views_sky130_reuse_forbidden')
    return blockers


def _validate_physical_validation(doc) -> list[str]:
    blockers = []
    if doc is None:
        return ['physical_validation_unreadable']
    if not doc.get('macros_accepted'):
        blockers.append('physical_validation_macros_not_accepted')
    # Require explicit evidence, not a lone boolean.
    for key in ('drc_status', 'lvs_status', 'extraction_status'):
        status = doc.get(key)
        if status not in ('pass', 'passed', 'ok'):
            blockers.append(f'physical_validation_{key}_not_pass')
    reports = doc.get('report_paths') or doc.get('evidence_paths') or []
    if not isinstance(reports, list) or not reports:
        blockers.append('physical_validation_missing_evidence_paths')
    else:
        existing = 0
        for rel in reports:
            path = OUT / rel if not Path(str(rel)).is_absolute() else Path(rel)
            if path.is_file() and path.stat().st_size > 0:
                existing += 1
        if existing == 0:
            blockers.append('physical_validation_evidence_files_absent')
    return blockers


def _validate_assembly_preflight(doc) -> list[str]:
    blockers = []
    if doc is None:
        return ['assembly_preflight_unreadable']
    if not doc.get('inventory_conserved'):
        blockers.append('assembly_inventory_not_conserved')
    states = doc.get('logical_membrane_identities') or doc.get('states')
    if states != EXPECTED_STATES:
        blockers.append('assembly_state_count_not_140k')
    actors = doc.get('actors') or doc.get('actor_count')
    if actors != EXPECTED_ACTORS:
        blockers.append('assembly_actor_count_not_25')
    if doc.get('model') not in (None, 'EventSpikeSeg140k'):
        if doc.get('model') != 'EventSpikeSeg140k':
            blockers.append('assembly_model_not_140k')
    return blockers


def _validate_orfs_files() -> list[str]:
    blockers = []
    top = OUT / 'orfs/top.v'
    sdc = OUT / 'orfs/constraints.sdc'
    cfg = OUT / 'orfs/config.mk'
    if not top.is_file() or top.stat().st_size < MIN_ORFS_TOP_BYTES:
        blockers.append('orfs_top_missing_or_too_small')
    else:
        text = top.read_text(errors='ignore')
        if 'module' not in text:
            blockers.append('orfs_top_missing_module')
        if re.search(r'\bblack.?box\b', text, re.I) and 'unimplemented' in text.lower():
            blockers.append('orfs_top_marks_unimplemented_blackboxes')
    if not sdc.is_file() or sdc.stat().st_size < MIN_SDC_BYTES:
        blockers.append('orfs_sdc_missing_or_too_small')
    else:
        text = sdc.read_text(errors='ignore')
        if 'clock' not in text.lower() and 'create_clock' not in text.lower():
            blockers.append('orfs_sdc_missing_clock')
    if not cfg.is_file() or cfg.stat().st_size < 16:
        blockers.append('orfs_config_missing_or_too_small')
    else:
        text = cfg.read_text(errors='ignore')
        if 'DESIGN' not in text and 'DESIGN_NAME' not in text:
            blockers.append('orfs_config_missing_design_name')
    return blockers


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / 'results').mkdir(exist_ok=True)
    card = PDK / 'models/hspice/7nm_TT_160803.pm'
    osdi = OUT / 'tools/bsimcmg107.osdi'
    ngspice = OUT / 'tools/ngspice45/bin/ngspice'
    probe = OUT / 'device_probe.cir'
    assert card.is_file() and probe.is_file(), 'Fetch pinned ASAP7 PDK and probe first'

    compatibility = OUT / 'results/compatibility_checks.json'
    current_checks = _load_json(compatibility) or {}
    results = current_checks.get('results', [])
    by_bench = {r.get('bench'): r for r in results}
    inverter_ok = all(
        by_bench.get(name, {}).get('simulation_completed') and by_bench.get(name, {}).get('rail_check_passed')
        for name in ('inverter_dc_check', 'inverter_transient')
    )
    plif = by_bench.get('sampled_plif_external', {})
    plif_smoke_ok = bool(
        plif.get('simulation_completed')
        and plif.get('spike_sequence_pass')
        and plif.get('provisional_state_error_pass')
        and (plif.get('final_independent_value') or 0) >= 80e-6 * 0.999
    )

    legacy_supported = False
    legacy_exit = None
    try:
        legacy = subprocess.run(
            ['docker', 'run', '--rm', '--memory', '1g', '--cpus', '1',
             '--volume', f'{ROOT}:/workspace:ro',
             '--workdir', '/workspace/artifacts/analog_asic/asap7',
             '--entrypoint', 'ngspice', 'eventspikeseg:analog-ngspice36',
             '-b', 'device_probe.cir'],
            capture_output=True, text=True, timeout=60)
        legacy_exit = legacy.returncode
        log = legacy.stdout + legacy.stderr
        (OUT / 'results/device_probe.log').write_text(log)
        legacy_supported = (
            legacy.returncode == 0 and 'unsupported' not in log.lower()
            and 'could not find a valid modelname' not in log.lower()
            and 'Only MOS device levels' not in log
        )
    except Exception as exc:
        (OUT / 'results/device_probe.log').write_text(f'legacy probe skipped: {exc}\n')

    required_paths = {
        'capacitor_physical_qualification': OUT / 'capacitor_qualification.json',
        'analog_macro_view_inventory': OUT / 'macro_views.json',
        'macro_drc_lvs_extraction_evidence': OUT / 'physical_validation.json',
        'model_conserving_assembly_preflight': OUT / 'assembly_preflight.json',
        'orfs_top_netlist': OUT / 'orfs/top.v',
        'orfs_constraints': OUT / 'orfs/constraints.sdc',
        'orfs_configuration': OUT / 'orfs/config.mk',
    }
    absent = [key for key, path in required_paths.items() if not path.is_file()]
    present_hashes = {key: _sha(path) for key, path in required_paths.items() if path.is_file()}

    blockers = list(absent)
    if not osdi.is_file():
        blockers.append('bsimcmg107_osdi_missing')
    if not ngspice.is_file():
        blockers.append('ngspice45_binary_missing')
    if not inverter_ok:
        blockers.append('osdi_inverter_checks_incomplete')
    if not plif_smoke_ok:
        blockers.append('sampled_plif_external_smoke_incomplete')

    # Content validation for every present prerequisite (not flags alone).
    content_blockers = []
    content_blockers += _validate_capacitor_qualification(
        _load_json(required_paths['capacitor_physical_qualification']))
    if required_paths['analog_macro_view_inventory'].is_file():
        content_blockers += _validate_macro_views(
            _load_json(required_paths['analog_macro_view_inventory']))
    if required_paths['macro_drc_lvs_extraction_evidence'].is_file():
        content_blockers += _validate_physical_validation(
            _load_json(required_paths['macro_drc_lvs_extraction_evidence']))
    if required_paths['model_conserving_assembly_preflight'].is_file():
        content_blockers += _validate_assembly_preflight(
            _load_json(required_paths['model_conserving_assembly_preflight']))
    if all(required_paths[k].is_file() for k in (
            'orfs_top_netlist', 'orfs_constraints', 'orfs_configuration')):
        content_blockers += _validate_orfs_files()
    # If a required file is present, its content blockers still apply even when
    # siblings are absent (partial trees must not look ready).
    for b in content_blockers:
        if b not in blockers:
            # Skip "unreadable/empty" noise only when the file itself is absent.
            if b.endswith('_unreadable') or b.endswith('_empty'):
                key_map = {
                    'capacitor_qualification_unreadable': 'capacitor_physical_qualification',
                    'macro_views_unreadable': 'analog_macro_view_inventory',
                    'macro_views_empty': 'analog_macro_view_inventory',
                    'physical_validation_unreadable': 'macro_drc_lvs_extraction_evidence',
                    'assembly_preflight_unreadable': 'model_conserving_assembly_preflight',
                }
                req = key_map.get(b)
                if req and req in absent:
                    continue
            blockers.append(b)

    scoped_limitations = []
    if not legacy_supported:
        scoped_limitations.append(
            'ngspice36 does not accept unmodified ASAP7 HSPICE level-72 cards; active path is ngspice45+OSDI Berkeley107')
    if plif_smoke_ok:
        scoped_limitations.append(
            'accepted PLIF smoke still uses provisional finite-gm sense, logistic compare+track-hold, and ideal capacitors until MOSCAP integration')

    # Ready only when nothing is missing and every content check passed.
    full_orfs_ready = len(blockers) == 0

    report = dict(
        requested_pdk='ASAP7',
        pdk_revision=subprocess.check_output(
            ['git', '-C', str(PDK), 'rev-parse', 'HEAD'], text=True).strip(),
        model_sha256=_sha(card),
        osdi_sha256=_sha(osdi),
        ngspice45_present=ngspice.is_file(),
        active_simulator='ngspice45_osdi_bsimcmg107',
        legacy_ngspice36_hspice_card_probe_passed=legacy_supported,
        legacy_ngspice36_probe_exit_code=legacy_exit,
        osdi_ngspice45_basic_device_checks_pass=inverter_ok,
        sampled_plif_external_smoke_pass=plif_smoke_ok,
        osdi_qualification=(
            'Original Berkeley107 with documented EOTACC parameter-range adaptation; '
            'no HSPICE cross-validation'
        ),
        current_compatibility_checks=current_checks,
        baseline_freeze_sha256=_sha(OUT / 'baseline_freeze.json'),
        missing_prerequisites=absent,
        present_prerequisite_sha256=present_hashes,
        content_validation_blockers=content_blockers,
        blockers=blockers,
        scoped_limitations=scoped_limitations,
        full_orfs_ready=full_orfs_ready,
        note=(
            'full_orfs_ready requires present files AND content checks: Option-B capacitor '
            'qualification with retention, real macro GDS/LEF sizes, DRC/LVS/extraction '
            'evidence paths, conserved 140k inventory, and non-placeholder ORFS collateral.'
        ),
        preserved_prototype='SKY130 results remain under artifacts/analog_asic/results and are not ASAP7 evidence',
    )
    (OUT / 'readiness.json').write_text(json.dumps(report, indent=2) + '\n')
    print('ASAP7 full ORFS ready:', 'YES' if full_orfs_ready else 'NO')
    print('OSDI inverter checks:', inverter_ok)
    print('PLIF external smoke:', plif_smoke_ok)
    for name in blockers:
        print('BLOCKER:', name)
    for note in scoped_limitations:
        print('LIMITATION:', note)
    return 0 if full_orfs_ready else 2


if __name__ == '__main__':
    raise SystemExit(main())
