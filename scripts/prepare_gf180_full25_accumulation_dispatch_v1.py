"""Prepare/route 25 actor-local categorical destination dispatchers."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,subprocess
from assemble_gf180_accumulation_fabric_ingress_v1 import sha

ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_accumulation_dispatch_v1'
CFG=ROOT/'asic/analog/orfs/gf180_full25_accumulation_dispatch_v1'
NAME='gf180_analog_full25_accumulation_dispatch_v1';VARIANT='accumulation_dispatch_v1'
CONTAINER='ess-gf180-full25-accumulation-dispatch-v1'
PORTS=[('input',1,'clk'),('input',1,'reset'),('input',1,'group_valid_i'),('output',1,'group_ready_o'),
       ('input',8,'channel_base_i'),('input',8,'lane_count_i'),('input',10,'x_i'),('input',10,'y_i'),
       ('input',24,'bin_tag_i'),('output',1,'group_settled_done_o'),('output',1,'service_valid_o'),
       ('input',1,'service_ready_i'),('input',1,'service_done_i'),('output',7,'channel_o'),
       ('output',10,'x_o'),('output',9,'y_o'),('output',8,'contribution_lane_o'),
       ('output',24,'service_bin_tag_o'),('output',20,'linear_bank_o'),('output',2,'service_kind_o'),
       ('output',22,'forest_address_o'),('output',7,'local_page_address_o'),
       ('output',1,'local_bank_select_o'),('output',3,'local_row_o'),('output',8,'column_select_o'),
       ('output',1,'fault_o'),('output',1,'busy_o')]


def ws(p):return '/workspace/'+p.relative_to(ROOT).as_posix()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--launch',action='store_true');args=ap.parse_args()
    source=ROOT/'asic/analog/gf180_analog_accumulation_dispatch_v1.sv'
    rtl=ROOT/'asic/analog'/(NAME+'.sv')
    prepared_path=OUT/'prepared.json'
    if not prepared_path.exists():
        assert not OUT.exists();OUT.mkdir(parents=True);CFG.mkdir(parents=True)
        population=BASE/'assembly/full25actor_original_float_population_manifest_v1.json'
        mapping=BASE/'assembly/full_population_page_access_v1/address_assembly_specification_v1.json'
        p=json.loads(population.read_text());m=json.loads(mapping.read_text())
        assert p['checkpoint_sha256']==m['checkpoint_sha256']=='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
        planes={v['actor']:v for v in m['planes'] if v['state_kind']=='membrane'}
        text='// Original-float topology; digital categorical destinations only.\n'
        declarations=[]
        for direction,width,name in PORTS:
            total=width if name in ['clk','reset'] else 25*width
            declarations.append(f'  {direction} wire '+(f'[{total-1}:0] ' if total>1 else '')+name)
        text+=f'module {NAME} (\n'+',\n'.join(declarations)+'\n);\n';actors=[]
        for i,a in enumerate(p['actors']):
            plane=planes[a['actor']];holes=plane['excluded_linear_banks']
            assert holes in [list(range(19)),list(range(9))+list(range(10,20))]
            c,h,w=a['channels'],a['height'],a['width'];gapped=int(holes[9]==10)
            assert plane['shape_chw']==[c,h,w]
            connections=[]
            for _,width,name in PORTS:
                value=name if name in ['clk','reset'] else f'{name}[{i}]' if width==1 else f'{name}[{i*width} +: {width}]'
                connections.append(f'.{name}({value})')
            text+=f'  gf180_analog_accumulation_dispatch_v1 #(.CHANNELS({c}),.HEIGHT({h}),.WIDTH({w}),.GAPPED_LOCAL_BANKS({gapped})) actor_{i:02d} (\n    '+',\n    '.join(connections)+'\n  );\n'
            actors.append(dict(actor_index=i,actor=a['actor'],shape_chw=[c,h,w],gapped_local_banks=gapped,excluded_linear_banks=holes))
        assert len(actors)==25 and sum(c*h*w for c,h,w in [a['shape_chw'] for a in actors])==30976000
        assert not rtl.exists();rtl.write_text(text+'endmodule\n',encoding='utf-8')
        sdc=CFG/'constraint.sdc';sdc.write_text('create_clock -name clk -period 25 [get_ports clk]\nset_clock_uncertainty -setup 1 [get_clocks clk]\nset_clock_uncertainty -hold 0.2 [get_clocks clk]\nset_input_delay -max 1 -clock clk [all_inputs -no_clocks]\nset_output_delay 1 -clock clk [all_outputs]\nset_false_path -from [get_ports reset]\n')
        hook=ROOT/'asic/analog/orfs/gf180_full25_packet_fabric_v1/nominal_via_resistance_hook_v5.tcl'
        config=CFG/'config.mk';config.write_text(f'export DESIGN_NAME = {NAME}\nexport DESIGN_NICKNAME = {NAME}\nexport PLATFORM = gf180\nexport VERILOG_FILES = {ws(source)} {ws(rtl)}\nexport SDC_FILE = {ws(sdc)}\nexport CORNER = TC\nexport TC_LIB_FILES = /OpenROAD-flow-scripts/flow/platforms/gf180/lib/gf180mcu_fd_sc_mcu9t5v0__tt_025C_3v30.lib.gz\nexport TC_VOLTAGE = 3.3\nexport TC_TEMPERATURE = 25c\nexport PRE_FINAL_REPORT_TCL = {ws(hook)}\nexport CORE_UTILIZATION = 30\nexport PLACE_DENSITY = 0.30\nexport CLOCK_PERIOD = 25\nexport SYNTH_HIERARCHICAL = 0\nexport ABC_AREA = 1\nexport NUM_CORES = 2\nexport SKIP_CTS_REPAIR_TIMING = 1\nexport SKIP_ANTENNA_REPAIR_POST_DRT = 1\n')
        prepared=dict(stage='prepared',actors=actors,ports=PORTS,checkpoint_sha256=p['checkpoint_sha256'],
                      scope='One reusable categorical destination dispatcher per actor. No numerical membrane/weight storage. Services complete only after external actual analog accumulation/writeback. Serial group scheduling is not a selected 5ms population schedule.',
                      sha256={f.relative_to(ROOT).as_posix():sha(f) for f in [Path(__file__),source,rtl,population,mapping,sdc,config,hook]})
        prepared_path.write_text(json.dumps(prepared,indent=2)+'\n')
    prepared=json.loads(prepared_path.read_text())
    for p,digest in prepared['sha256'].items():assert sha(ROOT/p)==digest,p
    if not args.launch:
        print(json.dumps({'stage':'prepared','actors':len(prepared['actors']),'rtl':rtl.relative_to(ROOT).as_posix()}));return
    assert not (OUT/'status.json').exists(),'Do not restart an attempted job.'
    sim=BASE/'results/accumulation_dispatch_v1/simulation.json';test=json.loads(sim.read_text())
    assert test['simulation_pass'] and test['sha256'][source.relative_to(ROOT).as_posix()]==sha(source)
    assert test['sha256'][rtl.relative_to(ROOT).as_posix()]==sha(rtl)
    assert subprocess.run(['docker','inspect',CONTAINER],capture_output=True).returncode!=0
    command=['docker','run','--detach','--name',CONTAINER,'--network','none','--memory','4g','--memory-swap','4g','--cpus','2','--volume',f'{ROOT}:/workspace:ro']
    for kind in ['logs','objects','reports','results']:command+=['--volume',f'{BASE/"orfs"/kind}:/OpenROAD-flow-scripts/flow/{kind}']
    flow=f'DESIGN_CONFIG={ws(CFG/"config.mk")} FLOW_VARIANT={VARIANT}'
    command+=['--entrypoint','timeout','eventspikeseg:orfs-guarded','1800','bash','-lc',f'make -C /OpenROAD-flow-scripts/flow {flow} && make -C /OpenROAD-flow-scripts/flow {flow} do-generate_abstract']
    launch=subprocess.run(command,capture_output=True,text=True);assert launch.returncode==0,launch.stderr
    status=dict(stage='physical_layout_running',container=CONTAINER,container_id=launch.stdout.strip(),
                design=NAME,variant=VARIANT,supply_v=3.3,clock_constraint_ns=25,actors=prepared['actors'],
                command=command,started_utc=datetime.now(timezone.utc).isoformat(),
                scope=prepared['scope'],full_chip_layout_complete=False,accumulation_5ms_accepted=False,
                sha256={**prepared['sha256'],sim.relative_to(ROOT).as_posix():sha(sim)})
    (OUT/'status.json').write_text(json.dumps(status,indent=2)+'\n')
    print(json.dumps({'stage':status['stage'],'container':CONTAINER,'container_id':status['container_id']}))


if __name__=='__main__':main()
