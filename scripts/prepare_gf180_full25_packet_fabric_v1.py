"""Connect the routed graph to 25 scalar result macros using hierarchical ORFS."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
import argparse

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'artifacts/analog_asic'
NAME = 'gf180_analog_full25_packet_fabric_v1'
VARIANT = 'packet_fabric_v1'
CONTAINER = 'ess-gf180-full25-packet-fabric-v1'
OUT = BASE/'assembly/full25_packet_fabric_v1'
CONFIG = ROOT/'asic/analog/orfs/gf180_full25_packet_fabric_v1'
GRAPH = 'gf180_analog_full25_event_graph_interconnect_v1'
ADAPTER = 'gf180_analog_scalar_result_packet_v1'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def workspace(p): return '/workspace/'+p.relative_to(ROOT).as_posix()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--resume-preparation',action='store_true')
    options=parser.parse_args()
    assert not OUT.exists() or (options.resume_preparation and not (OUT/'status.json').exists()), 'Preserve existing job and inspect its handle.'
    assert subprocess.run(['docker','inspect',CONTAINER],capture_output=True).returncode != 0
    OUT.mkdir(parents=True,exist_ok=options.resume_preparation)
    CONFIG.mkdir(parents=True,exist_ok=True)
    macros=[]
    for job in ['full25_event_graph_layout_v1','scalar_result_packet_layout_v1']:
        statuspath=BASE/'assembly'/job/'status.json'
        status=json.loads(statuspath.read_text())
        assert status['stage']=='physical_macro_completed'
        evidence=BASE/'assembly'/job/'physical_macro.json'
        macro=json.loads(evidence.read_text())
        assert macro['route_metrics']['detailedroute__route__drc_errors']==0
        files=BASE/'orfs/results/gf180'/status['design']/status['variant']
        for relative,digest in macro['sha256'].items():
            assert sha(ROOT/relative)==digest, relative
        # Same geometry, new timing abstract at the analog system's 3.3V supply.
        lib=OUT/(status['design']+'_3v3.lib')
        tcl=OUT/(status['design']+'_abstract_3v3.tcl')
        if options.resume_preparation and lib.exists():
            assert lib.stat().st_size>1000
            macros.append({'name':status['design'],'lef':files/(status['design']+'.lef'),
                           'gds':files/'6_final.gds','lib':lib,'evidence':evidence})
            continue
        tcl.write_text('read_liberty /OpenROAD-flow-scripts/flow/platforms/gf180/lib/gf180mcu_fd_sc_mcu9t5v0__tt_025C_3v30.lib.gz\n'
                       f'read_db {workspace(files/"6_final.odb")}\nread_sdc {workspace(files/"6_final.sdc")}\n'
                       f'read_spef {workspace(files/"6_final.spef")}\nwrite_timing_model {workspace(lib)}\nexit\n')
        run=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','1',
                            '--volume',f'{ROOT}:/workspace:ro','--volume',f'{OUT}:{workspace(OUT)}',
                            '--entrypoint','/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad',
                            'eventspikeseg:orfs-guarded','-exit',workspace(tcl)],
                           capture_output=True,text=True,timeout=240)
        (OUT/(status['design']+'_abstract_3v3.log')).write_text(run.stdout+run.stderr)
        assert run.returncode==0 and lib.is_file() and lib.stat().st_size>1000,run.stderr[-2000:]
        macros.append({'name':status['design'],'lef':files/(status['design']+'.lef'),
                       'gds':files/'6_final.gds','lib':lib,'evidence':evidence})
    flat=ROOT/'asic/analog/orfs/gf180_full25_event_graph_v1/full25_event_graph_flat.sv'
    header=flat.read_text().split(');',1)[0].split('module '+GRAPH,1)[1]
    original_ports=re.findall(r'\b(?:input|output)\s+logic\s+(?:\[[^]]+\]\s*)?(\w+)',header)
    assert len(original_ports)==26, len(original_ports)
    kept=[]; internal=[]
    for line in header.splitlines():
        if 'actor_out_' in line:
            internal.append(line.replace('input logic','wire').replace('output logic','wire').replace(',', ';'))
        else: kept.append(line)
    # Reconstruct declarations from parsed original header to avoid comma changes
    # accidentally producing invalid internal declarations on multi-port lines.
    internal=[]
    for direction,width,port in re.findall(r'\b(input|output)\s+logic\s*(\[[^]]+\])?\s*(\w+)',header):
        if port.startswith('actor_out_'):internal.append(f'  wire {width} {port};')
    top_ports=[]
    for direction,width,port in re.findall(r'\b(input|output)\s+logic\s*(\[[^]]+\])?\s*(\w+)',header):
        if not port.startswith('actor_out_'):top_ports.append(f'  {direction} wire {width} {port}')
    top_ports+=['  input wire [24:0] result_valid_i','  output wire [24:0] result_ready_o',
                '  input wire [24:0] result_spike_i','  input wire [649:0] result_address_i',
                '  input wire [599:0] result_bin_tag_i','  input wire [24:0] result_last_i',
                '  output wire [24:0] result_tag_error_o','  output wire [24:0] result_order_error_o']
    text='// Hierarchical categorical fabric. All numeric state and weights remain analog.\n'
    text+='// result_last_i is full actor-bin completion after all neuron decisions.\n'
    text+=f'module {NAME} (\n'+',\n'.join(top_ports)+'\n);\n'+'\n'.join(internal)+'\n'
    text+=f'  {GRAPH} graph_macro (\n'+',\n'.join('    .'+p+'('+p+')' for p in original_ports)+'\n  );\n'
    for i in range(25):
        connections={'clk':'clk','reset':'reset','result_valid_i':f'result_valid_i[{i}]',
                     'result_ready_o':f'result_ready_o[{i}]','result_spike_i':f'result_spike_i[{i}]',
                     'result_address_i':f'result_address_i[{26*i} +: 26]',
                     'result_bin_tag_i':f'result_bin_tag_i[{24*i} +: 24]',
                     'result_last_i':f'result_last_i[{i}]',
                     'event_valid_o':f'actor_out_valid_i[{i}]','event_ready_i':f'actor_out_ready_o[{i}]',
                     'event_payload_o':f'actor_out_payload_i[{32*i} +: 32]',
                     'event_completion_o':f'actor_out_completion_i[{i}]',
                     'event_bin_tag_o':f'actor_out_bin_tag_i[{24*i} +: 24]',
                     'tag_mismatch_o':f'result_tag_error_o[{i}]','address_order_error_o':f'result_order_error_o[{i}]'}
        text+=f'  {ADAPTER} result_{i:02d} (\n'+',\n'.join(f'    .{p}({v})' for p,v in connections.items())+'\n  );\n'
    text+='endmodule\n'
    rtl=ROOT/'asic/analog'/(NAME+'.sv');rtl.write_text(text)
    # Read only the macro port declarations as blackboxes, preserving existing GDS.
    blackboxes=CONFIG/'macro_blackboxes.v'
    declarations=[]
    for macro in macros:
        definition=(flat if macro['name']==GRAPH else ROOT/'asic/analog'/(ADAPTER+'.sv')).read_text()
        port_header=definition.split('module '+macro['name'],1)[1].split(');',1)[0]
        declarations.append('(* blackbox *) module '+macro['name']+port_header+');\nendmodule\n')
    blackboxes.write_text('\n'.join(declarations))
    sdc=CONFIG/'constraint.sdc'
    sdc.write_text('create_clock -name clk -period 20 [get_ports clk]\n'
                   'set_clock_uncertainty -setup 1 [get_clocks clk]\n'
                   'set_clock_uncertainty -hold 0.2 [get_clocks clk]\n'
                   'set_input_delay -max 1 -clock clk [all_inputs -no_clocks]\n'
                   'set_output_delay 1 -clock clk [all_outputs]\n'
                   'set_false_path -from [get_ports reset]\n')
    placement=CONFIG/'macro_placement.tcl'
    placement.write_text('place_macro -macro_name graph_macro -location {2200 800} -orientation R0\n'+
                         '\n'.join(f'place_macro -macro_name result_{i:02d} -location {{{100+(i%5)*360} {100+(i//5)*650}}} -orientation R0' for i in range(25))+'\n')
    config=CONFIG/'config.mk'
    config.write_text(f'export DESIGN_NAME = {NAME}\nexport DESIGN_NICKNAME = {NAME}\nexport PLATFORM = gf180\n'
                      f'export VERILOG_FILES = {workspace(blackboxes)} {workspace(rtl)}\n'
                      f'export SDC_FILE = {workspace(sdc)}\n'
                      'export CORNER = TC\n'
                      'export TC_LIB_FILES = /OpenROAD-flow-scripts/flow/platforms/gf180/lib/gf180mcu_fd_sc_mcu9t5v0__tt_025C_3v30.lib.gz\n'
                      'export TC_VOLTAGE = 3.3\nexport TC_TEMPERATURE = 25c\n'
                      'export ADDITIONAL_LEFS = '+' '.join(workspace(m['lef']) for m in macros)+'\n'
                      'export ADDITIONAL_GDS = '+' '.join(workspace(m['gds']) for m in macros)+'\n'
                      'export ADDITIONAL_LIBS = '+' '.join(workspace(m['lib']) for m in macros)+'\n'
                      'export DIE_AREA = 0 0 4500 3500\nexport CORE_AREA = 20 20 4480 3480\n'
                      f'export MACRO_PLACEMENT_TCL = {workspace(placement)}\n'
                      'export PLACE_DENSITY = 0.30\nexport CLOCK_PERIOD = 20.0\n'
                      'export SYNTH_HIERARCHICAL = 0\nexport ABC_AREA = 1\n'
                      'export NUM_CORES = 2\nexport SKIP_CTS_REPAIR_TIMING = 1\n')
    command=['docker','run','--detach','--name',CONTAINER,'--network','none',
             '--memory','8g','--memory-swap','8g','--cpus','2','--volume',f'{ROOT}:/workspace:ro']
    for kind in ['logs','objects','reports','results']:
        command+=['--volume',f'{BASE/"orfs"/kind}:/OpenROAD-flow-scripts/flow/{kind}']
    args=f'DESIGN_CONFIG={workspace(config)} FLOW_VARIANT={VARIANT}'
    command+=['--entrypoint','timeout','eventspikeseg:orfs-guarded','3600','bash','-lc',
              f'make -C /OpenROAD-flow-scripts/flow {args} && make -C /OpenROAD-flow-scripts/flow {args} do-generate_abstract']
    run=subprocess.run(command,capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    evidence=[rtl,blackboxes,config,sdc,placement,Path(__file__)]+[p for m in macros for k,p in m.items() if k!='name']
    status={'stage':'physical_layout_running','started_utc':datetime.now(timezone.utc).isoformat(),
            'container':CONTAINER,'container_id':run.stdout.strip(),'design':NAME,'variant':VARIANT,
            'macro_instances':26,'scalar_actor_output_adapters':25,'graph_packet_edges':53,
            'supply_v':3.3,'command':command,'full_chip_layout_complete':False,
            'scope':'Actual hierarchical packet-fabric layout. Native actor SPIKE/sample/address/control and graph actor-input synapse bindings remain outside this macro.',
            'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in evidence}}
    (OUT/'status.json').write_text(json.dumps(status,indent=2)+'\n')
    print(json.dumps({'container':CONTAINER,'container_id':status['container_id'],'status':str(OUT/'status.json')},indent=2))

if __name__=='__main__':main()
