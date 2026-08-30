# Bugs and limitations

## Dataset representation limitation

**Status: explicit approximation in software.**

The Ev-SegNet download contains histogram activity plus per-polarity timestamp mean/std, not raw asynchronous event tuples. The scheduler conserves activity across three arrivals at mean and mean±std. Exact within-interval timing cannot be reconstructed, so hardware/accuracy reporting must describe this moment approximation.

## Rare-class collapse

**Status:** open.

Object, nature, human, and vehicle classes remain weak or absent in the low-budget mechanism screen. Ground-truth support for the 128-sample held-out subset was:

```text
flat               54,829 pixels
construction+sky  388,044
object               1,615
nature              50,690
human                  702
vehicle              28,408
```

The mechanism-screen winner predicted no nature or vehicle pixels and only one human pixel. This cannot be fixed by architecture ranking alone. Continue recording ground-truth and predicted pixel counts, and do not promote a model solely on overall pixel accuracy.

## Resolved: whole-feature-map binary adaptation

The old `amax` activity rule treated one spike like dense activity and could raise an entire feature-map threshold. The active mechanism uses local triangular threshold adaptation driven by retinotopic membrane energy instead.

## Resolved: hidden hard winner gating in the active top five

The completed mechanism screen showed `winner_peer` inhibition starving the encoder: spike rates fell to approximately `0.0474 → 0.00306 → 0.000149` across enc1/enc2/enc3. The active structural top five therefore use `peer_membrane` inhibition only in the stem. The stronger winner gate remains a reusable component but is not part of the current contenders.

## Open: structural-cost trade-off

The active six-class DSEC/ASIC target is `EventSpikeSeg140k`: 149,835 registered
parameters, 149,423 executed inference parameters, 25 permanent PLIF actors, and one
temporal class-current readout. The prior 11-class export is historical only.
Parameter count is only a proxy for ASIC logic cost; the dominant constraint is persistent
membrane/adaptation traffic, followed by pointwise mixing, event routing, FIFO
pressure, and inhibition/adaptation arithmetic.

### Logical-state footprint is much larger than parameter memory

At native 440x640, v8 owns **30,976,000** membrane states. Threshold adaptation adds
age/amplitude on **10,982,400** neurons. Because the current DSEC training path uses touched-neuron lazy updates, exact runtime needs a compact 24-bit `last_bin_tag` for every live sparse state. A hypothetical dense exact representation is about **189.60 MiB** before queues/alignment. The full ASIC therefore requires characterized actor-local SRAM macros; a sparse implementation is valid only if full-sequence measurements establish a lossless bound.

## Open: continuous learned neuron parameters

PLIF beta, base threshold, inhibition strength, threshold-adaptation strength, and adaptation duration are learned numerical training variables. ASIC deployment requires frozen fixed-point formats, deterministic rounding/saturation, and integer-reference regression. The baseline preserves quantized per-channel beta; shift-only/power-of-two leakage is an optional optimization that requires accuracy revalidation.


## Open: native-resolution CPU stream-training cost

Each 50 ms record executes ten internal clock updates. Training truncates BPTT at record boundaries while retaining numeric PLIF state, so memory no longer grows across the entire recording. CPU runtime remains substantial because dense software convolutions execute for every internal clock; parameter count alone does not predict this cost.

Resolved on 2026-08-15: continuous state initially detached the project membrane
but left SpikingJelly `ParametricLIFNode.v` attached to the completed autograd graph.
The internal `v`/`w` references are now detached after each record, preventing the
previous record graph from overlapping the next forward pass.


## 2026-08-09 — Native-resolution training memory root cause

Native-resolution batch-1 training exposed an avoidable full-resolution temporal-state cost on top of intrinsic T=15 BPTT. The final model now keeps triangular threshold adaptation off on the stem/x1/detail path and enables it from x2 onward, where spatial state is 4× smaller. Stateless convolution plus affine current transforms are vectorized over the combined T×N batch dimension while PLIF/LIF updates remain sequential, preserving identical temporal dynamics and gradients. Training returns scalar activity-rate diagnostics instead of retaining complete hidden TNCHW spike sequences solely for regularization.


## Resolved: fake temporal axis from repeated static input

**Status:** resolved in code on 2026-08-14.

Previously one six-channel sample was repeated or adjacent files were stacked as a synthetic `T` axis. The timestamp-stream loader forbids both. Internal clock updates now come from timestamp scheduling inside one physical interval, while stream continuity comes from retained PLIF state between records.

## Open: installed training event tensors are incomplete

**Status:** dataset installation issue detected automatically.

The installed `events/train` folder has 2,887 NumPy tensors while `labels/train` has 10,001 indexed masks. Only `rec1487339175_export` is represented in the active event manifest. This loss of recording diversity is a likely accuracy limiter and must be fixed at the dataset installation level; the loader reports the mismatch explicitly.


## Full-chip ASIC integration still incomplete

Native SystemVerilog now covers channel-aware standard/grouped/depthwise kernel scatter, actor-local current/membrane/tag storage, exact PLIF commit, completion/spike backpressure, inhibition, adaptation, class-current/argmax primitives, lossless two-way event/token fanout, fixed concat channel remap, nearest-neighbor 2x event expansion, same-bin completion rendezvous, and a correctness-reference residual binary-OR/dedup join. The Python exporter now owns an explicit v8 **non-linear DAG** contract; the 25-actor list is only a deterministic topological/export order.

The active six-class trained-v4 generated channelized convolution/PLIF graph now includes all 25 actors, exact static routes, grouped retinotopic mechanism commits, 143,824 exported synaptic weights, and the temporal readout. A manifest-driven sparse integer oracle emits model-scale golden currents, membranes, spikes, and semantic output. The reduced 8x8 real-checkpoint RTL replay now matches all actor spikes/completions and the final output, but this is functional evidence only. Native 440x640 dataset-derived full-sequence traffic, characterized SRAM macro substitution, native residual occupancy measurement, and routed activity-based PPA remain open. Do not report real-time or power results until those paths are measured.

The production temporal readout now crosses a 281,600 x 144-bit 1R1W SRAM boundary and is
bit-exact in full-DAG replay. Its single-bank dense flush blocks final-actor traffic for
844,800 clocks per frame (8.448 ms at 100 MHz), so a native traffic study must prove upstream
FIFO capacity or justify a later ping-pong score-bank variant. This cost is explicit and is
not included in a power or real-time claim yet.

All nine generated residual joins now use direct-indexed seen-map SRAM plus compact linear-address
queue SRAM. The statically lossless native default occupies 30.078 MiB in the worst case and has
a 2,252,800-clock parallel reset scrub. The reduced replay's `RESIDUAL_MAX_EVENTS=512` override is
only a verified fixture bound. Reducing native storage requires maximum per-bin occupancy data from
complete DSEC sequences; overflow, eviction, or probabilistic deduplication remains prohibited.

Nine non-mechanism PLIF populations now use packed actor-owned 1R1W state SRAM plus first-touch
address-queue SRAM and are whole-DAG bit-exact. Their conservative full-address queues contribute
to a 186.276 MiB allocation and the largest parallel reset scrub takes 4,505,600 clocks. This is
correctness-first sizing, not a final area claim. The sixteen inhibition/adaptation populations
now also use actor-owned channel-lane SRAM transactions and are whole-DAG bit-exact. Their 65-bit
PLIF state lanes are universal, while 32-bit adaptation lanes exist only in the fifteen actors
that enable adaptation. Their current conservative banks total 144.841 MiB; characterized banking
remains physical optimization work.

Yosys 0.23 crashes internally when identical explicit `plif_leak_charge` parameter overrides are
derived repeatedly inside a generated channel-lane loop. The production widths already equal the
module defaults, so the redundant overrides were removed; two-lane synthesis and RTL behavior pass.
This is an EDA frontend workaround, not an arithmetic or model change.

The exact conservative SRAM manifest totals 366.030 MiB before compiler tiling overhead. This is
far larger than the 0.137 MiB int8 weight ROM because the frozen native-resolution DAG owns
30,976,000 logical neuron states plus lossless first-touch and residual queues. A cheap single-die
implementation is not currently substantiated. Reducing capacity requires complete native DSEC
occupancy evidence and a lossless safety policy; changing resolution/state precision or allowing
external state memory is a model/hardware contract change requiring explicit approval.
