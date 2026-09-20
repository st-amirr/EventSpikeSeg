# Active work and resume order

Read this after `project_spec.yaml`, `docs/AGENTS.md`, `docs/ARCHITECTURE.md`, and
`docs/DECISIONS.md`. Update it whenever a long-running stage starts, completes,
fails, or changes the next valid stage. Detailed history belongs in
`docs/PROGRESS.md`.

## Current processes

### EventSpikeSegXL training

- State: active at the 2026-09-15 inspection.
- Container: `eventspikeseg-train-dsec-xl-run-179bb2d1cab0`.
- A Docker engine restart interrupted and removed the prior auto-remove container
  during epoch 19. The replacement resumed epoch 19 from the durable epoch-18
  checkpoint; no epoch-19 checkpoint existed at restart.
- Latest durable checkpoint:
  `artifacts/model_checkpoints/dsec_XL/EventSpikeSegXL_seed17_epoch018.pt`,
  SHA-256 `340926232155f67fe3d1bf460209c63dbbec03a6da1f18c7237b77665c432324`.
- Constraint: do not stop or replace this run without explicit authorization.

### Epoch-11 complete native functional simulation

- State: complete and audited; the finished container was removed.
- Scope: exact 440x640, 44-actor integer DAG, ten 5 ms bins from the first 50 ms
  of `zurich_city_13_a/events.h5`.
- Result: exit zero, no OOM, 27,619.365 s host runtime, 428,367 input events,
  102,959,737 actor output spikes, 225,609,186 actor input events, and
  33,653,694,655 synaptic contributions.
- Output prefix:
  `artifacts/RTL/profile/xl_epoch011_zurich_city_13_a_native_50ms_resident_fix`.
  The uint8 prediction covers all 281,600 pixels and has SHA-256
  `679beb38969b94bffd9c2c78f4789ca7a3eb67ffd7f59f560da0109bf9b792d7`.
- Consumer-count stream reclamation and zero-offset immutable-list reuse fixed
  prior 8/14 GiB OOM without changing arithmetic or event order.
- This is complete short-interval functional/activity evidence from an
  unrectified sample. It is not hardware-cycle, full-sequence capacity, or
  publication-grade power evidence. Reuse it; do not rerun it for the current
  provisional checkpoint.

### XL full-chip physical implementation

- State: the exact 1x1 `down2.depthwise` route completed after adding its missing
  retinotopic-mechanism RTL dependency. The preceding 1x1 `enc1.depthwise`,
  `detail1.depthwise`, `detail2.vertical`, and `detail2.horizontal` routes and the
  exact 2x2 readout route are also complete. The hierarchy was regenerated after
  8x8, 4x4, and 2x2 actor capacity failures; every actor now uses exact 1x1 leaves.
- Current physical checkpoint: epoch-1 seed-17 provisional ASIC export. Keep it
  separate from the epoch-11 functional simulation.
- No actor ORFS process is currently active. The next physical work is the
  isolated primitive characterization listed below, followed by the remaining
  exact actor masters through the resumable driver.
- Completed physical view: exact readout master `xl_hm_readout__out_2x2`.
  Its route has zero final DRC and antenna violations, +1252.43 ps setup slack,
  +48.5815 ps hold slack, and 266.839 MHz reported fmax. Its hash-verified LEF,
  GDS, and Liberty are staged in `artifacts/ASIC_XL/hard_hierarchy/views/`.
- Exact inventory: 44 actors, 49,610 logical 8x8 actor tiles, 3,163,600 exact
  physical actor leaves, 4,400 logical readout tiles, 70,400 physical 2x2 readout
  leaves, 3,234,000 total hard-macro instances, 335 unique masters, 78,707,200
  PLIFs, 2,916,390,400 resident-state bits, and all 281,600 output pixels.
- Actor partitioning is deterministic and constrained by measured capacity: all
  44 actors use 1x1 leaves. No 2x2, 4x4, or 8x8 actor remains in the layout.
- Sources and gates:
  `artifacts/ASIC_XL/resident_macro_variants/manifest.json` and
  `artifacts/ASIC_XL/hard_hierarchy/`.
- The fixed macroized native top, wrappers, and conservation preflight preserve
  all 44 actor replacements, the readout, and the original soft graph.
- Physical-view readiness remains false until all 335 masters have LEF, GDS, and
  Liberty. The current representative actor routes cover 5/44 actor populations;
  the complete top-level route has not been run.

### Isolated primitive characterization

- State: ordinary one-cell PLIF and one fully connected nine-term 3x3 convolution
  output are complete through ASAP7 placement, detailed routing, extraction, and
  VCD-driven OpenSTA power. Outputs are under
  `artifacts/ASIC_XL/primitive_characterization/` and are aggregated by
  `scripts/inventory_xl_physical_primitives.py`.
- Ordinary PLIF: zero final detailed-route violations, 238.762 um^2 standard-cell
  area, 921.968 MHz fmax, 33.8188 pJ dynamic per bin update, and 0.205748 uW TT
  leakage. Multiplying 60,544,000 ordinary cells at 200 updates/s gives 0.4095 W
  dynamic, 12.4568 W leakage, and 14,455.61 mm^2 standard-cell area before shared
  routing, clocks, power grid, pads, and top-level whitespace.
- Nine-term convolution block: zero flow errors, 28.7372 um^2 standard-cell area,
  and 62.2855 uW dynamic under 128 pseudorandom vectors at one vector/5 ns.
  Normalized values are 3.19302 um^2, 0.0346031 pJ per bin evaluation, and
  2.37704 nW leakage per hardwired term. The exact model has 9,125,811,200 terms.
- A combined adaptation-plus-inhibition experiment was stopped and its partial
  outputs removed because no actor uses both mechanisms. Valid characterization
  must keep inhibition-only stem groups and adaptation-only encoder groups separate.

### Representative-block full-model estimate

- State: generated from the exact 3,234,000-instance inventory, the exact 98-edge
  graph, the completed native ten-bin activity profile, routed `enc1.depthwise`
  activity power, and the routed 2x2 readout area/leakage.
- Machine-readable outputs are in `artifacts/ASIC_XL/full_model_estimate/`; the
  tracked method is `asic/xl_representative_ppa.yaml` and the reproducible driver
  is `scripts/estimate_xl_full_model_ppa.py`.
- Current central proxy is 359,915.96 mm^2 standard-cell area and 259.51 W average
  at 20 predictions/s, with a 0.5x..3.0x sensitivity band. The actor dynamic
  component is 3.122 mJ per 50 ms sample. These values expose the scale of the
  fully parallel direct-state model; they are not routed full-chip PPA.
- Layout evidence currently comprises the structurally checked full hierarchy,
  one routed/activity-measured actor partition, and one routed readout master.
  Top-level floorplanning, placement, routing, extraction, and wirelength power
  are not complete.
## Completed evidence to reuse

- All 45 rows in
  `artifacts/ASIC_XL/partitioned_synthesis_1x1/summary.tsv` pass for corrected
  beta48 RTL. Legacy stride-2 and normalized boundary results are not exact
  hard-macro views.
- The corrected `enc1.depthwise` 1x1 route, exact gate replay, and
  activity-annotated power remain valid for that stride-1 interior partition.
- The exact actor macro generator distinguishes output shape, receptive halo,
  clipped boundary offset, true stride, padding, dilation, and tile origin. Its
  334 exact 1x1 actor masters conserve all 49,610 logical 8x8 tiles and every
  one of the 78,707,200 PLIF identities.
- The packed exact 8x8 readout master passes focused cocotb and structural Yosys.
- Flat full-top attempts at 8, 16, and 24 GiB produced no complete netlist. Reuse
  them only as capacity evidence; the active path is hard hierarchy.

## Next valid execution

1. Complete isolated activity characterization for the two valid retinotopic
   variants: inhibition-only and adaptation-only. Then characterize the soft
   routing/attention and temporal-readout primitives.
2. Add routed representative area, leakage, timing, and activity power for one
   physical instance of each of the 44 actors, updating the hierarchical estimate
   after every accepted result.
3. For full layout, generate and route all remaining exact boundary/halo masters
   resumably. Reuse only digest-matching completed views.
4. Re-run the macroized assembly generator after any catalog, model, tile-plan, or generated-top
   change; otherwise reuse its digest-bound current output.
5. After all 1,005 physical views are staged, run top-level floorplanning, placement, CTS, routing,
   extraction, timing, physical checks, GDS integrity, and full-graph activity power over all
   3,234,000 physical macro instances.
6. Reuse the completed ten-bin native simulation as provisional full-graph
   activity evidence. Report full-chip PPA only after every native graph and
   physical gate passes. Regenerate constants, views, simulation, and PPA for
   the selected final/QAT checkpoint before final silicon claims.

## Process rules

- Preserve exact 440x640 dimensions, all 44 permanent actors, direct local
  register/latch state, fixed graph routing, and every PLIF identity.
- The 8x8 value is the retained logical hierarchy boundary; exact 1x1
  physical leaves subdivide it without reducing the model or score map.
- Inspect containers, logs, status JSON, manifests, and digests before launching.
- Use bounded, non-dumpable containers and preserve restart artifacts.
- Do not create scheduled tasks for this flow.
- Never substitute SRAM, truncate dimensions, share actor compute, drop boundary
  variants, or call extrapolated tile measurements full-chip PPA.



