# EventSpikeSeg

Fully spiking event-camera semantic segmentation for DDD17 and DSEC-Semantic,
designed so the learned inference path can be mapped to a custom digital neuromorphic
FPGA accelerator with fixed-point PLIF state, sparse spike routing, and event-driven synaptic updates.

## Repository layout

```text
src/eventspikeseg/model.py              canonical EventSpikeSeg140k (~140k) plus optional EventSpikeSegXL
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

Semantic timestamps are nominally 20 Hz: the installed files measure approximately
50,000 µs between masks. One item slices raw events from `[label_time-50ms,
label_time)`, applies the supplied raw-to-rectified coordinate map, removes the
bottom 40 rows outside the 640×440 semantic view, and dispatches each polarity event
into its timestamp-selected PLIF clock. Input planes are binary: multiple events at
the same pixel, polarity, and clock remain one input spike. No histogram intensity,
timestamp mean/std reconstruction, or whole-recording preload is used.

`internal_updates=10` therefore means ten chronological 5 ms event clocks for one
mask—not ten repeated copies. The model receives `[T,N,2,H,W]` directly. The 140k
feature architecture is unchanged; DSEC necessarily replaces the six-population
DDD17 class head with eleven spiking output populations: `sky`, `building`, `fence`,
`person`, `pole`, `road`, `sidewalk`, `vegetation`, `vehicle`, `wall`, and
`traffic-sign`.

For memory-constrained training, `--sequential-chunks K` divides those clocks into
`K` equal chronological truncated-BPTT segments. For example,
`--internal-updates 10 --sequential-chunks 2` runs clocks 0–4, backpropagates,
preserves the numeric PLIF state while detaching its gradient history, and then runs
clocks 5–9. Chunk losses are averaged, and the optimizer still steps only after the
complete record (subject to `--accumulate-steps`). The default `1` retains the
original full-record forward/backward. Values above one are DSEC-only and must divide
`internal_updates` exactly.

The DSEC stability profile uses a base learning rate of `5e-4` for both synaptic
weights and learnable PLIF beta/threshold parameters; neuron parameters receive no
additional multiplier. Per-class soft-Dice values are still reported for all
classes, but the scalar Dice objective averages only semantic classes present in the
current target mask. This prevents an absent rare class from being trained toward
zero on every record where it has no labelled pixels.

## FPGA logical-state footprint

The model's ~140k trainable parameters are mostly shared synaptic/channel parameters and
are **not** the runtime neuron count. Every PLIF feature-map element has an independent
membrane state. For six-class `EventSpikeSeg140k`, the 37 executed inference populations
require

```text
N_mem = 678*H*W + 480*H2*W2 + 1280*H4*W4
H2=ceil(H/2), W2=ceil(W/2), H4=ceil(H2/2), W4=ceil(W2/2)
```

At 212x282 this is **52,524,272 membrane values**. fLong is enabled on **9,836,800** of
those logical neurons and stores separate adaptation age/amplitude state. We therefore
distinguish:

- **static/shared:** convolution weights, per-channel beta, per-channel base threshold;
- **persistent per-neuron:** membrane and enabled fLong state for each `(layer,c,y,x)`;
- **temporary:** per-layer/per-timestep synaptic-current accumulators and sparse spike FIFOs.

The FPGA may use far fewer physical PLIF arithmetic units by time-multiplexing them, but
it must preserve one logical state record per `(layer,c,y,x)`. The exact sparse execution
flow is `spike address -> destination-address generation -> weight addition into temporary
current -> timestep barrier -> PLIF update once -> state writeback -> emit fired addresses`.
This avoids dense sliding-window convolution while preserving the trained discrete-time
semantics. See `docs/ARCHITECTURE.md` and `project_spec.yaml` for the full contract.

## Main commands

```powershell
docker compose run --rm inspect-ddd17
docker compose run --rm inspect-dsec
docker compose run --rm lint
docker compose run --rm test
docker compose run --rm train-ddd17-smoke
docker compose run --rm train-ddd17
docker compose run --rm train-dsec
docker compose run --rm train-ddd17
```

`inspect-ddd17` validates the DDD17 manifest. `inspect-dsec` verifies sequence event,
rectification, timestamp, and label alignment. `train-ddd17` is the canonical DDD17 run; `train-dsec` is the same canonical feature architecture with the raw-event, eleven-class DSEC head.

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

## Canonical EventSpikeSeg140k model

`EventSpikeSeg140k` is the canonical **140,089-parameter** spike-native model. The optional 236,445-parameter expanded comparison is **`EventSpikeSegXL`**.

For DDD17, 140,089 is the registered parameter count; the executed training forward uses 135,033 parameters and deployed inference uses 134,637 because inherited `refine2` (5,056 parameters) is never called and the 396-parameter auxiliary head is training-only. The canonical topology uses:

```text
timestamp/raw-event input → two-polarity synaptic activity → 32-ch PLIF stem
→ Encoder 1: two residual DW/PW-PLIF blocks at full resolution
   ├─ persistent 32-ch detail path: three residual DW/PW-PLIF blocks
   └─ main semantic path
→ Encoder 2: stride-2 DW/PW-PLIF + two 64-ch residual refinements
→ Encoder 3: stride-2 DW/PW-PLIF + two 128-ch residual refinements
→ serial dilation-2 residual context ×2
→ project 128→64 PLIF + upsample + 64-ch skip + residual refinement
→ project 64→32 PLIF + upsample
→ late semantic32 + shallow32 + detail32 concatenation
→ 96→96 1×1 synaptic projection + PLIF selector + binary channel enable
→ DW96/PW32 PLIF fusion + residual 32-ch refinement
→ independent spiking class populations
→ temporal spike-count argmax
```

Neuron dynamics remain PLIF with learnable per-channel beta/base thresholds, stem-only `peer_membrane` fInst, and encoder/context triangular fLong/TThresh. PyTorch provides tensors/autograd/optimization; SpikingJelly supplies compatible spiking convolution/PLIF/surrogate infrastructure while project-specific dynamics stay explicit.

### What “fully spiking” means here

Every learned spatial or channel-mixing stage in `EventSpikeSeg140k` is a spike-driven synapse population coupled directly to PLIF neurons:

```text
input spikes → learned 3×3 or 1×1 synaptic kernel → membrane current → PLIF spike output
```

The 3×3 and 1×1 kernels are synaptic weights, not conventional ANN `Conv → ReLU` layers; there is no ReLU/GELU/sigmoid activation in the final learned feature or class-map path. These kernels require `spikingjelly.activation_based.layer.Conv2d` (40 registered `SpikingStage` populations; 37 execute during canonical inference); model construction fails clearly if SpikingJelly is unavailable. Depthwise/pointwise blocks deliberately contain two PLIF populations—3×3 spatial filtering followed by 1×1 channel mixing—so collapsing them would remove an intermediate spiking state and alter both connectivity and temporal dynamics.

There is no BatchNorm dependency, dense softmax attention, GAP/MLP inference gate, dense real-valued classifier, fourth downsampling stage, or hard hidden winner-peer WTA in the canonical path.

## Canonical training

The final model uses a deterministic temporal holdout from the DDD17 training split. With multiple sequence IDs, complete sequences are held out. With one sequence, one contiguous block is held out and the resulting frame-index gap forces a state reset. The official test split is reserved for final reporting.

The model exposes a late refinement schedule:

```text
0–70%   all layers train jointly
70–90%  semantic backbone frozen; detail/decoder/selector/heads refine
90–100% all layers unfrozen with an additional 0.25× LR multiplier
```

Final training validates after every epoch, saves the best validation-mIoU model, saves a recovery checkpoint every configured N epochs, and saves the last state separately. Auxiliary heads are training-only and are skipped in evaluation/inference.

## Accuracy status

`EventSpikeSeg140k` is the canonical architecture by design; its historical architecture-search numbers are not automatically timestamp-stream accuracy claims. Historical input-protocol results remain architecture-search evidence only. The next optional capacity comparison is canonical `EventSpikeSeg140k` versus `EventSpikeSegXL` on the same timestamp stream; FPGA deployment work is based on canonical `EventSpikeSeg140k`.


## Digital neuromorphic FPGA implementation target

Training remains PyTorch + SpikingJelly. Deployment keeps the same spike-native
semantics in VHDL-2008 on ZCU104: convolution kernels remain shared synaptic weights,
feature-map positions remain logical PLIF states, hidden communication remains binary
spikes/events, and membrane/adaptation state persists across clocks and records. The
values are fixed-point numerical membrane/current states—not physical voltages or
currents.

The canonical inference path has no softmax, ReLU/GELU, BatchNorm, or dense count-domain
MLP. `ChannelAffine` can be folded into quantized weights/scales; concat is channel-ID
routing; nearest upsample is spike-address fan-out; residual clamp is event merge/OR;
final temporal spike counting/argmax is implemented with integer counters and a
comparator. The selector's binary `amax(H,W)` can be implemented as one `seen_spike`
flag per channel rather than a dense floating-point reduction.

The scalable implementation is **coarse-grained and time-multiplexed**. A reusable
digital synaptic-accumulator + PLIF processing tile operates across spatial partitions,
channels, and stages while preserving convolutional weight sharing. Logical PLIF
membrane/adaptation state resides in banked BRAM/URAM/LUTRAM between visits. After an
exact full/tiled implementation is established, event sparsity can be exploited with
touched-address queues, active-neuron lists, lazy decay, and clock-enable during idle
periods. This trades processing-element count for latency and memory bandwidth without
changing the trained SNN semantics.

The three implementation-sensitive mechanisms are stem peer-membrane fInst,
encoder/context triangular fLong/TThresh adaptation, and the 96-channel selector global
binary enable. The first RTL version should reproduce them under the fixed-point golden
contract; any simplification requires explicit accuracy revalidation. DSEC raw events are
the preferred direct event-stream input, while DDD17 uses its existing digital moment
scheduler.

The verification flow is `SpikingJelly float -> bit-exact integer reference -> VHDL RTL
-> Vivado synthesis/place-route -> post-implementation timing + representative SAIF/VCD
power analysis -> optional ZCU104 measurement`. Vivado latency/power are reported as
estimates unless validated on an instrumented board.
