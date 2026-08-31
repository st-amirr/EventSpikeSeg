# EventSpikeSeg ASIC flow

The hardware implementation is native synthesizable SystemVerilog. Icarus Verilog and
cocotb provide executable RTL checks, Yosys performs technology mapping, and OpenROAD
Flow Scripts (ORFS) performs floorplanning through routed layout, parasitic extraction,
timing, and power analysis.

## Platform decision

- `asap7` is the primary open, reproducible **research PPA** platform. It is a predictive
  7 nm FinFET platform, not a manufacturable foundry PDK and not tapeout signoff.
- `sky130ram` is the future open, manufacturable **tile/test-chip** check when the actor
  SRAM boundary is bound to characterized macros. It is not dense enough for
  the complete native-resolution state on one economical die.
- A complete manufacturable EventSpikeSeg chip requires an accessible 22/28 nm-or-better
  foundry PDK plus characterized high-density SRAM macros. That target cannot be called
  selected or power-signoff-ready until those libraries are available.

The distinction matters because 143,824 int8 synaptic weights consume only about
0.137 MiB, while the frozen 440x640 graph has 30,976,000 logical membranes. Persistent
int16 membrane, adaptation fields, and 24-bit lazy-update tags require 189.60 MiB. Exact
same-bin collection additionally requires 88.62 MiB of 24-bit current and 3.69 MiB of
touched flags when implemented as direct-index storage, for 281.92 MiB excluding the
touched-address queues. Standard-cell flip-flops are not an acceptable full-chip memory
implementation. A smaller profiled sparse collection FIFO is valid only with an explicit
capacity, overflow behavior, and representative event-stream occupancy evidence.
The current full-depth, no-overflow RTL upper bound is 338.07 MiB excluding weight ROM;
it also includes touched queues, retinotopic markers, temporal scores, and default residual
buffers.

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
`scripts/generate_sram_manifest.py` derives every actor depth, record width, logical bank
count, persistent/transient total, and worst-case touched-queue bound from that same export.

`scripts/generate_asic_top.py` now consumes an exported `model_spec.yaml` and emits the exact
25-actor structural top with fixed ROM constants and all routing primitives. The generated
miniature-state regression exercises the complete completion-token DAG. Mechanism-enabled
actors use grouped retinotopic commits; the final readout accumulates signed class currents
and enumerates a dense prediction after the configured bin window. Large ROM constants are
emitted as bounded concatenation chunks so Icarus can lex the trained top without changing
word order. `actor_local_state_sram` defines the compiler-macro interface, and
`initialized_actor_state_bank` partitions large logical memories into at most 65,536-row
banks, zeroizes those banks in parallel at sequence start, and provides single-port request
arbitration. Ordinary and mechanism-enabled actor state, touched queues, retinotopic touched
markers, the temporal readout, and residual-union storage now cross this explicit SRAM
boundary. Simulation still selects its behavioral branch; physical PPA requires a real SRAM
compiler macro binding.
The generated top-level `USE_STATE_MACRO` parameter propagates to all 25 actors, nine
residual unions, and the temporal readout; leave it at `0` for simulation and set it to `1`
only when `eventspikeseg_1rw_sram_macro` is bound to a compatible characterized macro.

The active trained six-class v4 export is retained under
`artifacts/ASIC`; its generated weighted top contains all 25 actors and
exactly 143,824 int8 synaptic ROM words. The prior 11-class export is documented as
historical and is not kept in the active artifacts tree. The active top is the executable logical reference,
not a full-chip PPA netlist: its logical memories must not be expanded into standard cells or
reported as a physical implementation.

Before full-chip PPA, bind the SRAM boundary to characterized macros and size the residual
dedup capacity from full-sequence activity without overflow. The current default residual
capacity remains a 64-event equivalence setting, not a native-resolution bound.

Generate the technology-independent memory manifest from the active checkpoint export:

```sh
PYTHONPATH=src python scripts/generate_sram_manifest.py \
  --export artifacts/ASIC
```

Run native SystemVerilog compilation and the cocotb suite:

```sh
bash asic/scripts/check_rtl.sh
python scripts/run_rtl_tests.py
```

Set `ASIC_BUILD_DIR` to redirect generated netlists outside the repository when needed.

The isolated CPU-only implementation container pins CPU PyTorch and Icarus 12 and also
contains Yosys. It is independent of the CUDA training image:

```sh
docker compose -f compose_ASIC.yaml build
docker compose -f compose_ASIC.yaml run --rm test
docker compose -f compose_ASIC.yaml run --rm rtl
docker compose -f compose_ASIC.yaml run --rm replay
docker compose -f compose_ASIC.yaml run --rm synthesis
docker compose -f compose_ASIC.yaml run --rm lint
```

A passing full-DAG replay writes `artifacts/RTL/smoke/rtl_metrics.json` with initialization
cycles, steady-state cycles/frame, cycles/bin, utilization, and headroom. Those values are
explicitly reduced-8x8 verification metrics and must not be reported as native-resolution
latency or PPA.

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
