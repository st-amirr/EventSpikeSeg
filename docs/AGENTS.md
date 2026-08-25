# EventSpikeSeg Agent Instructions

## Mission

Build and validate only `EventSpikeSeg140k` for 11-class DSEC at native `440x640`, then map its
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

- `EventSpikeSeg140k`: the only ASIC target; 150,245 registered parameters for
  11-class, two-polarity DSEC.
- `EventSpikeSegXL`: software-only comparison; ASIC export must reject it.
- Deployable 140k inference: 149,503 executed parameters, 143,904 synaptic weights,
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

Instantiate one permanent actor for each of the 25 executed PLIF populations. Each actor owns
its convolution address generator, accumulator lanes, PLIF/mechanism unit, output FIFO,
and initialized local weight ROM. Cross-layer compute sharing, layer reconfiguration,
and partial reconfiguration are forbidden. Common clock/reset, fixed-slice input dispatch,
on-chip state banks, and final readout may be shared infrastructure. Logical spatial states are
still stored, not implemented as one physical register/neuron each.

### Exact autonomous actor execution order

DSEC ASIC inference must match the trained fixed 5 ms time grid while streaming live input.
Within a bin, actors run autonomously using ready/valid spike traffic. An ordered completion
token follows the final presynaptic event; it causes the receiving actor to update each
touched PLIF exactly once and then forward completion. This is logically asynchronous
actor dataflow, but the current RTL is clocked and makes no electrically clockless/QDI claim.
Never threshold after each signed tap contribution.

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
- final readout is a 16->11 signed current accumulator over all ten updates;
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
not tapeout signoff. Full-chip PPA is invalid until state arrays use characterized SRAM
macros; standard-cell-expanded memory must never be reported as the implementation.


## Autonomous 5 ms DSEC runtime rule

Live DSEC input retains 5 ms semantic epochs. Events and an ordered completion token propagate through the complete permanent 25-PLIF graph without a global actor scheduler. PLIF/adaptation state persists across epochs and predictions. Each touched state stores a 24-bit last-bin tag; `delta_bins` controls the exact repeated learned-beta leak before current integration. All contributions to one destination for a layer/epoch must be accumulated before one threshold/reset commit.

Prediction cadence is configurable, with **10 bins = 50 ms = 20 Hz** as the starting point to match training. Measure cycles/bin after implementation. Define `U = C_bin/(f_clk*0.005)` and `H = 1/U`. Hard sustained real time requires `U<=1` / `H>=1`; the starting design target is `U<=0.8` / `H>=1.25`. At 100 MHz this means 500,000 hard cycles/bin and 400,000 target cycles/bin.

## Active autonomous RTL interfaces

`presynaptic_tap_array` generates every valid nonzero kernel contribution in parallel for one channel plane. `convolution_plif_actor` serializes those contributions into the canonical actor-local destination array. `asynchronous_plif_actor` accumulates repeated destinations into one current entry, records first touches, and on completion walks only that queue through `plif_update`; spike and completion outputs are independently backpressured. The current behavioral state arrays are an equivalence prototype and must become actor-local SRAM macros. The final 16->11 readout remains non-spiking.

## Active fixed-step RTL interfaces

The baseline sparse-state entry contains address/tag, membrane, and adaptation age/amplitude only where enabled. It must not contain `last_timestamp_us`. `plif_update` consumes the exported learned per-channel beta directly once per 5 ms step. Any fixed-record compatibility controller uses 25 layers x 10 steps. The final 16->11 readout is stateless between records and uses signed current accumulation plus first-index-tie argmax; do not recreate output PLIF neurons or class-spike counting.
