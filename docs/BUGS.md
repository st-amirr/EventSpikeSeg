# Bugs and limitations

> Current scope (2026-09-21): EventSpikeSeg140k epoch-80 seed-17 is the primary ASIC layout/simulation/estimate target. Useful XL layouts and reports are preserved for secondary work; XL figures are not 140k evidence. See [target policy](AGENTS.md#current-asic-target-policy--2026-09-21). Older entries are historical where superseded.

## Dataset representation limitation

**Status: explicit approximation in software.**

The Ev-SegNet download contains histogram activity plus per-polarity timestamp mean/std, not raw asynchronous event tuples. The scheduler conserves activity across three arrivals at mean and mean±std. Exact within-interval timing cannot be reconstructed, so hardware/accuracy reporting must describe this moment approximation.

## Rare-class collapse

**Status:** open.

Object, nature, human, and vehicle classes remain weak or absent in the low-budget mechanism screen. Ground-truth support for the 128-sample held-out subset was:

```text
flat               54,829 pixels
construction+sky  388,044
object               1,615
nature              50,690
human                  702
vehicle              28,408
```

The mechanism-screen winner predicted no nature or vehicle pixels and only one human pixel. This cannot be fixed by architecture ranking alone. Continue recording ground-truth and predicted pixel counts, and do not promote a model solely on overall pixel accuracy.

## Resolved: whole-feature-map binary adaptation

The old `amax` activity rule treated one spike like dense activity and could raise an entire feature-map threshold. The active mechanism uses local triangular threshold adaptation driven by retinotopic membrane energy instead.

## Resolved: hidden hard winner gating in the active top five

The completed mechanism screen showed `winner_peer` inhibition starving the encoder: spike rates fell to approximately `0.0474 → 0.00306 → 0.000149` across enc1/enc2/enc3. The active structural top five therefore use `peer_membrane` inhibition only in the stem. The stronger winner gate remains a reusable component but is not part of the current contenders.

## Open: structural-cost trade-off

The active six-class DSEC/ASIC target is `EventSpikeSeg140k`: 149,835 registered
parameters, 149,423 executed inference parameters, 25 permanent PLIF actors, and one
temporal class-current readout. The prior 11-class export is historical only.
Parameter count is only a proxy for ASIC logic cost; the dominant constraint is physical
resident current/membrane/adaptation state, followed by pointwise mixing, event routing,
clock/reset distribution, and inhibition/adaptation arithmetic.

### Logical-state footprint is much larger than parameter memory

At native 440x640, v8 owns **30,976,000** current/membrane identities. Threshold adaptation adds
age/amplitude on **10,982,400** neurons. The active direct-state design gives every identity local
register/latch state and advances every PLIF once per 5 ms completion token; it therefore needs no
`last_bin_tag`, addressed state SRAM, fetch, or writeback. The exact logical state inventory is
1,265,792,000 bits, or **150.89 MiB-equivalent**, before routing and control. This is a physical
standard-cell/latch implementation burden, not a memory-device capacity requirement.

## Open: continuous learned neuron parameters

PLIF beta, base threshold, inhibition strength, threshold-adaptation strength, and adaptation duration are learned numerical training variables. ASIC deployment requires frozen fixed-point formats, deterministic rounding/saturation, and integer-reference regression. The baseline preserves quantized per-channel beta; shift-only/power-of-two leakage is an optional optimization that requires accuracy revalidation.


## Open: native-resolution CPU stream-training cost

Each 50 ms record executes ten internal clock updates. Training truncates BPTT at record boundaries while retaining numeric PLIF state, so memory no longer grows across the entire recording. CPU runtime remains substantial because dense software convolutions execute for every internal clock; parameter count alone does not predict this cost.

Resolved on 2026-08-15: continuous state initially detached the project membrane
but left SpikingJelly `ParametricLIFNode.v` attached to the completed autograd graph.
The internal `v`/`w` references are now detached after each record, preventing the
previous record graph from overlapping the next forward pass.


## 2026-08-09 — Native-resolution training memory root cause

Native-resolution batch-1 training exposed an avoidable full-resolution temporal-state cost on top of intrinsic T=15 BPTT. The final model now keeps triangular threshold adaptation off on the stem/x1/detail path and enables it from x2 onward, where spatial state is 4× smaller. Stateless convolution plus affine current transforms are vectorized over the combined T×N batch dimension while PLIF/LIF updates remain sequential, preserving identical temporal dynamics and gradients. Training returns scalar activity-rate diagnostics instead of retaining complete hidden TNCHW spike sequences solely for regularization.


## Resolved: fake temporal axis from repeated static input

**Status:** resolved in code on 2026-08-14.

Previously one six-channel sample was repeated or adjacent files were stacked as a synthetic `T` axis. The timestamp-stream loader forbids both. Internal clock updates now come from timestamp scheduling inside one physical interval, while stream continuity comes from retained PLIF state between records.

## Open: installed training event tensors are incomplete

**Status:** dataset installation issue detected automatically.

The installed `events/train` folder has 2,887 NumPy tensors while `labels/train` has 10,001 indexed masks. Only `rec1487339175_export` is represented in the active event manifest. This loss of recording diversity is a likely accuracy limiter and must be fixed at the dataset installation level; the loader reports the mismatch explicitly.


## Full-chip ASIC integration still incomplete

**Secondary XL history (2026-09-13): full-top elaboration exceeded memory; retained for reference. Primary 140k full-chip assembly is also unfinished.**

The checkpoint-bound beta48 XL preflight passes and the 1x1 partition journal contains
45 PASS rows. Guarded complete-top Yosys attempts at 8, 16, and 24 GiB all exited 137
while deriving the native hierarchy; the 24 GiB attempt reached 23.97 GiB and produced
no complete netlist. OpenROAD full-chip placement/routing, extracted timing, and
activity power have not started. The machine-readable record is
`artifacts/ASIC_XL/full_chip_layout/capacity_gate.json`, and the exact resume order is
`docs/ACTIVE_TASKS.md`. This is a host-capacity failure, not an RTL functional mismatch.

Native SystemVerilog now covers channel-aware standard/grouped/depthwise kernel scatter, actor-local current/membrane/tag storage, exact PLIF commit, completion/spike backpressure, inhibition, adaptation, class-current/argmax primitives, lossless two-way event/token fanout, fixed concat channel remap, nearest-neighbor 2x event expansion, same-bin completion rendezvous, and a correctness-reference residual binary-OR/dedup join. The Python exporter now owns an explicit v8 **non-linear DAG** contract; the 25-actor list is only a deterministic topological/export order.

The active six-class trained-v4 generated channelized convolution/PLIF graph includes all 25 actors, exact static routes, grouped retinotopic mechanism commits, 143,824 exported synaptic weights, and the temporal readout. A reduced 4x4 actor reaches clean routed SKY130 GDS with two characterized 80x64 macros, closing the interface experiment only. Full-model layout and routed physical checks remain open. Power is measured per block and multiplied by the exact physical inventory.

The paragraph above records the superseded SRAM implementation milestone; it is not the active
direct-state architecture. The active replacement uses resident state elements and spike-vector
synapse fabrics. Its full 25-actor generated graph, full-scale elaboration, placement, timing, and
power are not complete, so no resident full-model PPA claim is yet valid.

The former whole-model native profiler is retired. The present single-lane actor organization misses
the 5 ms deadline by at least 569.9x at the isolated tile's nominal clock; parallel bank/lane design
is now an explicit open implementation requirement.

Ordinary and retinotopic actors now have parallel scatter plus independent state/queue banks, and
the generated graph has ordered edge FIFOs. Aggregate bank/commit/link floors produced a 924-lane
200 MHz target, but the subsequent event-order timing model rejected the collection fabric:
`down2.standard` serializes peer-channel contributions and needs 40,107,810 isolated cycles. The
spatial-only contribution port must be replaced by channel-by-spatial accumulation with an atomic
spatial mechanism commit. Ordinary actors now have per-bank contribution FIFOs, but their native
depth/occupancy and combined timing have not been reprofiled. Inter-actor FIFO occupancy, route
backpressure, full-chip timing degradation, physical SRAM ports, area, and activity power remain
unmeasured. Do not report the earlier independent floors as end-to-end latency.

The final direction now removes addressed PLIF state SRAM entirely. Ordinary and retinotopic
resident populations, direct convolution synapses, raw-event ingress, bitmap routing, and the
resident temporal readout are implemented as primitives. Full 25-actor resident graph generation,
native elaboration, routed timing, and power remain open. Dense residency eliminates fetch latency
but exposes parallel reduction trees, roughly 31 million PLIF update datapaths, and their clock/reset
load. The former full-map-per-tile broadcast has been replaced by exact receptive-halo wiring;
reduced synthesis is still not proof the native graph fits. Publication results
must report the synthesized resident implementation rather than infer chip size from parameters.

Native resident elaboration currently exceeds the available tool memory. The checkpoint-derived
25-actor top was generated successfully, but Icarus was killed with exit 137 under the 8 GB Docker
limit before simulation. This is not a functional mismatch and must not be reported as a latency
or power result. Hierarchical spatial tiling and exact receptive-halo mapping now pass unit and full
regressions, but the physical design still contains about 1.59 billion resident state bits plus
update and synapse logic. Representative multi-tile routing is the next implementation experiment.
# 2026-09-02 — Exact resident tiles are slow in emulated Yosys/ORFS

The checkpoint-weighted 8x8 `detail_stem` resident tile spent more than ten minutes in Yosys
canonicalization. A 4x4 version canonicalized in 58 seconds (329 MiB peak) but remained in mapped
netlist optimization after more than twenty additional minutes. Both bounded runs were manually
terminated, producing exit 137 from container stop; neither was an OOM and neither reached routing.
No PPA may be extracted from these partial logs. The immediate characterization fallback is 2x2,
while the implementation hierarchy remains 8x8.

The subsequent 2x2 run completed detailed routing and extraction but failed strict final validation
on 68 max-slew endpoints (321.65--360.29 ps versus 320 ps). It had zero setup/hold, capacitance,
fanout, congestion, and DRC failures. Because it copied the stale SDC before the resident input-port
fix, it required a resident-SDC rerun.

**Resolved for the 2x2 characterization unit:** OpenROAD interprets `SLEW_MARGIN` as an integer
percentage. A 1.2% rerun left 27 violations and a 20% rerun left 8. The accepted 50% run resized
142 cells and inserted 292 additional pre-route repair buffers across the placement and global-route
stages. Extracted max-slew, max-capacitance, max-fanout, setup, hold, and detailed-route DRC counts
are all zero; worst max-slew margin is +90.03 ps. This does not resolve full-model elaboration or
full-chip PPA.

# 2026-09-03 — Two-tile resident detailed routing reaches Docker memory limit

The checkpoint-exact two-column `detail_stem` boundary top completed synthesis, placement, CTS,
and global routing, then reached detailed routing with 1,024,833 guides. At 10% of the first
detail-route optimization iteration it consumed 7,764,480 KB and was stopped by the configured
8 GB Docker limit. The final report bundle was never generated. The completed global-route slack
and area are intermediate only; no extracted timing, DRC, power, latency, or two-tile PPA claim is
valid. Repeat unchanged on a larger-memory/native-x86 host.

# 2026-09-02 — Multi-tile tag checker inferred a latch

The first Yosys process-lowering run of the checkpoint-exact two-tile wrapper found that the
integer loop index in the result-tag comparator was assigned only when results were valid. This
inferred unintended storage even though the comparator output itself had a default. The index now
has an unconditional combinational assignment. The same two-tile synthesis and cocotb regression
pass, and the tiled wrapper is now part of the representative synthesis gate.

## 2026-09-14 — Retired history: native activity profiler retained consumed streams

The complete XL integer simulator kept every upstream multi-million-event list
until the end of each 5 ms bin and copied zero-offset edge lists. Dense epoch-11
activity therefore exceeded 8 and 14 GiB before the first resume checkpoint.
The graph now counts remaining consumers, releases a stream after its final
consumer, and reuses immutable zero-offset lists. Arithmetic, event order,
actor state, and prediction semantics are unchanged. The exact 16 GiB run
completed all ten bins with exit zero and no OOM. The profiler and its generated
artifacts were removed on 2026-09-21 when whole-model simulation was retired.

## 2026-09-14 — Resolved: readout score array caused Yosys priority explosion

The resident temporal readout stored scores in an unpacked array written by
large procedural loops. Yosys treated it as a multiwrite memory and consumed
more than 12 GiB in `OPT_MEM_PRIORITY` for one 8x8 tile. Scores now occupy a
packed register vector with one generated constant writer per score. Focused
readout cocotb passes, Yosys reports zero memories, and the exact 8x8 structural
run completes with a 3649.98 MB peak.

## 2026-09-14 — Open: full hard-macro physical views

The exact catalog contains 236 unique checkpoint-bound masters, 54,010 nominal
tiles, and 120,010 physical instances after exact 2x2 readout subdivision.
Before native top-level placement, every master needs routed GDS, abstract LEF,
and extracted timing-model Liberty. The macroized native assembly is generated
and passes its conservation preflight. The exact-name 4x4 readout master also
OOM-killed during ABC at 20 GiB, so no view was staged. The next ORFS target is
xl_hm_readout__out_2x2, with 70,400 physical instances grouped sixteen per logical tile.
No full-chip layout claim is valid until all views, assembly, routing, timing,
and physical checks complete. Power uses independently measured blocks and exact counts.

## 2026-09-15 — Resolved: readout ORFS top-cell identity differed from catalog

The first 20 GiB external readout retry used the generic ORFS top-cell name
`resident_readout_tile_pnr_top`, while the hard-macro catalog and macroized
assembly require `xl_hm_readout__out_4x4`. A clean result from that run could not
be published as the catalog macro, so it was stopped and journaled. The readout
generator, catalog master RTL, ORFS `DESIGN_NAME`, blackbox, and normalized port
contract now agree on the exact catalog name. The corrected run uses the
resumable hard-macro driver and stages views only after route/DRC validation.


## 2026-09-15 — Resolved by subdivision: exact 4x4 readout exceeded 20 GiB

The catalog-identity-correct 4x4 readout still exhausted its 20 GiB ORFS limit during ABC. It produced no accepted physical view. The physical readout master is now an exact 2x2 leaf with 96 input bits and four output pixels. This changes physical hierarchy only: 70,400 leaves cover all 281,600 native pixels, and sixteen leaves compose each of the unchanged 4,400 logical 8x8 tiles. The regenerated wrapper uses a 17-bit leaf selector, and its conservation preflight passes. Full-chip PPA remains gated by all 708 required views.

## 2026-09-15 — Resolved by adaptive subdivision: exact 8x8 actor exceeded 20 GiB

The lowest-complexity exact 8x8 actor master, a clipped `detail2.vertical`
boundary, exhausted its 20 GiB ORFS limit during technology mapping and produced
no accepted view. Uniform 4x4 actor leaves are also unsafe for dense 128-channel
3x3 actors whose exact 1x1 synthesis already approaches 14 GiB. The hard hierarchy
now chooses exact 4x4 leaves only for light depthwise actors, 2x2 for moderate
actors, and 1x1 for dense actors. This physical subdivision preserves the logical
8x8 plan, global convolution coordinates and halos, all 78,707,200 PLIF identities,
and the 440x640 output. The new catalog contains 274 actor masters plus the accepted
2x2 readout master; full-chip PPA remains gated by all 825 required views.
