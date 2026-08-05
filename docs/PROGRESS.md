# Progress

## Current state

- The canonical backbone has been widened from `2→8→16→32` to `2→32→64→128` while preserving the existing kernels, strides, spatial resolutions, neuron dynamics, attention head, and decoding path. Code and configuration tests now target the wider model.
- All checkpoints and validation metrics recorded before 2026-08-05 are historical results for the smaller backbone. A new 32/64/128 training cycle has not yet been completed, so no accuracy improvement is claimed and the current milestone is retraining plus resource re-estimation.
- Fixed-duration timestamp binning produces deterministic integer `[T,N,2,180,240]`
  tensors and preserves repeated events.
- A SpikingJelly-surrogate, bias-free Conv-LIF slice and canonical three-layer backbone
  pass shape, state reset, deterministic spike, competition, and homeostasis tests.
- A bias-free 3×3 spiking attention head emits `[T,N,1,90,120]`; event-supported
  targets, predicted-attention pooling, classification, centroid/spread extraction, and
  deterministic box-free alpha-beta tracking pass synthetic tests. Legacy box utilities
  remain comparison diagnostics.
- Frozen fixed-point arithmetic and sparse shared-kernel event-scatter convolution pass
  dense/reference equivalence tests and deterministic golden-vector export.
- Synthesizable VHDL-2008 LIF, competition, homeostasis, event address generation, and
  repeated-weight accumulator entities pass cocotb under GHDL 6.0.0.
- Tiny NPZ event adapters and the DAVIS346→240×180 coordinate transform pass without a
  dataset download. Integrated attention-driven classification/tracking passes, and a
  full-system surrogate-gradient smoke optimizer step updates Conv1 weights.
- The real MEVDT adapter reads official split metadata, sequence event CSVs, nanosecond
  timestamps, and XYXY detection labels. It indexes 51 train and 12 test sequences with
  no sequence overlap and passes real-data parsing checks.
- The learned path is now fully spiking: predicted attention gates Conv3 spikes,
  bias-free class synapses drive independent class LIF neurons, and emitted spike counts
  determine the class. A repaired 1,024-step `f_inst` checkpoint measures pixel IoU
  `0.523869`, classification `0.828125`, centroid error `7.1510` pixels, and tracked
  center precision@20 `0.953125` on the documented bounded subset. The earlier analog
  readout checkpoints are superseded and removed.
- No converged full-dataset accuracy, FPGA resource, timing, power, or throughput result
  exists yet. The current figures are bounded development measurements.
- A future hybrid FPGA-memory policy is documented: large convolution state defaults to
  BRAM, suitable attention/weight/FIFO/scratch structures to LUTRAM, and tiny state to
  registers. It has not yet been implemented or synthesized.
- A deterministic scene-stratified MEVDT train/validation partition, checkpoint-frozen
  sequence lists, chronological evaluator, and standard success AUC, precision@20,
  HOTA, MOTA, IDF1, classification F1, and attention-IoU calculations are implemented.
  Seed-17 and seed-101 4,096-step runs and complete 1,424-frame validations are recorded.
  The original seed-101 model established a saturation regression (classification F1,
  HOTA, and tracking AUC all `0.0`). A five-bit class-current scaling repair now passes
  complete validation with classification F1 `0.929260`, HOTA `0.469137`, tracking AUC
  `0.567106`, and attention IoU `0.759312`. Seed 2026 has not started, so the three-seed
  robustness gate remains open.
- MEVDT is the sole primary dataset. EventVOT is documented only as a deferred
  general-object extension; no EventVOT data or result is present.

## Reproduction

On 2026-08-03, `make rtl-test` passed all five VHDL-2008 unit simulations under GHDL
6.0.0. The final migration validation also passed 41 Python tests, lint, end-to-end
smoke training, and 9 fixed-point/sparse reference tests. The earlier
SystemVerilog/Icarus measurements remain historical only.

MEVDT training/evaluation commands are recorded in `README.md`; historical bounded
results are in `docs/RESULTS.md`. Checkpoints are local, Git-ignored artifacts.

The fully spiking post-change self-review passed Ruff, 59 Python tests, the gradient
smoke optimizer, 9 quantized/sparse reference tests, and 5 actually executed
GHDL/cocotb VHDL-2008 simulations. The only retained checkpoint is the compatible
fully spiking model at `artifacts/checkpoints/mevdt_attention.pt`.

After the macOS-to-Windows recovery, a clean Python 3.11 environment indexes the local
dataset as 8,643 training frames and 1,424 validation frames. The full suite passes 65
tests and Ruff. Native Windows GHDL 6.0.0 analyzes the VHDL but cannot load cocotb's VPI
DLL; the read-only Docker fallback passes all 5 RTL simulations with GHDL 2.0.0.

The canonical host-independent environment is now a CPU-only Docker Compose image. Its
read-only-source services pass 65 Python tests, Ruff, and all 5 GHDL/cocotb simulations.
Training/evaluation services use a named MEVDT volume after an explicit one-time import;
the verified 2.0 GB volume now contains the 10,067 indexed source frames. The generated
native `.venv`, temporary checkpoints/caches, CUDA image, and unused Docker build cache
were removed.
