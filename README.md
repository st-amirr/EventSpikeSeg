# EventSCNN-FPGA

EventSCNN-FPGA is a synthetic-first reference implementation of a trainable,
hardware-oriented event-camera convolutional SNN and its independent sparse FPGA path.
The canonical input is a fixed-duration `[T, N, 2, 180, 240]` ON/OFF event-count tensor.
The planned VHDL backend uses a synthesis-guided hybrid memory hierarchy: large deep
neuron-state maps in BRAM, appropriate small/high-access memories in distributed LUTRAM,
and tiny channel/class/control state in registers. This is a future implementation policy,
not a current FPGA-utilization claim.

## Docker Compose setup and validation

Docker Compose is the canonical environment on Windows and macOS. Copy `.env.example`
to `.env`, then set `MEVDT_HOST_ROOT` to the absolute host dataset directory. Build the
CPU-only image and run the environment-independent checks with:

```text
docker compose build
docker compose run --rm test
docker compose run --rm lint
docker compose run --rm train-smoke
docker compose run --rm validate-reference
docker compose run --rm rtl-test
```

Windows/macOS bind-mounted CSV trees are too slow for this dataset's access pattern.
Import MEVDT once into a Docker-managed volume, then use the smoke or full workflow:

```text
docker compose run --rm dataset-import
docker compose run --rm train-mevdt-smoke
docker compose run --rm eval-mevdt-smoke
docker compose run --rm train-mevdt
docker compose run --rm eval-mevdt
```

Full `eval-mevdt` is a workflow gate: it prints the measured JSON and exits nonzero if
classification F1, HOTA, or tracking success AUC is zero. Treat that exit as a benchmark
regression and follow the active BUGS.md diagnostic/fix/retrain loop; do not continue to
capacity ablations or official-test evaluation.

The dataset volume is named `eventscnn-fpga-mevdt`; checkpoints remain on the host under
`artifacts/checkpoints`. The default is the repaired
`mevdt_seed101_scale32_4096.pt`; change `TRAIN_SEED`, `TRAIN_SAMPLES`, and `TRAIN_CHECKPOINT` in
`.env` for each evidence run. Delete only the Docker copy of the dataset with
`docker volume rm eventscnn-fpga-mevdt`; this never deletes the host dataset.

## Optional native setup

Python 3.9–3.12 is supported. From the repository root:

```bash
make setup
make test
make lint
make train-smoke
make validate-reference
```

On Windows, the same Make targets require GNU Make, use `.venv/Scripts/python.exe`, and create the
environment with the Python 3.11 launcher. Direct PowerShell equivalents use:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests scripts verification/cocotb
```

## MEVDT data and training

Use a real symbolic link or pass the dataset root explicitly; a macOS Finder alias is
not traversable by Python. The current machine uses `data/mevdt`, which links to the
download outside the repository. Validate one real optimizer step with:

```bash
make train-mevdt-smoke
```

The smoke target writes `artifacts/checkpoints/mevdt_smoke.pt`; it never overwrites the
canonical or long-run checkpoints. On this Windows machine, point it at the external
dataset with:

```powershell
make train-mevdt-smoke MEVDT_ROOT="C:/Users/stamir/Desktop/Dataset"
```

The primary learned path is fully spiking: event-supported pixel attention gates Conv3
spikes, bias-free class synapses drive class LIF neurons, and emitted spike counts select
the class. Boxes are not an inference ROI. Every new checkpoint freezes a deterministic,
scene-stratified validation partition from the official training sequences. Model
selection uses validation; official test sequences are reserved for final reporting.
Run a bounded development job with:

```bash
.venv/bin/python -m eventscnn.train --root data/mevdt \
  --window-steps 50 --max-samples 1024 --f-inst --seed 17 \
  --checkpoint artifacts/checkpoints/mevdt_attention.pt
.venv/bin/python -m eventscnn.evaluate --root data/mevdt \
  --checkpoint artifacts/checkpoints/mevdt_attention.pt \
  --split validation --max-sequences 1
```

On Windows, replace `.venv/bin/python` with `.venv/Scripts/python.exe` and pass
`C:/Users/stamir/Desktop/Dataset` as `--root`.

Omit both evaluation limits for chronological complete-sequence metrics. Report success
AUC, center precision@20, HOTA, MOTA, IDF1, classification F1, and pixel-attention IoU
for at least three training seeds before choosing an architecture ablation.

MEVDT is the primary training, validation, tracking, and hardware-replay dataset, with a
vehicle-versus-background classification scope. EventVOT is only a deferred future
general-object extension. No accuracy is claimed until the corresponding evaluation runs.

`make rtl-test` requires GHDL with VHDL-2008 support and
cocotb. It reports a blocker rather than claiming success when the simulator is absent.
On Windows, the native GHDL/cocotb VPI DLL may be ABI-incompatible even when both are
installed. Docker Desktop provides the verified fallback without writing to the source
tree:

```powershell
.\scripts\run_rtl_tests_docker.ps1
```

The target uses `python:3.11-bookworm`, installs Debian's GHDL and pinned cocotb test
dependencies inside the disposable container, and mounts this repository read-only.
On systems with GNU Make, `make rtl-test-docker` runs the equivalent command.

The implementation is driven by `project_spec.yaml`; architecture, decisions, measured
results, bugs, and the resumable execution plan live under `docs/`.

No dataset is downloaded by setup or tests. No model accuracy or FPGA implementation
metric is implied by synthetic validation.

## Source layout

The complete trainable neural model now lives in `src/eventscnn/model.py`. It contains the
hardware-compatible LIF dynamics, convolutional backbone, pixel-attention head,
classification head, and `EventSCNNSystem`. Deterministic tracking remains in
`tracking.py` because it is post-processing rather than part of the neural network.

The former `dynamics.py`, `models.py`, `heads.py`, and `system.py` modules were removed.
All model imports must now come directly from `eventscnn.model`; do not recreate the
previous split or compatibility wrappers.
