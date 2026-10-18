"""Archive terminal ASIC job evidence before removing disposable containers."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1]
ARCHIVES=ROOT/'artifacts/analog_asic/operations/docker_container_archive'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def archived_container(identity):
    folder=ARCHIVES/identity;path=folder/'archive.json'
    assert path.is_file(),'Missing container has no verified terminal archive.'
    record=json.loads(path.read_text())
    assert record['container_id']==identity
    for name,expected in record['sha256'].items():assert digest(folder/name)==expected,name
    inspected=json.loads((folder/'inspect.json').read_text())[0]
    assert inspected['Id']==identity and not inspected['State']['Running'] and inspected['State']['Status']=='exited'
    return inspected,folder

def archive_and_remove(name,expected_id=None):
    found=subprocess.run(['docker','inspect',name],capture_output=True)
    if found.returncode:
        assert expected_id
        inspected,folder=archived_container(expected_id)
        return dict(container_id=expected_id,name=inspected['Name'].lstrip('/'),already_archived=True)
    inspected=json.loads(found.stdout)[0];identity=inspected['Id'];state=inspected['State']
    assert expected_id is None or identity==expected_id,'Container identity changed.'
    assert inspected['Name'].lstrip('/').startswith('ess-') and inspected['Config']['Image'].startswith('eventspikeseg:'), 'Outside ASIC attempt scope.'
    assert state['Status']=='exited' and not state['Running'],'Never remove a live job.'
    mounts={m['Destination']:m for m in inspected['Mounts']}
    assert mounts.get('/workspace',{}).get('Type')=='bind'
    for kind in ['logs','reports','results','objects']:
        destination='/OpenROAD-flow-scripts/flow/'+kind
        assert mounts.get(destination,{}).get('Type')=='bind','Results must be persisted outside the container.'
    diff=subprocess.run(['docker','diff',identity],capture_output=True);assert diff.returncode==0
    for line in diff.stdout.decode().splitlines():
        kind,path=line.split(' ',1)
        if kind!='A':continue
        disposable=path in ['/root/.local','/root/.local/state'] or path.startswith(('/tmp/','/root/.klayout','/root/.local/state/yosys')) or ('/usr/lib/klayout/pymod/' in path and ('__pycache__' in path or path.endswith('.pyc')))
        persisted=path in mounts
        assert disposable or persisted,('Review unpersisted added file before removing container',path)
    folder=ARCHIVES/identity;folder.mkdir(parents=True,exist_ok=True)
    logs=subprocess.run(['docker','logs',identity],capture_output=True);assert logs.returncode==0
    snapshots={'inspect.json':found.stdout,'stdout.log':logs.stdout,'stderr.log':logs.stderr,'filesystem_diff.txt':diff.stdout}
    for filename,data in snapshots.items():
        target=folder/filename
        if target.exists():assert target.read_bytes()==data,'Prior archive changed'
        else:target.write_bytes(data)
    record=dict(container_id=identity,name=inspected['Name'].lstrip('/'),exit_code=state['ExitCode'],
                archived_utc=datetime.now(timezone.utc).isoformat(),results_persisted_in_host_bind_mounts=True,
                sha256={name:digest(folder/name) for name in snapshots})
    path=folder/'archive.json'
    if not path.exists():path.write_text(json.dumps(record,indent=2)+'\n')
    archived_container(identity)
    # No force or volume deletion: a job that restarted meanwhile cannot be removed.
    removed=subprocess.run(['docker','rm',identity],capture_output=True,text=True)
    assert removed.returncode==0,removed.stderr
    result=dict(container_id=identity,name=record['name'],exit_code=state['ExitCode'],removed=True,
                archive=folder.relative_to(ROOT).as_posix())
    (folder/'removal.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--all-stopped-asic',action='store_true');parser.add_argument('--container')
    args=parser.parse_args();assert args.all_stopped_asic or args.container
    names=[args.container] if args.container else subprocess.check_output(['docker','ps','-a','--filter','status=exited','--filter','name=ess-','--format','{{.Names}}'],text=True).splitlines()
    for name in names:print(json.dumps(archive_and_remove(name)))
