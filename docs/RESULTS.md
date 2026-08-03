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
