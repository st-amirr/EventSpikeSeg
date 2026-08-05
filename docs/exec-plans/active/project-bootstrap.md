# EventSCNN-FPGA Project Bootstrap Execution Plan

## Objective

Turn the research-only repository into a runnable, synthetic-first EventSCNN-FPGA
implementation whose software, integer, sparse-scatter, and RTL paths share explicit
operation ordering and testable contracts.

## Sources and relevant specification sections

Read completely on 2026-08-02: `agent.md` (the supplied lower-case instruction file)
and `project_spec.yaml`. Primary sections are `temporal_representation`, `model`,
`custom_spiking_dynamics`, `spikingjelly_contract`, `quantization`,
`custom_fpga_backend_strategy`, `verification`, and `implementation_plan`.

## Repository state at start

Commit `d60c76c` contained the specification and literature PDFs only. The worktree
already had user-owned changes to `.DS_Store`, `.gitignore`, and `project_spec.yaml`,
plus untracked `agent.md`; bootstrap must not overwrite or revert them. Python 3.9 and
GNU Make are available. PyTorch, SpikingJelly, NumPy, pytest, cocotb, GHDL, Icarus,
and Verilator were initially absent.

## Assumptions

- Timestamp units are microseconds and bins are half-open `[start, end)`.
- Canonical polarity mapping is `False/0 = OFF channel 0`, `True/1 = ON channel 1`.
- Empty input needs an explicit duration or bin count.
- Channel ties in `f_inst` select the lowest index.
- The default floating model uses dense `Conv2d`; sparse scatter is an independent
  reference and retains shared kernels.

## Ordered milestones and acceptance criteria

- [x] M0 — Scaffold and environment: package metadata, pinned compatible dependencies,
  Make targets, configuration objects, README, and required docs exist; clean install
  succeeds; configuration/schema tests pass.
- [x] M1 — First vertical slice: deterministic timestamped ON/OFF synthesis bins to
  `[T,N,2,180,240]` with configurable duration and repeated counts; one bias-free
  Conv-LIF block with power-of-two beta produces deterministic spikes; unit tests cover
  shape, boundary, repetition, reset, and deterministic output.
- [x] M2 — `f_inst`: enabled/disabled paths, unique winner, tie priority, optional loser
  decrement, and state-reset tests pass.
- [x] M3 — `f_long/T_thresh`: per-channel rise, decay-to-zero, effective-threshold use,
  and deterministic update-order tests pass.
- [x] M4 — Three-layer backbone: exact shapes `[8,90,120]`, `[16,45,60]`,
  `[32,45,60]`, all convolutions shared and `bias=False`, deterministic reset passes.
- [x] M5 — Proposal/objectness: 1×1 spiking objectness and connected-component boxes
  pass synthetic localization, empty-map, and border tests.
- [x] M6 — Classification: predicted-attention spike gating, bias-free class synapses,
  independent hardware-compatible LIF output neurons, deterministic spike-count decoding,
  and retained legacy ROI diagnostics pass unit/integration tests.
- [x] M7 — Tracking: single-object alpha-beta update, prediction, association/rejection,
  loss, and deterministic synthetic trajectory tests pass.
- [x] M8 — Quantization: frozen rounding, clipping, saturation, power-of-two leakage,
  integer LIF, export schema, and float/integer comparison tests pass.
- [x] M9 — Sparse event-scatter: shared-kernel address accumulation equals dense
  convolution for repeated, border, stride, and random seeded fixtures.
- [x] M10 — VHDL-2008 RTL units: synthesizable neuron, competition, homeostasis, and event-conv
  address/accumulation units exist with golden vectors; cocotb equivalence passes under
  an actually executed simulator. This milestone stays incomplete if none is installed.
- [x] M11a — Real MEVDT adapter: official train/test indexes, nanosecond CSV events,
  XYXY boxes, fixed-window alignment, repeated counts, border precision, and
  sequence-disjoint metadata pass fixture and full-index validation.
- [x] M11b — Floating MEVDT training entry point: balanced positive/background sampling,
  baseline `f_inst/f_long` ablation, restartable checkpoint, held-out evaluation, and
  one 1,024-step bounded run execute successfully.
- [x] M11c — Box-free pixel-attention redesign: a bias-free 3×3 spiking attention head at
  `[T,N,1,90,120]`, event-supported weak targets, predicted-attention feature pooling,
  and attention-centroid tracking pass deterministic unit/integration tests. Preserve
  `f_inst`, `f_long/T_thresh`, legacy box evaluation utilities, quantization, sparse
  reference, and VHDL unit paths. The user runs full MEVDT training; Codex must provide
  but not execute the reproducible command.
- [x] M11c2 — Useful real-data attention: on a frozen sequence-disjoint validation set,
  attention Dice/mIoU, centroid error, predicted-attention classification, and tracking
  center precision must be measured. No accuracy claim is allowed before user-run
  training produces and evaluates a new compatible checkpoint.
- [x] M11c3 — Evaluation protocol: deterministic scene-stratified complete-sequence
  validation partition, checkpoint-frozen membership, chronological evaluation, and
  tested success AUC, precision@20, HOTA, MOTA, IDF1, classification F1, and attention
  IoU are implemented.
- [ ] M11c4 — Three-seed MEVDT evidence: train substantially more samples with seeds
  `17`, `101`, and `2026`; evaluate complete validation sequences; diagnose failures;
  select the configuration without touching official test; then run one final complete
  official-test evaluation.
  Acceptance gate: classification F1, HOTA, and tracking success AUC must each be
  nonzero for every candidate seed. A zero value is a benchmark regression, not a valid
  completed run. Follow the BUGS.md reproduce/instrument/regress/fix/retrain/re-evaluate
  loop until the gate passes before advancing to capacity ablations or final test.
- [ ] M11d — EventVOT target-conditioned general-object extension: deferred until M11c4
  passes and the dataset is downloaded. MEVDT remains the sole primary dataset.

## Validation commands

```text
make setup
make test
make lint
make train-smoke
make train-mevdt-smoke
make eval-mevdt-smoke
make validate-reference
make rtl-test
make rtl-test-docker
```

## Progress log

- 2026-08-02: Completed full instruction/specification read and environment inventory.
- 2026-08-02: Created required documentation structure and this self-contained plan.
- 2026-08-02: M0–M4 passed: 9 first-slice tests plus 7 dynamics/backbone tests.
- 2026-08-02: M5–M7 passed: proposal, classification, and tracking synthetic tests.
- 2026-08-02: M8–M9 passed: 9 quantization/sparse equivalence tests.
- 2026-08-02: Installed Icarus Verilog 13.0 and repaired timescale, harness, and signed
  accumulation defects; M10 passed with 5 cocotb simulations.
- 2026-08-02: Tiny dataset adapters and surrogate-gradient smoke step pass. Broadest
  validation: 37 Python tests, lint, smoke training, 9 reference tests, and 5 RTL tests.
- 2026-08-02: Added integrated proposal-driven ROI classification/tracking inference and
  changed smoke training to backpropagate through the full three-layer system.
- 2026-08-02: Final self-review validation passed: 39 Python tests in 2.11 seconds,
  lint, end-to-end smoke training, 9 reference tests, and 5 Icarus/cocotb RTL tests.
- 2026-08-03: User selected VHDL-2008 as the required RTL language and replaced the
  blanket Spiker+ prohibition with evidence-driven optional framework reuse. M10 was
  reopened until the five ported VHDL units pass GHDL/cocotb equivalence.
- 2026-08-03: Replaced all five SystemVerilog prototypes with VHDL-2008 entities, changed
  the runner to GHDL, repaired one non-static aggregate, and passed 5/5 cocotb tests.
- 2026-08-03: Reviewed Spiker+ official sources. Its current FC/FC-recurrent accelerator
  is not a sensible main backend for EventSCNN's sparse shared-kernel convolution, so no
  dependency was added. Isolated compatible components remain candidates for later reuse.
- 2026-08-03: Added YAML policy regression tests and completed broad validation: 41
  Python tests, lint, end-to-end smoke training, 9 reference tests, and 5 GHDL/cocotb
  VHDL-2008 simulations all pass.
- 2026-08-03: Indexed the downloaded MEVDT using its official split CSVs: 10,067 train
  frames in 51 sequences and 2,627 test frames in 12 sequences, with no overlap.
- 2026-08-03: Fixed nanosecond conversion, XYXY parsing, floating border noise, detached
  surrogate gradients, and relative-symlink checkpoint metadata with regressions.
- 2026-08-03: Trained a balanced 1,024-step SpikingJelly-surrogate baseline and evaluated
  128 held-out frames. Oracle-ROI classification reached a measurable early baseline,
  but proposal recall@0.5 is zero; M11c remains open.
- 2026-08-03: Diagnosed the old 20 ms filled-box/1×1 objectness path, changed Conv3 to
  stride 1, implemented event-supported half-resolution attention, predicted-attention
  pooling, centroid tracking, and compatible MEVDT training/evaluation. Focused mechanics
  validation passed 20 tests. Deleted only obsolete generated checkpoints and caches.
- 2026-08-03: Final self-review passed YAML parsing, Ruff, 55 Python tests, the
  end-to-end surrogate-gradient smoke optimizer, 9 quantized/sparse reference tests,
  and 5 GHDL/cocotb VHDL-2008 simulations. No MEVDT training was run by Codex. Test and
  lint caches were removed again after validation; `artifacts/checkpoints/` is empty.
- 2026-08-04: Reproduced the user checkpoint's attention silence and repaired the
  window-target/rate mismatch, initialization, positive balancing, Conv1 support loss,
  dataset-order sampling bias, repeated CSV scans, and ineffective large-map `f_long`.
  Trained matched plain, `f_inst`, and calibrated `f_inst+f_long` 1,024-step checkpoints.
  Selected `f_inst` for localization/sparsity (IoU `0.536611`, classification `0.7890625`,
  tracked center precision@20 `1.0`) and retained combined dynamics as a measured
  classification ablation (`0.921875` classification, `0.459352` IoU).
- 2026-08-04: Post-repair self-review passed Ruff, 59 Python tests, the end-to-end
  gradient smoke step, 9 quantized/sparse tests, and 5 actually executed GHDL/cocotb
  VHDL-2008 simulations. Kept only the three meaningful 1,024-step checkpoints and made
  the selected `f_inst` model canonical at `artifacts/checkpoints/mevdt_attention.pt`.
- 2026-08-04: Replaced the remaining analog classification readout with attention-gated
  bias-free synapses and class LIF neurons. Diagnosed class-level `f_inst` spike starvation,
  made output neurons independent, and retrained 1,024 balanced steps. The bounded held-out
  gate reached classification `0.828125`, attention IoU `0.523869`, centroid error `7.1510`
  pixels, and tracked precision@20 `0.953125`. Post-change self-review passed Ruff,
  59 Python tests, the gradient smoke optimizer, 9 quantized/sparse tests, and 5 actually
  executed GHDL/cocotb VHDL-2008 unit simulations. Removed all incompatible/diagnostic
  checkpoints and retained only `artifacts/checkpoints/mevdt_attention.pt`.
- 2026-08-04: Documented a future synthesis-guided hybrid memory hierarchy to avoid a
  BRAM-only fit bottleneck: deep convolution state in BRAM, suitable small/high-access
  attention, weight, FIFO, queue, lookup, and scratch memories in LUTRAM, and tiny state
  in registers. No RTL placement or FPGA utilization result was produced in this slice.
- 2026-08-04: Recovered the project on Windows with a clean Python 3.11 environment and
  the external Desktop dataset. The full 65-test suite and Ruff pass. Native GHDL 6.0.0
  reaches elaboration but cannot load cocotb's Windows VPI DLL; a read-only Docker route
  passes all 5 VHDL-2008 simulations using GHDL 2.0.0/cocotb 1.9.2.
- 2026-08-04: Recovered the completed seed-17 4,096-step checkpoint and its full
  10-sequence/1,424-frame validation metrics.
- 2026-08-04: Made CPU-only Docker Compose the canonical Windows/macOS environment for
  tests, training/evaluation, reference checks, and RTL simulation. Python (65), Ruff,
  and RTL (5) services pass from the 1.85 GB slim image. The large CUDA experiment, native
  virtual environments, temporary checkpoints, and unused build cache were removed.
  Imported and verified the 2.0 GB MEVDT named volume for subsequent training runs.
- 2026-08-04: Re-ran seed 101 to completion in Docker (4,096 balanced steps) and
  evaluated all 1,424 validation frames. Attention IoU reached `0.735156`, but both
  predicted/oracle classification collapsed to background (F1 `0.0`) and produced no
  tracks. Preserved the checkpoint and recorded the regression; seed 2026 remains.
- 2026-08-04: Completed the zero-metric fix loop. Matched class traces identified
  seed-101 output saturation, not silence. Added trace export, a nonzero benchmark gate,
  and a five-bit class-current scale. The repaired 4,096-step seed-101 checkpoint passed
  all 1,424 validation frames with classification F1 `0.929260`, HOTA `0.469137`,
  tracking success AUC `0.567106`, and attention IoU `0.759312`.

## Discoveries

- The required `AGENTS.md` was absent; the full instructions were supplied as
  `agent.md`. A compatibility pointer is part of M0.
- Native Windows GHDL cannot load cocotb's VPI DLL; Docker is the verified local RTL
  execution path.

## Decisions

See `docs/DECISIONS.md`. The frozen ordering, tie rule, countdown homeostasis, and
synthetic-first strategy are normative for this plan.

## Unresolved risks

- Python 3.9 constrains compatible PyTorch/SpikingJelly versions.
- Dependency download may require network approval.
- VHDL unit equivalence passes; network-level routing/integration VHDL is not implemented.
- Homebrew currently warns that its GHDL cask will be disabled on 2026-09-01 because of
  a macOS Gatekeeper check; CI or an alternative supported installation path is needed
  for long-term reproducibility, although GHDL 6.0.0 executed successfully in this run.
- A concurrent external commit (`070fa2d`) tracked initial `.venv` files. Ignore rules
  prevent further additions, but repository-index cleanup remains.
- EventVOT is the documented later general-object path but is intentionally deferred;
  MEVDT is the sole primary dataset and is available locally.
- Two seeds now have complete validation results and the seed-101 classifier collapse is
  repaired. Seed 2026 remains unmeasured. The old 128-frame official-test subset was used
  for development and must not be presented as an untouched final test result.
- The hybrid BRAM/LUTRAM policy is unsynthesized; port replication, banking, and routing
  may change individual placements after a target Artix-7 part is selected.

## Next concrete action

Run seed 2026 with the frozen five-bit classification-current scale, complete the same
chronological validation, and compare all three seeds. Return to the zero-metric bug loop
if any core gate fails. Do not evaluate the official test split for model selection.
