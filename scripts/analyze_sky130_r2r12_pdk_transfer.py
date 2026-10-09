from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'artifacts/analog_asic'
RES=OUT/'results'; BENCH=OUT/'benches'; IMAGE='eventspikeseg:analog-ngspice36'; N=12

def main():
    BENCH.mkdir(parents=True,exist_ok=True); RES.mkdir(parents=True,exist_ok=True)
    mode=next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--switch-mode=')),'pdk')
    if mode not in {'pdk','ideal'}: raise ValueError('switch-mode must be pdk or ideal')
    resistor_mode=next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--resistor-mode=')),'pdk')
    switch_m=int(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--switch-m=')),'100'))
    vlo=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--vlo=')),'0'))
    vhi=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--vhi=')),'1.8'))
    resistor_w=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--resistor-w=')),'1.41'))
    resistor_l=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--resistor-l=')),'0.7'))
    corner=next((a.split('=',1)[1].lower() for a in sys.argv[1:] if a.startswith('--corner=')),'tt')
    temp=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--temp-c=')),{'tt':'27','ss':'0','ff':'85'}.get(corner,'27')))
    load_ohms=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--load-ohms=')),'1e7'))
    if corner not in {'tt','ss','ff'} or load_ohms<=0: raise ValueError('corner must be tt/ss/ff and load must be positive')
    if not (0<=vlo<vhi<=1.8): raise ValueError('reference rails outside 0..1.8V')
    if resistor_mode not in {'pdk','ideal'}: raise ValueError('resistor-mode must be pdk or ideal')
    lines=['* 12-bit R2R, measured SKY130 xhigh-poly resistor model',
      '.option scale=1u reltol=1e-6 abstol=1e-14 vntol=1e-9',
      '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"',
      '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
      f'.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
      f'.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
      '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"',
      '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po.model.spice"',
      '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"',
      '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"',
      '.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38',
      '.param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0',
      '.param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11',
      '.model SWMOD SW(Ron=1m Roff=1e15 Vt=0.9 Vh=0)',
      '.subckt r2r_switch a b en enb vdd vss']
    if mode=='ideal': lines.append('Ssw a b en 0 SWMOD')
    else:
      lines += [f'Xn a en b vss sky130_fd_pr__nfet_01v8 w=1 l=0.15 m={switch_m}',
                f'Xp a enb b vdd sky130_fd_pr__pfet_01v8 w=2 l=0.15 m={switch_m}']
    lines += ['.ends r2r_switch',f'.temp {temp:g}','Vdd vdd 0 1.8',f'Vhi vhi 0 {vhi:g}',f'Vlo vlo 0 {vlo:g}','Vsub vsub 0 0','Vcode code 0 0',f'Rload out vlo {load_ohms:g}']
    rline=lambda name,a,b: (f'R{name} {a} {b} 1225.298' if resistor_mode=='ideal' else f'X{name} {a} {b} vsub sky130_fd_pr__res_xhigh_po_1p41 w={resistor_w:g} l={resistor_l:g}')
    lines += [rline('term1','n0','t0'),rline('term2','t0','vlo')]
    for k in range(1,N):
      node='out' if k==N-1 else f'n{k}'; nxt=f'n{k-1}'
      lines.append(rline(f'lad{k}',node,nxt))
    for k in range(N):
      node='out' if k==N-1 else f'n{k}'
      lines += [rline(f'br{k}a',node,f'm{k}a'),rline(f'br{k}b',f'm{k}a',f'm{k}')]
      expr=f'1.8*(floor(V(code)/{2**k})-2*floor(V(code)/{2**(k+1)}))'
      lines += [f'Bbit{k} b{k} 0 V={{{expr}}}',f'Bbitb{k} bb{k} 0 V={{1.8-V(b{k})}}',
                f'Xhi{k} vhi m{k} b{k} bb{k} vdd 0 r2r_switch',
                f'Xlo{k} vlo m{k} bb{k} b{k} vdd 0 r2r_switch']
    rail_tag=f'lo{vlo:g}_hi{vhi:g}'.replace('.','p')
    geom_tag=f'w{resistor_w:g}_l{resistor_l:g}'.replace('.','p')
    tag=f'{mode}_{resistor_mode}_m{switch_m}_{rail_tag}_{geom_tag}_{corner}_t{temp:g}c_load{load_ohms:g}'
    data=f'/workspace/artifacts/analog_asic/results/sky130_r2r12_{tag}_transfer.dat'
    lines += ['.control','set noaskquit','set numdgt=15','set wr_singlescale','set wr_vecnames',
              f'dc Vcode 0 {2**N-1} 1',f'wrdata {data} v(out) ' + ' '.join(f'v(b{k})' for k in range(N)),'quit','.endc','.end','']
    deck=BENCH/f'sky130_r2r12_{tag}_transfer.cir';deck.write_text('\n'.join(lines),encoding='ascii')
    cmd=['docker','run','--rm','--memory','6g','--cpus','2','-v',f'{ROOT}:/workspace','-w',
         '/workspace/artifacts/analog_asic/benches','--entrypoint','timeout',IMAGE,'240','ngspice','-b',deck.name]
    proc=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=255);log=proc.stdout+proc.stderr
    (RES/f'sky130_r2r12_{tag}_transfer.log').write_text(log,encoding='utf-8')
    path=RES/f'sky130_r2r12_{tag}_transfer.dat'
    if proc.returncode or not path.exists() or 'ngspice-36 done' not in log: raise RuntimeError(log[-3000:])
    arr=np.loadtxt(path,skiprows=1); v=arr[:,1]; lsb=(vhi-vlo)/(2**N); ideal=vlo+np.arange(len(v))*lsb
    err=v-ideal; dnl=np.diff(v)/lsb-1
    report={'simulation_completed':True,'bits':N,'corner':corner.upper(),'temperature_c':temp,'switch_mode':mode,'switch_m':switch_m,'resistor_mode':resistor_mode,'resistor_width_um':resistor_w,'resistor_length_um':resistor_l,'load_ohms':load_ohms,
      'resistor_source':f'SKY130 xhigh-poly PCell model; R=one unit, 2R=two series units; w={resistor_w:g}um l={resistor_l:g}um',
      'switch_source':('ideal V-controlled switch Ron=1mOhm' if mode=='ideal' else f'SKY130 TT NMOS/PMOS TG models, m={switch_m}'),
      'codes':len(v),'output_min_v':float(v[0]),'output_max_v':float(v[-1]),'monotonic':bool(np.all(np.diff(v)>0)),
      'max_abs_lsb_error':float(np.max(np.abs(err))/lsb),
      'rms_lsb_error':float(np.sqrt(np.mean(err**2))/lsb),
      'max_abs_dnl_lsb':float(np.max(np.abs(dnl))),'min_dnl_lsb':float(np.min(dnl)),'max_dnl_lsb':float(np.max(dnl)),
      'worst_code':int(np.argmax(np.abs(err))),'worst_code_error_v':float(err[np.argmax(np.abs(err))]),'reference_low_v':vlo,'reference_high_v':vhi,
      'scope':'Full-scale DC sweep through all4096 codes at the named PVT point. Resistors use the SKY130 xhigh-poly PCell model and switches are either ideal control or SKY130 PDK MOS. Specified load is included. No resistor interconnect PEX, local mismatch, noise, settling, or routed full-DAC layout.'}
    (RES/f'sky130_r2r12_{tag}_transfer.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2));return 0
if __name__=='__main__': raise SystemExit(main())
