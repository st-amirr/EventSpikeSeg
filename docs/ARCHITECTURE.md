# EventSpikeSeg Architecture

## Canonical model

`EventSpikeSeg140k` is the project's primary ~140k architecture. `EventSpikeSegXL` is an
optional expanded ~236k comparison and is not the deployment baseline. New runs,
checkpoints, documentation, and deployment work use only these canonical names.

For the six-class DDD17 configuration, canonical `EventSpikeSeg140k` has **140,089
registered trainable parameters**. The Python module tree also contains an inherited
`refine2` block (5,056 parameters, two SpikingStage populations) that is never called
by the canonical forward graph. The training forward therefore executes **135,033**
parameters including the 396-parameter auxiliary head; inference executes **134,637**
parameters. Mixed-signal deployment must implement the executed inference graph, not
the dead inherited block or training-only auxiliary head.

The semantic class count is dataset-dependent: DDD17 uses 6 class populations and
DSEC-Semantic uses 11. The feature architecture is otherwise shared.

## Exact computational primitive

Every learned `SpikingStage` is implemented as:

```text
input spike/event activity
  -> SpikingJelly Conv2d synaptic projection (bias=False)
  -> optional per-channel affine current gain
  -> ParametricLIF neuron population
  -> binary output spikes
```

The convolution is **not itself a neuron**. Its learned kernel values are synaptic
weights/connectivity. The output feature map is the PLIF neuron population. Thus a
3x3 or 1x1 stage has a direct neuromorphic interpretation: presynaptic spikes activate
weighted synapses, synaptic currents are accumulated by postsynaptic PLIF membranes,
and those neurons emit the next spike map.

Depthwise/pointwise blocks intentionally contain two separate spiking populations:

```text
spikes -> DW 3x3 synapses -> PLIF -> spikes
       -> PW 1x1 synapses -> PLIF -> spikes
```

The intermediate PLIF population is part of the trained temporal state and must not
be collapsed during deployment.

## PLIF dynamics used by the trained model

`ParametricLIF` preserves explicit project-visible state while using SpikingJelly's
`ParametricLIFNode` charge equation. For each output channel `c`, the model learns a
shared retention `beta[c]` and a shared base threshold `theta[c]`; each spatial neuron
`(c,y,x)` keeps its own membrane state.

```text
candidate[c,y,x] = beta[c] * membrane[c,y,x] + current[c,y,x]
spike             = H(candidate - dynamic_threshold)
membrane          = candidate - reset - competition effects
```

Exact training/runtime facts:

- initial beta: `0.9375` (`beta_shift=4` initialization)
- beta: learnable per output channel
- SpikingJelly reciprocal tau: `1 - beta`
- initial base threshold: `0.5`
- base threshold: learnable per output channel
- threshold bounds: `[0.15, 1.25]`
- training surrogate: ATan
- inference spike: hard binary forward value
- reset: subtractive threshold reset (`v_reset=None` in the SpikingJelly core)
- membrane state persists through consecutive stream records and resets at sequence/gap boundaries

### Physical mixed-signal interpretation

Training values are dimensionless numerical states, not literal volts or amperes.
Deployment transfers the **dynamics**, not the numerical membrane value. After a
physical update interval `Delta_t` is chosen, a learned retention can be represented by
an equivalent continuous-time membrane constant:

```text
beta[c] = exp(-Delta_t / tau_m[c])
tau_m[c] = -Delta_t / ln(beta[c])
```

A mixed-signal target then calibrates capacitor/leak/bias settings so the measured
physical membrane retention over `Delta_t` matches the trained `beta[c]`. Thresholds
and synaptic weights are mapped using a target-specific voltage/current scale; they
must not be interpreted as direct volt or ampere values without that calibration.

## Input protocols

### DDD17

One record is a 50 ms six-channel event-statistic tensor. `TimestampEventInput`
schedules histogram activity into two polarity synaptic-input channels. With the
default 10 internal updates, the software reference uses 5 ms updates and three
weighted arrivals at `mean`, `mean-std`, and `mean+std` with weights `0.50/0.25/0.25`.
Because exact event tuples are absent, this is an input approximation. On mixed-signal
hardware it can be realized as timed current-pulse amplitudes or an equivalent event
encoding before the first PLIF population.

### DSEC-Semantic

DSEC is the preferred physical event-camera deployment path. Exact raw `(t,x,y,p)`
events are sliced before each semantic timestamp, rectified, and delivered as two
chronological polarity event channels. The DDD17 moment scheduler is bypassed. This
maps naturally to AER/event routing into the first synaptic/PLIF stage.

## Canonical EventSpikeSeg140k forward graph

```text
2-channel scheduled/raw event input
  -> stem: 3x3 synaptic Conv -> affine -> PLIF, 32 ch
  -> Encoder 1: two residual DW3x3-PLIF / PW1x1-PLIF blocks, 32 ch
       |-> persistent detail path: three residual DW/PW-PLIF blocks, 32 ch
       |-> shallow32 late-fusion route
       `-> Encoder 2
  -> Encoder 2: stride-2 DW/PW-PLIF + two residual refinements, 64 ch
       |-> 64-ch decoder skip
       `-> Encoder 3
  -> Encoder 3: stride-2 DW/PW-PLIF + two residual refinements, 128 ch
  -> semantic context: two serial residual dilation-2 DW/PW-PLIF blocks
  -> project3 128->64 PLIF -> nearest event upsample -> add/clamp x2 -> residual refine
  -> project2 64->32 PLIF -> nearest event upsample -> semantic32
  -> concatenate semantic32 + shallow32 + detail32 -> 96 channels
  -> PLIF selector: 1x1 96->96 synapses -> PLIF -> spatial binary channel enable
  -> final fuse: DW3x3 96->96 PLIF -> PW1x1 96->32 PLIF
  -> final residual 32-ch DW/PW-PLIF refinement
  -> semantic head: 1x1 32->Nclass synapses -> independent PLIF class populations
  -> temporal spike count -> per-pixel class argmax
```

There is **no softmax inference head**, no ReLU/GELU feature activation, no BatchNorm
dependency, and no dense count-domain MLP in the deployed canonical model.

## Homeostatic/competitive dynamics

### fInst

Stem-only `peer_membrane` inhibition is enabled. Its exact software rule uses a
retinotopic RMS-like membrane-energy term across feature channels and subtracts a
learned scaled decrement from peer membranes after a local spike event. This is more
complex than basic PLIF and is a mixed-signal mapping item: a target may implement the
exact function with mixed analog/digital support or validate a calibrated lateral-
inhibition approximation before claiming equivalence.

### fLong / TThresh

Triangular threshold adaptation is enabled on `down2`, `enc2`, `enc2_extra`, `down3`,
`enc3`, `enc3_extra`, `context1`, and `context2`. It is disabled on the full-resolution
Encoder-1/detail path and decoder. Each spiking neuron maintains adaptation age and
amplitude; the resulting retinotopic penalty is added to the base threshold. A physical
mapping may use programmable threshold bias/adaptation current or mixed-signal state,
but its time course must be measured against the software reference.

## Non-PLIF operations and mixed-signal treatment

The goal is **mixed-signal neuromorphic inference**, meaning synaptic integration and
PLIF membrane/leak/threshold dynamics should execute in physical analog/mixed-signal
neuron/synapse circuitry while digital event routing/control/readout is allowed. This
is the realistic architecture of available mixed-signal neuromorphic processors; a
strict all-analog end-to-end segmentation pipeline is not required.

| Software operation | Exact role | Deployment interpretation |
| --- | --- | --- |
| `ChannelAffine` | per-channel current gain | fold into synaptic efficacy/current scale |
| residual `add + clamp(0,1)` | merge binary spike routes | event merge/dedup or equivalent routing logic |
| nearest upsample | duplicate spatial spike locations | address fan-out/remapping |
| `torch.cat` | concatenate channel groups | channel/address remapping; no arithmetic |
| 96-ch selector `amax(H,W)` | binary global channel enable | digital event-control periphery or target-specific neuromorphic replacement |
| temporal spike sum | class evidence | event counters/readout |
| argmax | final semantic label | small digital readout comparator |
| DDD17 timestamp scheduler | reconstruct approximate timed deliveries | digital/event preprocessor or pulse scheduler |

The selector's 1x1 synaptic projection and PLIF population remain neuromorphic; only
the subsequent spatial global enable is non-local control logic. If a target requires
strictly local analog computation, this gate is the first candidate for replacement
and would require an accuracy revalidation/fine-tune rather than being silently changed.

## Primary implementation goal: mixed-signal neuromorphic hardware

The canonical deployment objective is now:

1. keep PyTorch/SpikingJelly as the digital training/reference implementation;
2. export learned convolution weights, per-channel beta, per-channel thresholds,
   fInst strength, and fLong parameters;
3. convert beta to calibrated physical membrane time constants and map synaptic weights
   to target-supported signed synaptic efficacy/current parameters;
4. map each executed `SpikingStage` to a synaptic projection plus a physical PLIF/LIF
   neuron population;
5. use digital AER/event routing only for connectivity, address transforms, gating,
   counters, configuration, and semantic readout;
6. compare membrane/spike traces against the SpikingJelly golden reference;
7. report real device latency, energy/power, accuracy, and mapping utilization only from
   actual mixed-signal hardware measurements.

Candidate hardware classes are analog/mixed-signal systems with programmable LIF/AdEx
membrane time constants and synaptic efficacy. Hardware selection is constrained by
network scale, convolution/connectivity mapping, per-channel parameter programmability,
and availability of measured latency/energy telemetry.

## Scalable mixed-signal execution

The deployment architecture should preserve convolutional weight sharing and reuse a
coarse-grained programmable synapse+PLIF tile across spatial partitions and stages rather
than physically unrolling every logical feature-map neuron. PLIF state is the limiting
resource: a logical population cannot simply be overwritten while its membrane/adaptation
state is still needed. The preferred implementation therefore supports state virtualization:

```text
logical PLIF state store -> restore tile state -> physical synapse/PLIF update
                         -> emit spikes -> save updated state -> reconfigure/reuse tile
```

Where capacity permits, frequently active or small populations may remain physically
resident. If membrane/adaptation state is digitized between visits, the system is a
mixed-signal virtualized neuromorphic accelerator rather than a continuously analog
physical neuron for every logical state. This is an explicit area/latency/state-bandwidth
trade-off, not a change to the trained SNN semantics.

## Secondary implementation path: FPGA digital reference

The existing VHDL/ZCU104 path remains useful as a deterministic digital reference and
fallback publication implementation. It can reproduce the same PLIF equations with
fixed-point arithmetic and provides synthesis/place-route latency and power estimates.
It is no longer the primary neuromorphic end goal.

## EventSpikeSegXL

`EventSpikeSegXL` is the 236,445-parameter expanded comparison model. It retains the same
32/64/128 PLIF basis but adds projected residual bridges, parallel d1/d2/d4 context,
a bottlenecked spike-mask attention residual, stronger mid-decoder concatenation,
asymmetric detail refinement, and a second training-only auxiliary head. It remains
available for accuracy/capacity comparison but is not the baseline for mixed-signal
mapping because its extra non-local/routing structures increase deployment complexity.

## Canonical naming

- `EventSpikeSeg140k`: canonical ~140k topology; use for all new runs and deployment work.
- `EventSpikeSegXL`: optional expanded ~236k comparison.

Legacy checkpoint architecture metadata is normalized internally during load and is
not exposed as a model class, registry entry, CLI architecture, or new checkpoint name.
Historical top-ten/top-five/top-three architecture-search results retain their original
names and measured values.
