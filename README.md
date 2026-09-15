# EventSpikeSeg

Fully spiking event-camera semantic segmentation for DDD17 and DSEC-Semantic,
designed so the learned inference path can be mapped to a custom digital neuromorphic
ASIC with fixed-point PLIF state, sparse spike routing, and event-driven synaptic updates.

## Repository layout

```text
src/eventspikeseg/model.py              EventSpikeSeg140k and EventSpikeSegXL ASIC model definitions
src/eventspikeseg/model_components.py   shared PLIF/SNN/convolution primitives
src/eventspikeseg/asic/                 fixed-point export, capacity, and integer event reference
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
docs/ACTIVE_TASKS.md                    active processes, blockers, and exact resume order
docs/BUGS.md                            open limitations and resolved failures
asic/                                   native SystemVerilog RTL and OpenROAD flow setup
```

Before resuming training or ASIC implementation, read `docs/ACTIVE_TASKS.md`. It records
the live process inventory, completed work that should be reused, current blockers, and
the ordered next stages.

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

Training and ASIC inference both preserve ten chronological 5 ms updates per 50 ms
record. The deployed input accepts camera events directly, routes them into the active
5 ms slice, adds shared-kernel contributions, and propagates only generated hidden spikes.
DSEC source masks contain eleven labels, which the active profile merges into six
continuous class-current outputs after the binary-spiking feature path: `flat`
(road + sidewalk), `construction+sky` (sky + building + fence + wall), `object`
(pole + traffic-sign), `nature` (vegetation), `human` (person), and `vehicle`.
Pass `--dsec-classes 11` only to reproduce the superseded fine-label experiment.

After every final-model validation pass, training saves the same three seed-selected
validation records under `<checkpoint-dir>/images`. Each PNG contains the complete 50 ms
event-count map on the left (negative events red, positive events blue, logarithmic
count-to-intensity scaling), the coloured ground-truth mask in the middle, and the
coloured semantic prediction on the right. The predictions are captured during the
normal chronological validation pass, so this adds no extra forward passes and does not
disturb recurrent stream state.

The trainer consumes every packet before forming one complete-record semantic objective.
Final-model loss coefficients follow a smooth epoch-fraction curriculum: pixel CE starts
stronger while predictions are unstructured; equal target-present-class macro CE, Dice,
and boundary supervision rise later; auxiliary CE declines as the main decoder matures.
Static class weights, focal loss, and same-class region consistency remain inactive.
`--sequential-chunks K` uses a memory-bounded two-pass replay: first form the
complete-record prediction without an activation graph, then replay chronological chunks
with that one objective's output gradients. This releases each chunk graph without ever
applying the complete target to a partial history. The replay state snapshot is kept in
host RAM so it does not duplicate the model's large persistent neuron state on the GPU.
Validation uses the same `K` chronological chunks under `no_grad`, preventing its
temporal feature tensors from exceeding the chunked training geometry while preserving
the same complete-record prediction.

For the active DSEC path, PLIF time advances on the same fixed grid used by hardware: ten explicit 5 ms updates per 50 ms record. Training presents one accumulated synaptic current per PLIF per update. The sparse ASIC reaches the same result lazily: a touched state uses its 24-bit bin tag to apply learned `beta` once per elapsed 5 ms interval, while untouched states incur no access. No microsecond timestamp is required. Logits and activity rates remain normalized to the complete physical record. The final 1×1 class
synapse accumulates continuous current over all ten updates rather than quantizing
confidence to a small number of possible output-spike counts.

The DSEC stability profile uses a base learning rate of `5e-4` for both synaptic
weights and learnable PLIF beta/threshold parameters; neuron parameters receive no
additional multiplier. Per-class soft-Dice values are still reported for all
classes, but the scalar Dice objective averages only semantic classes present in the
current target mask. This prevents an absent rare class from being trained toward
zero on every record where it has no labelled pixels.

## ASIC logical-state footprint

The sole hardware implementation target is a custom actor-local-memory ASIC.

Parameter count is **not** runtime neuron count. For the active six-class
`EventSpikeSeg140k` DSEC implementation at native 440x640, the 25 executed PLIF populations
require

```text
H2xW2 = 220x320, H4xW4 = 110x160, H8xW8 = 55x80
N_mem = 32*H*W + 128*H2*W2 + 416*H4*W4 + 1280*H8*W8
      = 30,976,000 membrane values
```

Triangular threshold adaptation is enabled on **10,982,400** neurons. The active clocked
resident runtime stores one signed 32-bit Q15.16 combined accumulator/state per PLIF, a 6-bit
integer age and 19-bit unsigned Q3.16 amplitude where adaptation is enabled, and no per-neuron
time tag. Synaptic weights use signed 24-bit Q7.16. Its exact logical resident state is
**150.89 MiB-equivalent**, down from 189.60 MiB for
separate int24 current, int16 membrane, and two-int16 adaptation fields. This is a logical
bit inventory, not a characterized full-chip area or power result.

- **static/shared:** convolution weights, per-channel beta, per-channel base threshold;
- **persistent per-neuron:** combined pre-leaked int32 Q15.16 accumulator/state and enabled compact threshold-adaptation state;
- **temporary/interconnect:** sparse spike and completion-token FIFOs.

The ASIC instantiates a permanent actor for every executed PLIF population, but the 25
actors are **not a linear chain**. They form the fixed EventSpikeSeg140k v8 DAG: input forks
into detail and semantic paths, residual blocks use binary-OR joins, `x1`/`x2` fan out into
later decoder skips, and decoder/final concatenations bring those branches together. For a
standard 3x3 plane, nine parallel presynaptic tap cells emit signed contributions into one
canonical postsynaptic current/membrane array. Events and ordered 5 ms completion tokens
follow the same fixed routes; every multi-input join waits for all required same-bin tokens
before forwarding completion. The SystemVerilog RTL uses clocked ready/valid channels and
does not claim an electrically clockless/QDI implementation. See `docs/ARCHITECTURE.md`,
`src/eventspikeseg/asic/topology.py`, and `project_spec.yaml` for the full contract.

## Main commands

CPU-only ASIC implementation verification uses its own Compose file and does not
pull the CUDA training image:

```powershell
docker compose -f compose_ASIC.yaml build
docker compose -f compose_ASIC.yaml run --rm test
docker compose -f compose_ASIC.yaml run --rm rtl
docker compose -f compose_ASIC.yaml run --rm synthesis
docker compose -f compose_ASIC.yaml run --rm lint
```

Dataset inspection and training continue to use the CUDA-capable main Compose file:

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
six-class 140k run; `train-dsec-xl` is an optional 11-class software capacity comparison.
Both DSEC replay services deliberately train in FP32. Do not add `--amp`: FP16
autocast is incompatible with the memory-bounded temporal surrogate-gradient
replay and can reject every optimizer update while leaving the scalar loss finite.
For both final models, the last three epochs enable quantization-aware training by default:
FP32 master parameters and gradients are retained, while the forward path uses the exact
range-matched ASIC fixed-point formats. QAT explicitly unfreezes the semantic backbone and
all PLIF/mechanism parameters so every deployed parameter can compensate for fixed-point
rounding. Set `--asic-qat-epochs 0` only for a deliberate floating-point diagnostic run.

The completed 140k epoch-80 checkpoint predates this QAT rule. Its exact 80-epoch correction
starts from `EventSpikeSeg140k_seed17_epoch077.pt` and reruns epochs 78--80 with
`--epochs 80 --asic-qat-epochs 3`; it does not restart from epoch 1. Keep `--resume-lr 0.001`
so the restored cosine scheduler is evaluated at epoch 77 on the original 80-epoch horizon.
The old epoch-80 export remains a valid pre-QAT hardware artifact until the corrected QAT
checkpoint is produced and validated. The existing `train-dsec` service is configured for this
epoch-77 to epoch-80 resume; run `docker compose run --rm train-dsec` after XL releases the GPU,
then regenerate `artifacts/ASIC` from the QAT-selected best checkpoint.

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

`EventSpikeSeg140k` is the baseline six-class DSEC/ASIC implementation target. With two raw-event
inputs and six classes it has 149,835 registered parameters, 149,423 executed inference
parameters, 143,824 executed synaptic weights, and 25 executed PLIF populations plus
one stateless temporal class-current readout.
`EventSpikeSegXL` is the expanded eleven-class ASIC target. Its epoch-1 checkpoint currently
drives structural export/RTL bring-up only; final constants must be regenerated from the
selected trained/QAT checkpoint. Its configuration stays below one million registered
parameters: 978,559 for six classes and 979,179 for eleven. Capacity is concentrated
at the lowest semantic resolution and in full-convolution decoder fusion so native
resolution state is limited to a 16-channel detail path and 24-channel final refinement.
Native 440x640 localization therefore complements the 55x80 semantic context rather
than being replaced by it.

The 140k graph keeps the 32/64/128 basis:

```text
native 440x640 two-polarity activity
   ├─ 2→8 PLIF stem + standard 3x3 PLIF detail block at native resolution
   └─ learned standard 5x5 stride-2 PLIF semantic stem → 32x220x320
→ standard 32-channel spatial/channel block + residual DW/PW refinement
→ standard stride-2 32→64 PLIF + two 64-channel DW/PW refinements at 110x160
→ stride-2 DW/PW 64→128 + two 128-channel refinements at 55x80
→ serial dilation-2 residual context ×2
→ project 128→64 PLIF + upsample + concatenate the quarter-scale 64-ch skip
→ standard 1×1 128→64 PLIF fusion
→ project 64→32 PLIF + upsample + multiplicity-preserving sum with the half-scale 32-ch skip
→ nearest event fan-out to native resolution
→ semantic32 + detail8 concatenation → standard 3×3 40→16 PLIF fusion
→ 16→6 class synapse → temporal continuous-current accumulation → argmax
```

Neuron dynamics remain PLIF with learnable per-channel beta/base thresholds, stem-only peer-membrane inhibition, and encoder/context triangular threshold adaptation. PyTorch provides tensors/autograd/optimization; SpikingJelly supplies compatible spiking convolution/PLIF/surrogate infrastructure while project-specific dynamics stay explicit.

### What “fully spiking” means here

Every learned feature-extraction spatial or channel-mixing stage in the 140k model is a
spike-driven synapse population coupled directly to PLIF neurons:

```text
input spikes → learned 3×3 or 1×1 synaptic kernel → membrane current → PLIF spike output
```

The 3×3 and 1×1 kernels are synaptic weights, not conventional ANN `Conv → ReLU`
layers. The deployed 140k inference executes 25 `SpikingStage`/PLIF populations. Depthwise/pointwise
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
0–90%   all layers train jointly
90–100% semantic backbone frozen; detail/decoder/readout heads refine
```

Final training validates after every epoch, saves the best validation-mIoU model, saves a recovery checkpoint every configured N epochs, and saves the last state separately. Auxiliary heads are training-only and are skipped in evaluation/inference.

The `train-dsec-no-custom-mechanisms` service performs a one-epoch weights-only
fine-tune from the completed epoch-80 checkpoint with peer-membrane inhibition
and triangular threshold adaptation forced off. It retains all tensor-shape and
checkpoint-compatible PLIF stages, uses a fresh `1e-5` optimizer, and writes only
to `artifacts/checkpointsV4/dsec_6class/no_custom_mechanisms`.

When resuming, `--resume-lr RATE` replaces the largest optimizer-group initial
learning rate with `RATE`, preserves the relative initial rates of the other
groups, retargets cosine decay to the current `--epochs` value, and then
calculates the current rates from the checkpoint's completed epoch. It does not
restart training at epoch zero or force a late epoch to use the full initial
rate. This also lets a checkpoint produced by a short ablation (for example,
one epoch) continue under a longer schedule without restoring an already
exhausted scheduler.

## Accuracy status

Choosing 140k as the implementation target does not make a new accuracy claim. Accuracy
must come from its DSEC checkpoint and subsequent fixed-point validation; historical
protocol numbers remain architecture-search evidence only.


## Digital neuromorphic ASIC implementation target

Training remains PyTorch + SpikingJelly with fixed physical-time divisions. Deployment
uses native SystemVerilog, Yosys technology mapping, and OpenROAD physical design.
Convolution kernels remain shared synaptic weights, feature-map positions remain
logical PLIF states, and hidden communication remains binary spike events. Combined accumulator
and adaptation state stays in the owning actor's local memory. The values are fixed-point numerical
states—not physical voltages or
currents.

The canonical inference path has no softmax, ReLU/GELU, BatchNorm, or dense count-domain
MLP. `ChannelAffine` can be folded into quantized weights/scales; concat is channel-ID
routing; nearest upsample is spike-address fan-out; residual clamp is event merge/OR;
and temporal class-current accumulation/argmax uses signed accumulators and a comparator.

The implementation uses **25 permanent PLIF actors in a compile-time static DAG plus one
class-current readout**. The actor tuple exported by software is a deterministic topological
listing only, not runtime `actor0 -> ... -> actor24` order. Every actor owns convolution
addressing, combined accumulator/PLIF logic, queues, local weight ROM, and local
state elements; there is no cross-layer compute sharing or reconfiguration. Dedicated fixed
routes implement fanout, residual OR/dedup, channel concatenation, upsample fanout, and the
multiplicity-preserving `project2 + x1` skip. Contributions add into the combined accumulator
during one fixed 5 ms bin; completion performs one threshold/reset/mechanism commit and pre-applies
beta for the next bin. There is no per-neuron timestamp or lazy time update.
This trades processing-element count for latency and memory bandwidth without
changing the trained SNN semantics.

The implementation-sensitive mechanisms are fixed-step PLIF decay, stem
peer-membrane inhibition, encoder/context triangular threshold adaptation, and the final
continuous class-current accumulator. The first RTL version should reproduce them under the fixed-point golden
contract; any simplification requires explicit accuracy revalidation. DSEC raw events are
the preferred direct event-stream input, while DDD17 uses its existing digital moment
scheduler.

The verification flow is `SpikingJelly float -> bit-exact integer reference -> SystemVerilog RTL
-> Icarus/cocotb -> Yosys/OpenROAD routed timing/parasitics -> representative DSEC VCD/SAIF power`.
ASAP7 is an open predictive 7 nm research-PPA platform, not a tapeout PDK. SKY130RAM is
reserved for a manufacturable actor-tile check. A scale-suitable full chip requires an
accessible 22/28 nm-or-better PDK and characterized SRAM macros.

Export a trained checkpoint with:

```sh
python scripts/export_asic_model.py \
  --checkpoint artifacts/checkpointsV4/dsec_6class/EventSpikeSeg140k_seed17_best.pt \
  --output artifacts/ASIC
```

Prepare the structurally exact XL epoch-1 export and generated resident RTL without synthesis:

```bash
docker compose -f compose_ASIC.yaml run --rm test \
  bash asic/scripts/prepare_xl_asic.sh
```

Set `XL_CHECKPOINT` and `XL_ASIC_EXPORT` when replacing epoch 1 with the selected final/QAT
checkpoint. Full XL Yosys elaboration is a separate explicitly launched
`asic/scripts/run_xl_synthesis.sh` because it competes heavily for host memory.

Run the exact epoch-1 44-actor integer graph over one ten-bin/50 ms DSEC sample in the CPU
verification Docker image with `bash asic/scripts/run_xl_native_integer_simulation.sh`. The
default export is `artifacts/ASIC_XL`; the run checkpoints at each bin and writes both an activity
JSON and the final 440x640 `uint8` prediction under `artifacts/RTL/profile/`. This validates
fixed-point graph execution, not trained accuracy, RTL cycles, or ASIC energy.

The complete `artifacts/` directory is intentionally ignored by Git. Checkpoints, exported
weights, generated tops, replay vectors, metrics, and physical-design outputs remain local and
must be retained or backed up outside Git; derived exports are regenerated from the retained
checkpoint using the tracked source and scripts.

The exporter emits either the exact 25-actor 140k or 44-actor XL manifest,
affine-folded signed 24-bit Q7.16 ROMs, per-actor quantized neuron parameters, the fixed-point contract,
and an explicit `layer_graph.json` containing DAG nodes, directed edges, channel-remap/fanout
operations, residual/skip join semantics, and same-bin completion-token rendezvous rules.


## ASIC runtime timing contract (autonomous actors, 5 ms semantic epochs)

DSEC training and hardware preserve the same 5 ms physical-time grid. Events move through
the permanently wired **non-linear actor DAG** without a global layer scheduler. A completion
token follows the last event of each epoch and is multicast anywhere the spike stream forks.
At residual/skip/concat joins, one downstream completion is released only after every
required upstream branch has delivered the same bin tag. This prevents a fast path from
closing a downstream PLIF before a slower skip/detail path has contributed. Per-contribution
thresholding is forbidden.

The ASIC ingress does not load a dense 5 ms tensor or store a complete input bin. Rectified
camera events arrive in timestamp order and immediately perform only their connected signed
weight additions. At the 5 ms boundary, the ingress sends an epoch-completion token. Thus
event ingestion and synaptic accumulation are sequential and sparse, while PLIF
leak/threshold/reset remains one clocked commit per resident destination per 5 ms epoch so it
stays equivalent to the trained model.

Every resident neuron owns one signed int32 Q15.16 combined accumulator. It begins a bin with the
pre-leaked prior membrane, receives that bin's signed contributions, and at completion is
clamped, thresholded/reset, processed by optional mechanisms, and pre-leaked for the next bin.
Adaptation age advances as an integer count of 5 ms bins. There is no per-neuron timestamp,
last-bin tag, or touched-state lookup.

The prediction window is configurable; start with **10 bins = 50 ms = 20 Hz** to match training/readout. PLIF state persists across prediction boundaries; only signed class-current accumulation resets after prediction.

Real-time feasibility is measured per bin. With `C_bin` cycles and routed clock `f_clk`, define `U=C_bin/(f_clk*0.005)` and `H=1/U`. Hard sustained operation requires `U<=1` (`H>=1`). The starting target is `U<=0.8` (`H>=1.25`). At 100 MHz that is 500,000 hard cycles/bin and 400,000 target cycles/bin; at 150 MHz 750,000/600,000; at 200 MHz 1,000,000/800,000.

The native SystemVerilog ASIC implementation now contains a synthesizable channel-aware
standard/grouped/depthwise convolution scatter, autonomous completion-token PLIF actor,
lossless two-way event/token fork, same-bin rendezvous join, fixed concat remap, 2x event
upsample, and a correctness-reference residual binary-OR/dedup merge. Trained weights remain
replaceable ROM contents. Channelized projections now feed independent per-output-channel
spatial PLIF state and per-channel beta/threshold tables. The trained v4 checkpoint has been
exported and the manifest-driven generator emits the complete weighted **25-actor DAG**,
including retinotopic mechanisms and the temporal readout. Model-scale state, queues,
readout, and residual storage now use bounded banked 1RW interfaces. Remaining physical work
is to bind characterized SRAM macros, size residual capacity from native activity, and run
routed PPA. The SRAM-integrated real-checkpoint reduced-8x8 full-DAG replay already matches
all 64 semantic outputs and records 12,135 steady-state cycles per ten-bin frame at the
assumed 100 MHz simulation clock; this is behavioral verification, not native PPA.
