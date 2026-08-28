# EventSpikeSeg Architecture

## Active implementation model

`EventSpikeSeg140k` is the only six-class DSEC/ASIC implementation target. Revision v8
uses the native **440x640** semantic plane and has **149,835 registered parameters**,
**149,423 executed inference parameters**, **143,824 executed synaptic weights**, and
**25 executed PLIF populations plus one stateless temporal class-current readout**.
`EventSpikeSegXL` remains a software comparison and hardware export rejects it.

The input loader no longer scales rectified event coordinates to 241x351. It schedules
ten chronological two-polarity 440x640 count maps. A learned standard 5x5 stride-2 PLIF
stem produces the 32-channel semantic half scale; therefore raw events encounter learned
filters before spatial reduction. An independent 8-channel native detail stem preserves
thin boundaries without putting the old 32/96-channel trunk at native resolution.

```text
input                         10xNx2x440x640
native detail stem/block      10xNx8x440x640
semantic stem + encoder-1     10xNx32x220x320
encoder-2 / decoder-2         10xNx64x110x160
encoder-3 / context           10xNx128x55x80
native semantic/detail merge  10xNx40x440x640
final PLIF fusion             10xNx16x440x640
class-current readout         Nx6x440x640
```

The native detail block, semantic stem/first block, and 32->64 transition use standard
spatial/channel convolutions. Later encoder blocks remain depthwise/pointwise. At quarter
scale, projected decoder64 and encoder64 spikes are concatenated and mixed by one standard
1x1 128->64 PLIF stage. At half scale, coincident projected/skip spikes retain multiplicity
instead of being binary-OR deduplicated. Native semantic32 and detail8 spikes are then
concatenated and fused by one standard 3x3 40->16 PLIF stage, so cross-channel and spatial
evidence combines before thresholding.

The final 16->6 1x1 synapse consumes binary spikes but does not threshold them into
class spikes. It accumulates signed current over all ten updates and exposes continuous
logits only after the complete record. This removes the old eleven-level (0..10)
confidence bottleneck. The training-only 64->6 auxiliary head and 16->1 boundary head
are omitted from deployment.

At 440x640 the exact deployed persistent state is:

```text
N_mem   = 32*440*640 + 128*220*320 + 416*110*160 + 1280*55*80
        = 30,976,000 membrane values
N_adapt = 320*110*160 + 1216*55*80
        = 10,982,400 adaptation-enabled values
```

With 16-bit membrane and two 16-bit adaptation fields, dense persistent state is
100.98 MiB before lazy-update tags, queues, and alignment. This is lower than the old 241x351 graph's
72.84 million membranes/192.44 MiB because the wide paths now begin at half resolution.
For ASIC deployment this is an SRAM-macro problem, not an FPGA BRAM limit. A dense
standard-cell implementation is invalid; full-chip PPA requires characterized actor-local
SRAM macros or a lossless sparse organization proven over complete DSEC sequences.


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

### Digital ASIC PLIF interpretation

Training membrane/current/threshold values are dimensionless numerical SNN states, not
literal volts or amperes. ASIC deployment keeps the same discrete-time dynamics and
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

The v8 ~150k parameter count is not the number of physical or logical PLIF neurons.
Weights, learned beta, and base thresholds are shared; membrane and adaptation state are
owned separately by every executed `(layer, channel, y, x)` logical neuron.

For the canonical native DSEC geometry define:

```text
H0 x W0 = 440 x 640  (native)
H1 x W1 = 220 x 320  (half)
H2 x W2 = 110 x 160  (quarter)
H3 x W3 =  55 x  80  (eighth)
```

The **25 deployed PLIF populations** sum to the following channel-equivalent state maps:

```text
native  :   32 * H0 * W0
half    :  128 * H1 * W1
quarter :  416 * H2 * W2
eighth  : 1280 * H3 * W3
```

Therefore:

```text
N_mem = 32*440*640 + 128*220*320 + 416*110*160 + 1280*55*80
      = 30,976,000 independent membrane values
```

Triangular threshold adaptation is disabled on the native and half-resolution paths.
It is active only on the semantic encoder/context populations beginning with `down2`:

```text
N_adapt = 320*110*160 + 1216*55*80
        = 10,982,400 adaptation-enabled neurons
```

Each adaptation-enabled neuron owns `adaptation_age` and `adaptation_amplitude`.
Because DSEC training keeps touched-neuron lazy updates enabled, the exact streaming
runtime also associates each live neuron with a compact **24-bit last-bin tag**. It is a
5 ms bin index, not a microsecond timestamp. On the next touch the elapsed-bin distance
`Δk` determines the required lazy leak `beta[c]^Δk`.

For a hypothetical dense exact-state implementation the persistent payload is therefore:

| State | Values | Storage |
| --- | ---: | ---: |
| membrane, int16 | 30,976,000 | 59.08 MiB |
| adaptation age + amplitude, two int16 fields | 21,964,800 | 41.90 MiB |
| last-bin tag, 24 bit | 30,976,000 | 88.62 MiB |
| exact dense touched-state total | — | **189.60 MiB** |

The active implementation is sparse, so last-bin tags exist only for live table entries.
With a 28-bit logical address, int16 membrane and 24-bit bin tag, the raw non-adaptive
payload is about 9 bytes/entry; adding two int16 adaptation fields gives about 13 bytes.
The conservative profiler keeps **12-byte non-adaptive** and **16-byte adaptive** aligned
entry budgets. This is why actor-local SRAM capacity and macro selection are hard full-chip gates.
For the ASIC target, these values set the SRAM-macro requirement rather than an FPGA BRAM
limit. Full-chip PPA is invalid until actor-local state is mapped to characterized SRAM
macros instead of standard-cell register arrays.

### Why v8 is structurally cheaper than v6

The revision intentionally spends slightly more static weight memory to remove expensive
high-resolution stateful transformations:

| Metric | superseded v6 | active v8 | change |
| --- | ---: | ---: | ---: |
| executed PLIF populations | 37 | 25 | -32.4% |
| executed synaptic weights | 127,456 | 143,904 | +12.9% |
| logical membranes | 72.84M | 30.98M | **-57.5%** |
| membrane+adaptation payload (excluding lazy bin tag) | 192.44 MiB | 100.98 MiB | **-47.5%** |
| full/native-resolution state coefficient | 651 | 32 | **-95.1%** |

The comparison is especially notable because v8 processes the **native 440x640** semantic
plane rather than 241x351. It has about 3.33x as many input pixels but still owns fewer
logical membranes. The state-per-synaptic-weight ratio falls from roughly 572 to 215.
This is the intended state-first hardware design direction: static int8 weights are cheap;
large read/write PLIF maps are expensive.

The reduction comes from four code-level changes:

1. the 32-channel semantic trunk starts with a learned 5x5 stride-2 standard convolution,
   so it becomes half-resolution immediately after learned filtering;
2. the native detail route is only 8 channels and has one residual standard block;
3. several early DW->PLIF->PW->PLIF pairs were replaced by one standard Conv->PLIF stage,
   spending weights to eliminate an entire persistent membrane population;
4. the native 96-channel selector, 32-channel decoder refinement, and output class-PLIF
   population were removed. The final classifier is now a stateless temporal-current readout.

These figures are structural cost proxies, not measured event-driven operation counts.
Actual synaptic additions still depend on spike activity and must be reported from traces.

### Exact v8 deployed PLIF populations at DSEC 440x640

`A` marks populations that additionally own triangular adaptation age/amplitude.

| Population | Output | Membranes | A |
| --- | ---: | ---: | :---: |
| detail_stem | 8x440x640 | 2,252,800 | |
| detail1.standard | 8x440x640 | 2,252,800 | |
| stem | 32x220x320 | 2,252,800 | |
| enc1.standard | 32x220x320 | 2,252,800 | |
| enc1_extra.depthwise | 32x220x320 | 2,252,800 | |
| enc1_extra.pointwise | 32x220x320 | 2,252,800 | |
| down2.standard | 64x110x160 | 1,126,400 | A |
| enc2.depthwise | 64x110x160 | 1,126,400 | A |
| enc2.pointwise | 64x110x160 | 1,126,400 | A |
| enc2_extra.depthwise | 64x110x160 | 1,126,400 | A |
| enc2_extra.pointwise | 64x110x160 | 1,126,400 | A |
| down3.depthwise | 64x55x80 | 281,600 | A |
| down3.pointwise | 128x55x80 | 563,200 | A |
| enc3.depthwise | 128x55x80 | 563,200 | A |
| enc3.pointwise | 128x55x80 | 563,200 | A |
| enc3_extra.depthwise | 128x55x80 | 563,200 | A |
| enc3_extra.pointwise | 128x55x80 | 563,200 | A |
| context1.depthwise | 128x55x80 | 563,200 | A |
| context1.pointwise | 128x55x80 | 563,200 | A |
| context2.depthwise | 128x55x80 | 563,200 | A |
| context2.pointwise | 128x55x80 | 563,200 | A |
| project3 | 64x55x80 | 281,600 | |
| decoder2_fuse | 64x110x160 | 1,126,400 | |
| project2 | 32x110x160 | 563,200 | |
| final_fuse.standard | 16x440x640 | 4,505,600 | |

The `16->6` class readout has **zero PLIF membrane state**. For each native pixel it sums
signed 1x1 synaptic current caused by the final hidden spikes over `t0..t9`. The common
positive `output_rate_scale / 10` factor does not change class argmax, so the ASIC may
perform argmax directly on the unscaled signed accumulators while retaining a scaled
path only when bit-exact logits are required for verification.

### State ownership

| Quantity | Sharing/lifetime |
| --- | --- |
| convolution/readout weights | static, spatially shared |
| `beta[c]` | static/shared by output channel |
| base threshold `theta[c]` | static/shared by output channel |
| membrane `V[layer,c,y,x]` | **independent persistent state** |
| adaptation age/amplitude | independent persistent state where enabled |
| per-neuron microsecond timestamp | absent |
| compact `last_bin_tag` | **24-bit persistent field for each live sparse state** |
| synaptic current accumulator | temporary for one layer/slice destination |
| hidden spikes | transient sparse `(slice,c,y,x)` events |
| final class-current accumulator | transient across configurable prediction window; default 10 bins / 50 ms, then reset |

## Input protocols

### DDD17

One record is a 50 ms six-channel event-statistic tensor. `TimestampEventInput` schedules
histogram activity into two polarity synaptic-input channels. With ten internal updates,
the software reference advances in 5 ms steps. Because exact event tuples are absent,
DDD17 remains an approximation input path and is not the active ASIC target.

### DSEC-Semantic

DSEC starts from exact raw `(t,x,y,p)` events sliced before each semantic timestamp and
rectified to the canonical 640x440 semantic plane. **There is no 241x351 resize in v8.**
Each 50 ms interval is assigned to ten ordered 5 ms ON/OFF slices with linear event
multiplicity. The hardware may keep those slices as sparse address/count lists rather
than dense tensors, but the ten temporal boundaries are explicit.

## Canonical EventSpikeSeg140k v8 forward graph

```text
raw DSEC events -> rectify -> ten 5 ms two-polarity sparse slices @ 440x640

native detail branch:
  3x3 2->8 PLIF
  -> residual standard 3x3 8->8 PLIF

semantic branch:
  5x5 stride2 2->32 PLIF                         @ 220x320
  -> residual standard 3x3 32->32 PLIF
  -> residual DW32 PLIF -> PW32 PLIF
  -> standard 3x3 stride2 32->64 PLIF            @ 110x160
  -> residual DW64/PW64
  -> residual DW64/PW64
  -> DW64 stride2 -> PW128                       @ 55x80
  -> residual DW128/PW128
  -> residual DW128/PW128
  -> two residual dilation-2 DW128/PW128 blocks

decoder:
  project3 128->64 PLIF -> nearest fanout to 110x160
  -> concatenate with x2 = 128 channels -> standard 1x1 128->64 PLIF
  -> project2 64->32 PLIF -> nearest fanout to 220x320
  -> multiplicity-preserving event sum with x1 (values 0, 1, or 2)
  -> nearest fanout to 440x640

late native fusion:
  concat semantic32 + detail8 = 40 channels
  -> standard 3x3 40->16 PLIF
  -> 1x1 16->6 signed temporal-current readout (no PLIF)
  -> accumulate over t0..t9 -> per-pixel argmax
```

Deployment omits the training-only `aux_head`, `boundary_head`, inherited `refine2`,
surrogate-gradient logic, and every XL-only module.

## ASIC actor graph topology: a DAG, not a 25-stage chain

The **25 PLIF populations are permanent hardware actors, but they are not connected as
`actor0 -> actor1 -> ... -> actor24`**.  The deployed v8 forward pass is a fixed directed
acyclic graph (DAG).  Input events fork into the native detail and semantic paths; residual
blocks contain binary-OR bypass joins; `x1` and `x2` fan out into both deeper encoder work
and later decoder skips; decoder fanout/concatenation brings the branches back together
before `final_fuse.standard`.

The ASIC exporter therefore treats the actor tuple only as a deterministic **topological
export order**. Runtime connectivity comes from explicit graph nodes/edges in
`src/eventspikeseg/asic/topology.py` and `layer_graph.json`. The static interconnect is
compiled for EventSpikeSeg140k; no generic programmable NoC or runtime layer scheduler is
required.

```text
                         -> detail_stem -> detail1 --residual OR-------------------
                        /                                                     \
input events -----------                                                       final concat
                        \                                                     /
                         -> stem -> enc1 -> enc1_extra = x1 ------------------+
                                      |                \                     |
                                      v                 \ decoder skip       |
                                    down2 -> enc2 -> enc2_extra = x2          |
                                                       | \                  |
                                                       v  \ decoder skip     |
                                                     down3 -> enc3 -> context
                                                                        |
                                                                     project3
                                                                        | 2x event fanout
                                                                        v
                                                          x2 --------> concat -> decoder2_fuse
                                                                                   |
                                                                                project2
                                                                                   | 2x fanout
                                               x1 ------------------------------> multiplicity sum
                                                                                   | 2x fanout
                                                                                   +----> final concat
                                                                                              |
                                                                                         final_fuse
                                                                                              |
                                                                                         class current
```

Completion tokens follow the **same DAG** as spikes. A fork copies the token to every
outgoing branch. A join may forward its 5 ms completion token only after all required
upstream branches have delivered the **same bin tag**; otherwise a fast branch could make a
downstream PLIF commit before a slower skip branch has contributed. Residual joins and
decoder joins therefore have different data rules but the same completion rendezvous rule:

- residual joins: binary OR / deduplicate coincident spike addresses;
- `decoder2` and final concatenations: preserve all events after fixed channel remapping;
- `project2 + x1`: deliberately preserve coincident events as multiplicity two;
- all joins: wait for all required upstream completion tokens for the bin.

## Inhibition and threshold-adaptation dynamics

### Peer-membrane inhibition

Stem-only `peer_membrane` inhibition is enabled. Its exact software rule uses a
retinotopic RMS-like membrane-energy term across feature channels and subtracts a
learned scaled decrement from peer membranes after a local spike event. This is more complex than basic PLIF and is an ASIC cost item because it needs
retinotopic cross-channel state access and extra arithmetic. The ASIC RTL must
match the fixed-point reference exactly; a cheaper approximation is allowed only with
explicit accuracy revalidation.

### Triangular threshold adaptation

Triangular threshold adaptation is enabled on `down2`, `enc2`, `enc2_extra`, `down3`,
`enc3`, `enc3_extra`, `context1`, and `context2`. It is disabled on the full-resolution
Encoder-1/detail path and decoder. Each spiking neuron maintains adaptation age and
amplitude; the resulting retinotopic penalty is added to the base threshold. On ASIC, adaptation age/amplitude and the resulting dynamic threshold are integer/
fixed-point state. Their time course must match the exported integer reference exactly.

## Non-PLIF operations and ASIC treatment

The goal is a **digital neuromorphic ASIC**. The native SystemVerilog reference uses clocked
ready/valid channels, while actors are logically autonomous: sparse events flow immediately
and an ordered completion token closes each trained 5 ms epoch. Only nonzero spike locations
trigger connected synaptic fan-out/additions. It is not a dense ANN accelerator with PLIF
inserted only as an activation, and it does not threshold after every signed contribution.

| Software operation | Exact role | ASIC interpretation |
| --- | --- | --- |
| `ChannelAffine` | per-channel current gain | fold into quantized weight/scale before export |
| quarter skip concat | preserve encoder/decoder event identity until learned fusion | channel-ID remap into one 1x1 synaptic accumulator |
| half skip sum | preserve coincident spike evidence | route both events; values 0/1/2 in dense training are event multiplicity, not an analog activation |
| nearest upsample | duplicate spatial spike locations | event-address fan-out/remapping |
| `torch.cat` | concatenate channel groups | channel-ID/address remapping; no arithmetic |
| final `TemporalCurrentReadout` | signed 1x1 class evidence over ten hidden-spike slices | accumulate signed class current per pixel; no output PLIF state |
| argmax | final semantic label | signed comparator tree / sequential maximum; first-index tie behavior |
| DDD17 timestamp scheduler | reconstruct approximate timed deliveries | compatibility scheduler feeding the same 5 ms neural-time grid |

XL-only bridges, parallel context, attention, selector, and class-spike head are documented
separately below because they are not present in the exported v8 graph.

## Primary implementation goal: digital neuromorphic ASIC

The canonical deployment objective is:

1. keep PyTorch/SpikingJelly as the training and floating-point golden reference;
2. export only the **25-population executed v8 140k PLIF graph plus its stateless temporal-current readout** and its learned weights, beta, thresholds,
   inhibition, adaptation strength, and adaptation-duration parameters;
3. define deterministic fixed-point formats, rounding, saturation, and overflow rules;
4. build a bit-exact integer reference and verify layer currents, membranes, spikes, and
   semantic output against the float model;
5. instantiate one permanent SystemVerilog actor per executed layer; each owns convolution
   addressing, accumulator lanes, PLIF/mechanism logic, queue, and weight ROM;
6. store persistent membrane/adaptation state in actor-local characterized SRAM macros together
   with the compact lazy-update metadata required by the frozen integer contract;
7. implement touched-address queues and lazy `beta^Δk` state updates as baseline behavior because
   DSEC training already uses touched-neuron asynchronous updates inside the fixed 5 ms time grid;
8. run Icarus/cocotb RTL verification, Yosys mapping, OpenROAD place-and-route/parasitics, and
   representative-event SAIF/VCD power analysis;
9. use ASAP7 only for predictive research PPA and require real foundry SRAM libraries before full-chip signoff.

## Exact streaming 5 ms sparse layer procedure

Training remains unchanged. DSEC training groups raw events into fixed physical-time
updates, while ASIC ingress accepts those same rectified events sequentially in timestamp
order. The ASIC does not load a dense bin or sweep the full feature map. The 5 ms boundary
is represented by an ordered completion token and remains the PLIF semantic commit boundary.

For input bin `k`:

1. Rectify each raw event and multicast its polarity/spatial address to the two fixed
   ingress actors required by the real graph: `detail_stem` and `stem`. No complete-bin
   dense tensor is required.
2. Each receiving actor immediately generates only its connected convolution destinations
   from kernel, stride, padding, dilation and group rules and adds its static signed weights.
3. All synaptic contributions targeting the same logical neuron **within this bin** are
   accumulated before threshold/reset; the neuron is committed at most once for that layer/bin.
4. Read the destination's sparse state. A missing entry is exact reset state. A live entry
   provides `V`, optional adaptation age/amplitude, and `last_bin_tag`.
5. Compute `Δk = (current_bin_tag - last_bin_tag) mod 2^24`. For a live entry apply the
   exported learned beta exactly `Δk` times (equivalent to `beta^Δk`) before adding current.
   The initial RTL uses an iterative multiply loop; a LUT/power accelerator is a later
   performance optimization and must remain bit-exact.
6. Apply the trained threshold/adaptation/reset/inhibition order, write the new state with
   `last_bin_tag = current_bin_tag`, reclaim it only when quantized membrane is zero and
   adaptation is inactive, and emit only output spikes.
7. After the input epoch marker arrives, both ingress branches commit their touched neurons.
   Event/completion tokens then follow the fixed DAG. Fanout nodes multicast losslessly;
   residual/concat/skip joins wait for all required upstream completion tokens carrying the
   same bin tag before forwarding one downstream completion. The final completion emerges
   only after `final_fuse.standard` and the stateless 16->6 class-current update have seen
   all branches for that bin.
8. PLIF/adaptation state persists across epochs. Camera ingress may continue independently
   if its event FIFO provides sufficient lossless backpressure capacity.
9. Signed class current persists only across the configured prediction window. The default
   is ten bins, so a segmentation argmax is emitted every **50 ms / 20 Hz**, matching training.
   The prediction-window length is configurable for later latency/accuracy experiments.

This is raw-event sequential synaptic processing, but not immediate per-contribution PLIF
firing. Signed contributions within an epoch must be accumulated before threshold/reset;
otherwise convolution order changes the trained model. The active ordering is:

```text
raw events k arrive -> fork -> detail path + semantic path accumulate locally
5 ms marker k       -> token forks with those paths
                     -> residual/skip branches run independently
                     -> each join waits for every required token tagged k
                     -> final_fuse commits only after semantic + detail rendezvous
                     -> class-current update -> bin k retired
raw events k+1 may enter a lossless ingress FIFO concurrently
```

### Real-time utilization and throughput contract

Let `C_bin` be the measured ASIC clock cycles from accepting a sealed bin until the final
readout update for that bin completes, `f_clk` the achieved clock frequency, and
`T_bin = 5 ms` the input-bin period.

```text
hard_cycle_budget   = floor(f_clk * T_bin)
U                    = C_bin / hard_cycle_budget
H                    = hard_cycle_budget / C_bin = 1/U
compute_time         = C_bin / f_clk
prediction_period    = prediction_bins * 5 ms
```

Hard sustained real time requires:

```text
U <= 1.00
H >= 1.00
compute_time <= 5 ms
```

The starting design target reserves 20% timing margin:

```text
U_target <= 0.80
H_target >= 1.25
target_cycle_budget = floor(0.8 * hard_cycle_budget)
```

At common clocks this gives:

| Routed clock | Hard 5 ms budget | 80% target budget |
| ---: | ---: | ---: |
| 100 MHz | 500,000 cycles | 400,000 cycles |
| 150 MHz | 750,000 cycles | 600,000 cycles |
| 200 MHz | 1,000,000 cycles | 800,000 cycles |

The controller reports cycles/bin plus hard-deadline and target-budget misses. Sparse
activity, cache/bank conflicts, iterative lazy-leak cycles, event-FIFO stalls and actor
parallelism are therefore automatically reflected in `U`; a design that cannot sustain
`U <= 1` cannot consume a continuous 200-bin/s camera stream without backlog or loss.

## Static layer-actor ASIC execution

There is no requirement for one hardware PLIF circuit per logical `[C,H,W]` neuron, but
there is one permanent actor per executed PLIF population. These actors are connected by
the fixed v8 DAG rather than a linear pipeline. An actor can sequence local lanes over its
own destinations; those arithmetic blocks are never reused by a different PLIF population:

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

## Why the ASIC implementation is still neuromorphic

The implementation is fully digital, but it intentionally preserves the neuromorphic
computational model: stateful PLIF neurons, sparse spikes as inter-layer communication,
event-driven synaptic additions instead of multiplying every zero activation, shared
local receptive fields, temporal state continuity, and activity-dependent work. The
membrane/current values are fixed-point numerical representations of neuron state—not
physical voltages/currents—and this distinction must be explicit in the paper.

## Verification and reporting

The required chain is `SpikingJelly float -> bit-exact integer reference -> SystemVerilog RTL ->
Icarus/cocotb -> Yosys/OpenROAD post-route implementation`. Latency comes from event traces and the
achieved routed clock. Power uses representative DSEC switching activity (SAIF/VCD), routed
parasitics, and characterized cells/macros. ASAP7 results are predictive research estimates;
only fabricated silicon measurements may be called measured ASIC power or latency.

## EventSpikeSegXL software comparison (not an ASIC target)

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

`T=10` below is the current software timing schedule. XL is not an ASIC export target; the
geometry is shown only to keep the software comparison accurate under the native 440x640 DSEC loader.
Raw DSEC events are accumulated into ten 5 ms slices before either model.

| Stage | Synaptic/spiking operation | Output `T,N,C,H,W` | PLIF populations |
| --- | --- | --- | ---: |
| input | rectified ON/OFF counts for training | `10,1,2,440,640` | 0 |
| stem | 3x3, 2->32, affine, PLIF | `10,1,32,440,640` | 1 |
| encoder-1 | two residual DW3x3/PW1x1 32-ch blocks | `10,1,32,440,640` | 4 |
| detail-1 | residual DW3x3/PW1x1 32-ch | `10,1,32,440,640` | 2 |
| detail-2 | DW3x1 -> DW1x3 -> PW1x1, residual | `10,1,32,440,640` | 3 |
| detail-3 | residual DW3x3/PW1x1 32-ch | `10,1,32,440,640` | 2 |
| down2 main | stride-2 DW32 -> PW64 | `10,1,64,220,320` | 2 |
| bridge12 | stride-2 1x1, 32->64; merge with down2 | `10,1,64,220,320` | 1 |
| encoder-2 | two residual DW/PW 64-ch blocks | `10,1,64,220,320` | 4 |
| down3 main | stride-2 DW64 -> PW128 | `10,1,128,110,160` | 2 |
| bridge23 | stride-2 1x1, 64->128; merge with down3 | `10,1,128,110,160` | 1 |
| encoder-3 | two residual DW/PW 128-ch blocks | `10,1,128,110,160` | 4 |
| serial context | two residual dilation-2 DW/PW 128-ch blocks | `10,1,128,110,160` | 4 |
| parallel context | DW3x3 d1/d2/d4, concat 384, 1x1->128, residual | `10,1,128,110,160` | 4 |
| local spike attention | Q/K/V 128->32, four heads x eight channels, 32->128 residual | `10,1,128,110,160` | 4 |
| project3 | 1x1 128->64, then nearest upsample | `10,1,64,220,320` | 1 |
| decoder-2 fusion | concat project3+x2=128; DW128 -> PW64 | `10,1,64,220,320` | 2 |
| decoder-2 refine | residual DW/PW 64-ch | `10,1,64,220,320` | 2 |
| project2 | 1x1 64->32, then nearest upsample | `10,1,32,440,640` | 1 |
| late merge | concatenate semantic32 + shallow32 + detail32 | `10,1,96,440,640` | 0 |
| local selector | 1x1 96->96 PLIF, retinotopic gate | `10,1,96,440,640` | 1 |
| final fusion | DW96 -> PW32 | `10,1,32,440,640` | 2 |
| decoder-1 refine | residual DW/PW 32-ch | `10,1,32,440,640` | 2 |
| class head | 1x1 32->11 independent class PLIFs | `10,1,11,440,640` | 1 |
| readout | sum class spikes over 50 ms, per-pixel argmax | `1,11,440,640` logits | 0 |

Training-only heads are `64->11` at 220x320 and `128->32->11` at 110x160. They are skipped
by `model.eval()` and omitted from ASIC export.

## Active autonomous ASIC runtime

There is no active global actor-index scheduler. Sparse events traverse the permanently
wired actor graph over ready/valid channels. After the final event belonging to a trained
5 ms epoch, the source injects an ordered completion token. Each receiving actor uses that
token as proof that all signed contributions for the epoch have arrived, commits every
touched PLIF exactly once, emits spikes, and forwards completion. The SystemVerilog RTL is a
clocked logical-asynchrony reference; a future clockless/QDI circuit would be a separate
physical implementation and validation step.

For one active input/output channel plane, `presynaptic_tap_array.sv` evaluates all kernel
taps in parallel. A 3x3 kernel therefore has nine tap projection cells. Each valid tap
emits `(destination_y, destination_x, signed_weight)` using the presynaptic scatter equation,
including stride divisibility, padding, dilation, bounds, and zero-weight suppression.
The receiving actor accumulates every tap into one canonical state indexed by output
channel and spatial location. Kernel taps never own membrane copies.

Each actor-local live state stores `last_bin_tag`. `plif_update.sv` accepts `elapsed_bins`
and implements the exact baseline lazy leak as repeated learned-beta fixed-point
multiplies before current integration.

### Actor-local state requirement

Int16 membranes + two int16 adaptation fields where enabled + a dense 24-bit last-bin tag
would require **189.60 MiB**. Actor ownership removes inter-layer state transport, but it
does not remove these bits. The complete implementation therefore requires actor-local,
characterized high-density SRAM macros; standard-cell registers are valid only for small
control/equivalence prototypes. A zero-default sparse organization remains an allowed
lossless SRAM representation:

```text
missing address == membrane 0 and inactive adaptation
live entry       == address/tag + membrane + last_bin_tag [+ age + amplitude]
```

A state may be reclaimed only when its **quantized** membrane is zero and adaptation is
inactive. Full associative sets assert overflow; live state is never silently evicted.
The conservative profiler uses 12-byte non-adaptive and 16-byte adaptive aligned entries;
these budgets include the compact bin tag. The selected SRAM compiler's LEF/liberty and
post-route OpenROAD reports are the physical authority.

A previous one-record profile is not a capacity proof. The v8 model must be profiled over
complete DSEC sequences and report per-layer high-watermarks, set conflicts, FIFO occupancy,
class-current accumulator occupancy, cycles/bin, utilization `U`, headroom `H`, and margin
before claiming no-DDR real-time fit.

### Active native SystemVerilog RTL blocks

- `asic/rtl/convolution_plif_actor.sv`: integrated static-kernel scatter and actor-local PLIF population;
- `asic/rtl/presynaptic_tap_array.sv`: parallel presynaptic tap scatter for one kernel plane;
- `asic/rtl/asynchronous_plif_actor.sv`: actor-local current/membrane/tag arrays, first-touch commits, and output backpressure;
- `asic/rtl/plif_update.sv`: learned-beta lazy PLIF with subtractive reset;
- `asic/rtl/peer_membrane_inhibition.sv`: retinotopic RMS-energy decrement for non-spiking peers;
- `asic/rtl/triangular_threshold_adaptation.sv`: per-neuron learned-amplitude inverted-V threshold state;
- `asic/rtl/class_current_update.sv`: signed class-current accumulation and prediction flush;
- `asic/rtl/class_argmax.sv`: first-index-tie signed argmax matching PyTorch behavior;
- `asic/rtl/event_fork2.sv`: lossless two-way multicast for events and completion tokens;
- `asic/rtl/event_join2.sv`: multiplicity-preserving two-input merge with same-bin completion rendezvous;
- `asic/rtl/binary_event_union2.sv`: correctness-reference residual binary-OR/dedup merge with same-bin completion rendezvous.
- `asic/rtl/event_channel_offset.sv`: fixed compile-time channel-ID remap for concatenation routes;
- `asic/rtl/event_upsample2x.sv`: nearest-neighbor 2x event-address expansion with one completion-token forwarding;
- `asic/rtl/channelized_convolution_scatter.sv`: standard/grouped/depthwise input-to-output-channel projection using PyTorch Conv2d weight order.
- `asic/rtl/channelized_convolution_plif_actor.sv`: channel-aware scatter integrated with canonical `(channel,y,x)` local state and per-channel beta/threshold tables.
- `asic/rtl/streaming_channelized_plif_actor.sv`: unified packed spike/completion-token interface used by generated graph wiring;
- `asic/rtl/plif_leak_charge.sv`: lazy learned-beta leak/current phase for grouped mechanism commits;
- `asic/rtl/retinotopic_mechanism_update.sv`: summed triangular-threshold and shared-RMS peer-inhibition commit across all channels at one location;
- `asic/rtl/retinotopic_asynchronous_plif_actor.sv`: touched-location grouped state engine for mechanism-enabled actors;
- `asic/rtl/temporal_class_readout.sv`: signed non-spiking 16-to-6 temporal current accumulation and dense prediction enumeration;
- `asic/rtl/actor_local_state_sram.sv`: behavioral/compiled-macro 1R1W SRAM binding boundary.

`scripts/generate_asic_top.py` now creates the complete structural 25-actor DAG directly from
the exported graph and ROM images. A reduced-state generated instance compiles and propagates
completion through every branch and join into the prediction boundary. Model-scale physical
implementation still requires replacing behavioral actor/readout arrays with characterized
SRAM macros, real-checkpoint full-DAG equivalence, and full-sequence activity, latency, and
energy measurement.

The 16->6 readout is not a spiking layer. Final hidden spikes trigger signed readout
weight additions at the same `(y,x)`. Class currents accumulate across the configured
prediction window (default ten 5 ms bins) and reset after each prediction; PLIF/adaptation
state continues across predictions until a sequence/gap reset.

## ASIC routing/control requirements for v8

- `project3` nearest upsample is event-address fan-out to quarter resolution; its channels
  are concatenated with encoder-2 and fused by `decoder2_fuse` before one PLIF threshold.
- `project2` nearest fanout is multiplicity-summed with encoder-1 at half resolution and
  then fanned out again to native resolution. Coincident events are not deduplicated.
- Late concatenation is only a channel-ID remap: semantic channels 0..31 plus detail 32..39.
- There is no v8 selector, attention rendezvous, projected bridge, or class-spike counter.
- The readout requires signed current accumulation and per-pixel 6-way argmax; common
  positive readout scaling may be skipped for class selection.
- Persistent state is actor-local SRAM. Full-scale implementation requires characterized
  SRAM macros; behavioral arrays are used only for RTL control/equivalence checks.
- Verification compares float -> integer -> RTL at layer currents, membrane/adaptation
  trajectories, emitted hidden spikes, final signed class-current accumulators, and argmax.

## Canonical naming

- `EventSpikeSeg140k`: only six-class DSEC/ASIC implementation target.
- `EventSpikeSegXL`: software-only capacity comparison; rejected by ASIC export.

Historical top-ten/top-five/top-three architecture-search results retain their original
names and measured values.

Published source terminology is retained only when citing the source or preserving a
historical experiment identifier. Active software, exported model specifications, and RTL
use `peer_membrane_inhibition`, `triangular_threshold_adaptation`, and
`adaptation_duration`.
