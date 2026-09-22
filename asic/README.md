# EventSpikeSeg ASIC flow

The hardware implementation is native synthesizable SystemVerilog. Icarus Verilog and
cocotb provide executable RTL checks, Yosys performs technology mapping, and OpenROAD
Flow Scripts (ORFS) performs floorplanning through routed layout, parasitic extraction,
timing, and power analysis.

## Platform decision

- `asap7` is the primary open, reproducible **research PPA** platform. It is a predictive
  7 nm FinFET platform, not a manufacturable foundry PDK and not tapeout signoff.
- `sky130hd` plus the bundled `sky130ram` OpenRAM views records the superseded addressed-SRAM
  **tile/test-chip** experiment. It is retained for article evidence, not as the final actor.
- The final target is a standard-cell/latch resident-state ASIC on an accessible 22 nm-or-better
  foundry PDK. That target cannot be called selected or power-signoff-ready until the complete
  resident graph is elaborated, placed, timed, and measured in an appropriate library.

The distinction matters because the 140k target's 143,824 signed 24-bit Q7.16 synaptic weights
consume only about 0.41 MiB, while its frozen 440x640 graph has 30,976,000 logical PLIF states. The selected
direct-state design allocates one signed 32-bit Q15.16 combined accumulator/state per PLIF plus
a 6-bit integer age and unsigned 19-bit Q3.16 amplitude only on adaptation-enabled PLIFs:
150.89 MiB-equivalent of logical resident state. These are distributed registers/latches local to the PLIFs,
not a byte-addressed memory capacity or an SRAM-fetch design. The elimination of reads, writes,
tags, touched queues, and scrub cycles is intentional; the resulting physical area, clock-tree
load, combinational depth, and switching power remain an open full-chip implementation result.

The XL target uses the same precision and resident-state rules with 44 PLIF actors,
959,824 convolution weights, 78,707,200 logical PLIF states, and 15,910,400 adaptive
states (347.66 MiB-equivalent). `resident_spike_mask_attention.sv` implements its four-head,
eight-channel-per-head Q/K coincidence popcount and V-spike gate without softmax or an NxN map.
The epoch-1 XL export is structural bring-up only; replace its constants with the selected final
trained/QAT checkpoint before equivalence, accuracy, or PPA reporting.

## Current synthesis boundary

The current operational status and ordered full-chip resume procedure are maintained in
`docs/ACTIVE_TASKS.md`. As of 2026-09-13, the beta48 XL preflight and all 45 current 1x1
partition rows pass, but complete-top Yosys elaboration has exited 137 at 8, 16, and
24 GiB. OpenROAD full-chip placement has therefore not started. Reuse the completed
partition and `enc1.depthwise` gate-power artifacts; the next valid full-chip action is
complete native elaboration on a larger-memory host.

`resident_channelized_plif_actor.sv` is the active replacement actor. Its
`resident_convolution_synapses.sv` fabric gates compile-time signed 24-bit Q7.16 weights with a presynaptic
spike bitmap and produces every postsynaptic current delta in parallel. Ordinary PLIFs use
`resident_plif_population.sv`; layers with peer inhibition or threshold adaptation use
`resident_retinotopic_plif_population.sv`. Every logical PLIF owns one combined accumulator/state
and, where enabled, compact clocked adaptation elements for the life of the sequence. There is no
addressed state fetch.

`scripts/plan_asic_resident_tiles.py` partitions each actor spatially while preserving global
convolution coordinates and the exact PLIF count:

```bash
python scripts/plan_asic_resident_tiles.py \
  artifacts/ASIC/model_spec.yaml \
  artifacts/ASIC/resident_tile_plan_8x8.json \
  --tile-width 8 --tile-height 8
```

The derived output remains under the wholly ignored `artifacts/` tree. Tiling is a physical and
elaboration hierarchy only; it does not introduce runtime state loads or reduce total state.

The older `convolution_plif_actor.sv` and channelized/streaming actors remain temporarily as
equivalence references while the generated full graph is migrated.
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
The exporter emits matching signed 24-bit Q7.16 synapses, unsigned 24-bit UQ1.23 beta, signed
24-bit Q7.16 thresholds, and the corresponding adaptation constants for each actor.
`scripts/generate_asic_top.py` now defaults to the resident bitmap graph; pass
`--architecture legacy_sram` only for the prior exact scalar replay reference.

Prepare the complete XL export, graph top, tile plan, and logical memory manifest without
starting Yosys/OpenROAD:

```bash
docker compose -f compose_ASIC.yaml run --rm test \
  bash asic/scripts/prepare_xl_asic.sh
```

Build the guarded CPU verification image once, then run the resumable partition synthesis:

```bash
docker build --pull=false \
  -t eventspikeseg:torch2.2.2-cpu-verification-guarded \
  -f asic/tools/Dockerfile.synthesis_guard asic/tools
bash asic/scripts/run_xl_partitioned_synthesis.sh
```

The runner defaults to checkpoint-exact 1x1 spatial partitions, three 8 GiB
virtual-address-space workers, and serial 16 GiB retries for memory-limited actors. A 1x1
partition retains the complete channel group at one spatial coordinate while avoiding the
fourfold elaboration cost of a 2x2 partition for dense 128-channel convolutions. Per-actor
signatures and status journals make completed work
reusable. Summary writes are atomic and transient storage errors are retried. The guarded image
sets each synthesis process non-dumpable after `exec`; this is required on WSL because its piped
crash handler can capture multi-gigabyte dumps even when the ordinary core-size limit is zero.

After the XL structural partitions pass, route the representative 128-to-128 pointwise
partition with:

```bash
bash asic/scripts/run_orfs_xl_enc3_pointwise_1x1.sh
```

This produces an ASAP7 GDS/DEF/SPEF/netlist, extracted timing and DRC reports, and OpenROAD's
vectorless power estimate for one checkpoint-exact XL 1x1 actor partition. It is neither a
full-chip layout nor representative-event power; activity-annotated power still requires a
cycle-accurate VCD or SAIF.

The separately gated full structural elaboration command is
`bash asic/scripts/run_xl_synthesis.sh`. Do not launch it while training is using host memory.
It writes `xl_full_synthesis.log` inside the selected ignored XL export directory and is an
elaboration/synthesis check, not full-chip PPA.

Generated exports are ignored build products under `artifacts/ASIC`; the checkpoint-authoritative
six-class export contains all 25 actors and exactly 143,824 signed 24-bit synaptic weights. The existing
generated scalar/SRAM top is an executable logical reference, not the selected resident full-chip
implementation and not a reportable PPA netlist.

Before full-chip layout, complete bitmap graph generation, prove structural conservation, elaborate
the native dimensions without truncation, and size any boundary/result buffering without overflow.

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
docker compose -f compose_ASIC.yaml run --rm synthesis
docker compose -f compose_ASIC.yaml run --rm lint
```

Run with the official OpenROAD Flow Scripts Docker image (the default is
`openroad/orfs:latest`):

```bash
bash asic/scripts/run_orfs.sh
```

Run the separate SKY130HD actor-tile flow with two real 80x64 OpenRAM macros:

```bash
bash asic/scripts/run_orfs_sky130_sram.sh
```

Run the checkpoint-exact resident `detail_stem` characterization unit separately:

```bash
bash asic/scripts/run_orfs_resident_tile.sh
```

Run the checkpoint-exact Q7.16-weight/Q15.16-combined-state two-tile receptive-halo boundary
characterization on a larger-memory
machine with:

```bash
bash asic/scripts/run_orfs_resident_two_tile.sh
```

Before running it on another machine, place the trained checkpoint at
`artifacts/checkpointsV4/dsec_6class/EventSpikeSeg140k_seed17_best.pt`, regenerate the ignored
checkpoint export if it is absent, and allocate **at least 16 GiB of Docker system memory**;
24--32 GiB is recommended. GPU VRAM is not used by Yosys/OpenROAD. The command creates the ignored
two-column, two-2x2-tile `detail_stem` top and runs the separate
`resident_detail_stem_2x2x2` ASAP7 flow. It must produce `6_report.json` plus the final routed
reports before any area, timing, power, or DRC result is accepted.

This uses the trained weights and a 2x2/32-PLIF interior unit because 8x8 and 4x4 fully parallel
standard-cell elaboration are impractically slow under the current x86-on-Apple emulation. It is a
scaling experiment only; the production resident hierarchy remains 8x8. The accepted ASAP7 run
uses a 50% integer slew-repair margin and passes extracted setup, hold, slew, capacitance, fanout,
detailed-route DRC, power-connectivity, and GDS-integrity checks. Its 639.636 MHz, 7,311.29 um^2,
and 30.9607 mW vectorless results characterize this unit only, not the full model.

The production tiled wrapper uses exact compile-time receptive halos rather than sending each full
actor input bitmap to every spatial tile. For the checkpoint-derived nominal 8x8 hierarchy this
reduces logical tile-input endpoints from 73,444,096,000 to 51,871,626 (99.929%). This is a wiring
inventory only; it is not a routed power, capacitance, area, or latency result.

This variant uses the same 4x4 actor geometry only as a macro-integration test. It checks
that exactly two SRAMs survive synthesis, builds an explicit met3-to-met4 macro power grid,
and fails on extracted timing/driver violations or nonempty detailed-route DRC. It is not a
full-model capacity, latency, energy, or power result. The checked-in configuration skips
post-CTS timing repair only because the amd64 OpenROAD binary raises `SIGILL` under
Apple-silicon emulation; a native-x86 publication run must remove that switch.

Generated flow data is written below the Git-ignored `artifacts/OpenROAD` directory. To use a
host ORFS checkout instead, set `ORFS_ROOT` to its root:

```sh
ORFS_ROOT=/path/to/OpenROAD-flow-scripts bash asic/scripts/run_orfs.sh
```

The ORFS configuration targets the integrated convolution/PLIF **actor prototype** on ASAP7.
Its report is a representative node result, not a 25-actor-DAG full-model estimate. Full-chip
PPA requires the exported DAG top level, characterized SRAM macros, all merge/fanout routes,
and representative full-sequence activity. Activity-based power requires a representative
VCD/SAIF from the exported DSEC event stream; vectorless default-toggle power must be labeled
preliminary.

For the corrected XL `enc1.depthwise` beta48 representative partition, run:

```bash
bash asic/scripts/run_xl_enc1_gate_power.sh
```

The launcher requires a passing ten-bin RTL JUnit result and validates trace/checkpoint/event plus
routed ODB/SPEF/SDC/netlist hashes. It generates OpenSTA SDF as timing evidence, runs exact
post-route functional gate equivalence for the activity VCD, and then requires complete OpenROAD
VCD pin annotation before accepting power. Icarus cannot reproduce all ASAP7/OpenSTA SDF forms,
so extracted OpenSTA timing reports remain authoritative for setup and hold.

### XL native hard hierarchy

Generate the checkpoint-bound hard-macro inventory and assembly map without elaborating the
native RTL hierarchy:

```bash
python scripts/prepare_xl_hard_hierarchy.py \
  --model-spec artifacts/ASIC_XL/model_spec.yaml \
  --tile-plan artifacts/ASIC_XL/resident_tile_plan.json \
  --output-dir artifacts/ASIC_XL/hard_hierarchy
```

The catalog conserves all 44 actors, 49,610 logical 8x8 actor tiles, 4,400 logical 8x8 readout tiles,
and the 440x640 geometry. The packed-register 8x8 readout leaf passes structural synthesis at
3,649.98 MB peak, but its ORFS technology mapping reached 11.99/12 GiB and was stopped before
OOM while full simulation and training were active. The active physical hierarchy therefore
groups each logical readout tile from sixteen exact 2x2 hard masters: 70,400 physical readout
macros. The first exact 8x8 actor master also exceeded 20 GiB during technology mapping.
The actor hierarchy therefore uses deterministic adaptive leaves: 4x4 for seven light
depthwise actors, 2x2 for fourteen moderate actors, and 1x1 for twenty-three dense actors.
Its 952,720 actor leaves give 1,023,120 physical macros overall while preserving all
78,707,200 PLIF identities. Exact-name 4x4 readout ORFS still OOM-killed at a 20 GiB
limit, so it remains structural/capacity evidence rather than an active physical master. The preparation emits parameter-free logical
blackboxes, one deterministic row per physical
instance, commands for generating each unique checkpoint-exact master RTL, and explicit ORFS
LEF/GDS/Liberty bindings. `hard_macro_view_readiness.json` is a hard gate: native assembly must
not start until every listed view exists and its module/port contract matches the generated
blackbox. The assembly replaces only tiled leaves; graph routing, joins, completion-token
rendezvous, prediction order, and dedicated resident state remain in the native top.

Generate the fixed native assembly after preparing the catalog:

```bash
python scripts/generate_xl_macroized_native_top.py \
  --model-spec artifacts/ASIC_XL/model_spec.yaml \
  --tile-plan artifacts/ASIC_XL/resident_tile_plan.json \
  --catalog artifacts/ASIC_XL/hard_hierarchy/hard_macro_catalog.json \
  --instances artifacts/ASIC_XL/hard_hierarchy/hard_macro_instances.tsv \
  --source-top artifacts/ASIC_XL/generated_eventspikesegxl_dag_top.sv \
  --output-top artifacts/ASIC_XL/hard_hierarchy/generated_eventspikesegxl_macroized_top.sv \
  --output-wrappers artifacts/ASIC_XL/hard_hierarchy/generated_xl_macro_wrappers.sv \
  --output-preflight artifacts/ASIC_XL/hard_hierarchy/macroized_assembly_preflight.json
```

The actor wrappers retain complete-vector ready/valid and completion-token behavior, broadcast
accepted transactions only when every physical leaf is ready, wire each clipped receptive halo,
group adaptive leaves beneath the unchanged logical 8x8 boundaries, and reconstruct each global
channel-major result. The readout wrapper preserves lockstep input,
global row-major prediction arbitration, frame completion, and same-tag checking across all
70,400 physical leaves. The digest-bound preflight checks every instance geometry and conserves
the full actor state, readout pixels, soft routing, joins, and attention. Top-level ORFS remains
gated on all 825 catalogued LEF/GDS/Liberty views.
