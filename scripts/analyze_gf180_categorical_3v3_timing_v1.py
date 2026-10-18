"""Analyze unchanged routed geometry using the available 3.3V cell library."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'artifacts/analog_asic'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('job',choices=['full25_event_graph_layout_v1','scalar_result_packet_layout_v1'])
    parser.add_argument('--attempt',type=int,default=1)
    parser.add_argument('--summarize-existing',action='store_true')
    args=parser.parse_args()
    directory=BASE/'assembly'/args.job
    status=json.loads((directory/'status.json').read_text())
    assert status['stage']=='physical_macro_completed'
    out=directory/f'timing_3v3_v{args.attempt}'
    if not args.summarize_existing:
        assert not out.exists(), 'Preserve the previous timing evidence.'
        out.mkdir()
    results=BASE/'orfs/results/gf180'/status['design']/status['variant']
    odb, sdc, spef = [results/n for n in ['6_final.odb','6_final.sdc','6_final.spef']]
    lib='/OpenROAD-flow-scripts/flow/platforms/gf180/lib/gf180mcu_fd_sc_mcu9t5v0__tt_025C_3v30.lib.gz'
    path=lambda p:'/workspace/'+p.relative_to(ROOT).as_posix()
    tcl=out/'analyze.tcl'
    if not args.summarize_existing:
        tcl.write_text(f'read_liberty {lib}\nread_db {path(odb)}\nread_sdc {path(sdc)}\n'
                   f'read_spef {path(spef)}\n'
                   'puts "NOMINAL_3V3_TIMING_BEGIN"\n'
                   'report_worst_slack -max\nreport_worst_slack -min\nreport_tns\n'
                   'report_checks -path_delay max -format full_clock_expanded -group_path_count 3\n'
                   'report_check_types -max_slew -max_capacitance -violators\nreport_power\n'
                   'puts "NOMINAL_3V3_TIMING_END"\nexit\n')
    cmd=['docker','run','--rm','--network','none','--memory','4g','--cpus','1',
         '--volume',f'{ROOT}:/workspace:ro','--entrypoint','bash','eventspikeseg:orfs-guarded',
         '-lc',f'sha256sum {lib}; /OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad -exit {path(tcl)}']
    if args.summarize_existing:
        log=(out/'timing.log').read_text()
        returncode=json.loads((out/'summary.json').read_text())['returncode']
    else:
        run=subprocess.run(cmd,capture_output=True,text=True,timeout=240)
        log=run.stdout+run.stderr
        returncode=run.returncode
        (out/'timing.log').write_text(log)
    slacks=dict((kind,float(value)) for kind,value in re.findall(r'worst slack\s+(max|min)\s+(-?[\d.]+)',log))
    passed=returncode==0 and 'NOMINAL_3V3_TIMING_END' in log and '[ERROR' not in log and len(slacks)==2
    report={'analysis_completed':passed,'returncode':returncode,'voltage_v':3.3,
            'process_corner':'typical','temperature_c':25,'library':lib,
            'reported_worst_slacks_ns':slacks,
            'geometry_unchanged':True,'scope':'Nominal STA on the existing routed ODB/SPEF at 3.3V. Does not prove loaded analog input levels, PVT closure, metastability or full-chip service.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [odb,sdc,spef,tcl]}}
    (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if not passed: raise SystemExit(returncode or 1)

if __name__=='__main__':main()
