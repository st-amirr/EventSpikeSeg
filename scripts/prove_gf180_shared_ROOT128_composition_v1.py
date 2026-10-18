"""Prove two existing64-channel native reducers on one ROOT equal native128 topology."""
from pathlib import Path
import hashlib,json,re,subprocess
from gf180_compact_lvs_v2 import compact
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'

def main():
    d=B/'verification/shared_ROOT128_composition_v1';assert not d.exists();d.mkdir()
    cells=[f'gf180_energy_mean_root{n}_v1' for n in [64,128]]
    fs=[B/'layout'/c/(c+'.spice') for c in cells]
    qs=[B/'layout'/c/'qualification.json' for c in cells]
    q64,q128=[json.loads(p.read_text()) for p in qs]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for c,p,q in zip(cells,fs,[q64,q128]):
        assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0
        assert sha(p)==q['sha256'][p.name]
    ports=q128['ports'];text=fs[0].read_text()+'\n.subckt paired128 '+' '.join(ports)+'\n'
    for block in range(2):
        mapped=[re.sub(r'^(IN_[PN])(\d+)$',lambda m:m[1]+str(int(m[2])+64*block),p) for p in q64['ports']]
        text+=f'Xhalf{block} '+' '.join(mapped)+' '+cells[0]+'\n'
    text+='.ends\n';(d/'paired_hierarchical_reference.spice').write_text(text)
    a,sa=compact(text,'paired128');b,sb=compact(fs[1].read_text(),cells[1])
    assert sa['primitive_devices']==sb['primitive_devices']==896
    a=a.replace('.subckt paired128 ','.subckt parent ',1)
    b=b.replace('.subckt '+cells[1]+' ','.subckt parent ',1)
    sp=d/'paired_flat.spice';rp=d/'full128_flat.spice';sp.write_text(a);rp.write_text(b)
    proof=d/'exact_composition.json'
    run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:torch2.2.2-cuda11.8','120','python','scripts/compare_gf180_exact_unique_net_bijection_v1.py','--source',sp.relative_to(R).as_posix(),'--other',rp.relative_to(R).as_posix(),'--report',proof.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135)
    (d/'proof.log').write_text(run.stdout+run.stderr)
    ok=run.returncode==0 and proof.exists() and json.loads(proof.read_text())['all_subcircuits_compositionally_equivalent']
    o={'two64_shared_ROOT_equals_native128_primitive_graph':ok,'native_primitives':896,
       'native_square_kernels':128,'native_root_receivers':128,
       'mechanism':'ROOT is the current-summing/root-feedback node,not a buffered RMS voltage output. Sharing ROOT and VBASE/VDD/VSS connects128 quadratic kernels and128 native receiver devices, identical to existing native128 reducer. Do not average two independently buffered RMS voltage results.',
       'next_physical_action':'Join ROOT ports of the two existing formatted64 macros in each128-channel actor; keep individual channel identities and shared formatter reference/penalty contracts. No added sqrt or voltage averaging circuit needed.',
       'physical_parent_routing_qualified':False,'nominal128_parent_simulation_completed':False,'full_chip_complete':False,
       'scope':'Exact complete primitive/pin/edge equivalence proves proposed composition. Existing qualified children do not qualify new physical parent wires or analog accuracy. Native receiver threshold/gain errors and epsilon remain unaccepted.',
       'sha256':{p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),*fs,*qs,sp,rp,proof] if p.exists()}}
    (d/'composition_review.json').write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k!='sha256'},indent=2));assert ok

if __name__=='__main__':main()
