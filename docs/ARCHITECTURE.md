# EventSpikeSeg Architecture

## Analog synapse decision review — 2026-09-24

Use a signed charge-per-presynaptic-event interface on the active SKY130 prototype. Continue the existing pulse-duration injector as the first candidate; switched-capacitor charge injection is the conditional alternative, not a more inherently SNN-faithful implementation. Do not use pulse-density error feedback across semantic bins or future events. Weight determines a connection's contribution; it does not independently set presynaptic firing frequency. Internal subpulses are implementation phases, not extra network spikes, and must finish within the same update.

The primary analog reference is the full-float seed-17 EventSpikeSeg140k best-validation checkpoint from the 80-epoch training run: `artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt`, epoch 58 / best epoch 58, SHA-256 `c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7`. The epoch-80 checkpoint is retained as a comparison, not the primary reference, because its metadata says `is_best=false`. Neither checkpoint contains ASIC-QAT provenance fields; analog work does not require QAT or a quantized reference. Float32 storage also does not imply that analog hardware must attain float32 numerical accuracy; its acceptable error is to be established from float-model state, spike and output sensitivity.

At the update boundary, reproduce the float model's signed weighted sum, learned beta, threshold/reset, inhibition and adaptation order. For this model's ordinary PLIF path, the installed SpikingJelly configuration uses `decay_input=False`, so its charge equation is `candidate = beta * previous_post_reset_state + weighted_current`; beta multiplies the old state only. Apply beta exactly once, threshold after the bin's contributions, and preserve raw-event multiplicity at ingress. Do not add QAT conventions or use a quantized export in the analog reference path.

The bin-based contract means finite pulse duration is not automatically less faithful than a capacitor packet: integrated signed charge and completion before the 5 ms boundary are decisive. Charge delivery, saturation, uncommanded droop and order effects must still be measured. Preserve all digital/XL artifacts and keep their campaigns stopped; no new Markdown files or full-model SPICE campaign.


## Full analog implementation delegation — 2026-09-23

The user now authorizes Grok to perform the full ASAP7 analog/mixed-signal workflow, including design, debug, per-module simulation, physical macro generation, full assembly and ORFS execution once readiness passes. `docs/ACTIVE_TASKS.md` is the authoritative staged task plan. Earlier Grok-test-only and blanket no-ORFS instructions are superseded. Keep digital/XL jobs paused and all artifacts preserved. Use existing docs and YAML only. Approximate research estimates are allowed with explicit evidence/coverage; full layout still requires real implemented macros and validated assembly.


## ASAP7 analog readiness — 2026-09-23

The user requested ASAP7 and eventual full ORFS preparation. The complete PDK has now been fetched and pinned: umbrella d24f8b857ff74cf5b21ab18a7e1b11a3954c449b, device PDK 58d72c9d291e186a77468586ab0c43d8a21eda6a. Its unmodified TT card declares HSPICE level 72, BSIM-CMG version 107. A one-inverter probe fails in installed ngspice 36 with unsupported model level; no ASAP7 transistor result is accepted. Host/WSL/container checks found no HSPICE, Calibre, Xyce or OpenVAF.

An open-source path exists through ngspice >=39 OSDI/OpenVAF, but the currently inspected VA-Models tree supplies BSIM-CMG 111.2.1, not the original 107 card's model version. Do not silently change the model level/version or drop unsupported parameters and call it validated ASAP7. Establish a compatible model implementation/parameter mapping and benchmark before analog PPA claims. User tool-access clarification is pending; commercial tools are not assumed available.

The PDK's Calibre DRC/LVS/PEX directories contain download instructions rather than the rule decks. A physically qualified capacitor, completed analog macro netlists/layouts, LEF/Liberty views, extraction evidence and a conserving full-model assembly remain missing. ORFS accepts hardened macro views; it does not synthesize the behavioral SPICE library into analog layouts. Full ORFS is NOT ready, and no launch command is advertised as ready. Check: `python scripts/check_asap7_analog_ready.py` (expected exit 2 and explicit missing prerequisites). Evidence: artifacts/analog_asic/asap7/readiness.json and results/device_probe.log. The check is intentionally read-only with respect to physical campaigns and cannot launch a placeholder chip.

Preserve the SKY130 prototype as a separate experiment and all digital checkpoints. No extra Markdown documents were created. Next: resolve tool/model path, implement and qualify ASAP7 analog macros, then prepare/validate the ORFS assembly. Do not route empty boxes or use SKY130 physical views on ASAP7.

Sources: https://ngspice.sourceforge.io/osdi.html ; https://github.com/The-OpenROAD-Project/asap7 ; https://openroad-flow-scripts.readthedocs.io/en/latest/user/FlowVariables.html .


## Active approach override — 2026-09-23

User authorized analog/mixed-signal 140k feasibility as the active approach. Follow docs/ARCHITECTURE.md and write outputs to artifacts/analog_asic. Digital-only/register-state rules below now describe the preserved digital fallback, not restrictions on this analog experiment. Analog approximations and scaled estimates are allowed with explicit limitations; distinguish ideal, schematic, extracted and full-chip evidence. Preserve all digital/XL artifacts and keep their jobs paused. Prior active work is in docs/PROGRESS.md.


## Active implementation model

`EventSpikeSeg140k` is the six-class baseline DSEC/ASIC implementation target. Revision v8
uses the native **440x640** semantic plane and has **149,835 registered parameters**,
**149,423 executed inference parameters**, **143,824 executed synaptic weights**, and
**25 executed PLIF populations plus one stateless temporal class-current readout**.
`EventSpikeSegXL` is a secondary eleven-class ASIC reference target; primary layout,
simulation and estimates use the 140k checkpoint and inventory. Preserve useful XL
physical views and reports separately under `artifacts/ASIC_XL/`. Its epoch-1 checkpoint is used only
for structural export/RTL bring-up while training continues; final constants must come from
the selected trained/QAT checkpoint before accuracy or PPA claims.

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

## Secondary EventSpikeSegXL reference and software comparison

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

The XL ASIC uses the same clocked combined-state contract: signed int32 Q15.16 accumulator,
6-bit integer age, and unsigned 19-bit Q3.16 amplitude. This calculates to **347.66
MiB-equivalent** for XL, compared with 436.00 MiB under the former separate int24-current,
int16-membrane, and two-int16-adaptation representation. The exporter, exact DAG, spike-mask
attention RTL, capacity/tile manifests, and generated resident top now support XL; synthesis
and final-checkpoint equivalence remain gated.

### Deferred secondary XL ASIC migration procedure

XL is not a parameter-only replacement for the 140k netlist. Most arithmetic actors are reusable,
but its graph and one operation class are different. Promotion requires these gates in order:

1. Complete XL training and the final three-epoch QAT stage, then select the best checkpoint using
   fixed-point validation. Epoch 1 freezes architecture/shape plumbing only, never final constants.
2. **Implemented:** generalize the exporter from the hard-coded six-class/25-actor 140k contract to an explicit
   XL contract with 44 inference PLIF actors, 11 classes, 959,824 shared convolution weights,
   24-to-11 temporal readout, and training-only auxiliary heads omitted.
3. **Implemented:** write and validate the exact XL DAG: projected `bridge12`/`bridge23` residual joins, two semantic
   capacity blocks, three-way parallel dilated context, asymmetric detail kernels, decoder refinement,
   fanout, concatenation, binary residual joins, and completion-token rendezvous.
4. **Implemented and compile-checked:** reuse the existing fixed convolution/PLIF/tile/readout RTL for ordinary 1x1, 3x3, rectangular
   depthwise, strided, and dilated actors. Add one new spike-attention primitive: per spatial location,
   form Q/K coincidence popcounts for four eight-channel heads, compare each count with its exported
   fixed threshold, gate V spikes, and rendezvous before the existing 1x1 output actor and residual join.
5. **Implemented for export/capacity/tile/top generation:** remove 25-actor, six-class,
   16-channel-readout, and 140k-only topology assumptions. Use focused block equivalence;
   whole-model replay is retired and must not be restarted.
6. **Historical integer actor-DAG evidence (whole-model simulation retired):** the exported epoch-1 graph completed a real-event
   ten-bin/50 ms run actor by actor and emitted a 440x640 prediction. Serial and parallel integer
   execution are state/output equivalent. Layerwise final-checkpoint FP32/QAT -> integer -> RTL
   equivalence, cycle-accurate RTL execution, and activity-annotated PPA remain open.

The software/export work is moderate, the attention/rendezvous RTL is moderate-to-hard, and the
physical implementation is hard. XL has about 2.30 times the resident state of 140k (347.66 versus
150.89 MiB-equivalent), 44 versus 25 PLIF actors, and about 2.75 MiB of signed 24-bit convolution
weights. The state/routing/clock-tree scale—not weight ROM size—is the main feasibility risk.

The completed integer oracle stores these same logical fields in dense typed host arrays solely
to avoid Python-object overhead; this does not change the ASIC's resident-state count or precision.
Its four-worker Docker run processes disjoint output-channel ranges and deterministically merges
them in original event/tap order. Ten chronological bins took 15,308.731 host seconds. This host
runtime is not an ASIC latency estimate, and its activity counters are not energy without an
RTL/gate VCD/SAIF and characterized post-route power model.

### Native DSEC layer graph and dimensions

`T=10` below is the shared software/ASIC timing schedule. The geometry is the exact native
440x640 XL export contract.
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
- `asic/rtl/resident_temporal_class_readout.sv`: parameterized resident signed non-spiking
  16-to-6 (140k) or 24-to-11 (XL) temporal current accumulation and argmax;
- `asic/rtl/resident_spike_mask_attention.sv`: XL four-head Q/K spike-coincidence threshold
  and V-gating primitive.

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

- `EventSpikeSeg140k`: six-class baseline DSEC/ASIC implementation target.
- `EventSpikeSegXL`: secondary eleven-class ASIC reference, structurally prepared from epoch 1
  while final trained/QAT constants and synthesis are pending.

Historical top-ten/top-five/top-three architecture-search results retain their original
names and measured values.

Published source terminology is retained only when citing the source or preserving a
historical experiment identifier. Active software, exported model specifications, and RTL
use `peer_membrane_inhibition`, `triangular_threshold_adaptation`, and
`adaptation_duration`.


## Analog ASIC feasibility plan — 2026-09-23

## Scope
Primary experiment: EventSpikeSeg140k v8 epoch 80 seed 17, six classes, 440x640, 25 actors, 54 graph edges and 30,976,000 membrane identities. Keep local per-layer state and exact inventory, no cross-layer state sharing. Write all analog outputs in artifacts/analog_asic. Preserve digital ASIC and secondary XL data unchanged as fallback.

Goal: per-module analog/mixed-signal simulation and reusable layouts, scaled full-model estimates, then feasibility-gated full assembly. A full architectural floorplan is not a routed chip. The user permits analog approximations informed by SpikingJelly; do not claim bit-exactness or accuracy equivalence. Training dtype does not determine ADC resolution. A purely analog membrane-to-spike path does not need an ADC; converter boundaries and precision remain design variables.

## Model-to-circuit contract (Stage 2, 2026-09-23)

Authoritative machine-readable copy: `artifacts/analog_asic/design.yaml` (`circuit_contract`, `asap7_encoding`, `pending_physical`) and `artifacts/analog_asic/asap7/circuit_contract.json`. Stimuli: `asap7/stimuli/`.

- Sampled 5 ms phases (nonoverlapping; hold spike across commit): accumulate → snapshot → threshold → reset/inhibition → adaptation → learned beta once → hold.
- ASAP7 encoding provisional: VDD=0.7 V, vcm=0.35 V, smoke 0.07 V per model unit. The bounded 8-finger MOSFET-Cgg experiment drifts −0.197 V (−2.816 units) over 5 ms and fails the provisional 0.02-unit limit; Option B is not accepted and must not be scaled. See `docs/RESULTS.md` and `artifacts/analog_asic/asap7/capacitor_qualification.json`.
- Export ranges (quantized): beta ≈0.323..0.975; threshold ≈0.286..0.766; weights absmax up to ≈68.4 on final_fuse — use shared-cell variants, not one scale for every layer.
- Reset: subtractive (`v_reset=None`); readout: 16→6 signed current over 10 bins, first-index-tie argmax, no class PLIF.
- Acceptance tiers: circuit smoke 0.02 (smoke-only); module spike/state criteria TBD after transistor integration; workload accuracy not claimed.
- Pending physical placeholders: logistic compare, finite-gm sense, ideal C, B-source synapses, beta/reset drivers, adaptation/inhibition energy, readout argmax, on-chip phases.

## Tasks, in order
1. COMPLETE: stop digital workers, preserve stopped containers and durable stage files; source-linked 140k inventory; 80-bin ideal sampled ordinary PLIF equation smoke test. This is not transistor simulation or model accuracy validation.
2. Schematic tools ready: ngspice 36 and existing KLayout; pinned SKY130 NFET/PFET models load successfully. Capacitor devices and complete analog DRC/LVS/extraction support still need qualification. Do not assume ASAP7 digital cell libraries supply validated analog devices. Record any technology change; comparisons across PDKs are not controlled architecture comparisons. Stop for a decision if models/licenses are unavailable.
3. COMPLETE (Stage 2): Verify checkpoint/model equations and export small representative per-module SpikingJelly stimuli. Existing inventory/ideal smoke uses quantized digital exports, not the original float checkpoint. Start with detail_stem channel PLIF, signed charge injection, programmable leak, threshold and subtractive reset. Preserve bin-boundary sampled semantics initially; label continuous-time alternatives explicitly. Select voltage range, capacitor and precision from sensitivity, not training dtype. Define tolerated error before claiming equivalence. No full-model hardware replay.
4. Implement ONE transistor PLIF and signed synapse injection circuit using real PDK models. Run bounded SPICE transient checks for signed accumulation, idle retention/leak, threshold, reset, pulse/settling delay and supply energy integral V*I. Include bias/conversion overhead; capacitor energy alone is not total power. Add process/voltage/temperature and mismatch checks where models support them. After repeated failures, isolate the cause and follow the current stop conditions in docs/ACTIVE_TASKS.md; do not repeat identical retries.
5. Lay out that reusable cell, DRC/LVS, extract and resimulate before replication. Keep ideal, schematic and extracted results distinct. No full-chip run before this gate passes.
6. Cover inhibition, adaptation, signed weight delivery, routing/control and six-class temporal readout with separate module evidence. Label mixed-signal/digital helpers; do not reuse incompatible-PDK physical views. Missing coverage must remain explicitly unknown.
7. Scale from exact 140k counts and measured/model-derived activity, with sensitivity ranges for unknown activity. Report energy/event, energy/bin, idle/static power and latency separately. Derive latency from graph dependencies, bandwidth, contention and settling. The 50 ms observation window is not circuit propagation delay. Include mechanisms, interconnect and conversion overhead or mark exclusions.
8. Produce a hierarchical full-model floorplan/instance plan using reusable blocks without flattening 31 million neurons. Assess area, analog integrity, routing and host/tool capacity before full physical assembly. If infeasible, document the limits and continue analog alternatives; return to digital only on the user's explicit instruction. Do not promise hours-to-full-layout.

## Reproducibility and evidence
Run `python scripts/prepare_analog_asic.py`. This creates inventory.json, ideal_plif_trace.csv and ideal_plif_result.json in artifacts/analog_asic. The 80-bin check uses normalized signed mathematical state, learned quantized detail_stem beta/threshold, ideal sampled subtraction/reset, and no noise/saturation/mechanisms. Physical voltage common-mode/differential representation is not selected. The listed equivalent decay time constant does not make continuous event-time leak bin-equivalent. Power, area and latency are null until supported.

Digital resume: docs/PROGRESS.md and artifacts/ASIC/digital_pause_20260923. No deletions or automatic digital/XL restarts. Update ACTIVE_TASKS and PROGRESS as gates complete.

First-touch analog candidate (2026-09-29): hold each untouched differential membrane at the model-zero common mode, then open both physical clamps before the first signed weighted injection. A local two-phase event path must release ahead of the MOS pulse; nominal TT10µm MIM/TG testing preserves the event charge with0.2ns lead and fails badly at onset or later. Subsequent PLIF updates must keep the membrane floating and preserve subtractive reset. This is a candidate state-initialization sequence, not a qualified solution: the replay assumes ideal detection and switching, and circuit kT/C, local timing variation, 5ms retention, threshold/beta/adaptation and all-state service remain open. Details and measured bounds are in `docs/RESULTS.md`.

Selected SS/FF at0/85°C retain that release-order behavior, but the uncalibrated fixed gate delivers a37.3× single-event charge range. A3µm pair reduces bare resident MIM area to557.568mm² yet worsens the first-touch noise proxy enough to lower both sampled-frame IoUs substantially. Any implemented first-touch channel therefore needs a stable/calibrated signed event source and a denser or lower-noise state/reference solution before macro replication.

Exact-zero state allocation is not an immediate substitute for resident analog storage: on two complete float validation records,75–76% of all30.976m membranes are nonzero after the first update and82% after the tenth. A sparse pool would still need most state capacity and would add addressing/switching. The measured software occupancy does not include adaptation or hardware noise; see `docs/RESULTS.md`.

An ideal single-local-cap plus global-reference proxy halves the MIM count and improves the software first-touch noise response, but10µm cells still occupy3,097.6mm² bare over the full inventory. Physical reference distribution, switched noise, retention and single-ended threshold offset are unqualified. Keep this as a comparison bound rather than a macro specification.

The direct MOS injector also needs a nonlinear weight mapping across PVT. Solver-controlled fractions0.4/0.6 produce a1.62× spread in their charge ratio across selected corners; scalar gain adjustment cannot align both. A physical per-macro calibration/reference or a more stable charge source must be demonstrated before the ideal float weights can be bound to a gate DAC or replicated layout.

A fixed pulse width per PLIF stage may extend the current-amplitude encoding without making each static weight's pulse long. On the three sampled float patches, an illustrative worst-corner width ceiling is444.1ns and optimistic p99 serialized pulse service is≤15.74µs per stage. The physical positive event is close to linear with width through450ns at zero state, but has5.35% transfer variation over prepared±0.9V differential. This remains a range/service candidate only; no full weighted fan-in, negative-sign table, physical calibration, state-noise budget or graph timing closure exists.

A signed ten-event physical sequence now bounds repeated transfer at one gate setting. At40ns same-sign accumulation is0.0731% low, but alternating signs leave2.135µV differential residual; at450ns the corresponding errors are0.822% and0.2657mV. These residuals are measured against a simulator no-event control, and the positive/negative branches are nominally matched. Actual float-weighted fan-in and PLIF decision/reset behavior remain the next architecture gate.

The first-touch candidate now has a bounded actual float-weighted fan-in screen at SS/0°C. A stage-fixed40.253ns pulse and ideal gate levels represent each signed epoch58 weight; a sparse single-event charge table supplies the nonlinear map. Physical MIM/TG/four-MOS accumulation was simulated for370,322 and329 event sites. Log interpolation of the directly measured stage-width curve improves the370-event sum to within0.39–1.66% but leaves0.662mV event-order spread. The329-event site at32.623µV target has9–22nV deterministic error, while a nearly cancelling322-event site changes nanovolt sign with ordering. This topology remains a **schematic event-source candidate**: the gate table has no physical DAC/reference or trim loop, the capacitor pair is area/noise prohibitive as a replicated store, and no credible switched readout or PLIF update loop is attached. The next integration boundary is a physically generated calibrated gate plus noise-aware state sensing and beta/reset/adaptation, followed by 5ms service sizing.

Selected TT/27°C and FF/85°C device runs preserve the370-event sum within0.03–1.67% only when each receives its own externally measured ideal gate table. Reusing the SS table at TT drives the contribution to−141/−148mV instead of−52.45mV; at FF the ordered output ranges from+25.6 to−596mV. The next analog module must generate and refresh a local or shared calibration reference for the nonlinear gate-to-charge relation under operating temperature and process variation. This requirement adds area, service and noise costs that are absent from the current ideal-driver schematic; no transistor implementation of that module has passed.

An analog weight storage screen now tests two physical connections to that injector. A sampled gate capacitor connected only during an event suffers gate-node charge sharing; enlarging its two MIM capacitors to100µm each still gives−2.90% transfer error after5ms and≈2,874.56mm² bare area for folded PLIF weights. Keeping the MOS gates attached and steering source/drain current avoids that connection, but rail-clamped idle source nodes cause a21.93mV neutral switching packet. VCM idle clamping cuts the neutral packet to0.351µV at one gate fraction, while continuous current and stored-gate drift remain:10/20/50/100µm pairs change the gate-dependent event+91/+20/+3.1/+0.77% over5ms. The next circuit boundary is a physically isolated/buffered and refreshed analog weight reference with measured service, power and noise. Neither sampled-gate mux nor the current drain-steered variant is a chosen weight cell.

An existing transistor OTA provides a preliminary shared-buffer boundary. In SS/0°C DC unity feedback with ideal biases, its selected p-gate at0.936V is within24µV, while low n-gate levels0.48/0.30V miss by1.25/2.67mV. Driving the physical injector gate loads after an off-rail step, the p output settles in about0.1µs but the n output takes roughly7–9µs and overshoots. This means a shared buffer needs early weight prefetch and more parallel service than a50ns direct event train assumes. The OTA is not yet connected to a sampled analog weight store or a physical calibration loop, so it remains outside the selected physical datapath.


## Analog module implementation update — 2026-09-23

Historical ownership note: superseded by the full implementation delegation above. Initial module library in asic/analog/modules.spice now covers sampled PLIF, membrane hold, signed synapse, leak target, threshold/subtractive reset, square/root energy, triangular adaptation, peer inhibition, class integration and argmax, plus CMOS primitives. The design YAML binds roles and learned exported constants to all 25 actors. It is a mixed-level prototype: only switches/inverters/comparator use actual SKY130 transistor models; behavioral components are not physically implemented or power-complete.

Five bounded ngspice benches pass. The first integrated PLIF attempt exposed destructive charge sharing between state and snapshot capacitors. A labelled ideal isolation buffer fixes functional charge transfer; its transistor implementation remains required. Eight-bin maximum state error is 0.004235 model units with a provisional 0.02 smoke tolerance, not an accuracy target. Two capacitors plus a buffer are currently required by this prototype; do not count it as one bare capacitor per neuron.

Comparator stimulus mean VDD power is 1.48973 uW over 5 us, at SKY130 TT and 1.8 V. This excludes bias/reference generation and layout parasitics; do not scale it as whole-model or whole-PLIF power. All other behavioral modules retain unknown physical power/area/latency. Result evidence: artifacts/analog_asic/results/test_results.json and per-bench logs/traces. No physical analog layout, DRC/LVS, extracted PPA, 5 ms retention test or whole-model accuracy validation exists.

Models: https://github.com/google/skywater-pdk-libs-sky130_fd_pr at f62031a1be9aefe902d6d54cddd6f59b57627436; preserved upstream files/licenses. SKY130 is a feasibility choice, distinct from digital ASAP7; cross-technology numbers are not direct architecture comparisons.
