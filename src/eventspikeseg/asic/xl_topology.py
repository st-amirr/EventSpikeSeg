"""Exact EventSpikeSegXL inference DAG used by export and RTL generation."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

EVENTSPIKESEGXL_ACTORS = (
    "detail_stem",
    "detail1.depthwise",
    "detail1.pointwise",
    "detail2.vertical",
    "detail2.horizontal",
    "detail2.mix",
    "stem",
    "enc1.depthwise",
    "enc1.pointwise",
    "enc1_extra.depthwise",
    "enc1_extra.pointwise",
    "down2.depthwise",
    "down2.pointwise",
    "bridge12",
    "enc2.depthwise",
    "enc2.pointwise",
    "enc2_extra.depthwise",
    "enc2_extra.pointwise",
    "down3.depthwise",
    "down3.pointwise",
    "bridge23",
    "enc3.depthwise",
    "enc3.pointwise",
    "enc3_extra.standard",
    "context1.standard",
    "context2.standard",
    "semantic_capacity.0.standard",
    "semantic_capacity.1.standard",
    "parallel_context.branches.0",
    "parallel_context.branches.1",
    "parallel_context.branches.2",
    "parallel_context.fuse",
    "deep_attention.q",
    "deep_attention.k",
    "deep_attention.v",
    "deep_attention.out",
    "project3",
    "decoder2_fuse.standard",
    "decoder2_extra.depthwise",
    "decoder2_extra.pointwise",
    "project2",
    "final_fuse.standard",
    "decoder1_extra.depthwise",
    "decoder1_extra.pointwise",
)

EVENTSPIKESEGXL_CURRENT_READOUT = "head.synapse"


def _edge(
    source: str,
    destination: str,
    *,
    transform: str = "identity",
    channel_offset: int | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "source": source,
        "destination": destination,
        "transform": transform,
        "carries": ["spike_event", "ordered_5ms_completion_token"],
    }
    if channel_offset is not None:
        value["channel_offset"] = channel_offset
    if note is not None:
        value["note"] = note
    return value


def _residual(edges: list[dict[str, Any]], source: str, stages: tuple[str, ...], join: str) -> None:
    edges.append(_edge(source, stages[0]))
    edges.append(_edge(source, join, transform="residual_bypass"))
    for left, right in zip(stages, stages[1:]):
        edges.append(_edge(left, right))
    edges.append(_edge(stages[-1], join, transform="residual_main"))


_edges: list[dict[str, Any]] = [_edge("input", "detail_stem"), _edge("input", "stem")]
_residual(_edges, "detail_stem", ("detail1.depthwise", "detail1.pointwise"), "detail1.residual_or")
_residual(
    _edges,
    "detail1.residual_or",
    ("detail2.vertical", "detail2.horizontal", "detail2.mix"),
    "detail2.residual_or",
)
_residual(_edges, "stem", ("enc1.depthwise", "enc1.pointwise"), "enc1.residual_or")
_residual(
    _edges,
    "enc1.residual_or",
    ("enc1_extra.depthwise", "enc1_extra.pointwise"),
    "enc1_extra.residual_or",
)
_edges.extend(
    [
        _edge("enc1_extra.residual_or", "down2.depthwise"),
        _edge("down2.depthwise", "down2.pointwise"),
        _edge("enc1_extra.residual_or", "bridge12"),
        _edge("down2.pointwise", "x2_transition.residual_or", transform="residual_main"),
        _edge("bridge12", "x2_transition.residual_or", transform="residual_bypass"),
    ]
)
_residual(
    _edges, "x2_transition.residual_or", ("enc2.depthwise", "enc2.pointwise"), "enc2.residual_or"
)
_residual(
    _edges,
    "enc2.residual_or",
    ("enc2_extra.depthwise", "enc2_extra.pointwise"),
    "enc2_extra.residual_or",
)
_edges.extend(
    [
        _edge("enc2_extra.residual_or", "down3.depthwise"),
        _edge("down3.depthwise", "down3.pointwise"),
        _edge("enc2_extra.residual_or", "bridge23"),
        _edge("down3.pointwise", "x3_transition.residual_or", transform="residual_main"),
        _edge("bridge23", "x3_transition.residual_or", transform="residual_bypass"),
    ]
)
_residual(
    _edges, "x3_transition.residual_or", ("enc3.depthwise", "enc3.pointwise"), "enc3.residual_or"
)
_residual(_edges, "enc3.residual_or", ("enc3_extra.standard",), "enc3_extra.residual_or")
_residual(_edges, "enc3_extra.residual_or", ("context1.standard",), "context1.residual_or")
_residual(_edges, "context1.residual_or", ("context2.standard",), "context2.residual_or")
_residual(
    _edges,
    "context2.residual_or",
    ("semantic_capacity.0.standard",),
    "semantic_capacity.0.residual_or",
)
_residual(
    _edges,
    "semantic_capacity.0.residual_or",
    ("semantic_capacity.1.standard",),
    "semantic_capacity.1.residual_or",
)

# Three dilated depthwise branches concatenate, fuse, and binary-residual merge.
for index in range(3):
    _edges.append(_edge("semantic_capacity.1.residual_or", f"parallel_context.branches.{index}"))
_edges.extend(
    [
        _edge(
            "parallel_context.branches.0",
            "parallel_context.concat01",
            transform="channel_concat",
            channel_offset=0,
        ),
        _edge(
            "parallel_context.branches.1",
            "parallel_context.concat01",
            transform="channel_concat",
            channel_offset=128,
        ),
        _edge(
            "parallel_context.concat01",
            "parallel_context.concat",
            transform="channel_concat",
            channel_offset=0,
        ),
        _edge(
            "parallel_context.branches.2",
            "parallel_context.concat",
            transform="channel_concat",
            channel_offset=256,
        ),
        _edge("parallel_context.concat", "parallel_context.fuse"),
        _edge("parallel_context.fuse", "parallel_context.residual_or", transform="residual_main"),
        _edge(
            "semantic_capacity.1.residual_or",
            "parallel_context.residual_or",
            transform="residual_bypass",
        ),
    ]
)

# Q/K/V are spikes.  The qkv joins preserve channel identity; the mask primitive
# counts Q&K coincidences per head and gates V before the output PLIF projection.
for name in ("q", "k", "v"):
    _edges.append(_edge("parallel_context.residual_or", f"deep_attention.{name}"))
_edges.extend(
    [
        _edge("deep_attention.q", "deep_attention.mask", transform="attention_q"),
        _edge("deep_attention.k", "deep_attention.mask", transform="attention_k"),
        _edge("deep_attention.v", "deep_attention.mask", transform="attention_v"),
        _edge("deep_attention.mask", "deep_attention.out"),
        _edge("deep_attention.out", "deep_attention.residual_or", transform="residual_main"),
        _edge(
            "parallel_context.residual_or",
            "deep_attention.residual_or",
            transform="residual_bypass",
        ),
        _edge("deep_attention.residual_or", "project3"),
        _edge("project3", "project3.upsample2x", transform="nearest_event_fanout_2x"),
        _edge(
            "project3.upsample2x", "decoder2.concat", transform="channel_concat", channel_offset=0
        ),
        _edge(
            "enc2_extra.residual_or",
            "decoder2.concat",
            transform="channel_concat",
            channel_offset=64,
        ),
        _edge("decoder2.concat", "decoder2_fuse.standard"),
    ]
)
_residual(
    _edges,
    "decoder2_fuse.standard",
    ("decoder2_extra.depthwise", "decoder2_extra.pointwise"),
    "decoder2_extra.residual_or",
)
_edges.extend(
    [
        _edge("decoder2_extra.residual_or", "project2"),
        _edge("project2", "project2.upsample2x", transform="nearest_event_fanout_2x"),
        _edge(
            "project2.upsample2x",
            "semantic_half.multiplicity_sum",
            transform="multiplicity_preserving_merge",
        ),
        _edge("enc1_extra.residual_or", "semantic_half.multiplicity_sum", transform="skip_fanout"),
        _edge(
            "semantic_half.multiplicity_sum",
            "semantic_native.upsample2x",
            transform="nearest_event_fanout_2x",
        ),
        _edge(
            "semantic_native.upsample2x",
            "final.concat",
            transform="channel_concat",
            channel_offset=0,
        ),
        _edge("detail2.residual_or", "final.concat", transform="channel_concat", channel_offset=32),
        _edge("final.concat", "final_fuse.standard"),
    ]
)
_residual(
    _edges,
    "final_fuse.standard",
    ("decoder1_extra.depthwise", "decoder1_extra.pointwise"),
    "decoder1_extra.residual_or",
)
_edges.extend(
    [
        _edge("decoder1_extra.residual_or", EVENTSPIKESEGXL_CURRENT_READOUT),
        _edge(
            EVENTSPIKESEGXL_CURRENT_READOUT,
            "prediction",
            transform="temporal_current_accumulate_and_argmax",
        ),
    ]
)
EVENTSPIKESEGXL_EDGES = tuple(_edges)

_BINARY_JOINS = {
    "detail1.residual_or",
    "detail2.residual_or",
    "enc1.residual_or",
    "enc1_extra.residual_or",
    "x2_transition.residual_or",
    "enc2.residual_or",
    "enc2_extra.residual_or",
    "x3_transition.residual_or",
    "enc3.residual_or",
    "enc3_extra.residual_or",
    "context1.residual_or",
    "context2.residual_or",
    "semantic_capacity.0.residual_or",
    "semantic_capacity.1.residual_or",
    "parallel_context.residual_or",
    "deep_attention.residual_or",
    "decoder2_extra.residual_or",
    "decoder1_extra.residual_or",
}
_CONCATS = {
    "parallel_context.concat01",
    "parallel_context.concat",
    "decoder2.concat",
    "final.concat",
}
_UPSAMPLES = {"project3.upsample2x", "project2.upsample2x", "semantic_native.upsample2x"}


def _nodes() -> list[dict[str, Any]]:
    names = {"input", EVENTSPIKESEGXL_CURRENT_READOUT, "prediction"}
    names.update(EVENTSPIKESEGXL_ACTORS)
    for edge in EVENTSPIKESEGXL_EDGES:
        names.add(str(edge["source"]))
        names.add(str(edge["destination"]))
    nodes: list[dict[str, Any]] = []
    for name in sorted(names):
        if name == "input":
            kind = "event_input"
        elif name in EVENTSPIKESEGXL_ACTORS:
            kind = "plif_actor"
        elif name == EVENTSPIKESEGXL_CURRENT_READOUT:
            kind = "current_readout"
        elif name == "prediction":
            kind = "semantic_output"
        elif name in _BINARY_JOINS:
            kind = "binary_residual_or"
        elif name in _CONCATS:
            kind = "channel_concat"
        elif name in _UPSAMPLES:
            kind = "nearest_event_fanout_2x"
        elif name == "semantic_half.multiplicity_sum":
            kind = "multiplicity_preserving_sum"
        elif name == "deep_attention.mask":
            kind = "spike_mask_attention"
        else:
            kind = "routing"
        nodes.append({"name": name, "kind": kind})
    return nodes


def _topological_order() -> list[str]:
    nodes = {node["name"] for node in _nodes()}
    indegree = {name: 0 for name in nodes}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in EVENTSPIKESEGXL_EDGES:
        source, destination = str(edge["source"]), str(edge["destination"])
        outgoing[source].append(destination)
        indegree[destination] += 1
    ready = deque(sorted(name for name, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while ready:
        name = ready.popleft()
        order.append(name)
        for destination in outgoing[name]:
            indegree[destination] -= 1
            if indegree[destination] == 0:
                ready.append(destination)
    if len(order) != len(nodes):
        raise RuntimeError("EventSpikeSegXL ASIC topology contains a cycle")
    return order


def validate_eventspikesegxl_topology() -> None:
    if len(EVENTSPIKESEGXL_ACTORS) != 44 or len(set(EVENTSPIKESEGXL_ACTORS)) != 44:
        raise RuntimeError("EventSpikeSegXL must expose 44 unique inference PLIF actors")
    nodes = {node["name"] for node in _nodes()}
    for edge in EVENTSPIKESEGXL_EDGES:
        if edge["source"] not in nodes or edge["destination"] not in nodes:
            raise RuntimeError(f"XL topology edge references unknown node: {edge}")
    _topological_order()


def eventspikesegxl_graph_contract() -> dict[str, Any]:
    validate_eventspikesegxl_topology()
    join_names = _BINARY_JOINS | _CONCATS | {"semantic_half.multiplicity_sum"}
    return {
        "graph_kind": "static_directed_acyclic_actor_graph",
        "linear_pipeline": False,
        "actor_count": 44,
        "current_readout": EVENTSPIKESEGXL_CURRENT_READOUT,
        "actor_topological_order": list(EVENTSPIKESEGXL_ACTORS),
        "node_topological_order": _topological_order(),
        "nodes": _nodes(),
        "edges": [dict(edge) for edge in EVENTSPIKESEGXL_EDGES],
        "join_nodes": {
            name: {
                "kind": next(node["kind"] for node in _nodes() if node["name"] == name),
                "completion_rule": "wait_for_all_inputs_same_bin",
            }
            for name in sorted(join_names)
        },
        "routing_policy": "compile_time_dedicated_paths_not_programmable_NoC",
        "fanout_policy": "ready_valid_multicast_with_lossless_backpressure",
        "completion_token_policy": (
            "fork_on_fanout; "
            "joins_wait_for_all_required_upstream_tokens_of_same_5ms_bin"
        ),
        "residual_policy": "binary_OR_deduplicate_before_downstream_synaptic_use",
        "decoder_skip_policy": "project2_plus_x1_preserves_event_multiplicity",
        "attention_policy": "four_head_spiking_QK_coincidence_threshold_gates_spiking_V",
    }
