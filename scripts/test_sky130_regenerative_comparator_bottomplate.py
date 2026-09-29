# Historical bottom-plate screen with incorrect switch order and an always-active latch; superseded by sampler-only and clock-gated screens.
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
      'Vsample_lo slo 0 PWL(0 0 10.9n 0 11n 1.8 59.9n 1.8 60n 0 300n 0)',
      'Vsample_lob slob 0 PWL(0 1.8 10.9n 1.8 11n 0 59.9n 0 60n 1.8 300n 1.8)',
      'Vreset reset 0 PWL(0 1.8 4.9n 1.8 5n 0 300n 0)','Vresetb resetb 0 PWL(0 0 4.9n 0 5n 1.8 300n 1.8)',
      '.subckt regen inp inn clk outp outn vdd vss params: win=2 tailw=4',
      'Xpre_p outp clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5','Xpre_n outn clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5',
      'Xlp outp outn vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5','Xln outp outn vss vss sky130_fd_pr__nfet_01v8 w=2 l=0.5',
      'Xrp outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5','Xrn outn outp vss vss sky130_fd_pr__nfet_01v8 w=2 l=0.5',
      'Xin_p outp inp tail vss sky130_fd_pr__nfet_01v8 w={win} l=0.5','Xin_n outn inn tail vss sky130_fd_pr__nfet_01v8 w={win} l=0.5',
      'Xtail tail clk vss vss sky130_fd_pr__nfet_01v8 w={tailw} l=1','.ends regen']
    outputs=[]
    for width in (10.0,30.0):
      for delta in (-3.0,0.0,3.0):
        tag=f'c{width:g}_d{delta:g}'.replace('-','m').replace('.','p')
        src=f'src_{tag}'; diff=f'diff_{tag}'; ret=f'ret_{tag}'; dum=f'dum_{tag}'; dret=f'dret_{tag}'
        lines += [f'Vsrc_{tag} {src} 0 {0.9+delta*1e-6:.12f}',f'Cmem_{tag} {src} vcm 20p',
          f'Xsampler_{tag} {src} vcm {diff} {ret} shi shib slo slob reset resetb vdd 0 vcm sky130_sc_diff_cap_sampler_bp sample_um={width:g}',
          f'Xdummy_{tag} vcm vcm {dum} {dret} shi shib slo slob reset resetb vdd 0 vcm sky130_sc_diff_cap_sampler_bp sample_um={width:g}',
          f'Xregen_{tag} {dum} {diff} clk op_{tag} on_{tag} vdd 0 regen win=2',f'Cloadp_{tag} op_{tag} 0 20f',f'Cloadn_{tag} on_{tag} 0 20f']
        outputs += [f'v(op_{tag})',f'v(on_{tag})',f'v({diff})',f'v({dum})']
    deck=BENCH/'sky130_regenerative_comparator_bottomplate.cir'; data='sky130_regenerative_comparator_bottomplate.dat'
    lines += ['.control','set wr_singlescale','set wr_vecnames','tran 0.2n 300n uic',f'wrdata ../results/{data} '+' '.join(outputs),'quit','.endc','.end']
    deck.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    cmd=['docker','run','--rm','--memory','4g','--cpus','2','--volume',f'{ROOT}:/workspace:ro','--volume',f'{OUT}:/workspace/artifacts/analog_asic','--workdir','/workspace/artifacts/analog_asic/benches','--entrypoint','timeout','eventspikeseg:analog-ngspice36','60','ngspice','-b',deck.name]
    run=subprocess.run(cmd,text=True,capture_output=True,timeout=75); log=run.stdout+run.stderr;(RES/'sky130_regenerative_comparator_bottomplate.log').write_text(log,encoding='utf-8')
    raw=[]; dat=RES/data
    if dat.exists():
      for ln in dat.read_text().splitlines()[1:]:
        try: raw.append([float(x) for x in ln.split()])
        except ValueError: pass
    report={'test':'sky130_regenerative_comparator_bottomplate_sampler','simulation_completed':run.returncode==0 and len(raw)>10,'return_code':run.returncode,'sample_cap_width_um':[10,30],'input_differential_uv':[-3,0,3],'sample_switch_open_ns':60,'evaluation_clock_edge_ns':100,'scope':'TT schematic, physical MIM sampler and PDK TGs, matched nominal dummy, ideal clamped membrane source, symmetric comparator; no source impedance, mismatch, sampled noise, PVT or extraction'}
    if report['simulation_completed']:
      for j,width in enumerate((10.,30.)):
        for k,delta in enumerate((-3.,0.,3.)):
          base=1+((j*3+k)*4); i90=min(range(len(raw)),key=lambda i:abs(raw[i][0]-90e-9)); i105=min(range(len(raw)),key=lambda i:abs(raw[i][0]-105e-9)); a=raw[i90]; b=raw[i105]; sampled=(a[base+2]-a[base+3])*1e6; diff=b[base]-b[base+1]
          report.setdefault('measurements',[]).append({'sample_cap_width_um':width,'input_differential_uv':delta,'pre_latch_input_diff_uv':sampled,'latch_output_diff_v':diff,'latch_polarity_matches_sampled_inputs':(diff>0)==(sampled<0) if abs(sampled)>1e-6 else None})
    (RES/'sky130_regenerative_comparator_bottomplate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); print(json.dumps(report,indent=2)); return 0 if report['simulation_completed'] else 1
if __name__=='__main__': raise SystemExit(main())
