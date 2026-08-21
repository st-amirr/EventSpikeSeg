# EventSpikeSeg Architecture

## Active implementation model

`EventSpikeSegXL` is the active detailed 11-class DSEC/FPGA implementation target at
`241x351`. `EventSpikeSeg140k` remains the compact reference baseline. The XL choice is an
implementation decision, not a claim of measured accuracy superiority; both public Python
model names remain stable.

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

## Logical neuron-state count: parameters are not neuron states

The ~140k parameter count is **not** the number of PLIF neurons. Convolution kernels are
shared spatially, while every executed PLIF output element owns an independent persistent
membrane value. A logical neuron is addressed by `(layer, channel, y, x)`; `beta` and the
base threshold are shared per output channel, but `V[channel,y,x]` is not shared.

For an input of `H x W`, define

```text
H2 = ceil(H / 2), W2 = ceil(W / 2)
H4 = ceil(H2 / 2), W4 = ceil(W2 / 2)
```

Summing the output channels of all **37 executed inference PLIF populations** gives

```text
full-resolution PLIF state coefficient    = 672 + Nclass
half-resolution PLIF state coefficient    = 480
quarter-resolution PLIF state coefficient = 1280
```

so the general membrane-state count is

```text
N_mem = (672 + Nclass) * H * W
      + 480 * H2 * W2
      + 1280 * H4 * W4
```

For six-class DDD17 this becomes

```text
N_mem = 678 * H * W + 480 * H2 * W2 + 1280 * H4 * W4.
```

At the canonical `212 x 282` training/deployment resolution:

```text
H2 x W2 = 106 x 141
H4 x W4 = 53 x 71
N_mem   = 52,524,272 independent membrane values
```

Raw membrane storage alone would therefore be approximately 50.09 MiB at 8 bits,
75.14 MiB at 12 bits, 100.18 MiB at 16 bits, or 125.23 MiB at 20 bits. This is a
**logical-state** requirement, not a requirement for 52.5 million physical PLIF circuits.
A small array of physical PLIF processing elements may be time-multiplexed as long as
every logical neuron address retains its own state between visits.

Triangular fLong is enabled only on `down2`, `enc2`, `enc2_extra`, `down3`, `enc3`,
`enc3_extra`, `context1`, and `context2`. The enabled logical-neuron count is

```text
N_fLong = 352 * H2 * W2 + 1216 * H4 * W4
```

which is **9,836,800 neurons** at 212 x 282. Each of those neurons retains its own
adaptation age and adaptation amplitude, i.e. 19,673,600 additional logical state
values before quantization. The dynamic threshold can be derived when the neuron is
updated; it does not need to be stored as a third full map. Stem peer-membrane fInst
uses the membrane values themselves and does not introduce a separate full-resolution
membrane copy.

### XL state accounting at DSEC 241x351

The executed XL inference graph has 18 full-resolution, 12 half-resolution, and 20
quarter-resolution PLIF populations. Summing their output channels gives:

```text
full-resolution coefficient    = 672 + Nclass
half-resolution coefficient    = 768
quarter-resolution coefficient = 2144

N_mem_XL = (672 + Nclass) * H * W
         + 768 * H2 * W2
         + 2144 * H4 * W4
```

For 11-class DSEC:

```text
H x W   = 241 x 351 = 84,591 locations
H2 x W2 = 121 x 176 = 21,296 locations
H4 x W4 =  61 x  88 =  5,368 locations

N_mem_XL = 683*84,591 + 768*21,296 + 2144*5,368
         = 85,639,973 membrane values
```

The 26 fLong-enabled populations sum to 416 half-resolution and 2080
quarter-resolution channels:

```text
N_fLong_XL = 416*H2*W2 + 2080*H4*W4
           = 20,024,576 neurons
```

Each fLong neuron stores age and amplitude, adding 40,049,152 persistent values. Direct
asynchronous DSEC additionally needs one last-update timestamp for each of the 85,639,973
membrane states. Raw storage examples are:

| Persistent state | Count | Illustrative format | Storage |
| --- | ---: | ---: | ---: |
| membrane | 85,639,973 | 16 bit | 163.35 MiB |
| last-update timestamp | 85,639,973 | 32 bit | 326.69 MiB |
| fLong age + amplitude | 40,049,152 | 16 bit each value | 76.39 MiB |
| total above | 211,329,098 values | mixed | 566.42 MiB |
| class counters | 930,501 | illustrative 16 bit | 1.77 MiB |

This exact uncompressed footprint cannot be assumed to fit in on-chip PL memory. The XL
baseline therefore stores persistent state in external DDR and uses BRAM/URAM/LUTRAM as
a banked active-tile cache. Any timestamp compression, reduced state width, sparse state
allocation, or all-on-chip claim must be quantified and checked against the bit-exact
integer reference.

Training executes three additional auxiliary populations: 11 channels at half resolution
and 32+11 channels at quarter resolution, adding 465,080 transient training-only membrane
states. The inherited dead `refine2` would add 128 half-resolution channels (2,725,888
states) but is not called and must not be exported.

### State ownership

| Quantity | Sharing/lifetime |
| --- | --- |
| convolution weights | shared by the convolution across all `(y,x)` locations; static after export |
| `beta[c]` | shared by every neuron in output channel `c` |
| base threshold `theta[c]` | shared by every neuron in output channel `c` |
| membrane `V[c,y,x]` | **independent persistent state for every logical neuron** |
| fLong age/amplitude | independent persistent state for every fLong-enabled logical neuron |
| synaptic current accumulator | temporary for one layer/timestep; may be cleared/reused after PLIF update |
| spikes | transient sparse `(t,c,y,x)` event addresses between stages |


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
events are sliced before each semantic timestamp and rectified. GPU training accumulates
them into fixed physical-time divisions while retaining linear event multiplicity. Event
density never changes the number of training updates. The FPGA does not create these
divisions: AER events enter the first synaptic/PLIF stage directly.

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
  -> PLIF selector: local 1x1 96->96 synapses -> PLIF -> retinotopic binary gate
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

The goal is a **digital neuromorphic FPGA accelerator**. The substrate uses synchronous
digital circuits internally, but model execution is asynchronous: camera/hidden events
trigger only affected fan-out, touched neurons decay from their stored last-update
timestamp, and there is no global model timestep barrier. It is not a dense ANN
accelerator with PLIF inserted only as an activation.

| Software operation | Exact role | FPGA interpretation |
| --- | --- | --- |
| `ChannelAffine` | per-channel current gain | fold into quantized weight/scale before export |
| residual `add + clamp(0,1)` | merge binary spike routes | event merge / binary OR-dedup equivalent |
| nearest upsample | duplicate spatial spike locations | event-address fan-out/remapping |
| `torch.cat` | concatenate channel groups | channel-ID/address remapping; no arithmetic |
| XL projected bridges | preserve spikes around strided paths | timestamp-tagged local residual merge queues |
| XL parallel d1/d2/d4 context | retain three receptive-field identities | three address generators, channel remap, 384->128 fusion, local residual join |
| XL Q/K/V spike-mask attention | four local 8-channel coincidence gates | per-location/timestamp rendezvous counters and short V holding buffer; no spatial NxN matrix |
| local 96-ch PLIF selector | retinotopic binary gate | immediate local event gate; no frame reduction |
| temporal spike sum | class evidence | integer per-pixel class counters |
| argmax | final semantic label | comparator tree / sequential maximum |
| DDD17 timestamp scheduler | reconstruct approximate timed deliveries | digital scheduler feeding event/current arrivals |

The selector's 1x1 synaptic projection and PLIF population remain ordinary spike-native
SNN computation. A selector event gates only its own retinotopic feature event, avoiding
the former spatial `amax(H,W)` synchronization barrier.

## Primary implementation goal: digital neuromorphic FPGA

The canonical deployment objective is:

1. keep PyTorch/SpikingJelly as the training and floating-point golden reference;
2. export only the **executed XL inference graph** and its learned weights, beta, thresholds,
   fInst, and fLong parameters;
3. define deterministic fixed-point formats, rounding, saturation, and overflow rules;
4. build a bit-exact integer reference and verify layer currents, membranes, spikes, and
   semantic output against the float model;
5. implement reusable VHDL synaptic-accumulator + PLIF processing elements, preserving
   shared convolution kernels and binary spike routing;
6. store persistent membrane/adaptation/timestamp state in external DDR behind banked
   BRAM/URAM/LUTRAM tile caches and time-multiplex processing elements across tiles,
   channels, and stages;
7. first establish exact full/tiled execution, then add sparse optimizations such as
   touched-address queues, active-neuron lists, lazy decay, and clock-enable during idle
   periods only after equivalence is proven;
8. run RTL simulation, Vivado synthesis/place-and-route, post-implementation timing
   simulation, and representative-event SAIF/VCD power analysis;
9. optionally validate final latency/power on a physical ZCU104 when available.

## Exact event-addressed layer procedure

The training backend evaluates dense tensor `Conv2d` on fixed physical-time divisions.
The asynchronous FPGA evaluates the shared network parameters input-centrically:

1. Receive one timestamped presynaptic event `(t,c,y,x)`.
2. Generate only valid postsynaptic destinations from kernel, stride, padding, dilation,
   and group/depthwise address rules.
3. For each touched destination, load `V`, adaptation, and its `last_update_timestamp`.
4. Apply `retention = beta ** ((t-last_update)/5000us)`, then add the corresponding
   shared weight and execute threshold, reset, fInst, and fLong in the exported order.
5. Write the state and timestamp back. Enqueue each generated binary spike at timestamp
   `t`; if no spike is generated, propagation along that path stops.
6. Merge residual events, remap concatenated channels, and fan out nearest-upsample events
   by address. The local selector never waits for a complete spatial frame.
7. Read semantic class-spike counters at label timestamps. Persistent neuron state resets
   only at sequence/frame gaps, not at semantic-label boundaries.

There is no global neural timestep barrier in DSEC inference. Fixed-time training
divisions are a PyTorch approximation sharing the same weights and physical-time decay.

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

### Exact parameter accounting

| Configuration/graph | Parameters |
| --- | ---: |
| DDD17, 6 classes, registered module | 236,445 |
| DSEC, 11 classes, registered module | 237,115 |
| DSEC executed training forward | 232,059 |
| DSEC executed inference/export graph | 226,767 |
| inherited dead `refine2`, omitted | 5,056 |
| mid auxiliary head, training only | 726 |
| deep auxiliary head, training only | 4,566 |

The DSEC inference parameters split into 215,936 shared convolution weights, 3,584
foldable affine gains, 3,595 PLIF beta values, 3,595 PLIF base thresholds, four attention
comparison thresholds, one fInst strength, and 26 pairs of fLong strength/duration
parameters. The deployed graph contains 50 PLIF populations; training adds three auxiliary
populations, while the registered dead block contains two more populations.

### Native DSEC layer graph and dimensions

`T=10` below is the default PyTorch training schedule. FPGA input is a direct asynchronous
event stream and does not store ten input bins. Spatial dimensions and channel identities
are nevertheless the same.

| Stage | Synaptic/spiking operation | Output `T,N,C,H,W` | PLIF populations |
| --- | --- | --- | ---: |
| input | rectified ON/OFF counts for training | `10,1,2,241,351` | 0 |
| stem | 3x3, 2->32, affine, PLIF | `10,1,32,241,351` | 1 |
| encoder-1 | two residual DW3x3/PW1x1 32-ch blocks | `10,1,32,241,351` | 4 |
| detail-1 | residual DW3x3/PW1x1 32-ch | `10,1,32,241,351` | 2 |
| detail-2 | DW3x1 -> DW1x3 -> PW1x1, residual | `10,1,32,241,351` | 3 |
| detail-3 | residual DW3x3/PW1x1 32-ch | `10,1,32,241,351` | 2 |
| down2 main | stride-2 DW32 -> PW64 | `10,1,64,121,176` | 2 |
| bridge12 | stride-2 1x1, 32->64; merge with down2 | `10,1,64,121,176` | 1 |
| encoder-2 | two residual DW/PW 64-ch blocks | `10,1,64,121,176` | 4 |
| down3 main | stride-2 DW64 -> PW128 | `10,1,128,61,88` | 2 |
| bridge23 | stride-2 1x1, 64->128; merge with down3 | `10,1,128,61,88` | 1 |
| encoder-3 | two residual DW/PW 128-ch blocks | `10,1,128,61,88` | 4 |
| serial context | two residual dilation-2 DW/PW 128-ch blocks | `10,1,128,61,88` | 4 |
| parallel context | DW3x3 d1/d2/d4, concat 384, 1x1->128, residual | `10,1,128,61,88` | 4 |
| local spike attention | Q/K/V 128->32, four heads x eight channels, 32->128 residual | `10,1,128,61,88` | 4 |
| project3 | 1x1 128->64, then nearest upsample | `10,1,64,121,176` | 1 |
| decoder-2 fusion | concat project3+x2=128; DW128 -> PW64 | `10,1,64,121,176` | 2 |
| decoder-2 refine | residual DW/PW 64-ch | `10,1,64,121,176` | 2 |
| project2 | 1x1 64->32, then nearest upsample | `10,1,32,241,351` | 1 |
| late merge | concatenate semantic32 + shallow32 + detail32 | `10,1,96,241,351` | 0 |
| local selector | 1x1 96->96 PLIF, retinotopic gate | `10,1,96,241,351` | 1 |
| final fusion | DW96 -> PW32 | `10,1,32,241,351` | 2 |
| decoder-1 refine | residual DW/PW 32-ch | `10,1,32,241,351` | 2 |
| class head | 1x1 32->11 independent class PLIFs | `10,1,11,241,351` | 1 |
| readout | sum class spikes over 50 ms, per-pixel argmax | `1,11,241,351` logits | 0 |

Training-only heads are `64->11` at 121x176 and `128->32->11` at 61x88. They are skipped
by `model.eval()` and omitted from VHDL export.

### FPGA routing/control requirements

- `bridge12`/`bridge23` require timestamp-tagged merge queues for main and projected paths.
- Parallel d1/d2/d4 context concatenates channel address ranges and joins the residual by
  logical timestamp/location; it does not average branches.
- Attention is local rather than dense spatial attention. For each `(timestamp,y,x)`, Q
  and K form four eight-channel coincidence counts, each compared with its learned head
  threshold; the resulting four gates mask corresponding V groups before the 32->128
  projection. Path latency requires a local rendezvous/V holding buffer, not a global
  61x88 frame barrier.
- Decoder concatenations are channel-ID remaps. Nearest upsample is address fan-out.
- The 96->96 selector gates only the matching `(channel,y,x,timestamp)` event.
- Persistent state lives in DDR-backed tiles; shared weights and hot queues/tile banks may
  reside on chip. Weight storage is small compared with logical neuron state.
- Export and RTL verification must compare branch joins, attention coincidences/gates,
  membrane/timestamp trajectories, fInst/fLong state, emitted events, and final counters.

## Canonical naming

- `EventSpikeSegXL`: active detailed 11-class DSEC/FPGA implementation target.
- `EventSpikeSeg140k`: compact reference/baseline.

Historical top-ten/top-five/top-three architecture-search results retain their original
names and measured values.
