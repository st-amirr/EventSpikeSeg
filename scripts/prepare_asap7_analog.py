"""Translate ASAP7 model-card syntax to the original BSIM-CMG 107 OSDI model.

All physical parameter values are preserved. Only HSPICE's model selector and
version metadata are replaced by the explicitly compiled Berkeley 107 model.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/analog_asic/asap7'
PDK=ROOT/'artifacts/analog_asic/pdk'


def main():
    (OUT/'models').mkdir(exist_ok=True)
    (OUT/'benches').mkdir(exist_ok=True)
    va='\n'.join(p.read_text() for p in (PDK/'bsimcmg107/code').glob('*') if p.is_file())
    declared={x.lower() for x in re.findall(r'parameter\s+(?:real|integer)\s+(\w+)',va)}
    provenance=[]
    for corner in ['TT','SS','FF']:
        card=PDK/f'asap7/asap7_pdk_r1p7/models/hspice/7nm_{corner}_160803.pm'
        original=card.read_text()
        keys=set(re.findall(r'\b(\w+)\s*=', '\n'.join(l for l in original.splitlines() if l.startswith('+'))))
        assert keys-declared == {'version'}, sorted(keys-declared)
        assert set(re.findall(r'\bversion\s*=\s*(\d+)',original))=={'107'}
        translated=re.sub(r'(?im)^\.model\s+(\w+)\s+([np])mos\s+level\s*=\s*72\s*$',
            lambda m:f'.model {m[1]} bsimcmg DEVTYPE={1 if m[2].lower()=="n" else 0}',original)
        translated=re.sub(r'\bversion\s*=\s*107\b','',translated)
        # Berkeley 107 exposes geometry as model parameters. This smoke uses
        # three fins; L=21nm is already specified by the original ASAP7 card.
        translated=re.sub(r'(?m)^(\.model .*)$',r'\1\n+ nfin=3',translated)
        assert 'level = 72' not in translated
        target=OUT/f'models/{corner.lower()}_osdi.spice'
        target.write_text(translated)
        provenance.append(dict(corner=corner,source=str(card.relative_to(ROOT)),
                               source_sha256=hashlib.sha256(card.read_bytes()).hexdigest(),
                               output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                               physical_parameter_keys=len(keys)-1,unknown_parameters=[]))
    (OUT/'models/translation.json').write_text(json.dumps(dict(
        source_model='Berkeley BSIM-CMG 107.0.0 20130712',
        modifications=['model type nmos/pmos level72 -> bsimcmg DEVTYPE1/0',
                       'remove version=107 metadata; compiled model is fixed version107',
                       'set nfin=3 geometry for smoke test; card L=21nm retained'],
        physical_parameter_values_changed=False,corners=provenance),indent=2)+'\n')
    (OUT/'benches/inverter.cir').write_text('''ASAP7 original BSIM-CMG 107 inverter DC transfer
.include "../models/tt_osdi.spice"
Vdd vdd 0 0.7
Vin input 0 0
Nn output input 0 0 nmos_rvt
Np output input vdd vdd pmos_rvt
.control
pre_osdi ../tools/bsimcmg107.osdi
set wr_singlescale
set wr_vecnames
dc Vin 0 0.7 0.01
wrdata ../results/inverter_dc.dat v(input) v(output) i(Vdd)
quit
.endc
.end
''')
    dc=(OUT/'benches/inverter.cir').read_text()
    transient=dc.replace('Vin input 0 0','Vin input 0 PWL(0 0 1n 0 2n 0.7 4n 0.7 5n 0 7n 0)\nCload output 0 1f')
    transient=transient.replace('dc Vin 0 0.7 0.01','tran 1p 7n').replace('inverter_dc.dat','inverter_transient.dat')
    (OUT/'benches/inverter_transient.cir').write_text(transient)
    print('Prepared TT/SS/FF cards preserving every physical parameter; inverter probe ready')


if __name__=='__main__': main()
