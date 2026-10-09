"""Join routed GF180 charge-reader geometry, transient and stationary-noise evidence."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'


def main():
    sources=[Path(__file__)]
    geometry_path=BASE/'layout/gf180_charge_read_frontend/qualification.json'
    geometry=json.loads(geometry_path.read_text());sources.append(geometry_path)
    rows=[]
    for corner,temp,count,offset in [('typical',27,0,750),('ff',85,0,750),('ss',0,0,750),('typical',27,0,2),('typical',27,1,750),('typical',27,4,750)]:
        suffix=f'_loadmim{count}' if count else ''
        rp=BASE/f'results/gf180_active_charge_read_{corner}_temp{temp}_cf100ff_offset{offset}mv_combinedfrontend{suffix}.json'
        report=json.loads(rp.read_text());sources.append(rp)
        if not report['simulation_completed']:
            raise ValueError(f'incomplete read: {rp}')
        low,high=report['rows']['low'],report['rows']['high']
        row={'corner':corner,'temperature_c':temp,'offset_mv':offset,'physical_load_mim_count':count,
             'signal_gain_from_held_span':abs((high['r900n']-low['r900n'])/(high['held']-low['held'])),
             'max_100ns_vs900ns_difference_uv':max(abs(r['100ns_to_900ns_output_difference_mv'])*1000 for r in report['rows'].values()),
             'max_500ns_vs900ns_difference_uv':max(abs(r['r500n']-r['r900n'])*1e6 for r in report['rows'].values()),
             'zero_read_output_v':report['rows']['zero']['r900n']}
        np=BASE/f'results/gf180_combined_reader_stationary_noise_{corner}_temp{temp}_read_frozenop{suffix}.json'
        if offset==750 and np.exists():
            noise=json.loads(np.read_text());sources.append(np)
            if not noise['simulation_completed'] or not noise['operating_point_in_range']:
                raise ValueError(f'invalid stationary noise: {np}')
            row['stationary_output_noise_uv_rms_10hz_100mhz']=noise['values']['onoise_total']*1e6
            row['linear_input_noise_uv_rms_proxy']=row['stationary_output_noise_uv_rms_10hz_100mhz']/row['signal_gain_from_held_span']
            row['same_phase_filters_not_physical_sampling']=noise.get('ideal_filter_probes_not_implemented_or_switched_noise',[])
        rows.append(row)
    xmin,ymin,xmax,ymax=geometry['bbox_um']
    result={'physical_state_accepted':False,'reader_geometry':geometry,
            'reader_footprint_um2':(xmax-xmin)*(ymax-ymin),'rows':rows,
            'conclusion':'Routed charge read works deterministically across screened MOS corners but is destructive, offset dependent and too noisy to qualify unencoded linear computation. Typical-only MIM corners. Physical output-load increase modestly reduces stationary noise and slows settling; not selected as accuracy solution.',
            'next_step':'Develop physically sampled/averaged or correlated sensing and analog restore/nonlinear encoding. Characterize phase noise/covariance, mismatch, qualified gate leakage, resistance extraction, original-float accuracy and complete5ms service before array/full-chip expansion.',
            'limitations':'Stationary noise is not sampled state error. Frozen read DC constraints are ideal AC-open bench inductors. Linear input referral uses deterministic secant gain, not nonlinear decoder noise. Filter probes assume same stationary process and do not establish pre/post phase covariance or sampling hardware. No physical encoder/restore, complete PLIF or chip acceptance.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    path=BASE/'results/gf180_combined_charge_reader_boundary.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'report':str(path),'reader_area_um2':result['reader_footprint_um2'],
                      'rows':[{k:v for k,v in row.items() if k!='same_phase_filters_not_physical_sampling'} for row in rows]},indent=2))


if __name__=='__main__':
    main()
