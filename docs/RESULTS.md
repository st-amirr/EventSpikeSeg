# Results

Only measured results belong here.

## 2026-08-02 bootstrap validation

- Python unit suite: 39 passed in 2.11 seconds on Python 3.9.6 / PyTorch 2.2.2.
- Quantized/sparse reference subset: 9 passed in 1.36 seconds.
- Icarus Verilog 13.0 cocotb RTL unit suite: 5 passed in 1.92 seconds.
- Deterministic end-to-end smoke optimizer step: loss 1.54416668 and maximum Conv1
  weight change 0.00005585. This verifies gradient flow only; it is not an accuracy result.

No dataset accuracy, FPGA resources, timing, power, latency, or throughput has been measured.

## 2026-08-03 VHDL migration validation

- Python unit suite including YAML/language-policy regressions: 41 passed in 2.08 seconds.
- Quantized/sparse reference subset: 9 passed in 1.25 seconds.
- GHDL 6.0.0 cocotb VHDL-2008 unit suite: 5 passed in 6.34 seconds after the complete
  replacement of the earlier SystemVerilog sources.
- This is simulation/equivalence evidence only; synthesis and FPGA execution were not run.

## 2026-08-03 MEVDT loader and floating baseline

These measurements are historical results from the superseded box-objectness
architecture. Its generated checkpoints were deleted after the pixel-attention redesign
and the numbers must not be attributed to the new model.

- Official split index: 10,067 train frames / 51 sequences and 2,627 test frames / 12
  sequences, with zero sequence overlap.
- Parsed annotations: 7,816 train boxes and 2,010 test boxes.
- Balanced baseline training: 1,024 optimizer steps (512 positive, 512 background),
  91,371 events in 20×1 ms windows, mean sampled training loss `0.76926452`, final
  sampled loss `0.50544769`, and maximum Conv1 weight change `0.33447054`.
- Held-out balanced subset: 128 frames (64 positive, 64 background). Oracle-ROI binary
  classification accuracy `0.84375`; positive best-proposal mean IoU `0.062355`;
  proposal recall@0.5 `0.0`; background mean proposal count `0.71875`.
- These are early bounded-development measurements, not a converged full-dataset result.
  Oracle-ROI classification is not end-to-end tracking accuracy. The proposal result is
  currently inadequate and no FPGA performance claim is made.

## 2026-08-04 MEVDT pixel-attention repair and dynamics ablations

All values below use the same frozen balanced 128-frame official test subset (64 vehicle,
64 background), 50×1 ms input windows, and a two-spike (`0.04` rate) attention threshold.
They are bounded development measurements, not full-dataset or final-paper results.

- Plain LIF, seeded sequence-diverse 1,024 steps: predicted-attention classification
  `0.8125`, pixel IoU `0.507893`, Dice `0.673646`, precision `0.546974`, recall
  `0.876671`, and centroid error `11.6883` pixels.
- `f_inst`, seeded sequence-diverse 1,024 steps (selected localization checkpoint):
  classification `0.7890625`, pixel IoU `0.536611`, Dice `0.698434`, precision
  `0.594844`, recall `0.845712`, centroid error `11.1092` pixels, tracked centroid error
  `11.0857` pixels, and tracked center precision@20 pixels `1.0`.
- The selected `f_inst` checkpoint attends `0.672454%` of pixels on background frames.
  Only `3.125%` of background frames are completely empty, showing that isolated false
  pixels remain even though their spatial rate is low.
- `f_inst + f_long`, calibrated 1,024 steps: classification `0.921875`, pixel IoU
  `0.459352`, Dice `0.629529`, precision `0.517161`, recall `0.804280`, and centroid
  error `12.4594` pixels. This is retained as a classification-oriented ablation, not
  substituted for the higher-IoU localization checkpoint.
- On a 64-frame diagnostic subset, `f_inst` reduced Conv3 mean spike rate from
  `0.0106812` to `0.00180441` (about 83%) and reduced negative attention activity from
  `0.000590741` to `0.000374248`. These are software spike-rate measurements, not FPGA
  energy, power, latency, or resource results.

## 2026-08-04 post-repair validation

- Ruff passed over `src`, `tests`, scripts, and cocotb verification code.
- Python suite: 59 passed in 1.89 seconds.
- Quantization/sparse reference subset: 9 passed in 0.70 seconds.
- End-to-end surrogate-gradient smoke optimizer passed with loss `0.36416665` and
  maximum Conv1 weight change `0.00002223`.
- GHDL 6.0.0/cocotb VHDL-2008 unit suite: 5 passed in 5.07 seconds, with one cocotb
  experimental-runner API warning.
- These VHDL results cover the existing units only. The new attention pooling and
  centroid-moment RTL units do not exist yet and are the next hardware milestone.

## 2026-08-04 fully spiking readout retraining

The selected model replaces the analog classifier with bias-free synapses and class LIF
neurons. Training used 1,024 balanced optimizer steps (512 vehicle, 512 background),
50×1 ms windows, `f_inst` in the backbone, and independent class output neurons. It
processed 422,677 input events; mean sampled loss was `1.25049026`, final sampled loss
was `1.16529310`, and maximum Conv1 weight change was `0.19084743`.

On the same bounded 128-frame official-test development subset (64 vehicle, 64
background) at a two-spike (`0.04`) attention threshold:

- predicted-attention classification accuracy: `0.828125`;
- oracle-attention classification accuracy through the same spiking readout: `1.0`;
- pixel attention IoU `0.523869`, Dice `0.687551`, precision `0.609991`, recall `0.787708`;
- attention centroid detection rate `1.0` and mean error `7.1510` pixels;
- tracked centroid mean error `7.1101` pixels and precision@20 pixels `0.953125`;
- positive derived-proposal mean best IoU `0.453767` and recall@0.5 `0.4375`;
- background attention pixel rate `0.00679543`; background-empty rate `0.03125`.

These are bounded development measurements on a subset already used for architecture
selection, not untouched final-test or full-dataset results. No FPGA resource, timing,
power, latency, throughput, or end-to-end RTL result is claimed.

## 2026-08-04 fully spiking post-change validation

- Ruff passed over `src`, `tests`, scripts, and cocotb verification code.
- Python suite: 59 passed in 1.61 seconds.
- Quantization/sparse reference subset: 9 passed in 1.09 seconds.
- End-to-end surrogate-gradient smoke optimizer passed with loss `4.35416651` and
  maximum Conv1 weight change `0.00004750`.
- GHDL 6.0.0/cocotb VHDL-2008 unit suite: 5 passed in 5.57 seconds, with one cocotb
  experimental-runner API warning.
- RTL coverage is unchanged: these five units do not yet implement the attention gate,
  class synapse/LIF readout, centroid moments, or network-level integration.
