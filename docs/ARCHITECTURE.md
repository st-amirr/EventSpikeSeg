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

The active resident mapping uses one signed int32 Q15.16 combined accumulator/state value per PLIF. A
6-bit integer-bin age plus 19-bit unsigned Q3.16 amplitude is present only where adaptation is
enabled, so exact logical state totals **150.89 MiB-equivalent**. At completion the accumulator is
thresholded/reset and then receives the learned beta step for the next 5 ms bin; there is no
separate permanent current or membrane array. For ASIC deployment this is a direct standard-cell/register/latch area, clock,
and routing problem—not an FPGA BRAM or runtime-SRAM capacity requirement. Full-chip PPA must
place, route, and power this complete direct-state design.


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

The active RTL stores this equation in one signed int32 Q15.16 combined element `A`. Immediately
after a commit it stores `A = round(beta_q * V_committed)`; all signed contributions for
the following bin add directly to `A`; the next completion clamps `A` to signed 24-bit Q7.16 for
threshold/reset/mechanism evaluation and again pre-applies beta. Thus the logical equation
is unchanged without separate permanent current and membrane arrays. This equivalence assumes
the int32 accumulator does not saturate; overflow counters and semantic validation remain required.

`beta_q`, thresholds, combined state, synaptic contributions, and adaptation state use
integer/fixed-point values under one frozen rounding/saturation contract. The first
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

Each adaptation-enabled neuron owns `adaptation_age` and `adaptation_amplitude`. The active
resident implementation gives every PLIF one int32 Q15.16 combined accumulator/state element; it
does not keep a second membrane or current array. An ordered completion token advances all PLIFs
exactly once per 5 ms epoch, so it needs no touched-neuron tag or lazy
elapsed-bin calculation.

The exact resident-state inventory is therefore:

| State | Values | Storage |
| --- | ---: | ---: |
| combined accumulator/state, signed int32 Q15.16 | 30,976,000 | 118.16 MiB |
| adaptation age, unsigned 6-bit integer bins | 10,982,400 | 7.85 MiB |
| adaptation amplitude, unsigned 19-bit Q3.16 | 10,982,400 | 24.88 MiB |
| exact resident-state total | — | **150.89 MiB-equivalent** |

These bits are distributed register/latch state beside their PLIF update logic, not an addressed
byte store or SRAM capacity request. Full-chip PPA must include all of them; a reduced tile result
cannot establish full-model feasibility.

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
This is the intended state-first hardware design direction: static int24 Q7.16 weights remain small;
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
| compact `last_bin_tag` | absent; completion advances every resident PLIF |
| synaptic current accumulator | independent resident int24 state per PLIF; cleared at commit |
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

XL-only bridges, parallel context, attention, and class-spike head are documented
separately below because they are not present in the exported v8 graph.

## Primary implementation goal: digital neuromorphic ASIC

The canonical deployment objective is:

1. keep PyTorch/SpikingJelly as the training and floating-point golden reference;
2. export only the **25-population executed v8 140k PLIF graph plus its stateless temporal-current readout** and its learned weights, beta, thresholds,
   inhibition, adaptation strength, and adaptation-duration parameters;
3. define deterministic fixed-point formats, rounding, saturation, and overflow rules;
4. build a bit-exact integer reference and verify layer currents, membranes, spikes, and
   semantic output against the float model;
5. instantiate one permanent SystemVerilog actor per executed layer and spatially tile it; every
   logical PLIF owns one local combined accumulator and optional compact adaptation registers/latches;
6. implement convolution as compile-time weighted connectivity from each tile's exact input
   receptive halo, with no runtime weight or state-memory transaction;
7. send ordered completion tokens through the same DAG as spikes and apply exactly one learned-beta
   update to every resident PLIF at each 5 ms boundary;
8. run Icarus/cocotb RTL verification, Yosys mapping, OpenROAD place-and-route/parasitics, and
   representative-event SAIF/VCD power analysis;
9. use ASAP7 only for predictive research PPA and require a manufacturable foundry standard-cell/
   latch library before tapeout signoff.

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
   from kernel, stride, padding, dilation and group rules and adds its static signed Q7.16 weights.
3. All synaptic contributions targeting the same logical neuron **within this bin** accumulate
   directly in that PLIF's resident int32 Q15.16 combined accumulator/state element.
4. After the input epoch marker arrives, both ingress branches commit every resident PLIF once.
   Each PLIF clamps the combined value to the membrane grid, applies the trained threshold,
   clocked mechanism, and reset order, then pre-applies the learned beta for the next bin and
   emits only output spikes. There is no separate current clear or membrane write.
5. Event/completion tokens then follow the fixed DAG. Fanout nodes multicast losslessly;
   residual/concat/skip joins wait for all required upstream completion tokens carrying the
   same bin tag before forwarding one downstream completion. The final completion emerges
   only after `final_fuse.standard` and the stateless 16->6 class-current update have seen
   all branches for that bin.
6. No state address, sparse-table lookup, reclaim operation, `last_bin_tag`, or state SRAM
   transaction occurs on this active path.
7. PLIF/adaptation state persists across epochs. Camera ingress may continue independently
   if its event/vector buffering provides sufficient lossless backpressure capacity.
8. Signed class current persists only across the configured prediction window. The default
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
activity, vector handshakes, completion-token stalls, resident commit latency and actor
parallelism are therefore automatically reflected in `U`; a design that cannot sustain
`U <= 1` cannot consume a continuous 200-bin/s camera stream without backlog or loss.

## Static layer-actor ASIC execution

There is one permanent actor per executed PLIF population and one physically distinct state
identity per logical `[C,H,W]` PLIF. These actors are connected by the fixed v8 DAG rather than
a linear pipeline. The active direct-state architecture spatially partitions each actor into
8x8 output tiles without sharing or addressing their state:

```text
spike bitmap -> compile-time receptive-halo wiring -> fixed-weight synaptic sums
             -> local current registers -> fixed-step resident PLIF commit
             -> resident membrane/adaptation registers -> output spike bitmap
```

Each tile receives only the exact clamped input rectangle needed by its convolution receptive
fields. Global coordinates are converted to tile-local halo coordinates at elaboration, so this
is static physical connectivity rather than a runtime fetch. A border halo can overlap the halo
of an adjacent output tile, but no membrane/current/adaptation state is duplicated by that
overlap. Kernel weights and per-channel beta/threshold values are compile-time constants.

Every 5 ms completion token causes exactly one learned-beta commit in every resident PLIF. Current
registers clear after commit; membrane and enabled adaptation registers persist across epochs.
There is no state address, tag lookup, cache, SRAM read/write, reconfiguration, or reclaim policy
in the active path. Common clock/reset and completion routing are shared infrastructure, not shared
state or layer compute. The cost is the physical area and clock/reset load of roughly 31 million
logical PLIF state/update datapaths; spatial tiling controls hierarchy and wiring locality but does
not reduce that state inventory.

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
| DDD17, 6 classes, registered module | 978,559 |
| DSEC, 11 classes, registered module | 979,179 |
| DSEC executed training forward | 974,123 |
| DSEC executed inference graph | 968,831 |
| inherited dead `refine2`, omitted | 5,056 |
| mid auxiliary head, training only | 726 |
| deep auxiliary head, training only | 4,566 |

The DSEC inference parameters split into 959,824 shared convolution weights, 2,984
foldable affine gains, 2,984 PLIF beta values, 2,984 PLIF base thresholds, four attention
comparison thresholds, one inhibition strength, and 25 pairs of threshold-adaptation
strength/duration parameters. The inference graph contains 44 PLIF populations; training
adds three auxiliary populations, while the registered dead block contains two more.

At native 440x640 DSEC resolution, XL owns 78,707,200 inference membrane elements:
168 channel-populations at 440x640, 160 at 220x320, 640 at 110x160, and 2,016 at
55x80. This is a deliberate middle ground: 63.5% fewer membrane elements than the
wide-everywhere XL layout, while retaining a multi-stage native detail path. The
15,910,400 adaptation-enabled neurons remain confined to semantic encoder/context scales.

Any future XL ASIC must use the same clocked combined-state contract: signed int32 Q15.16 accumulator,
6-bit integer age, and unsigned 19-bit Q3.16 amplitude. This calculates to **347.66
MiB-equivalent** for XL, compared with 436.00 MiB under the former separate int24-current,
int16-membrane, and two-int16-adaptation representation. XL export remains rejected until the
140k implementation is fully validated and an explicit XL export/RTL verification project is approved.

### XL ASIC migration procedure

XL is not a parameter-only replacement for the 140k netlist. Most arithmetic actors are reusable,
but its graph and one operation class are different. Promotion requires these gates in order:

1. Complete XL training and epochs 78--80 QAT, then select the best checkpoint using fixed-point
   validation. Do not freeze an RTL graph from an epoch-1 or floating-point-only checkpoint.
2. Generalize the exporter from the hard-coded six-class/25-actor 140k contract to an explicit
   XL contract with 44 inference PLIF actors, 11 classes, 959,824 shared convolution weights,
   24-to-11 temporal readout, and training-only auxiliary heads omitted.
3. Write and validate the exact XL DAG: projected `bridge12`/`bridge23` residual joins, two semantic
   capacity blocks, three-way parallel dilated context, asymmetric detail kernels, decoder refinement,
   fanout, concatenation, binary residual joins, and completion-token rendezvous.
4. Reuse the existing fixed convolution/PLIF/tile/readout RTL for ordinary 1x1, 3x3, rectangular
   depthwise, strided, and dilated actors. Add one new spike-attention primitive: per spatial location,
   form Q/K coincidence popcounts for four eight-channel heads, compare each count with its exported
   fixed threshold, gate V spikes, and rendezvous before the existing 1x1 output actor and residual join.
5. Extend the integer reference, capacity manifest, tile planner, top generator, and replay tooling so
   none assumes 25 actors, six classes, a 16-channel readout, or the 140k-only topology module.
6. Prove layerwise FP32/QAT -> integer -> RTL equivalence, followed by the complete 5 ms event interval
   and ten-bin/50 ms prediction. Only then attempt full-graph elaboration and activity-annotated PPA.

The software/export work is moderate, the attention/rendezvous RTL is moderate-to-hard, and the
physical implementation is hard. XL has about 2.30 times the resident state of 140k (347.66 versus
150.89 MiB-equivalent), 44 versus 25 PLIF actors, and about 2.75 MiB of signed 24-bit convolution
weights. The state/routing/clock-tree scale—not weight ROM size—is the main feasibility risk.

### Native DSEC layer graph and dimensions

`T=10` below is the current software timing schedule. XL is not an ASIC export target; the
geometry is shown only to keep the software comparison accurate under the native 440x640 DSEC loader.
Raw DSEC events are accumulated into ten 5 ms slices before either model.

| Stage | Synaptic/spiking operation | Output `T,N,C,H,W` | PLIF populations |
| --- | --- | --- | ---: |
| input | rectified ON/OFF counts for training | `10,1,2,440,640` | 0 |
| native detail | 2->16 stem, residual DW/PW, asymmetric DW/DW/PW | `10,1,16,440,640` | 6 |
| semantic stem | learned 5x5 stride-2, 2->32, affine, PLIF | `10,1,32,220,320` | 1 |
| encoder-1 | two residual DW3x3/PW1x1 32-ch blocks | `10,1,32,220,320` | 4 |
| down2 main | stride-2 DW32 -> PW64 | `10,1,64,110,160` | 2 |
| bridge12 | stride-2 1x1, 32->64; merge with down2 | `10,1,64,110,160` | 1 |
| encoder-2 | two residual DW/PW 64-ch blocks | `10,1,64,110,160` | 4 |
| down3 main | stride-2 DW64 -> PW128 | `10,1,128,55,80` | 2 |
| bridge23 | stride-2 1x1, 64->128; merge with down3 | `10,1,128,55,80` | 1 |
| encoder-3 | residual DW/PW then full 3x3 128-ch refinement | `10,1,128,55,80` | 3 |
| serial context | two residual full 3x3 dilation-2 128-ch blocks | `10,1,128,55,80` | 2 |
| semantic capacity | two residual full 3x3 128-ch blocks | `10,1,128,55,80` | 2 |
| parallel context | DW3x3 d1/d2/d4, concat 384, 1x1->128, residual | `10,1,128,55,80` | 4 |
| local spike attention | Q/K/V 128->32, four heads x eight channels, 32->128 residual | `10,1,128,55,80` | 4 |
| project3 | 1x1 128->64, then nearest upsample | `10,1,64,110,160` | 1 |
| decoder-2 fusion | concat project3+x2=128; full 3x3 ->64 | `10,1,64,110,160` | 1 |
| decoder-2 refine | residual DW/PW 64-ch | `10,1,64,110,160` | 2 |
| project2 | 1x1 64->32, merge x1, then upsample | `10,1,32,220,320` | 1 |
| late merge | concatenate semantic32 + native detail16 | `10,1,48,440,640` | 0 |
| final fusion | full 3x3 48->24 | `10,1,24,440,640` | 1 |
| decoder-1 refine | residual DW/PW 24-ch | `10,1,24,440,640` | 2 |
| class readout | 1x1 24->11 signed current accumulated over 50 ms | `1,11,440,640` logits | 0 |

Training-only heads are `64->11` at 220x320 and `128->32->11` at 110x160. They are skipped
by `model.eval()` and omitted from ASIC export.

## Active autonomous ASIC runtime

There is no active global actor-index scheduler. Sparse events traverse the permanently
wired actor graph over ready/valid channels. After the final event belonging to a trained
5 ms epoch, the source injects an ordered completion token. Each receiving actor uses that
token as proof that all signed contributions for the epoch have arrived, commits every
resident PLIF exactly once, emits spikes, and forwards completion. The SystemVerilog RTL is a
clocked logical-asynchrony reference; a future clockless/QDI circuit would be a separate
physical implementation and validation step.

`resident_convolution_synapses.sv` evaluates the fixed Conv2d connectivity in parallel. A 3x3
kernel has nine static tap projections; an asserted input bit gates its corresponding signed
weight into the canonical local current register. The receptive-halo wrapper applies stride,
padding, dilation, grouping, bounds, and tile-coordinate mapping at elaboration. Kernel taps
never own membrane copies or runtime weight storage.

### Actor-local state requirement

The signed int32 Q15.16 combined accumulator plus optional 6-bit age and 19-bit amplitude require
**150.89 MiB-equivalent** of permanent local state. Actor ownership removes inter-layer state
transport and runtime state fetches, but does not remove these physical bits. Every state element
is a dedicated standard-cell register/latch beside its PLIF logic; it is never reclaimed, aliased,
or indexed through a sparse table. The complete physical implementation must therefore measure
register/latch area, clock/reset distribution, routing, and switching activity rather than
substituting an SRAM-capacity estimate.

A previous one-record profile is not a capacity or real-time proof. The v8 model must be exercised
over complete DSEC sequences and report event/vector occupancy, completion-token backpressure,
cycles/bin, utilization `U`, headroom `H`, and activity-annotated energy before claiming sustained
operation.

### Active native SystemVerilog RTL blocks

- `asic/rtl/resident_convolution_synapses.sv`: compile-time standard/grouped/depthwise weighted
  connectivity into one current delta per resident destination;
- `asic/rtl/resident_plif_population.sv`: direct resident combined-accumulator PLIF commit;
- `asic/rtl/resident_retinotopic_plif_population.sv`: direct resident inhibition/adaptation commit;
- `asic/rtl/resident_channelized_plif_actor.sv`: one resident convolution/PLIF actor tile;
- `asic/rtl/tiled_resident_channelized_plif_actor.sv`: exact receptive-halo spatial hierarchy;
- `asic/rtl/resident_spike_vector_*.sv`: fixed vector fork, route, union, edge, and upsample
  operations with completion-token rendezvous;
- `asic/rtl/streaming_resident_channelized_plif_actor.sv`: vector/completion interface used by
  generated DAG wiring;
- `asic/rtl/resident_temporal_class_readout.sv`: resident signed non-spiking 16-to-6 temporal
  current accumulation and argmax.

The scalar scatter, banked, and SRAM blocks remain tracked only as historical/equivalence
references. They are not the active physical implementation or PPA target.

`scripts/generate_asic_top.py` creates the complete structural 25-actor DAG directly from
the exported graph and compile-time constants. A reduced-state generated instance compiles and
propagates completion through every branch and join into the prediction boundary. Model-scale
physical implementation still requires full resident-graph elaboration, routing, and
activity-annotated DSEC measurement. Historical SRAM-integrated reduced-geometry replay remains
an equivalence reference, not a native PPA result.

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
- Persistent state is actor-local direct combined-accumulator/compact-adaptation registers or latches; full-scale
  implementation must route and clock the complete resident state inventory.
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
