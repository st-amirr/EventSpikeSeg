"""Join physical write-noise probes to explicitly ideal full-float sensitivity."""
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'results'
SHA='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'


def main():
    files=[]
    def load(name):
        p=OUT/name; files.append(p); return json.loads(p.read_text())
    mapping=load('gf180_write_noise_float_proxy_mapping.json')
    probes=[]
    for state in [0.9,1.65,2.4]:
        d=load(f'gf180_extracted_write_on_noise_ff85_state{state:g}v.json')
        if not d['simulation_completed']:
            raise RuntimeError('noise probe incomplete')
        probes.append({'state_v':state,'stationary_write_on_noise_uv_rms':d['noise_v_rms']['onoise_total']*1e6})
    replays=[]
    cases=[(0,'writeback_every_bin_g1_n274.199uv'),(1,'writeback_every_bin_g1_n274.199uv'),
           (0,'writeback_every_bin_g1000_piecewise6_ideal_n274.199uv'),(1,'writeback_every_bin_g1000_piecewise6_ideal_n274.199uv'),
           (0,'writeback_every_bin_g1_n274.199uv_channel_ranges'),(0,'none_g1_channel_ranges'),
           (0,'writeback_every_bin_g1000_piecewise6_ideal_n274.199uv_compute_n3uv'),
           (0,'writeback_every_bin_g1000_piecewise6_ideal_n274.199uv_compute_n30uv')]
    for record, suffix in cases:
        name=f'sky130_float_state_saturation_validation_{record}_all_neurons_full_{suffix}.json'
        d=load(name)
        if d['checkpoint_sha256']!=SHA or d['qat_or_quantized_reference_used'] is not False or d['scope']!='all-neurons' or not d['full_frame']:
            raise RuntimeError('replay contract mismatch')
        metrics=['final_fuse_spike_mismatch','segmentation_pixel_agreement_with_float','present_class_mean_iou','labeled_pixel_accuracy']
        replays.append({'source':name,'record_index':record,'encoding':d['encoding'],
                        'range_scope':d.get('range_scope','actor'),'noise_mode':d['noise_mode'],
                        'linear_compute_noise_sigma_uv':d.get('linear_compute_noise_sigma_uv_rms',0),
                        'baseline_present_class_mean_iou':d['baseline_present_class_mean_iou'],
                        'means':{metric:sum(row[metric] for row in d['trials'])/len(d['trials']) for metric in metrics},
                        'seeds':[row['seed'] for row in d['trials']]})
    kval=1.380649e-23;temp=358.15;states=30_976_000
    analytic=[]
    for proxy_uv in [3,30]:
        actual_uv=proxy_uv*1.5/0.9
        c=2*kval*temp/(actual_uv*1e-6)**2
        area_per_channel_um2=2*c/(4.4e-15)
        for service_ns in [100,1000]:
            channels=math.ceil(states*service_ns*1e-9/0.005)
            analytic.append({'linear_replay_sigma_uv':proxy_uv,'physical_differential_sigma_uv':actual_uv,
                             'independent_pair_equilibrium_ktc_cap_f_per_rail':c,
                             'shared_service_ns':service_ns,'ideal_parallel_channel_floor':channels,
                             'two_rail_gate_oxide_plate_area_per_channel_um2':area_per_channel_um2,
                             'repeated_plate_area_mm2':area_per_channel_um2*channels/1e6})
    report={'physical_state_accepted':False,'checkpoint_sha256':SHA,'qat_or_quantized_reference_used':False,
            'stationary_noise_probes':probes,'proxy_mapping':mapping,'full_frame_replays':replays,
            'conditional_reset_noise_and_service_estimates':analytic,
            'oxide_density_source':'https://gf180mcu-pdk.readthedocs.io/en/latest/analog/spice/elec_specs/elec_specs_5_3.html',
            'analytic_scope':'Conditional independent equilibrium kTC estimate at85C using published typical3.3V oxide density4.4fF/um2, not a measured shared compute block, finite-aperture noise, array floor or achieved service. Gate oxide plate only; contacts, routing, access, sensing and encoding absent.',
            'interpretation':'Actor-linear and channel-linear storage fail these illustrative every-bin writeback-noise probes. Ideal six-range companding is a research lead with near-baseline mean IoU on two frames, but many changed spikes/pixels; it does not qualify encoder hardware or accuracy.3uV pre-encoding computation noise remains near baseline on record0 while30uV degrades it; these are not measured acceptance thresholds. Physical compensated sensing/nonlinear encoding/restoration, noise/correlation, gate leakage, density and5ms service remain required.',
            'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    p=OUT/'gf180_original_float_write_noise_boundary.json';p.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'output':str(p),'replays':replays,'conditional_estimates':analytic},indent=2))


if __name__=='__main__':
    main()
