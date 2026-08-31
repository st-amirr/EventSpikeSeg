"""Derive exact logical actor-local memory requirements from an ASIC export."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bank_plan(depth: int, maximum_depth: int) -> dict[str, int]:
    bank_count = math.ceil(depth / maximum_depth)
    return {
        "maximum_bank_depth": maximum_depth,
        "bank_count": bank_count,
        "full_bank_count": depth // maximum_depth,
        "tail_bank_depth": depth % maximum_depth,
    }


def build_sram_manifest(
    export_directory: str | Path,
    *,
    maximum_bank_depth: int = 65_536,
) -> dict[str, Any]:
    """Build a technology-independent memory/banking manifest.

    The persistent state total reproduces the export's frozen 189.60 MiB contract.
    Collection current and touched metadata are reported separately because they are
    transient but still require a bounded physical implementation. No SRAM area or
    power is invented before a characterized macro catalog is supplied.
    """

    if maximum_bank_depth <= 0:
        raise ValueError("maximum_bank_depth must be positive")

    export_path = Path(export_directory)
    model_spec_path = export_path / "model_spec.yaml"
    spec = json.loads(model_spec_path.read_text(encoding="utf-8"))
    actors: list[dict[str, Any]] = []

    persistent_bits = 0
    collection_current_bits = 0
    touched_bitmap_bits = 0
    worst_case_queue_bits = 0
    rtl_actor_state_bits = 0
    rtl_queue_bits = 0
    rtl_spatial_marker_bits = 0
    rtl_state_bank_count = 0
    rtl_queue_bank_count = 0
    rtl_spatial_marker_bank_count = 0
    adaptation_states = 0
    weight_bits = 0

    for layer in spec["layers"]:
        depth = int(layer.get("logical_membrane_states", 0))
        if depth == 0:
            weight_bits += int(layer.get("weight_count", 0)) * 8
            continue

        parameters = json.loads(
            (export_path / layer["parameter_file"]).read_text(encoding="utf-8")
        )
        adaptation = bool(parameters["threshold_adaptation_enabled"])
        inhibition = bool(parameters["inhibition_enabled"])
        mechanism_enabled = adaptation or inhibition
        persistent_width = 16 + 24 + (32 if adaptation else 0)
        address_width = max(1, math.ceil(math.log2(depth)))
        actor_persistent_bits = depth * persistent_width
        spatial_depth = int(layer["output_hw"][0]) * int(layer["output_hw"][1])
        rtl_state_width = 24 + 16 + 24 + 2 + (
            32 if adaptation else (2 if inhibition else 0)
        )
        queue_depth = spatial_depth if mechanism_enabled else depth
        queue_address_width = max(1, math.ceil(math.log2(queue_depth)))
        actor_queue_bits = queue_depth * queue_address_width
        actor_marker_bits = spatial_depth if mechanism_enabled else 0
        state_banking = _bank_plan(depth, maximum_bank_depth)
        queue_banking = _bank_plan(queue_depth, maximum_bank_depth)
        marker_banking = (
            _bank_plan(spatial_depth, maximum_bank_depth) if mechanism_enabled else None
        )

        persistent_bits += actor_persistent_bits
        collection_current_bits += depth * 24
        touched_bitmap_bits += depth
        worst_case_queue_bits += depth * address_width
        rtl_actor_state_bits += depth * rtl_state_width
        rtl_queue_bits += actor_queue_bits
        rtl_spatial_marker_bits += actor_marker_bits
        rtl_state_bank_count += state_banking["bank_count"]
        rtl_queue_bank_count += queue_banking["bank_count"]
        if marker_banking is not None:
            rtl_spatial_marker_bank_count += marker_banking["bank_count"]
        weight_bits += int(layer["weight_count"]) * 8
        if adaptation:
            adaptation_states += depth

        actors.append(
            {
                "id": int(layer["id"]),
                "name": layer["name"],
                "depth": depth,
                "address_width_bits": address_width,
                "output_channels": int(layer["out_channels"]),
                "output_hw": layer["output_hw"],
                "adaptation_enabled": adaptation,
                "inhibition_enabled": inhibition,
                "persistent_record": {
                    "width_bits": persistent_width,
                    "fields": {
                        "membrane": 16,
                        "last_bin_tag": 24,
                        **(
                            {"adaptation_age": 16, "adaptation_amplitude": 16}
                            if adaptation
                            else {}
                        ),
                    },
                    "logical_bits": actor_persistent_bits,
                },
                "collection_record": {
                    "current_bits": 24,
                    "touched_bits": 1,
                    "semantics": "transient_same_bin_synaptic_sum_before_one_PLIF_commit",
                },
                "banking": state_banking,
                "rtl_packed_state": {
                    "width_bits": rtl_state_width,
                    "logical_bits": depth * rtl_state_width,
                    "fields": {
                        "current": 24,
                        "membrane": 16,
                        "last_bin_tag": 24,
                        "live": 1,
                        "touched": 1,
                        **(
                            {"adaptation_age": 16, "adaptation_amplitude": 16}
                            if adaptation
                            else (
                                {"unused_adaptation_placeholders": 2}
                                if inhibition
                                else {}
                            )
                        ),
                    },
                },
                "touched_queue": {
                    "depth": queue_depth,
                    "width_bits": queue_address_width,
                    "logical_bits": actor_queue_bits,
                    "banking": queue_banking,
                },
                "retinotopic_touched_marker": (
                    {
                        "depth": spatial_depth,
                        "width_bits": 1,
                        "logical_bits": actor_marker_bits,
                        "banking": marker_banking,
                    }
                    if mechanism_enabled
                    else None
                ),
                "weight_rom_words_int8": int(layer["weight_count"]),
            }
        )

    persistent_bytes = persistent_bits // 8
    capacity = spec["state_capacity"]
    if persistent_bytes != int(capacity["dense_exact_state_bytes"]):
        raise ValueError(
            "derived persistent state does not match model_spec state_capacity: "
            f"{persistent_bytes} != {capacity['dense_exact_state_bytes']}"
        )
    if adaptation_states != int(capacity["adaptation_enabled_neurons"]):
        raise ValueError("derived adaptation population does not match model_spec")
    if weight_bits // 8 != int(capacity["weight_bytes_int8"]):
        raise ValueError("derived weight ROM size does not match model_spec")

    combined_direct_bits = persistent_bits + collection_current_bits + touched_bitmap_bits
    total_bank_count = sum(actor["banking"]["bank_count"] for actor in actors)
    parallel_scrub_cycles = max(
        min(actor["depth"], maximum_bank_depth) for actor in actors
    )
    readout_layer = next(layer for layer in spec["layers"] if layer.get("kind"))
    readout_depth = int(readout_layer["output_hw"][0]) * int(readout_layer["output_hw"][1])
    readout_width = int(readout_layer["out_channels"]) * 24
    readout_bits = readout_depth * readout_width
    readout_banking = _bank_plan(readout_depth, maximum_bank_depth)
    residual_union_count = sum(
        join["kind"] == "binary_residual_or"
        for join in spec["graph"]["join_nodes"].values()
    )
    residual_max_events = 64
    residual_payload_width = 32
    residual_bits = residual_union_count * residual_max_events * residual_payload_width
    rtl_sram_bits = (
        rtl_actor_state_bits
        + rtl_queue_bits
        + rtl_spatial_marker_bits
        + readout_bits
        + residual_bits
    )
    return {
        "schema_version": "1.0.0",
        "source": {
            "model_spec": str(model_spec_path),
            "model_spec_sha256": _sha256(model_spec_path),
            "checkpoint": spec["checkpoint"],
        },
        "memory_contract": {
            "port": "synchronous_single_port_1RW",
            "read_write_same_cycle": "forbidden",
            "ownership": "one_permanent_PLIF_actor_owns_its_local_banks",
            "runtime_reconfiguration": False,
            "inter_actor_membrane_access": False,
            "sequence_start_initialization": "all_actor_banks_zeroized_in_parallel",
            "events_accepted_during_initialization": False,
        },
        "actors": actors,
        "totals": {
            "actor_count": len(actors),
            "logical_bank_count": total_bank_count,
            "logical_neurons": sum(actor["depth"] for actor in actors),
            "adaptation_enabled_neurons": adaptation_states,
            "persistent_state_bits": persistent_bits,
            "persistent_state_bytes": persistent_bytes,
            "persistent_state_mib": persistent_bytes / 2**20,
            "collection_current_bits": collection_current_bits,
            "collection_current_bytes": collection_current_bits // 8,
            "touched_bitmap_bits": touched_bitmap_bits,
            "touched_bitmap_bytes": touched_bitmap_bits // 8,
            "direct_index_exact_bits_excluding_queue": combined_direct_bits,
            "direct_index_exact_bytes_excluding_queue": math.ceil(combined_direct_bits / 8),
            "direct_index_exact_mib_excluding_queue": combined_direct_bits / 8 / 2**20,
            "worst_case_touched_queue_bits": worst_case_queue_bits,
            "worst_case_touched_queue_bytes": math.ceil(worst_case_queue_bits / 8),
            "weight_rom_bits": weight_bits,
            "weight_rom_bytes": weight_bits // 8,
            "parallel_bank_scrub_cycles": parallel_scrub_cycles,
            "parallel_bank_scrub_time_us_at_200MHz": parallel_scrub_cycles / 200,
            "rtl_actor_packed_state_bits": rtl_actor_state_bits,
            "rtl_touched_queue_bits": rtl_queue_bits,
            "rtl_retinotopic_marker_bits": rtl_spatial_marker_bits,
            "rtl_temporal_readout_bits": readout_bits,
            "rtl_residual_union_bits_at_default_capacity": residual_bits,
            "rtl_sram_bits_excluding_weight_rom": rtl_sram_bits,
            "rtl_sram_bytes_excluding_weight_rom": math.ceil(rtl_sram_bits / 8),
            "rtl_sram_mib_excluding_weight_rom": rtl_sram_bits / 8 / 2**20,
            "rtl_state_bank_count": rtl_state_bank_count,
            "rtl_queue_bank_count": rtl_queue_bank_count,
            "rtl_retinotopic_marker_bank_count": rtl_spatial_marker_bank_count,
            "rtl_readout_bank_count": readout_banking["bank_count"],
        },
        "shared_state": {
            "temporal_readout": {
                "depth": readout_depth,
                "width_bits": readout_width,
                "logical_bits": readout_bits,
                "banking": readout_banking,
            },
            "residual_unions": {
                "count": residual_union_count,
                "maximum_events_each": residual_max_events,
                "payload_width_bits": residual_payload_width,
                "logical_bits": residual_bits,
            },
        },
        "physical_status": {
            "macro_catalog_selected": False,
            "area_power_latency_available": False,
            "reason": "requires_characterized_SRAM_macro_catalog_and_activity_bound",
            "queue_note": (
                "A full-depth touched-address queue is the correctness upper bound; an article PPA "
                "result may use a smaller profiled FIFO only when overflow handling and the "
                "bound are reported."
            ),
        },
    }


def write_sram_manifest(
    export_directory: str | Path,
    output_path: str | Path | None = None,
    *,
    maximum_bank_depth: int = 65_536,
) -> Path:
    """Write the derived manifest and return its path."""

    export_path = Path(export_directory)
    destination = Path(output_path) if output_path else export_path / "sram_manifest.json"
    manifest = build_sram_manifest(export_path, maximum_bank_depth=maximum_bank_depth)
    destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return destination
