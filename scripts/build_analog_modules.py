"""Generate bounded analog module benches and a machine-readable design contract.

The .yaml contract is JSON syntax (valid YAML 1.2), requiring no extra packages.
"""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/analog_asic'


def main():
    benches = OUT / 'benches'
    benches.mkdir(parents=True, exist_ok=True)
    pdk = OUT / 'pdk/sky130_fd_pr'
    revision = subprocess.check_output(['git', '-C', str(pdk), 'rev-parse', 'HEAD'], text=True).strip()
    includes = ['.option scale=1u',
                '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"']
    for device in ('nfet_01v8', 'pfet_01v8'):
        base = f'../pdk/sky130_fd_pr/cells/{device}/sky130_fd_pr__{device}'
        includes += [f'.include "{base}__tt.corner.spice"',
                     f'.include "{base}__mismatch.corner.spice"']
    (benches / 'models_tt.spice').write_text('\n'.join(includes)+'\n')
    common = '.include "../../../asic/analog/modules.spice"\n'
    transistor = '''SKY130 capacitor sample and hold smoke; not a PLIF validation
.include "models_tt.spice"
'''+common+'''
Vdd vdd 0 1.8
Vcm vcm 0 0.9
Vin input 0 PWL(0 0.9 1u 0.9 1.01u 1.1 3u 1.1 3.01u 0.7 6u 0.7)
Vclk sample 0 PULSE(0 1.8 0.5u 1n 1n 1.5u 5u)
Xinv sample sample_b vdd 0 inv
Xhold input state sample sample_b vdd 0 vcm membrane_hold
.control
set wr_singlescale
set wr_vecnames
tran 2n 5u
wrdata ../results/membrane_hold.dat v(input) v(state) v(sample) i(Vdd) i(Vin)
quit
.endc
.end
'''
    (benches / 'membrane_hold.cir').write_text(transistor)
    behavioral = '''Behavioral mechanism and readout combinational sweep
'''+common+'''
Vage age 0 PWL(0 -1 1u 0 11u 10 12u 11)
Vamp amplitude 0 0.2
Vc candidate 0 0.6
Vres residual 0 0.3
Vany any 0 1
Vown own 0 0
Xtri age amplitude penalty adaptation_triangle duration=5
Xsq candidate penalty square energy_square
Xroot square rms energy_root
Xthr candidate penalty spike residual_thr threshold_reset theta=0.45
Xinh residual rms any own inhibited peer_inhibition strength=0.2
V0 c0 0 0.1
V1 c1 0 0.7
V2 c2 0 0.7
V3 c3 0 -0.2
V4 c4 0 0
V5 c5 0 0.3
Xarg c0 c1 c2 c3 c4 c5 winner argmax6
.control
set wr_singlescale
set wr_vecnames
tran 20n 12u
wrdata ../results/mechanisms.dat v(age) v(penalty) v(square) v(rms) v(spike) v(residual_thr) v(inhibited) v(winner)
quit
.endc
.end
'''
    (benches / 'mechanisms.cir').write_text(behavioral)
    (benches / 'comparator.cir').write_text('''SKY130 threshold comparator prototype
.include "models_tt.spice"
'''+common+'''
Vdd vdd 0 1.8
Vbias bias 0 0.65
Vref reference 0 0.9
Vin input 0 PWL(0 0.8 1u 0.8 1.1u 1.0 3u 1.0 3.1u 0.8 5u 0.8)
Xcmp input reference output bias vdd 0 comparator
Cload output 0 10f
.control
set wr_singlescale
set wr_vecnames
tran 2n 5u
wrdata ../results/comparator.dat v(input) v(output) i(Vdd)
quit
.endc
.end
''')
    (benches / 'synapse_readout.cir').write_text('''Signed charge injection, readout reset and sampled leak interfaces
'''+common+'''
Vcm vcm 0 0.9
Vp pulse 0 PULSE(0 1 1u 1n 1n 1u 10u)
Vn npulse 0 PULSE(0 1 3u 1n 1n 1u 10u)
Xpos pulse membrane vcm signed_synapse w=0.5
Xneg npulse membrane vcm signed_synapse w=-0.25
Cmem membrane vcm 1p ic=0
Rdc membrane vcm 1e15
Vcurrent input_current 0 PWL(0 0 1u 0 1.001u 100n 2u 100n 2.001u 0 6u 0)
Vreset reset 0 PWL(0 1 0.5u 1 0.501u 0 4.5u 0 4.501u 1 6u 1)
Xread input_current reset readout vcm class_integrator
Vcommit committed 0 0.5
Xleak committed target vcm sampled_leak beta=0.8
.control
set wr_singlescale
set wr_vecnames
tran 2n 6u uic
wrdata ../results/synapse_readout.dat v(membrane) v(readout) v(target)
quit
.endc
.end
''')
    learned = json.loads((ROOT/'artifacts/ASIC/parameters/00_detail_stem.json').read_text())
    beta, theta = learned['beta_q'][0]/2**23, learned['threshold_q'][0]/2**16
    currents = [0.0, .12, -.08, .35, .04, -.2, .5, 0.0]
    events = []
    for i, weight in enumerate(currents):
        events += [f'Vp{i} p{i} 0 PULSE(0 1 {i*10+1}u 1n 1n 1u 1000u)',
                   f'Xs{i} p{i} state vcm signed_synapse w={weight}']
    plif = '''Sampled PLIF mixed-level prototype; accelerated phase timing, no real-time claim
.include "models_tt.spice"
'''+common+f'''
Vdd vdd 0 1.8
Vcm vcm 0 0.9
Vbias bias 0 0.65
Vreset reset 0 PWL(0 1.8 0.4u 1.8 0.401u 0 80u 0)
Vcapture capture 0 PULSE(0 1.8 8u 1n 1n 0.3u 10u)
Vcommit commit 0 PULSE(0 1.8 9u 1n 1n 0.3u 10u)
Xplif state snapshot spike capture commit reset bias vdd 0 vcm sampled_plif beta={beta} theta={theta}
'''+ '\n'.join(events)+'''
.control
set wr_singlescale
set wr_vecnames
tran 10n 80u
wrdata ../results/sampled_plif.dat v(state) v(snapshot) v(spike) i(Vdd)
quit
.endc
.end
'''
    (benches/'sampled_plif.cir').write_text(plif)
    reference = []; state=0.0
    for i, current in enumerate(currents):
        candidate=beta*state+current; spike=int(candidate>=theta); state=candidate-spike*theta
        reference.append(dict(bin=i, candidate=candidate, spike=spike, preleaked=beta*state))
    (OUT/'sampled_plif_reference.json').write_text(json.dumps(reference,indent=2)+'\n')
    spec = json.loads((ROOT/'artifacts/ASIC/model_spec.yaml').read_text())
    modules = {
        'sampled_plif': 'integrated CMOS storage/comparator with ideal isolation buffer, signed injection, target scaling driver and capacitors; not complete physical circuit',
        'comparator': 'SKY130 differential pair/mirror load with CMOS buffers; external bias, offset/headroom qualification pending',
        'membrane_hold': 'SKY130 CMOS transmission gate plus ideal capacitor; no extracted capacitor or leakage qualification',
        'signed_synapse': 'behavioral signed current injector; physical weight DAC pending',
        'threshold_reset': 'behavioral threshold and subtractive reset; standalone transistor comparator prototype exists, integration/charge subtraction pending',
        'sampled_leak': 'behavioral learned-beta target; switched charge scaling amplifier pending',
        'energy_square': 'behavioral squarer; transistor realization pending',
        'energy_root': 'behavioral RMS root; transistor realization pending',
        'adaptation_triangle': 'behavioral triangle; age/amplitude storage and refresh controller pending',
        'peer_inhibition': 'behavioral gated decrement; physical injection circuit pending',
        'class_integrator': 'ideal capacitor and reset switch; physical readout pending',
        'argmax6': 'behavioral six-class first-index comparator tree',
        'routing_control': 'preserved digital DAG interface specification; analog integration pending',
    }
    actors = []
    for layer in spec['layers']:
        if not layer.get('logical_membrane_states'): continue
        param = json.loads((ROOT/'artifacts/ASIC'/layer['parameter_file']).read_text())
        roles = ['signed_synapse', 'membrane_hold', 'sampled_leak', 'threshold_reset']
        if param.get('inhibition_enabled'): roles += ['energy_square','energy_root','peer_inhibition']
        if param.get('threshold_adaptation_enabled'): roles += ['energy_square','energy_root','adaptation_triangle']
        actors.append(dict(name=layer['name'], roles=roles, states=layer['logical_membrane_states'],
                           parameters=param, beta_fraction_bits=23, threshold_fraction_bits=16))
    contract = dict(schema_version=1, model='EventSpikeSeg140k', owner='Codex', grok_role='testing_and_debugging_only',
                    source_export='artifacts/ASIC/model_spec.yaml', actors=actors, modules=modules,
                    pdk=dict(name='SKY130', revision=revision, url='https://github.com/google/skywater-pdk-libs-sky130_fd_pr',
                             corner='tt', mismatch='nominal; no Monte Carlo qualification'),
                    provisional_electrical=dict(vdd=1.8, common_mode=0.9, volts_per_state_unit=0.2, membrane_capacitance_f=1e-12,
                                                warning='Illustrative starting point, not range/noise/area qualified'),
                    timing=dict(semantic_bin_s=.005, commit='sample threshold, subtract reset/inhibition, apply beta once, hold, accept next-bin charge',
                                phases='non-overlap controller and stable state snapshot required; not implemented'),
                    layout_complete=False, total_power_w=None, latency_s=None,
                    source_sha256=hashlib.sha256((ROOT/'asic/analog/modules.spice').read_bytes()).hexdigest())
    (OUT/'design.yaml').write_text(json.dumps(contract, indent=2)+'\n')
    print('Generated five bounded benches and contracts for', len(actors), 'actors;', len(modules), 'module roles')


if __name__ == '__main__':
    main()
