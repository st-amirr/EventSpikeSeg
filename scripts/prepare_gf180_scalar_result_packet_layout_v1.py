"""Launch bounded physical implementation of the scalar analog result boundary."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'
NAME = 'gf180_analog_scalar_result_packet_v1'
VARIANT = 'scalar_result_v1'
CONTAINER = 'ess-gf180-scalar-result-v1'

def main():
    report = BASE / 'assembly/scalar_result_packet_layout_v1/status.json'
    assert not report.exists(), 'Inspect existing job rather than restarting.'
    assert subprocess.run(['docker','inspect',CONTAINER],capture_output=True).returncode != 0
    simulation = BASE / 'results/scalar_result_packet_v1/simulation.json'
    result = json.loads(simulation.read_text())
    assert result['simulation_pass']
    source = ROOT / 'asic/analog' / (NAME+'.sv')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert result['sha256'][source.relative_to(ROOT).as_posix()] == digest
    directory = ROOT / 'asic/analog/orfs/gf180_scalar_result_packet_v1'
    directory.mkdir(parents=True,exist_ok=True)
    sdc = directory / 'constraint.sdc'
    sdc.write_text('create_clock -name clk -period 20.0 [get_ports clk]\n'
                   'set_clock_uncertainty -setup 1.0 [get_clocks clk]\n'
                   'set_clock_uncertainty -hold 0.2 [get_clocks clk]\n'
                   'set_input_delay -max 1.0 -clock clk [all_inputs -no_clocks]\n'
                   'set_output_delay 1.0 -clock clk [all_outputs]\n'
                   'set_false_path -from [get_ports reset]\n')
    config = directory / 'config.mk'
    config.write_text(f'export DESIGN_NAME = {NAME}\nexport DESIGN_NICKNAME = {NAME}\n'
                      f'export PLATFORM = gf180\nexport VERILOG_FILES = /workspace/{source.relative_to(ROOT).as_posix()}\n'
                      f'export SDC_FILE = /workspace/{sdc.relative_to(ROOT).as_posix()}\n'
                      'export CORE_UTILIZATION = 30\nexport PLACE_DENSITY = 0.30\n'
                      'export CLOCK_PERIOD = 20.0\nexport SYNTH_HIERARCHICAL = 0\n'
                      'export ABC_AREA = 1\nexport NUM_CORES = 1\nexport SKIP_CTS_REPAIR_TIMING = 1\n')
    command = ['docker','run','--detach','--name',CONTAINER,'--network','none',
               '--memory','4g','--memory-swap','4g','--cpus','1','--volume',f'{ROOT}:/workspace:ro']
    for kind in ['logs','objects','reports','results']:
        directory_out = BASE / 'orfs' / kind
        directory_out.mkdir(parents=True,exist_ok=True)
        command += ['--volume',f'{directory_out}:/OpenROAD-flow-scripts/flow/{kind}']
    args = f'DESIGN_CONFIG=/workspace/{config.relative_to(ROOT).as_posix()} FLOW_VARIANT={VARIANT}'
    command += ['--entrypoint','timeout','eventspikeseg:orfs-guarded','1800','bash','-lc',
                f'make -C /OpenROAD-flow-scripts/flow {args} && make -C /OpenROAD-flow-scripts/flow {args} do-generate_abstract']
    run = subprocess.run(command,capture_output=True,text=True)
    assert run.returncode == 0,run.stderr
    data = {'stage':'physical_layout_running','started_utc':datetime.now(timezone.utc).isoformat(),
            'container':CONTAINER,'container_id':run.stdout.strip(),'command':command,
            'design':NAME,'variant':VARIANT,'simulation_pass':True,
            'scope':'Reusable sampled scalar comparator result to sorted graph packet boundary; address, sample-valid and full-bin completion controller bindings remain required.',
            'full_chip_layout_complete':False,
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,config,sdc,simulation]}}
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'container':CONTAINER,'container_id':data['container_id'],'status':str(report)},indent=2))

if __name__ == '__main__': main()
