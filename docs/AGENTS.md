# EventSpikeSeg Agent Instructions

## Mission

Build and validate the canonical `EventSpikeSeg140k` (~140k registered parameters for the
six-class DDD17 configuration), then map its spike-native PLIF inference graph to a
**custom digital neuromorphic FPGA accelerator**. Training remains PyTorch + SpikingJelly;
the deployment target is VHDL-2008 on ZCU104 with fixed-point PLIF state, sparse
event/spike routing, shared-kernel synaptic additions, and activity-aware execution.

## Source-of-truth order

1. `project_spec.yaml`
2. `AGENTS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DECISIONS.md`
5. tests and executable code

Python constructors/forward methods remain authoritative if older diagrams disagree.

## Canonical naming

- `EventSpikeSeg140k`: canonical ~140k topology; all new work uses this name.
- `EventSpikeSegXL`: 236,445-parameter expanded comparison only.

Do not re-promote XL without an explicit new decision.

## Exact inference semantics

A learned `SpikingStage` is `SpikingJelly Conv2d (synapses) -> optional ChannelAffine ->
ParametricLIF -> binary spikes`. Convolution kernels are synaptic weights; the output
feature-map elements are PLIF neurons. DW/PW blocks contain two distinct PLIF
populations and must not be collapsed.

Canonical six-class accounting:

- registered parameters: 140,089
- executed training-forward parameters: 135,033
- executed inference-forward parameters: 134,637
- registered-but-dead `refine2`: 5,056 parameters / 2 SpikingStage populations
- training-only auxiliary head: 396 parameters
- executed inference SpikingStage populations: 37

Hardware deployment implements the executed inference graph only.

## PLIF digital FPGA mapping contract

Per output channel, `beta=sigmoid(beta_logit)` and threshold are learned. Spatial
neurons keep individual membrane state. Software charge is equivalent to
`candidate = beta * membrane + current` before dynamic threshold/reset effects.

FPGA values are fixed-point numerical SNN states, not physical volts/amps. Freeze the
weight, beta, threshold, membrane, accumulator, adaptation, rounding, saturation, and
overflow formats in the integer export contract. The baseline must preserve the learned
per-channel beta with a quantized coefficient. Shift-only/power-of-two leak is an
optional optimization only after bit-exact and semantic-accuracy revalidation.

## Logical state accounting rule

Do not infer neuron-state memory from the ~140k parameter count. For the six-class
canonical graph, the 37 executed PLIF populations require
`N_mem = 678*H*W + 480*H2*W2 + 1280*H4*W4`, where `H2/W2=ceil(H/W over 2)` and
`H4/W4=ceil(H2/W2 over 2)`. At `212x282`, this is **52,524,272 independent membrane
states**. The general class-count form is `(672+Nclass)*H*W + 480*H2*W2 +
1280*H4*W4`.

fLong-enabled layers contain `352*H2*W2 + 1216*H4*W4` logical neurons: **9,836,800**
at 212x282. Each carries separate adaptation age and adaptation amplitude. `beta` and
base threshold are per-channel shared parameters; convolution weights are spatially
shared; membrane and fLong state are per `(layer,c,y,x)`.

Hardware may reuse a small number of physical PLIF PEs, but **must never alias logical
membrane addresses from different channels, positions, or layers**. Current accumulators
are temporary per layer/timestep; persistent membrane/adaptation state survives timesteps
and consecutive records until the documented reset boundary.

## Digital neuromorphic FPGA deployment rule

The primary runtime is fully digital but must preserve neuromorphic/SNN execution:

- PLIF membrane and adaptation state persist in fixed-point memory;
- hidden binary spikes are represented as events/addresses and trigger shared-weight
  additions rather than dense multiply-by-zero work;
- convolution remains shared local synaptic connectivity;
- event FIFOs/address logic route only emitted spikes between stages;
- clock-enable/inactivity suppression should be used where safe;
- CPU/GPU dense inference is absent from the deployed learned feature path.

### Scalable execution rule

Do not instantiate one hardware PLIF datapath per logical `[C,H,W]` state. Prefer a
reusable coarse-grained digital synaptic-accumulator + PLIF tile, with logical
membrane/adaptation state stored in banked BRAM/URAM/LUTRAM. Reuse the tile across
spatial partitions, channels, and stages while preserving shared convolution kernels.
Start with exact full/tiled state execution; sparse touched-address/lazy-decay
optimizations come only after bit-exact equivalence is demonstrated.

### Exact sparse execution order

For each layer/timestep: accept sparse `(c,y,x)` spikes -> generate valid destination
addresses from kernel/stride/padding/dilation/groups -> accumulate fixed/shared weights
into temporary destination currents -> wait for the layer/timestep accumulation barrier ->
read each destination's own persistent state -> apply fixed-point PLIF/fInst/fLong/reset ->
write state back -> emit only firing addresses. Do **not** threshold/reset once per incoming
spike. The baseline must preserve the trained once-per-timestep neuron update.

The initial RTL may sweep every logical PLIF state at the neuron-update phase so beta leak
is exact even when no current arrived. Sparse touched-neuron/lazy-decay updates are later
optimizations after bit-exact equivalence, not the initial semantics.

### Natural mappings

- Conv weights -> shared signed fixed-point weight tables
- binary hidden spikes -> event addresses that trigger weight additions
- PLIF beta -> quantized per-channel leak coefficient
- learned threshold -> quantized per-channel comparator threshold
- membrane/adaptation -> banked fixed-point state memory
- ChannelAffine -> fold into quantized weight/scale
- concat -> channel-ID routing
- nearest upsample -> spike-address fan-out
- residual spike add/clamp -> event merge / OR-dedup
- class spike sum/argmax -> integer event counters/comparator

### Mapping risks requiring explicit validation

- stem `peer_membrane` fInst uses retinotopic cross-channel membrane energy;
- encoder/context triangular fLong uses adaptation age/amplitude and dynamic threshold;
- final selector uses a global spatial binary enable after a 96->96 PLIF projection.

Do not silently replace these. If hardware cannot reproduce them, define an explicit
hardware-compatible approximation and revalidate/fine-tune accuracy.

## Input contracts

DDD17 uses the 50 ms statistic scheduler and is an approximation because raw tuples are
unavailable. DSEC uses exact raw rectified events and bypasses the moment scheduler;
DSEC is therefore the cleaner direct event-stream FPGA deployment path.

## Verification

For the FPGA target, preserve this staged golden comparison:

1. SpikingJelly floating-point trained model
2. exported bit-exact fixed-point integer reference
3. VHDL unit/full RTL simulation
4. Vivado synthesis + place-and-route + post-implementation timing simulation
5. representative-event SAIF/VCD power analysis
6. optional instrumented ZCU104 measurement

Compare layer currents, membrane trajectories, spikes, output spike counts, semantic
accuracy, cycle counts, and overflow/saturation behavior. Post-route timing and Vivado
power are estimates and must be labeled as such; only instrumented board results may be
called measured FPGA power/latency.

