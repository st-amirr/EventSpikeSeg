# Progress

## Current state

- Fixed-duration timestamp binning produces deterministic integer `[T,N,2,180,240]`
  tensors and preserves repeated events.
- A SpikingJelly-surrogate, bias-free Conv-LIF slice and canonical three-layer backbone
  pass shape, state reset, deterministic spike, competition, and homeostasis tests.
- Bias-free spiking objectness, connected-component proposals, ROI spike-count
  classification, and deterministic alpha-beta single-object tracking pass synthetic tests.
- Frozen fixed-point arithmetic and sparse shared-kernel event-scatter convolution pass
  dense/reference equivalence tests and deterministic golden-vector export.
- Synthesizable VHDL-2008 LIF, competition, homeostasis, event address generation, and
  repeated-weight accumulator entities pass cocotb under GHDL 6.0.0.
- Tiny NPZ event adapters and the DAVIS346→240×180 coordinate transform pass without a
  dataset download. Integrated proposal-driven ROI classification/tracking passes, and a
  full-system surrogate-gradient smoke optimizer step updates Conv1 weights.
- The real MEVDT adapter reads official split metadata, sequence event CSVs, nanosecond
  timestamps, and XYXY detection labels. It indexes 51 train and 12 test sequences with
  no sequence overlap and passes real-data parsing checks.
- A balanced 1,024-step floating baseline checkpoint was trained with `f_inst/f_long`
  disabled. Held-out oracle-ROI binary classification is measurable, but learned
  proposal recall@0.5 remains zero, so end-to-end detection/tracking is not ready.
- No converged full-dataset accuracy, FPGA resource, timing, power, or throughput result
  exists yet.

## Reproduction

On 2026-08-03, `make rtl-test` passed all five VHDL-2008 unit simulations under GHDL
6.0.0. The final migration validation also passed 41 Python tests, lint, end-to-end
smoke training, and 9 fixed-point/sparse reference tests. The earlier
SystemVerilog/Icarus measurements remain historical only.

MEVDT reproduction commands and bounded measured results are recorded in `README.md`
and `docs/RESULTS.md`. Checkpoints are local, Git-ignored artifacts.
