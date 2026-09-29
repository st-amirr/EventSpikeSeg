"""TT gate-amplitude sweep for fixed-duration differential MOS synapse pulses."""
from __future__ import annotations
import json,re,subprocess,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'artifacts/analog_asic'; BENCH=OUT/'benches'; RES=OUT/'results'
COMMON='''.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
'''
def main():
  arg=lambda k,d: next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith(k+'=')),str(d))
  fractions=[float(v) for v in arg('--fractions','0,0.025,0.05,0.1,0.15,0.2,0.3,0.4,0.5,0.65,0.8,1').split(',')]
  width_ns=float(arg('--pulse-width-ns',10.5)); cap=float(arg('--membrane-cap-um',20)); pfull=float(arg('--p-gate-full-v',0.72)); nfull=float(arg('--n-gate-full-v',0.6)); wp=float(arg('--p-width-um',1.5)); wn=float(arg('--n-width-um',1)); length=float(arg('--injector-length-um',10)); step_ns=float(arg('--tstep-ns',2)); timeout=int(arg('--timeout-s',240))
  corner=arg('--mos-corner','tt'); temperature_c=float(arg('--temperature-c',27))
  if corner not in ('tt','ss','ff'): raise ValueError('MOS corner must be tt, ss or ff')
  if min(fractions)<0 or max(fractions)>1 or min(width_ns,cap,step_ns)<=0: raise ValueError('invalid sweep parameter')
  end_us=float(arg('--stop-us',1000)); initdiff=float(arg('--initial-differential-v',0)); initcm=float(arg('--initial-common-mode-v',0.9)); event_us=float(arg('--event-us',100)); measure_us=end_us-1.
  if not 0 < event_us < event_us+1 < measure_us: raise ValueError('stop must cover event and early/final measurements')
  cases=[('ref','z',0.0)]+[(f'{sign}{f:g}',sign,f) for f in fractions for sign in ('p','n')]
  lines=['SKY130 direct differential MOS fixed-duration gate-amplitude sweep',COMMON.replace('__tt.corner.spice',f'__{corner}.corner.spice'),f'.temp {temperature_c:g}','Vdd vdd 0 1.8','Vcm vcm 0 0.9',
    '.subckt diff_inject vp vn pp np pn nn vdd vss params: wp=1.5 wn=1 l=10',
    'Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}',
    'Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w={wn} l={l}',
    'Xp_neg vn pn vdd vdd sky130_fd_pr__pfet_01v8 w={wp} l={l}',
    'Xn_pos vp np vss vss sky130_fd_pr__nfet_01v8 w={wn} l={l}','.ends diff_inject']
  for name,sign,f in cases:
    vp=f'vp_{name}'; vn=f'vn_{name}'; pg=1.8-f*(1.8-pfull); ng=f*nfull
    lines += [f'Xmem_p_{name} {vp} vcm membrane_mim w_um={cap:g} l_um={cap:g}',f'Xmem_n_{name} {vn} vcm membrane_mim w_um={cap:g} l_um={cap:g}',f'.ic v({vp})={initcm+initdiff/2:g}',f'.ic v({vn})={initcm-initdiff/2:g}',f'.ic v(xmem_p_{name}.xmim.a)={initcm+initdiff/2:g}',f'.ic v(xmem_n_{name}.xmim.a)={initcm-initdiff/2:g}']
    gates={'pp':'1.8','pn':'1.8','np':'0','nn':'0'}
    if sign=='p': gates.update(pp=f'PWL(0 1.8 {event_us-.001:g}u 1.8 {event_us:g}u {pg:g} {event_us+width_ns/1000:g}u {pg:g} {event_us+width_ns/1000+.0001:g}u 1.8 {end_us:g}u 1.8)',nn=f'PWL(0 0 {event_us-.001:g}u 0 {event_us:g}u {ng:g} {event_us+width_ns/1000:g}u {ng:g} {event_us+width_ns/1000+.0001:g}u 0 {end_us:g}u 0)')
    elif sign=='n': gates.update(pn=f'PWL(0 1.8 {event_us-.001:g}u 1.8 {event_us:g}u {pg:g} {event_us+width_ns/1000:g}u {pg:g} {event_us+width_ns/1000+.0001:g}u 1.8 {end_us:g}u 1.8)',np=f'PWL(0 0 {event_us-.001:g}u 0 {event_us:g}u {ng:g} {event_us+width_ns/1000:g}u {ng:g} {event_us+width_ns/1000+.0001:g}u 0 {end_us:g}u 0)')
    for port,node,value in [('pp','pp',gates['pp']),('np','np',gates['np']),('pn','pn',gates['pn']),('nn','nn',gates['nn'])]: lines += [f'V{port}_{name} {node}_{name} 0 {value}']
    lines += [f'Xinj_{name} {vp} {vn} pp_{name} np_{name} pn_{name} nn_{name} vdd 0 diff_inject wp={wp:g} wn={wn:g} l={length:g}']
  lines += ['.control','set numdgt=15',f'tran {step_ns:g}n {end_us:g}u uic']
  for name,_,_ in cases: lines += [f'let diff_{name}=v(vp_{name})-v(vn_{name})',f'let cm_{name}=(v(vp_{name})+v(vn_{name}))/2',f'meas tran early_diff_{name} find diff_{name} at={event_us+1:g}u',f'meas tran final_diff_{name} find diff_{name} at={measure_us:g}u',f'meas tran early_cm_{name} find cm_{name} at={event_us+1:g}u',f'meas tran final_cm_{name} find cm_{name} at={measure_us:g}u']
  lines += ['quit','.endc','.end']; BENCH.mkdir(parents=True,exist_ok=True); RES.mkdir(parents=True,exist_ok=True)
  frac_hash=hashlib.sha1(','.join(f'{x:g}' for x in fractions).encode()).hexdigest()[:10]; tag=f'c{cap:g}_w{width_ns:g}n_pg{pfull:g}_ng{nfull:g}_wp{wp:g}_wn{wn:g}_l{length:g}_d{initdiff:g}v_cm{initcm:g}v_t{end_us:g}u_ev{event_us:g}u_n{len(fractions)}_fr{fractions[0]:g}-{fractions[-1]:g}_h{frac_hash}_step{step_ns:g}n_mos{corner}_temp{temperature_c:g}'
  deck=BENCH/f'sky130_ms_diff_gate_amplitude_{tag}.cir'; deck.write_text('\n'.join(lines)+'\n',encoding='utf-8')
  cmd=['docker','run','--rm','--memory','8g','--cpus','2','--volume',f'{ROOT}:/workspace:ro','--volume',f'{OUT}:/workspace/artifacts/analog_asic','--workdir','/workspace/artifacts/analog_asic/benches','--entrypoint','timeout','eventspikeseg:analog-ngspice36',str(timeout),'ngspice','-b',deck.name]
  proc=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout+15); log=proc.stdout+proc.stderr; (RES/f'sky130_ms_diff_gate_amplitude_{tag}.log').write_text(log,encoding='utf-8')
  m={(phase,node,case):float(val) for phase,node,case,val in re.findall(r'(?im)^\s*(early|final)_(diff|cm)_([\w.]+)\s*=\s*([-+0-9.eE]+)',log)}
  complete=proc.returncode==0 and len(m)==4*len(cases); results=[]
  if complete:
    for name,sign,f in cases:
      if sign=='z': continue
      row={'polarity':sign,'gate_magnitude_fraction':f,'p_gate_on_v':1.8-f*(1.8-pfull),'n_gate_on_v':f*nfull}
      for phase in ('early','final'):
        d=m[phase,'diff',name]-m[phase,'diff','ref']
        cm=m[phase,'cm',name]-m[phase,'cm','ref']
        row[f'{phase}_differential_change_mv']=d*1e3; row[f'{phase}_common_mode_change_mv']=cm*1e3
      results.append(row)
  report={'test':'sky130_differential_mos_fixed_width_gate_amplitude_sweep','simulation_completed':complete,'return_code':proc.returncode,'measurements':len(m),'mos_corner':corner,'temperature_c':temperature_c,'membrane_cap_square_width_um':cap,'pulse_width_ns':width_ns,'p_gate_full_magnitude_v':pfull,'n_gate_full_magnitude_v':nfull,'simulation_stop_us':end_us,'event_time_us':event_us,'event_transfer_by_gate_magnitude':results,'scope':'One fixed-duration isolated differential current event per case, measured after the event and near the end of the hold. Selected MOS corner and temperature, typical passive R/C/MIM; gate voltages are ideal sources, no analog weight storage/DAC, repeated events, readout, threshold/reset, supply corners, mismatch, noise, extraction, or network feedback.'}
  out=RES/f'sky130_ms_diff_gate_amplitude_{tag}.json'; out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'output':str(out),'simulation_completed':complete,'results':results},indent=2)); return 0 if complete else 2
if __name__=='__main__': raise SystemExit(main())


