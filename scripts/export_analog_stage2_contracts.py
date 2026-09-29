"""Stage 2: freeze model-to-circuit contracts and export representative stimuli.

Reads EventSpikeSeg140k quantized exports only. Does not run full-model simulation.
"""
from __future__ import annotations

import ast
import hashlib
import json
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASIC = ROOT / "artifacts/ASIC"
OUT = ROOT / "artifacts/analog_asic"
ASAP7 = OUT / "asap7"
STIM = ASAP7 / "stimuli"

BETA_FRAC = 23
THR_FRAC = 16
WEIGHT_FRAC = 16


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _decode_npy(payload: bytes):
    assert payload[:6] == b"\x93NUMPY"
    major = payload[6]
    if major == 1:
        hlen = struct.unpack("<H", payload[8:10])[0]
        hoff = 10
    else:
        hlen = struct.unpack("<I", payload[8:12])[0]
        hoff = 12
    meta = ast.literal_eval(payload[hoff : hoff + hlen].decode("latin1"))
    dtype = meta["descr"]
    shape = meta["shape"]
    body = payload[hoff + hlen :]
    if not isinstance(dtype, str):
        raise ValueError(f"unsupported dtype {dtype!r}")
    endian, kind, nbytes = dtype[0], dtype[1], int(dtype[2:])
    n = 1
    for s in shape:
        n *= max(int(s), 1)
    if n == 0:
        return [], shape, dtype
    if kind == "i" and nbytes == 4:
        fmt = ("<" if endian in "<|=" else ">") + "i" * n
        vals = struct.unpack(fmt, body[: 4 * n])
        return [v / float(2**WEIGHT_FRAC) for v in vals], shape, dtype
    if kind == "f" and nbytes == 4:
        fmt = ("<" if endian in "<|=" else ">") + "f" * n
        return list(struct.unpack(fmt, body[: 4 * n])), shape, dtype
    raise ValueError(f"unsupported array {dtype} {shape}")


def weight_ranges() -> dict:
    path = ASIC / "quantized_weights.npz"
    extremes = []
    wmin = wmax = None
    absmax = 0.0
    count = 0
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            floats, shape, dtype = _decode_npy(zf.read(name))
            if not floats:
                continue
            mn = min(floats)
            mx = max(floats)
            am = max(abs(mn), abs(mx))
            extremes.append(
                {
                    "key": name,
                    "min": mn,
                    "max": mx,
                    "absmax": am,
                    "count": len(floats),
                    "shape": list(shape),
                    "dtype": dtype,
                }
            )
            wmin = mn if wmin is None else min(wmin, mn)
            wmax = mx if wmax is None else max(wmax, mx)
            absmax = max(absmax, am)
            count += len(floats)
    extremes.sort(key=lambda x: x["absmax"], reverse=True)
    by_layer = {
        e["key"].removesuffix(".npy"): {
            "min": e["min"],
            "max": e["max"],
            "absmax": e["absmax"],
            "count": e["count"],
        }
        for e in extremes
    }
    return {
        "source": "artifacts/ASIC/quantized_weights.npz",
        "source_sha256": _sha(path),
        "format": "signed_Q7.16_in_24bit_export_contract_float_decode_/2^16",
        "weight_count_inspected": count,
        "executed_convolution_weights_spec": 143824,
        "min": wmin,
        "max": wmax,
        "absmax": absmax,
        "largest_abs_layers": extremes[:8],
        "per_layer": by_layer,
        "scaling_note": (
            "Per-tap weight absmax spans ~0.3..68 across layers; membrane thresholds "
            "are only ~0.29..0.77. Do not use one unproven volts/unit scale for every actor."
        ),
    }


def layer_parameter_ranges() -> dict:
    params_dir = ASIC / "parameters"
    layers = []
    beta_all = []
    thr_all = []
    inhib = []
    adapt_s = []
    adapt_d = []
    for path in sorted(params_dir.glob("*.json")):
        d = json.loads(path.read_text())
        betas = [x / 2**BETA_FRAC for x in d["beta_q"]]
        thrs = [x / 2**THR_FRAC for x in d["threshold_q"]]
        beta_all.extend(betas)
        thr_all.extend(thrs)
        row = {
            "file": str(path.relative_to(ASIC)).replace("\\", "/"),
            "channels": len(betas),
            "beta_min": min(betas),
            "beta_max": max(betas),
            "threshold_min": min(thrs),
            "threshold_max": max(thrs),
            "inhibition_enabled": bool(d.get("inhibition_enabled")),
            "threshold_adaptation_enabled": bool(d.get("threshold_adaptation_enabled")),
            "adaptation_kind": d.get("adaptation_kind"),
            "inhibition_kind": d.get("inhibition_kind"),
        }
        if d.get("inhibition_strength_q"):
            vals = [x / 2**THR_FRAC for x in d["inhibition_strength_q"]]
            row["inhibition_strength"] = vals
            inhib.extend(vals)
        if d.get("threshold_adaptation_strength_q"):
            vals = [x / 2**THR_FRAC for x in d["threshold_adaptation_strength_q"]]
            row["adaptation_strength"] = vals
            adapt_s.extend(vals)
        if d.get("adaptation_duration_q"):
            vals = [x / 2**THR_FRAC for x in d["adaptation_duration_q"]]
            row["adaptation_duration_bins"] = vals
            adapt_d.extend(vals)
        layers.append(row)
    return {
        "source": "artifacts/ASIC/parameters/*.json",
        "evidence": "Quantized digital export, not original float checkpoint tensors",
        "layer_count": len(layers),
        "beta": {"min": min(beta_all), "max": max(beta_all), "fraction_bits": BETA_FRAC},
        "threshold": {
            "min": min(thr_all),
            "max": max(thr_all),
            "fraction_bits": THR_FRAC,
            "units": "model_state_units_Q7.16",
        },
        "inhibition_strength": {
            "layers_enabled": sum(1 for x in layers if x["inhibition_enabled"]),
            "min": min(inhib) if inhib else None,
            "max": max(inhib) if inhib else None,
            "note": "stem peer_membrane only in 140k deploy graph",
        },
        "adaptation_strength": {
            "layers_enabled": sum(
                1 for x in layers if x["threshold_adaptation_enabled"]
            ),
            "min": min(adapt_s) if adapt_s else None,
            "max": max(adapt_s) if adapt_s else None,
        },
        "adaptation_duration_bins": {
            "min": min(adapt_d) if adapt_d else None,
            "max": max(adapt_d) if adapt_d else None,
        },
        "per_layer": layers,
    }


def plif_step(state: float, current: float, beta: float, threshold: float) -> dict:
    """ASIC-QAT ordinary PLIF without adaptation/inhibition.

    Matches export contract used by prepare_analog_asic / sampled_plif_reference:
    candidate = preleaked_state + current; spike if candidate >= theta;
    membrane = candidate - spike*theta; store beta*membrane for next bin.
    """
    candidate = state + current
    spike = int(candidate >= threshold)
    after_reset = candidate - spike * threshold
    preleaked = beta * after_reset
    return {
        "current": current,
        "candidate": candidate,
        "spike": spike,
        "after_reset": after_reset,
        "preleaked_next": preleaked,
    }


def build_stimuli(detail: dict) -> dict:
    beta0 = detail["beta_q"][0] / 2**BETA_FRAC
    thr0 = detail["threshold_q"][0] / 2**THR_FRAC
    # near-threshold channels for boundary cases
    thr_vals = [x / 2**THR_FRAC for x in detail["threshold_q"]]
    thr_idx = min(range(len(thr_vals)), key=lambda i: abs(thr_vals[i] - 0.4))
    beta_b = detail["beta_q"][thr_idx] / 2**BETA_FRAC
    thr_b = thr_vals[thr_idx]

    cases = {}

    def run(name: str, currents: list[float], beta: float, threshold: float, note: str):
        state = 0.0
        bins = []
        for i, cur in enumerate(currents):
            step = plif_step(state, cur, beta, threshold)
            bins.append({"bin": i, **step})
            state = step["preleaked_next"]
        cases[name] = {
            "module": "ordinary_sampled_plif",
            "actor": "detail_stem",
            "channel": 0 if beta == beta0 else thr_idx,
            "beta": beta,
            "threshold": threshold,
            "note": note,
            "bins": bins,
        }

    run(
        "silence",
        [0.0] * 8,
        beta0,
        thr0,
        "No synaptic charge; membrane remains at reset/hold; spike sequence all zeros",
    )
    run(
        "signed_cancellation",
        [0.25, -0.25, 0.18, -0.18, 0.4, -0.35, 0.05, -0.05],
        beta0,
        thr0,
        "Alternating signed charge cancels; verify bidirectional injection and no false spikes",
    )
    # threshold boundary: just below / just at / just above
    eps = 1e-6
    run(
        "threshold_boundaries",
        [thr_b - 0.05, thr_b - eps, thr_b, thr_b + eps, 0.0, -0.1, thr_b * 0.5, 0.0],
        beta_b,
        thr_b,
        "Boundary currents relative to learned threshold; inclusive >= compare",
    )
    run(
        "bursts",
        [0.55, 0.55, 0.55, 0.55, 0.0, 0.55, 0.55, 0.0],
        beta0,
        thr0,
        "Repeated strong positive charge and residual after subtractive reset",
    )
    run(
        "persistence",
        [0.15, 0.0, 0.0, 0.0, 0.12, 0.0, 0.0, 0.2],
        beta0,
        thr0,
        "Sparse charge with idle bins; state must persist under beta each completion",
    )
    run(
        "smoke_reference_currents",
        [0.0, 0.12, -0.08, 0.35, 0.04, -0.2, 0.5, 0.0],
        beta0,
        thr0,
        "Matches artifacts/analog_asic sampled_plif_reference / ideal_plif currents",
    )

    # synapse corner: signed weight * pulse multiplicity
    w_pos = 0.5
    w_neg = -0.25
    synapse = {
        "module": "signed_synapse",
        "note": "Ideal B-source placeholder semantics: pulse asserts weight addition once per event",
        "cases": [
            {"name": "silence", "pulses": [0, 0, 0, 0], "weight": w_pos, "charge": [0, 0, 0, 0]},
            {
                "name": "positive_burst",
                "pulses": [1, 1, 1, 0],
                "weight": w_pos,
                "charge": [w_pos, w_pos, w_pos, 0.0],
            },
            {
                "name": "negative_weight",
                "pulses": [1, 0, 1, 1],
                "weight": w_neg,
                "charge": [w_neg, 0.0, w_neg, w_neg],
            },
            {
                "name": "multiplicity_preserve",
                "pulses": [2, 1, 0, 3],
                "weight": w_pos,
                "charge": [2 * w_pos, w_pos, 0.0, 3 * w_pos],
                "note": "Decoder project2+x1 path must preserve coincident multiplicity",
            },
        ],
    }

    # readout: 16->6 signed current accumulate over 10 bins, first-index-tie argmax
    class_currents = [
        [0.1, 0.0, -0.05, 0.2, 0.0, 0.15, 0.0, 0.0, 0.05, 0.0],  # class0
        [0.0, 0.2, 0.0, 0.0, 0.1, 0.0, 0.05, 0.0, 0.0, 0.1],
        [0.05] * 10,
        [-0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0] * 10,
        [0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08],
    ]
    accum = [sum(seq) for seq in class_currents]
    best = max(accum)
    argmax = accum.index(best)  # first-index tie
    readout = {
        "module": "temporal_class_readout",
        "in_channels": 16,
        "out_classes": 6,
        "prediction_bins": 10,
        "tie_break": "first_index_argmax",
        "note": "No class PLIF; signed current only. 16-ch example collapsed to 6 accumulators for corner check",
        "per_class_bin_currents": class_currents,
        "accumulated": accum,
        "predicted_class": argmax,
    }

    # stem inhibition smoke: one location, 4 channels toy
    inhib_strength = 0.0141754150390625
    inhib = {
        "module": "peer_membrane_inhibition",
        "actor": "stem",
        "note": "Synchronous: keep simultaneous spikes, then subtract strength*RMS from non-spiking peers",
        "inhibition_strength": inhib_strength,
        "toy_channels": 4,
        "candidate": [0.6, 0.55, 0.2, -0.1],
        "spikes": [1, 1, 0, 0],
        "rms_energy": None,
        "peer_decrement": None,
    }
    cand = inhib["candidate"]
    # energy uses candidate with no adaptation penalty in this toy
    mean_sq = sum(c * c for c in cand) / len(cand)
    rms = (mean_sq + 1e-8) ** 0.5
    inhib["rms_energy"] = rms
    inhib["peer_decrement"] = inhib_strength * rms
    # Spikers keep post-reset membrane (toy uses 0); peers subtract strength*RMS.
    inhib["membrane_after_inhibition_only"] = [
        (c if s else c - inhib["peer_decrement"])
        for c, s in zip(cand, inhib["spikes"])
    ]

    return {
        "model": "EventSpikeSeg140k",
        "checkpoint": {"epoch": 80, "seed": 17, "architecture": "EventSpikeSeg140k"},
        "scope": "Small per-module SpikingJelly/export-equivalent stimuli; NOT full 31M-state simulation",
        "ordinary_plif": cases,
        "signed_synapse": synapse,
        "readout": readout,
        "peer_inhibition": inhib,
        "semantics_order": [
            "accumulate_all_synaptic_contributions_during_bin",
            "snapshot_state",
            "threshold_compare",
            "subtractive_reset_and_or_peer_inhibition",
            "update_triangular_adaptation_if_enabled",
            "apply_learned_beta_once",
            "hold_for_next_bin",
        ],
        "source_hashes": {
            "parameters/00_detail_stem.json": _sha(ASIC / "parameters/00_detail_stem.json"),
            "model_spec.yaml": _sha(ASIC / "model_spec.yaml"),
        },
    }


def circuit_contract(param_ranges: dict, weights: dict) -> dict:
    # Prototype uses 0.07 V per model unit at VDD=0.7 / vcm=0.35.
    # Full signed swing at that scale is +/-5 model units -> +/-0.35 V around vcm.
    # Export thresholds/weights are much smaller; do not force one scale for all layers.
    vdd = 0.7
    vcm = 0.35
    smoke_scale = 0.07
    thr_absmax = max(abs(param_ranges["threshold"]["min"]), abs(param_ranges["threshold"]["max"]))
    w_absmax = weights["absmax"]
    # Suggested shared-cell variants from inspected ranges (provisional, not sized)
    variants = [
        {
            "name": "plif_state_A",
            "intended_state_absmax": 1.0,
            "volts_per_state_unit_candidates": [0.05, 0.07, 0.1],
            "covers": "learned thresholds 0.286..0.766 and ordinary held membrane",
            "status": "provisional_unqualified",
        },
        {
            "name": "plif_state_B",
            "intended_state_absmax": 4.0,
            "volts_per_state_unit_candidates": [0.03, 0.05, 0.07],
            "covers": "short-term accumulation before threshold with multi-tap events",
            "status": "provisional_unqualified",
        },
        {
            "name": "synapse_inject_narrow",
            "weight_absmax_cover": 8.0,
            "covers": "majority of encoder/decoder layers with |w|<~8 after inspection",
            "status": "provisional_unqualified",
        },
        {
            "name": "synapse_inject_wide",
            "weight_absmax_cover": float(w_absmax),
            "covers": f"final_fuse.standard absmax={w_absmax:.3f}; may need DAC/attenuator variant",
            "status": "provisional_unqualified",
        },
    ]
    return {
        "schema_version": 1,
        "model": "EventSpikeSeg140k",
        "target": "ASAP7_analog_mixed_signal",
        "physical_layout_complete": False,
        "full_orfs_ready": False,
        "asap7_encoding": {
            "vdd_v": vdd,
            "vss_v": 0.0,
            "vcm_v": vcm,
            "bias_v_smoke": 0.3,
            "signed_representation": "single_ended_around_vcm_provisional",
            "voltage_to_state": {
                "smoke_prototype_volts_per_state_unit": smoke_scale,
                "smoke_note": "Used only by current ASAP7 sampled_plif behavioral benches; not a proven per-layer scale",
                "signed_voltage_span_at_smoke_scale_v": smoke_scale * 2 * 5.0,
                "headroom_note": "At 0.07 V/unit, |state|<=5 maps to [0,0.7] around 0.35 V midrail",
            },
            "export_numeric_formats": {
                "source": "artifacts/ASIC/model_spec.yaml quantization",
                "weight": "signed_Q7.16_24bit",
                "membrane": "signed_Q7.16_24bit",
                "threshold": "signed_Q7.16_24bit",
                "current_accumulator": "signed_Q15.16_32bit_combined",
                "beta": "unsigned_UQ1.23_24bit",
                "adaptation_age": "unsigned_6bit_integer_bins",
                "adaptation_amplitude": "unsigned_Q3.16_19bit",
                "adaptation_duration": "unsigned_Q5.16_21bit",
                "adaptation_strength": "unsigned_Q3.16_19bit",
                "inhibition_strength": "unsigned_Q3.16_19bit",
            },
            "inspected_ranges": {
                "beta": param_ranges["beta"],
                "threshold": param_ranges["threshold"],
                "inhibition_strength": param_ranges["inhibition_strength"],
                "adaptation_strength": param_ranges["adaptation_strength"],
                "adaptation_duration_bins": param_ranges["adaptation_duration_bins"],
                "weights": {
                    "min": weights["min"],
                    "max": weights["max"],
                    "absmax": weights["absmax"],
                    "count": weights["weight_count_inspected"],
                    "per_layer_absmax": {
                        k: v["absmax"] for k, v in weights["per_layer"].items()
                    },
                    "scaling_note": weights["scaling_note"],
                },
                "threshold_absmax_for_scaling": thr_absmax,
            },
            "shared_cell_variants_under_consideration": variants,
            "capacitor_options_f": {
                "under_consideration": [1e-12, 10e-12, 20e-12],
                "retention_5ms_ideal_c_one_stimulus": {
                    "1pF_drift_v": 0.015149,
                    "10pF_drift_v": 0.001590,
                    "20pF_drift_v": 0.000805,
                    "normalized_at_0p07_V_per_unit": {
                        "1pF": 0.2164,
                        "10pF": 0.02271,
                        "20pF": 0.01149,
                    },
                    "provisional_0p02_smoke": "only_20pF_met_for_that_stimulus",
                    "status": "ideal_C_only_not_physical_qualification",
                },
                "selection_rule": "Do not pick 20pF blindly; qualify area, leakage, temperature, corners, all state types",
            },
            "weight_programming": {
                "present_placeholder": "ideal_B_source_signed_current_injector",
                "required_physical": [
                    "weight_storage_or_DAC",
                    "bias_and_reference_distribution",
                    "pulse_or_charge_or_duration_coding_delivery",
                    "loading_and_shared_bus_accounting",
                ],
                "ppa_note": "Ideal B-source supply current is not valid physical synapse power",
            },
            "bias_and_references": {
                "smoke_bias_v": 0.3,
                "status": "external_ideal_sources_in_benches_only",
                "pending": "on_chip_bias_generation_and_distribution",
            },
        },
        "sampled_5ms_semantics": {
            "semantic_bin_s": 0.005,
            "prediction_window_bins_default": 10,
            "order": [
                "accumulate",
                "snapshot",
                "threshold",
                "reset_and_inhibition",
                "adaptation_update",
                "beta_once",
                "hold",
            ],
            "nonoverlapping_phases_required": True,
            "hold_spike_decision_across_commit": True,
            "software_forward_trace": {
                "source": "src/eventspikeseg/model_components.py HardwareLIF.forward / ParametricLIF",
                "asic_qat_order": [
                    "advance_triangular_adaptation_age",
                    "candidate = preleaked_or_combined_state + current",
                    "effective_threshold = base + adaptation_penalty (clamped)",
                    "spike = candidate >= threshold (competition gate optional)",
                    "membrane = candidate - spike*threshold (- loser decrement if winner_peer)",
                    "peer_membrane_inhibition on non-spiking peers if enabled",
                    "refresh triangular adaptation amplitude/age on spikes",
                    "membrane = membrane * learned_beta (once per completion)",
                ],
                "reset_convention": "subtractive_v_reset_None_subtract_threshold",
                "readout": "head.synapse 16_to_6 signed current over 10 bins; first-index-tie argmax; no class PLIF",
            },
            "continuous_time_note": "Continuous event-time leak is not bin-equivalent; any continuous substitute needs quantified error",
        },
        "acceptance_criteria": {
            "circuit_tolerances_provisional": {
                "smoke_max_state_error_model_units": 0.02,
                "label": "smoke_only",
                "not": "trained_model_accuracy_guarantee",
                "evidence": "ASAP7 sampled_plif_external max_state_error≈0.00897 with logistic placeholder compare",
            },
            "module_spike_state_criteria": {
                "spike_sequence_must_match_reference": True,
                "state_trajectory_max_abs_error_model_units": None,
                "status": "define_per_module_after_transistor_integration; smoke uses 0.02 as temporary gate only",
            },
            "workload_accuracy_claims": {
                "status": "unavailable",
                "limitation": "No analog-vs-SpikingJelly semantic mIoU campaign; use sensitivity estimates only and label them",
                "sensitivity_placeholder": "Not yet quantified; do not equate 0.02 state error to segmentation accuracy",
            },
        },
        "pending_physical": [
            {
                "id": "logistic_compare",
                "present": "scale-normalized logistic Btarget (k=2000 on model units) + capture track-hold",
                "required": "transistor comparator at VDD=0.7 with qualified offset/metastability",
            },
            {
                "id": "finite_gm_sense",
                "present": "30uA tanh sense to vcm, Rout=5k provisional driver",
                "required": "transistor sense buffer / isolation amp",
            },
            {
                "id": "ideal_C",
                "present": "ideal membrane/snapshot capacitors in netlist",
                "required": "qualified ASAP7 capacitor structure, area, leakage, extraction",
            },
            {
                "id": "B_source_synapses",
                "present": "ideal behavioral signed current injector",
                "required": "physical weight delivery (DAC/charge/pulse-duration) + storage",
            },
            {
                "id": "beta_target_driver",
                "present": "behavioral continuous target / 5k driver",
                "required": "switched-capacitor or amp beta scaling",
            },
            {
                "id": "reset_charge_subtraction",
                "present": "behavioral threshold subtract path",
                "required": "physical subtractive reset with feedthrough/control",
            },
            {
                "id": "adaptation_inhibition_energy",
                "present": "behavioral triangle/RMS/peer modules in SKY130 library",
                "required": "transistor or characterized helpers + digital glue cost if hybrid",
            },
            {
                "id": "readout_argmax",
                "present": "behavioral class integrator + argmax6",
                "required": "physical 16-to-6 accumulate and first-index-tie compare",
            },
            {
                "id": "phase_generator",
                "present": "external ideal clocks in ASAP7 external bench",
                "required": "on-chip nonoverlap phase generation and distribution",
            },
        ],
    }


def merge_into_design(contract: dict, param_ranges: dict) -> None:
    path = OUT / "design.yaml"
    design = json.loads(path.read_text())
    design["owner"] = "Grok_with_Codex_continuity"
    design["grok_role"] = "full_design_simulation_layout_ORFS_and_estimation"
    design["circuit_contract"] = {
        "stage": 2,
        "status": "frozen_provisional_for_sizing",
        "updated": "2026-09-23",
        "asap7_encoding": contract["asap7_encoding"],
        "sampled_5ms_semantics": contract["sampled_5ms_semantics"],
        "acceptance_criteria": contract["acceptance_criteria"],
    }
    design["asap7_encoding"] = contract["asap7_encoding"]
    design["pending_physical"] = contract["pending_physical"]
    design["parameter_ranges_inspected"] = {
        "beta": param_ranges["beta"],
        "threshold": param_ranges["threshold"],
        "inhibition_strength": param_ranges["inhibition_strength"],
        "adaptation_strength": param_ranges["adaptation_strength"],
        "adaptation_duration_bins": param_ranges["adaptation_duration_bins"],
        "evidence": param_ranges["evidence"],
    }
    design["stimuli"] = {
        "directory": "artifacts/analog_asic/asap7/stimuli",
        "manifest": "artifacts/analog_asic/asap7/stimuli/manifest.json",
    }
    design["timing"] = {
        "semantic_bin_s": 0.005,
        "commit": "accumulate, snapshot, threshold, reset/inhibition, adaptation, beta once, hold",
        "phases": "non-overlapping; hold spike decision across commit; external clocks in smoke only",
        "phase_controller_implemented": False,
    }
    design["asap7_status"] = (
        "stage2_contracts_frozen_provisional; physical_PLIF_and_ORFS_not_ready"
    )
    design["full_orfs_ready"] = False
    design["active_plan"] = "docs/ACTIVE_TASKS.md"
    path.write_text(json.dumps(design, indent=2) + "\n")


def main() -> None:
    STIM.mkdir(parents=True, exist_ok=True)
    detail = json.loads((ASIC / "parameters/00_detail_stem.json").read_text())
    param_ranges = layer_parameter_ranges()
    weights = weight_ranges()
    stimuli = build_stimuli(detail)
    contract = circuit_contract(param_ranges, weights)

    (ASAP7 / "circuit_contract.json").write_text(json.dumps(contract, indent=2) + "\n")
    (ASAP7 / "parameter_ranges.json").write_text(json.dumps(param_ranges, indent=2) + "\n")
    (ASAP7 / "weight_ranges.json").write_text(json.dumps(weights, indent=2) + "\n")

    # Split stimuli for Stage 6 reuse
    files = {}
    for name, case in stimuli["ordinary_plif"].items():
        p = STIM / f"ordinary_plif_{name}.json"
        p.write_text(json.dumps(case, indent=2) + "\n")
        files[name] = str(p.relative_to(OUT)).replace("\\", "/")
    for key in ("signed_synapse", "readout", "peer_inhibition"):
        p = STIM / f"{key}.json"
        p.write_text(json.dumps(stimuli[key], indent=2) + "\n")
        files[key] = str(p.relative_to(OUT)).replace("\\", "/")
    manifest = {
        "model": "EventSpikeSeg140k",
        "scope": stimuli["scope"],
        "semantics_order": stimuli["semantics_order"],
        "files": files,
        "combined": "asap7/stimuli/stimuli_bundle.json",
        "source_hashes": stimuli["source_hashes"],
    }
    (STIM / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (STIM / "stimuli_bundle.json").write_text(json.dumps(stimuli, indent=2) + "\n")

    merge_into_design(contract, param_ranges)
    summary = {
        "circuit_contract": "artifacts/analog_asic/asap7/circuit_contract.json",
        "design_yaml_updated": "artifacts/analog_asic/design.yaml",
        "stimuli_manifest": "artifacts/analog_asic/asap7/stimuli/manifest.json",
        "beta_range": param_ranges["beta"],
        "threshold_range": param_ranges["threshold"],
        "weight_absmax": weights["absmax"],
        "vdd": 0.7,
        "vcm": 0.35,
        "smoke_volts_per_state_unit": 0.07,
        "smoke_tolerance": 0.02,
        "pending_physical_count": len(contract["pending_physical"]),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
