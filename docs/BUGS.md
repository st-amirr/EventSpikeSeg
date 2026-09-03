# Bugs and limitations

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
1,590,476,800 bits, or **189.60 MiB-equivalent**, before routing and control. This is a physical
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

Native SystemVerilog now covers channel-aware standard/grouped/depthwise kernel scatter, actor-local current/membrane/tag storage, exact PLIF commit, completion/spike backpressure, inhibition, adaptation, class-current/argmax primitives, lossless two-way event/token fanout, fixed concat channel remap, nearest-neighbor 2x event expansion, same-bin completion rendezvous, and a correctness-reference residual binary-OR/dedup join. The Python exporter now owns an explicit v8 **non-linear DAG** contract; the 25-actor list is only a deterministic topological/export order.

The active six-class trained-v4 generated channelized convolution/PLIF graph includes all 25 actors, exact static routes, grouped retinotopic mechanism commits, 143,824 exported synaptic weights, and the temporal readout. Model-scale memories now cross bounded banked 1RW interfaces, and the SRAM-integrated reduced-geometry full-DAG replay passes final-output plus per-actor current, candidate/membrane, spike, and adaptation age/amplitude comparison. A reduced 4x4 actor now also reaches clean routed SKY130 GDS with two characterized 80x64 macros, closing the interface experiment only. Full-model macro selection/banking, native residual-dedup capacity, native-resolution activity/latency, and routed activity-based PPA remain open. Do not report native real-time or power results until those paths are measured.

The paragraph above records the superseded SRAM implementation milestone; it is not the active
direct-state architecture. The active replacement uses resident state elements and spike-vector
synapse fabrics. Its full 25-actor generated graph, full-scale elaboration, placement, timing, and
power are not complete, so no resident full-model PPA claim is yet valid.

The tracked native profiler still targets the checkpoint-authoritative complete 234-record
validation sequence `zurich_city_02_a` for a capacity claim. A real `zurich_city_13_a/events.h5`
sample is now available and its first 5 ms has completed through the full native integer DAG, but
the sample has no matching rectification map and is not the checkpoint validation sequence. It is
therefore preliminary implementation activity, not a full-sequence capacity or publication power
claim. The resulting activity also proves that the present single-lane actor organization misses
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

# 2026-09-02 — Multi-tile tag checker inferred a latch

The first Yosys process-lowering run of the checkpoint-exact two-tile wrapper found that the
integer loop index in the result-tag comparator was assigned only when results were valid. This
inferred unintended storage even though the comparator output itself had a default. The index now
has an unconditional combinational assignment. The same two-tile synthesis and cocotb regression
pass, and the tiled wrapper is now part of the representative synthesis gate.
