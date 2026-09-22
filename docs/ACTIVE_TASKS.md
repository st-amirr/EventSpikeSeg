# Active work and resume order

## 2026-09-22 — Bounded 140k mechanism checks

- Reused existing inhibition/adaptation physical checkpoints and existing block directories. Each activity case checks 64 midpoint samples from its checkpoint-derived synthetic pool; no whole-model simulation, new synthesis or rerouting was performed.
- Accepted 6/9 activity cases: penalty_lane, square_lane, commit_lane, penalty_direct, penalty_lower, penalty_upper. All accepted cases have zero unannotated pins. 5 accepted activity cases use detailed-route parasitics; 1 use global-route estimated parasitics. Three penalty-reducer roles share one physical design.
- Pending after the bounded runs: inhibition, energy64, energy128. Do not increase the 120-second per-stage limit or launch a broad retry campaign automatically. No new measured power is accepted for pending cases; existing input-trace estimates remain separately labeled historical evidence.
- Mechanism-only scaled proxies: 0.009344 W dynamic and 39.630 W leakage at 200 bins/s, using exact 140k counts. These omit the resident state/learned-beta update circuitry around mechanism populations as well as graph/control, top-level clocks/routing, and measured spike sparsity. They are not full-chip power.
- Report: `artifacts/ASIC/primitive_characterization/base_140k_inventory/GATE_RESULTS.md`; detailed audit: `mechanism_gate_results.json`, `mechanism_gate_manifest.json`, and `mechanism_gate_status.json` in the same directory.
- No ASIC process remains running from this step. Original physical databases and useful XL layout/training data were unchanged. Full 25-actor layout is still incomplete; physical assembly is a separate remaining milestone.

## Current ASIC target policy — 2026-09-21

All primary ASIC layout, block simulation, power, area, timing, and inventory work is based on **EventSpikeSeg140k v8, epoch 80, seed 17**: six classes, 440x640, 25 permanent PLIF actors, 54 graph edges, 30,976,000 resident PLIF identities, and 143,824 deployed synaptic weights. Primary exports/results live under `artifacts/ASIC/`; the latest accepted small gate-simulation results are in `artifacts/ASIC/primitive_characterization/`.

**EventSpikeSegXL is secondary/reference work.** Preserve useful accepted XL GDS/LEF/Liberty views, final routed ODB/DEF/netlist/SDC/SPEF files, checkpoint-specific constants, hierarchy catalogs/instance maps/preflight, and validation/power reports. Keep them under `artifacts/ASIC_XL/` and their existing named OpenROAD result directories. Retain the latest useful unfinished-run database and failure summaries; redundant intermediate databases and rebuildable simulation binaries need not be retained. Never relabel XL measurements or its 44-actor inventory as 140k results. Reuse an XL physical view for 140k only after proving matching RTL, constants, geometry, interfaces and constraints.

XL physical expansion remains paused behind 140k work. Preserve independent XL training and checkpoints. Neither model has a completed full-chip layout; existing routed blocks and structural hierarchy data must be labeled accordingly. Current work uses small per-block simulations and extracted-layout measurements; whole-model simulation remains retired. Historical entries below retain their original model and date and do not change this priority.


## 2026-09-21 — Simple layout/block-simulation milestone (latest)

User requested small steps, storage cleanup, and reuse of layouts for per-block simulation/power rather than prolonged full-model simulation and repeated physical retries.

- Removed 16.44 GiB of redundant OpenROAD database checkpoints and compiled simulation executables. Final views, all reports, latest unfinished-run databases, source RTL and training/checkpoint data are preserved; deletion manifests are under `artifacts/ASIC/`.
- Reused the 140k ordinary-PLIF and conv9 final layouts. Post-route functional gate simulations passed 65 and 255 output-snapshot checks; extracted-SPEF power has zero unannotated pins for both.
- Current compact results: `artifacts/ASIC/primitive_characterization/base_140k_inventory/GATE_RESULTS.md` and `gate_results.json`. These supersede the corresponding input-only power measurements for this workload, not all other blocks or the entire model.
- Prior PLIF annotation covered 116 pins with 12,869 unannotated; the old 2.013376 W subtotal must not be presented as validated full-chip power.
- Full 25-actor layout remains incomplete. Existing GDS files are isolated blocks. Readout now passes 49 gate-level reference checks after correcting pre-edge versus post-edge testbench sampling. Its existing layout supplied extracted power; 45,229 pins have VCD activity and only the two verified-zero coordinate outputs are unannotated. RTL and physical files were unchanged.
- XL training was observed running in `eventspikeseg-train-dsec-xl-run-0abd58c1b591` and was not interrupted. No ASIC container remains running from this milestone.

Read this after `project_spec.yaml`, `docs/AGENTS.md`, `docs/ARCHITECTURE.md`, and
`docs/DECISIONS.md`. Update it whenever a long-running stage starts, completes,
fails, or changes the next valid stage. Detailed history belongs in
`docs/PROGRESS.md`.

## Current processes

### EventSpikeSeg140k full-model ASIC implementation

- State: primary active physical target as of 2026-09-20. Use the canonical
  epoch-80 seed-17 six-class checkpoint export in `artifacts/ASIC/`; keep all
  XL estimates and views separate.
- Exact inventory: 25 permanent PLIF actors, 54 graph edges, 30,976,000 direct
  register/latch-resident PLIF identities, 143,824 deployed weights,
  3,730,918,400 expanded actor synapse terms per dense bin, and 27,033,600
  readout terms per dense bin.
- Three checkpoint-exact isolated primitives are complete through ASAP7 detailed
  route and a fourth exact 32-channel stem-inhibition group is timing-closed and
  congestion-free through global route. All four have zero setup/hold TNS and
  VCD-driven power.
- Reproducible results and capacity multiplication:
  `artifacts/ASIC/primitive_characterization/base_140k_inventory/`.
- Historical input-trace subtotal at 20 frames/s and ten bins was 2.013376 W dynamic
  for ordinary PLIF updates, dense actor synapse terms, exact readout blocks, and
  all 70,400 stem-inhibition groups. This excludes adaptation, full graph routing,
  clocks, and measured spike sparsity;
  it is not full-chip power signoff.
- Full-model layout is not complete. The isolated PLIF footprint multiplied over
  all 30,976,000 state identities is a capacity bound of 46,647.068 mm^2 of die
  footprint before mechanism variants, synapses, clock, power, and routing.
- No ASIC run is active at the latest inspection. Reuse completed 140k layouts
  and accepted small-block measurements; remaining adaptation characterization and
  the full 25-actor hierarchy are unfinished work, not running jobs.

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

### XL full-chip physical implementation

- State: paused as a secondary/reference target while the 140k base model is the
  primary physical target. The exact 1x1 `down2.depthwise` route completed after adding its missing
  retinotopic-mechanism RTL dependency. The preceding 1x1 `enc1.depthwise`,
  `detail1.depthwise`, `detail2.vertical`, and `detail2.horizontal` routes and the
  exact 2x2 readout route are also complete. The hierarchy was regenerated after
  8x8, 4x4, and 2x2 actor capacity failures; every actor now uses exact 1x1 leaves.
- Current physical checkpoint: epoch-1 seed-17 provisional ASIC export.
- No XL actor ORFS process is active. Preserve the accepted views and reports
  below for secondary work; do not resume the XL master campaign as the primary flow.
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

### Secondary XL isolated primitive characterization

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

## Preserved secondary XL evidence

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
  them only as XL capacity evidence; full 140k assembly remains separate work.

## Next valid execution

1. Complete checkpoint-exact 140k inhibition-only and adaptation-only PLIF
   characterizations, followed by the six-class temporal readout and graph-control
   primitives.
2. Generate the exact 25-actor base hard hierarchy from
   `resident_tile_plan_8x8.json`, retaining every direct resident state identity,
   boundary/halo variant, and all 54 graph edges.
3. Route all required base masters resumably, reusing only digest-matching views.
4. Run top-level floorplanning, placement, CTS, routing, extraction, timing,
   physical checks, GDS integrity, and IR analysis. Compute power by multiplying
   accepted per-block activity results by the exact physical inventory.
5. Keep the XL hierarchy paused and separate until the 140k target reaches those
   gates or the user explicitly changes the primary target.

## Process rules

- Primary 140k work preserves exact 440x640 dimensions, all 25 permanent actors,
  all 54 graph edges, and all 30,976,000 local register/latch PLIF identities.
- Secondary XL evidence preserves its own 44 actors and 78,707,200 PLIF identities;
  these counts must never be used as the 140k implementation inventory.
- The 8x8 value is the retained logical hierarchy boundary; exact 1x1
  physical leaves subdivide it without reducing the model or score map.
- Inspect containers, logs, status JSON, manifests, and digests before launching.
- Use bounded, non-dumpable containers and preserve restart artifacts.
- Do not create scheduled tasks for this flow.
- Do not recreate full-model simulation, replay, native activity profiling, or
  activity-derived whole-model estimates for 140k or XL. Simulate and measure
  blocks independently, then multiply by the exact full-layout inventory.
- Never substitute SRAM, truncate dimensions, share actor compute, drop boundary
  variants, or call extrapolated tile measurements full-chip PPA.



