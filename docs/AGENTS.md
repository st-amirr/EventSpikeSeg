# EventSpikeSeg Agent Instructions

## Mission

Build and validate only `EventSpikeSeg140k` for six-class DSEC at native `440x640`, then map its
spike-native PLIF inference graph to a custom static digital-neuromorphic accelerator.
Training remains PyTorch + SpikingJelly; deployment is a custom ASIC described directly in
synthesizable SystemVerilog, with Icarus/cocotb and Yosys/OpenROAD as the open verification
and PPA path.

## Source-of-truth order

1. `project_spec.yaml`
2. `AGENTS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DECISIONS.md`
5. tests and executable code

Python constructors/forward methods remain authoritative if older diagrams disagree.

## Canonical naming and frozen graph

- `EventSpikeSeg140k`: the only ASIC target; 149,835 registered parameters for
  six-class, two-polarity DSEC.
- `EventSpikeSegXL`: software-only comparison; ASIC export must reject it.
- Deployable 140k inference: 149,423 executed parameters, 143,824 synaptic weights,
  25 Conv/ChannelAffine/PLIF populations, and one temporal class-current readout.
- Omit dead `refine2`, training-only `aux_head`/`boundary_head`, surrogate gradients,
  and all XL modules.

## Exact inference semantics

A learned `SpikingStage` is `SpikingJelly Conv2d (synapses) -> optional ChannelAffine ->
ParametricLIF -> binary spikes`. Convolution kernels are synaptic weights; the output
feature-map elements are PLIF neurons. DW/PW blocks contain two distinct PLIF
populations and must not be collapsed.

Hardware deployment implements the frozen executed 140k inference graph only. Hidden
layers are binary-spiking; the final 1x1 synapse accumulates continuous signed class
current over the ten updates and does not allocate class PLIF state.

## PLIF digital ASIC mapping contract

Per output channel, `beta=sigmoid(beta_logit)` and threshold are learned. Spatial
neurons keep individual membrane state. Software charge is equivalent to
`candidate = beta * membrane + current` before dynamic threshold/reset effects.

ASIC values are fixed-point numerical SNN states, not physical volts/amps. Freeze the
weight, beta, threshold, membrane, accumulator, adaptation, rounding, saturation, and
overflow formats in the integer export contract. The baseline must preserve the learned
per-channel beta with a quantized coefficient. Shift-only/power-of-two leak is an
optional optimization only after bit-exact and semantic-accuracy revalidation.

## Logical state accounting rule

Do not infer neuron-state memory from parameter count. The 25-population 140k graph has
30,976,000 logical membrane states and 10,982,400 adaptation-enabled states at DSEC
`440x640`. With int16 membrane, two int16 adaptation fields where enabled, and the compact 24-bit last-bin tag required by the trained touched-neuron runtime, a hypothetical dense exact state is about 189.60 MiB before queues/counters. No microsecond timestamp is used. Actor ownership eliminates cross-layer fetching but not this capacity. Full-chip PPA therefore requires characterized local SRAM macros; a lossless sparse live-state SRAM is allowed only after measured worst-case occupancy proves its bound. Overflow eviction or state loss is forbidden.

Each actor owns direct-indexed local state across its spatial/channel destinations and may
not lend that state or compute identity to another layer. It must never alias logical
membrane addresses from different channels, positions, or layers. Current accumulators are temporary;
persistent membrane/adaptation state survives events and consecutive records until the
documented reset boundary.

## Digital neuromorphic ASIC deployment rule

The primary runtime is fully digital but must preserve neuromorphic/SNN execution:

- PLIF membrane and adaptation state persist in fixed-point memory;
- hidden binary spikes are represented as events/addresses and trigger shared-weight
  additions rather than dense multiply-by-zero work;
- convolution remains shared local synaptic connectivity;
- event FIFOs/address logic route only emitted spikes between stages;
- clock-enable/inactivity suppression should be used where safe;
- CPU/GPU dense inference is absent from the deployed learned feature path.

### Static actor execution rule

Instantiate one permanent actor for each of the 25 executed PLIF populations. **These actors
form the exact EventSpikeSeg140k v8 DAG; the actor tuple is only a topological export order,
not a linear actor0->actor24 pipeline.** Each actor owns its convolution address generator,
accumulator lanes, PLIF/mechanism unit, output FIFO, and initialized local weight ROM.
Cross-layer compute sharing, layer reconfiguration, and partial reconfiguration are forbidden.
The interconnect is compile-time fixed: input/detail-semantic forks, residual binary-OR joins,
`x1`/`x2` skip fanout, decoder upsample/concat, multiplicity-preserving `project2+x1`, and
late semantic/detail concat. Common clock/reset and final readout may be shared infrastructure.
Logical spatial states are still stored, not implemented as one physical register/neuron each.

### Exact autonomous actor execution order

DSEC ASIC inference must match the trained fixed 5 ms time grid while streaming live input.
Raw rectified events enter sequentially in timestamp order and immediately cause only their
connected signed-weight additions; no dense tensor or complete 5 ms bin is loaded. Within
an epoch, actors run autonomously using ready/valid spike traffic. An ordered completion
token follows the final presynaptic event. Tokens follow the **same DAG as spikes**: fanout
nodes duplicate them to every branch, and residual/skip/concat joins may forward one
downstream token only after all required upstream tokens carry the same 24-bit bin tag.
Only then may the downstream actor know that every contribution for that bin has arrived.
This is logically asynchronous actor dataflow, but the current RTL is clocked and makes no
electrically clockless/QDI claim. Never threshold after each signed tap contribution.

For a 3x3 convolution, approximately nine parallel tap projection cells calculate valid
postsynaptic destinations and signed weights. They all feed the same canonical destination
current/membrane array. A tap is a synapse projection, not a separate PLIF and not a separate
membrane copy. Stride is output-address divisibility in the scatter equation; it is not a
dense sliding scan.

### Natural mappings

- Conv weights -> shared signed fixed-point weight tables
- binary hidden spikes -> event addresses that trigger weight additions
- PLIF beta -> quantized per-channel leak coefficient
- learned threshold -> quantized per-channel comparator threshold
- membrane/adaptation -> banked fixed-point state memory
- ChannelAffine -> fold into quantized weight/scale
- concat -> channel-ID routing
- nearest upsample -> spike-address fan-out
- quarter skip concat -> channel-ID routing into one 1x1 fusion accumulator
- half skip sum -> preserve coincident event multiplicity rather than OR-dedup
- class current accumulation/argmax -> signed accumulators/comparator

### Mapping risks requiring explicit validation

- stem peer-membrane inhibition uses retinotopic cross-channel membrane energy;
- encoder/context triangular threshold adaptation uses age/amplitude and a dynamic threshold;
- final readout is a 16->6 signed current accumulator over all ten updates;
- DSEC PLIF decay advances in fixed 5 ms steps, with 5 ms as the
  learned-beta reference interval;
- no microsecond timestamp is stored; every live sparse state carries a compact 24-bit `last_bin_tag`, and lazy `beta^delta_bins` is baseline behavior because training already uses touched-neuron updates.

Do not silently replace these. If hardware cannot reproduce them, define an explicit
hardware-compatible approximation and revalidate/fine-tune accuracy.

## Input contracts

DDD17 uses the 50 ms statistic scheduler and is an approximation because raw tuples are
unavailable. DSEC uses exact raw rectified events and bypasses the moment scheduler. GPU
training accumulates events into fixed physical-time divisions; the ASIC ingress accepts the
camera stream directly and does not store those training divisions as input bins.

## Verification

For the ASIC target, preserve this staged golden comparison:

1. SpikingJelly floating-point trained model
2. exported bit-exact fixed-point integer reference
3. SystemVerilog unit/full RTL simulation with Icarus and cocotb
4. Yosys synthesis and technology mapping
5. OpenROAD placement/routing, parasitic extraction, timing, and representative-event VCD/SAIF power
6. later test-silicon measurement

Compare layer currents, membrane trajectories, adaptation, hidden spikes, signed class-current accumulators, semantic
accuracy, latency, and overflow/saturation behavior. ASAP7 is predictive research PPA,
not tapeout signoff. Full-chip PPA is invalid until the implemented bank interfaces bind
characterized SRAM macros; standard-cell-expanded memory must never be reported as the implementation.


## Autonomous 5 ms DSEC runtime rule

Live DSEC input retains 5 ms semantic epochs. Events and ordered completion tokens propagate through the complete permanent **25-PLIF DAG** without a global actor scheduler. The input stream forks to `detail_stem` and `stem`; `x1` and `x2` each fan out into deeper encoder and later decoder routes. Residual joins binary-OR/deduplicate coincident addresses, whereas the `project2+x1` decoder merge must preserve multiplicity. Every multi-input join waits for all same-bin completion tokens before forwarding completion. PLIF/adaptation state persists across epochs and predictions. Each touched state stores a 24-bit last-bin tag; `delta_bins` controls the exact repeated learned-beta leak before current integration. All contributions to one destination for a layer/epoch must be accumulated before one threshold/reset commit.

Prediction cadence is configurable, with **10 bins = 50 ms = 20 Hz** as the starting point to match training. Measure cycles/bin after implementation. Define `U = C_bin/(f_clk*0.005)` and `H = 1/U`. Hard sustained real time requires `U<=1` / `H>=1`; the starting design target is `U<=0.8` / `H>=1.25`. At 100 MHz this means 500,000 hard cycles/bin and 400,000 target cycles/bin.

## Active autonomous RTL interfaces

`presynaptic_tap_array` generates every valid nonzero kernel contribution in parallel for one channel plane. `channelized_convolution_scatter` extends projection across legal standard/grouped/depthwise input/output channels in PyTorch Conv2d weight order. `streaming_channelized_plif_actor` connects packed ready/valid traffic to canonical `(output_channel,y,x)` state and compile-time per-channel beta/threshold tables. Mechanism-enabled layers select `retinotopic_asynchronous_plif_actor`, which commits all channels at one spatial location atomically through `retinotopic_mechanism_update`; ordinary layers use `asynchronous_plif_actor`. `event_fork2` provides lossless two-way event/token multicast, `event_join2` provides multiplicity-preserving same-bin rendezvous, `binary_event_union2` is the exact residual OR/dedup join, `event_channel_offset` performs concat remaps, and `event_upsample2x` performs nearest-neighbor address expansion. `scripts/generate_asic_top.py` instantiates the exact exported 25-actor DAG and `temporal_class_readout` implements the non-spiking 16->6 output. `actor_local_state_sram` is the technology-independent synchronous single-port 1RW macro boundary; read and write are mutually exclusive in one cycle. `initialized_actor_state_bank` partitions large logical storage into bounded banks, scrubs them in parallel, and blocks events until initialization completes. Actor state, queues/markers, temporal scores, and residual events use this boundary. Its behavioral branch is for equivalence only; full-chip PPA requires the generated macro switch and a characterized compiler binding.

## Active fixed-step RTL interfaces

The baseline sparse-state entry contains address/tag, membrane, and adaptation age/amplitude only where enabled. It must not contain `last_timestamp_us`. `plif_update` consumes the exported learned per-channel beta and repeats the fixed-point leak once for each elapsed 5 ms bin indicated by `delta_bins`. Do not reintroduce a fixed-record 25-layer controller: runtime is the autonomous static DAG with ordered completion-token rendezvous. The final 16->6 readout uses signed current accumulation across the configured prediction window plus first-index-tie argmax; do not recreate output PLIF neurons or class-spike counting.
