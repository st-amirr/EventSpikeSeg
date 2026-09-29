# Historical sampler screen with an always-active latch; its latch decision timing is invalid.
from __future__ import annotations
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/analog_asic'; BENCH=OUT/'benches'; RES=OUT/'results'

def main():
    rows=[]
    lines=['SKY130 TT regenerative comparator with physical differential MIM sampling caps',
      '.option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9',
      '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
      '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
      '.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38',
      '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
      '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
      '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
      '.include "../../../asic/analog/modules.spice"','.include "../../../asic/analog/sky130_ms_plif.spice"','Vdd vdd 0 1.8','Vcm vcm 0 0.9',
      'Vclk clk 0 PWL(0 0 99.9n 0 100n 1.8 300n 1.8)','Vclkb clkb 0 PWL(0 1.8 99.9n 1.8 100n 0 300n 0)',
      'Vsample sample 0 PWL(0 0 9.9n 0 10n 1.8 59.9n 1.8 60n 0 300n 0)',
      'Vsampleb sampleb 0 PWL(0 1.8 9.9n 1.8 10n 0 59.9n 0 60n 1.8 300n 1.8)',
      'Vreset reset 0 PWL(0 1.8 4.9n 1.8 5n 0 300n 0)','Vresetb resetb 0 PWL(0 0 4.9n 0 5n 1.8 300n 1.8)',
      '.subckt regen inp inn clk outp outn vdd vss params: win=2 tailw=4',
      'Xpre_p outp clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5','Xpre_n outn clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5',
      'Xlp outp outn vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5','Xln outp outn vss vss sky130_fd_pr__nfet_01v8 w=2 l=0.5',
      'Xrp outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5','Xrn outn outp vss vss sky130_fd_pr__nfet_01v8 w=2 l=0.5',
      'Xin_p outp inp tail vss sky130_fd_pr__nfet_01v8 w={win} l=0.5','Xin_n outn inn tail vss sky130_fd_pr__nfet_01v8 w={win} l=0.5',
      'Xtail tail clk vss vss sky130_fd_pr__nfet_01v8 w={tailw} l=1','.ends regen']
    outputs=[]
    for width in (5.0,10.0,20.0):
      for delta in (-6.0,-3.0,0.0,3.0,6.0):
        tag=f'c{width:g}_d{delta:g}'.replace('-','m').replace('.','p'); sourcep='srcp_'+tag; sourcen='srcn_'+tag; inp='inp_'+tag; inn='inn_'+tag
        # Source is ideal voltage clamped at a nominal membrane level; Cmem models source storage but not finite driver impedance.
        lines += [f'Vsrcp_{tag} {sourcep} 0 {0.9+delta*0.5e-6:.12f}',f'Vsrcn_{tag} {sourcen} 0 {0.9-delta*0.5e-6:.12f}',
          f'Cmem_p_{tag} {sourcep} vcm 20p',f'Cmem_n_{tag} {sourcen} vcm 20p',
          f'Xsamp_p_{tag} {inp} vcm membrane_mim w_um={width:g} l_um={width:g}',f'Xsamp_n_{tag} {inn} vcm membrane_mim w_um={width:g} l_um={width:g}',
          f'Xsample_p_{tag} {sourcep} {inp} sample sampleb vdd 0 transmission_gate',f'Xsample_n_{tag} {sourcen} {inn} sample sampleb vdd 0 transmission_gate',
          f'Xpre_p_{tag} {inp} vcm reset resetb vdd 0 transmission_gate',f'Xpre_n_{tag} {inn} vcm reset resetb vdd 0 transmission_gate',
          f'Xregen_{tag} {inp} {inn} clk op_{tag} on_{tag} vdd 0 regen win=2',f'Cloadp_{tag} op_{tag} 0 20f',f'Cloadn_{tag} on_{tag} 0 20f']
        outputs += [f'v(op_{tag})',f'v(on_{tag})',f'v({inp})',f'v({inn})']
    data='sky130_regenerative_comparator_sampled_interface.dat'; deck=BENCH/'sky130_regenerative_comparator_sampled_interface.cir'
    lines += ['.control','set wr_singlescale','set wr_vecnames','tran 0.2n 300n uic',f'wrdata ../results/{data} '+' '.join(outputs),'quit','.endc','.end']
    deck.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    cmd=['docker','run','--rm','--memory','4g','--cpus','2','--volume',f'{ROOT}:/workspace:ro','--volume',f'{OUT}:/workspace/artifacts/analog_asic','--workdir','/workspace/artifacts/analog_asic/benches','--entrypoint','timeout','eventspikeseg:analog-ngspice36','60','ngspice','-b',deck.name]
    run=subprocess.run(cmd,text=True,capture_output=True,timeout=75); log=run.stdout+run.stderr;(RES/'sky130_regenerative_comparator_sampled_interface.log').write_text(log,encoding='utf-8')
    dat=RES/data; raw=[]
    if dat.exists():
      for ln in dat.read_text().splitlines()[1:]:
        try: raw.append([float(x) for x in ln.split()])
        except ValueError: pass
    report={'test':'sky130_regenerative_comparator_physical_mim_sample_interface','simulation_completed':run.returncode==0 and len(raw)>10,'return_code':run.returncode,'sample_cap_width_um':[5,10,20],'input_differential_uv':[-6,-3,0,3,6],'sample_open_ns':60,'evaluation_edge_ns':100,'source_storage_cap_pf_per_leg':20.0,'scope':'TT schematic with physical MIM sampling capacitors and PDK transmission gates, but ideal DC-clamped membrane sources and clock; symmetric devices; no finite source impedance, mismatch, transient noise, parasitic extraction or PVT'}
    if report['simulation_completed']:
      for j,width in enumerate((5.,10.,20.)):
        for k,delta in enumerate((-6.,-3.,0.,3.,6.)):
          base=1+((j*5+k)*4); idx=min(range(len(raw)),key=lambda i:abs(raw[i][0]-105e-9)); r=raw[idx]; p,n,_,_=r[base:base+4]; idxs=min(range(len(raw)),key=lambda i:abs(raw[i][0]-90e-9)); rs=raw[idxs]; sp,sn=rs[base+2:base+4]
          report.setdefault('measurements',[]).append({'sample_cap_width_um':width,'input_differential_uv':delta,'sampled_input_diff_at_90ns_uv':(sp-sn)*1e6,'latch_output_diff_v':p-n,'correct_polarity':((p-n)>0)==(delta>0) if delta else None})
    (RES/'sky130_regenerative_comparator_sampled_interface.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); print(json.dumps(report,indent=2)); return 0 if report['simulation_completed'] else 1
if __name__=='__main__': raise SystemExit(main())
