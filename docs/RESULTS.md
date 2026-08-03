# Results

Only measured results belong here.

## 2026-08-02 bootstrap validation

- Python unit suite: 39 passed in 2.11 seconds on Python 3.9.6 / PyTorch 2.2.2.
- Quantized/sparse reference subset: 9 passed in 1.36 seconds.
- Icarus Verilog 13.0 cocotb RTL unit suite: 5 passed in 1.92 seconds.
- Deterministic end-to-end smoke optimizer step: loss 1.54416668 and maximum Conv1
  weight change 0.00005585. This verifies gradient flow only; it is not an accuracy result.

No dataset accuracy, FPGA resources, timing, power, latency, or throughput has been measured.
