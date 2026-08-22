# EventSpikeSeg Agent Instructions

## Mission

Build and validate `EventSpikeSegXL` for 11-class DSEC at `241x351`, then map its
spike-native PLIF inference graph to a **custom digital neuromorphic FPGA accelerator**.
`EventSpikeSeg140k` remains the compact reference baseline. Training remains PyTorch +
SpikingJelly; deployment targets VHDL-2008 on ZCU104 with fixed-point PLIF state, sparse
event/spike routing, shared-kernel synaptic additions, and activity-aware execution.

## Source-of-truth order

1. `project_spec.yaml`
2. `AGENTS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DECISIONS.md`
5. tests and executable code

Python constructors/forward methods remain authoritative if older diagrams disagree.

## Canonical naming

- `EventSpikeSegXL`: active detailed DSEC/FPGA implementation target; 237,115 registered
  parameters for the 11-class configuration.
- `EventSpikeSeg140k`: compact reference/baseline; 140,089 registered parameters for
  six-class DDD17.

## Exact inference semantics

A learned `SpikingStage` is `SpikingJelly Conv2d (synapses) -> optional ChannelAffine ->
ParametricLIF -> binary spikes`. Convolution kernels are synaptic weights; the output
feature-map elements are PLIF neurons. DW/PW blocks contain two distinct PLIF
populations and must not be collapsed.

XL 11-class DSEC accounting:

- registered parameters: 237,115
- executed training-forward parameters: 232,059
- executed inference-forward parameters: 226,767
- registered-but-dead `refine2`: 5,056 parameters / 2 SpikingStage populations
- training-only heads: 726-parameter mid auxiliary + 4,566-parameter deep auxiliary
- executed inference SpikingStage populations: 50

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

Do not infer neuron-state memory from parameter count. XL's 50 inference PLIF populations
require `N_mem = (672+Nclass)*H*W + 768*H2*W2 + 2144*H4*W4`. At 11-class DSEC
`241x351`, `H2xW2=121x176` and `H4xW4=61x88`, giving **85,639,973 independent
membrane states**.

XL threshold-adaptation-enabled populations contain `416*H2*W2 + 2080*H4*W4` logical neurons:
**20,024,576** at 241x351. Each carries adaptation age and amplitude. Direct DSEC
execution also keeps one last-update timestamp per membrane state. With illustrative
16-bit membrane/age/amplitude and 32-bit timestamps, persistent state is about
**566.42 MiB** before output counters and buffering. The exact XL baseline therefore
requires external DDR plus an on-chip banked tile/cache unless later measured
quantization/compression proves an all-on-chip mapping.

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
membrane/adaptation/timestamp state stored in external DDR behind banked on-chip tile
caches. Use BRAM/URAM/LUTRAM for active tiles, queues, and small tables. Reuse the tile
across spatial partitions, channels, and stages while preserving shared convolution
kernels and deterministic timestamp-tagged branch joins.

### Exact sparse execution order

DSEC inference is asynchronous. For each timestamped `(polarity,y,x)` event, generate its
valid destinations, lazily decay each touched state from its own last-update timestamp,
add the shared synaptic weight, apply PLIF/inhibition/adaptation/reset, write the state and timestamp,
then immediately route emitted spikes to the next layer. There is no input bin, dense idle
state sweep, or global layer/timestep barrier.

DDD17 retains its historical fixed-step approximation because source event tuples are not
available. Its per-timestep accumulation barrier is not the DSEC/FPGA execution contract.

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

- stem peer-membrane inhibition uses retinotopic cross-channel membrane energy;
- encoder/context triangular threshold adaptation uses age/amplitude and a dynamic threshold;
- projected residual bridges join the strided 32->64 and 64->128 encoder paths;
- parallel d1/d2/d4 context requires deterministic timestamp-tagged branch joins;
- four-head Q/K/V attention uses 32 channels (8 per head) and requires a local
  timestamp/location rendezvous without a global frame barrier;
- final selector is a local retinotopic binary gate after a 96->96 PLIF projection;
- DSEC PLIF decay is a function of physical timestamp delta, with 5 ms as the
  learned-beta reference interval;
- touched state uses physical-time lazy decay in the asynchronous FPGA path.

Do not silently replace these. If hardware cannot reproduce them, define an explicit
hardware-compatible approximation and revalidate/fine-tune accuracy.

## Input contracts

DDD17 uses the 50 ms statistic scheduler and is an approximation because raw tuples are
unavailable. DSEC uses exact raw rectified events and bypasses the moment scheduler. GPU
training accumulates events into fixed physical-time divisions; the FPGA accepts the
camera stream directly and does not store those training divisions as input bins.

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
