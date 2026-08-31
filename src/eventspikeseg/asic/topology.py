"""Frozen EventSpikeSeg140k v8 ASIC graph topology.

The 25 PLIF populations are *actors in a directed acyclic graph*, not a linear
25-stage pipeline.  This module is intentionally free of PyTorch so export,
RTL-generation, verification, and documentation can share one exact connectivity
contract.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

EVENTSPIKESEG140K_ACTORS = (
    "detail_stem",
    "detail1.standard",
    "stem",
    "enc1.standard",
    "enc1_extra.depthwise",
    "enc1_extra.pointwise",
    "down2.standard",
    "enc2.depthwise",
    "enc2.pointwise",
    "enc2_extra.depthwise",
    "enc2_extra.pointwise",
    "down3.depthwise",
    "down3.pointwise",
    "enc3.depthwise",
    "enc3.pointwise",
    "enc3_extra.depthwise",
    "enc3_extra.pointwise",
    "context1.depthwise",
    "context1.pointwise",
    "context2.depthwise",
    "context2.pointwise",
    "project3",
    "decoder2_fuse",
    "project2",
    "final_fuse.standard",
)

EVENTSPIKESEG140K_CURRENT_READOUT = "head.synapse"

# Stateless routing/merge nodes are explicit because they are semantically important:
# residual merges deduplicate binary spikes, while the project2+x1 skip deliberately
# preserves coincident events as multiplicity two.
EVENTSPIKESEG140K_ROUTE_NODES = (
    "input",
    "detail1.residual_or",
    "enc1.residual_or",
    "enc1_extra.residual_or",
    "enc2.residual_or",
    "enc2_extra.residual_or",
    "enc3.residual_or",
    "enc3_extra.residual_or",
    "context1.residual_or",
    "context2.residual_or",
    "project3.upsample2x",
    "decoder2.concat",
    "project2.upsample2x",
    "semantic_half.multiplicity_sum",
    "semantic_native.upsample2x",
    "final.concat",
    EVENTSPIKESEG140K_CURRENT_READOUT,
    "prediction",
)


def _edge(
    source: str,
    destination: str,
    *,
    transform: str = "identity",
    channel_offset: int | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    edge: dict[str, Any] = {
        "source": source,
        "destination": destination,
        "transform": transform,
        "carries": ["spike_event", "ordered_5ms_completion_token"],
    }
    if channel_offset is not None:
        edge["channel_offset"] = int(channel_offset)
    if note is not None:
        edge["note"] = note
    return edge


# Exact inference connectivity derived from EventSpikeSeg140k.forward() and
# SpikingConvBlock residual semantics.  The order here is descriptive only.
EVENTSPIKESEG140K_EDGES = (
    # Input fork: native detail and learned stride-2 semantic stem run independently.
    _edge("input", "detail_stem"),
    _edge("input", "stem"),

    # Native detail residual block.
    _edge("detail_stem", "detail1.standard"),
    _edge("detail_stem", "detail1.residual_or", transform="residual_bypass"),
    _edge("detail1.standard", "detail1.residual_or", transform="residual_main"),

    # Half-resolution encoder: standard residual then DW/PW residual.
    _edge("stem", "enc1.standard"),
    _edge("stem", "enc1.residual_or", transform="residual_bypass"),
    _edge("enc1.standard", "enc1.residual_or", transform="residual_main"),
    _edge("enc1.residual_or", "enc1_extra.depthwise"),
    _edge("enc1.residual_or", "enc1_extra.residual_or", transform="residual_bypass"),
    _edge("enc1_extra.depthwise", "enc1_extra.pointwise"),
    _edge("enc1_extra.pointwise", "enc1_extra.residual_or", transform="residual_main"),

    # x1 fans out: deeper encoder and later decoder skip.
    _edge("enc1_extra.residual_or", "down2.standard"),
    _edge(
        "enc1_extra.residual_or",
        "semantic_half.multiplicity_sum",
        transform="skip_fanout",
        note="x1 decoder skip; preserve coincident events rather than binary dedup",
    ),

    # Quarter-resolution encoder residual blocks.
    _edge("down2.standard", "enc2.depthwise"),
    _edge("down2.standard", "enc2.residual_or", transform="residual_bypass"),
    _edge("enc2.depthwise", "enc2.pointwise"),
    _edge("enc2.pointwise", "enc2.residual_or", transform="residual_main"),
    _edge("enc2.residual_or", "enc2_extra.depthwise"),
    _edge("enc2.residual_or", "enc2_extra.residual_or", transform="residual_bypass"),
    _edge("enc2_extra.depthwise", "enc2_extra.pointwise"),
    _edge("enc2_extra.pointwise", "enc2_extra.residual_or", transform="residual_main"),

    # x2 fans out: deeper encoder and decoder concatenation.
    _edge("enc2_extra.residual_or", "down3.depthwise"),
    _edge(
        "enc2_extra.residual_or",
        "decoder2.concat",
        transform="channel_concat",
        channel_offset=64,
        note="x2 occupies decoder2 input channels 64..127",
    ),

    # Eighth-resolution encoder and context residual blocks.
    _edge("down3.depthwise", "down3.pointwise"),
    _edge("down3.pointwise", "enc3.depthwise"),
    _edge("down3.pointwise", "enc3.residual_or", transform="residual_bypass"),
    _edge("enc3.depthwise", "enc3.pointwise"),
    _edge("enc3.pointwise", "enc3.residual_or", transform="residual_main"),
    _edge("enc3.residual_or", "enc3_extra.depthwise"),
    _edge("enc3.residual_or", "enc3_extra.residual_or", transform="residual_bypass"),
    _edge("enc3_extra.depthwise", "enc3_extra.pointwise"),
    _edge("enc3_extra.pointwise", "enc3_extra.residual_or", transform="residual_main"),
    _edge("enc3_extra.residual_or", "context1.depthwise"),
    _edge("enc3_extra.residual_or", "context1.residual_or", transform="residual_bypass"),
    _edge("context1.depthwise", "context1.pointwise"),
    _edge("context1.pointwise", "context1.residual_or", transform="residual_main"),
    _edge("context1.residual_or", "context2.depthwise"),
    _edge("context1.residual_or", "context2.residual_or", transform="residual_bypass"),
    _edge("context2.depthwise", "context2.pointwise"),
    _edge("context2.pointwise", "context2.residual_or", transform="residual_main"),

    # Decoder: project deepest events, 2x spatial fanout, then concatenate with x2.
    _edge("context2.residual_or", "project3"),
    _edge("project3", "project3.upsample2x", transform="nearest_event_fanout_2x"),
    _edge(
        "project3.upsample2x",
        "decoder2.concat",
        transform="channel_concat",
        channel_offset=0,
        note="upsampled project3 occupies decoder2 input channels 0..63",
    ),
    _edge("decoder2.concat", "decoder2_fuse"),

    # project2 returns to half scale.  x1 + project2 is an arithmetic spike-count sum,
    # so two coincident binary spikes must reach final_fuse as two synaptic events.
    _edge("decoder2_fuse", "project2"),
    _edge("project2", "project2.upsample2x", transform="nearest_event_fanout_2x"),
    _edge(
        "project2.upsample2x",
        "semantic_half.multiplicity_sum",
        transform="multiplicity_preserving_merge",
    ),
    _edge(
        "semantic_half.multiplicity_sum",
        "semantic_native.upsample2x",
        transform="nearest_event_fanout_2x",
    ),

    # Native semantic/detail concatenation followed by one standard Conv->PLIF actor.
    _edge(
        "semantic_native.upsample2x",
        "final.concat",
        transform="channel_concat",
        channel_offset=0,
        note="semantic channels 0..31",
    ),
    _edge(
        "detail1.residual_or",
        "final.concat",
        transform="channel_concat",
        channel_offset=32,
        note="detail channels 32..39",
    ),
    _edge("final.concat", "final_fuse.standard"),
    _edge("final_fuse.standard", EVENTSPIKESEG140K_CURRENT_READOUT),
    _edge(
        EVENTSPIKESEG140K_CURRENT_READOUT,
        "prediction",
        transform="temporal_current_accumulate_and_argmax",
        note="default prediction window is ten 5 ms bins",
    ),
)


EVENTSPIKESEG140K_JOIN_NODES = {
    "detail1.residual_or": {
        "kind": "binary_residual_or",
        "data_rule": "deduplicate_equal_binary_spike_addresses",
        "completion_rule": "wait_for_all_inputs_same_bin",
    },
    "enc1.residual_or": {
        "kind": "binary_residual_or",
        "data_rule": "deduplicate_equal_binary_spike_addresses",
        "completion_rule": "wait_for_all_inputs_same_bin",
    },
    "enc1_extra.residual_or": {
        "kind": "binary_residual_or",
        "data_rule": "deduplicate_equal_binary_spike_addresses",
        "completion_rule": "wait_for_all_inputs_same_bin",
    },
    "enc2.residual_or": {
        "kind": "binary_residual_or",
        "data_rule": "deduplicate_equal_binary_spike_addresses",
        "completion_rule": "wait_for_all_inputs_same_bin",
    },
    "enc2_extra.residual_or": {
        "kind": "binary_residual_or",
        "data_rule": "deduplicate_equal_binary_spike_addresses",
        "completion_rule": "wait_for_all_inputs_same_bin",
    },
    "enc3.residual_or": {
        "kind": "binary_residual_or",
        "data_rule": "deduplicate_equal_binary_spike_addresses",
        "completion_rule": "wait_for_all_inputs_same_bin",
    },
    "enc3_extra.residual_or": {
        "kind": "binary_residual_or",
        "data_rule": "deduplicate_equal_binary_spike_addresses",
        "completion_rule": "wait_for_all_inputs_same_bin",
    },
    "context1.residual_or": {
        "kind": "binary_residual_or",
        "data_rule": "deduplicate_equal_binary_spike_addresses",
        "completion_rule": "wait_for_all_inputs_same_bin",
    },
    "context2.residual_or": {
        "kind": "binary_residual_or",
        "data_rule": "deduplicate_equal_binary_spike_addresses",
        "completion_rule": "wait_for_all_inputs_same_bin",
    },
    "decoder2.concat": {
        "kind": "channel_concat",
        "data_rule": "preserve_all_events_after_channel_offset_remap",
        "completion_rule": "wait_for_all_inputs_same_bin",
    },
    "semantic_half.multiplicity_sum": {
        "kind": "multiplicity_preserving_sum",
        "data_rule": "forward_coincident_events_without_deduplication",
        "completion_rule": "wait_for_all_inputs_same_bin",
    },
    "final.concat": {
        "kind": "channel_concat",
        "data_rule": "preserve_all_events_after_channel_offset_remap",
        "completion_rule": "wait_for_all_inputs_same_bin",
    },
}


def graph_nodes() -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = [{"name": "input", "kind": "event_input"}]
    nodes.extend({"name": name, "kind": "plif_actor"} for name in EVENTSPIKESEG140K_ACTORS)
    for name in EVENTSPIKESEG140K_ROUTE_NODES:
        if name in {"input", EVENTSPIKESEG140K_CURRENT_READOUT, "prediction"}:
            continue
        if name in EVENTSPIKESEG140K_JOIN_NODES:
            kind = EVENTSPIKESEG140K_JOIN_NODES[name]["kind"]
        elif "upsample2x" in name:
            kind = "nearest_event_fanout_2x"
        else:
            kind = "routing"
        nodes.append({"name": name, "kind": kind})
    nodes.append({"name": EVENTSPIKESEG140K_CURRENT_READOUT, "kind": "current_readout"})
    nodes.append({"name": "prediction", "kind": "semantic_output"})
    return nodes


def _topological_node_order() -> list[str]:
    nodes = {node["name"] for node in graph_nodes()}
    indegree = {node: 0 for node in nodes}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in EVENTSPIKESEG140K_EDGES:
        source = str(edge["source"])
        destination = str(edge["destination"])
        outgoing[source].append(destination)
        indegree[destination] += 1
    ready = deque(sorted(name for name, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while ready:
        node = ready.popleft()
        order.append(node)
        for destination in outgoing[node]:
            indegree[destination] -= 1
            if indegree[destination] == 0:
                ready.append(destination)
    if len(order) != len(nodes):
        raise RuntimeError("EventSpikeSeg140k ASIC topology contains a cycle")
    return order


def validate_eventspikeseg140k_topology() -> None:
    nodes = {node["name"] for node in graph_nodes()}
    if len(EVENTSPIKESEG140K_ACTORS) != 25:
        raise RuntimeError("EventSpikeSeg140k must expose exactly 25 PLIF actors")
    if len(set(EVENTSPIKESEG140K_ACTORS)) != len(EVENTSPIKESEG140K_ACTORS):
        raise RuntimeError("duplicate EventSpikeSeg140k actor name")
    for edge in EVENTSPIKESEG140K_EDGES:
        if edge["source"] not in nodes or edge["destination"] not in nodes:
            raise RuntimeError(f"topology edge references unknown node: {edge}")
    _topological_node_order()

    # The key non-linear paths must remain present; these checks catch accidental
    # reduction back to a linear actor chain.
    edge_pairs = {(edge["source"], edge["destination"]) for edge in EVENTSPIKESEG140K_EDGES}
    required = {
        ("input", "detail_stem"),
        ("input", "stem"),
        ("enc1_extra.residual_or", "down2.standard"),
        ("enc1_extra.residual_or", "semantic_half.multiplicity_sum"),
        ("enc2_extra.residual_or", "down3.depthwise"),
        ("enc2_extra.residual_or", "decoder2.concat"),
        ("project3.upsample2x", "decoder2.concat"),
        ("detail1.residual_or", "final.concat"),
        ("semantic_native.upsample2x", "final.concat"),
    }
    missing = required - edge_pairs
    if missing:
        raise RuntimeError(f"EventSpikeSeg140k non-linear DAG edges missing: {sorted(missing)}")


def eventspikeseg140k_graph_contract() -> dict[str, Any]:
    validate_eventspikeseg140k_topology()
    return {
        "graph_kind": "static_directed_acyclic_actor_graph",
        "linear_pipeline": False,
        "actor_count": len(EVENTSPIKESEG140K_ACTORS),
        "current_readout": EVENTSPIKESEG140K_CURRENT_READOUT,
        "actor_topological_order": list(EVENTSPIKESEG140K_ACTORS),
        "node_topological_order": _topological_node_order(),
        "nodes": graph_nodes(),
        "edges": [dict(edge) for edge in EVENTSPIKESEG140K_EDGES],
        "join_nodes": {
            name: dict(contract) for name, contract in EVENTSPIKESEG140K_JOIN_NODES.items()
        },
        "routing_policy": "compile_time_dedicated_paths_not_programmable_NoC",
        "fanout_policy": "ready_valid_multicast_with_lossless_backpressure",
        "completion_token_policy": (
            "fork_on_fanout; joins_wait_for_all_required_upstream_tokens_of_same_5ms_bin"
        ),
        "residual_policy": "binary_OR_deduplicate_before_downstream_synaptic_use",
        "decoder_skip_policy": "project2_plus_x1_preserves_event_multiplicity",
    }
