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

## Logical resident-state accounting rule

Do not infer neuron-state capacity from parameter count. The 25-population 140k graph has
30,976,000 logical accumulator/membrane identities and 10,982,400 adaptation-enabled states at DSEC
`440x640`. Every logical PLIF owns one signed int32 Q15.16 combined accumulator/state element. During a
bin it contains the pre-leaked membrane plus accepted current; completion thresholds/resets it and
pre-applies beta for the next bin. Static weights use signed Q7.16 in 24 bits, membrane and
threshold use signed Q7.16 in 24 bits, and beta uses unsigned UQ1.23. Enabled adaptation stores a
6-bit integer-bin age and a 19-bit unsigned Q3.16 amplitude. This is 150.89 MiB-equivalent of
logical state, but it is
distributed register/latch state rather than an addressed byte store. There is no last-bin tag,
touched queue, SRAM fetch, or writeback. Full-chip PPA must measure this resident design.

Each actor owns resident local state across its spatial/channel destinations and may
not lend that state or compute identity to another layer. It must never alias logical
membrane identities from different channels, positions, or layers. The combined element becomes
the pre-leaked state for the next bin at commit; combined accumulator/adaptation state survives
events and consecutive records until the
documented reset boundary.

## Digital neuromorphic ASIC deployment rule

The primary runtime is fully digital but must preserve neuromorphic/SNN execution:

- PLIF combined accumulator and adaptation state persist in local fixed-point elements;
- hidden binary spike pulse/vector bits gate compile-time fixed weights;
- convolution remains fixed local synaptic connectivity and skips unasserted inputs;
- elastic pulse/vector routing carries only emitted binary activity between stages;
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
Every logical spatial PLIF owns one physical register/latch combined accumulator element; enabled
adaptation fields are local to that PLIF. This direct-state rule is intentional.

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

For a 3x3 convolution, the nine tap connections gate their compile-time signed weights from
asserted presynaptic pulse bits into the canonical postsynaptic current element. A tap is a
synapse projection, not a separate PLIF and not a membrane copy. Stride is fixed connectivity,
not a dense sliding scan.

### Natural mappings

- Conv weights -> compile-time signed fixed-point constants/wires
- binary hidden spikes -> pulse/vector bits that gate weight additions
- PLIF beta -> quantized per-channel leak coefficient
- learned threshold -> quantized per-channel comparator threshold
- combined accumulator/compact adaptation -> register/latch-resident per-PLIF state
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
- every resident PLIF receives exactly one learned-beta update at each 5 ms completion, so no
  microsecond timestamp or `last_bin_tag` is stored.

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
not tapeout signoff. Full-chip PPA is invalid until the complete native resident graph—not a
reduced actor or superseded SRAM reference—is placed, routed, timed, and activity measured.


## Autonomous 5 ms DSEC runtime rule

Live DSEC input retains 5 ms semantic epochs. Events and ordered completion tokens propagate through the complete permanent **25-PLIF DAG** without a global actor scheduler. The input stream forks to `detail_stem` and `stem`; `x1` and `x2` each fan out into deeper encoder and later decoder routes. Residual joins binary-OR/deduplicate coincident pulse bits, whereas the `project2+x1` decoder merge must preserve multiplicity. Every multi-input join waits for all same-bin completion tokens before forwarding completion. PLIF/adaptation state persists across epochs and predictions. Every resident PLIF applies one learned-beta step per completion; there is no touched-state tag. All contributions to a layer/bin accumulate before one threshold/reset commit.

Prediction cadence is configurable, with **10 bins = 50 ms = 20 Hz** as the starting point to match training. Measure cycles/bin after implementation. Define `U = C_bin/(f_clk*0.005)` and `H = 1/U`. Hard sustained real time requires `U<=1` / `H>=1`; the starting design target is `U<=0.8` / `H>=1.25`. At 100 MHz this means 500,000 hard cycles/bin and 400,000 target cycles/bin.

## Active autonomous RTL interfaces

`resident_convolution_synapses` implements fixed standard/grouped/depthwise connectivity in
PyTorch Conv2d weight order. `streaming_resident_channelized_plif_actor` connects bitmap pulse
traffic to ordinary or retinotopic resident populations. `resident_event_ingress_adapter`
preserves raw-event multiplicity for the two ingress actors. Resident vector offset, upsample,
union, edge, fork, and join primitives implement the fixed DAG, and
`resident_temporal_class_readout` holds signed class currents locally. Older scalar scatter,
banked, and SRAM actors are temporary equivalence references pending resident graph equivalence.

## Active fixed-step RTL interfaces

The resident baseline has no sparse-state entry, state address, or timestamp. Each PLIF consumes
its exported learned per-channel beta once per 5 ms completion. Do not reintroduce a fixed-record
25-layer controller: runtime is the autonomous static DAG with ordered completion-token
rendezvous. The final 16->6 resident readout uses signed current accumulation across the configured
prediction window plus first-index-tie argmax; do not create output PLIFs or class-spike counting.
