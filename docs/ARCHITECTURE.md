# EventSpikeSeg Architecture

## Active implementation model

`EventSpikeSeg140k` is the only 11-class DSEC/FPGA implementation target at `241x351`.
For two raw-event input polarities and 11 classes it has **140,589 registered
parameters**, **134,807 executed inference parameters**, **127,456 executed convolution
weights**, and **37 executed PLIF populations**. `EventSpikeSegXL` remains a software
comparison and the FPGA exporter rejects it.

The Python module tree also contains an inherited
`refine2` block (5,056 parameters, two SpikingStage populations) that is never called
by the canonical forward graph. The 11-class training forward executes **135,533**
parameters including the 726-parameter auxiliary head. FPGA deployment implements the
executed inference graph, not
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
full-resolution PLIF state coefficient    = 640 + Nclass
half-resolution PLIF state coefficient    = 512
quarter-resolution PLIF state coefficient = 1280
```

so the general membrane-state count is

```text
N_mem = (640 + Nclass) * H * W
      + 512 * H2 * W2
      + 1280 * H4 * W4
```

For six-class DDD17 this becomes

```text
N_mem = 646 * H * W + 512 * H2 * W2 + 1280 * H4 * W4.
```

At the canonical `212 x 282` training/deployment resolution:

```text
H2 x W2 = 106 x 141
H4 x W4 = 53 x 71
N_mem   = 51,089,456 independent membrane values
```

Raw membrane storage alone would therefore be approximately 48.72 MiB at 8 bits,
73.08 MiB at 12 bits, 97.45 MiB at 16 bits, or 121.81 MiB at 20 bits. This is a
**logical-state** requirement, not a requirement for 52.5 million physical PLIF circuits.
Each of the 37 permanent layer actors has its own PLIF update lanes. An actor may sequence
those local lanes across its own logical addresses, but lanes are not shared between
layers and every logical neuron retains its own state between visits.

Triangular threshold adaptation is enabled only on `down2`, `enc2`, `enc2_extra`, `down3`, `enc3`,
`enc3_extra`, `context1`, and `context2`. The enabled logical-neuron count is

```text
N_adapt = 352 * H2 * W2 + 1216 * H4 * W4
```

which is **9,836,800 neurons** at 212 x 282. Each of those neurons retains its own
adaptation age and adaptation amplitude, i.e. 19,673,600 additional logical state
values before quantization. The dynamic threshold can be derived when the neuron is
updated; it does not need to be stored as a third full map. Stem peer-membrane inhibition
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

The 26 threshold-adaptation-enabled populations sum to 416 half-resolution and 2080
quarter-resolution channels:

```text
N_adapt_XL = 416*H2*W2 + 2080*H4*W4
           = 20,024,576 neurons
```

Each adaptation-enabled neuron stores age and amplitude, adding 40,049,152 persistent values. Direct
A direct asynchronous variant would additionally need one last-update timestamp for every membrane state, but that is no longer the baseline runtime contract. Raw storage examples are:

| Persistent state | Count | Illustrative format | Storage |
| --- | ---: | ---: | ---: |
| membrane | 85,639,973 | 16 bit | 163.35 MiB |
| last-update timestamp | 85,639,973 | 32 bit | 326.69 MiB |
| threshold-adaptation age + amplitude | 40,049,152 | 16 bit each value | 76.39 MiB |
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
| threshold-adaptation age/amplitude | independent persistent state for every adaptation-enabled logical neuron |
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

DSEC starts from exact raw `(t,x,y,p)` events sliced before each semantic timestamp and rectified. Both training and the baseline FPGA runtime use the same fixed-time contract: each 50 ms semantic interval is accumulated into ten chronological 5 ms polarity slices with linear event multiplicity. Event density never changes the number of SNN updates. The baseline FPGA therefore does **not** propagate raw camera events asynchronously through the whole network; raw events are first assigned to one of the ten 5 ms runtime slices.

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

### Exact DSEC membrane-state count by executed population

`B` is a population already present in the shared encoder/decoder skeleton. `C` is a
population added by the canonical 140k detail/context/selector/refinement architecture.
Every row is an ordinary PLIF membrane array; custom neuron dynamics do not create a
second membrane array. `A` marks populations that additionally carry triangular
adaptation age/amplitude.

| Population | Origin | Output | Membranes | A |
| --- | :---: | ---: | ---: | :---: |
| stem | B | 32x241x351 | 2,706,912 | |
| enc1.depthwise | B | 32x241x351 | 2,706,912 | |
| enc1.pointwise | B | 32x241x351 | 2,706,912 | |
| enc1_extra.depthwise | C | 32x241x351 | 2,706,912 | |
| enc1_extra.pointwise | C | 32x241x351 | 2,706,912 | |
| detail1.depthwise | C | 32x241x351 | 2,706,912 | |
| detail1.pointwise | C | 32x241x351 | 2,706,912 | |
| detail2.depthwise | C | 32x241x351 | 2,706,912 | |
| detail2.pointwise | C | 32x241x351 | 2,706,912 | |
| detail3.depthwise | C | 32x241x351 | 2,706,912 | |
| detail3.pointwise | C | 32x241x351 | 2,706,912 | |
| down2.depthwise | B | 32x121x176 | 681,472 | A |
| down2.pointwise | B | 64x121x176 | 1,362,944 | A |
| enc2.depthwise | B | 64x121x176 | 1,362,944 | A |
| enc2.pointwise | B | 64x121x176 | 1,362,944 | A |
| enc2_extra.depthwise | C | 64x121x176 | 1,362,944 | A |
| enc2_extra.pointwise | C | 64x121x176 | 1,362,944 | A |
| down3.depthwise | B | 64x61x88 | 343,552 | A |
| down3.pointwise | B | 128x61x88 | 687,104 | A |
| enc3.depthwise | B | 128x61x88 | 687,104 | A |
| enc3.pointwise | B | 128x61x88 | 687,104 | A |
| enc3_extra.depthwise | C | 128x61x88 | 687,104 | A |
| enc3_extra.pointwise | C | 128x61x88 | 687,104 | A |
| context1.depthwise | C | 128x61x88 | 687,104 | A |
| context1.pointwise | C | 128x61x88 | 687,104 | A |
| context2.depthwise | C | 128x61x88 | 687,104 | A |
| context2.pointwise | C | 128x61x88 | 687,104 | A |
| project3 | B | 64x61x88 | 343,552 | |
| decoder2_extra.depthwise | C | 64x121x176 | 1,362,944 | |
| decoder2_extra.pointwise | C | 64x121x176 | 1,362,944 | |
| project2 | B | 32x121x176 | 681,472 | |
| final_selector.selector | C | 96x241x351 | 8,120,736 | |
| final_fuse.depthwise | C | 96x241x351 | 8,120,736 | |
| final_fuse.pointwise | C | 32x241x351 | 2,706,912 | |
| decoder1_extra.depthwise | C | 32x241x351 | 2,706,912 | |
| decoder1_extra.pointwise | C | 32x241x351 | 2,706,912 | |
| head.stage | B | 11x241x351 | 930,501 | |
| **Base skeleton subtotal** | B | 14 populations | **17,251,429** | |
| **Canonical additions subtotal** | C | 23 populations | **55,591,904** | |
| **Executed total** | | 37 populations | **72,843,333** | **14,023,680 adapted** |

The earlier count placed `project2` after its nearest-neighbor upsample. That was wrong:
the PLIF state is half-resolution and only its binary spike addresses are fanned out.

## Inhibition and threshold-adaptation dynamics

### Peer-membrane inhibition

Stem-only `peer_membrane` inhibition is enabled. Its exact software rule uses a
retinotopic RMS-like membrane-energy term across feature channels and subtracts a
learned scaled decrement from peer membranes after a local spike event. This is more complex than basic PLIF and is an FPGA cost item because it needs
retinotopic cross-channel state access and extra arithmetic. The first RTL version must
match the fixed-point reference exactly; a cheaper approximation is allowed only with
explicit accuracy revalidation.

### Triangular threshold adaptation

Triangular threshold adaptation is enabled on `down2`, `enc2`, `enc2_extra`, `down3`,
`enc3`, `enc3_extra`, `context1`, and `context2`. It is disabled on the full-resolution
Encoder-1/detail path and decoder. Each spiking neuron maintains adaptation age and
amplitude; the resulting retinotopic penalty is added to the base threshold. On FPGA, adaptation age/amplitude and the resulting dynamic threshold are integer/
fixed-point state. Their time course must match the exported integer reference exactly.

## Non-PLIF operations and FPGA treatment

The goal is a **digital neuromorphic FPGA accelerator**. The substrate uses synchronous
digital circuits and preserves the trained fixed-time SNN semantics: each 50 ms DSEC
record contains ten explicit 5 ms neural updates. Within each update, only nonzero
spike locations trigger connected synaptic fan-out/additions, so the synaptic datapath
remains sparse even though neuron time advances on a fixed schedule. It is not a dense
ANN accelerator with PLIF inserted only as an activation.

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
2. export only the **37-population executed 140k inference graph** and its learned weights, beta, thresholds,
   inhibition, adaptation strength, and adaptation-duration parameters;
3. define deterministic fixed-point formats, rounding, saturation, and overflow rules;
4. build a bit-exact integer reference and verify layer currents, membranes, spikes, and
   semantic output against the float model;
5. instantiate one permanent VHDL actor per executed layer; each owns convolution
   addressing, accumulator lanes, PLIF/mechanism logic, queue, and weight ROM;
6. store persistent membrane/adaptation state in banked/tiled memory; the fixed-step baseline
   does not require a per-membrane timestamp; external/onboard DDR is forbidden and fit must be measured;
7. first establish exact T=10 tiled execution, then add sparse optimizations such as
   touched-address queues, active-neuron lists, compact lazy-step tags, and clock-enable during idle
   periods only after equivalence is proven;
8. run RTL simulation, Vivado synthesis/place-and-route, post-implementation timing
   simulation, and representative-event SAIF/VCD power analysis;
9. optionally validate final latency/power on a physical Nexys Video when available.

## Exact fixed-step sparse layer procedure

The training backend evaluates `[T,N,C,H,W]` sequences with ten fixed 5 ms updates per
50 ms DSEC record. The baseline FPGA preserves exactly that temporal contract while
changing the convolution execution order to exploit sparsity.

For one layer and one 50 ms record:

1. Consume the layer's ten chronological input spike/count slices `t0..t9`.
2. For slice `t`, enumerate only nonzero presynaptic locations `(c,y,x)` and generate
   valid postsynaptic destinations from kernel, stride, padding, dilation, and group/depthwise rules.
3. Accumulate the corresponding shared weights into the destination current for that 5 ms step;
   binary spikes require no activation multiply.
4. Advance the layer's PLIF/adaptation state once for that 5 ms step using the exported
   fixed-point equation, then apply threshold, reset, peer inhibition, and threshold adaptation.
5. Emit the slice's binary output spikes and continue with `t+1` while the layer/state tile
   remains resident where possible.
6. After `t9`, write the layer/tile's final persistent state back and provide the ten output
   spike slices/event lists to the next feed-forward layer.
7. After the semantic head finishes `t0..t9`, sum class spikes over the 50 ms record and
   emit one per-pixel argmax segmentation. Persistent neuron state carries into the next
   consecutive record and resets only at sequence/frame gaps.

There is therefore an explicit 5 ms neural timestep boundary, but no need to run dense
zero-valued convolution. The baseline does not update/threshold once per raw camera event
and does not need a per-neuron `last_update_us` timestamp. A lazy step-tag optimization is
allowed only after exact integer-reference equivalence is demonstrated.

## Static layer-actor FPGA execution

There is no requirement for one hardware PLIF circuit per logical `[C,H,W]` neuron, but
there is one permanent actor per executed layer. An actor can sequence local lanes over
its own destinations; those arithmetic blocks are never reused by a different layer:

```text
event/spike FIFO -> shared-kernel weight lookup -> synaptic accumulator
                 -> load PLIF state -> fixed-point leak/integrate/threshold/reset
                 -> save state -> emit output spike event
```

The state path is banked and locality-aware. A layer actor does not issue a backing-memory
transaction for every individual synaptic addition. It retains recently touched state in
actor-local banks, accumulates the contribution for the destination being serviced, performs
one PLIF update, and writes the resulting state once. A missing sparse-table address is the
exact reset state. A state entry may be reclaimed only when quantized membrane and adaptation
are inactive; a full associative set reports overflow and never evicts live state silently.

This reduces traffic but does not remove the fundamental per-neuron state requirement. A
presynaptic event that touches a postsynaptic destination must eventually read or already
have that destination's state locally. Conventional and neuromorphic hardware differ mainly
in where that state resides, how spikes are multicast, and how well local memory exploits
event locality.

Logical live membrane/adaptation state remains persistent in banked on-chip BRAM/LUTRAM.
Common clock/reset and state-bank fabrics are shared infrastructure, not shared layer
compute. The main trade-off is per-actor lane parallelism versus state-bank bandwidth, event-FIFO
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
Vivado Report Power. These are **post-implementation estimates** unless a Nexys Video is
actually instrumented; only real board measurements may be called measured power or
measured hardware latency.

## EventSpikeSegXL software comparison (not an FPGA target)

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
comparison thresholds, one inhibition strength, and 26 pairs of threshold-adaptation strength/duration
parameters. The deployed graph contains 50 PLIF populations; training adds three auxiliary
populations, while the registered dead block contains two more populations.

### Native DSEC layer graph and dimensions

`T=10` below is both the default PyTorch training schedule and the baseline FPGA runtime schedule. Raw DSEC events are accumulated into the same ten 5 ms slices; FPGA input is not a direct asynchronous
event stream. Hardware may represent the ten 5 ms inputs as sparse event/count lists rather than dense full-frame bins, but their temporal boundaries are explicit. Spatial dimensions and channel identities
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

#
## Fixed 50 ms FPGA runtime schedule

The baseline hardware now deliberately matches the trained multi-step execution rather than converting the checkpoint to a different asynchronous neuron model.

One DSEC semantic record is 50 ms and contains ten chronological 5 ms SNN slices. The hardware scheduling unit is the **complete 50 ms record**, while the neuron integration unit remains **5 ms**:

```text
raw DSEC events for 50 ms
        -> rectify / map coordinates
        -> accumulate into t0..t9 (10 x 5 ms)
        -> Layer 1: process t0..t9 sequentially with Layer-1 persistent PLIF state
        -> buffer Layer-1 output spikes for t0..t9
        -> Layer 2: process t0..t9 sequentially with Layer-2 persistent PLIF state
        -> ...
        -> semantic head t0..t9
        -> temporal class-spike count
        -> one segmentation result for the 50 ms record
```

This layer-major schedule is equivalent to the trained `[T,N,C,H,W]` graph because recurrence is local to each PLIF population and inter-layer connections are feed-forward. Computing the complete ten-step output sequence of layer `L` before layer `L+1` consumes it does not change the mathematical result.

### Memory consequence

This schedule is specifically chosen to reduce persistent-state traffic. For a layer or spatial tile:

1. load its membrane/adaptation state from backing memory into BRAM/URAM/cache;
2. keep that state resident while executing `t0` through `t9` in chronological order;
3. exploit spike sparsity inside each 5 ms slice so zero input locations cause no synaptic weight additions;
4. update PLIF state once per 5 ms slice under the exported fixed-point equation;
5. buffer the ten output spike slices/event lists required by the next layer;
6. write the final state back once after `t9` and advance to the next layer/tile.

The baseline therefore does **not** require a 32-bit `last_update_us` value per logical membrane. Time advances uniformly in known 5 ms steps. A later lazy-update implementation may use a compact step tag to skip untouched-state decay, but it is an optimization and must be proven equivalent to the fixed-step integer reference.

This design is **not fully asynchronous**. It is a fixed-time digital neuromorphic SNN with sparse/event-addressed synaptic work inside each 5 ms slice. The sustained real-time requirement is one complete record every 50 ms (20 Hz). Input acquisition for record `k+1` may be double-buffered while record `k` is computed.

## FPGA routing/control requirements

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
  membrane/timestamp trajectories, inhibition/adaptation state, emitted events, and final counters.

## Canonical naming

- `EventSpikeSeg140k`: only 11-class DSEC/FPGA implementation target.
- `EventSpikeSegXL`: software-only capacity comparison; rejected by FPGA export.

Historical top-ten/top-five/top-three architecture-search results retain their original
names and measured values.

Published source terminology is retained only when citing the source or preserving a
historical experiment identifier. Active software, exported model specifications, and RTL
use `peer_membrane_inhibition`, `triangular_threshold_adaptation`, and
`adaptation_duration`.
