"""Isolate extracted MIM-state startup with and without the SKY130 OTA buffer."""
from __future__ import annotations
import json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH, RES = OUT / "benches", OUT / "results"
IMAGE = "eventspikeseg:analog-ngspice36"

def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True); RES.mkdir(parents=True, exist_ok=True)
    reports=[]
    for buffered in (False, True):
        mode="buffered" if buffered else "cap_only"
        stem=f"sky130_mim_pex_startup_tt_{mode}"
        deck=BENCH/f"{stem}.cir"; data=RES/f"{stem}.dat"
        lines=["SKY130 extracted MIM startup isolation "+mode,
          ".option scale=1u reltol=1e-6 abstol=1e-15 vntol=1e-9",
          '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
          '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
          '.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38',
          '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
          '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
          '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
          '.include "../../../asic/analog/sky130_sc_charge_integrator.spice"',
          '.include "../layout/sky130_mim_state_bank_square/mim_state_square_3x4_w30_l30.spice"',
          '.temp 27', 'Vdd vdd 0 1.8', 'Vcm vcm 0 0.9',
          'Xstate_p sigstate vcm mim_state_square_3x4_w30_l30',
          'Xstate_n refstate vcm mim_state_square_3x4_w30_l30',
          'Rcm_sig sigstate vcm 1e9', 'Rcm_ref refstate vcm 1e9',
          'Vinit_sig srcsig 0 0.900020', 'Vinit_ref srcref 0 0.900000',
          'Vinit_en init_en 0 PWL(0 1.8 1u 1.8 1.0001u 0 30u 0)',
          '.model init_sw sw ron=1 roff=1e30 vt=0.9 vh=0.1',
          'Sinit_sig sigstate srcsig init_en 0 init_sw',
          'Sinit_ref refstate srcref init_en 0 init_sw']
        vectors=['v(sigstate)','v(refstate)']
        if buffered:
            lines += ['Vbn vbnn 0 0.65','Vbp vbpp 0 0.75',
              'Xbufs bufs sigstate bufs vbnn vbpp vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f',
              'Xbufr bufr refstate bufr vbnn vbpp vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f',
              'Rbufs bufs vcm 1Meg','Rbufr bufr vcm 1Meg']
            vectors += ['v(bufs)','v(bufr)']
        lines += ['.control','set wr_singlescale','set wr_vecnames','tran 10n 30u uic',
                  'wrdata ../results/'+data.name+' '+' '.join(vectors),'quit','.endc','.end']
        deck.write_text('\n'.join(lines)+'\n',encoding='utf-8')
        cmd=['docker','run','--rm','--memory','4g','--cpus','2','--volume',f'{ROOT}:/workspace:ro',
             '--volume',f'{OUT}:/workspace/artifacts/analog_asic','--workdir','/workspace/artifacts/analog_asic/benches',
             '--entrypoint','timeout',IMAGE,'60','ngspice','-b',deck.name]
        run=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=75)
        log=run.stdout+run.stderr; (RES/f'{stem}.log').write_text(log,encoding='utf-8')
        rows=[]
        if data.exists():
            for row in data.read_text(encoding='utf-8').splitlines()[1:]:
                try: rows.append([float(x) for x in row.split()])
                except ValueError: pass
        complete=run.returncode==0 and len(rows)>10 and 'ngspice-36 done' in log.lower() and 'tran simulation(s) aborted' not in log.lower()
        report={'mode':mode,'simulation_completed':complete,'return_code':run.returncode,'samples':len(rows),
                'scope':'Two PEX 30um-square 12-unit MIM banks, one per state rail to VCM; explicit ±10uV source-switch initialization; 1G common-mode returns; with two PDK OTA followers' if buffered else 'Two PEX 30um-square 12-unit MIM banks, one per state rail to VCM; explicit ±10uV source-switch initialization; 1G common-mode returns; no active devices'}
        if complete:
            before=min(rows,key=lambda r:abs(r[0]-2e-6)); after=min(rows,key=lambda r:abs(r[0]-29e-6))
            report['state_diff_2us_uv']=(before[1]-before[2])*1e6
            report['state_diff_29us_uv']=(after[1]-after[2])*1e6
            report['state_change_uv']=report['state_diff_29us_uv']-report['state_diff_2us_uv']
            if buffered: report['buffer_diff_2us_uv']=(before[3]-before[4])*1e6
        (RES/f'{stem}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report)); reports.append(report)
    return 0 if all(r['simulation_completed'] for r in reports) else 1
if __name__=='__main__': raise SystemExit(main())
