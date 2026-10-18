"""Freeze actual float-population dimensions and route categorical scan controls."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_decision_control_v3';CFG=ROOT/'asic/analog/orfs/gf180_full25_decision_control_v3'
NAME='gf180_analog_full25_decision_control_v3';VARIANT='decision_control_v3';CONTAINER='ess-gf180-full25-decision-control-v3'
SHA='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ws(p):return '/workspace/'+p.relative_to(ROOT).as_posix()

def main():
    assert not OUT.exists();assert subprocess.run(['docker','inspect',CONTAINER],capture_output=True).returncode!=0
    population=BASE/'assembly/full25actor_original_float_population_manifest_v1.json'
    mapping=BASE/'assembly/full_population_page_access_v1/address_assembly_specification_v1.json'
    reference=BASE/'model_reference/eventspikeseg140k_float_reference.json'
    sim=BASE/'results/decision_scan_v3/simulation.json';cell=ROOT/'asic/analog/gf180_analog_decision_scan_v3.sv'
    p=json.loads(population.read_text());a=json.loads(mapping.read_text());ref=json.loads(reference.read_text());test=json.loads(sim.read_text())
    carry=BASE/'results/decision_bank_carry_v3/simulation.json';carry_test=json.loads(carry.read_text());assert carry_test['simulation_pass'] and carry_test['boundary_cases']==3600 and carry_test['sha256'][cell.relative_to(ROOT).as_posix()]==sha(cell)
    assert p['checkpoint_sha256']==a['checkpoint_sha256']==ref['checkpoint_sha256']==SHA
    assert len(p['actors'])==25 and test['simulation_pass'] and test['sha256'][cell.relative_to(ROOT).as_posix()]==sha(cell)
    mem={plane['actor']:plane for plane in a['planes'] if plane['state_kind']=='membrane'}
    for actor in p['actors']:
        plane=mem[actor['actor']]
        assert plane['shape_chw']==[actor['channels'],actor['height'],actor['width']]
        holes=plane['excluded_linear_banks']
        assert holes in [list(range(19)),list(range(9))+list(range(10,20))]
        ny,nx=plane['bank_grid_yx']
        physical=[e['channel']*ny*nx+e['bank_y']*nx+e['bank_x'] for e in plane['existing_service_exceptions']]
        assert physical==holes and len(physical)==19
    for plane in a['planes']:
        if plane['state_kind']!='membrane':assert plane['excluded_linear_banks']==[]
    OUT.mkdir();CFG.mkdir(parents=True,exist_ok=True)
    ports=[('input',1,'clk'),('input',1,'reset'),('input',25,'start_i'),('output',25,'start_ready_o'),
           ('input',600,'bin_tag_i'),('input',25,'service_ready_i'),('input',25,'service_done_i'),
           ('output',25,'service_valid_o'),('output',500,'parameter_bank_address_o'),
           ('output',50,'service_kind_o'),('output',550,'forest_address_o'),('output',550,'auxiliary_forest_address_o'),
           ('output',175,'local_page_address_o'),('output',25,'local_bank_select_o'),
           ('output',75,'local_row_o'),('output',200,'column_select_o'),
           ('output',25,'result_valid_o'),('input',25,'result_ready_i'),('output',650,'result_address_o'),
           ('output',600,'result_bin_tag_o'),('output',25,'result_last_o'),('output',25,'result_hold_o'),
           ('output',25,'busy_o'),('output',25,'done_o'),('input',25,'done_ready_i')]
    text='// Original-float actor dimensions; categorical control only, no numerical digital state.\n'
    text+=f'module {NAME} (\n'+',\n'.join(f'  {direction} wire '+(f'[{width-1}:0] ' if width>1 else '')+name for direction,width,name in ports)+'\n);\n'
    records=[]
    widths={'start_i':1,'start_ready_o':1,'bin_tag_i':24,'service_valid_o':1,'service_ready_i':1,'service_done_i':1,
            'linear_bank_o':20,'service_kind_o':2,'forest_address_o':22,'auxiliary_forest_address_o':22,
            'local_page_address_o':7,'local_bank_select_o':1,'local_row_o':3,'column_select_o':8,
            'result_valid_o':1,'result_ready_i':1,'result_address_o':26,'result_bin_tag_o':24,'result_last_o':1,
            'result_hold_o':1,'busy_o':1,'done_o':1,'done_ready_i':1}
    for i,actor in enumerate(p['actors']):
        c,h,w=actor['channels'],actor['height'],actor['width']
        holes=mem[actor['actor']]['excluded_linear_banks']
        local_literal=f"380'h{sum(v<<(20*i) for i,v in enumerate(holes)):095x}"
        connections=['.clk(clk)','.reset(reset)','.channel_o()','.y_o()','.x_o()']
        for port,width in widths.items():
            top='parameter_bank_address_o' if port=='linear_bank_o' else port
            expression=f'{top}[{i}]' if width==1 else f'{top}[{i*width} +: {width}]'
            connections.append(f'.{port}({expression})')
        text+=f'  gf180_analog_decision_scan_v3 #(.CHANNELS({c}),.HEIGHT({h}),.WIDTH({w}),.LOCAL_BANKS({local_literal})) actor_{i:02d} (\n    '+',\n    '.join(connections)+'\n  );\n'
        records.append({'actor_index':i,'actor':actor['actor'],'shape_chw':[c,h,w],'valid_neurons':c*h*w,'membrane_exceptions':holes,'address_bits':mem[actor['actor']]['categorical_row_bank_address_bits']})
    text+='endmodule\n';rtl=ROOT/'asic/analog'/(NAME+'.sv');rtl.write_text(text)
    sdc=CFG/'constraint.sdc';sdc.write_text('create_clock -name clk -period 25 [get_ports clk]\nset_clock_uncertainty -setup 1 [get_clocks clk]\nset_clock_uncertainty -hold 0.2 [get_clocks clk]\nset_input_delay -max 1 -clock clk [all_inputs -no_clocks]\nset_output_delay 1 -clock clk [all_outputs]\nset_false_path -from [get_ports reset]\n')
    hook=ROOT/'asic/analog/orfs/gf180_full25_packet_fabric_v1/nominal_via_resistance_hook_v5.tcl'
    config=CFG/'config.mk';config.write_text(f'export DESIGN_NAME = {NAME}\nexport DESIGN_NICKNAME = {NAME}\nexport PLATFORM = gf180\nexport VERILOG_FILES = {ws(cell)} {ws(rtl)}\nexport SDC_FILE = {ws(sdc)}\nexport CORNER = TC\nexport TC_LIB_FILES = /OpenROAD-flow-scripts/flow/platforms/gf180/lib/gf180mcu_fd_sc_mcu9t5v0__tt_025C_3v30.lib.gz\nexport TC_VOLTAGE = 3.3\nexport TC_TEMPERATURE = 25c\nexport PRE_FINAL_REPORT_TCL = {ws(hook)}\nexport CORE_UTILIZATION = 30\nexport PLACE_DENSITY = 0.30\nexport CLOCK_PERIOD = 25\nexport SYNTH_HIERARCHICAL = 0\nexport ABC_AREA = 1\nexport NUM_CORES = 2\nexport SKIP_CTS_REPAIR_TIMING = 1\nexport SKIP_ANTENNA_REPAIR_POST_DRT = 1\n')
    command=['docker','run','--detach','--name',CONTAINER,'--network','none','--memory','4g','--memory-swap','4g','--cpus','2','--volume',f'{ROOT}:/workspace:ro']
    for kind in ['logs','objects','reports','results']:command+=['--volume',f'{BASE/"orfs"/kind}:/OpenROAD-flow-scripts/flow/{kind}']
    args=f'DESIGN_CONFIG={ws(config)} FLOW_VARIANT={VARIANT}'
    command+=['--entrypoint','timeout','eventspikeseg:orfs-guarded','1800','bash','-lc',f'make -C /OpenROAD-flow-scripts/flow {args} && make -C /OpenROAD-flow-scripts/flow {args} do-generate_abstract']
    launch=subprocess.run(command,capture_output=True,text=True);assert launch.returncode==0,launch.stderr
    status={'stage':'physical_layout_running','container':CONTAINER,'container_id':launch.stdout.strip(),'started_utc':datetime.now(timezone.utc).isoformat(),'command':command,'design':NAME,'variant':VARIANT,'supply_v':3.3,'clock_constraint_ns':25,'checkpoint_sha256':SHA,'actors':records,'total_valid_neurons':sum(r['valid_neurons'] for r in records),'scope':'25 actual population decision/address scans. No numerical digital state. Starts require upstream accumulation/RMS readiness; native analog service-request/settled-done, hold and physical controller-to-fabric/storage bindings remain required. No5ms/accuracy acceptance.','full_chip_layout_complete':False,'sha256':{q.relative_to(ROOT).as_posix():sha(q) for q in [Path(__file__),population,mapping,reference,sim,carry,cell,rtl,sdc,hook,config]}}
    assert status['total_valid_neurons']==30976000
    (OUT/'status.json').write_text(json.dumps(status,indent=2)+'\n')
    print(json.dumps({'container':CONTAINER,'container_id':status['container_id'],'actor_count':25,'valid_neurons':status['total_valid_neurons'],'status':str(OUT/'status.json')},indent=2))

if __name__=='__main__':main()
