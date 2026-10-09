"""Extracted GF180 storage read into a schematic shared charge amplifier."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corner',choices=['typical','ff','ss'],default='typical')
    parser.add_argument('--temp-c',type=float,default=27)
    parser.add_argument('--feedback-ff',type=float,default=100)
    parser.add_argument('--offset-mv',type=float,default=750)
    parser.add_argument('--physical-reset',action='store_true')
    parser.add_argument('--physical-ota',action='store_true')
    parser.add_argument('--physical-caps',action='store_true')
    parser.add_argument('--combined-frontend',action='store_true',help='Use the routed reader including reset, bias diode and both MIM caps')
    parser.add_argument('--load-mim-count',type=int,choices=[0,1,4,16],default=0)
    parser.add_argument('--comp-resistance-ohm',type=float,default=100)
    args=parser.parse_args()
    if args.combined_frontend and (args.physical_reset or args.physical_ota or args.physical_caps or args.feedback_ff != 100):
        raise ValueError('combined frontend requires nominal100fF and no separate-piece switches')
    if not 50 <= args.feedback_ff <= 200 or not 0 < args.offset_mv <= 750:
        raise ValueError('feedback capacitance or state offset outside bounded range')
    if args.physical_caps and (not args.physical_ota or args.feedback_ff != 100):
        raise ValueError('physical capacitor screen requires physical OTA and nominal100fF feedback selection')
    if not 0 <= args.comp_resistance_ohm <= 3000:
        raise ValueError('compensation resistor outside0..3000ohm screen')
    stem=f'gf180_active_charge_read_{args.corner}_temp{args.temp_c:g}_cf{args.feedback_ff:g}ff_offset{args.offset_mv:g}mv'
    if args.physical_reset:
        stem += '_physicalreset'
    if args.physical_ota:
        stem += '_physicalota'
    if args.physical_caps:
        stem += '_physicalcaps_groundedsubstrate'
    if args.comp_resistance_ohm != 100:
        stem += f'_rcomp{args.comp_resistance_ohm:g}'
    if args.combined_frontend:
        stem += '_combinedfrontend'
    if args.load_mim_count:
        if not args.combined_frontend:
            raise ValueError('physical load screen requires combined frontend')
        stem += f'_loadmim{args.load_mim_count}'
    modeldir=BASE/'pdk/gf180_primitive_source/models/ngspice'
    prefix='/workspace/'+modeldir.relative_to(ROOT).as_posix()
    cell=BASE/'layout/gf180_gate_state_cell/gf180_gate_state_cell_cap.spice'
    ota=ROOT/'asic/analog/gf180_shared_ota.spice'
    reset=BASE/'layout/gf180_fixed_body_tg/gf180_fixed_body_tg_cap.spice'
    core=BASE/'layout/gf180_shared_ota_core/gf180_shared_ota_core_cap.spice'
    feedback=BASE/'layout/gf180_mim_7x7/gf180_mim_7x7_cap.spice'
    compensation=BASE/'layout/gf180_mim_22x22/gf180_mim_22x22_cap.spice'
    frontend=BASE/'layout/gf180_charge_read_frontend/gf180_charge_read_frontend_cap.spice'
    deck=BASE/f'benches/{stem}.spice'
    lines=['GF180 active charge read: storage extracted, OTA schematic',f'.include {prefix}/design.spice',
           '.param sw_stat_global=0 sw_stat_mismatch=0',f'.lib {prefix}/sm141064.spice {args.corner}',
           f'.temp {args.temp_c:g}', '.options gmin=1e-18 reltol=1e-6 abstol=1e-16 vntol=1e-10',
           *cell.read_text().splitlines(),*ota.read_text().splitlines(),
           'Vdd vdd 0 3.3','Vcm vcm 0 1.65','Iref vdd bias 20u',
           'Xref bias bias 0 0 nfet_03v3 w=10u l=2u as=4.4p ad=4.4p ps=20.88u pd=20.88u',
           '.model ideal_phase SW(Ron=10 Roff=1e30 Vt=1.65 Vh=0.1)',
           'Vinit init 0 PWL(0 3.3 0.99u 3.3 1u 0 5.01m 0)',
           'Vreset reset 0 PWL(0 3.3 4.99949m 3.3 4.9995m 0 5.01m 0)',
           'Ven en 0 PWL(0 0 4.99999m 0 5m 3.3 5.00099m 3.3 5.001m 0 5.01m 0)',
           'Venb enb 0 PWL(0 3.3 4.99999m 3.3 5m 0 5.00099m 0 5.001m 3.3 5.01m 3.3)']
    if args.physical_reset:
        lines += reset.read_text().splitlines()+['Vresetb resetb 0 PWL(0 0 4.99949m 0 4.9995m 3.3 5.01m 3.3)']
    if args.combined_frontend:
        lines.remove('Iref vdd bias 20u')
        lines.remove('Xref bias bias 0 0 nfet_03v3 w=10u l=2u as=4.4p ad=4.4p ps=20.88u pd=20.88u')
        lines += [f'.lib {prefix}/sm141064.spice mimcap_typical',
                  'Vresetb resetb 0 PWL(0 0 4.99949m 0 4.9995m 3.3 5.01m 3.3)',
                  *frontend.read_text().splitlines()]
    if args.physical_ota:
        lines += core.read_text().splitlines()
    if args.physical_caps:
        lines += [f'.lib {prefix}/sm141064.spice mimcap_typical']+feedback.read_text().splitlines()+compensation.read_text().splitlines()
    if args.load_mim_count:
        lines += compensation.read_text().splitlines()
    kinds=['low','high','zero']
    for kind, sign in [('low',-1),('high',1),('zero',0)]:
        target=1.65+sign*args.offset_mv/1000
        lines += [f'Vtarget_{kind} target_{kind} 0 {target:.12g}',
                  f'Sinit_{kind} target_{kind} state_{kind} init 0 ideal_phase',
                  f'Xcell_{kind} virtual_{kind} state_{kind} en enb 0 vdd gf180_gate_state_cell',
                  f'Xota_{kind} vcm virtual_{kind} out_{kind} vdd 0 bias gf180_shared_ota',
                  f'Cf_{kind} out_{kind} virtual_{kind} {args.feedback_ff:g}f',
                  f'Sreset_{kind} out_{kind} virtual_{kind} reset 0 ideal_phase',
                  f'Cload_{kind} out_{kind} 0 100f']
        if args.load_mim_count:
            lines.remove(f'Cload_{kind} out_{kind} 0 100f')
            lines += [f'Xload_{kind}_{i} out_{kind} 0 0 gf180_mim_22x22' for i in range(args.load_mim_count)]
        if args.combined_frontend:
            lines.remove(f'Xota_{kind} vcm virtual_{kind} out_{kind} vdd 0 bias gf180_shared_ota')
            lines.remove(f'Cf_{kind} out_{kind} virtual_{kind} {args.feedback_ff:g}f')
            lines.remove(f'Sreset_{kind} out_{kind} virtual_{kind} reset 0 ideal_phase')
            lines += [f'Iref_{kind} vdd bias_{kind} 20u',
                      f'Xfrontend_{kind} vcm virtual_{kind} out_{kind} vdd 0 bias_{kind} reset resetb gf180_charge_read_frontend']
        if args.physical_reset:
            lines.remove(f'Sreset_{kind} out_{kind} virtual_{kind} reset 0 ideal_phase')
            lines.append(f'Xreset_{kind} out_{kind} virtual_{kind} reset resetb 0 vdd gf180_fixed_body_tg')
        if args.physical_ota:
            lines.remove(f'Xota_{kind} vcm virtual_{kind} out_{kind} vdd 0 bias gf180_shared_ota')
            lines += [f'Xota_{kind} vcm virtual_{kind} out_{kind} vdd 0 bias cmp_{kind} gf180_shared_ota_core',
                      f'Ccomp_{kind} cmp_{kind} comp_{kind} 1p',f'Rcomp_{kind} comp_{kind} out_{kind} {args.comp_resistance_ohm:g}']
        if args.physical_caps:
            lines.remove(f'Cf_{kind} out_{kind} virtual_{kind} {args.feedback_ff:g}f')
            lines.remove(f'Ccomp_{kind} cmp_{kind} comp_{kind} 1p')
            lines += [f'Xcf_{kind} out_{kind} virtual_{kind} 0 gf180_mim_7x7',
                      f'Xcomp_{kind} cmp_{kind} comp_{kind} 0 gf180_mim_22x22']
        if args.physical_ota and args.comp_resistance_ohm == 0:
            lines.remove(f'Rcomp_{kind} comp_{kind} out_{kind} 0')
            if args.physical_caps:
                lines.remove(f'Xcomp_{kind} cmp_{kind} comp_{kind} 0 gf180_mim_22x22')
                lines.append(f'Xcomp_{kind} cmp_{kind} out_{kind} 0 gf180_mim_22x22')
            else:
                lines.remove(f'Ccomp_{kind} cmp_{kind} comp_{kind} 1p')
                lines.append(f'Ccomp_{kind} cmp_{kind} out_{kind} 1p')
    lines += ['.control','set numdgt=15','tran 500n 5.01m']
    for kind in kinds:
        for name,node,time in [('held','state','4.998m'),('pre','out','4.9998m'),('r100n','out','5.0001m'),('r500n','out','5.0005m'),('r900n','out','5.0009m'),('virtual','virtual','5.0009m'),('readstate','state','5.0009m'),('post','out','5.002m')]:
            lines.append(f'meas tran {kind}_{name} find v({node}_{kind}) at={time}')
    lines += ['quit','.endc','.end']
    deck.write_text('\n'.join(lines)+'\n',encoding='ascii')
    proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2',
                         '--env','NGSPICE_MEAS_PRECISION=15','--volume',f'{ROOT}:/workspace','--workdir',prefix,
                         '--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b',
                         '/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log=proc.stdout+proc.stderr;logpath=BASE/f'results/{stem}.log';logpath.write_text(log)
    values={k:float(v) for k,v in re.findall(r'(?m)^\s*((?:low|high|zero)_(?:held|pre|r100n|r500n|r900n|virtual|readstate|post))\s*=\s*([-+0-9.eE]+)',log)}
    complete=proc.returncode==0 and 'ngspice-47 done' in log and len(values)==24
    rows={kind:{k:values[f'{kind}_{k}'] for k in ['held','pre','r100n','r500n','r900n','virtual','readstate','post']} for kind in kinds} if complete else {}
    if complete:
        for kind,row in rows.items():
            row['virtual_error_mv']=(row['virtual']-1.65)*1000
            row['state_read_disturbance_mv']=(row['readstate']-row['held'])*1000
            row['read_response_relative_to_zero_v']=row['r900n']-rows['zero']['r900n']
            row['100ns_to_900ns_output_difference_mv']=(row['r100n']-row['r900n'])*1000
    sources=[Path(__file__),cell,ota,deck,logpath,modeldir/'design.spice',modeldir/'sm141064.spice']
    if args.physical_reset:
        sources.append(reset)
    if args.physical_ota:
        sources.append(core)
    if args.physical_caps:
        sources += [feedback,compensation,modeldir/'sm141064_mim.spice']
    if args.combined_frontend:
        sources += [frontend,modeldir/'sm141064_mim.spice']
    if args.load_mim_count:
        sources.append(compensation)
    result={'simulation_completed':complete,'corner':args.corner,'temperature_c':args.temp_c,'offset_mv':args.offset_mv,'feedback_ff_nominal':args.feedback_ff,'physical_feedback_reset':args.physical_reset,'physical_ota_core':args.physical_ota,'physical_feedback_compensation_caps':args.physical_caps,'compensation_resistance_ohm':args.comp_resistance_ohm,'mim_corner':'typical' if args.physical_caps else None,'rows':rows,
            'physical_state_accepted':False,
            'scope':'Extracted storage/access, optional reset TG, OTA core and MIM feedback/compensation caps.20uA reference, reference transistor geometry,100ohm compensation resistor, load and phases remain schematic/ideal. MIM explicitly typical, not fast/slow with MOS. Separately extracted pieces, no combined routed frontend. Destructive read only, no restore/encoder, switched noise, mismatch, qualified gate leakage or full-float/service acceptance.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    if args.combined_frontend:
        result.update(combined_routed_frontend=True,physical_feedback_reset=True,physical_ota_core=True,
                      physical_feedback_compensation_caps=True,compensation_resistance_ohm=0,mim_corner='typical',
                      scope='Combined routed10MOS/2MIM frontend with capacitance extraction, including reset TG, OTA, bias diode, feedback and direct Miller compensation. Separately extracted storage/access. Ideal20uA external current reference,100fF load, initial programming and phases. Typical MIM with selected MOS corner; no resistance extraction, restore/encoder, switched noise/mismatch, qualified gate leakage or full-float/service acceptance.')
    result['physical_output_load_mim_count']=args.load_mim_count
    if args.load_mim_count:
        result['scope']=result['scope'].replace('100fF load','separately extracted22x22um MIM output loads (no combined load routing)')
    (BASE/f'results/{stem}.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    if not complete:
        raise RuntimeError(log[-2200:])


if __name__=='__main__':
    main()
