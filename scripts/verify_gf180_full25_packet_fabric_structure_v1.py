"""Check exact adapter-to-graph connectivity in the synthesized parent netlist."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
NAME='gf180_analog_full25_packet_fabric_v1'
OUT=BASE/'assembly/full25_packet_fabric_v1'

def main():
    dest=OUT/'synthesized_structure_v1.json'
    assert not dest.exists(), 'Preserve prior structural evidence.'
    netlist=BASE/'orfs/results/gf180'/NAME/'packet_fabric_v1/1_2_yosys.v'
    boxes=ROOT/'asic/analog/orfs/gf180_full25_packet_fabric_v1/macro_blackboxes.v'
    path=lambda p:'/workspace/'+p.relative_to(ROOT).as_posix()
    graph_json=OUT/'synthesized_netlist_v1.json'
    command=['docker','run','--rm','--network','none','--memory','2g','--cpus','1',
             '--volume',f'{ROOT}:/workspace:ro','--volume',f'{OUT}:{path(OUT)}',
             '--entrypoint','yosys','eventspikeseg:orfs-guarded','-Q','-T','-q','-p',
             f'read_verilog -sv {path(boxes)} {path(netlist)}; hierarchy -check -top {NAME}; write_json {path(graph_json)}']
    run=subprocess.run(command,capture_output=True,text=True,timeout=120)
    (OUT/'synthesized_structure_v1.log').write_text(run.stdout+run.stderr)
    assert run.returncode==0,run.stderr
    module=json.loads(graph_json.read_text())['modules'][NAME]
    cells=module['cells']; ports=module['ports']
    graph=cells['graph_macro']
    assert graph['type']=='gf180_analog_full25_event_graph_interconnect_v1'
    records=[]
    fields={'event_valid_o':('actor_out_valid_i',1),'event_ready_i':('actor_out_ready_o',1),
            'event_payload_o':('actor_out_payload_i',32),
            'event_completion_o':('actor_out_completion_i',1),
            'event_bin_tag_o':('actor_out_bin_tag_i',24)}
    external={'result_valid_i':1,'result_ready_o':1,'result_spike_i':1,
              'result_address_i':26,'result_bin_tag_i':24,'result_last_i':1,
              'result_tag_error_o':1,'result_order_error_o':1}
    adapters={n:c for n,c in cells.items() if c['type']=='gf180_analog_scalar_result_packet_v1'}
    assert len(adapters)==25
    for i in range(25):
        cell=adapters[f'result_{i:02d}']; conn=cell['connections']
        for local,(target,width) in fields.items():
            assert conn[local]==graph['connections'][target][i*width:(i+1)*width], (i,local)
        for top,width in external.items():
            local={'result_tag_error_o':'tag_mismatch_o','result_order_error_o':'address_order_error_o'}.get(top,top)
            assert conn[local]==ports[top]['bits'][i*width:(i+1)*width], (i,top)
        for control in ['clk','reset']:
            assert conn[control]==graph['connections'][control]==ports[control]['bits']
        records.append({'actor_index':i,'instance':f'result_{i:02d}',
                        'graph_packet_bits_checked':59,'external_result_bits_checked':56})
    result={'synthesized_structure_pass':True,'graph_instances':1,'scalar_adapters':25,
            'graph_packet_bit_connections_checked':1475,'actors':records,
            'scope':'Exact synthesized hierarchical net equivalence for all 25 scalar result boundaries, graph packet handshake/payload/completion/tag, external result buses and common clock/reset. Physical routing and analog producer binding remain separate requirements.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [netlist,boxes,graph_json,Path(__file__)]}}
    dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['actors','sha256']},indent=2))

if __name__=='__main__':main()
