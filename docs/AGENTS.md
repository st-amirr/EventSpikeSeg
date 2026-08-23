# EventSpikeSeg Agent Instructions

## Mission

Build and validate only `EventSpikeSeg140k` for 11-class DSEC at `241x351`, then map its
spike-native PLIF inference graph to a custom static digital-neuromorphic accelerator.
Training remains PyTorch + SpikingJelly; deployment targets VHDL-2008 on the conventional
Digilent Nexys Video XC7A200T
with fixed-point PLIF state, sparse event routing, and activity-aware execution.

## Source-of-truth order

1. `project_spec.yaml`
2. `AGENTS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DECISIONS.md`
5. tests and executable code

Python constructors/forward methods remain authoritative if older diagrams disagree.

## Canonical naming and frozen graph

- `EventSpikeSeg140k`: the only FPGA target; 140,589 registered parameters for
  11-class, two-polarity DSEC.
- `EventSpikeSegXL`: software-only comparison; FPGA export must reject it.
- Deployable 140k inference: 134,807 executed parameters, 127,456 convolution weights,
  and 37 executed Conv/ChannelAffine/PLIF populations.
- Omit dead `refine2`, training-only `aux_head`, surrogate gradients, and all XL modules.

## Exact inference semantics

A learned `SpikingStage` is `SpikingJelly Conv2d (synapses) -> optional ChannelAffine ->
ParametricLIF -> binary spikes`. Convolution kernels are synaptic weights; the output
feature-map elements are PLIF neurons. DW/PW blocks contain two distinct PLIF
populations and must not be collapsed.

Hardware deployment implements the frozen executed 140k inference graph only.

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

Do not infer neuron-state memory from parameter count. The 37-population 140k graph has
72,843,333 logical membrane states and 14,023,680 adaptation-enabled states at DSEC
`241x351`. With the baseline 16-bit membrane and two 16-bit adaptation fields where enabled, dense persistent state is about 192.44 MiB before queues/counters. The fixed 5 ms baseline does not require one 32-bit timestamp per membrane. XC7A200T BRAM is 1.604 MiB, about 120 times too small for the dense state.
External memory, including the board's DDR3, is forbidden. A lossless sparse live-state
table is the only remaining possible mapping and must pass a measured worst-case bound;
overflow eviction or state loss is forbidden.

Each actor may sequence its own lanes across spatial/channel destinations, but may not
lend those lanes to another layer. It must never alias logical membrane addresses from
different channels, positions, or layers. Current accumulators are temporary;
persistent membrane/adaptation state survives events and consecutive records until the
documented reset boundary.

## Digital neuromorphic FPGA deployment rule

The primary runtime is fully digital but must preserve neuromorphic/SNN execution:

- PLIF membrane and adaptation state persist in fixed-point memory;
- hidden binary spikes are represented as events/addresses and trigger shared-weight
  additions rather than dense multiply-by-zero work;
- convolution remains shared local synaptic connectivity;
- event FIFOs/address logic route only emitted spikes between stages;
- clock-enable/inactivity suppression should be used where safe;
- CPU/GPU dense inference is absent from the deployed learned feature path.

### Static actor execution rule

Instantiate one permanent actor for each of the 37 executed populations. Each actor owns
its convolution address generator, accumulator lanes, PLIF/mechanism unit, output FIFO,
and initialized local weight ROM. Cross-layer compute sharing, layer reconfiguration,
and partial reconfiguration are forbidden. Common clock/reset, timestamp dispatch,
on-chip state banks, and final readout may be shared infrastructure. Logical spatial states are
still stored, not implemented as one physical register/neuron each.

### Exact sparse execution order

DSEC FPGA inference is fixed-time and must match training. One 50 ms semantic record is represented by ten chronological 5 ms slices. Do not implement direct raw-event end-to-end asynchronous propagation as the baseline. Within each 5 ms slice, sparse spike addresses may drive only the connected synaptic additions, but PLIF state advances under an explicit 5 ms step boundary. The preferred hardware schedule is layer-major over the full T=10 record: process t0..t9 for one layer/tile while its state is resident, then pass the ten output spike slices to the next layer.

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
- final selector is a local retinotopic binary gate after a 96->96 PLIF projection;
- DSEC PLIF decay advances in fixed 5 ms steps, with 5 ms as the
  learned-beta reference interval;
- per-membrane timestamps are not required in the baseline; lazy tagged updates are optional only after equivalence proof.

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
4. Vivado XC7A200T synthesis + place-and-route + post-implementation timing simulation
5. representative-event SAIF/VCD power analysis
6. optional instrumented Nexys Video measurement

Compare layer currents, membrane trajectories, spikes, output spike counts, semantic
accuracy, cycle counts, and overflow/saturation behavior. Post-route timing and Vivado
power are estimates and must be labeled as such; only instrumented board results may be
called measured FPGA power/latency.


## 50 ms DSEC runtime rule

Treat each 50 ms DSEC record as one hardware scheduling transaction containing exactly ten 5 ms SNN steps. Preserve chronological step order and persistent PLIF/adaptation state. It is legal and preferred to process all ten steps of one layer (or one spatial state tile) before moving to the next feed-forward layer, because this matches multi-step SpikingJelly semantics. Never collapse ten steps into one, never threshold/reset once per raw camera event, and never claim the baseline is asynchronous.
