# EventSpikeSeg

Fully spiking event-camera semantic segmentation for DDD17 and DSEC-Semantic,
designed so the learned inference path can be mapped to a custom digital neuromorphic
FPGA accelerator with fixed-point PLIF state, sparse spike routing, and event-driven synaptic updates.

## Repository layout

```text
src/eventspikeseg/model.py              EventSpikeSeg140k FPGA target plus optional XL software comparison
src/eventspikeseg/model_components.py   shared PLIF/SNN/convolution primitives
src/eventspikeseg/fpga/                 fixed-point export and integer event reference
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

Training and FPGA inference both preserve ten chronological 5 ms updates per 50 ms
record. The deployed input accepts camera events directly, routes them into the active
5 ms slice, adds shared-kernel contributions, and propagates only generated hidden spikes.
DSEC uses eleven continuous class-current outputs after the binary-spiking feature path:
`sky`, `building`, `fence`,
`person`, `pole`, `road`, `sidewalk`, `vegetation`, `vehicle`, `wall`, and
`traffic-sign`.

The trainer consumes every packet before forming one weighted CE + Dice + semantic
auxiliary + boundary objective. `--sequential-chunks K` uses a memory-bounded two-pass replay: first form the
complete-record prediction without an activation graph, then replay chronological chunks
with that one objective's output gradients. This releases each chunk graph without ever
applying the complete target to a partial history. The replay state snapshot is kept in
host RAM so it does not duplicate the model's large persistent neuron state on the GPU.

PLIF leakage is physical-time based:
`retention(delta_us) = beta ** (delta_us / 5000)`. Logits and activity rates are
normalized by elapsed physical time rather than packet count. The final 1×1 class
synapse accumulates continuous current over all ten updates rather than quantizing
confidence to eleven possible output-spike counts.

The DSEC stability profile uses a base learning rate of `5e-4` for both synaptic
weights and learnable PLIF beta/threshold parameters; neuron parameters receive no
additional multiplier. Per-class soft-Dice values are still reported for all
classes, but the scalar Dice objective averages only semantic classes present in the
current target mask. This prevents an absent rare class from being trained toward
zero on every record where it has no labelled pixels.

## FPGA logical-state footprint

Parameter count is **not** runtime neuron count. For the active 11-class
`EventSpikeSeg140k` DSEC implementation at native 440x640, the 27 executed PLIF populations
require

```text
H2xW2 = 220x320, H4xW4 = 110x160, H8xW8 = 55x80
N_mem = 72*H*W + 128*H2*W2 + 480*H4*W4 + 1280*H8*W8
      = 43,366,400 membrane values
```

Triangular threshold adaptation is enabled on **10,982,400** neurons and stores age plus amplitude. A direct asynchronous variant would also require a last-update timestamp per membrane, but the fixed 5 ms baseline does not. With 16-bit membrane plus two 16-bit adaptation fields where enabled, the dense persistent-state baseline is about **124.61 MiB** before queues and counters. Artix-7 XC7A200T has only 1.604 MiB BRAM.
External and onboard DDR are forbidden, so only a lossless zero-default sparse state
table could fit; measured worst-case occupancy is a hard feasibility gate.

- **static/shared:** convolution weights, per-channel beta, per-channel base threshold;
- **persistent per-neuron:** membrane and enabled threshold-adaptation state;
- **temporary:** touched-event synaptic current and sparse spike FIFOs.

The FPGA instantiates a permanent actor for every executed layer. An actor may sequence
its own lanes, but arithmetic is not shared across layers and it must preserve one
logical state record per `(layer,c,y,x)`. The exact sparse execution
flow for the baseline DSEC runtime is `50 ms raw-event record -> ten 5 ms slices -> layer-major sparse destination-address generation -> fixed-step
decay -> weight addition -> threshold/reset -> state writeback -> emitted events`.
There is an explicit 5 ms neural timestep boundary; the complete 50 ms record contains ten such ordered updates. See `docs/ARCHITECTURE.md` and
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
rectification, timestamp, and label alignment. `train-dsec` is the active native 440x640,
11-class 140k run; `train-dsec-xl` is an optional software capacity comparison.
Both DSEC replay services deliberately train in FP32. Do not add `--amp`: FP16
autocast is incompatible with the memory-bounded temporal surrogate-gradient
replay and can reject every optimizer update while leaving the scalar loss finite.

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

`EventSpikeSeg140k` is the only DSEC/FPGA implementation target. With two raw-event
inputs and 11 classes it has 142,277 registered parameters, 141,535 executed inference
parameters, 135,624 executed synaptic weights, and 27 executed PLIF populations plus
one stateless temporal class-current readout.
`EventSpikeSegXL` remains a software-only capacity comparison and is rejected by the
FPGA exporter.

The 140k graph keeps the 32/64/128 basis:

```text
native 440x640 two-polarity activity
   ├─ 2→8 PLIF stem + standard 3x3 PLIF detail block at native resolution
   └─ learned standard 5x5 stride-2 PLIF semantic stem → 32x220x320
→ standard 32-channel spatial/channel block + residual DW/PW refinement
→ standard stride-2 32→64 PLIF + two 64-channel DW/PW refinements at 110x160
→ stride-2 DW/PW 64→128 + two 128-channel refinements at 55x80
→ serial dilation-2 residual context ×2
→ project 128→64 PLIF + upsample + binary OR with the quarter-scale 64-ch skip
→ residual 64-ch DW/PW-PLIF decoder refinement
→ project 64→32 PLIF + upsample + binary OR with the half-scale 32-ch skip
→ nearest event fan-out to native resolution
→ semantic32 + detail8 concatenation → DW40/PW16 PLIF fusion
→ 16→11 class synapse → temporal continuous-current accumulation → argmax
```

Neuron dynamics remain PLIF with learnable per-channel beta/base thresholds, stem-only peer-membrane inhibition, and encoder/context triangular threshold adaptation. PyTorch provides tensors/autograd/optimization; SpikingJelly supplies compatible spiking convolution/PLIF/surrogate infrastructure while project-specific dynamics stay explicit.

### What “fully spiking” means here

Every learned feature-extraction spatial or channel-mixing stage in the 140k model is a
spike-driven synapse population coupled directly to PLIF neurons:

```text
input spikes → learned 3×3 or 1×1 synaptic kernel → membrane current → PLIF spike output
```

The 3×3 and 1×1 kernels are synaptic weights, not conventional ANN `Conv → ReLU`
layers. The deployed 140k inference executes 27 `SpikingStage`/PLIF populations. Depthwise/pointwise
blocks deliberately contain two PLIF populations, so collapsing them changes trained
connectivity and temporal state.

The only non-spiking learned inference operation is the final 1×1 class-current
accumulator. It consumes binary spikes and maps to conditional stored-weight additions;
it avoids the old ten-step output spike-count quantization.

## DSEC training

The 140k run uses sequence-disjoint DSEC validation, chronological per-sequence training
windows, ten fixed 5 ms training divisions per 50 ms label interval, and one final loss
after all ten divisions. Numeric state carries only across consecutive frames in the same
sequence and resets at sequence/frame gaps.

The model exposes a late refinement schedule:

```text
0–70%   all layers train jointly
70–90%  semantic backbone frozen; detail/decoder/readout heads refine
90–100% all layers unfrozen with an additional 0.20× LR multiplier
```

Final training validates after every epoch, saves the best validation-mIoU model, saves a recovery checkpoint every configured N epochs, and saves the last state separately. Auxiliary heads are training-only and are skipped in evaluation/inference.

## Accuracy status

Choosing 140k as the implementation target does not make a new accuracy claim. Accuracy
must come from its DSEC checkpoint and subsequent fixed-point validation; historical
protocol numbers remain architecture-search evidence only.


## Digital neuromorphic FPGA implementation target

Training remains PyTorch + SpikingJelly with fixed physical-time divisions. Deployment
in VHDL-2008 on the Digilent Nexys Video XC7A200T
accepts camera events directly: convolution kernels remain shared synaptic weights,
feature-map positions remain logical PLIF states, hidden communication remains binary
spikes/events, and membrane/adaptation/timestamp state persists across events and records
in a lossless sparse on-chip BRAM/LUTRAM state store. The board's DDR3 is deliberately
not used. This mapping is conditional on measured worst-case live-state occupancy; the
dense state cannot fit. The values are fixed-point numerical
membrane/current states—not physical voltages or
currents.

The canonical inference path has no softmax, ReLU/GELU, BatchNorm, or dense count-domain
MLP. `ChannelAffine` can be folded into quantized weights/scales; concat is channel-ID
routing; nearest upsample is spike-address fan-out; residual clamp is event merge/OR;
and temporal class-current accumulation/argmax uses signed accumulators and a comparator.

The implementation uses **27 permanent PLIF layer actors plus one class-current readout**. Every actor owns convolution
addressing, accumulator lanes, PLIF/mechanism logic, queues, and local weight ROM; there
is no cross-layer compute sharing or reconfiguration. Logical PLIF
membrane/adaptation state resides in banked sparse BRAM/LUTRAM. Within an actor,
event sparsity is fundamental: touched-address queues, active-neuron lists, fixed-step
state advancement, and clock-enable suppress idle work.
This trades processing-element count for latency and memory bandwidth without
changing the trained SNN semantics.

The implementation-sensitive mechanisms are fixed-step PLIF decay, stem
peer-membrane inhibition, encoder/context triangular threshold adaptation, and the final
continuous class-current accumulator. The first RTL version should reproduce them under the fixed-point golden
contract; any simplification requires explicit accuracy revalidation. DSEC raw events are
the preferred direct event-stream input, while DDD17 uses its existing digital moment
scheduler.

The verification flow is `SpikingJelly float -> bit-exact integer reference -> VHDL RTL
-> Vivado synthesis/place-route -> post-implementation timing + representative SAIF/VCD
power analysis -> optional Nexys Video measurement`. Vivado latency/power are reported as
estimates unless validated on an instrumented board.

Export a trained checkpoint with:

```powershell
python scripts/export_fpga_model.py --checkpoint artifacts/EventSpikeSeg140k_seed17_best.pt --output artifacts/fpga_export
```

The exporter hard-rejects XL and emits the exact 27-PLIF-actor plus current-readout manifest, affine-folded int8
ROMs, per-actor quantized neuron parameters, and the fixed-point contract.


## FPGA runtime timing contract (50 ms records)

DSEC hardware inference follows the same temporal discretization used for training. Each semantic record spans 50 ms and is represented by ten chronological 5 ms slices. The FPGA treats one complete 50 ms record as the scheduling/output unit, but it must still execute all ten PLIF updates; the ten slices must never be collapsed into one neuron update.

For memory locality, the intended hardware order is layer-major over the complete temporal record: keep a layer (or a spatial tile of that layer) resident, execute its `t0..t9` updates in order, buffer the resulting ten spike slices, write the final persistent state back, then move to the next layer. Sparse convolution is retained inside every 5 ms slice: only nonzero spike locations generate synaptic additions. The baseline is therefore fixed-time rather than fully asynchronous, and no per-membrane 32-bit timestamp is required.

One segmentation result is emitted per 50 ms record (20 Hz dataset cadence) after temporal class-current accumulation. To sustain real time, compute for one record must average no more than 50 ms; double buffering may overlap acquisition of the next record with computation of the previous one.
