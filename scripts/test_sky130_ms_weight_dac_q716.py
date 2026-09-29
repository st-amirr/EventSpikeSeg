"""Bounded SKY130 23-bit Q7.16 weight-magnitude R-2R transfer probe.

This checks the generated weight DAC pins from the signed_int24_Q7.16 format;
it does not claim DAC ENOB or qualify MOS weight-injection current scaling.
"""
import json, math, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/analog_asic'; BENCH=OUT/'benches'; RES=OUT/'results'
VDD=1.8; VLO=0.9; VHI=1.8; MAX_CODE=1<<23; ERR_LIMIT=0.005
CODES=(0, 1<<16, 2<<16, 8<<16, 68<<16)
COMMON='''.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_r2r24.spice"
'''
def run_one(code):
    name=f'sky130_weight_q716_{code}'
    sources='\n'.join(f'Vw{i} w{i} 0 {VDD if (code>>i)&1 else 0}' for i in range(23))
    pins=' '.join(f'w{i}' for i in range(22,-1,-1))
    deck=f'''SKY130 Q7.16 weight magnitude R-2R code={code}\n{COMMON}
Vdd vdd 0 {VDD}
Vhi vhi 0 {VHI}
Vlo vlo 0 {VLO}
{sources}
Xmag vw {pins} vhi vlo vdd 0 weight_mag_vdac_u23
.control
op
print v(vw)
quit
.endc
.end
'''
    (BENCH/f'{name}.cir').write_text(deck)
    cmd=['docker','run','--rm','--memory','8g','--cpus','2','--volume',f'{ROOT}:/workspace:ro','--volume',f'{OUT}:/workspace/artifacts/analog_asic','--workdir','/workspace/artifacts/analog_asic/benches','--entrypoint','timeout','eventspikeseg:analog-ngspice36','30','ngspice','-b',f'{name}.cir']
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=45); log=p.stdout+p.stderr
    (RES/f'{name}.log').write_text(log)
    match=re.search(r'v\(vw\)\s*=\s*([-+0-9.eE]+)',log,re.I)
    v=float(match.group(1)) if match else None
    expect=VLO+(code/MAX_CODE)*(VHI-VLO)
    done=p.returncode==0 and v is not None and math.isfinite(v) and 'fatal' not in log.lower() and 'aborted' not in log.lower()
    return {'q716_magnitude':code/65536,'raw_magnitude_code':code,'expected_v':expect,'measured_v':v,'abs_error_v':abs(v-expect) if v is not None else None,'simulation_completed':done,'exit_code':p.returncode}
def main():
    BENCH.mkdir(parents=True,exist_ok=True); RES.mkdir(parents=True,exist_ok=True)
    rows=[run_one(c) for c in CODES]
    valid=[r for r in rows if r['simulation_completed']]
    mono=len(valid)==len(rows) and all(a['measured_v']<b['measured_v'] for a,b in zip(valid,valid[1:]))
    transfer=len(valid)==len(rows) and all(r['abs_error_v']<=ERR_LIMIT for r in valid)
    report={'architecture':'sky130_mixed_signal_signed_q716_weight_magnitude_dac','input_format':'unsigned_abs_value_from_signed_int24_Q7.16','weight_rails_v':[VLO,VHI],'r_ladder':'1k/2k ideal R; DAC-only switches m=100, SKY130 TT','max_transfer_error_limit_v':ERR_LIMIT,'results':rows,'monotonic_pass':mono,'coarse_transfer_pass':transfer,'analog_q716_precision_qualified':False,'injection_current_not_tested':True,'screen_pass':mono and transfer}
    (RES/'sky130_weight_q716_dac_screen.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2)); return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
