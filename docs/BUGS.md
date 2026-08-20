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

## Resolved: whole-feature-map binary homeostasis

The old `amax` activity rule treated one spike like dense activity and could raise an entire feature-map threshold. The active mechanism uses local triangular threshold adaptation driven by retinotopic membrane energy instead.

## Resolved: hidden hard winner gating in the active top five

The completed mechanism screen showed `winner_peer` inhibition starving the encoder: spike rates fell to approximately `0.0474 → 0.00306 → 0.000149` across enc1/enc2/enc3. The active structural top five therefore use `peer_membrane` inhibition only in the stem. The stronger winner gate remains a reusable component but is not part of the current contenders.

## Open: structural-cost trade-off

The historical structural contenders span approximately 21k to 107k trainable parameters. The canonical `EventSpikeSeg140k` model is the ~140k topology: 140,089 registered trainable parameters for DDD17, of which 134,637 participate in the deployed inference forward graph. The larger 236,445-parameter expansion is retained as `EventSpikeSegXL`. Parameter count is only a proxy for FPGA implementation cost. The dominant hardware constraints include pointwise width, persistent membrane/adaptation state, event-address generation, shared-weight bandwidth, BRAM/URAM banking, line/tile buffering, FIFO pressure, and the arithmetic cost of learned beta/fInst/fLong dynamics.

### Logical-state footprint is much larger than parameter memory

For six-class DDD17, the executed graph owns `678*H*W + 480*H2*W2 + 1280*H4*W4`
independent membrane values. At 212x282 this is **52,524,272** membrane states, despite
only 134,637 active inference parameters. fLong adds age/amplitude state on **9,836,800**
logical neurons at that resolution. This is not a requirement for one physical neuron per
state: time-multiplexed PLIF PEs are allowed, but the memory system must preserve every
logical `(layer,c,y,x)` state separately. Incorrect state aliasing, clearing membrane at a
timestep boundary, or thresholding once per incoming spike instead of once after the full
timestep accumulation would change model semantics.

## Open: continuous learned neuron parameters

PLIF beta, base threshold, inhibition strength, threshold-adaptation strength, and adaptation duration are learned numerical training variables. For FPGA deployment they require frozen fixed-point formats, deterministic rounding/saturation, and integer-reference regression. The baseline preserves quantized per-channel beta; shift-only/power-of-two leakage is an optional optimization that requires accuracy revalidation.


## Open: native-resolution CPU stream-training cost

Each 50 ms record executes ten internal clock updates. Training truncates BPTT at record boundaries while retaining numeric PLIF state, so memory no longer grows across the entire recording. CPU runtime remains substantial because dense software convolutions execute for every internal clock; parameter count alone does not predict this cost.

Resolved on 2026-08-15: continuous state initially detached the project membrane
but left SpikingJelly `ParametricLIFNode.v` attached to the completed autograd graph.
The internal `v`/`w` references are now detached after each record, preventing the
previous record graph from overlapping the next forward pass.


## 2026-08-09 — Native-resolution training memory root cause

Native-resolution batch-1 training exposed an avoidable full-resolution temporal-state cost on top of intrinsic T=15 BPTT. The final model now keeps triangular fLong off on the stem/x1/detail path and enables it from x2 onward, where spatial state is 4× smaller. Stateless convolution plus affine current transforms are vectorized over the combined T×N batch dimension while PLIF/LIF updates remain sequential, preserving identical temporal dynamics and gradients. Training returns scalar activity-rate diagnostics instead of retaining complete hidden TNCHW spike sequences solely for regularization.


## Resolved: fake temporal axis from repeated static input

**Status:** resolved in code on 2026-08-14.

Previously one six-channel sample was repeated or adjacent files were stacked as a synthetic `T` axis. The timestamp-stream loader forbids both. Internal clock updates now come from timestamp scheduling inside one physical interval, while stream continuity comes from retained PLIF state between records.

## Open: installed training event tensors are incomplete

**Status:** dataset installation issue detected automatically.

The installed `events/train` folder has 2,887 NumPy tensors while `labels/train` has 10,001 indexed masks. Only `rec1487339175_export` is represented in the active event manifest. This loss of recording diversity is a likely accuracy limiter and must be fixed at the dataset installation level; the loader reports the mismatch explicitly.
