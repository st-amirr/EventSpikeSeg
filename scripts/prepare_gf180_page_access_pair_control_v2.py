"""Physically implement two independent categorical analog-page interlocks."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/page_access_pair_control_v2'
CFG=ROOT/'asic/analog/orfs/gf180_page_access_pair_control_v2'
NAME='gf180_analog_page_access_pair_control_v2';VARIANT='page_access_v2'
CONTAINER='ess-gf180-page-access-pair-control-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ws(p):return '/workspace/'+p.relative_to(ROOT).as_posix()

def main():
    assert not OUT.exists();OUT.mkdir();CFG.mkdir(parents=True,exist_ok=True)
    source=ROOT/'asic/analog/gf180_analog_page_access_control_v2.sv'
    sim=BASE/'results/page_access_control_v2/simulation.json';test=json.loads(sim.read_text())
    assert test['simulation_pass'] and test['sha256'][source.relative_to(ROOT).as_posix()]==sha(source)
    ports=[('input',1,'clk'),('input',1,'reset'),('input',1,'command_valid_i'),('output',1,'command_ready_o'),
           ('input',3,'command_i'),('input',7,'row_address_i'),('input',3,'column_i'),('input',1,'compute_done_i'),
           ('output',1,'done_o'),('input',1,'done_ready_i'),('output',1,'fault_o'),
           ('output',7,'page_address_o'),('output',8,'page_select_o'),('output',1,'page_read_o'),
           ('output',1,'page_read_enable_o'),('output',1,'page_write_o'),('output',1,'page_restore_o'),
           ('output',1,'page_restoreb_o'),('output',1,'external_initialize_o'),('output',1,'external_initializeb_o'),('output',1,'compute_init_o'),('output',1,'compute_initb_o'),
           ('output',1,'compute_write_o'),('output',1,'compute_writeb_o'),
           ('output',8,'capture_o'),('output',8,'captureb_o'),('output',8,'captured_columns_o'),('output',1,'busy_o')]
    declarations=[]
    for direction,width,name in ports:
        size=width if name in ['clk','reset'] else width*2
        declarations.append(f'  {direction} wire '+(f'[{size-1}:0] ' if size>1 else '')+name)
    text=f'module {NAME} (\n'+',\n'.join(declarations)+'\n);\n'
    for i in range(2):
        connections=[]
        for _,width,name in ports:
            value=name if name in ['clk','reset'] else (f'{name}[{i}]' if width==1 else f'{name}[{i*width} +: {width}]')
            connections.append(f'.{name}({value})')
        text+=f'  gf180_analog_page_access_control_v2 lane_{i} (\n    '+',\n    '.join(connections)+'\n  );\n'
    rtl=ROOT/'asic/analog'/(NAME+'.sv');rtl.write_text(text+'endmodule\n')
    sdc=CFG/'constraint.sdc';sdc.write_text('create_clock -name clk -period 25 [get_ports clk]\nset_clock_uncertainty -setup 1 [get_clocks clk]\nset_clock_uncertainty -hold 0.2 [get_clocks clk]\nset_input_delay -max 1 -clock clk [all_inputs -no_clocks]\nset_output_delay 1 -clock clk [all_outputs]\nset_false_path -from [get_ports reset]\n')
    hook=ROOT/'asic/analog/orfs/gf180_full25_packet_fabric_v1/nominal_via_resistance_hook_v5.tcl'
    config=CFG/'config.mk';config.write_text(f'export DESIGN_NAME = {NAME}\nexport DESIGN_NICKNAME = {NAME}\nexport PLATFORM = gf180\nexport VERILOG_FILES = {ws(source)} {ws(rtl)}\nexport SDC_FILE = {ws(sdc)}\nexport CORNER = TC\nexport TC_LIB_FILES = /OpenROAD-flow-scripts/flow/platforms/gf180/lib/gf180mcu_fd_sc_mcu9t5v0__tt_025C_3v30.lib.gz\nexport TC_VOLTAGE = 3.3\nexport TC_TEMPERATURE = 25c\nexport PRE_FINAL_REPORT_TCL = {ws(hook)}\nexport CORE_UTILIZATION = 30\nexport PLACE_DENSITY = 0.30\nexport CLOCK_PERIOD = 25\nexport SYNTH_HIERARCHICAL = 0\nexport ABC_AREA = 1\nexport NUM_CORES = 2\nexport SKIP_CTS_REPAIR_TIMING = 1\nexport SKIP_ANTENNA_REPAIR_POST_DRT = 1\n')
    assert subprocess.run(['docker','inspect',CONTAINER],capture_output=True).returncode!=0
    command=['docker','run','--detach','--name',CONTAINER,'--network','none','--memory','4g','--memory-swap','4g','--cpus','2','--volume',f'{ROOT}:/workspace:ro']
    for kind in ['logs','objects','reports','results']:
        command+=['--volume',f'{BASE/"orfs"/kind}:/OpenROAD-flow-scripts/flow/{kind}']
    flow=f'DESIGN_CONFIG={ws(config)} FLOW_VARIANT={VARIANT}'
    command+=['--entrypoint','timeout','eventspikeseg:orfs-guarded','1800','bash','-lc',f'make -C /OpenROAD-flow-scripts/flow {flow} && make -C /OpenROAD-flow-scripts/flow {flow} do-generate_abstract']
    launch=subprocess.run(command,capture_output=True,text=True);assert launch.returncode==0,launch.stderr
    status=dict(stage='physical_layout_running',container=CONTAINER,container_id=launch.stdout.strip(),
                started_utc=datetime.now(timezone.utc).isoformat(),command=command,design=NAME,variant=VARIANT,
                supply_v=3.3,clock_constraint_ns=25,lane_count=2,
                scope='Two independent categorical access interlocks with physical zero-state initialization from EXTERNAL_INIT_DATA tied to COMPUTE_REFERENCE; conservative inherited bench-like duration defaults require native loaded timing qualification. At40MHz defaults read/restore takes20.25us and capture10.2us; serial1024slot sweep exceeds5ms. These defaults are not a selected real-time schedule. Native parallel page binding, compute completion/phase producers and weight distribution remain required.',
                full_chip_layout_complete=False,full_5ms_population_service_accepted=False,
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),source,rtl,sim,sdc,config,hook]})
    (OUT/'status.json').write_text(json.dumps(status,indent=2)+'\n')
    print(json.dumps({k:status[k] for k in ['container','container_id','lane_count','stage']},indent=2))

if __name__=='__main__':main()
