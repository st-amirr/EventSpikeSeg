# EventSpikeSeg

Fully spiking event-camera semantic segmentation for DDD17 and DSEC-Semantic,
designed so the learned inference path can be mapped to a custom digital neuromorphic
FPGA accelerator with fixed-point PLIF state, sparse spike routing, and event-driven synaptic updates.

## Repository layout

```text
src/eventspikeseg/model.py              EventSpikeSegXL implementation target plus compact EventSpikeSeg140k baseline
src/eventspikeseg/model_components.py   shared PLIF/SNN/convolution primitives
src/eventspikeseg/top_ten_models.py     frozen round-one model registry
src/eventspikeseg/top_five_models.py    frozen structural top-five registry
src/eventspikeseg/top_three_models.py   frozen accuracy top-three registry
src/eventspikeseg/train.py              single training/benchmark engine for all suites
src/eventspikeseg/data.py               DDD17 and raw DSEC temporal data loading
src/eventspikeseg/evaluate.py           checkpoint evaluation and visualizations
scripts/                                utility/diagnostic scripts only
docs/ARCHITECTURE.md                    current architecture and runtime contract
docs/DECISIONS.md                       chronological design decisions
docs/RESULTS.md                         measured experiment results
docs/PROGRESS.md                        current implementation/validation state
docs/BUGS.md                            open limitations and resolved failures
```

The historical model registries remain importable for reproducibility, but there is only one training engine. `train.py` handles `top-ten`, `top-five`, `top-three`, and `final`; the old standalone top-three benchmark runner is retired.

## DDD17 input

Expected host layout:

```text
DDD17/
├── ddd17_temporal_manifest.json
├── events/{train,test}/*.npy
└── labels/{train,test}/*.png
```

The manifest is the authoritative semantic chronology: each row supplies the event/label file, `sequence_id`, and chronological `frame_index`. No HDF5 or separate raw recording is required.

The sole active representation is `timestamp-events`. One loader item is one
already-integrated 50 ms six-channel NumPy record, producing `[N,6,H,W]`; adjacent
files are not stacked. The two histogram channels supply polarity activity. The
per-polarity timestamp mean and standard deviation schedule three weighted arrivals
over ten 5 ms input-clock updates by default before the first PLIF layer. PLIF state persists
into the next consecutive record and resets at sequence/frame gaps.

The archive stores timestamp moments rather than every raw event, so this is a
moment-based arrival approximation, not reconstruction of exact event tuples.

`--internal-updates 10` controls the within-record PLIF clock count. It must divide
the 50,000 µs interval exactly and is stored in the checkpoint protocol.

Classes: `flat`, `construction+sky`, `object`, `nature`, `human`, `vehicle`. Label `255` is ignored.

If `--height` and `--width` are omitted, stored resolution is preserved. `--train-samples` accepts `0` for the full pool, a fraction in `(0,1]`, or an absolute count. For DDD17, a limited run selects one deterministic contiguous stream segment per epoch. Records are not shuffled, and stateful training/evaluation requires batch size 1.

## DSEC-Semantic raw-event input

The DSEC path consumes each sequence's continuous `events.h5`, `rectify_map.h5`,
semantic timestamp text file, and `11classes` PNG masks. Both the installed flat
layout and the official nested DSEC-Semantic layout are recognized.

DSEC validation holds out complete sequences, with coverage scaled by
`--train-samples`. Fractions through `0.5` hold out one sequence; fractions above
`0.5` hold out two. The complete-sequence choice closest to
`total_records × validation_fraction × active_train_fraction` is fixed for the run,
with split seed 17 used only for tie-breaking. On the installed data,
`--train-samples 0.5 --validation-fraction 0.10` selects the 234-record
`zurich_city_02_a`; `--train-samples 0.7` selects `zurich_city_01_a` plus
`zurich_city_02_a` (914 records). Fractional training sampling is then applied
separately to every remaining sequence: `0.5` selects one chronological contiguous
half-window from each training sequence, rather than half of the pooled records from
only some folders. Window locations change deterministically by epoch; record order
is never shuffled.

Semantic timestamps are nominally 20 Hz. One item slices raw events from
`[label_time-50ms, label_time)`, rectifies them, crops the semantic view, and preserves
their chronological order. GPU training groups them into fixed time divisions of
`50ms / internal_updates`; with the default 10 updates, these are ten fixed 5 ms
divisions. Every source event contributes one unit—there is no binary collision collapse,
logarithm, event-count limit, or count cap. Hidden activations remain binary.

Time division accelerates training; it is not the FPGA input protocol. The deployed
model accepts camera events directly, lazily decays touched PLIF state from the exact
timestamp delta, adds shared-kernel contributions, and propagates only generated spikes.
DSEC necessarily replaces the six-population
DDD17 class head with eleven spiking output populations: `sky`, `building`, `fence`,
`person`, `pole`, `road`, `sidewalk`, `vegetation`, `vehicle`, `wall`, and
`traffic-sign`.

The trainer consumes every packet before forming one weighted CE + Dice + auxiliary
objective. `--sequential-chunks K` uses a memory-bounded two-pass replay: first form the
complete-record prediction without an activation graph, then replay chronological chunks
with that one objective's output gradients. This releases each chunk graph without ever
applying the complete target to a partial history. The replay state snapshot is kept in
host RAM so it does not duplicate the model's large persistent neuron state on the GPU.

PLIF leakage is physical-time based:
`retention(delta_us) = beta ** (delta_us / 5000)`. Logits and activity rates are
normalized by elapsed physical time rather than packet count. The local 1×1 PLIF
selector also removes the previous global frame-reduction barrier.

The DSEC stability profile uses a base learning rate of `5e-4` for both synaptic
weights and learnable PLIF beta/threshold parameters; neuron parameters receive no
additional multiplier. Per-class soft-Dice values are still reported for all
classes, but the scalar Dice objective averages only semantic classes present in the
current target mask. This prevents an absent rare class from being trained toward
zero on every record where it has no labelled pixels.

## FPGA logical-state footprint

Parameter count is **not** runtime neuron count. For the active 11-class
`EventSpikeSegXL` DSEC implementation at 241x351, the 50 executed inference populations
require

```text
H2xW2 = 121x176, H4xW4 = 61x88
N_mem = 683*H*W + 768*H2*W2 + 2144*H4*W4
      = 85,639,973 membrane values
```

fLong is enabled on **20,024,576** neurons and stores age plus amplitude. Direct
asynchronous execution also stores one last-update timestamp per membrane. An
illustrative 16-bit membrane/age/amplitude plus 32-bit timestamp layout is about
**566.42 MiB**, before queues and counters. Therefore XL uses external DDR as the exact
persistent-state backing store and banked on-chip memory as an active-tile cache.

- **static/shared:** convolution weights, per-channel beta, per-channel base threshold;
- **persistent per-neuron:** membrane, last-update timestamp, and enabled fLong state;
- **temporary:** touched-event synaptic current and sparse spike FIFOs.

The FPGA may use far fewer physical PLIF arithmetic units by time-multiplexing them, but
it must preserve one logical state record per `(layer,c,y,x)`. The exact sparse execution
flow for DSEC is `timestamped event -> destination-address generation -> lazy physical-time
decay -> weight addition -> threshold/reset -> state/timestamp writeback -> emitted events`.
There is no global neural timestep barrier. See `docs/ARCHITECTURE.md` and
`project_spec.yaml` for the full contract.

## Main commands

```powershell
docker compose run --rm inspect-ddd17
docker compose run --rm inspect-dsec
docker compose run --rm lint
docker compose run --rm test
docker compose run --rm train-ddd17-smoke
docker compose run --rm train-ddd17
docker compose run --rm train-dsec
docker compose run --rm train-dsec-xl
```

`inspect-ddd17` validates the DDD17 manifest. `inspect-dsec` verifies sequence event,
rectification, timestamp, and label alignment. `train-dsec-xl` is the active 241x351,
11-class XL run; `train-dsec` retains the compact reference run.

## Measured architecture-search evidence

The measured historical incumbent remains:

```text
v10_fpga_hybrid
mIoU            0.3130
pixel accuracy  0.7871
parameters      44,016
spike rate      0.1412
```

The completed structural top-five selected `f05_compact16_dilated` at mIoU `0.2596` with only `21,491` parameters. The completed accuracy top-three selected `t02_dualpath_detail` at mIoU `0.2728` with `24,211` parameters. These experiments established the main design evidence carried into EventSpikeSeg: preserve high-resolution detail, retain moderate channel capacity, prefer depthwise/pointwise processing and simple dilation, and avoid a fourth downsampling scale or hard hidden winner gating.

Full rankings and per-class evidence are in `docs/RESULTS.md`; chronological interpretation is in `docs/DECISIONS.md`.

## EventSpikeSeg models

`EventSpikeSegXL` is the active detailed DSEC/FPGA implementation target. It has 237,115
registered parameters for 11 classes, 232,059 parameters in its training forward, and
226,767 in the exported inference graph. `EventSpikeSeg140k` remains the compact
140,089-parameter six-class DDD17 reference.

For reference, DDD17 `EventSpikeSeg140k` registers 140,089 parameters and executes
134,637 at inference. XL keeps the same 32/64/128 basis and adds:

```text
timestamp/raw-event input → two-polarity synaptic activity → 32-ch PLIF stem
→ Encoder 1: two residual DW/PW-PLIF blocks at full resolution
   ├─ persistent 32-ch detail path: three residual DW/PW-PLIF blocks
   └─ main semantic path
→ Encoder 2: stride-2 DW/PW-PLIF + two 64-ch residual refinements
   └─ projected stride-2 32→64 residual bridge
→ Encoder 3: stride-2 DW/PW-PLIF + two 128-ch residual refinements
   └─ projected stride-2 64→128 residual bridge
→ serial dilation-2 residual context ×2
→ parallel d1/d2/d4 residual context
→ local Q/K/V spike-mask attention: 32 channels, four 8-channel heads
→ project 128→64 PLIF + upsample + concat 64-ch skip + DW/PW fusion
→ project 64→32 PLIF + upsample
→ late semantic32 + shallow32 + detail32 concatenation
→ 96→96 1×1 synaptic projection + PLIF selector + binary channel enable
→ DW96/PW32 PLIF fusion + residual 32-ch refinement
→ independent spiking class populations
→ temporal spike-count argmax
```

Neuron dynamics remain PLIF with learnable per-channel beta/base thresholds, stem-only `peer_membrane` fInst, and encoder/context triangular fLong/TThresh. PyTorch provides tensors/autograd/optimization; SpikingJelly supplies compatible spiking convolution/PLIF/surrogate infrastructure while project-specific dynamics stay explicit.

### What “fully spiking” means here

Every learned spatial or channel-mixing stage in both models is a spike-driven synapse
population coupled directly to PLIF neurons:

```text
input spikes → learned 3×3 or 1×1 synaptic kernel → membrane current → PLIF spike output
```

The 3×3 and 1×1 kernels are synaptic weights, not conventional ANN `Conv → ReLU`
layers. XL inference executes 50 `SpikingStage`/PLIF populations. Depthwise/pointwise
blocks deliberately contain two PLIF populations, so collapsing them changes trained
connectivity and temporal state.

There is no BatchNorm dependency, dense softmax attention, GAP/MLP inference gate, dense real-valued classifier, fourth downsampling stage, or hard hidden winner-peer WTA in the canonical path.

## XL DSEC training

The XL run uses sequence-disjoint DSEC validation, chronological per-sequence training
windows, ten fixed 5 ms training divisions per 50 ms label interval, and one final loss
after all ten divisions. Numeric state carries only across consecutive frames in the same
sequence and resets at sequence/frame gaps.

The model exposes a late refinement schedule:

```text
0–70%   all layers train jointly
70–90%  semantic backbone frozen; detail/decoder/selector/heads refine
90–100% all layers unfrozen with an additional 0.20× LR multiplier
```

Final training validates after every epoch, saves the best validation-mIoU model, saves a recovery checkpoint every configured N epochs, and saves the last state separately. Auxiliary heads are training-only and are skipped in evaluation/inference.

## Accuracy status

XL is the implementation target, but this does not claim it has already outperformed the
compact model. Accuracy must come from the new DSEC run and subsequent fixed-point
validation; historical protocol numbers remain architecture-search evidence only.


## Digital neuromorphic FPGA implementation target

Training remains PyTorch + SpikingJelly with fixed physical-time divisions. Deployment
in VHDL-2008 on ZCU104
accepts camera events directly: convolution kernels remain shared synaptic weights,
feature-map positions remain logical PLIF states, hidden communication remains binary
spikes/events, and membrane/adaptation/timestamp state persists across events and records
in an external-DDR-backed tile store. The values are fixed-point numerical
membrane/current states—not physical voltages or
currents.

The canonical inference path has no softmax, ReLU/GELU, BatchNorm, or dense count-domain
MLP. `ChannelAffine` can be folded into quantized weights/scales; concat is channel-ID
routing; nearest upsample is spike-address fan-out; residual clamp is event merge/OR;
and temporal class-spike counting/argmax uses integer counters and a comparator. The
selector is local: its 1×1 PLIF spike gates only the corresponding `(channel,y,x)` event.

The scalable implementation is **coarse-grained and time-multiplexed**. A reusable
digital synaptic-accumulator + PLIF processing tile operates across spatial partitions,
channels, and stages while preserving convolutional weight sharing. Logical PLIF
membrane/adaptation state resides in banked BRAM/URAM/LUTRAM between visits. After an
event sparsity is fundamental: touched-address queues, active-neuron lists, per-neuron
last-update timestamps, lazy physical-time decay, and clock-enable suppress idle work.
This trades processing-element count for latency and memory bandwidth without
changing the trained SNN semantics.

The implementation-sensitive mechanisms are timestamp-aware lazy PLIF decay, stem
peer-membrane fInst, encoder/context triangular fLong/TThresh adaptation, and the local
96-channel PLIF selector. The first RTL version should reproduce them under the fixed-point golden
contract; any simplification requires explicit accuracy revalidation. DSEC raw events are
the preferred direct event-stream input, while DDD17 uses its existing digital moment
scheduler.

The verification flow is `SpikingJelly float -> bit-exact integer reference -> VHDL RTL
-> Vivado synthesis/place-route -> post-implementation timing + representative SAIF/VCD
power analysis -> optional ZCU104 measurement`. Vivado latency/power are reported as
estimates unless validated on an instrumented board.
