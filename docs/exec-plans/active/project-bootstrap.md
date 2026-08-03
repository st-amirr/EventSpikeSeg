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
  `[32,23,30]`, all convolutions shared and `bias=False`, deterministic reset passes.
- [x] M5 — Proposal/objectness: 1×1 spiking objectness and connected-component boxes
  pass synthetic localization, empty-map, and border tests.
- [x] M6 — Classification: ROI spike-count pooling and configurable-class output pass
  shape, ROI clipping, empty ROI, and deterministic-logit tests.
- [x] M7 — Tracking: single-object alpha-beta update, prediction, association/rejection,
  loss, and deterministic synthetic trajectory tests pass.
- [x] M8 — Quantization: frozen rounding, clipping, saturation, power-of-two leakage,
  integer LIF, export schema, and float/integer comparison tests pass.
- [x] M9 — Sparse event-scatter: shared-kernel address accumulation equals dense
  convolution for repeated, border, stride, and random seeded fixtures.
- [x] M10 — VHDL-2008 RTL units: synthesizable neuron, competition, homeostasis, and event-conv
  address/accumulation units exist with golden vectors; cocotb equivalence passes under
  an actually executed simulator. This milestone stays incomplete if none is installed.
- [ ] M11 — Integrated/data milestones: synthetic end-to-end smoke training passes;
  FE108/MEVDT loaders pass metadata/tiny-fixture tests. Dataset accuracy, synthesis,
  board replay, power, and throughput require the corresponding external assets/tools
  and must not be claimed from synthetic tests.

## Validation commands

```text
make setup
make test
make lint
make train-smoke
make validate-reference
make rtl-test
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

## Discoveries

- The required `AGENTS.md` was absent; the full instructions were supplied as
  `agent.md`. A compatibility pointer is part of M0.
- The initial environment has no Python ML/test dependencies and no RTL simulator.

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
- Full dataset/training and FPGA measurements are external-resource milestones.

## Next concrete action

Complete M11 by adding real-format FE108 AEDAT4 and MEVDT event/annotation adapters using
tiny redistributable or user-provided samples, then test timestamp/annotation alignment
and sequence-disjoint split metadata. Do not download the full datasets or report task
accuracy until those samples and official split information are available.
