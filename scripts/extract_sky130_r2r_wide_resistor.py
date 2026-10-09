from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/analog_asic/layout/sky130_r2r_wide_resistor_probe'
IMAGE='eventspikeseg:analog-layout';RC='/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/magic/sky130A.magicrc'
name='sky130_fd_pr__res_xhigh_po_5p73_B4TZ4A'

def main():
    mag=OUT/f'{name}.mag';s=mag.read_text(encoding='ascii')
    labels=('<< labels >>\n'
    'rlabel metal1 s -569 611 569 617 4 R1\nport 1 nsew\n'
    'rlabel metal1 s -569 -617 569 -611 4 R0\nport 2 nsew\n')
    mag.write_text(s.replace('<< end >>',labels+'<< end >>'),encoding='ascii')
    tcl='\n'.join([f'load {name}','drc check','drc count','extract all','ext2spice lvs','ext2spice scale off',f'ext2spice -o {name}.spice',f'gds write {name}.gds','save','quit -noprompt',''])
    cmd=['docker','run','--rm','-i','-v',f'{ROOT}:/workspace','-e','PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root','-w','/workspace/artifacts/analog_asic/layout/sky130_r2r_wide_resistor_probe','--entrypoint','magic',IMAGE,'-dnull','-noconsole','-rcfile',RC]
    p=subprocess.run(cmd,input=tcl,text=True,capture_output=True,timeout=180,cwd=ROOT);log=p.stdout+p.stderr;(OUT/'magic_extract.log').write_text(log,encoding='utf-8')
    print('return',p.returncode,'drc_zero','Total DRC errors found: 0' in log);print(log[-2500:]);print('outputs',[f.name for f in OUT.glob(f'{name}.*')])
    if p.returncode or 'Total DRC errors found: 0' not in log:return 2
    spice=OUT/f'{name}.spice'; text=spice.read_text(encoding='ascii')
    import re,json
    body=sorted(set(re.findall(r'^X\S+\s+\S+\s+\S+\s+(\S+)\s+sky130_fd_pr__res_xhigh_po_5p73\s',text,re.M)) - {'R1','R0'})
    if not body:raise RuntimeError('missing extracted resistor body net')
    ref=OUT/'wide_res_reference.spice'
    ref.write_text(f'.subckt {name} R1 R0\nX0 R0 R1 VSUBS sky130_fd_pr__res_xhigh_po_5p73 l=6e+06u\n.ends\n',encoding='ascii')
    setup='/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/netgen/sky130A_setup.tcl'
    netcmd=['docker','run','--rm','-v',f'{ROOT}:/workspace','-e','PDK_ROOT=/workspace/artifacts/analog_asic/pdk/ciel_root','-w','/workspace/artifacts/analog_asic/layout/sky130_r2r_wide_resistor_probe','--entrypoint','netgen-lvs',IMAGE,'-batch','lvs',f'{name}.spice {name}',f'{ref.name} {name}',setup,'wide_res_lvs.out']
    nl=subprocess.run(netcmd,capture_output=True,text=True,timeout=180,cwd=ROOT);nlog=nl.stdout+nl.stderr;(OUT/'netgen_wide_lvs.log').write_text(nlog,encoding='utf-8')
    print('LVS unique','Circuits match uniquely' in nlog);print(nlog[-1500:])
    deck=OUT/'wide_res_dc.cir';bn=body[0]
    deck.write_text(f'''* Extracted wide SKY130 xhigh-poly resistor DC measurement
    .option scale=1u
    .include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"
    .include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
    .include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"
    .include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po.model.spice"
    .include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_5p73.model.spice"
    .include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"
    .include "/workspace/artifacts/analog_asic/layout/sky130_r2r_wide_resistor_probe/{name}.spice"
    .global {bn}
    .param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0
    .param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11
    Vsub {bn} 0 0
    Vtest in out 1m
    Xprobe in out {name}
    .control
    op
    let r=1m/abs(i(Vtest))
    print r
    quit
    .endc
    .end
    ''',encoding='ascii')
    simcmd=['docker','run','--rm','-v',f'{ROOT}:/workspace','-w','/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models','--entrypoint','ngspice','eventspikeseg:analog-ngspice36','-b',f'/workspace/{deck.relative_to(ROOT).as_posix()}']
    sim=subprocess.run(simcmd,capture_output=True,text=True,timeout=90,cwd=ROOT);slog=sim.stdout+sim.stderr;(OUT/'ngspice_wide_dc.log').write_text(slog,encoding='utf-8')
    mm=re.search(r'^r\s*=\s*([-+0-9.eE]+)',slog,re.M|re.I);measured=float(mm.group(1)) if mm else None
    q={'pcell':'sky130_fd_pr__res_xhigh_po_5p73','drawn_w_um':5.73,'drawn_l_um':6.0,'simulation_completed':sim.returncode==0 and 'ngspice-36 done' in slog,'magic_drc_zero':'Total DRC errors found: 0' in log,'netgen_lvs_unique':'Circuits match uniquely' in nlog,'extracted_dc_ohms':measured,'schematic_model_dc_ohms':None,'gds_written':(OUT/f'{name}.gds').exists(),'scope':'Standalone wide xhigh-poly resistor PCell; TT/27C physical extraction and DC only. No DAC network, array matching, PVT, mismatch, or noise.'}
    (OUT/'qualification.json').write_text(json.dumps(q,indent=2)+'\n',encoding='utf-8');print(json.dumps(q,indent=2))

if __name__ == "__main__":
    raise SystemExit(main())
