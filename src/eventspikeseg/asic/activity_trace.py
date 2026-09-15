"""Checkpoint-provenanced actor vectors for RTL switching-activity replay."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .fixed_point import ASIC_FORMATS
from .integer_reference import IntegerPLIF


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file without loading it all into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _seal_trace_payload(trace: dict[str, Any]) -> None:
    """Refresh the digest after constructing or refining trace vectors."""

    payload = {key: value for key, value in trace.items() if key != "trace_payload_sha256"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    trace["trace_payload_sha256"] = hashlib.sha256(canonical).hexdigest()


def build_actor_trace(
    *,
    actor_name: str,
    layer: dict[str, Any],
    bins: list[dict[str, list[tuple[int, int, int]]]],
    checkpoint_sha256: str,
    model_spec_sha256: str,
    event_file_sha256: str,
    bin_duration_ms: int = 5,
) -> dict[str, Any]:
    """Select the busiest interior coordinate and encode exact per-bin vectors.

    A 1x1 spatial actor tile is translation invariant.  Selecting the coordinate
    with the most presynaptic spikes retains one real temporal state trajectory
    without pretending that a single coordinate represents whole-chip activity.
    """

    kernel = [int(value) for value in layer["kernel"]]
    stride = [int(value) for value in layer["stride"]]
    if stride != [1, 1]:
        raise ValueError("activity replay currently supports only stride-1 actors")
    input_channels = int(layer["in_channels"])
    output_channels = int(layer["out_channels"])
    input_h, input_w = (int(value) for value in layer["input_hw"])
    output_h, output_w = (int(value) for value in layer["output_hw"])
    pad_y, pad_x = (int(value) for value in layer["padding"])
    dilation_y, dilation_x = (int(value) for value in layer["dilation"])
    kernel_h, kernel_w = kernel
    halo_h = (kernel_h - 1) * dilation_y + 1
    halo_w = (kernel_w - 1) * dilation_x + 1
    coordinate_counts: Counter[tuple[int, int]] = Counter()
    for bin_trace in bins:
        for _, input_y, input_x in bin_trace["inputs"]:
            for kernel_y in range(kernel_h):
                output_y = input_y + pad_y - kernel_y * dilation_y
                if not 0 <= output_y < output_h:
                    continue
                halo_origin_y = output_y - pad_y
                if halo_origin_y < 0 or halo_origin_y + halo_h > input_h:
                    continue
                for kernel_x in range(kernel_w):
                    output_x = input_x + pad_x - kernel_x * dilation_x
                    if not 0 <= output_x < output_w:
                        continue
                    halo_origin_x = output_x - pad_x
                    if halo_origin_x < 0 or halo_origin_x + halo_w > input_w:
                        continue
                    coordinate_counts[(output_y, output_x)] += 1
    if not coordinate_counts:
        raise ValueError(f"{actor_name} trace contains no presynaptic events")
    # Counter.most_common tie order depends on insertion order.  Make selection
    # stable across worker counts and Python versions.
    selected_y, selected_x = min(
        coordinate_counts,
        key=lambda coordinate: (-coordinate_counts[coordinate], coordinate),
    )

    input_vectors: list[str] = []
    output_vectors: list[str] = []
    for bin_index, bin_trace in enumerate(bins, start=1):
        halo_origin_y = selected_y - pad_y
        halo_origin_x = selected_x - pad_x
        input_bits_seen = [
            channel * halo_h * halo_w
            + (y - halo_origin_y) * halo_w
            + (x - halo_origin_x)
            for channel, y, x in bin_trace["inputs"]
            if halo_origin_y <= y < halo_origin_y + halo_h
            and halo_origin_x <= x < halo_origin_x + halo_w
        ]
        if len(input_bits_seen) != len(set(input_bits_seen)):
            raise ValueError(
                f"{actor_name} bin {bin_index} has duplicate presynaptic events in the "
                f"halo at ({selected_y}, {selected_x}); bitmap replay would lose multiplicity"
            )
        output_channels_seen = [
            channel
            for channel, y, x in bin_trace["outputs"]
            if (y, x) == (selected_y, selected_x)
        ]
        if len(output_channels_seen) != len(set(output_channels_seen)):
            raise ValueError(
                f"{actor_name} bin {bin_index} has duplicate output channels at "
                f"({selected_y}, {selected_x})"
            )
        input_vector_width = input_channels * halo_h * halo_w
        if any(not 0 <= bit < input_vector_width for bit in input_bits_seen):
            raise ValueError(f"{actor_name} trace contains an out-of-range input bit")
        if any(not 0 <= channel < output_channels for channel in output_channels_seen):
            raise ValueError(f"{actor_name} trace contains an out-of-range output channel")
        input_vector = sum(1 << bit for bit in input_bits_seen)
        output_vector = sum(1 << channel for channel in output_channels_seen)
        input_vectors.append(f"{input_vector:0{(input_vector_width + 3) // 4}x}")
        output_vectors.append(f"{output_vector:0{(output_channels + 3) // 4}x}")

    trace = {
        "schema_version": "1.0.0",
        "scope": "single_coordinate_checkpoint_exact_integer_actor_trace",
        "actor": actor_name,
        "coordinate_yx": [selected_y, selected_x],
        "selection": "maximum_presynaptic_events_then_lexicographic_yx",
        "bins": len(bins),
        "bin_duration_ms": int(bin_duration_ms),
        "input_channels": input_channels,
        "input_width": halo_w,
        "input_height": halo_h,
        "input_vector_bits": input_channels * halo_h * halo_w,
        "output_channels": output_channels,
        "input_vectors_hex": input_vectors,
        "expected_output_vectors_hex": output_vectors,
        "selected_input_spikes": sum(
            int(value, 16).bit_count() for value in input_vectors
        ),
        "selected_output_spikes": sum(
            int(value, 16).bit_count() for value in output_vectors
        ),
        "checkpoint_sha256": checkpoint_sha256,
        "model_spec_sha256": model_spec_sha256,
        "event_file_sha256": event_file_sha256,
        "power_claim": False,
        "limitation": (
            "one real coordinate trajectory for actor-level VCD; "
            "not full-actor or full-chip activity"
        ),
    }
    _seal_trace_payload(trace)
    return trace


def apply_resident_ordinary_expectations(
    trace: dict[str, Any],
    *,
    layer: dict[str, Any],
    weights: Any,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Replace sparse-oracle outputs with one-bin resident PLIF commits.

    The event DAG records only destinations touched by a nonzero synaptic
    contribution.  A resident actor has a stronger clocking contract: every
    physical destination applies threshold/reset and beta at every completion,
    including bins with no new input.  A post-reset membrane may therefore emit
    again on an idle bin.  Derive the 1x1 tile's expected outputs directly from
    the saved input bitmaps so activity replay checks that resident contract.
    """

    if parameters.get("inhibition_enabled") or parameters.get(
        "threshold_adaptation_enabled"
    ):
        raise ValueError("ordinary resident expectations do not support mechanisms")
    kernel_h, kernel_w = (int(value) for value in layer["kernel"])
    input_channels = int(layer["in_channels"])
    output_channels = int(layer["out_channels"])
    groups = int(layer["groups"])
    if input_channels % groups or output_channels % groups:
        raise ValueError("resident trace channel counts must be divisible by groups")
    if int(trace["input_width"]) != kernel_w or int(trace["input_height"]) != kernel_h:
        raise ValueError("resident trace bitmap does not describe one full receptive field")
    if int(trace["input_channels"]) != input_channels:
        raise ValueError("resident trace input channel count does not match layer")
    if int(trace["output_channels"]) != output_channels:
        raise ValueError("resident trace output channel count does not match layer")

    inputs_per_group = input_channels // groups
    outputs_per_group = output_channels // groups
    betas = [int(value) for value in parameters["beta_q"]]
    thresholds = [int(value) for value in parameters["threshold_q"]]
    if len(betas) != output_channels or len(thresholds) != output_channels:
        raise ValueError("resident trace PLIF parameter count does not match layer")

    plif = IntegerPLIF()
    accumulators = [0] * output_channels
    output_vectors: list[str] = []
    hex_digits = (output_channels + 3) // 4
    current_format = ASIC_FORMATS["current"]
    for vector_hex in trace["input_vectors_hex"]:
        vector = int(vector_hex, 16)
        output_vector = 0
        for output_channel in range(output_channels):
            group = output_channel // outputs_per_group
            current = 0
            for local_input in range(inputs_per_group):
                input_channel = group * inputs_per_group + local_input
                for kernel_y in range(kernel_h):
                    for kernel_x in range(kernel_w):
                        tap = kernel_y * kernel_w + kernel_x
                        bit = input_channel * kernel_h * kernel_w + tap
                        if (vector >> bit) & 1:
                            try:
                                weight = weights[
                                    output_channel,
                                    local_input,
                                    kernel_y,
                                    kernel_x,
                                ]
                            except TypeError:
                                weight = weights[output_channel][local_input][kernel_y][kernel_x]
                            current = current_format.saturate(
                                current + int(weight)
                            )
            committed = plif.commit_combined_accumulator(
                accumulator_q=current_format.saturate(
                    accumulators[output_channel] + current
                ),
                beta_q=betas[output_channel],
                threshold_q=thresholds[output_channel],
            )
            accumulators[output_channel] = committed.next_accumulator
            output_vector |= committed.spike << output_channel
        output_vectors.append(f"{output_vector:0{hex_digits}x}")

    trace["expected_output_vectors_hex"] = output_vectors
    trace["selected_output_spikes"] = sum(
        int(value, 16).bit_count() for value in output_vectors
    )
    trace["expectation_semantics"] = "resident_all_destinations_commit_every_bin"
    _seal_trace_payload(trace)
    return trace


def build_pointwise_actor_trace(**kwargs: Any) -> dict[str, Any]:
    """Backward-compatible pointwise trace entry point."""

    layer = kwargs["layer"]
    if [int(value) for value in layer["kernel"]] != [1, 1]:
        raise ValueError("pointwise activity replay requires a 1x1 kernel")
    return build_actor_trace(**kwargs)


def write_actor_trace(path: Path, trace: dict[str, Any]) -> None:
    """Write a trace atomically so interrupted profiling cannot leave a valid-looking file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def validate_trace_payload(trace: dict[str, Any]) -> None:
    """Verify that vectors and metadata still match their creation-time digest."""

    expected = trace.get("trace_payload_sha256")
    payload = {key: value for key, value in trace.items() if key != "trace_payload_sha256"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    observed = hashlib.sha256(canonical).hexdigest()
    if expected != observed:
        raise ValueError(
            f"actor trace payload digest mismatch: expected={expected}, observed={observed}"
        )
