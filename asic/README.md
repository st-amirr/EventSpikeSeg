# EventSpikeSeg ASIC flow

The hardware implementation is native synthesizable SystemVerilog. Icarus Verilog and
cocotb provide executable RTL checks, Yosys performs technology mapping, and OpenROAD
Flow Scripts (ORFS) performs floorplanning through routed layout, parasitic extraction,
timing, and power analysis.

## Platform decision

- `asap7` is the primary open, reproducible **research PPA** platform. It is a predictive
  7 nm FinFET platform, not a manufacturable foundry PDK and not tapeout signoff.
- `sky130ram` is the future open, manufacturable **tile/test-chip** check when the actor
  state arrays have been replaced by explicit SRAM macros. It is not dense enough for
  the complete native-resolution state on one economical die.
- A complete manufacturable EventSpikeSeg chip requires an accessible 22/28 nm-or-better
  foundry PDK plus characterized high-density SRAM macros. That target cannot be called
  selected or power-signoff-ready until those libraries are available.

The distinction matters because 143,824 int8 synaptic weights consume only about
0.137 MiB, while the frozen 440x640 graph has 30,976,000 logical membranes. The current
exact dense reference is 189.60 MiB when int16 membrane, adaptation fields, and 24-bit
lazy-update tags are all included. Standard-cell flip-flops are not an acceptable
full-chip memory implementation.

## Current synthesis boundary

`convolution_plif_actor.sv` is the one-plane reference actor. The channelized and streaming
actors extend it to exported per-channel parameters and packed ready/valid traffic.
EventSpikeSeg140k v8 contains 25 permanent PLIF actors connected as a fixed DAG with
input/detail-semantic forks, residual binary-OR joins, `x1`/`x2` skip fanout, decoder
upsample/concat, multiplicity-preserving `project2+x1`, and late semantic/detail concat.

`src/eventspikeseg/asic/topology.py` is the connectivity source of truth. The exporter writes
explicit DAG nodes/edges/join semantics to `layer_graph.json`; its actor tuple is only a
deterministic topological export order. `event_fork2.sv` provides lossless two-way event and
completion-token multicast, `event_join2.sv` provides multiplicity-preserving same-bin
completion rendezvous, and `binary_event_union2.sv` is the correctness-reference residual
OR/dedup join. The generated top instantiates these routes around all 25 actors.
`event_channel_offset.sv` implements fixed concatenation channel remaps,
`event_upsample2x.sv` expands a spike into four nearest-neighbor addresses, and
`channelized_convolution_scatter.sv` expands one input spike across legal standard, grouped,
or depthwise output-channel/tap projections using exported PyTorch Conv2d weight order.
`channelized_convolution_plif_actor.sv` now joins that scatter to canonical local
`(output_channel,y,x)` membrane/current/tag state and selects compile-time per-channel beta
and threshold tables. The exporter emits matching 16-bit beta and threshold ROM images for
each actor. `scripts/generate_asic_top.py` performs model-scale instantiation and wiring.

`scripts/generate_asic_top.py` now consumes an exported `model_spec.yaml` and emits the exact
25-actor structural top with fixed ROM constants and all routing primitives. The generated
miniature-state regression exercises the complete completion-token DAG. Mechanism-enabled
actors use grouped retinotopic commits; the final readout accumulates signed class currents
and enumerates a dense prediction after the configured bin window. `actor_local_state_sram`
defines the compiler-macro interface, but the current actor arrays remain behavioral until a
real SRAM compiler is selected and bound.

`src/eventspikeseg/asic/dag_reference.py` is the sparse bit-exact whole-graph oracle. It
executes exported convolution scatter, joins, lazy PLIF state, retinotopic mechanisms, and
the temporal readout. Generate the five required compact NPZ golden artifacts with:

```sh
docker compose -f compose_ASIC.yaml run --rm test python scripts/generate_asic_golden.py artifacts/asic_export_v4_6class/model_spec.yaml
```

The checked-in active artifacts use deterministic synthetic stress traffic. Dataset-derived
full-sequence traffic is still required for occupancy, latency, accuracy, and power claims.

For executable whole-DAG RTL equivalence, build the reduced-spatial fixture with unchanged
real weights, channels, mechanisms, and topology, then run Verilator:

```sh
docker compose -f compose_ASIC.yaml run --rm rtl python scripts/prepare_asic_rtl_replay.py artifacts/asic_export_v4_6class artifacts/asic_rtl_replay_smoke_v4_6class --height 8 --width 8 --bins 10 --events-per-bin 4 --stimulus center_burst
docker compose -f compose_ASIC.yaml run --rm rtl python scripts/run_asic_golden_rtl_replay.py artifacts/asic_rtl_replay_smoke_v4_6class --simulator verilator --residual-capacity 512 --timeout-cycles 50000
```

The generated actors load static int8 kernels from per-actor ROM files; the packed parameter
fallback remains only for small unit fixtures. Passive generated-top trace buses expose every
actor transfer without changing ready/valid backpressure. The replay is logical equivalence
evidence, not native 440x640 capacity, latency, or physical PPA evidence.

The generated top uses `temporal_class_readout_sram`. At native 440x640 and six classes its
score bank is 281,600 x 144 bits = 4.834 MiB. A synchronous 1R1W transaction accepts at most
one final hidden event every two clocks. Power-on reset scrubs 281,600 words; prediction flush
uses three clocks per pixel (844,800 clocks/frame) and backpressures the final actor. At
100 MHz these fixed costs are 2.816 ms once after reset and 8.448 ms per output frame. Input
FIFO sizing must cover this backpressure before a real-time claim. Set the generated-top
`USE_SCORE_SRAM_MACRO=1` parameter only when the black-box boundary is bound to a compatible
characterized macro.

The active trained six-class v4 export is retained under
`artifacts/asic_export_v4_6class`; its generated weighted top contains all 25 actors and
exactly 143,824 int8 synaptic ROM words. The prior 11-class export under
`artifacts/asic_export_v4` is historical. The active top is the executable logical reference,
not a full-chip PPA netlist: its large behavioral arrays must not be mapped to standard cells
or reported as a physical implementation.

All nine production residual joins use a direct-indexed one-bit seen-map SRAM and compact
linear-address queue SRAM. With full logical-address capacity, their combined worst-case native
allocation is 252,313,600 bits (30.078 MiB). The replay command's capacity 512 is a bounded 8x8
fixture only; a smaller native capacity requires complete-sequence occupancy proof and must never
drop or evict events. Before full-chip PPA, every generic actor-state, touch-queue, residual, and
readout SRAM boundary must be bound to characterized macros; no production actor relies on
inter-layer state fetch or a behavioral state array.

The nine actors without retinotopic mechanisms now select `asynchronous_plif_actor_sram`.
Each neuron owns one packed 66-bit current/membrane/tag/live/touched word and each actor owns a
narrow first-touch address queue. At native geometry these banks conservatively total 186.276 MiB
when queues can hold every logical address. This guarantees losslessness but is not an optimized
physical allocation; complete DSEC occupancy measurements are required before reducing queue
depth. The sixteen mechanism-enabled actors use `retinotopic_asynchronous_plif_actor_sram`:
one 65-bit PLIF state lane per channel is addressed by spatial location, allowing all channels at
a location to be read and committed atomically for inhibition/adaptation. A separate 32-bit
adaptation lane is generated only for the fifteen actors that enable adaptation; the inhibition-only
stem omits it. These conservative native banks total 144.841 MiB. All production actor state now crosses generic SRAM boundaries; real
compiler macros and occupancy-derived queue depths are still required for physical claims.

Generate the exact logical compiler request manifest with:

```sh
python scripts/generate_asic_sram_manifest.py \
  artifacts/asic_export_v4_6class/model_spec.yaml \
  artifacts/asic_export_v4_6class/sram_manifest.json
```

The conservative active manifest contains 100 bank records, 3,173 lane instances, and
3,070,478,400 bits (366.030 MiB). A physical binding must split these logical requests into
available compiler depths/widths and preserve synchronous 1R1W behavior.

After replacing the schema-only example with an actual compiler catalog, create a banking plan:

```sh
python scripts/plan_asic_sram_banking.py \
  artifacts/asic_export_v4_6class/sram_manifest.json \
  path/to/characterized_macro_catalog.json \
  artifacts/asic_export_v4_6class/sram_banking_plan.json
```

`asic/sram_macro_catalog.example.json` documents the required schema but is deliberately marked
uncharacterized and therefore cannot make a plan PPA-eligible.

Profile first-touch queues from an exact integer current trace with:

```sh
python scripts/profile_asic_touch_occupancy.py MODEL_SPEC CURRENT_TRACE OUTPUT_JSON
```

The active synthetic report peaks at 11,135 entries but does not touch every deep actor, so it
cannot justify reducing any production queue. Only complete native DSEC coverage can establish a
candidate bound, and the design must remain lossless.

`profile_asic_residual_occupancy.py` replays golden ingress through the exact integer DAG and
reports all nine binary-OR queue occupancies. The active synthetic maximum is 507, but four deep
joins receive no events, so the report explains only the 512-entry verification fixture and does
not change native production capacity.

Run native SystemVerilog compilation and the cocotb suite:

```sh
bash asic/scripts/check_rtl.sh
python scripts/run_rtl_tests.py
```

Set `ASIC_BUILD_DIR` to redirect generated netlists outside the repository when needed.

The isolated CPU-only implementation container pins CPU PyTorch, Icarus 12, Verilator, and
Yosys. It is independent of the CUDA training image:

```sh
docker compose -f compose_ASIC.yaml build
docker compose -f compose_ASIC.yaml run --rm test
docker compose -f compose_ASIC.yaml run --rm rtl
docker compose -f compose_ASIC.yaml run --rm synthesis
docker compose -f compose_ASIC.yaml run --rm lint
```

If an ORFS checkout or installation is available, set `ORFS_ROOT` to its root and run:

```sh
ORFS_ROOT=/path/to/OpenROAD-flow-scripts bash asic/scripts/run_orfs.sh
```

The ORFS configuration targets the integrated convolution/PLIF **actor prototype** on ASAP7.
Its report is a representative node result, not a 25-actor-DAG full-model estimate. Full-chip
PPA requires the exported DAG top level, characterized SRAM macros, all merge/fanout routes,
and representative full-sequence activity. Activity-based power requires a representative
VCD/SAIF from the exported DSEC event stream; vectorless default-toggle power must be labeled
preliminary.
