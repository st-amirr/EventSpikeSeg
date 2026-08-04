# EventSCNN-FPGA

EventSCNN-FPGA is a synthetic-first reference implementation of a trainable,
hardware-oriented event-camera convolutional SNN and its independent sparse FPGA path.
The canonical input is a fixed-duration `[T, N, 2, 180, 240]` ON/OFF event-count tensor.
The planned VHDL backend uses a synthesis-guided hybrid memory hierarchy: large deep
neuron-state maps in BRAM, appropriate small/high-access memories in distributed LUTRAM,
and tiny channel/class/control state in registers. This is a future implementation policy,
not a current FPGA-utilization claim.

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

The primary learned path is fully spiking: event-supported pixel attention gates Conv3
spikes, bias-free class synapses drive class LIF neurons, and emitted spike counts select
the class. Boxes are not an inference ROI. Run a bounded development job with:

```bash
.venv/bin/python -m eventscnn.train_mevdt --root data/mevdt \
  --window-steps 50 --max-samples 1024 --f-inst \
  --checkpoint artifacts/checkpoints/mevdt_attention.pt
.venv/bin/python -m eventscnn.evaluate_mevdt --root data/mevdt \
  --checkpoint artifacts/checkpoints/mevdt_attention.pt --max-samples 128
```

MEVDT is currently a binary vehicle/background baseline. Increase `--max-samples` only
after the bounded command completes successfully. It does not replace FE108 for the
planned 21-class model, and no accuracy is claimed until evaluation actually runs.

`make rtl-test` requires GHDL with VHDL-2008 support and
cocotb. It reports a blocker rather than claiming success when the simulator is absent.

The implementation is driven by `project_spec.yaml`; architecture, decisions, measured
results, bugs, and the resumable execution plan live under `docs/`.

No dataset is downloaded by setup or tests. No model accuracy or FPGA implementation
metric is implied by synthetic validation.
