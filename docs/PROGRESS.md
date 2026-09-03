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
- added a technology-independent synchronous single-port 1RW state-memory boundary with behavioral simulation and a
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
- generated the historical real weighted 370 KiB 11-class SystemVerilog DAG top;
- the complete pinned-container regression passes 79 tests and Ruff reports no issues;
- full-chip implementation is now bounded by characterized SRAM binding, scalable residual
  capacity proof, golden-stream bit-exact replay, and an accessible manufacturable PDK—not by
  missing graph, weight, or actor RTL generation.

## 2026-08-29 — Active six-class export and CPU-only implementation verification

- added `compose_ASIC.yaml` and `docker/app/dockerfile_ASIC`, independent of the
  CUDA training image;
- pinned CPU PyTorch 2.2.2, CPU torchvision 0.17.2, upstream Icarus Verilog 12, cocotb,
  and Yosys in the implementation image;
- exported the trained six-class v4 checkpoint to `artifacts/ASIC` with
  149,835 registered parameters, 149,423 executed parameters, 143,824 weight words,
  25 PLIF actors, one inhibition actor, and fifteen adaptation actors;
- generated the active weighted 25-actor SystemVerilog DAG top;
- removed an unpacked combinational effective-age temporary that crashed Icarus and replaced
  it with equivalent per-channel scalar recomputation;
- the CPU implementation image passes 87 Python/structural tests, 23 cocotb RTL groups,
  Ruff, and the representative Yosys synthesis gate;
- the prior 11-class result remains documented as historical evidence but is not retained in
  the active artifacts tree;
- full-chip physical completion still requires a characterized SRAM compiler/library,
  a selected manufacturable PDK, real golden event streams, and routed activity data.

## 2026-08-31 — Epoch-35 provenance, memory contract, and full-DAG replay

- verified that the then-active checkpoint was epoch 35/seed 17 and exactly matched the epoch-35
  tensor state, then regenerated all weights, neuron parameters, and the structural top;
- quarantined the two remaining epoch-19 replay directories so they cannot be reported as
  evidence for the current checkpoint;
- derived 487 logical actor-local banks at a maximum 65,536 rows: persistent state is
  189.60 MiB, exact direct-index current plus touched flags add 92.32 MiB, and a worst-case
  full-depth touched queue is reported separately rather than hidden;
- added a synthesizable initialized single-port bank that zeroizes all banks in parallel at
  sequence start, blocks events until completion, and takes at most 65,536 cycles (327.68 us
  at the current 200 MHz research target);
- changed generated weight constants to bounded SystemVerilog concatenation chunks while
  preserving exact ROM word order, eliminating Icarus scanner overflow on trained weights;
- regenerated an epoch-35 160-event integer-oracle profile and a four-event RTL smoke replay;
  the full 25-actor smoke top matched all 64 final semantic pixels and bin-10 completion in
  Icarus 12 (191.66 s host simulation time);
- 87 Python tests, all 23 component cocotb groups, Ruff, representative Yosys synthesis, and
  the dedicated full-DAG replay pass in the CPU-only implementation image;
- per-actor RTL trace comparison, native DSEC occupancy/activity measurement, characterized
  SRAM binding, and routed PPA remain open and must not be inferred from the smoke replay.

## 2026-08-31 — ASIC actor-local SRAM integration

- replaced destination-scale behavioral current/membrane/tag arrays in ordinary and
  mechanism-enabled actors with packed single-port read-modify-write SRAM state;
- moved touched-address queues, retinotopic touched markers, signed temporal class-current
  scores, and exact residual-union event storage behind the same technology boundary;
- partitioned large logical memories into at most 65,536-row banks and verified parallel
  scrub plus tail-bank decoding; actors reject events until every owned bank is initialized;
- retained exact 5 ms completion-token semantics: raw events cause sparse signed-weight
  accumulation, while each touched PLIF thresholds/resets exactly once after completion;
- derived a 338.07 MiB direct-index SRAM correctness upper bound excluding the 0.137 MiB
  weight ROM; this includes worst-case full-depth queues and is not an area/power result;
- passed Icarus self-checks for ordinary PLIF persistence, grouped peer inhibition, temporal
  readout, residual deduplication, and multibank SRAM, plus all-top compilation and
  representative Yosys synthesis;
- propagated one generated-top SRAM macro selector through all 35 memory-owning blocks and
  added replay-side cycle/bin, utilization, and headroom capture;
- gated generated-top ingress on all 25 actor initialization signals plus readout
  initialization, so no event can be buffered while owned SRAM is being scrubbed;
- reran the complete SRAM-integrated 25-actor smoke DAG: all 64 semantic pixels and the
  bin-10 completion tag matched, no fault asserted, and 1,024 initialization cycles were
  excluded from 12,135 steady-state cycles (1,213.5 cycles/bin, 0.2427% of a 5 ms bin at
  100 MHz, 412.03x timing headroom) in the reduced 8x8 case;
- all 23 component cocotb groups, generated-top contract tests, and both behavioral and
  macro-selected complete-top compilations pass after the initialization-gate change.
- added per-actor touched-queue and per-residual-join high-watermarks to the existing replay
  profile instead of creating another artifact family; the deterministic reduced four-event
  smoke fixture observes maxima of 287 touched entries and one residual entry, while the
  160-event stress fixture observes 1,018 and 158 respectively;
- removed the smoke runner's 2,048-entry residual-capacity override so full-DAG verification
  exercises the generated top's actual 64-entry default; fixture observations remain explicitly
  non-native and are not a safe production capacity bound;
- reran the complete smoke DAG with that 64-entry default: all 64 pixels and bin-10 completion
  still match with no fault or overflow, while the architectural metrics remain 12,135 cycles
  per ten-bin frame after excluding 1,024 initialization cycles;
- built and ran `compose_ASIC.yaml`: 87 Python tests, Ruff, 23 cocotb groups, representative
  Yosys synthesis, and the complete exported-DAG replay pass in the CPU-only image; the image
  identifies itself as Torch 2.2.2+cpu with no CUDA build or available CUDA runtime;
- reconciled the stale final-loss regression/YAML with the newer committed v12 implementation:
  pixel CE 1.0, macro CE 0.0, Dice 0.30, region consistency 0.0, auxiliary CE 0.10, and
  boundary 0.02.

## 2026-08-31 — OpenROAD routed actor prototype

- completed the official ORFS ASAP7 flow through parasitic extraction and final GDS for a
  reduced 4x4 integrated convolution/PLIF actor at a 5 ns (200 MHz) clock constraint;
- post-route timing has zero setup and hold violations, 3.888 ns setup slack, 36.61 ps hold
  slack, and a reported minimum period of 1.112 ns (899.23 MHz nominal actor-only fmax);
- the 63.297 x 63.297 um die has 4,006.51 um2 die area, 3,502.74 um2 core area, and
  1,254.57 um2 non-filler standard-cell area at 35.82% utilization;
- detailed routing completed with zero DRC violations and the flow reported zero fatal errors;
- replaced a rejected global 280 ps slew guardband with a targeted 64-sink fanout constraint;
  the routed maximum net degree fell from 136 to 65 and extracted maximum-slew, fanout, and
  capacitance violations are all zero, with +47.64 ps worst slew margin;
- public ASAP7 supplies no characterized SRAM macros, therefore this experiment expands the
  tiny 4x4 memories into 1,553 sequential cells and cannot be scaled into a full-model area or
  power claim;
- OpenROAD's vectorless estimate is 1.335 mW and is retained only as a tool sanity result, not
  article evidence for event-driven model power; representative checkpoint/event activity and
  characterized SRAMs remain required;
- the amd64 ORFS image ran under Apple-silicon emulation with documented post-CTS timing repair
  skipped after that phase reproducibly raised SIGILL; native-x86 rerun must restore it before
  publication;
- `run_orfs.sh` now uses the installed official Docker image when `ORFS_ROOT` is unset and keeps
  every generated physical-design file under the Git-ignored `artifacts/OpenROAD` tree.
- `run_orfs.sh` now validates the extracted JSON and detailed-route report after Docker exits;
  any nonzero setup, hold, slew, fanout, capacitance, DRC, or flow-error count fails the command
  even when OpenROAD itself returns success.

## 2026-09-01 — Per-actor RTL current, membrane, and spike equivalence

- extended the existing epoch-35 full-DAG replay without adding RTL debug ports or a new
  artifact family: cocotb observes each generated actor's accepted output stream internally;
- compared bin tag, channel, y, and x for every emitted spike against the existing integer
  oracle for all 25 permanent PLIF actors, including exact silence checks;
- the reduced four-event 8x8 fixture matched all five emitted actor-spike rows exactly, while
  retaining the final 64-pixel semantic-frame and bin-10 completion-tag checks;
- trace monitoring does not alter the established latency result: initialization remains
  1,024 excluded cycles and steady-state completion remains 12,135 cycles;
- the first direct membrane comparison exposed a genuine one-LSB lazy-leak oracle defect:
  Python formed a rounded beta-power coefficient and multiplied membrane once, whereas RTL
  correctly rounds the membrane after each elapsed 5 ms beta update;
- corrected `IntegerPLIF` and the mechanism-enabled DAG reference to repeat membrane decay in
  RTL order, added a signed three-bin rounding regression, and regenerated the same fixture;
- the final replay exactly matches 1,532 accumulated-current rows, 1,538 candidate/membrane/
  spike transition rows, and five actor-output spike rows across all 25 actors;
- extended the existing membrane artifact and non-synthesizable monitors to compare adaptation
  age and amplitude without adding RTL ports or another artifact family; all 126 commits from
  adaptation-enabled actors match exactly;
- the final extended replay passes in 209.55 seconds of Icarus host runtime; the focused 37-test
  ASIC/training regression and Ruff pass after the trace extension, while the prior complete
  88-test regression remains the latest full-suite result;
- the five-spike smoke fixture is not a native-resolution activity or capacity bound.

## 2026-09-01 — Native DSEC activity-profile path

- added a narrow native integer-DAG profiler using the existing `artifacts/RTL/profile`
  output family; no new RTL implementation hierarchy or report claim was introduced;
- bound record selection to the active checkpoint's exact held-out sequence membership:
  all 234 records of `zurich_city_02_a`, with PLIF state retained across its 2,340 bins;
- preserve integer event multiplicity when converting the dataset's ten 5 ms count planes
  back to ingress events, and report per-actor live-state, touched-queue, output-spike, and
  residual-union high-watermarks;
- partial runs are explicitly marked `capacity_claim: false`; untimed integer execution also
  marks cycle latency and power activity unavailable;
- the complete Python regression now passes 89 tests and Ruff;
- native execution awaits a mounted DSEC tree; the active checkpoint is present locally, but
  no raw DSEC dataset is installed on this Mac and the repository sample directory is empty.

## 2026-09-01 — SKY130 SRAM-backed actor-tile layout

- bound the technology-independent actor memory boundary to two characterized
  `sky130_sram_1rw1r_80x64_8` OpenRAM macros: one stores the 66-bit packed PLIF state and one
  stores the touched-address queue for the reduced 4x4 actor;
- added a dedicated SKY130HD ORFS configuration, fixed macro adapter, and explicit power grid
  connecting the macros' lowercase met3 `vdd`/`gnd` pins to the met4/met5 core grid;
- completed synthesis, macro placement, CTS, detailed routing, extraction, connected-power
  analysis, and merged GDS using the official ORFS image;
- the final flow contains exactly two SRAM macros, has zero setup/hold/driver violations,
  zero detailed-route DRC, zero antenna violations, and no orphan LEF/GDS cells;
- at a 20 ns constraint, extracted setup and hold slack are 5.009 ns and 0.449 ns, with a
  reported 97.31 MHz nominal actor-tile fmax;
- die/core area is 1,679,210/1,574,100 um2, comprising 363,942 um2 of SRAM macros and
  52,935.8 um2 of non-filler standard cells; this deliberately wasteful pair of 80x64 SRAMs
  validates integration, not the eventual native actor banking policy;
- vectorless power is 8.295 mW and worst VDD/VSS IR drop is 0.114/0.102 mV; both are tool
  sanity values without checkpoint-derived DSEC switching activity and are not article
  event-driven power evidence;
- normalized the shared report checker across ASAP7 picosecond and SKY130 nanosecond report
  units and made the SKY130 flow fail unless exactly two macros survive;
- verified 66-bit write/readback and read-valid timing against the exact bundled OpenRAM
  functional model; its declaration-order issue required only a temporary Icarus-compatible
  copy, while the checked-in adapter remains unchanged;
- added the external-SRAM actor branch to the normal Icarus and representative Yosys gates;
- post-CTS timing repair remains skipped only for the documented Apple-silicon amd64-emulation
  `SIGILL`; native-x86 rerun with repair enabled is still required before publication.

## 2026-09-01 — Native real-event full-DAG short-interval execution

- rebuilt the CPU-only ASIC image with the declared HDF5 compression plugin and read the supplied
  `zurich_city_13_a/events.h5` directly; no CUDA training image is involved;
- executed the first complete 5 ms interval through all 25 checkpoint-exported actors at native
  440x640 geometry, retaining event multiplicity and actor-local state while disabling only the
  enormous diagnostic row trace;
- the raw file contains 42,764 indexed events in the first 5 ms; the unrectified native crop keeps
  41,839, so this is a sample-only activity run until the matching DSEC rectification map is added;
- regenerated all ASIC weights, parameters, memory manifest, and the 25-actor top after a
  provenance guard detected that the current checkpoint is epoch 40/seed 17 strategy v12 rather
  than the previous epoch-35 export; profiling now refuses any such mismatch;
- the corrected bit-exact run completed in 349.53 host seconds, performed 138,562,457 synaptic
  additions, emitted 646,175 actor spikes, and ended with 5,869,959 live actor-state entries;
- `final_fuse.standard` is the present single-lane RTL bottleneck: 88,597,529 additions,
  1,401,431 touched destinations, and 275,576 spikes imply a conservative 277,279,611-cycle
  actor-service floor;
- using the routed SKY130 actor tile's non-full-chip nominal 97.31 MHz only as a clock reference,
  that floor is 2.849 s per 5 ms bin (at least 569.9x over deadline) and requires at least 570
  ideal conflict-free lanes/banks before routing and SRAM conflicts;
- this is full-model native functional activity plus an RTL-FSM lower bound, not a cycle-accurate
  full-native RTL run or a routed full-chip power/latency result. Activity-based power remains open.

## 2026-09-01 — Banked actor implementation resume point

- keep the 25 permanent actor DAG and exact bin-completion semantics; the performance defect is
  intra-actor serialization, not runtime layer reconfiguration;
- retain `asynchronous_plif_actor.sv` as the one-lane oracle and implement an ordinary-actor bank
  wrapper first, with `global_destination % lane_count` routing and disjoint local SRAM/queue state;
- required wrapper behavior: selected-lane input backpressure, global/local address conversion,
  fair spike merge, one same-tag completion only after every lane completes, error aggregation, and
  all-lane initialization gating;
- after ordinary-lane equivalence, replace the single-output convolution scatter bottleneck with
  parallel contribution streams, then bank retinotopic mechanism actors by spatial address so all
  channels at one location remain atomic;
- verification gates are one-lane equivalence, collision/no-loss tests, independent-bank overlap,
  completion rendezvous, randomized integer-oracle comparison, synthesis, and native workload lane
  sizing. Do not claim the ideal 570-lane floor as an implemented result.

### Completed ordinary-actor banking stage

- regenerated the reduced smoke and 160-event profiles from the epoch-40/seed-17 strategy-v12
  export; the reduced full-DAG RTL replay passes exact output plus 1,540 current, 1,542 membrane,
  five spike, and adaptation trace comparisons in 12,178 steady-state cycles;
- added `banked_asynchronous_plif_actor.sv`, which interleaves global destinations across disjoint
  local state/queue SRAMs and never duplicates a membrane/current entry;
- added global-stride/offset parameter lookup to the retained single-lane actor so an interleaved
  local row still selects the correct global output-channel beta and threshold;
- implemented selected-bank input backpressure, local/global address conversion, deterministic
  spike merge, all-lane completion/tag rendezvous, initialization gating, and fault aggregation;
- integrated ordinary banking beneath `channelized_convolution_plif_actor` and
  `streaming_channelized_plif_actor` with `STATE_LANE_COUNT=1` as the equivalence-preserving default;
- four lanes accept eight round-robin-bank contributions on eight consecutive clocks; same-bank
  accesses correctly backpressure, and global-channel parameter/spike-address tests pass;
- all 25 component cocotb groups pass after integration. The next resume point is parallel
  convolution scatter: the current scalar contribution output still caps the actor at one addition
  per clock even when state banks are available.

### Completed parallel scatter and mechanism-aware actor banking

- added a vector convolution scatter that emits at most one ordered contribution per
  channel-by-spatial bank each clock and retains the remaining projection bitmap under
  backpressure; per-bank projection order matches the scalar reference so signed saturation
  behavior is unchanged;
- added the end-to-end ordinary parallel actor with disjoint state/queue memories and verified
  simultaneous contributions to different channel/spatial banks, state retention across bins,
  global coordinate reconstruction, and completion rendezvous;
- added spatially interleaved retinotopic banks. Every lane owns all channels for its pixels, so
  inhibition and threshold adaptation remain atomic across peer channels while different pixels
  execute independently;
- integrated both ordinary and mechanism-enabled parallel actors beneath the unified stream
  interface. Reference, four-bank ordinary, and two-bank inhibited stream configurations pass;
- corrected the stream testbench to hold a completion packet until the completion-specific ready
  signal accepts it; the former zero-latency assumption could drop a token while parallel scatter
  work was draining;
- the next resume point is full-DAG generation: export per-actor lane factors, instantiate the
  parallel stream paths in the generated 25-actor top, then derive conflict-aware lane sizing from
  the native epoch-40 activity rather than presenting the 570 ideal floor as implemented latency.

### Completed native conflict-aware lane sizing

- extended the full-DAG generator with an external per-actor lane manifest and emitted explicit
  parallel-state, channel-lane, and spatial-lane parameters for all 25 actors; generated RTL embeds
  the exact manifest SHA-256;
- added low-memory bank counters to the integer DAG reference. They count all additions, touched
  entries, and spikes by the same modulo mapping used in RTL without retaining a 138-million-row
  contribution trace;
- require per-bank counts to conserve the aggregate actor totals before accepting a service result,
  and added a synthetic imbalance regression;
- iterated the one-bin native profile against actual modulo-bank imbalance. The final manifest owns
  1,718 independent actor lanes; ordinary actors split channel and spatial dimensions, while the 15
  mechanism actors split only spatial locations;
- the final exact activity totals remain 138,562,457 additions, 646,175 actor spikes, and 5,869,959
  live sparse state entries. Manifest, profile, and generated top share SHA-256
  `8ff8673edbe91a72142aaa95f6b91d530808013110f662700fcb3a92ff6c0519`;
- the busiest configured bank is `enc2_extra.depthwise` at a 388,589-cycle service floor, 3.993 ms
  at the isolated tile's 97.31 MHz reference, and `U=0.79866`; both the hard `U<=1` and engineering
  `U<=0.8` service-floor gates pass for this sample;
- do not report this as end-to-end latency or power. Next resume point: add generated-top FIFO depth
  sizing and a tractable cycle-accurate critical-path/full-DAG validation, then bind the 1,718 bank
  interfaces to scale-suitable characterized SRAM macros before full-chip PPA.

### Completed lossless elastic DAG-edge buffering

- added `event_stream_fifo.sv`, a synthesizable ordered ready/valid queue for the unified payload,
  completion flag, and bin tag; full queues backpressure and never discard or reorder packets;
- inserted a configurable FIFO on every non-prediction edge generated for the exact 25-actor DAG,
  breaking direct combinational ready chains while guaranteeing completion stays behind its bin's
  spikes;
- verified full/backpressure behavior and ordered spike/token drain in cocotb, and compiled plus
  token-simulated the complete reduced generated DAG with all edge FIFOs present;
- added per-edge occupancy/high-watermark registers and reran the epoch-40 reduced 8x8 replay. It
  remains bit-exact for all current, membrane, spike, and adaptation traces and completes in 12,186
  cycles; the FIFO insertion adds eight cycles relative to the 12,178-cycle unbuffered replay;
- 17 of 53 edges reach the depth-two default on that fixture, so none of those edges may be reduced
  to depth one from current evidence. Full queues can pop and accept a replacement in one clock;
- the default depth is still a reduced-fixture timing choice, not a native occupancy claim. Next
  resume point: obtain native cycle traffic or a calibrated event-level schedule before selecting
  deeper per-edge buffers or reporting end-to-end latency.

### Completed completion-token latency-floor sizing

- split each configured bank's service estimate into collection and post-token PLIF-commit terms;
  because a downstream actor cannot commit before all required same-bin tokens arrive, a
  topological longest-path sum of commit terms is a strict response-latency floor;
- the 1,718-lane throughput configuration fails that test at 1,050,545 cycles, 10.796 ms at the
  isolated 97.31 MHz tile reference, or 2.159 times the 5 ms deadline. This corrects the possible
  misreading of its 3.993 ms busiest-bank service interval as end-to-end latency;
- added `plan_asic_latency_lanes.py`, which adds spatial banks using observed commit imbalance and
  an explicit safety factor. Its output is labelled a candidate and cannot become a measurement
  until the exact native event profile is rerun;
- exact reprofiling accepted a 1,966-lane mapping. It leaves the `final_fuse.standard` service
  bottleneck at 384,334 cycles (3.950 ms, `U=0.78992`) and reduces the commit-only critical path to
  349,094 cycles (3.587 ms, `U=0.71749`), passing both 5 ms and 80% floor gates on this sample;
- the accepted manifest/profile/generated-top SHA-256 is
  `172121ae49208c034d95314ab65b1cf6cb1975f7a7166d78f558f830f6ff003d`; the prior 1,718-lane
  manifest is retained locally as the throughput-only baseline;
- post-change verification passes: lint, 94 Python tests, 32 cocotb RTL groups, representative
  Yosys synthesis, and the previously completed bit-exact FIFO-buffered replay;
- this remains a lower bound, not measured end-to-end latency. Next resume point: account for
  native edge traffic, FIFO/backpressure, route/join/readout cycles, then characterize the
  1,966-bank SRAM organization and run full-chip physical PPA.

### Completed native edge-volume gate

- derived every edge's exact one-bin data volume from actor outputs and route semantics, validating
  each actor input count against its incoming graph stream; the generated graph has 53 FIFO edges;
- the busiest edge is `final.concat -> final_fuse.standard` with 657,634 data events plus one
  completion token. A scalar link therefore has a 657,635-cycle serialization floor: 6.758 ms and
  `U=1.35163` at 97.31 MHz, failing both hard and 80% gates;
- the minimum volume-only width is two packets per clock at 97.31 MHz. Occupancy is still unknown
  because volume alone has no arrival/departure timing and is not used to resize the FIFOs;
- removed the avoidable empty cycle between parallel-scatter inputs: when every pending projection
  handshakes, the next presynaptic spike can replace it on the same rising edge; focused RTL
  back-to-back acceptance passes;
- next resume point: either implement and verify a two-packet hot-path interface or demonstrate a
  routed full-chip clock of at least 164.41 MHz for the scalar volume/80% gate, then run a timed
  native backpressure model. The current 97.31 MHz result cannot support a real-time claim.

### Completed 200 MHz lane-cost refinement

- evaluated the existing architectural 200 MHz target, whose 800,000-cycle 80% budget allows the
  scalar hot edge to pass without adding a second packet network;
- rejected the first 917-lane candidate after exact reprofiling: `stem` reached 1,176,798 cycles
  and the commit chain reached 897,040 cycles, demonstrating that ideal/projection sizing was
  insufficient;
- fed those measured conflicts into a second exact iteration. The 924-lane result passes the three
  independent floors: busiest bank 781,772 cycles (`U=0.78177`), completion-token commit path
  737,691 cycles (`U=0.73769`), and scalar edge 657,635 cycles (`U=0.65764`);
- promoted the 924-lane mapping to the generated full top and preserved the 1,966-lane 97.31 MHz
  mapping locally. Manifest, exact profile, and top share SHA-256
  `81f8381ec225b82d5f03965e5a9415bb7e07b1126a4072497906f4037860f257`;
- this promotion is a target configuration, not a full-chip latency claim. Next resume point:
  timed scatter/bank/FIFO backpressure analysis and full-chip 200 MHz physical closure with
  scale-suitable SRAM macros; failure of either requires wider links or more lanes.

### Event-order collection timing rejected the spatial-only mechanism datapath

- instrumented exact event order, same-cycle scatter replacement, ordinary three-cycle bank
  cadence, mechanism five-cycle cadence plus first-spatial-touch write, and completion admission
  only after every bank returns to collect;
- the promoted 924-lane mapping fails before inter-actor FIFOs are considered. `down2.standard`
  requires 40,097,168 collection cycles and 40,107,810 cycles including its busiest commit bank
  (200.539 ms at 200 MHz); `stem` needs 6,593,614 total isolated cycles;
- `final_fuse.standard` also rises from its bank-count floor to 1,875,150 isolated cycles because a
  single pending-event bitmap stalls all otherwise independent banks when any destination bank is
  busy;
- the mechanism failure is structural: spatial-only contribution ports serialize all output
  channels that target the same pixel. More spatial modulo banks cannot fix this same-pixel
  serialization;
- next resume point: separate mechanism accumulation banking from mechanism commit atomicity.
  Channel-by-spatial current/state ports must collect independently, then one spatial coordinator
  must read peer channels, apply inhibition/adaptation atomically, and write them together. Ordinary
  actors also need multiple pending scatter contexts or per-bank projection queues.

### Ordinary actor scatter decoupling in progress

- added an ordered depth-four contribution FIFO between each ordinary scatter output and its
  destination state bank; each queue stores destination channel/coordinate and signed weight;
- full queues backpressure only their corresponding scatter bank, simultaneous pop/push has no
  bubble, and completion cannot enter until the scatter plus every contribution FIFO is empty;
- integrated tests accept four consecutive presynaptic events while the three-cycle accumulator
  banks are busy, then prove the expected spikes and clean completion with no routing fault;
- this is a functional decoupling step, not a new native timing result. FIFO depth and ordinary
  actor timing must be reprofiled after the mechanism channel-by-spatial collection path exists.

### Register-resident PLIF replacement started

- added `resident_plif_population.sv`: every logical ordinary neuron owns local current and
  membrane state elements, parallel contribution lanes accumulate directly into those elements,
  and one completion edge updates the whole population in parallel;
- the resident primitive has no state-memory request/response interface, touched queue, scrub pass,
  or last-bin tag. Applying one beta update to every neuron on every 5 ms completion is numerically
  equivalent to lazy elapsed-bin leakage while state remains continuously resident;
- a four-neuron/two-channel test accepts two different destination contributions in one clock and
  produces the exact two-neuron spike bitmap on the following completion transaction;
- Icarus and Yosys pass; Yosys explicitly reports the current and membrane arrays replaced by
  registers, confirming that this primitive does not infer SRAM. Full regression now contains 33
  RTL groups;
- next resume point: create the resident retinotopic population with per-channel current/membrane/
  adaptation state, parallel peer-channel inhibition/adaptation at completion, then replace the
  generated actor stream with direct spike bitmaps and remove superseded SRAM actor paths.

### Direct resident actor datapath implemented

- added `resident_retinotopic_plif_population.sv`; every mechanism-enabled PLIF now owns
  resident current, membrane, adaptation-age, and adaptation-amplitude state, while each
  spatial peer group performs its inhibition/adaptation commit atomically and in parallel;
- added `resident_convolution_synapses.sv`; a binary presynaptic spike bitmap gates the
  compile-time int8 convolution weights and forms the complete postsynaptic current-delta
  vector without weight-ROM or state-memory transactions;
- added `resident_channelized_plif_actor.sv` to bind the static synapse fabric to either the
  ordinary or mechanism-enabled resident population. Repeated bitmap transactions preserve
  event multiplicity, and the completion token commits the resident population;
- focused cocotb verification covers direct grouped convolution, simultaneous peer-channel
  accumulation, inhibition/adaptation, and an end-to-end resident actor transaction;
- next resume point: change the generated 25-actor graph and its join/fanout representation
  from scalar event streams to resident spike-vector transactions, then establish full-model
  elaboration feasibility before removing the superseded SRAM actors.

### Resident graph routing and readout primitives implemented

- added `streaming_resident_channelized_plif_actor.sv`, which accepts one or more spike-vector
  pulses followed by a completion token and emits one result vector followed by the matching
  completion token;
- added `resident_event_ingress_adapter.sv`; every raw `(channel,y,x)` event becomes a one-hot
  pulse transaction, so timestamp order and repeated-event multiplicity are preserved without
  constructing or preloading a 5 ms input bin;
- added bitmap-native channel-offset, nearest-neighbor 2x upsample, and binary residual-OR
  blocks. The residual block rendezvous-checks bin tags and emits coincident spikes once;
- added a storage-free two-way vector fork that retains only branch-acceptance bits while the
  source holds its vector stable, avoiding a duplicate feature-map register bank at fanout;
- added `resident_temporal_class_readout.sv`; signed class currents are local resident elements
  over the prediction window and first-index-tie argmax enumerates the semantic map;
- updated `docs/AGENTS.md`, which still mandated the superseded SRAM/tag design, to match the
  higher-priority resident-state project specification;
- next resume point: make resident bitmap generation the default path in
  `scripts/generate_asic_top.py`, infer every intermediate vector shape from the exported graph,
  compile the complete 25-actor reduced fixture, then attempt native checkpoint elaboration.

### Resident 25-actor generator completed; native elaboration exceeded 8 GB

- `scripts/generate_asic_top.py` now defaults to the resident architecture and infers every
  actor/route channel-height-width vector shape from the exported non-linear graph. The old path
  remains available only as `--architecture legacy_sram` for replay/equivalence history;
- the geometry-preserving reduced fixture generates and compiles all 25 resident actors, nine
  bitmap residual unions, three bitmap upsamplers, both concats, the multiplicity join, and the
  resident temporal readout. Icarus event simulation of even that fully parallel graph is too
  slow for the normal gate, so behavior remains covered by bounded primitive/actor cocotb tests;
- generated the checkpoint-authoritative native top at
  `artifacts/ASIC/eventspikeseg140k_resident_dag_top.sv` (ignored, 387,139 bytes), containing all
  25 actors and 143,824 exported int8 synaptic weights;
- native Icarus elaboration under the configured 8 GB Docker limit was killed with exit 137 after
  roughly 79 seconds. No native simulation began, so this produces no latency or power result;
- next resume point: introduce a spatially tiled hierarchical resident implementation and
  characterize one exact tile per actor configuration. State remains register/latch-local to each
  PLIF; tiling may reduce tool object expansion but cannot erase the 1.59-billion resident state
  bits or guarantee that full-chip synthesis will fit in 8 GB.

### Register-resident spatial tile boundary established

- added output-tile coordinates and dimensions to the resident convolution, direct actor, and
  streaming actor. A tile evaluates the original global convolution coordinates but instantiates
  state only for the PLIFs physically owned by that tile;
- actor-level cocotb proves that a tile covering global x=2..3 responds to those source
  coordinates and returns its two local PLIF results;
- changed the vector-to-completion edge to retain only one phase bit. The producer holds its result
  bitmap and tag stable through the data and completion handshakes, avoiding a second wide register;
- added `scripts/plan_asic_resident_tiles.py`. The checkpoint export's nominal 8x8 plan contains
  20,410 tiles and conserves all 30,976,000 PLIFs. Resident state is 1,590,476,800 bits
  (198,809,600 byte-equivalent): 24-bit current plus 16-bit membrane for every PLIF, plus 16-bit
  adaptation age and 16-bit adaptation amplitude where enabled;
- the 25 PLIF actors own 143,728 int8 convolution weights; the remaining 96 of the model's 143,824
  weights belong to the temporal readout. The derived ignored manifest is
  `artifacts/ASIC/resident_tile_plan_8x8.json`;
- next resume point: add a lockstep tile-array wrapper and compile a reduced multi-tile actor, then
  synthesize representative exact 8x8 actor tiles. Scaled tile PPA remains an estimate, not a
  substitute for full-chip placement and routing.

### Resident tile hierarchy integrated; emulated PPA front-end bounded

- added `tiled_resident_channelized_plif_actor.sv`. Every child tile accepts input and completion
  atomically with its peers, retains its own state, and contributes its local bitmap back to the
  actor's global channel-major output. A two-tile test proves one event/completion/result transaction;
- the streaming resident actor now defaults to explicit 8x8 spatial children, and the native
  checkpoint top was regenerated with the tile dimensions embedded for all 25 actors;
- added a PPA-top generator that uses the real checkpoint weights, beta, and threshold. This avoids
  the invalid zero-weight optimization that would otherwise erase the synapse fabric;
- bounded ASAP7 attempts under amd64 emulation did not reach routing: the 8x8 `detail_stem` tile was
  stopped after more than ten minutes in Yosys canonicalization; the 4x4 tile canonicalized in 58 s
  at 329 MiB peak but was stopped after more than twenty minutes in technology-map optimization.
  Both exited 137 because their disposable containers were deliberately stopped, not because the
  8 GB limit was exhausted. Neither attempt provides latency, area, or power;
- next resume point: route a checkpoint-exact 2x2 characterization unit, then use its result only as
  a standard-cell scaling datum while improving the structural synapse/leak elaboration.

### Checkpoint-exact 2x2 resident unit routed with a slew-cleanup failure

- disabled optional ASAP7 full-adder extraction for this characterization flow; under x86
  emulation it dominated runtime without changing the RTL state or arithmetic contract;
- Yosys mapped the 32-PLIF `detail_stem` unit with its 144 trained int8 weights. Synthesis took
  271 s and peaked at 1,456 MiB; detailed routing completed and peaked at 7,568 MiB;
- the routed unit contains 1,337 sequential cells and 56,841 multi-input combinational cells.
  Final standard-cell instance area is 7,247.19 um^2 in a 21,139.7 um^2 core (34% utilization);
- setup/hold, max capacitance, max fanout, global congestion, detailed-route DRC, power connectivity,
  and GDS orphan-cell checks pass. Reported internal fmax is 772.241 MHz;
- final validation still fails on 68 internal max-slew endpoints: 321.65--360.29 ps against the
  320 ps limit. The completed run also used the previously copied SDC with stale input names, so
  timing is not accepted for publication;
- vectorless power is 30.9699 mW at 0.77 V and 200 MHz, with 0.003579 V (0.46%) worst VDD drop.
  This is preliminary default-toggle tile power, not DSEC activity-based power and not full-chip
  power. The next run uses the resident-port SDC and corrected integer-percentage slew repair.

### Checkpoint-exact 2x2 resident unit reaches clean routed sign-off checks

- the resident-specific SDC rerun reduced but did not eliminate extracted max-slew failures:
  1.2% repair margin left 27 violations and 20% left 8. OpenROAD's `SLEW_MARGIN` is an integer
  percentage, not a multiplier;
- the accepted run uses a conservative 50% pre-route slew margin. Placement repair resized 140
  cells and inserted 175 buffers; global-route repair resized 2 more cells and inserted 117 more
  buffers. Final standard-cell area is 7,311.29 um^2 in the unchanged 21,139.7 um^2 core
  (34.59% utilization);
- extracted setup and hold violation counts are zero, max-slew/max-capacitance/max-fanout counts
  are all zero, and worst slew has 90.03 ps positive margin against the 320 ps ASAP7 limit.
  Detailed-route DRC is empty, global congestion is zero, both power nets are connected, and GDS
  merging reports neither missing nor orphan cells;
- reported internal fmax is 639.636 MHz. Default vectorless power is 30.9607 mW at 0.77 V and
  200 MHz; worst VDD drop is 4.453 mV (0.58%). These are clean physical-characterization results
  for one checkpoint-exact 2x2/32-PLIF `detail_stem` unit, not full-model latency or power and not
  DSEC activity-based energy;
- next resume point: replace full-layer bitmap broadcast at the production tile wrapper with each
  tile's exact convolution receptive halo, verify global-to-local coordinate equivalence, and then
  characterize the reduced inter-tile fanout. Full-chip PPA remains blocked by native scale.

### Production resident tiles use exact receptive halos

- replaced full-input bitmap replication at `tiled_resident_channelized_plif_actor` with a
  compile-time clamped receptive rectangle for every output tile. The synapse fabric subtracts the
  halo origin after applying the checkpoint's global stride, padding, and dilation geometry;
- the local bitmap contains input spike bits only. Every tile still owns exactly its original
  output PLIF current, membrane, and optional adaptation registers, so the change adds neither
  runtime state addressing nor duplicated PLIF state;
- a cross-tile 3x3 cocotb case proves that the second output tile receives an input pixel from the
  neighboring receptive border and produces the same three global outputs as untiled convolution.
  The focused tests, all 47 cocotb groups, 96 Python tests, Verilator lint, and compilation of all
  40 SystemVerilog tops pass;
- the checkpoint-derived 8x8 plan now counts 51,871,626 tile-input bit endpoints versus
  73,444,096,000 endpoints for replicating every complete actor input bitmap to every tile: a
  99.929% logical endpoint reduction. This is a static wiring/fanout inventory, not routed wire
  length, capacitance, power, or full-chip PPA;
- next resume point: synthesize a representative boundary-aware multi-tile wrapper and compare its
  net fanout/area against the isolated interior unit. Full native graph simulation and PPA remain
  blocked by the 8 GB elaboration boundary and physical model scale.

### Checkpoint-exact two-tile synthesis gate added

- extended the resident physical-design top generator with explicit tile rows/columns. Its default
  remains the accepted isolated interior unit; multi-tile mode keeps the actor's real padding and
  stride and instantiates the production receptive-halo wrapper;
- generated and synthesized a two-column `detail_stem` top containing all 144 trained int8 weights,
  64 resident PLIFs, and two 2x2 child tiles. Yosys `proc`, memory lowering, optimization, and
  structural `check` complete successfully;
- the first synthesis exposed an unintended latch on the procedural tag-check loop index. The index
  is now assigned on every combinational path; the same synthesis and tiled cocotb regression pass.
  A small tiled-wrapper case is included in `check_synthesis.sh` so this class of issue is gated;
- next resume point: produce a separate OpenROAD configuration for the two-tile boundary top and
  obtain routed fanout/area/timing data. Keep it distinct from the accepted single-unit result and
  do not extrapolate either result to full-chip power or latency.

### Two-tile boundary PPA reaches detailed-route memory boundary

- the separate checkpoint-exact `detail_stem` two-column (two 2x2 child tiles, 64 resident PLIFs,
  all 144 actor weights) ASAP7 flow completed synthesis, floorplan, placement, CTS, and global
  routing after the multi-tile ready/valid loop was removed;
- completed intermediate values: 13,492.10 um^2 synthesized standard-cell area; 38,466.18 um^2
  core at 35% target utilization; 13,226 um^2 after CTS; 118,367 CTS instances; 2,674 clock sinks;
  197 clock buffers; global-route area 13,271 um^2; +3,502.265 ps global-route setup slack at the
  5 ns constraint. These are not extracted final results;
- detailed routing began with 1,024,833 guides and reached 10% of its first optimization pass with
  zero violations, then the amd64-on-Apple container stopped at 7,764,480 KB peak memory, which is
  effectively the configured 8 GB Docker limit. No `6_report.json`, detailed-route DRC report,
  extracted timing, IR-drop, GDS, or power report was produced;
- next resume point: run this same configuration on a host with more than 8 GB Docker memory (or a
  native x86 host) before reporting any two-tile PPA. Do not shrink/replace the checkpoint-exact
  hierarchy merely to obtain a routed result.
