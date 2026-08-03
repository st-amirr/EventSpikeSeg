# EventSCNN-FPGA

EventSCNN-FPGA is a synthetic-first reference implementation of a trainable,
hardware-oriented event-camera convolutional SNN and its independent sparse FPGA path.
The canonical input is a fixed-duration `[T, N, 2, 180, 240]` ON/OFF event-count tensor.

## Setup and validation

Python 3.9–3.12 is supported. From the repository root:

```bash
make setup
make test
make lint
make train-smoke
make validate-reference
```

`make rtl-test` requires GHDL with VHDL-2008 support and
cocotb. It reports a blocker rather than claiming success when the simulator is absent.

The implementation is driven by `project_spec.yaml`; architecture, decisions, measured
results, bugs, and the resumable execution plan live under `docs/`.

No dataset is downloaded by setup or tests. No model accuracy or FPGA implementation
metric is implied by synthetic validation.
