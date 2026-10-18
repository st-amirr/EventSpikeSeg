"""Verify the remaining native compute-operation pads in the final research GDS."""
from pathlib import Path
import json
from gf180_fast_cells_v1 import cells_read
from assemble_gf180_full25_shared_page1024_v7 import labels
from assemble_gf180_accumulation_fabric_ingress_v1 import sha
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';OUT=BASE/'assembly/full25_native_controls_v31'

def main():
    dest=OUT/'native_operation_pads_v1.json';assert not dest.exists()
    mp=OUT/'physical_assembly.json';m=json.loads(mp.read_text());proof=OUT/'independent_readback_v1.json';assert json.loads(proof.read_text())['readback_pass']
    gds=ROOT/m['gds'];assert sha(gds)==m['sha256'][m['gds']];_,cells=cells_read(gds.read_bytes())
    bp=BASE/'assembly/full25_layout_integration_v14/actor_boundary_ports_v1.json';bound=json.loads(bp.read_text());ep=BASE/'assembly/full25_analog_interfaces_v24/escape_plan.json';escapes=json.loads(ep.read_text());already={(e['actor_index'],e['native_pin']) for e in escapes['escapes'] if e['endpoint_kind']=='actor'}
    drive=['compute__INIT','compute__INITB','compute__RESTORE','compute__RESTOREB','compute__PARK_BIAS','compute__C_PARK_AZ','compute__C_PARK_AZB','compute__C_WRITE','compute__C_WRITEB','compute__C_AUXRESET','compute__C_AUXREF','compute__C_SENSE_REF','compute__C_SENSE_BIAS','compute__C_OUTPUT_HOLD','compute__C_OUTPUT_HOLDB','compute__C_RESET_PROGRAM','compute__C_NCAS','compute__C_INJ_PPROGRAM','compute__C_INJ_NPROGRAM','compute__C_PCAS','compute__C_PARK','compute__UP_BIAS','compute__DOWN_BIAS']
    observe=['EXTERNAL_COMPUTE_DATA','EXTERNAL_RECOVERED','EXTERNAL_SHIFTED','PAGE_RECOVERED','PAGE_SHIFTED','compute__RECOV']
    v15p=BASE/'assembly/full25_spike_breakouts_v15/physical_assembly.json';v15=json.loads(v15p.read_text())
    entries=[]
    for a in bound['actors']:
        ai=a['actor_index'];n=a['native_actor'];actual_cell=v15['cloned_cells'].get(n['cell'],n['cell']);actual=labels(cells[actual_cell]);ox,oy=n['origin_top_dbu']
        for name in drive+observe:
            if (ai,name) in already:continue
            es=n['ports'][name];assert len(es)==1;e=es[0];l,x,y=actual[name]
            assert l==e['layer'] and [x,y]==e['xy_local_dbu'] and [x+ox,y+oy]==e['xy_top_dbu'],(ai,name)
            entries.append(dict(actor_index=ai,actor=a['actor'],native_cell=actual_cell,native_pin=name,layer=l,xy_top_dbu=e['xy_top_dbu'],role='external_native_operation_input' if name in drive else 'observation_only',external_drive_allowed=name in drive,interface_access='in_situ_native_module_pad',extended_to_wrapper_boundary=False))
    report=dict(native_operation_pad_labels_verified=True,entries=entries,verified_count=len(entries),scope='Actual native GDS TEXT and preserved physical source-module pad coordinates for remaining operation inputs and observations. These in-situ pads are research probe/stimulus interfaces; no package pads or extra parent boundary routing is claimed. Their native circuit extraction remains source-module evidence.',sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/gf180_fast_cells_v1.py',mp,proof,gds,bp,ep,v15p]})
    dest.write_text(json.dumps(report,indent=2)+'\n');print('Verified native operation pads: '+str(len(entries)),flush=True)
if __name__=='__main__':main()
