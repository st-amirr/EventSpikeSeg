"""Corrected extracted OTA unity-follower bringup with explicit schematic peripherals."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'artifacts/analog_asic'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bias-ua',type=int,choices=[1,5],default=1)
    parser.add_argument('--comp-size-um',type=int,choices=[7,22],default=7)
    args = parser.parse_args()
    cell = 'gf180_shared_ota_core_pmos_input_fullroute'
    directory = BASE/'layout'/cell
    qp = directory/'qualification.json'
    q = json.loads(qp.read_text())
    if q['magic_drc_count'] or q['gds_roundtrip_drc_count'] or not q['gds_roundtrip_lvs_unique'] or q['mos_count'] != 7:
        raise ValueError('Corrected OTA actual GDS required')
    sources = {qp,Path(__file__)}
    for name,expected in q['sha256'].items():
        p = directory/name
        if digest(p) != expected:
            raise ValueError('OTA view changed')
        sources.add(p)
    for key in ['input_sha256','gds_roundtrip_sha256']:
        for name,expected in q[key].items():
            p = ROOT/name
            if digest(p) != expected:
                raise ValueError('OTA input/readback changed')
            sources.add(p)
    modeldir = BASE/'pdk/gf180_primitive_source/models/ngspice'
    sources.update(modeldir.rglob('*.spice'))
    prefix = '/workspace/'+modeldir.relative_to(ROOT).as_posix()
    source_sha = digest(Path(__file__))
    stem = f'gf180_fullroute_ota_bias{args.bias_ua}ua_comp{args.comp_size_um}um_src{source_sha[:12]}'
    snapshot = BASE/'tools/source_snapshots'/(stem+'.py')
    if not snapshot.exists():
        snapshot.write_bytes(Path(__file__).read_bytes())
    sources.remove(Path(__file__))
    sources.add(snapshot)
    deck = BASE/'benches'/(stem+'.spice')
    lines = ['Corrected extracted OTA unity follower with schematic reference/compensation',
             f'.include {prefix}/design.spice','.param sw_stat_global=0 sw_stat_mismatch=0',
             f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',
             '.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',
             *(directory/(cell+'_cap.spice')).read_text().splitlines(),
             'Vdd vdd 0 3.3',f'Ireference bias 0 {args.bias_ua}u',
             'Xreference bias bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u',
             'Vin input 0 PWL(0 1.65 1u 1.65 1.02u 1.55 3u 1.55 3.02u 1.75 5u 1.75 5.02u 1.65 8u 1.65)',
             f'Xota input output output vdd 0 bias cmp {cell}',
             f'Xcomp cmp output cap_mim_2f0_m4m5_noshield c_length={args.comp_size_um}u c_width={args.comp_size_um}u',
             'Cexternal_load output 0 50f','.control','set numdgt=15','op','print v(bias) v(output) i(vdd)',
             'dc Vin 0.3 3.0 0.3']
    for i in range(10):
        value = .3*(i+1)
        lines.append(f'meas dc dc_{i} find v(output) at={value:.12g}')
    lines += ['reset','tran 5n 8u 0 5n','let error=v(output)-v(input)','let power=-v(vdd)*i(vdd)']
    for i,(begin,end) in enumerate([(2.5e-6,2.9e-6),(4.5e-6,4.9e-6),(7.0e-6,7.5e-6)]):
        lines += [f'meas tran error_{i} avg error from={begin:.12g} to={end:.12g}',
                  f'meas tran ripple_{i} pp v(output) from={begin:.12g} to={end:.12g}']
    lines += ['meas tran energy integ power from=0 to=8u','quit','.endc','.end']
    deck.write_text('\n'.join(lines)+'\n')
    sources.add(deck)
    result = subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2',
                             '--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout',
                             'eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log = result.stdout+result.stderr
    lp = BASE/'results'/(stem+'.log')
    lp.write_text(log)
    sources.add(lp)
    values = {name:float(value) for name,value in re.findall(r'(?m)^(dc_\d+|error_\d+|ripple_\d+|energy)\s*=\s*([-+0-9.eE]+)',log)}
    complete = result.returncode == 0 and len(values) == 17 and 'timestep too small' not in log.lower()
    report = {'simulation_completed':complete,'settings':vars(args),'measurements':values,
              'dc_voltage_error_mv':{f'{.3*(i+1):.1f}':(values[f'dc_{i}']-.3*(i+1))*1000 for i in range(10)} if complete else {},
              'source_snapshot':snapshot.relative_to(ROOT).as_posix(),
              'read_restore_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,
              'scope':'Actual corrected OTA extraction only. Diode-connected PF bias reference is schematic native model geometry driven by an ideal current source; compensation is a native MIM model with specified dimensions, no routed compensation/reference assembly. External50fF load is ideal. Nominal DC and unity-feedback small-step transient, no actual floating sampler load, differential readout, sampled noise, PVT/mismatch, RPEX, model accuracy or5ms population service acceptance. Devices/model cards unchanged.',
              'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
    target = BASE/'results'/(stem+'.json')
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'report':str(target),'simulation_completed':complete,'dc_voltage_error_mv':report['dc_voltage_error_mv'],'measurements':values},indent=2))
    if not complete:
        raise RuntimeError(log[-2000:])


if __name__ == '__main__':
    main()
