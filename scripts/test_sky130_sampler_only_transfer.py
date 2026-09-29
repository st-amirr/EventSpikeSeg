from __future__ import annotations
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/analog_asic'; BENCH=OUT/'benches'; RES=OUT/'results'

def main():
    lines=['SKY130 TT bottom-plate differential sampler plus regenerative latch',
      '.option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9',
      '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
      '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
      '.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38',
      '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
      '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
      '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
      '.include "../../../asic/analog/modules.spice"','.include "../../../asic/analog/sky130_ms_plif.spice"','.include "../../../asic/analog/sky130_sc_charge_integrator.spice"',
      'Vdd vdd 0 1.8','Vcm vcm 0 0.9',
      'Vclk clk 0 PWL(0 0 99.9n 0 100n 1.8 300n 1.8)',
      'Vsample_hi shi 0 PWL(0 0 9.9n 0 10n 1.8 59.9n 1.8 60n 0 300n 0)',
      'Vsample_hib shib 0 PWL(0 1.8 9.9n 1.8 10n 0 59.9n 0 60n 1.8 300n 1.8)',
      'Vsample_lo slo 0 PWL(0 0 9.9n 0 10n 1.8 59.4n 1.8 59.5n 0 300n 0)',
      'Vsample_lob slob 0 PWL(0 1.8 9.9n 1.8 10n 0 59.4n 0 59.5n 1.8 300n 1.8)',
      'Vreset reset 0 PWL(0 1.8 4.9n 1.8 5n 0 300n 0)','Vresetb resetb 0 PWL(0 0 4.9n 0 5n 1.8 300n 1.8)']
    outputs=[]
    for width in (10.0,):
      for delta in (-100.0,-6.0,-3.0,0.0,3.0,6.0,100.0):
        tag=f'c{width:g}_d{delta:g}'.replace('-','m').replace('.','p')
        src=f'src_{tag}'; diff=f'diff_{tag}'; ret=f'ret_{tag}'; dum=f'dum_{tag}'; dret=f'dret_{tag}'
        lines += [f'Vsrc_{tag} {src} 0 {0.9+delta*1e-6:.12f}',f'Cmem_{tag} {src} vcm 20p',
          f'Xsampler_{tag} {src} vcm {diff} {ret} shi shib slo slob reset resetb vdd 0 vcm sky130_sc_diff_cap_sampler_bp sample_um={width:g}',
          f'Xdummy_{tag} vcm vcm {dum} {dret} shi shib slo slob reset resetb vdd 0 vcm sky130_sc_diff_cap_sampler_bp sample_um={width:g}',
          ]
        outputs += [f'v({diff})',f'v({dum})']
    deck=BENCH/'sky130_sampler_only_transfer.cir'; data='sky130_sampler_only_transfer.dat'
    lines += ['.control','set wr_singlescale','set wr_vecnames','tran 0.2n 300n uic',f'wrdata ../results/{data} '+' '.join(outputs),'quit','.endc','.end']
    deck.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    cmd=['docker','run','--rm','--memory','4g','--cpus','2','--volume',f'{ROOT}:/workspace:ro','--volume',f'{OUT}:/workspace/artifacts/analog_asic','--workdir','/workspace/artifacts/analog_asic/benches','--entrypoint','timeout','eventspikeseg:analog-ngspice36','60','ngspice','-b',deck.name]
    run=subprocess.run(cmd,text=True,capture_output=True,timeout=75); log=run.stdout+run.stderr;(RES/'sky130_sampler_only_transfer.log').write_text(log,encoding='utf-8')
    raw=[]; dat=RES/data
    if dat.exists():
      for ln in dat.read_text().splitlines()[1:]:
        try: raw.append([float(x) for x in ln.split()])
        except ValueError: pass
    report={'test':'sky130_bottomplate_sampler_only_transfer','simulation_completed':run.returncode==0 and len(raw)>10,'return_code':run.returncode,'sample_cap_width_um':[10],'input_differential_uv':[-100,-6,-3,0,3,6,100],'sample_switch_open_ns':60,'scope':'sampler-only TT schematic with physical MIM capacitor and PDK TGs, matched nominal dummy and ideal DC-clamped source with20pF source MIM; no latch, finite source impedance, mismatch, noise, PVT or extraction'}
    if report['simulation_completed']:
      for j,width in enumerate((10.,)):
        for k,delta in enumerate((-100.,-6.,-3.,0.,3.,6.,100.)):
          base=1+(k*2); i90=min(range(len(raw)),key=lambda i:abs(raw[i][0]-90e-9)); a=raw[i90]; sampled=(a[base]-a[base+1])*1e6
          report.setdefault('measurements',[]).append({'sample_cap_width_um':width,'input_differential_uv':delta,'pre_latch_input_diff_uv':sampled,'sampler_output_minus_dummy_uv':sampled,'transfer_gain':sampled/delta if delta else None})
    (RES/'sky130_sampler_only_transfer.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); print(json.dumps(report,indent=2)); return 0 if report['simulation_completed'] else 1
if __name__=='__main__': raise SystemExit(main())
