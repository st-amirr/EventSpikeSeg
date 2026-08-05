# EventSCNN-FPGA

Hardware-oriented event-camera spiking neural network for MEVDT vehicle detection and tracking.

The current model uses a three-layer spiking backbone:

```text
2 input polarity channels -> 32 -> 64 -> 128 feature channels
```

It produces a shared spiking attention map and vehicle/background class spikes. Deterministic post-processing converts the attention into a centroid, spatial spread, optional connected-component proposals, and a single alpha-beta track.

## Requirements

- Docker Desktop with Docker Compose
- The extracted MEVDT dataset

The MEVDT root must contain at least:

```text
sequences/
labels/
event_samples/
data_splits/
```

## 1. Configure the dataset path

Copy `.env.example` to `.env` and set `MEVDT_HOST_ROOT` to the extracted MEVDT directory.

Windows example:

```text
MEVDT_HOST_ROOT=C:/Users/your-name/Datasets/MEVDT
```

Linux/macOS example:

```text
MEVDT_HOST_ROOT=/home/your-name/datasets/MEVDT
```

The training configuration can also be changed in `.env`:

```text
TRAIN_WINDOW_STEPS=50
TRAIN_SAMPLES=4096
TRAIN_SEED=101
TRAIN_CHECKPOINT=mevdt_seed101_scale32_4096.pt
```

## 2. Build the Docker image

Run from the project root:

```bash
docker compose build
```

## 3. Import MEVDT into the Docker volume

This copies the dataset once into the Docker-managed volume used by training and validation:

```bash
docker compose run --rm dataset-import
```

The source dataset on the host is mounted read-only and is not modified.

## 4. Train the model

Basic training:

```bash
docker compose run --rm train-mevdt
```

The checkpoint is written to:

```text
artifacts/checkpoints/<TRAIN_CHECKPOINT>
```

Default checkpoint:

```text
artifacts/checkpoints/mevdt_seed101_scale32_4096.pt
```

For a two-sample pipeline check before a full run:

```bash
docker compose run --rm train-mevdt-smoke
```

## 5. Validate the trained model

Run chronological validation using the checkpoint selected by `TRAIN_CHECKPOINT`:

```bash
docker compose run --rm eval-mevdt
```

The command prints the validation metrics as JSON, including:

- classification F1
- attention IoU
- tracking success AUC
- HOTA
- MOTA
- IDF1

It also saves eight evenly distributed visual summaries to:

```text
artifacts/Validation/
```

Each JPEG contains:

1. accumulated input event activity
2. accumulated attention spikes
3. event/attention overlay with ground-truth boxes, proposals, centroid, and spread
4. predicted class, class spike counts, center, confidence, and tracker state

For a two-sample validation check:

```bash
docker compose run --rm eval-mevdt-smoke
```

## Typical workflow

```bash
docker compose build
docker compose run --rm dataset-import
docker compose run --rm train-mevdt
docker compose run --rm eval-mevdt
```

## Change the training run

Edit `.env`, for example:

```text
TRAIN_WINDOW_STEPS=50
TRAIN_SAMPLES=8192
TRAIN_SEED=17
TRAIN_CHECKPOINT=mevdt_seed17_8192.pt
```

Then run:

```bash
docker compose run --rm train-mevdt
docker compose run --rm eval-mevdt
```

Training and validation use the same `TRAIN_CHECKPOINT` value.

## Useful maintenance commands

Run the Python tests:

```bash
docker compose run --rm test
```

Run lint checks:

```bash
docker compose run --rm lint
```

Delete only the Docker copy of MEVDT and re-import it:

```bash
docker volume rm eventscnn-fpga-mevdt
docker compose run --rm dataset-import
```

This does not delete the host dataset.

## Current model limitations

- The classifier currently predicts only `background` or `vehicle`.
- The network emits one shared attention spike map for the full scene.
- The primary tracking path returns one dominant centroid and one track.
- Disconnected attention regions can be converted into multiple proposals, but nearby vehicles may merge.
- Bounding boxes are derived from attention or ground-truth annotations; the network does not directly regress box coordinates.

## Main source files

```text
src/eventscnn/model.py      complete trainable spiking model
src/eventscnn/data.py       event binning and MEVDT loading
src/eventscnn/tracking.py   deterministic centroid tracking
src/eventscnn/metrics.py    validation and tracking metrics
src/eventscnn/hardware.py   quantization and sparse FPGA references
src/eventscnn/train.py      training CLI
src/eventscnn/evaluate.py   validation CLI and JPEG generation
```

Detailed design history and measured results are kept under `docs/`.
