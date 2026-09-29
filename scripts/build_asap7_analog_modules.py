"""Generate separately labelled ASAP7 research prototypes; preserve SKY130.

Fixed 21nm/3-fin devices are a starting geometry, not a ported/optimized cell.
"""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/analog_asic/asap7'


def main():
    source=(ROOT/'asic/analog/modules.spice').read_text()
    def transistor(match):
        name,nodes,polarity=match.groups()
        return f'N{name} {nodes} {polarity}mos_rvt'
    source=re.sub(r'^X(\w+) (.*?) sky130_fd_pr__([np])fet_01v8 w=[\d.]+ l=[\d.]+$',transistor,source,flags=re.M)
    source=source.replace('SKY130','ASAP7')
    # ASAP7 midrail is 0.35 V (VDD/2); SKY130 source keeps 0.9 V mid references.
    source=source.replace('v(spike)-0.9','v(spike)-0.35')
    source=source.replace('v(capture)-0.9','v(capture)-0.35')
    source=source.replace('v(spike)>0.9','v(spike)>0.35')
    # Explicit provisional output loading prevents unphysical unloaded logic
    # nodes; this is a declared wiring/load assumption, not extracted capacitance.
    source=source.replace('.ends inv','Cprovisional_load y vss 1f\n.ends inv')
    source=source.replace('.ends comparator','Cprovisional_compensation d2 vss 50f\n.ends comparator')
    # Default ASAP7 smoke keeps scale-normalized logistic compare + capture track-hold
    # (accepted baseline). MOSFET comparator completes in isolation and in a capture+amp
    # bench, but reintegrating it into full sampled_plif still aborts Newton on sense_int
    # at the first threshold crossing; see benches/comparator_isolated.cir and
    # benches/capture_compare_isolated.cir. Transistor reintegration remains Stage 3.
    source=source.replace(
        'Xcmp snap_cmp threshold spike vbias vdd vss comparator',
        'Bcmp_raw cmp_out vss V={v(vdd)/(1+exp(-2000*((v(snap_cmp)-v(threshold))/max(scale,1e-6))))}\n'
        'Ccmp_raw cmp_out vss 5f\n'
        'Bhold vss spike I={(v(cmp_out)-v(spike))*(2e-4)/(1+exp(-100*(v(capture)-0.35)))}\n'
        'Cspike_hold spike vss 50f\n'
        'Rspike_bleed spike vcm 500Meg')
    # ASAP7 provisional sense-path RC: larger Rout/shunt so TG charge-share into
    # 1pF remains well-posed inside the 0.3us capture window (not a physical R/C).
    source=source.replace('Rsense sense_int sensed 20k','Rsense sense_int sensed 5k')
    source=source.replace('Csense_shunt sensed vcm 200f','Csense_shunt sensed vcm 50f')
    source=source.replace('Rsnap_s snapshot snap_cmp 50k','Rsnap_s snapshot snap_cmp 10k')
    source=source.replace('Csnap_s snap_cmp vcm 100f','Csnap_s snap_cmp vcm 20f')
    source=source.replace('Btarget target vss V=',
        'Rtarget target_driver target 5k\nCtarget_shunt target vcm 50f\nBtarget target_driver vss V=')
    source='* AUTO-GENERATED: 21nm, 3 fins, VDD 0.7V; sense/target drivers are finite-Z provisional models.\n'+source
    (OUT/'modules.spice').write_text(source)
    # Start from the same normalized learned beta/threshold and input sequence.
    old=(ROOT/'artifacts/analog_asic/benches/sampled_plif.cir').read_text()
    old=old.replace('.include "models_tt.spice"','.include "../models/tt_osdi.spice"')
    old=old.replace('.include "../../../asic/analog/modules.spice"','.include "../modules.spice"')
    old=old.replace('1.8','0.7').replace('Vcm vcm 0 0.9','Vcm vcm 0 0.35').replace('Vbias bias 0 0.65','Vbias bias 0 0.3')
    old=re.sub(r'(Xplif[^\n]+)',r'\1 scale=0.07',old)
    old=re.sub(r'(Xs\d+[^\n]+)',r'\1 scale=0.07',old)
    old=old.replace('.control','.control\npre_osdi ../tools/bsimcmg107.osdi')
    (OUT/'benches/sampled_plif.cir').write_text(old)
    # Isolate the storage/update core from phase-buffer convergence. The actual
    # digital controller must later deliver both phases; its power is excluded.
    external=source.replace('spike capture commit reset vbias vdd vss vcm',
        'spike capture capture_b commit commit_b reset reset_b vbias vdd vss vcm')
    for line in ['Xci capture capture_b vdd vss inv','Xwi commit commit_b vdd vss inv','Xri reset reset_b vdd vss inv']:
        external=external.replace(line,'* Complementary phases supplied by external controller')
    (OUT/'modules_external_phases.spice').write_text(external)
    external_bench=old.replace('../modules.spice','../modules_external_phases.spice')
    external_bench=external_bench.replace('Xplif state snapshot spike capture commit reset bias',
        'Bcapb capture_b 0 V={0.7-v(capture)}\nBcomb commit_b 0 V={0.7-v(commit)}\nBrstb reset_b 0 V={0.7-v(reset)}\nXplif state snapshot spike capture capture_b commit commit_b reset reset_b bias')
    external_bench=external_bench.replace('results/sampled_plif.dat','results/sampled_plif_external.dat')
    # Soften phase edges: 1ns ideal steps couple TG charge into the sense buffer.
    # 50ns is still << 0.3us capture; not a simulator-tolerance change.
    external_bench=external_bench.replace('PULSE(0 0.7 8u 1n 1n 0.3u 10u)','PULSE(0 0.7 8u 50n 50n 0.3u 10u)')
    external_bench=external_bench.replace('PULSE(0 0.7 9u 1n 1n 0.3u 10u)','PULSE(0 0.7 9u 50n 50n 0.3u 10u)')
    (OUT/'benches/sampled_plif_external.cir').write_text(external_bench)
    (OUT/'benches/retention.cir').write_text('''ASAP7 5ms capacitor retention test; ideal capacitor excludes dielectric leakage
.include "../models/tt_osdi.spice"
.include "../modules.spice"
Vdd vdd 0 0.7
Vcm vcm 0 0.35
Vin input 0 PWL(0 0.42 2u 0.42 2.001u 0.28 5.002m 0.28)
Vsample sample 0 PWL(0 0.7 1u 0.7 1.001u 0 5.002m 0)
Xinv sample sample_b vdd 0 inv
Xhold input state sample sample_b vdd 0 vcm membrane_hold cmem=1p
.control
pre_osdi ../tools/bsimcmg107.osdi
set wr_singlescale
set wr_vecnames
tran 1u 5.002m 0 1u
wrdata ../results/retention.dat v(state) v(input) i(Vdd)
quit
.endc
.end
''')
    hold=(OUT/'benches/retention.cir').read_text().replace('Xinv sample sample_b vdd 0 inv',
        'Vsampleb sample_b 0 PWL(0 0 1u 0 1.001u 0.7 5.002m 0.7)')
    (OUT/'benches/retention_external_clock.cir').write_text(hold.replace('results/retention.dat','results/retention_external_clock.dat'))
    (OUT/'prototype.json').write_text(json.dumps(dict(
        voltage=0.7,common_mode=0.35,volts_per_state_unit=.07,membrane_capacitance_f=1e-12,
        device_geometry=dict(length_m=21e-9,fins=3),
        source='asic/analog/modules.spice',physical_layout_complete=False,
        caveats=[
            'initial unsized circuit',
            'provisional finite-gm sense buffer (30uA tanh to vcm, Rout=5k, light shunt/bleeds) and 5k target driver; not transistor layout',
            'ASAP7 smoke uses scale-normalized logistic compare (k=2000) + capture track-hold; MOSFET cmp proven only in isolation/capture benches (not yet in full PLIF)',
            'ASAP7 external bench uses 50ns phase edges (still << 0.3us capture); provisional driver model',
            'continuous logistic Btarget (midrail 0.35V); spike decision held after capture for commit',
            '1fF assumed load per inverter output; MOSFET comparator card retains 50fF compensation',
            'ideal membrane capacitors; no dielectric leakage or extracted parasitics',
            'no HSPICE cross-validation',
            'EOTACC declaration-range adaptation recorded separately',
        ],
    ), indent=2)+'\n')
    print('Generated ASAP7 sampled PLIF and real-duration 5ms retention benches')


if __name__=='__main__': main()
