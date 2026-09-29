"""Bounded SKY130 PDK-capacitor storage screen (Docker ngspice only).

Pivots analog physical storage off ASAP7 MOS-Cgg (unqualified) onto SkyWater
devices that ship real capacitor models (MIM/VPP). Not a full-model encoding
change and not ASAP7 PPA.
"""
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/analog_asic'
BENCH = OUT / 'benches'
RES = OUT / 'results'
PDK = OUT / 'pdk/sky130_fd_pr'

# SKY130 smoke encoding for this storage screen only (existing prototype rails).
VDD = 1.8
VCM = 0.9
SCALE = 0.2  # volts per model unit (modules.spice default)
DRIFT_LIMIT_V = 0.02 * SCALE  # provisional 0.02-unit smoke
# Numerical floor: treat |I| below this as inconclusive for leakage-from-current.
I_FLOOR_A = 1e-18


def docker_ngspice(cir_name: str, timeout_s: int = 120) -> tuple[int, str]:
    cmd = [
        'docker', 'run', '--rm', '--memory', '2g', '--cpus', '2',
        '--volume', f'{ROOT}:/workspace:ro',
        '--volume', f'{OUT}:/workspace/artifacts/analog_asic',
        '--workdir', '/workspace/artifacts/analog_asic/benches',
        '--entrypoint', 'timeout', 'eventspikeseg:analog-ngspice36',
        str(timeout_s), 'ngspice', '-b', cir_name,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 30)
    log = result.stdout + result.stderr
    (RES / f'{Path(cir_name).stem}.log').write_text(log)
    return result.returncode, log


def write_bench():
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    # PDK MIM density/params from r+c lin corner; sized for ~20fF (camimc=2e-15 F/um^2).
    # w,l are in microns under .option scale=1u.
    (BENCH / 'sky130_mim_retention_5ms.cir').write_text(f'''SKY130 MIM capacitor 5ms hold + TG; PDK cap_mim model density
.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param
+ m4_dw = 0
+ tol_m4 = 0
+ tc1rm4 = 0
+ tc2rm4 = 0
+ tc1rvia4 = 0
+ tc2rvia4 = 0
+ rm4 = 0.047
+ rcvia4 = 0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"

Vdd vdd 0 {VDD}
Vcm vcm 0 {VCM}
Vin input 0 PWL(0 1.1 2u 1.1 2.001u 0.7 5.002m 0.7)
Vsample sample 0 PWL(0 {VDD} 1u {VDD} 1.001u 0 5.002m 0)
Xinv sample sample_b vdd 0 inv
Xsw input state sample sample_b vdd 0 transmission_gate
* ~20pF at camimc=2e-15 F/um^2 => area ~1e4 um^2 (w=l=100); PDK MIM subckt
Xmim state vcm sky130_fd_pr__cap_mim_m3_2 w=100 l=100 mf=1
.control
set wr_singlescale
set wr_vecnames
tran 1u 5.002m 0 1u
wrdata ../results/sky130_mim_retention_5ms.dat v(state) v(input) i(Vdd)
quit
.endc
.end
''')


def analyze(rows):
    if not rows:
        return dict(simulation_completed=False)
    initial = min(rows, key=lambda r: abs(r[0] - 1.1e-6))[1]
    final = rows[-1][1]
    drift = final - initial
    rate = drift / 0.005
    return dict(
        simulation_completed=rows[-1][0] >= 5.002e-3 * 0.999,
        hold_start_v=initial,
        hold_end_v=final,
        hold_drift_v=drift,
        hold_drift_rate_v_per_s=rate,
        normalized_model_drift=drift / SCALE,
        volts_per_unit=SCALE,
        provisional_0_02_unit_retention_pass=abs(drift) < DRIFT_LIMIT_V,
        device='sky130_fd_pr__cap_vpp_08p6x07p8_l1m1m2_noshield',
        caveat='SKY130 PDK VPP schematic model + TG; not extracted; not ASAP7',
    )


def main():
    write_bench()
    dat = RES / 'sky130_mim_retention_5ms.dat'
    if dat.exists():
        dat.unlink()
    code, log = docker_ngspice('sky130_mim_retention_5ms.cir', timeout_s=180)
    rows = []
    if dat.is_file():
        rows = [[float(x) for x in line.split()] for line in dat.read_text().splitlines()[1:] if line.strip()]
    abort = 'aborted' in log.lower() or 'timestep too small' in log.lower()
    ok = code == 0 and bool(rows) and rows[-1][0] >= 5.002e-3 * 0.999 and not abort
    report = dict(bench='sky130_mim_retention_5ms', simulation_completed=ok, exit_code=code)
    if ok:
        report.update(analyze(rows))
        report['device'] = 'sky130_fd_pr__cap_mim_m3_2 w=l=100um (~20pF at camimc=2e-15 F/um^2)'
    else:
        for line in log.splitlines():
            low = line.lower()
            if 'error' in low or 'unable' in low or 'no such' in low or 'undefined' in low or 'timestep' in low:
                report['failure_hint'] = line.strip()
                break
    out = dict(
        architecture_pivot='sky130_pdk_mim_capacitor_storage',
        asap7_mos_cgg='rejected_unqualified',
        deferred=['ideal_leakage_servo_compensation', 'asap7_same_family_mos_sweeps', 'powered_ota_integrator_as_first_storage'],
        pass_metric=f'|drift| < {DRIFT_LIMIT_V} V over 5ms (=0.02 model units at {SCALE} V/unit)',
        result=report,
    )
    (RES / 'sky130_storage_screen.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(report))
    print('wrote', RES / 'sky130_storage_screen.json')
    return 0 if ok and report.get('provisional_0_02_unit_retention_pass') else 2


if __name__ == '__main__':
    raise SystemExit(main())
