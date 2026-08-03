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
- Synthesizable SystemVerilog LIF, competition, homeostasis, event address generation,
  and repeated-weight accumulator units pass cocotb under Icarus Verilog 13.0.
- Tiny NPZ event adapters and the DAVIS346→240×180 coordinate transform pass without a
  dataset download. Integrated proposal-driven ROI classification/tracking passes, and a
  full-system surrogate-gradient smoke optimizer step updates Conv1 weights.
- No training accuracy, FPGA resource, timing, power, or throughput result exists yet.

## Reproduction

On 2026-08-02: `make test` (39 passed in 2.11 seconds), `make lint`, `make train-smoke`,
`make validate-reference` (9 passed), and `make rtl-test` (5 passed) all succeeded.
