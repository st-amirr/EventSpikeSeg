"""Collect terminal job evidence and real LEF terminals, without restarting jobs."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import re
import subprocess
from docker_attempt_lifecycle import archived_container,archive_and_remove

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('job',choices=['full25_event_graph_layout_v1','scalar_result_packet_layout_v1','full25_packet_fabric_v1','full25_decision_control_v2','full25_decision_control_v3','full25_actor_ingress_v1','full25_actor_ingress_v2','page_access_pair_control_v1','page_access_pair_control_v2','full25_accumulation_dispatch_v1'])
    args = parser.parse_args()
    directory = BASE / 'assembly' / args.job
    status_path = directory / 'status.json'
    status = json.loads(status_path.read_text())
    inspect = subprocess.run(['docker','inspect',status['container']],capture_output=True,text=True)
    archived_folder = None
    if inspect.returncode == 0:
        container = json.loads(inspect.stdout)[0]
    else:
        container,archived_folder = archived_container(status['container_id'])
    assert container['Id'] == status['container_id'], 'Container identity changed.'
    state = container['State']
    observation = {'observed_utc':datetime.now(timezone.utc).isoformat(),'container_id':container['Id'],'state':state}
    (directory / 'last_observation.json').write_text(json.dumps(observation,indent=2)+'\n')
    if state['Running']:
        print(json.dumps({'job':args.job,'running':True}))
        return
    if archived_folder is None:
        log = subprocess.run(['docker','logs',status['container']],capture_output=True,text=True)
        (directory / 'docker.log').write_text(log.stdout+log.stderr)
    elif status['stage']=='physical_macro_completed':
        saved=json.loads((directory/'physical_macro.json').read_text())
        for name,digest in saved['sha256'].items():assert sha(ROOT/name)==digest,('archived artifact changed',name)
        print(json.dumps({'job':args.job,'physical_macro_completed':True,'terminal_container_archived_and_removed':True}))
        return
    assert state['Status'] == 'exited', state
    files = BASE / 'orfs/results/gf180' / status['design'] / status['variant']
    logs = BASE / 'orfs/logs/gf180' / status['design'] / status['variant']
    required = ['6_final.gds','6_final.odb','6_final.def','6_final.v','6_final.spef',status['design']+'.lef']
    missing = [n for n in required if not (files/n).is_file() or (files/n).stat().st_size == 0]
    if state['ExitCode'] != 0 or missing:
        status.update(stage='physical_layout_failed',exit_code=state['ExitCode'],missing_artifacts=missing,
                      observed_utc=observation['observed_utc'])
        status_path.write_text(json.dumps(status,indent=2)+'\n')
        archive_and_remove(status['container'],status['container_id'])
        raise RuntimeError(json.dumps({'exit_code':state['ExitCode'],'missing':missing}))
    for relative, digest in status['sha256'].items():
        assert sha(ROOT/relative) == digest, ('source changed during physical job',relative)
    lef = (files/(status['design']+'.lef')).read_text()
    size = re.search(r'\bSIZE\s+([\d.]+)\s+BY\s+([\d.]+)',lef)
    assert size
    pins = {}
    for match in re.finditer(r'^  PIN (\S+)\n(.*?)^  END \1\s*$',lef,re.M|re.S):
        name, body = match.group(1,2)
        direction = re.search(r'DIRECTION (\w+)',body)
        rectangles = []
        for segment in re.finditer(r'LAYER (\w+)\s*;(.*?)(?=\bLAYER\b|\bEND\b|$)',body,re.S):
            for rect in re.finditer(r'RECT\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*;',segment[2]):
                xy = list(map(float,rect.groups()))
                rectangles.append({'layer':segment[1],'rect_um':xy,
                                   'center_um':[(xy[0]+xy[2])/2,(xy[1]+xy[3])/2]})
        assert rectangles, name
        pins[name] = {'direction':direction[1] if direction else None,'rectangles':rectangles}
    assert len(pins)>10
    metrics_path = logs/'6_report.json'
    metrics = json.loads(metrics_path.read_text())
    route_metrics = logs/'5_2_route.json'
    route = json.loads(route_metrics.read_text()) if route_metrics.exists() else {}
    lib_files = sorted(files.glob('*.lib*'))
    evidence = [files/n for n in required]+lib_files+[metrics_path]+([route_metrics] if route_metrics.exists() else [])
    result = {'physical_implementation_completed':True,'container_exit_code':state['ExitCode'],
              'design':status['design'],'variant':status['variant'],'size_um':list(map(float,size.groups())),
              'pin_count':len(pins),'ports':pins,'final_metrics':metrics,'route_metrics':route,
              'timing_voltage_scope':('GF180 typical 25C/3.3V standard cells and regenerated 3.3V macro timing abstracts.' if status.get('supply_v')==3.3 else 'ORFS default GF180 9t5v0 characterization, observed 5.5V corner; no 3.3V analog interface timing claim.'),
              'full_chip_layout_complete':False,
              'scope':'Routed categorical macro and actual terminal contract. Does not prove analog binding, global supply compatibility, parent routing, full-chip accuracy or 5ms service.',
              'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in evidence}}
    (directory/'physical_macro.json').write_text(json.dumps(result,indent=2)+'\n')
    status.update(stage='physical_macro_completed',exit_code=0,completed_utc=state['FinishedAt'],
                  evidence='physical_macro.json',full_chip_layout_complete=False)
    status_path.write_text(json.dumps(status,indent=2)+'\n')
    archive_and_remove(status['container'],status['container_id'])
    print(json.dumps({'job':args.job,'physical_macro_completed':True,'pin_count':len(pins),
                      'size_um':result['size_um'],'evidence':str(directory/'physical_macro.json')},indent=2))

if __name__ == '__main__': main()
