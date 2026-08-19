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
parameters. FPGA deployment must implement the executed inference graph, not
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

### Digital FPGA PLIF interpretation

Training membrane/current/threshold values are dimensionless numerical SNN states, not
literal volts or amperes. FPGA deployment keeps the same discrete-time dynamics and
quantizes them into deterministic fixed-point arithmetic. The baseline per-channel PLIF
update is:

```text
V_next[c,y,x] = beta_q[c] * V[c,y,x] + I_q[c,y,x]
spike = V_next >= threshold_q[c] + adaptive_threshold_q[c,y,x]
```

`beta_q`, thresholds, membrane state, synaptic currents, and adaptation state are stored
as integer/fixed-point values under one frozen rounding/saturation contract. The first
implementation should preserve the learned per-channel beta with a fixed-point
coefficient. A shift-only/power-of-two leak is an optional optimization only after its
accuracy and bit-level behavior are explicitly revalidated.

## Input protocols

### DDD17

One record is a 50 ms six-channel event-statistic tensor. `TimestampEventInput`
schedules histogram activity into two polarity synaptic-input channels. With the
default 10 internal updates, the software reference uses 5 ms updates and three
weighted arrivals at `mean`, `mean-std`, and `mean+std` with weights `0.50/0.25/0.25`.
Because exact event tuples are absent, this is an input approximation. On FPGA, a
digital timestamp scheduler emits the same weighted polarity deliveries into the first
synaptic accumulator/PLIF stage.

### DSEC-Semantic

DSEC is the preferred direct event-stream FPGA deployment path. Exact raw `(t,x,y,p)`
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
learned scaled decrement from peer membranes after a local spike event. This is more complex than basic PLIF and is an FPGA cost item because it needs
retinotopic cross-channel state access and extra arithmetic. The first RTL version must
match the fixed-point reference exactly; a cheaper approximation is allowed only with
explicit accuracy revalidation.

### fLong / TThresh

Triangular threshold adaptation is enabled on `down2`, `enc2`, `enc2_extra`, `down3`,
`enc3`, `enc3_extra`, `context1`, and `context2`. It is disabled on the full-resolution
Encoder-1/detail path and decoder. Each spiking neuron maintains adaptation age and
amplitude; the resulting retinotopic penalty is added to the base threshold. On FPGA, adaptation age/amplitude and the resulting dynamic threshold are integer/
fixed-point state. Their time course must match the exported integer reference exactly.

## Non-PLIF operations and FPGA treatment

The goal is a **digital neuromorphic FPGA accelerator**. The substrate is clocked digital
logic, but the runtime preserves the SNN structure: binary spike communication,
persistent PLIF membrane/adaptation state, event-address-triggered synaptic additions,
convolutional weight sharing, and inactivity-aware scheduling. It is not a dense ANN
accelerator with PLIF inserted only as an activation.

| Software operation | Exact role | FPGA interpretation |
| --- | --- | --- |
| `ChannelAffine` | per-channel current gain | fold into quantized weight/scale before export |
| residual `add + clamp(0,1)` | merge binary spike routes | event merge / binary OR-dedup equivalent |
| nearest upsample | duplicate spatial spike locations | event-address fan-out/remapping |
| `torch.cat` | concatenate channel groups | channel-ID/address remapping; no arithmetic |
| 96-ch selector `amax(H,W)` | binary global channel enable | one per-channel `seen_spike` flag / OR reduction over emitted events |
| temporal spike sum | class evidence | integer per-pixel class counters |
| argmax | final semantic label | comparator tree / sequential maximum |
| DDD17 timestamp scheduler | reconstruct approximate timed deliveries | digital scheduler feeding event/current arrivals |

The selector's 1x1 synaptic projection and PLIF population remain ordinary spike-native
SNN computation. Because its `amax(H,W)` is applied to binary spikes, the FPGA does not
need a dense floating-point global reduction: it can set a channel flag whenever any
selector spike is emitted during that clock.

## Primary implementation goal: digital neuromorphic FPGA

The canonical deployment objective is:

1. keep PyTorch/SpikingJelly as the training and floating-point golden reference;
2. export only the **executed inference graph** and its learned weights, beta, thresholds,
   fInst, and fLong parameters;
3. define deterministic fixed-point formats, rounding, saturation, and overflow rules;
4. build a bit-exact integer reference and verify layer currents, membranes, spikes, and
   semantic output against the float model;
5. implement reusable VHDL synaptic-accumulator + PLIF processing elements, preserving
   shared convolution kernels and binary spike routing;
6. store persistent membrane/adaptation state in banked BRAM/URAM/LUTRAM and
   time-multiplex processing elements across spatial tiles/channels/stages;
7. first establish exact full/tiled execution, then add sparse optimizations such as
   touched-address queues, active-neuron lists, lazy decay, and clock-enable during idle
   periods only after equivalence is proven;
8. run RTL simulation, Vivado synthesis/place-and-route, post-implementation timing
   simulation, and representative-event SAIF/VCD power analysis;
9. optionally validate final latency/power on a physical ZCU104 when available.

## Scalable FPGA execution

There is no requirement for one hardware PLIF circuit per logical `[C,H,W]` neuron. A
small array of digital processing elements can be reused across the network:

```text
event/spike FIFO -> shared-kernel weight lookup -> synaptic accumulator
                 -> load PLIF state -> fixed-point leak/integrate/threshold/reset
                 -> save state -> emit output spike event
```

Logical membrane/adaptation state remains persistent in memory between visits. This is
normal time-multiplexed accelerator execution, not a change to the SNN semantics. The
main trade-off is processing-element parallelism versus BRAM/URAM bandwidth, event-FIFO
pressure, logic area, and latency.

## Why the FPGA implementation is still neuromorphic

The implementation is fully digital, but it intentionally preserves the neuromorphic
computational model: stateful PLIF neurons, sparse spikes as inter-layer communication,
event-driven synaptic additions instead of multiplying every zero activation, shared
local receptive fields, temporal state continuity, and activity-dependent work. The
membrane/current values are fixed-point numerical representations of neuron state—not
physical voltages/currents—and this distinction must be explicit in the paper.

## Verification and reporting

The required chain is `SpikingJelly float -> bit-exact integer reference -> VHDL RTL ->
post-route implementation`. Latency is derived from cycle counts and the achieved routed
clock. Power should use representative DDD17/DSEC switching activity (SAIF/VCD) with
Vivado Report Power. These are **post-implementation estimates** unless a ZCU104 is
actually instrumented; only real board measurements may be called measured power or
measured hardware latency.

## EventSpikeSegXL

`EventSpikeSegXL` is the 236,445-parameter expanded comparison model. It retains the same
32/64/128 PLIF basis but adds projected residual bridges, parallel d1/d2/d4 context,
a bottlenecked spike-mask attention residual, stronger mid-decoder concatenation,
asymmetric detail refinement, and a second training-only auxiliary head. It remains
available for accuracy/capacity comparison but is not the FPGA deployment baseline
because its extra non-local/routing structures increase memory, control, and latency cost.

## Canonical naming

- `EventSpikeSeg140k`: canonical ~140k topology; use for all new runs and deployment work.
- `EventSpikeSegXL`: optional expanded ~236k comparison.

Historical top-ten/top-five/top-three architecture-search results retain their original
names and measured values.
