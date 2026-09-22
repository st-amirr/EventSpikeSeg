#!/usr/bin/env python3
"""Legacy offline capacity analysis for an already-supplied activity profile.

This script is retained for historical physical-capacity studies. It is not
part of the active ASIC flow and must not be used to launch or require a new
full-model simulation/profile. Current power uses routed per-block activity.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _mechanism_enabled(export: Path, layer: dict[str, Any]) -> bool:
    parameters = json.loads(
        (export / str(layer["parameter_file"])).read_text(encoding="utf-8")
    )
    return bool(parameters.get("inhibition_enabled", False)) or bool(
        parameters.get("threshold_adaptation_enabled", False)
    )


def _lane_factorization(
    required_lanes: int,
    *,
    channels: int,
    spatial_destinations: int,
    mechanism_enabled: bool,
) -> tuple[int, int]:
    """Choose legal interleaved lane factors meeting a scalar work quotient."""
    required_lanes = max(1, required_lanes)
    if mechanism_enabled:
        channel_lanes = 1
    else:
        channel_lanes = min(channels, required_lanes)
    spatial_lanes = math.ceil(required_lanes / channel_lanes)
    if spatial_lanes > spatial_destinations:
        raise ValueError("requested lanes exceed the logical PLIF population")
    return channel_lanes, spatial_lanes


def _completion_token_critical_path(
    graph: dict[str, Any], actor_commit_cycles: dict[str, int]
) -> tuple[int, list[str]]:
    """Return the strict same-bin commit dependency floor through the DAG.

    An actor may collect currents while its predecessors are active, but it cannot
    start its PLIF commit until every required predecessor completion token has
    arrived.  Routing and FIFO delay are deliberately assigned zero cycles here,
    making this a lower bound rather than a cycle-accurate schedule.
    """
    edges = list(graph["edges"])
    incoming: dict[str, list[str]] = {}
    for edge in edges:
        incoming.setdefault(str(edge["destination"]), []).append(str(edge["source"]))
    arrival = {"input": 0}
    predecessor: dict[str, str] = {}
    for node in graph["node_topological_order"]:
        name = str(node)
        if name == "input":
            continue
        sources = incoming.get(name, [])
        if sources:
            critical_source = max(sources, key=lambda source: arrival[source])
            predecessor[name] = critical_source
            upstream = arrival[critical_source]
        else:
            upstream = 0
        arrival[name] = upstream + actor_commit_cycles.get(name, 0)

    endpoint = "prediction" if "prediction" in arrival else str(
        graph["node_topological_order"][-1]
    )
    path = [endpoint]
    while path[-1] in predecessor:
        path.append(predecessor[path[-1]])
    path.reverse()
    return arrival[endpoint], path


def _derive_edge_traffic(
    profile: dict[str, Any], graph: dict[str, Any]
) -> list[dict[str, Any]]:
    """Derive exact one-bin data/token volume on every static graph edge."""
    if int(profile["bins_profiled"]) != 1:
        raise ValueError("edge traffic derivation currently requires exactly one bin")
    kinds = {str(node["name"]): str(node["kind"]) for node in graph["nodes"]}
    incoming: dict[str, list[dict[str, Any]]] = {}
    for edge in graph["edges"]:
        incoming.setdefault(str(edge["destination"]), []).append(edge)
    actor_spikes = profile["actor_output_spikes"]
    actor_inputs = profile["actor_input_events"]
    residual_counts = profile["maximum_residual_events_by_join"]
    node_events: dict[str, int] = {"input": int(profile["input_events"])}

    for raw_name in graph["node_topological_order"]:
        name = str(raw_name)
        if name == "input":
            continue
        sources = [str(edge["source"]) for edge in incoming.get(name, [])]
        input_count = sum(node_events[source] for source in sources)
        kind = kinds[name]
        if kind == "plif_actor":
            if input_count != int(actor_inputs[name]):
                raise ValueError(
                    f"{name} graph input count {input_count} does not conserve profiled "
                    f"actor input count {actor_inputs[name]}"
                )
            node_events[name] = int(actor_spikes[name])
        elif kind == "nearest_event_fanout_2x":
            node_events[name] = 4 * input_count
        elif kind == "binary_residual_or":
            node_events[name] = int(residual_counts[name])
        elif kind in {
            "channel_concat",
            "multiplicity_preserving_sum",
            "routing",
            "current_readout",
        }:
            node_events[name] = input_count
        elif kind == "semantic_output":
            node_events[name] = 0
        else:
            raise ValueError(f"unsupported node kind for edge traffic: {name}={kind}")

    return [
        {
            "edge_index": index,
            "source": str(edge["source"]),
            "destination": str(edge["destination"]),
            "data_events": node_events[str(edge["source"])],
            "completion_tokens": 1,
            "total_packets": node_events[str(edge["source"])] + 1,
            "generated_FIFO_present": str(edge["destination"]) != "prediction",
        }
        for index, edge in enumerate(graph["edges"])
    ]


def analyze(
    profile_path: Path,
    model_spec_path: Path,
    *,
    clock_mhz: float,
    bin_us: float,
    target_utilization: float = 0.8,
) -> dict[str, Any]:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    spec = json.loads(model_spec_path.read_text(encoding="utf-8"))
    if profile.get("bins_profiled") != 1:
        raise ValueError("the current RTL service bound requires exactly one profiled bin")
    if clock_mhz <= 0 or bin_us <= 0 or not 0 < target_utilization <= 1:
        raise ValueError(
            "clock_mhz and bin_us must be positive and utilization in (0, 1]"
        )

    export = model_spec_path.parent / str(spec.get("artifact_root", "."))
    layers = {str(layer["name"]): layer for layer in spec["layers"]}
    contributions = profile["actor_synaptic_contributions"]
    touched = profile["maximum_touched_queue_entries_by_actor"]
    spikes = profile["actor_output_spikes"]
    cycles_available = clock_mhz * bin_us
    actors: dict[str, dict[str, Any]] = {}
    profiled_bank_activity = profile.get("bank_activity")
    isolated_collection = profile.get(
        "maximum_isolated_saturated_collection_cycles_by_actor"
    )

    for name in spec["graph"]["actor_topological_order"]:
        layer = layers[name]
        contribution_count = int(contributions[name])
        touched_count = int(touched[name])
        spike_count = int(spikes[name])
        channels = int(layer["out_channels"])
        output_h, output_w = (int(value) for value in layer["output_hw"])
        spatial_destinations = output_h * output_w
        mechanism = _mechanism_enabled(export, layer)
        if mechanism:
            # CONTRIBUTION_* uses at least five cycles per addition and one
            # extra cycle when first marking a spatial location. A mechanism
            # commit reads and writes every channel at a touched location.
            collection_cycles = 5 * contribution_count + touched_count
            commit_cycles = touched_count * (3 * channels + 6) + spike_count
        else:
            # The single 1RW contribution lane accepts one addition every
            # three clocks. Queue/state/PLIF commit needs at least eight.
            collection_cycles = 3 * contribution_count
            commit_cycles = 8 * touched_count + spike_count
        serial_floor = collection_cycles + commit_cycles
        deadline_lanes = math.ceil(serial_floor / cycles_available)
        target_lanes = math.ceil(
            serial_floor / (cycles_available * target_utilization)
        )
        channel_lanes, spatial_lanes = _lane_factorization(
            target_lanes,
            channels=channels,
            spatial_destinations=spatial_destinations,
            mechanism_enabled=mechanism,
        )
        actor_result = {
            "mechanism_enabled": mechanism,
            "output_channels": channels,
            "synaptic_contributions": contribution_count,
            "touched_entries": touched_count,
            "output_spikes": spike_count,
            "collection_cycle_floor": collection_cycles,
            "commit_cycle_floor": commit_cycles,
            "serial_actor_cycle_floor": serial_floor,
            "serial_actor_latency_us_floor": serial_floor / clock_mhz,
            "ideal_independent_lane_count_floor_for_deadline": deadline_lanes,
            "ideal_independent_lane_count_floor_for_target": target_lanes,
            "provisional_channel_lane_count": channel_lanes,
            "provisional_spatial_lane_count": spatial_lanes,
            "provisional_physical_lane_count": channel_lanes * spatial_lanes,
        }
        if isinstance(profiled_bank_activity, dict):
            bank = profiled_bank_activity[name]
            bank_contributions = [int(value) for value in bank["synaptic_contributions"]]
            bank_touched = [int(value) for value in bank["maximum_touched_entries"]]
            bank_spikes = [int(value) for value in bank["output_spikes"]]
            if not (
                len(bank_contributions) == len(bank_touched) == len(bank_spikes)
            ):
                raise ValueError(f"{name} bank activity arrays have different lengths")
            if sum(bank_contributions) != contribution_count:
                raise ValueError(f"{name} bank contributions do not conserve activity")
            if sum(bank_touched) != touched_count:
                raise ValueError(f"{name} bank touches do not conserve activity")
            if sum(bank_spikes) != spike_count:
                raise ValueError(f"{name} bank spikes do not conserve activity")
            bank_cycles = []
            bank_collection_cycles = []
            bank_commit_cycles = []
            for contributions_in_bank, touched_in_bank, spikes_in_bank in zip(
                bank_contributions, bank_touched, bank_spikes
            ):
                if mechanism:
                    bank_collection = 5 * contributions_in_bank + touched_in_bank
                    bank_commit = touched_in_bank * (3 * channels + 6) + spikes_in_bank
                else:
                    bank_collection = 3 * contributions_in_bank
                    bank_commit = 8 * touched_in_bank + spikes_in_bank
                bank_collection_cycles.append(bank_collection)
                bank_commit_cycles.append(bank_commit)
                bank_cycles.append(bank_collection + bank_commit)
            configured_floor = max(bank_cycles, default=0)
            profiled_channel_lanes = int(bank["channel_lanes"])
            profiled_spatial_lanes = int(bank["spatial_lanes"])
            refined_spatial_lanes = max(
                1,
                math.ceil(
                    profiled_spatial_lanes
                    * configured_floor
                    / (cycles_available * target_utilization)
                ),
            )
            refined_spatial_lanes = min(
                refined_spatial_lanes, spatial_destinations
            )
            actor_result.update(
                {
                    "profiled_physical_lane_count": len(bank_cycles),
                    "profiled_channel_lane_count": profiled_channel_lanes,
                    "profiled_spatial_lane_count": profiled_spatial_lanes,
                    "profiled_maximum_bank_collection_cycle_floor": max(
                        bank_collection_cycles, default=0
                    ),
                    "profiled_maximum_bank_commit_cycle_floor": max(
                        bank_commit_cycles, default=0
                    ),
                    "profiled_maximum_bank_cycle_floor": configured_floor,
                    "profiled_maximum_bank_latency_us_floor": (
                        configured_floor / clock_mhz
                    ),
                    "profiled_maximum_bank_utilization_floor": (
                        configured_floor / cycles_available
                    ),
                    "profiled_bank_cycle_imbalance": (
                        max(bank_cycles) / (sum(bank_cycles) / len(bank_cycles))
                        if bank_cycles and sum(bank_cycles)
                        else 0.0
                    ),
                    "refined_channel_lane_count": profiled_channel_lanes,
                    "refined_spatial_lane_count": refined_spatial_lanes,
                    "refined_physical_lane_count": (
                        profiled_channel_lanes * refined_spatial_lanes
                    ),
                }
            )
            if isinstance(isolated_collection, dict):
                actor_result["profiled_isolated_saturated_collection_cycles"] = int(
                    isolated_collection[name]
                )
                actor_result["profiled_isolated_saturated_actor_cycles"] = (
                    int(isolated_collection[name])
                    + int(actor_result["profiled_maximum_bank_commit_cycle_floor"])
                )
        actors[name] = actor_result

    bottleneck_name = max(
        actors, key=lambda actor_name: actors[actor_name]["serial_actor_cycle_floor"]
    )
    bottleneck = actors[bottleneck_name]
    result = {
        "schema_version": "1.0.0",
        "result_kind": (
            "conservative_existing_RTL_FSM_service_floor_from_exact_native_activity"
        ),
        "source_activity_profile": str(profile_path),
        "source_scope": profile["scope"],
        "clock_mhz": clock_mhz,
        "clock_source": "routed_SKY130_actor_tile_nominal_fmax_not_full_chip",
        "semantic_bin_us": bin_us,
        "cycles_available_per_bin": cycles_available,
        "target_utilization": target_utilization,
        "bottleneck_actor": bottleneck_name,
        "full_DAG_latency_us_floor": bottleneck["serial_actor_latency_us_floor"],
        "deadline_miss_factor_floor": (
            bottleneck["serial_actor_latency_us_floor"] / bin_us
        ),
        "actors": actors,
        "cycle_accurate_full_native_RTL_simulation": False,
        "power_available": False,
        "reporting_limit": (
            "This proves the present single-lane RTL cannot meet the bin deadline. "
            "It is a lower bound, not full-chip routed latency; ideal lane counts ignore "
            "routing, arbitration, and SRAM-bank conflicts."
        ),
    }
    if all(
        key in profile
        for key in (
            "actor_input_events",
            "maximum_residual_events_by_join",
            "input_events",
        )
    ):
        edge_traffic = _derive_edge_traffic(profile, spec["graph"])
        fifo_edges = [edge for edge in edge_traffic if edge["generated_FIFO_present"]]
        busiest_edge = max(fifo_edges, key=lambda edge: int(edge["total_packets"]))
        scalar_edge_cycles = int(busiest_edge["total_packets"])
        result.update(
            {
                "edge_traffic": edge_traffic,
                "generated_FIFO_count": len(fifo_edges),
                "maximum_generated_FIFO_data_events": max(
                    (int(edge["data_events"]) for edge in fifo_edges), default=0
                ),
                "maximum_generated_FIFO_total_packets": max(
                    (int(edge["total_packets"]) for edge in fifo_edges), default=0
                ),
                "scalar_edge_bottleneck": {
                    "edge_index": busiest_edge["edge_index"],
                    "source": busiest_edge["source"],
                    "destination": busiest_edge["destination"],
                },
                "scalar_edge_serialization_cycle_floor": scalar_edge_cycles,
                "scalar_edge_serialization_latency_us_floor": (
                    scalar_edge_cycles / clock_mhz
                ),
                "scalar_edge_serialization_utilization_floor": (
                    scalar_edge_cycles / cycles_available
                ),
                "scalar_edge_realtime_floor_pass": (
                    scalar_edge_cycles <= cycles_available
                ),
                "scalar_edge_target_floor_pass": (
                    scalar_edge_cycles <= cycles_available * target_utilization
                ),
                "edge_lanes_required_floor_for_deadline": math.ceil(
                    scalar_edge_cycles / cycles_available
                ),
                "edge_lanes_required_floor_for_target": math.ceil(
                    scalar_edge_cycles
                    / (cycles_available * target_utilization)
                ),
                "edge_traffic_occupancy_available": False,
            }
        )
        if isinstance(isolated_collection, dict):
            isolated_bottleneck_name = max(
                actors,
                key=lambda actor_name: actors[actor_name][
                    "profiled_isolated_saturated_actor_cycles"
                ],
            )
            isolated_cycles = int(
                actors[isolated_bottleneck_name][
                    "profiled_isolated_saturated_actor_cycles"
                ]
            )
            result.update(
                {
                    "isolated_saturated_actor_bottleneck": isolated_bottleneck_name,
                    "isolated_saturated_actor_cycle_floor": isolated_cycles,
                    "isolated_saturated_actor_latency_us_floor": (
                        isolated_cycles / clock_mhz
                    ),
                    "isolated_saturated_actor_realtime_floor_pass": (
                        isolated_cycles <= cycles_available
                    ),
                    "isolated_saturated_actor_target_floor_pass": (
                        isolated_cycles <= cycles_available * target_utilization
                    ),
                    "isolated_saturated_actor_scope": (
                        "event-order scatter plus bank collection handshake cadence and "
                        "maximum bank commit; excludes inter-actor arrival timing, edge FIFO "
                        "backpressure, routing, readout, and physical timing"
                    ),
                }
            )
    if isinstance(profiled_bank_activity, dict):
        configured_bottleneck_name = max(
            actors,
            key=lambda actor_name: actors[actor_name][
                "profiled_maximum_bank_cycle_floor"
            ],
        )
        configured_cycles = actors[configured_bottleneck_name][
            "profiled_maximum_bank_cycle_floor"
        ]
        result.update(
            {
                "profiled_banked_bottleneck_actor": configured_bottleneck_name,
                "profiled_banked_full_DAG_cycle_floor": configured_cycles,
                "profiled_banked_full_DAG_latency_us_floor": (
                    configured_cycles / clock_mhz
                ),
                "profiled_banked_full_DAG_utilization_floor": (
                    configured_cycles / cycles_available
                ),
                "profiled_banked_realtime_floor_pass": configured_cycles
                <= cycles_available,
                "profiled_banked_target_floor_pass": configured_cycles
                <= cycles_available * target_utilization,
            }
        )
        commit_cycles = {
            name: int(actor["profiled_maximum_bank_commit_cycle_floor"])
            for name, actor in actors.items()
        }
        critical_cycles, critical_path = _completion_token_critical_path(
            spec["graph"], commit_cycles
        )
        result.update(
            {
                "completion_token_critical_path_cycle_floor": critical_cycles,
                "completion_token_critical_path_latency_us_floor": (
                    critical_cycles / clock_mhz
                ),
                "completion_token_critical_path_deadline_miss_factor_floor": (
                    critical_cycles / cycles_available
                ),
                "completion_token_critical_path_realtime_floor_pass": (
                    critical_cycles <= cycles_available
                ),
                "completion_token_critical_path_target_floor_pass": (
                    critical_cycles <= cycles_available * target_utilization
                ),
                "completion_token_critical_path": critical_path,
                "completion_token_critical_path_scope": (
                    "configured-bank PLIF commit phases only; excludes collection overlap, "
                    "FIFO/routing cycles, readout cycles, backpressure, and physical timing"
                ),
            }
        )
    independent_floors: dict[str, int] = {}
    if "profiled_banked_full_DAG_cycle_floor" in result:
        independent_floors["busiest_bank_service"] = int(
            result["profiled_banked_full_DAG_cycle_floor"]
        )
    if "completion_token_critical_path_cycle_floor" in result:
        independent_floors["completion_token_commit_path"] = int(
            result["completion_token_critical_path_cycle_floor"]
        )
    if "scalar_edge_serialization_cycle_floor" in result:
        independent_floors["scalar_edge_serialization"] = int(
            result["scalar_edge_serialization_cycle_floor"]
        )
    if "isolated_saturated_actor_cycle_floor" in result:
        independent_floors["isolated_saturated_actor"] = int(
            result["isolated_saturated_actor_cycle_floor"]
        )
    if independent_floors:
        envelope = max(independent_floors.values())
        result.update(
            {
                "independent_cycle_floor_envelope": independent_floors,
                "maximum_independent_cycle_floor": envelope,
                "minimum_clock_mhz_floor_for_deadline": envelope / bin_us,
                "minimum_clock_mhz_floor_for_target": (
                    envelope / (bin_us * target_utilization)
                ),
                "combined_timed_schedule_available": False,
            }
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument(
        "--model-spec", type=Path, default=Path("artifacts/ASIC/model_spec.yaml")
    )
    parser.add_argument("--clock-mhz", type=float, default=97.31)
    parser.add_argument("--bin-us", type=float, default=5000.0)
    parser.add_argument("--target-utilization", type=float, default=0.8)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lane-config-output", type=Path)
    args = parser.parse_args()
    result = analyze(
        args.profile,
        args.model_spec,
        clock_mhz=args.clock_mhz,
        bin_us=args.bin_us,
        target_utilization=args.target_utilization,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.lane_config_output is not None:
        has_profiled_banks = "profiled_banked_bottleneck_actor" in result
        lane_config = {
            "schema_version": "1.0.0",
            "source_service_bounds": str(args.output),
            "status": (
                "conflict_refined_factorization_requires_reprofile"
                if has_profiled_banks
                else "provisional_scalar_work_factorization_requires_conflict_validation"
            ),
            "actors": {
                name: {
                    "use_parallel_banked_state": True,
                    "channel_lanes": actor.get(
                        "profiled_channel_lane_count",
                        actor["provisional_channel_lane_count"],
                    ),
                    "spatial_lanes": actor.get(
                        "profiled_spatial_lane_count",
                        actor["provisional_spatial_lane_count"],
                    ),
                }
                for name, actor in result["actors"].items()
            },
        }
        args.lane_config_output.parent.mkdir(parents=True, exist_ok=True)
        args.lane_config_output.write_text(
            json.dumps(lane_config, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
