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
        persistent_width = 16 + 24 + (32 if adaptation else 0)
        address_width = max(1, math.ceil(math.log2(depth)))
        actor_persistent_bits = depth * persistent_width

        persistent_bits += actor_persistent_bits
        collection_current_bits += depth * 24
        touched_bitmap_bits += depth
        worst_case_queue_bits += depth * address_width
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
                "inhibition_enabled": bool(parameters["inhibition_enabled"]),
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
                "banking": _bank_plan(depth, maximum_bank_depth),
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
