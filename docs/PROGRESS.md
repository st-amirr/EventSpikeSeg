# Progress

## Working now

- active DSEC target merged from eleven source labels into six broad semantic classes
- manifest-backed DDD17 temporal loading: consecutive two-channel histogram bins or six-channel windows
- `model.py` exposes the sole ASIC target `EventSpikeSeg140k` and optional XL software comparison
- frozen completed ten-model structural benchmark in `top_ten_models.py`
- completed structural top-five registry in `top_five_models.py`
- completed/frozen accuracy-oriented top-three registry in `top_three_models.py`
- PLIF with learnable beta and base thresholds
- local triangular threshold adaptation
- stem-only peer-membrane inhibition
- native 440x640 DSEC input with learned stride-2 semantic stem
- 8-channel native detail path and memory-bounded 32/64/128 semantic path
- continuous temporal class-current readout after binary-spiking hidden features
- equal-per-present-class macro CE/focal without static class weights in every suite
- ordinary-sized checkpoints without captured membrane/adaptation runtime tensors
- explicit 3- or 4-stage channel schedules
- configurable stem and first-block kernel size
- dynamic `enc4_spikes` activity/evaluation diagnostics for the deep contender

## Completed evidence

### Historical structural incumbent

`v10_fpga_hybrid`: mIoU 0.3130, pixel accuracy 0.7871, 44,016 parameters, output spike rate 0.1412 under the full round-one protocol.

### Latest neuron-mechanism screen

Protocol: seed 17, 5 epochs, 256 train, 128 held-out, 64×64, 8 internal timesteps.

| architecture | mIoU | pixel accuracy | spike rate |
| --- | ---: | ---: | ---: |
| `f05_v02_light_peer_membrane_inhibition` | 0.1991 | 0.7607 | 0.0616 |
| `f02_v10_plif_threshold_adaptation` | 0.1459 | 0.7395 | 0.0470 |
| `f01_v10_plif_threshold_wta` | 0.1402 | 0.7334 | 0.0457 |
| `f04_v03_dilated_threshold_adaptation` | 0.1366 | 0.7217 | 0.0513 |
| `f03_v10_plif_winner_peer_inhibition` | 0.1233 | 0.7384 | 0.0415 |

Selected mechanism base: PLIF + learnable threshold + stem peer-membrane inhibition + encoder triangular threshold adaptation.

## Completed structural top five

Protocol: seed 17, 8 epochs, 2,048 train, 512 held-out, 64×64, 15 timesteps, batch 14, LR 0.002.

| architecture | mIoU | parameters | useful evidence |
| --- | ---: | ---: | --- |
| `f05_compact16_dilated` | **0.2596** | **21,491** | best overall/efficiency |
| `f02_wide32_multiscale` | 0.2284 | 77,751 | best object IoU in round |
| `f04_deep4_dilated` | 0.2079 | 107,131 | strongest aggregate rare-class signal |
| `f01_base24_multiscale` | 0.1626 | 46,423 | weak controlled baseline |
| `f03_early5x5_multiscale` | 0.1482 | 49,111 | early 5×5 rejected |

None beat the 0.3130 historical result under the then-current repeated-static input protocol. The architecture evidence remains useful, but those mIoU values are not direct baselines for the current temporal input protocol.

## Completed accuracy top three

- `t02_dualpath_detail` — **0.2728 mIoU**, 24,211 params; winner and evidence for a persistent high-resolution spiking detail stream.
- `t01_spike_pyramid_concat` — 0.1671 mIoU, 63,147 params; parallel multiscale concat did not recover accuracy.
- `t03_deep_attention_fpn` — 0.1555 mIoU, 108,781 params; extra depth/attention collapsed predictions toward dominant classes.

## Canonical native-resolution candidate implemented

- native 2→8 standard-convolution PLIF detail stem and 8-channel detail refinement;
- learned standard 5×5 stride-2 2→32 PLIF semantic stem before spatial reduction;
- standard 32-channel early feature block and standard stride-2 32→64 transition;
- 32/64/128 semantic path with deeper residual DW/PW refinement and dilation-2 context;
- additive quarter/half encoder skips and late semantic32/detail8 concatenation;
- concatenative quarter-scale 128->64 standard 1x1 PLIF fusion;
- multiplicity-preserving half-scale spike skip;
- standard 3x3 40->16 native semantic/detail fusion before one PLIF threshold;
- continuous 16→11 temporal class-current readout rather than a ten-level class-spike count;
- training-only quarter-scale semantic auxiliary head and native boundary head;
- SpikingJelly `Conv2d`/PLIF/surrogate infrastructure where compatible, with project-specific per-channel beta, peer inhibition, threshold adaptation, and operation order preserved;
- canonical-only 70/20/10 joint → backbone-frozen refinement → low-LR joint-unfreeze schedule;
- exact 10-way replay in the DSEC compose service so each backward replay holds one 5 ms update.

## Validation/cleanup state

- all architecture suites now dispatch through `train.py`; the duplicate standalone top-three trainer is retired;
- every suite uses macro per-present-class CE (and macro focal where configured); static class-weight estimation is removed from training;
- the generated `ddd17_temporal_manifest.json` is the required chronology source; the runtime neither generates it nor infers sequence boundaries from filenames;
- `timestamp-events` is the sole input representation; HDF5/raw and multi-file window paths are removed;
- one 50 ms record is scheduled over ten 5 ms input clocks and PLIF state persists across consecutive records;
- final best-checkpoint selection uses whole held-out sequences when available, otherwise one contiguous block;
- checkpoints fingerprint the manifest/split/physical-clock protocol and reject all older input protocols;
- auxiliary heads are skipped in evaluation/inference;
- native-resolution checkpoints are supported by `evaluate.py` when `output_size` is `None`;
- single-sequence contiguous validation and exact checkpoint holdout reconstruction are covered by regression tests; limited per-epoch training preserves temporal order;
- obsolete `benchmark_top_three.py`, MEVDT/EventSCNN scripts, the dead `rtl-test` PowerShell wrapper, and checked-in `.ruff_cache` were removed; the completed DDD17 architecture-search plan is archived under `docs/exec-plans/completed/`.

## Open issues

- rare-class IoU remains the dominant accuracy limitation;
- the completed top-three hypotheses are measured only under the removed repeated-static protocol; the scaled canonical candidate has not yet been measured under the current temporal protocol;
- the installed training data is incomplete: 2,887 event tensors versus 10,001 masks, leaving only one event recording usable;
- with an 11-class DSEC head, XL registers 237,115 parameters and executes 226,767 at inference;
- learned continuous neuron dynamics and learned attention thresholds remain unquantized;
- the native-resolution v7 140k checkpoint has not yet completed a training epoch, so its 50% target remains unmeasured.

## Next action

Run the native 440x640 11-class `EventSpikeSeg140k` configuration from scratch. Verify
that loss, gradients, class prediction shares, and rare-class IoUs move during epoch 1
before committing to the full 80 epochs. Then validate its revised fixed-point export.

## 2026-08-23 — native-resolution accuracy revision

- retained the public `EventSpikeSeg140k` FPGA target and checkpoint directory;
- changed DSEC training geometry from 241x351 to native 440x640;
- added an 8-channel native detail route and learned 5x5 stride-2 semantic stem;
- changed the early 32-channel block and 32->64 downsample to standard convolution;
- moved the semantic bottleneck to 55x80, preserving a three-level 32/64/128 hierarchy;
- replaced the spiking class head with continuous temporal class-current accumulation;
- added a training-only native boundary objective at coefficient 0.1;
- set DSEC replay chunks to 10 so each gradient replay retains only one update graph;
- revised FPGA export to 25 PLIF actors plus one current readout;
- revised state accounting to 30,976,000 membranes and 10,982,400 adaptation states.

## 2026-08-15 timestamp-stream v3

- one dataset item is one 50 ms NumPy interval and its same-record indexed mask;
- stored `hist0,hist1,mean0,std0,mean1,std1` is decoded into per-polarity activity/mean/std;
- mean and mean±std schedule conserved synaptic activity before the first PLIF layer;
- DataLoader order is chronological, batch size is one, and fractions are contiguous;
- recurrent numeric state carries across records; training detaches its graph after each record;
- SpikingJelly's internal PLIF `v`/`w` references are also detached, removing a retained-graph RAM peak;
- `--internal-updates` defaults to 10 and is frozen into each checkpoint protocol;
- HDF5/raw readers, event-bin/sequential window datasets, T/stride flags, and raw compatibility commands are removed;
- model parameter count depends on class-head width: XL is 236,445 for six classes and 237,115 for eleven.


## 2026-08-22 — 140k static-actor FPGA Iteration 0

- froze `EventSpikeSeg140k` as the only FPGA target: 140,589 registered / 134,807
  executed inference parameters, 127,456 executed convolution weights, 37 PLIF actors;
- initially selected Alveo U55C, then superseded it with conventional Nexys Video
  XC7A200T when the no-accelerator-card requirement was clarified;
- fixed the topology to 37 permanent layer actors with no cross-layer compute sharing,
  reconfiguration, or partial reconfiguration;
- assigned local initialized weight ROM, convolution addressing, accumulator lanes,
  PLIF/mechanism logic, and output queue to every actor;
- corrected `project2` state to its actual pre-upsample half resolution and measured the
  exact fixed-step incompatibility: about 192.44 MiB dense membrane/adaptation state versus 1.604 MiB XC7A200T BRAM (~120x); the earlier 470.31 MiB figure included a now-superseded 32-bit timestamp per membrane;
  no external/onboard DDR is allowed, so lossless sparse live
  state must pass a measured hard-capacity gate before full deployment is feasible;
- added `src/eventspikeseg/fpga`: fixed formats, deterministic 37-actor export,
  affine-folded int8 ROMs, per-actor parameters, integer PLIF, and sparse state profiler;
- FPGA export hard-rejects XL and omits dead `refine2`, auxiliary training head, and
  surrogate gradients;
- added the canonical externally state-backed, ready/valid PLIF RTL lane with learned
  retention coefficient, integer rounding, saturation, soft reset, and backpressure;
- 72 Python tests and all 6 GHDL/cocotb RTL groups pass in Docker.

## 2026-08-22 — 140k static-actor FPGA Iteration 1 state bank

- added a ready/valid, set-associative, zero-default sparse neuron-state bank in VHDL;
- stores address tags, membrane, last timestamp, adaptation age, and adaptation amplitude;
- supports exact hit update, missing-address reset reads, and exact dead-state reclamation;
- forbids live-state eviction: a full set raises an explicit capacity overflow without
  altering resident state;
- added collision/reclamation cocotb coverage; all 7 GHDL RTL groups pass and Python lint
  passes in the CPU-only Docker verification service;
- next integration is state-bank read -> lazy-retention selection -> PLIF update ->
  state-bank writeback inside one actor-local event lane.
- the epoch-2 one-record sparse profile reached 27,182,700 live entries (37.32% of all
  logical membranes) and 320.08 MiB of tagged state, requiring 295.98x the usable Artix-7
  state budget after weights and reserve; even one bit for every logical membrane would
  require 8.68 MiB, so an exact no-DDR XC7A200T deployment is now rejected rather than
  treated as a likely compression target.

## 2026-08-19 FPGA implementation direction (superseded target/platform details)

- public model names remain `EventSpikeSegXL` and `EventSpikeSeg140k`; XL is the active implementation target;
- XL DSEC accounting: 237,115 registered / 232,059 training-forward / 226,767 inference-forward parameters;
- FPGA deployment omits inherited dead `refine2` and the training-only auxiliary head;
- primary hardware target is custom VHDL-2008 on Xilinx ZCU104;
- PLIF membrane/current/beta/threshold/adaptation are digital fixed-point SNN states, not physical voltages/currents;
- convolution kernels remain shared synaptic weights, while emitted hidden spikes are event addresses that trigger weight additions;
- no softmax exists in the canonical deployed path;
- coarse-grained synaptic-accumulator + PLIF processing elements are time-multiplexed across spatial tiles/channels/stages while persistent state stays in banked memory;
- first hardware milestone is bit-exact integer/RTL equivalence; sparse touched-address/lazy-decay/clock-enable optimizations follow only after exactness;
- DSEC training and baseline FPGA runtime both use ten fixed 5 ms updates per 50 ms record; sparse synaptic work is retained inside each update;
- memory-bounded replay forms one complete-record objective before propagating its gradients through chronological chunks;
- remaining RTL-sensitive mechanisms are fixed-step PLIF decay, peer-membrane inhibition, triangular threshold adaptation, and the local PLIF selector;
- XL adds projected bridge joins, parallel-context joins, local Q/K/V rendezvous, and an external-DDR state-store requirement;
- evaluation flow is RTL simulation -> synthesis/place-route -> post-implementation timing -> representative SAIF/VCD Vivado power -> optional ZCU104 measurement.

### 2026-08-20 logical-state accounting

- compact-reference accounting separates 37 executed PLIF populations from the ~140k shared parameter count;
- general membrane formula: `(672+Nclass)*H*W + 480*H2*W2 + 1280*H4*W4`;
- six-class 212x282 DDD17 requires **51,089,456 independent membrane values**;
- threshold-adaptation scopes cover **9,836,800 logical neurons** at that resolution, each with adaptation age and amplitude;
- implementation contract: static/shared weights and channel parameters, persistent per-`(layer,c,y,x)` neuron state, temporary current accumulators, sparse event FIFOs;
- exact sparse layer execution accumulates all weight contributions for a timestep before one PLIF threshold/reset update, then writes persistent state back and emits only fired addresses;
- a small physical PE array may be time-multiplexed, but logical state addresses may not be aliased; fixed 5 ms state advancement is part of the bit-exact DSEC baseline.

### 2026-08-21 XL DSEC implementation accounting

- then-active resized DSEC dimensions: 241x351 -> 121x176 -> 61x88 (historical XL accounting; current v7 uses native 440x640);
- 50 inference PLIF populations and 226,767 executed inference parameters;
- 85,639,973 membrane states plus 40,049,152 threshold-adaptation age/amplitude values;
- the fixed-step baseline does not require a per-membrane last-update timestamp; layer/tile state can remain resident across t0..t9;
- historical timestamped-prototype persistent store estimate: 566.42 MiB (not the current fixed-step state format);
- historical XL implementation assumption: external DDR backing store with banked on-chip active-tile cache; XL is not the current FPGA target.


### 2026-08-22 fixed 50 ms FPGA runtime decision

- one DSEC semantic record = 50 ms = ten chronological 5 ms SNN updates;
- baseline FPGA runtime now matches this trained timing contract rather than direct per-event asynchronous propagation;
- preferred hardware order is layer-major across the full T=10 record: load/cache one layer or spatial state tile, process t0..t9, write state back once, then advance to the next layer;
- sparse event-addressed convolution remains active inside each 5 ms slice;
- one segmentation output is produced per 50 ms record after temporal class-spike counting;
- baseline fixed-step state no longer requires one 32-bit timestamp per membrane; lazy step-tagging is future optional optimization;
- sustained real-time target is 20 records/s, with optional double buffering of acquisition and compute.

## 2026-08-23 — v7 fixed-step Artix-7 implementation iteration 2

- rebased hardware docs on the native 440x640 v7 `EventSpikeSeg140k` graph;
- canonical deployment is 25 PLIF stages + stateless 16->11 temporal current readout;
- documented 30,976,000 membrane states and 10,982,400 adaptation-enabled neurons;
- recorded the state-first trade: +6.4% synaptic weights versus v6, but -40.5% logical membranes and -35.2% dense persistent state;
- made Artix-7 XC7A200T the explicit FPGA target, using Nexys Video only as the reference carrier board;
- removed `last_timestamp_us` from the integer reference and sparse RTL state record;
- changed exact PLIF RTL/reference to consume learned beta once per fixed 5 ms step;
- replaced the old shift-only local LIF baseline with a learned-beta local PLIF lane;
- added `fixed_record_controller.vhd` for 27-layer x 10-step layer-major scheduling;
- added signed class-current argmax RTL for the new non-spiking readout;
- updated exporter manifest timing/state contracts and sparse-state entry accounting;
- v7 full-sequence sparse occupancy/BRAM fit remains the next hard feasibility measurement.


## 2026-08-23 — FPGA iteration 3: streaming 5 ms bins and lazy state tags

- replaced the active 50 ms layer-major scheduling contract with bin-major end-to-end execution;
- added a streaming runtime reference with configurable prediction windows (default 10 bins / 50 ms);
- added explicit real-time metrics `U=C_bin/(f_clk*5ms)` and `H=1/U`, with hard `U<=1` and target `U<=0.8`;
- added 24-bit `last_bin_tag` to sparse neuron state and restored exact touched-neuron lazy leak semantics without microsecond timestamps;
- changed the integer PLIF reference to repeated learned-beta decay for `delta_bins`;
- changed `plif_update.vhd` to a multi-cycle iterative lazy-leak lane;
- changed the sparse state bank to store/read the compact bin tag;
- added `streaming_bin_controller.vhd`; its actor-count generic is now configured for actor 0..24 bin-major scheduling, cycles/bin instrumentation, deadline/target flags, global bin tags and prediction-due;
- the old `fixed_record_controller` schedule is superseded;
- v8 exact dense touched-state reference is 189.60 MiB including a dense 24-bit tag, while conservative sparse aligned entries remain budgeted at 12 bytes non-adaptive / 16 bytes adaptive;
- full actor integration, ping-pong ingress storage, sparse class-current storage, and GHDL/Vivado verification remain open.

## 2026-08-25 — FPGA iteration 4: streaming integration lanes

- added a lossless two-bank event ingress that overlaps capture with processing, preserves empty 5 ms bins, and forbids reuse until end-to-end release;
- added an actor-local touched-neuron lane sequencing sparse lookup, modular bin-tag distance, iterative learned-beta PLIF update, and exact live-state writeback/reclamation;
- corrected the sparse missing-entry contract so adaptation age resets to the canonical inactive value `-1`;
- added a weight-independent 11-class current-update lane with signed saturation, temporal prediction flush, sparse-state-live output, and first-index tie behavior;
- updated superseded timestamp/retention cocotb tests to the active bin-tag/beta interfaces;
- added executable coverage for the streaming controller, class argmax, ingress buffer, touched-neuron lane, and class-current update;
- all 12 RTL unit groups pass with GHDL 6.0.0 and cocotb 1.9.2; the updated cocotb sources pass Ruff;
- next integration is exported weight ROM + convolution destination accumulation into 25 instantiated actor lanes, followed by exact inhibition/adaptation, sparse per-pixel readout storage/flush, full-graph equivalence, and measured occupancy/cycles per bin.

## 2026-08-25 — ASIC iteration 5: autonomous tap-scatter PLIF actor

- changed the primary hardware direction from globally scheduled FPGA execution to 25 permanent ASIC actors connected by spike and completion-token channels;
- defined the exact 3x3 mapping as nine parallel presynaptic tap projections feeding one canonical postsynaptic current/membrane array;
- added `presynaptic_tap_array.vhd` with padding, stride divisibility, dilation, bounds, signed shared weight, and zero-weight suppression;
- added `asynchronous_plif_actor.vhd` with duplicate contribution accumulation, a first-touch commit queue (no dense destination sweep), actor-local direct-indexed state, lazy learned-beta PLIF updates, and lossless spike/completion backpressure;
- added cocotb tests for 3x3 address fanout, border/zero suppression, completion-gated firing, shared membrane accumulation, and channel backpressure;
- both new VHDL blocks pass GHDL 6 synthesis elaboration, and all 14 RTL unit groups pass with cocotb 1.9.2;
- added a VHDL-preserving GHDL-to-Verilog flow and an ASAP7 ORFS actor configuration for open predictive PPA;
- documented that full-model PPA is blocked on explicit actor-local SRAM macros and a scale-suitable 22 nm-or-better manufacturable PDK; behavioral arrays may be used only for control/equivalence prototypes.

## 2026-08-25 — Native SystemVerilog ASIC implementation

- replaced the VHDL/FPGA hardware tree with native synthesizable SystemVerilog under `asic/rtl`;
- integrated static convolution kernel taps with the actor-local PLIF current/membrane/tag population in `convolution_plif_actor`;
- retained autonomous ready/valid spike traffic and ordered completion-token commits, with no global layer scheduler or runtime reconfiguration;
- migrated exporter, fixed-point contracts, capacity accounting, and integer reference from `eventspikeseg.fpga` to `eventspikeseg.asic`;
- removed obsolete FPGA scheduler, ingress, sparse-bank, lane, accumulator, and VHDL simulation sources;
- changed local RTL verification to Icarus Verilog + cocotb and the open PPA front end to native SystemVerilog + Yosys/OpenROAD;
- all eight native RTL groups pass, including an integrated nine-tap-to-nine-membrane convolution/PLIF test;
- full 25-actor channel fanout, SRAM macro wrappers, mechanism integration, graph equivalence, and routed PPA remain the next implementation stage.
- preserved the complete retired FPGA feasibility/scheduling history inside `project_spec.yaml` under `legacy_fpga_history`, with detailed chronology in the decision/progress logs and sources recoverable from Git history;
- clarified ASIC ingress as timestamp-ordered raw-event synaptic accumulation with no dense bin preload, while retaining one touched-PLIF commit at each trained 5 ms completion boundary.

## 2026-08-25 — Explicit non-linear ASIC DAG contract

- re-fetched the current v8 `EventSpikeSeg140k` forward graph before editing;
- corrected the ASIC interpretation: the 25 PLIF populations are permanent actors in a
  directed acyclic graph, not a sequential `actor0 -> ... -> actor24` pipeline;
- added `src/eventspikeseg/asic/topology.py` with the exact actor nodes, directed edges,
  input/detail-semantic fork, residual bypass joins, `x1`/`x2` skip fanout, 2x event
  upsample routes, decoder/final channel remaps, and multiplicity-preserving `project2+x1`;
- changed export schema to 2.1.0 and made `layer_order` explicitly a deterministic
  topological/export order only; `layer_graph.json` now carries nodes, edges, join semantics,
  and graph kind;
- added SystemVerilog `event_fork2`, `event_join2`, and correctness-reference
  `binary_event_union2` primitives so completion tokens can fork and same-bin branches can
  rendezvous without pretending the graph is linear;
- residual joins are explicitly binary-OR/deduplicating, while decoder `project2+x1` keeps
  coincident events as multiplicity two;
- full 25-actor DAG instantiation, model-scale channel fanout/remap, scalable residual dedup,
  SRAM macro replacement, full-DAG equivalence, and activity-based PPA remain open.

## 2026-08-26 — Channel-aware sparse routing and convolution scatter

- added executable cocotb coverage for the lossless fork, same-bin join, and residual
  binary-OR/dedup blocks, including fail-closed mismatched completion tags;
- added fixed channel-ID offset routing for concatenation and nearest-neighbor 2x event
  expansion that forwards each completion token exactly once;
- added channel-aware standard, grouped, and depthwise convolution scatter with static
  weights flattened in PyTorch `[out][in/groups][ky][kx]` order;
- retained stride, padding, dilation, bounds, channel-group, and zero-weight filtering without
  a dense sliding scan;
- all 16 native Icarus/cocotb RTL groups pass, including separate standard, grouped, and
  depthwise channel-routing cases;
- the next integration boundary is channelized actor-local state/parameter access followed by
  physical instantiation and wiring of the exported 25-actor DAG.

## 2026-08-26 — Channelized convolution/PLIF actor integration

- extended the autonomous PLIF state engine with compile-time per-output-channel beta and
  threshold tables while retaining its scalar compatibility interface;
- integrated channel-aware convolution projections into one canonical actor-local state index
  for every `(output_channel,y,x)` destination and decoded spikes back to event coordinates;
- verified independent membrane persistence and different thresholds for two channels at the
  same spatial coordinate across consecutive completion-tagged epochs;
- extended export with one 16-bit beta ROM image and one signed 16-bit threshold ROM image per
  PLIF actor, alongside the existing JSON parameters and int8 weight ROM;
- all 17 native Icarus/cocotb RTL groups pass;
- next is the generated structural top that instantiates the 25 permanent actors and their
  exact fork/join/concat/upsample DAG routes.

## 2026-08-26 — Generated full DAG, mechanisms, and temporal readout

- added one unified packed event/completion stream wrapper around permanent PLIF actors;
- added a manifest-driven SystemVerilog generator that instantiates all 25 actors and inserts
  every exact fork, residual OR, multiplicity join, concat offset, and 2x upsample route;
- verified a generated reduced-state 25-actor graph compiles and carries two ordered bins
  through the complete non-linear topology to a prediction frame completion;
- added atomic retinotopic all-channel commits for mechanism-enabled actors, including summed
  triangular threshold processes and shared-RMS peer-membrane inhibition;
- added the non-spiking signed temporal class-current bank, configurable ten-bin window, dense
  pixel argmax enumeration, and prediction reset;
- added a technology-independent 1R1W state-memory boundary with behavioral simulation and a
  compiled-SRAM black-box branch;
- 22 cocotb RTL groups plus the generated-DAG compile/simulation test pass locally;
- real-checkpoint export/equivalence and physical SRAM binding remain gated separately from the
  completed structural RTL reference.

## 2026-08-26 — Legacy 11-class trained v4 checkpoint ASIC export

- exported `artifacts/checkpointsV4/dsec/EventSpikeSeg140k_seed17_best.pt` in the pinned
  PyTorch/SpikingJelly container;
- revalidated 150,245 registered parameters, 149,503 executed parameters, 143,904 int8
  synaptic weights, 25 PLIF actors, and 30,976,000 logical membrane states;
- emitted exactly 143,904 weight-ROM words plus beta/threshold ROMs and mechanism parameters
  for every actor; the export enables peer inhibition in one actor and triangular adaptation
  in fifteen actors;
- generated the real weighted 370 KiB `artifacts/asic_export_v4/eventspikeseg140k_dag_top.sv`;
- the complete pinned-container regression passes 79 tests and Ruff reports no issues;
- full-chip implementation is now bounded by characterized SRAM binding, scalable residual
  capacity proof, golden-stream bit-exact replay, and an accessible manufacturable PDK—not by
  missing graph, weight, or actor RTL generation.

## 2026-08-29 — Active six-class export and CPU-only implementation verification

- added `compose_ASIC.yaml` and `docker/app/dockerfile_ASIC`, independent of the
  CUDA training image;
- pinned CPU PyTorch 2.2.2, CPU torchvision 0.17.2, upstream Icarus Verilog 12, cocotb,
  and Yosys in the implementation image;
- exported the trained six-class v4 checkpoint to `artifacts/asic_export_v4_6class` with
  149,835 registered parameters, 149,423 executed parameters, 143,824 weight words,
  25 PLIF actors, one inhibition actor, and fifteen adaptation actors;
- generated the active 378,396-byte weighted 25-actor SystemVerilog DAG top;
- removed an unpacked combinational effective-age temporary that crashed Icarus and replaced
  it with equivalent per-channel scalar recomputation;
- the CPU implementation image passes 83 Python/structural tests, 22 cocotb RTL groups,
  Ruff, and the representative Yosys synthesis gate;
- the prior 11-class `artifacts/asic_export_v4` result is retained as historical evidence;
- full-chip physical completion still requires a characterized SRAM compiler/library,
  a selected manufacturable PDK, real golden event streams, and routed activity data.
