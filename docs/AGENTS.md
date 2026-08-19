# EventSpikeSeg Agent Instructions

## Mission

Build and validate the canonical `EventSpikeSeg140k` (~140k registered parameters for the
six-class DDD17 configuration), then map its spike-native PLIF inference graph to
**mixed-signal neuromorphic hardware**. Training remains PyTorch + SpikingJelly; the
runtime goal is physical synaptic/neuron dynamics with digital event routing/control.
The FPGA/VHDL path is a secondary deterministic reference/fallback, not the primary
neuromorphic target.

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

## PLIF physical mapping contract

Per output channel, `beta=sigmoid(beta_logit)` and threshold are learned. Spatial
neurons keep individual membrane state. Software charge is equivalent to
`candidate = beta * membrane + current` before dynamic threshold/reset effects.

For a chosen physical time interval `Delta_t`, use the continuous-time equivalent
`tau_m = -Delta_t / ln(beta)` as the starting physical membrane-time-constant target.
Do not interpret training membrane/current/threshold numbers directly as volts/amps.
Target-specific calibration must choose a consistent voltage/current scale and verify
measured retention, threshold, and synaptic response against golden traces.

## Mixed-signal deployment rule

The primary target is not a strict all-analog system. It is a mixed-signal neuromorphic
runtime in which:

- membrane integration/leak/threshold and preferably synaptic current generation are
  physical analog/mixed-signal dynamics;
- AER/event routing, address remapping, configuration, counters, gating, and final
  semantic readout may be digital;
- CPU/GPU dense inference is absent from the deployed learned feature path.

### Scalable execution rule

Do not assume one physical PLIF circuit per logical `[C,H,W]` state. Prefer a reusable
coarse-grained analog/mixed-signal synapse+PLIF tile with convolutional weight sharing.
Inactive logical membrane/adaptation state may be saved/restored through a state store;
small/hot populations may remain physically resident. State save/restore must preserve
numeric dynamics and is part of the target-equivalent verification contract.

### Natural mappings

- Conv weights -> programmable signed synaptic efficacy/current
- PLIF beta -> calibrated membrane time constant/leak
- learned threshold -> calibrated threshold/bias
- ChannelAffine -> fold into synaptic efficacy
- concat -> channel routing
- nearest upsample -> spike-address fan-out
- residual spike add/clamp -> event merge/dedup
- class spike sum/argmax -> digital event counters/comparator

### Mapping risks requiring explicit validation

- stem `peer_membrane` fInst uses retinotopic cross-channel membrane energy;
- encoder/context triangular fLong uses adaptation age/amplitude and dynamic threshold;
- final selector uses a global spatial binary enable after a 96->96 PLIF projection.

Do not silently replace these. If hardware cannot reproduce them, define an explicit
hardware-compatible approximation and revalidate/fine-tune accuracy.

## Input contracts

DDD17 uses the 50 ms statistic scheduler and is an approximation because raw tuples are
unavailable. DSEC uses exact raw rectified events and bypasses the moment scheduler;
DSEC is therefore the cleaner physical event-camera deployment path.

## Verification

For every hardware target, preserve a staged golden comparison:

1. SpikingJelly trained model
2. exported parameter/graph representation
3. target-equivalent simulator/model
4. mapped hardware

Compare layer spike traces, membrane trajectories where observable, output spike counts,
semantic accuracy, latency, energy/power, and mapping utilization. Hardware power and
latency claims require actual device measurement; simulator estimates must be labeled.

## FPGA secondary path

Keep the VHDL/ZCU104 implementation work as a deterministic digital reference and
fallback publication route. It may use post-route timing/activity power estimates and
later board measurements, but it no longer defines the primary model-design objective.
