"""Bound sampled analog comparator-offset correction noise and MIM area."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts/analog_asic/results"
LAYOUT = ROOT / "artifacts/analog_asic/layout/sky130_mim_membrane_10x10/qualification.json"
MARGIN = RESULTS / "sky130_float_threshold_margin_distribution.json"
SENSOR_NOISE = RESULTS / "sky130_diff_sensor_noise_tt_1meg_size100.json"
SENSOR_SIZES = (10, 20, 100)


def main() -> int:
    kval = 1.380649e-23
    temp_k = 300.0
    inventory = 30_976_000
    qual = json.loads(LAYOUT.read_text(encoding="utf-8"))
    margin = json.loads(MARGIN.read_text(encoding="utf-8"))
    sensor_noise = json.loads(SENSOR_NOISE.read_text(encoding="utf-8"))
    cap_per_cell_f = float(qual["extracted_cv_f"])
    drawn_area_um2 = float(qual["device_geometry_um"]["w"]) * float(qual["device_geometry_um"]["l"])
    density_f_per_um2 = cap_per_cell_f / drawn_area_um2
    q01_uv = float(margin["all"]["absolute_margin_quantiles_mapped_uv"]["0.1"])
    cap_points = {}
    for target_uv in (q01_uv, 1.0, 6.0):
        target_v = target_uv * 1e-6
        # Independent equal capacitors have differential kT/C noise sqrt(2kT/C).
        cap_leg_f = 2 * kval * temp_k / target_v**2
        area_leg_um2 = cap_leg_f / density_f_per_um2
        area_pair_um2 = 2 * area_leg_um2
        cap_points[str(target_uv)] = {
            "target_differential_noise_uv_rms": target_uv,
            "required_capacitance_per_leg_f": cap_leg_f,
            "required_drawn_area_per_leg_mm2": area_leg_um2 / 1e6,
            "required_differential_pair_area_mm2_per_identity": area_pair_um2 / 1e6,
            "bare_cap_area_m2_for_inventory": area_pair_um2 * inventory / 1e12,
        }
    existing_cap_f = cap_per_cell_f
    existing_noise_uv = math.sqrt(2 * kval * temp_k / existing_cap_f) * 1e6
    observed_latch_eval_s = 2.6e-6
    decisions_per_s = inventory / 5e-3
    min_parallel_latches = math.ceil(decisions_per_s * observed_latch_eval_s)
    sensor_frontier = []
    for scale in SENSOR_SIZES:
        sensor_row = {str(fmax): json.loads((RESULTS / f"sky130_diff_sensor_noise_tt_{fmax}_size{scale}.json").read_text(encoding="utf-8"))
                      for fmax in ("100k", "1meg")}
        area_um2 = scale * (2 * 10 * 1 + 2 * 20 * 1) + 10 * 2
        sensor_frontier.append({
            "parallel_devices_per_side": scale,
            "input_noise_uv_rms_10hz_to_100khz": sensor_row["100k"]["integrated_input_noise_v_rms"] * 1e6,
            "input_noise_uv_rms_10hz_to_1mhz": sensor_row["1meg"]["integrated_input_noise_v_rms"] * 1e6,
            "bare_device_area_um2_per_latch": area_um2,
            "bare_device_area_mm2_at_ideal_min_parallelism": area_um2 * min_parallel_latches / 1e6,
            "layout_mux_bias_and_latch_included": False,
        })
    sensor_scale = int(sensor_noise["parallel_input_and_load_devices_per_side"])
    sensor_pvt = {corner: json.loads((RESULTS / f"sky130_diff_sensor_noise_{corner}_1meg_size20.json").read_text(encoding="utf-8"))
                  for corner in ("ss", "tt", "ff")}
    sensor_pvt_100 = {corner: json.loads((RESULTS / f"sky130_diff_sensor_noise_{corner}_1meg_size100.json").read_text(encoding="utf-8"))
                      for corner in ("ss", "tt", "ff")}
    # Bare active-device geometry for the screened matched diff pair, mirror
    # loads, and shared tail. Excludes taps, routing, bias, mux, and latch.
    sensor_area_per_latch_um2 = sensor_scale * (2 * 10 * 1 + 2 * 20 * 1) + 10 * 2
    sensor_bank_area_mm2 = sensor_area_per_latch_um2 * min_parallel_latches / 1e6
    report = {
        "test": "sky130_sampled_autozero_kTC_area_boundary",
        "temperature_k": temp_k,
        "logical_membrane_inventory": inventory,
        "mim_cap_density_f_per_um2_from_extracted_layout": density_f_per_um2,
        "measured_unit_mim_capacitance_f": existing_cap_f,
        "unit_mim_pair_analytic_differential_noise_uv_rms": existing_noise_uv,
        "full_float_q0p1_mapped_margin_uv": q01_uv,
        "requirements": cap_points,
        "shared_readout_service_lower_bound": {
            "membrane_decisions_per_5ms_bin": inventory,
            "required_decisions_per_second": decisions_per_s,
            "observed_latch_evaluation_time_s": observed_latch_eval_s,
            "minimum_parallel_latches_without_mux_or_control_overhead": min_parallel_latches,
            "state_reads_per_latch_per_bin_at_that_parallelism": inventory / min_parallel_latches,
            "candidate_sensor_noise_input_uv_rms_10hz_to_1mhz": sensor_noise["integrated_input_noise_v_rms"] * 1e6,
            "candidate_sensor_parallel_devices_per_side": sensor_scale,
            "candidate_sensor_bare_device_area_um2_per_latch": sensor_area_per_latch_um2,
            "candidate_sensor_bare_area_mm2_at_min_parallelism": sensor_bank_area_mm2,
            "20_device_sensor_pvt_input_noise_uv_rms_10hz_to_1mhz": {
                corner: row["integrated_input_noise_v_rms"] * 1e6
                for corner, row in sensor_pvt.items()
            },
            "100_device_sensor_pvt_input_noise_uv_rms_10hz_to_1mhz": {
                corner: row["integrated_input_noise_v_rms"] * 1e6
                for corner, row in sensor_pvt_100.items()
            },
            "candidate_sensor_area_scope": "First-order active-device geometry only; no taps, spacing, routing, bias generator, mux, latch, or physical layout.",
            "sensor_noise_area_frontier": sensor_frontier,
            "scope": "Throughput lower bound only; the2.6µs result is one ideal-trim latch transient, and this excludes mux settling, calibration, reset, event generation and graph dependencies."
        },
        "scope": "Analytic sampled thermal-noise lower bound using measured SKY130 MIM density and the existing mapped full-float margin quantile. Excludes switch noise, parasitics, mismatch, trim quantization, routing and active circuitry. Does not imply that decision-noise RMS must equal the q0.1 margin; it is a conservative comparison point, not a chosen error-rate requirement.",
        "interpretation": "Per-identity stored autozero on two independent MIM capacitors does not scale to the 30,976,000-state inventory at microvolt residuals. A 100-device differential sensor is a low-disturbance, about20uV/1MHz-noise readout candidate, but its bare sensor devices alone occupy about97mm2 at the ideal 16,108-latch throughput floor. Shared readout therefore has a concrete area/noise tradeoff and still needs mux, latch, bias, sampled-noise, mismatch, and layout qualification."
    }
    (RESULTS / "sky130_autozero_noise_area_boundary.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
