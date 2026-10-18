"""Build categorical event-to-weight addressing for the actual float actors."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'
OUT = BASE / 'assembly/full25_actor_ingress_v1'
CFG = ROOT / 'asic/analog/orfs/gf180_full25_actor_ingress_v1'
NAME = 'gf180_analog_full25_actor_ingress_v1'
VARIANT = 'actor_ingress_v1'
CONTAINER = 'ess-gf180-full25-actor-ingress-v1'
SHA = 'c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ws(p): return '/workspace/' + p.relative_to(ROOT).as_posix()
def save(p, value): p.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--launch', action='store_true')
    args = parser.parse_args()
    assert not OUT.exists(), 'Preserve earlier artifacts; do not overwrite.'
    paths = [BASE/'model_reference/eventspikeseg140k_float_reference.json',
             BASE/'assembly/full25actor_original_float_population_manifest_v1.json',
             BASE/'assembly/full25actor_analog_connectivity_v1.json']
    ref, population, graph = [json.loads(p.read_text(encoding='utf-8')) for p in paths]
    assert all(v['checkpoint_sha256'] == SHA for v in [ref, population, graph])
    weights = {v['name']: v for v in ref['effective_folded_weight_and_neuron_parameters']}
    nodes = {v['name']: v for v in graph['nodes']}
    cells = [ROOT/'asic/analog/gf180_analog_weight_event_scatter_parallel.sv',
             ROOT/'asic/analog/gf180_analog_actor_ingress_v1.sv']
    sim = BASE/'results/actor_ingress_v1/simulation.json'
    evidence = json.loads(sim.read_text())
    assert evidence['simulation_pass']
    assert all(evidence['sha256'][p.relative_to(ROOT).as_posix()] == sha(p) for p in cells)
    ports = [('input',1,'clk'),('input',1,'reset'),('input',1,'accumulate_enable_i'),
             ('input',1,'graph_valid_i'),('output',1,'graph_ready_o'),('input',32,'graph_payload_i'),
             ('input',1,'graph_completion_i'),('input',24,'graph_bin_tag_i'),
             ('output',1,'group_valid_o'),('input',1,'group_ready_i'),('input',1,'group_settled_done_i'),
             ('output',20,'weight_address_base_o'),('output',20,'weight_lane_stride_o'),
             ('output',8,'output_channel_base_o'),('output',8,'output_lane_count_o'),
             ('output',10,'output_x_o'),('output',10,'output_y_o'),
             ('output',24,'contribution_bin_tag_o'),('output',1,'bin_complete_valid_o'),
             ('input',1,'bin_complete_ready_i'),('output',24,'bin_complete_tag_o'),
             ('output',1,'busy_o'),('output',1,'tag_error_o'),('output',1,'input_error_o')]
    declarations = []
    for direction, width, name in ports:
        size = 1 if name in ['clk','reset'] else 25*width
        declarations.append(f'  {direction} wire '+(f'[{size-1}:0] ' if size > 1 else '')+name)
    text = '// Categorical addresses only; original float numerical parameters stay analog.\n'
    text += f'module {NAME} (\n'+',\n'.join(declarations)+'\n);\n'
    records = []
    for i, actor in enumerate(population['actors']):
        name = actor['actor']; weight = weights[name]
        incoming = [v for v in graph['edges'] if v['destination'] == name]
        assert len(incoming) == 1, (name, incoming)
        source = incoming[0]['source']
        cin, ih, iw = nodes[source]['shape_chw']
        cout, local_cin, kh, kw = weight['weight_shape_oihw']
        groups = weight['conv_groups']; sy, sx = weight['conv_stride']
        py, px = weight['conv_padding']; dy, dx = weight['conv_dilation']
        oh, ow = actor['height'], actor['width']
        assert [cout,local_cin,kh,kw] == actor['synaptic_weight_shape_oihw']
        assert cin == local_cin*groups and cout == actor['channels'] and cout % groups == 0
        assert (ih+2*py-dy*(kh-1)-1)//sy+1 == oh
        assert (iw+2*px-dx*(kw-1)-1)//sx+1 == ow
        assert cin <= 128 and cout <= 128 and iw <= 1024 and ih <= 512
        count = cout*local_cin*kh*kw
        assert count == actor['synaptic_weight_count'] == weight['weight']['count'] and count < 2**20
        parameters = dict(INPUT_CHANNELS=cin, OUTPUT_CHANNELS=cout, GROUPS=groups,
                          INPUT_WIDTH=iw, INPUT_HEIGHT=ih, OUTPUT_WIDTH=ow, OUTPUT_HEIGHT=oh,
                          KERNEL_WIDTH=kw, KERNEL_HEIGHT=kh, STRIDE_X=sx, STRIDE_Y=sy,
                          DILATION_X=dx, DILATION_Y=dy, PAD_X=px, PAD_Y=py)
        connections = []
        for _, width, port in ports:
            expression = port if port in ['clk','reset'] else (f'{port}[{i}]' if width == 1 else f'{port}[{i*width} +: {width}]')
            connections.append(f'.{port}({expression})')
        text += '  gf180_analog_actor_ingress_v1 #(\n    '+',\n    '.join(f'.{k}({v})' for k,v in parameters.items())+f'\n  ) actor_{i:02d} (\n    '+',\n    '.join(connections)+'\n  );\n'
        records.append(dict(actor_index=i, actor=name, source=source, input_shape_chw=[cin,ih,iw],
                            output_shape_chw=[cout,oh,ow], parameters=parameters, weight_count=count,
                            weight_lane_stride=local_cin*kh*kw, output_lanes=cout//groups,
                            weight_array=actor['float_weight_array']))
    assert len(records) == 25
    OUT.mkdir(); CFG.mkdir(parents=True, exist_ok=True)
    rtl = ROOT/'asic/analog'/(NAME+'.sv'); rtl.write_text(text+'endmodule\n', encoding='utf-8')
    sdc = CFG/'constraint.sdc'
    sdc.write_text('create_clock -name clk -period 25 [get_ports clk]\nset_clock_uncertainty -setup 1 [get_clocks clk]\nset_clock_uncertainty -hold 0.2 [get_clocks clk]\nset_input_delay -max 1 -clock clk [all_inputs -no_clocks]\nset_output_delay 1 -clock clk [all_outputs]\nset_false_path -from [get_ports reset]\n', encoding='utf-8')
    hook = ROOT/'asic/analog/orfs/gf180_full25_packet_fabric_v1/nominal_via_resistance_hook_v5.tcl'
    config = CFG/'config.mk'
    config.write_text(f'export DESIGN_NAME = {NAME}\nexport DESIGN_NICKNAME = {NAME}\nexport PLATFORM = gf180\nexport VERILOG_FILES = '+ ' '.join(ws(p) for p in cells+[rtl])+f'\nexport SDC_FILE = {ws(sdc)}\nexport CORNER = TC\nexport TC_LIB_FILES = /OpenROAD-flow-scripts/flow/platforms/gf180/lib/gf180mcu_fd_sc_mcu9t5v0__tt_025C_3v30.lib.gz\nexport TC_VOLTAGE = 3.3\nexport TC_TEMPERATURE = 25c\nexport PRE_FINAL_REPORT_TCL = {ws(hook)}\nexport CORE_UTILIZATION = 30\nexport PLACE_DENSITY = 0.30\nexport CLOCK_PERIOD = 25\nexport SYNTH_HIERARCHICAL = 0\nexport ABC_AREA = 1\nexport NUM_CORES = 2\nexport SKIP_CTS_REPAIR_TIMING = 1\n', encoding='utf-8')
    scope = '25 real float-model convolution address services. One packet per event, preserve duplicates. A group acknowledgment requires every connected output-channel analog contribution completed. Native analog weight delivery, supply/clock integration and full-chip control remain unbound. No numeric digital state, accuracy or5ms acceptance.'
    status = dict(stage='physical_layout_prepared', design=NAME, variant=VARIANT,
                  checkpoint_sha256=SHA, actors=records, clock_constraint_ns=25, supply_v=3.3,
                  scope=scope, full_chip_layout_complete=False,
                  sha256={p.relative_to(ROOT).as_posix():sha(p) for p in paths+cells+[sim,rtl,sdc,config,hook,Path(__file__)]})
    if args.launch:
        assert subprocess.run(['docker','inspect',CONTAINER],capture_output=True).returncode != 0
        command = ['docker','run','--detach','--name',CONTAINER,'--network','none','--memory','4g','--memory-swap','4g','--cpus','2','--volume',f'{ROOT}:/workspace:ro']
        for kind in ['logs','objects','reports','results']:
            command += ['--volume',f'{BASE/"orfs"/kind}:/OpenROAD-flow-scripts/flow/{kind}']
        flow = f'DESIGN_CONFIG={ws(config)} FLOW_VARIANT={VARIANT}'
        command += ['--entrypoint','timeout','eventspikeseg:orfs-guarded','1800','bash','-lc',f'make -C /OpenROAD-flow-scripts/flow {flow} && make -C /OpenROAD-flow-scripts/flow {flow} do-generate_abstract']
        launch = subprocess.run(command,capture_output=True,text=True)
        assert launch.returncode == 0, launch.stderr
        status.update(stage='physical_layout_running',container=CONTAINER,container_id=launch.stdout.strip(),
                      started_utc=datetime.now(timezone.utc).isoformat(),command=command)
    save(OUT/'status.json',status)
    print(json.dumps(dict(stage=status['stage'], actors=len(records), total_weight_addresses=sum(r['weight_count'] for r in records), status=str(OUT/'status.json')),indent=2))

if __name__ == '__main__': main()
