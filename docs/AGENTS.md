# EventSpikeSeg Agent Instructions

## Analog synapse decision review — 2026-09-24

Use a signed charge-per-presynaptic-event interface on the active SKY130 prototype. Continue the existing pulse-duration injector as the first candidate; switched-capacitor charge injection is the conditional alternative, not a more inherently SNN-faithful implementation. Do not use pulse-density error feedback across semantic bins or future events. Weight determines a connection's contribution; it does not independently set presynaptic firing frequency. Internal subpulses are implementation phases, not extra network spikes, and must finish within the same update.

The primary analog reference is the best-validation full-float 140k seed-17 checkpoint from the 80-epoch run: `artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt`, epoch 58 / best epoch 58, `is_best=true`, SHA-256 `c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7`. The epoch-80 checkpoint is a comparison only (`is_best=false`). Verify metadata/hash before use. The analog path uses the checkpoint's ordinary float inference parameters; QAT, Q7.16 exports and quantized references are not needed and must not define analog precision or acceptance. Float32 storage does not require float32 analog accuracy.

At the update boundary, reproduce the model's signed weighted sum, learned beta, threshold/reset, inhibition and adaptation order. For this float PLIF, charge is `candidate = beta * previous_post_reset_state + summed_current`; apply beta once. Preserve the float path's subtractive reset, affine gain and any offsets, including when no presynaptic spike arrives. Hold uncommanded leak sufficiently small during accumulation and threshold only after all contributions arrive. Raw-event ingress may have multiplicity; do not reduce it to binary hidden-layer semantics.

The bin-based contract means finite pulse duration is not automatically less faithful than a capacitor packet: integrated signed charge and completion before the 5 ms boundary are decisive. Charge delivery, saturation, uncommanded droop and order effects must still be measured. Preserve all digital/XL artifacts and keep their campaigns stopped; no new Markdown files or full-model SPICE campaign.


## Full analog implementation delegation — 2026-09-23

The user authorizes the full analog/mixed-signal workflow, including design, debug, per-module simulation, physical macro generation, full assembly and ORFS execution once readiness passes. ASAP7 is not mandatory: evaluate another PDK where it is a better fit, and keep technology-specific comparisons clearly separated. `docs/ACTIVE_TASKS.md` is the authoritative staged task plan. Earlier Grok-test-only and blanket no-ORFS instructions are superseded. Keep digital/XL jobs paused and all artifacts preserved. Use existing docs and YAML only. Approximate research estimates are allowed with explicit evidence/coverage; full layout still requires real implemented macros and validated assembly.


## Active approach override — 2026-09-23

User authorized analog/mixed-signal 140k feasibility as the active approach. Follow docs/ARCHITECTURE.md and write outputs to artifacts/analog_asic. Digital-only/register-state rules below now describe the preserved digital fallback, not restrictions on this analog experiment. Analog approximations and scaled estimates are allowed with explicit limitations; distinguish ideal, schematic, extracted and full-chip evidence. Preserve all digital/XL artifacts and keep their jobs paused. Prior active work is in docs/PROGRESS.md.


## Mission

## Preserved digital fallback target policy — 2026-09-21

The epoch-80 target statement below is the preserved digital ASIC baseline. The active analog experiment uses the best-validation epoch-58 full-float checkpoint specified above and in `docs/ACTIVE_TASKS.md`; do not apply the digital QAT/quantization contracts below to analog design or acceptance.

All primary ASIC layout, block simulation, power, area, timing, and inventory work is based on **EventSpikeSeg140k v8, epoch 80, seed 17**: six classes, 440x640, 25 permanent PLIF actors, 54 graph edges, 30,976,000 resident PLIF identities, and 143,824 deployed synaptic weights. Primary exports/results live under `artifacts/ASIC/`; the latest accepted small gate-simulation results are in `artifacts/ASIC/primitive_characterization/`.

**EventSpikeSegXL is secondary/reference work.** Preserve useful accepted XL GDS/LEF/Liberty views, final routed ODB/DEF/netlist/SDC/SPEF files, checkpoint-specific constants, hierarchy catalogs/instance maps/preflight, and validation/power reports. Keep them under `artifacts/ASIC_XL/` and their existing named OpenROAD result directories. Retain the latest useful unfinished-run database and failure summaries; redundant intermediate databases and rebuildable simulation binaries need not be retained. Never relabel XL measurements or its 44-actor inventory as 140k results. Reuse an XL physical view for 140k only after proving matching RTL, constants, geometry, interfaces and constraints.

XL physical expansion remains paused behind 140k work. Preserve independent XL training and checkpoints. Neither model has a completed full-chip layout; existing routed blocks and structural hierarchy data must be labeled accordingly. Current work uses small per-block simulations and extracted-layout measurements; whole-model simulation remains retired. Historical entries below retain their original model and date and do not change this priority.


Build and validate `EventSpikeSeg140k` for six-class DSEC at `440x640` as the primary
custom digital-neuromorphic ASIC target. Keep the eleven-class `EventSpikeSegXL`
model and its useful physical implementation evidence for secondary work.
Training remains PyTorch + SpikingJelly; deployment is a custom ASIC described directly in
synthesizable SystemVerilog, with Icarus/cocotb and Yosys/OpenROAD as the open verification
and PPA path.

## Source-of-truth order

1. `project_spec.yaml`
2. `AGENTS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DECISIONS.md`
5. tests and executable code

For operational state and task handoff, read `docs/ACTIVE_TASKS.md` after the sources
above, then inspect `docs/PROGRESS.md` and the referenced machine-readable status files.
Update `docs/ACTIVE_TASKS.md` whenever a long-running process starts, completes, fails,
or changes the next valid stage. Do not infer active work from container names alone.

Python constructors/forward methods remain authoritative if older diagrams disagree.

## Canonical naming and frozen graph

- `EventSpikeSeg140k`: validated baseline ASIC target; 149,835 registered parameters for
  six-class, two-polarity DSEC.
- `EventSpikeSegXL`: second ASIC target; 979,179 registered parameters for eleven-class,
  two-polarity DSEC. Epoch 1 is a structural/constants bring-up checkpoint, not a final
  accuracy checkpoint; regenerate its constants from the selected trained/QAT checkpoint.
- Deployable 140k inference: 149,423 executed parameters, 143,824 synaptic weights,
  25 Conv/ChannelAffine/PLIF populations, and one temporal class-current readout.
- The 140k export omits dead `refine2`, training-only `aux_head`/`boundary_head`,
  surrogate gradients, and XL-only modules.
- XL deployable inference has 968,831 executed parameters, 959,824 convolution weights,
  44 PLIF populations, four learned attention thresholds, and one 24-to-11 current readout.
  Omit `aux_head`, `deep_aux_head`, and surrogate-gradient-only behavior.

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

ASIC values are fixed-point numerical SNN states, not physical volts/amps. Both targets use
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
The 44-population XL graph has 78,707,200 logical membranes and 15,910,400
adaptation-enabled states, totaling 347.66 MiB-equivalent under the same widths.

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

Instantiate one permanent actor for every executed PLIF population (25 for 140k, 44 for XL).
**Each actor tuple is only a topological export order, never a linear pipeline.** Each actor owns its convolution address generator,
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
- final readout is 16->6 for 140k and 24->11 for XL, using signed current accumulation over all ten updates;
- XL attention is fully spiking: four eight-channel Q/K coincidence popcounts compare
  exported Q7.16 thresholds, gate V spikes, and feed a spiking 1x1 output actor plus residual OR;
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

## Secondary XL physical estimation and artifact preservation

Keep XL checkpoint-specific exports below
`artifacts/ASIC_XL/checkpoint_exports/<checkpoint-purpose>/`; do not create new
top-level `artifacts/ASIC_XL_*` siblings. Preserve differing checkpoint constants
as separate exports rather than merging or deleting them.

The retained secondary XL physical hierarchy retains logical 8x8 grouping but uses 1x1
physical leaves for every actor because 8x8 and 4x4 exceeded 20 GiB during mapping
and 2x2 exceeded 20 GiB during detailed routing. Regenerate the catalog, instance
map, wrappers, macroized top, and preflight together after any partition change.

For early feasibility, characterize one routed, activity-measured physical instance
of each block class and write results below the target's
`primitive_characterization/` directory. Scale only with the exact physical-instance
inventory and report measured coverage and uncertainty. Do not run or reconstruct a
whole-model simulation for either target. Full-chip layout still requires all catalog
views and top-level placement, routing, extraction, timing, and physical checks.


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
rendezvous. The parameterized final resident readout uses signed current accumulation across the configured
prediction window plus first-index-tie argmax; do not create output PLIFs or class-spike counting.
