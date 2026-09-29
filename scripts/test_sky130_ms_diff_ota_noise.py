"""Measure schematic OTA device noise and gain for the shared analog readout."""
from __future__ import annotations

import json
import math
import re
import subprocess
from bisect import bisect_right
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/analog_asic'


def main() -> int:
    corner, temp_c, bias_n, bias_p = 'tt', 27.0, 0.65, 0.75
    width_um, comp_ff = 2.0, 20.0
    noise_stop_hz = 1e7
    noise_start_hz = 1.0
    unity_buffer = False
    for arg in __import__('sys').argv[1:]:
        key, _, value = arg.partition('=')
        if key == '--mos-corner': corner = value
        elif key == '--temperature-c': temp_c = float(value)
        elif key == '--bias-n-v': bias_n = float(value)
        elif key == '--bias-p-v': bias_p = float(value)
        elif key == '--input-width-um': width_um = float(value)
        elif key == '--comp-cap-ff': comp_ff = float(value)
        elif key == '--noise-stop-hz': noise_stop_hz = float(value)
        elif key == '--noise-start-hz': noise_start_hz = float(value)
        elif key == '--unity-buffer': unity_buffer = value.lower() in ('1', 'true', 'yes')
    if (corner not in ('tt', 'ss', 'ff') or min(width_um, comp_ff, noise_start_hz) <= 0
            or noise_stop_hz <= noise_start_hz):
        raise ValueError('invalid MOS corner or nonpositive OTA geometry')
    tag = f'{corner}_temp{temp_c:g}_w{width_um:g}_cc{comp_ff:g}_f{noise_start_hz:g}-{noise_stop_hz:g}' + ('_unity' if unity_buffer else '')
    tag = tag.replace('.', 'p')
    signal_source = 'Vinn' if unity_buffer else 'Vinp'
    input_ac = ('Vinp inp 0 0.918', 'Vinn inn 0 0.918 AC 1') if unity_buffer else ('Vinp inp 0 0.918 AC 1', 'Vinn inn 0 0.918')
    bench = OUT / 'benches' / f'sky130_ms_diff_ota_noise_{tag}.cir'
    result = OUT / 'results' / f'sky130_ms_diff_ota_noise_{tag}.json'
    spectrum_path = OUT / 'results' / f'sky130_ms_diff_ota_noise_{tag}_spectrum.dat'
    log_path = OUT / 'results' / f'sky130_ms_diff_ota_noise_{tag}.log'
    bench.parent.mkdir(parents=True, exist_ok=True)
    result.parent.mkdir(parents=True, exist_ok=True)
    bench.write_text('\n'.join([
        f'SKY130 {corner.upper()} OTA input-referred device-noise screen',
        '.option scale=1u', f'.temp {temp_c:g}',
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        f'.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
        f'.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
        '.include "../../../asic/analog/sky130_sc_charge_integrator.spice"',
        'Vdd vdd 0 1.8', *input_ac,
        f'Vbn vbnn 0 {bias_n:g}', f'Vbp vbpp 0 {bias_p:g}',
        f'Xota {"out" if unity_buffer else "inp"} {"inn" if unity_buffer else "inn"} out vbnn vbpp vdd 0 sky130_sc_ota win={width_um:g} wn3=2 wp3=27.8 cc={comp_ff:g}f',
        'Rload out 0 1Meg', '.control', 'set numdgt=15',
        'ac dec 20 1 10Meg', 'let gainmag=mag(v(out))',
        'meas ac gain_1khz find gainmag at=1k',
        f'noise v(out) {signal_source} dec 20 {noise_start_hz:g} {noise_stop_hz:g}',
        'setplot noise1', 'set wr_singlescale', 'set wr_vecnames',
        f'wrdata ../results/{spectrum_path.name} frequency inoise_spectrum',
        'setplot noise2', 'print onoise_total inoise_total',
        'quit', '.endc', '.end']) + '\n', encoding='utf-8')
    cmd = ['docker', 'run', '--rm', '--memory', '4g', '--cpus', '2',
           '--volume', f'{ROOT}:/workspace:ro', '--volume', f'{OUT}:/workspace/artifacts/analog_asic',
           '--workdir', '/workspace/artifacts/analog_asic/benches', '--entrypoint', 'timeout',
           'eventspikeseg:analog-ngspice36', '90', 'ngspice', '-b', bench.name]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=105)
    log = run.stdout + run.stderr
    log_path.write_text(log, encoding='utf-8')
    gain = re.search(r'(?im)^\s*gain_1khz\s*=\s*([-+0-9.eE]+)', log)
    totals = {key:float(value) for key, value in re.findall(
        r'(?im)^\s*(onoise_total|inoise_total)\s*=\s*([-+0-9.eE]+)', log)}
    noise_table = []
    if spectrum_path.exists():
        for row in spectrum_path.read_text(encoding='utf-8').splitlines()[1:]:
            try:
                noise_table.append(tuple(map(float, row.split())))
            except ValueError:
                continue
    chop_residuals = {}
    boxcar_chop_residuals = {}
    aperture_noise = {}
    if len(noise_table) > 1:
        # The first two columns are frequency (ngspice wrdata repeats the scale).
        # For two instantaneous samples of one stationary process, Var(x2-x1)
        # = 2*integral(S(f)*(1-cos(2*pi*f*dt))) df for one-sided S.
        for spacing_us in (0.25, 0.5, 1.5, 5.0):
            dt = spacing_us * 1e-6
            area = 0.0
            for left, right in zip(noise_table, noise_table[1:]):
                f0, psd0 = left[0], left[2]**2
                f1, psd1 = right[0], right[2]**2
                y0 = 2.0 * psd0 * (1.0 - math.cos(2.0 * math.pi * f0 * dt))
                y1 = 2.0 * psd1 * (1.0 - math.cos(2.0 * math.pi * f1 * dt))
                area += 0.5 * (y0 + y1) * (f1 - f0)
            chop_residuals[f'{spacing_us:g}us'] = math.sqrt(max(area, 0.0))
        for spacing_us, aperture_us in ((1.5, 0.5), (1.5, 1.0), (3.0, 1.0)):
            dt, aperture = spacing_us * 1e-6, aperture_us * 1e-6
            area = 0.0
            for left, right in zip(noise_table, noise_table[1:]):
                f0, psd0 = left[0], left[2]**2
                f1, psd1 = right[0], right[2]**2
                def integrand(f, psd):
                    x = math.pi*f*aperture
                    boxcar = math.sin(x)/x if x else 1.0
                    return 4.0*psd*math.sin(math.pi*f*dt)**2*boxcar**2
                area += 0.5*(integrand(f0, psd0)+integrand(f1, psd1))*(f1-f0)
            boxcar_chop_residuals[f'{spacing_us:g}us_spacing_{aperture_us:g}us_aperture'] = math.sqrt(max(area, 0.0))
        for aperture_us in (1.0, 10.0, 100.0, 1000.0):
            aperture = aperture_us * 1e-6
            # The noise deck is logarithmic in frequency. A coarse trapezoid on
            # that grid aliases the sinc-squared aperture response at long T,
            # so interpolate the smooth PDK spectrum and integrate on a linear
            # grid with at least 20 samples per highest-frequency aperture lobe.
            f_start, f_stop = noise_table[0][0], noise_table[-1][0]
            step_hz = 1.0 / (20.0 * aperture)
            transition_hz = min(f_stop, max(f_start, 1.0/(10.0*aperture)))
            decades = max(0.0, math.log10(transition_hz/f_start))
            log_count = max(1, math.ceil(decades*500.0))
            log_grid = [f_start*(transition_hz/f_start)**(i/log_count) for i in range(log_count+1)]
            linear_count = max(1, math.ceil((f_stop-transition_hz)/step_hz))
            freq_grid = log_grid + [transition_hz+(f_stop-transition_hz)*i/linear_count
                                    for i in range(1, linear_count+1)]
            log_f = [math.log(row[0]) for row in noise_table]
            log_v = [math.log(max(row[2], 1e-300)) for row in noise_table]
            def aperture_integrand(freq):
                i = min(len(noise_table)-2, max(0, bisect_right(log_f, math.log(freq))-1))
                frac = (math.log(freq)-log_f[i])/(log_f[i+1]-log_f[i])
                amplitude = math.exp(log_v[i] + frac*(log_v[i+1]-log_v[i]))
                x = math.pi*freq*aperture
                boxcar = math.sin(x)/x if x else 1.0
                return amplitude*amplitude*boxcar*boxcar
            previous_f = freq_grid[0]
            previous_y = aperture_integrand(previous_f)
            area = 0.0
            for freq in freq_grid[1:]:
                value = aperture_integrand(freq)
                area += 0.5*(previous_y+value)*(freq-previous_f)
                previous_f, previous_y = freq, value
            single = math.sqrt(max(area, 0.0))
            aperture_noise[f'{aperture_us:g}us'] = {
                'single_buffer_v_rms': single,
                'two_independent_buffers_differential_v_rms': math.sqrt(2.0)*single,
            }
        def sampled_difference_noise(aperture_us, spacing_us):
            aperture = aperture_us*1e-6
            spacing = spacing_us*1e-6
            scale = max(aperture, spacing, 1e-12)
            f_start, f_stop = noise_table[0][0], noise_table[-1][0]
            transition_hz = min(f_stop, max(f_start, 1.0/(10.0*scale)))
            decades = max(0.0, math.log10(transition_hz/f_start))
            log_count = max(1, math.ceil(decades*500.0))
            log_grid = [f_start*(transition_hz/f_start)**(i/log_count) for i in range(log_count+1)]
            step_hz = 1.0/(20.0*scale)
            linear_count = max(1, math.ceil((f_stop-transition_hz)/step_hz))
            freq_grid = log_grid + [transition_hz+(f_stop-transition_hz)*i/linear_count
                                    for i in range(1, linear_count+1)]
            def value(freq):
                i = min(len(noise_table)-2, max(0, bisect_right(log_f, math.log(freq))-1))
                frac = (math.log(freq)-log_f[i])/(log_f[i+1]-log_f[i])
                amp = math.exp(log_v[i]+frac*(log_v[i+1]-log_v[i]))
                x = math.pi*freq*aperture
                boxcar = math.sin(x)/x if aperture and x else 1.0
                chop = 4.0*math.sin(math.pi*freq*spacing)**2 if spacing else 1.0
                return amp*amp*boxcar*boxcar*chop
            prev_f = freq_grid[0]
            prev_y = value(prev_f)
            area = 0.0
            for freq in freq_grid[1:]:
                y = value(freq)
                area += 0.5*(prev_y+y)*(freq-prev_f)
                prev_f, prev_y = freq, y
            return math.sqrt(max(area, 0.0))
        for spacing_us in (0.25, 0.5, 1.5, 5.0):
            chop_residuals[f'{spacing_us:g}us'] = sampled_difference_noise(0.0, spacing_us)
        for spacing_us, aperture_us in ((1.5, 0.5), (1.5, 1.0), (3.0, 1.0)):
            boxcar_chop_residuals[f'{spacing_us:g}us_spacing_{aperture_us:g}us_aperture'] = sampled_difference_noise(
                aperture_us, spacing_us)
    report = {'test':'sky130_physical_ota_ac_noise', 'simulation_completed':run.returncode == 0,
              'return_code':run.returncode, 'mos_corner':corner, 'temperature_c':temp_c,
              'ideal_bias_n_v':bias_n, 'ideal_bias_p_v':bias_p,
              'input_width_um':width_um, 'compensation_cap_ff':comp_ff,
              'gain_magnitude_1khz':float(gain.group(1)) if gain else None,
              'integrated_output_noise_v_rms':totals.get('onoise_total'),
              'integrated_input_noise_v_rms':totals.get('inoise_total'),
              'noise_spectrum_rows':len(noise_table),
              'noise_spectrum_first_last':([noise_table[0], noise_table[-1]] if noise_table else []),
              'noise_spectrum_file':str(spectrum_path.relative_to(ROOT)) if noise_table else None,
              'ideal_same_OTA_two_sample_difference_input_noise_v_rms_by_spacing':chop_residuals,
              'ideal_same_OTA_boxcar_averaged_chop_difference_input_noise_v_rms':boxcar_chop_residuals,
              'ideal_boxcar_sample_aperture_noise_v_rms':aperture_noise,
              'correlation_model_scope':('Stationary closed-loop buffer input-noise PSD; ideal boxcar aperture and same-amplifier sequential samples, without switch, settling or nonlinear effects. Estimates are not switched-circuit transient results.' if unity_buffer else 'Stationary open-loop input-noise PSD; ideal instantaneous same-OTA samples with no aperture, switch, gain-settling or nonlinear effects. This estimates common-noise rejection only and is not a switched-circuit noise result.'),
              'integration_band_hz':[noise_start_hz, noise_stop_hz],
              'scope':('PDK transistor noise for the schematic OTA in unity-feedback buffer configuration with ideal bias. This is closed-loop small-signal noise before transient sample-switch and MIM aperture effects; no offset/mismatch, layout parasitics, or full PLIF is included.' if unity_buffer else 'PDK transistor noise for the schematic OTA, open-loop, with ideal bias and sources. No MIM state, sampled threshold network, offset/mismatch, correlated noise, layout parasitics, or full PLIF is included.')}
    result.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if run.returncode == 0 else 2


if __name__ == '__main__':
    raise SystemExit(main())
