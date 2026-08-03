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

## MEVDT data and training

Use a real symbolic link or pass the dataset root explicitly; a macOS Finder alias is
not traversable by Python. The current machine uses `data/mevdt`, which links to the
download outside the repository. Validate one real optimizer step with:

```bash
make train-mevdt-smoke
```

Longer bounded training and held-out evaluation are explicit commands:

```bash
.venv/bin/python -m eventscnn.train_mevdt --root data/mevdt \
  --max-samples 1024 --checkpoint artifacts/checkpoints/mevdt_baseline_1024.pt
.venv/bin/python -m eventscnn.evaluate_mevdt --root data/mevdt \
  --checkpoint artifacts/checkpoints/mevdt_baseline_1024.pt --max-samples 128
```

MEVDT is currently a binary vehicle/background baseline. It does not replace FE108 for
the planned 21-class model.

`make rtl-test` requires GHDL with VHDL-2008 support and
cocotb. It reports a blocker rather than claiming success when the simulator is absent.

The implementation is driven by `project_spec.yaml`; architecture, decisions, measured
results, bugs, and the resumable execution plan live under `docs/`.

No dataset is downloaded by setup or tests. No model accuracy or FPGA implementation
metric is implied by synthetic validation.
