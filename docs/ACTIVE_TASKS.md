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

- State: exact hard-macro hierarchy regenerated after the first 8x8 actor master exceeded
  its 20 GiB technology-mapping limit. The next characterization launch is pending.
- Current physical checkpoint: epoch-1 seed-17 provisional ASIC export. Keep it
  separate from the epoch-11 functional simulation.
- Next actor master: exact light-depthwise 4x4 boundary master
  `xl_hm_actor__detail2_vertical__out_4x4__halo_5x4__offset__1_0`, using the
  resumable driver with 20 GiB memory, 40 GiB swap, and 8 CPUs.
- Completed physical view: exact readout master `xl_hm_readout__out_2x2`.
  Its route has zero final DRC and antenna violations, +1252.43 ps setup slack,
  +48.5815 ps hold slack, and 266.839 MHz reported fmax. Its hash-verified LEF,
  GDS, and Liberty are staged in `artifacts/ASIC_XL/hard_hierarchy/views/`.
- Exact inventory: 44 actors, 49,610 logical 8x8 actor tiles, 952,720 adaptive
  physical actor leaves, 4,400 logical readout tiles, 70,400 physical 2x2 readout
  leaves, 1,023,120 total hard-macro instances, 275 unique masters, 78,707,200
  PLIFs, 2,916,390,400 resident-state bits, and all 281,600 output pixels.
- Actor partition classes are deterministic and conservative: 7 light depthwise
  actors use 4x4 leaves (80,320 instances), 14 moderate actors use 2x2 leaves
  (335,600 instances), and 23 dense actors use 1x1 leaves (536,800 instances).
- Sources and gates:
  `artifacts/ASIC_XL/resident_macro_variants/manifest.json` and
  `artifacts/ASIC_XL/hard_hierarchy/`.
- The fixed macroized native top, wrappers, and conservation preflight preserve
  all 44 actor replacements, the readout, and the original soft graph.
- Physical-view readiness remains false until all 275 masters have LEF, GDS, and
  Liberty. The readout contributes the first 3 of 825 required view files.
## Completed evidence to reuse

- All 45 rows in
  `artifacts/ASIC_XL/partitioned_synthesis_1x1/summary.tsv` pass for corrected
  beta48 RTL. Legacy stride-2 and normalized boundary results are not exact
  hard-macro views.
- The corrected `enc1.depthwise` 1x1 route, exact gate replay, and
  activity-annotated power remain valid for that stride-1 interior partition.
- The exact actor macro generator distinguishes output shape, receptive halo,
  clipped boundary offset, true stride, padding, dilation, and tile origin. Its
  274 adaptive actor masters conserve all 49,610 logical 8x8 tiles and every
  one of the 78,707,200 PLIF identities.
- The packed exact 8x8 readout master passes focused cocotb and structural Yosys.
- Flat full-top attempts at 8, 16, and 24 GiB produced no complete netlist. Reuse
  them only as capacity evidence; the active path is hard hierarchy.

## Next valid execution

1. Generate and route the exact 4x4 light-depthwise master
   `xl_hm_actor__detail2_vertical__out_4x4__halo_5x4__offset__1_0`, requiring
   final GDS/DEF/ODB/SPEF/netlist, exit zero, clean detailed-route DRC, and valid
   setup/hold reports.
2. Run ORFS `generate_abstract` and stage its LEF, GDS, and Liberty in the
   catalogued hard-hierarchy view directory.
3. Generate and route the remaining 273 exact adaptive actor masters
   resumably. Reuse only digest-matching completed views.
4. Re-run the macroized assembly generator after any catalog, model, tile-plan, or generated-top
   change; otherwise reuse its digest-bound current output.
5. After all 825 physical views are staged, run top-level floorplanning, placement, CTS, routing,
   extraction, timing, physical checks, GDS integrity, and full-graph activity power over all
   1,023,120 physical macro instances.
6. Reuse the completed ten-bin native simulation as provisional full-graph
   activity evidence. Report full-chip PPA only after every native graph and
   physical gate passes. Regenerate constants, views, simulation, and PPA for
   the selected final/QAT checkpoint before final silicon claims.

## Process rules

- Preserve exact 440x640 dimensions, all 44 permanent actors, direct local
  register/latch state, fixed graph routing, and every PLIF identity.
- The 8x8 value is the retained logical hierarchy boundary; adaptive 4x4/2x2/1x1
  physical leaves subdivide it without reducing the model or score map.
- Inspect containers, logs, status JSON, manifests, and digests before launching.
- Use bounded, non-dumpable containers and preserve restart artifacts.
- Do not create scheduled tasks for this flow.
- Never substitute SRAM, truncate dimensions, share actor compute, drop boundary
  variants, or call extrapolated tile measurements full-chip PPA.



