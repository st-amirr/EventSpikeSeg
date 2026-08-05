# EventSpikeSeg-FPGA

Lightweight spiking semantic segmentation for the Ev-SegNet semantic extension of DDD17, with a later sparse FPGA implementation target.

The former MEVDT attention/classification/tracking pipeline is no longer part of the active package. MEVDT can remain beside DDD17 as a separate dataset, but current training and evaluation use DDD17 semantic labels only.

## Dataset used now

Expected host layout (embedded path `Desktop/Dataset/DDD17`):

```text
DDD17/
├── events/
│   ├── train/
│   └── test/
├── labels/
│   ├── train/
│   └── test/
├── images/
└── events_images/   # ignored preview folder
```

The loader uses these folders directly. Event and label files are paired by matching
stems. Preview folders such as `events_images` and `labels/test_colored` are ignored.
Training uses `train`; architecture selection and evaluation use official `test`.

The active loader follows the official Ev-SegNet layout. Each `events/*.npy` sample is a six-channel event representation:

```text
2 polarity histograms
2 normalized timestamp means
2 normalized timestamp standard deviations
```

It is one event-statistic image per labeled sample, not a raw asynchronous `[timestamp, x, y, polarity]` stream. The SNN benchmark uses **direct encoding**: the same six-channel current is presented during each internal SNN timestep. The six channels are never reinterpreted as six timesteps.

Classes:

```text
0 flat
1 construction+sky
2 object
3 nature
4 human
5 vehicle
255 ignore
```

The Ev-SegNet labels are approximate semantic labels generated for selected DDD17 intervals, not native DDD17 ground truth.

## Configure the path

The DDD17 root is embedded for this machine:

```text
C:/Users/stamir/Desktop/Dataset/DDD17
```

Docker mounts that folder read-only at `/datasets/DDD17`. Override only if needed:

```text
DDD17_HOST_ROOT=C:/Users/stamir/Desktop/Dataset/DDD17
```

The default architecture-search resolution is deliberately small:

```text
DDD17_HEIGHT=64
DDD17_WIDTH=64
```

The original Ev-SegNet training resolution was `224 × 352`. Use that only after selecting finalists or when sufficient GPU memory is available:

```text
DDD17_HEIGHT=224
DDD17_WIDTH=352
```

## Build and inspect

```bash
docker compose build
docker compose run --rm inspect-datasets
docker compose run --rm inspect-ddd17
```

`inspect-datasets` must show `/datasets/DDD17` with `events` and `labels` underneath.
The DDD17 inspector should then report train/test records and an Ev-SegNet six-channel
representation. If `labels/train` is missing from the download, inspection reports that
explicitly; re-download the Ev-SegNet package before training.

To verify the resolved Windows bind source before running a container:

```powershell
docker compose config | Select-String -Pattern "DDD17_HOST_ROOT|source:|target: /datasets" -Context 0,1
```

## Run tests

```bash
docker compose run --rm test
docker compose run --rm lint
```

## Smoke test

```bash
docker compose run --rm train-ddd17-smoke
```

This verifies loading, forward/backward propagation, checkpoint writing, and validation on two samples.

## Compare the ten architectures on the same seed

```bash
docker compose run --rm benchmark-ddd17
```

All variants use the same:

- seed and initialization policy
- deterministic training records and official Ev-SegNet test as held-out set
- shuffle order
- class weights
- optimizer and learning-rate schedule
- direct-encoding timestep count
- input/output resolution
- loss and evaluation code

Outputs:

```text
artifacts/ablation/
├── summary.json
└── checkpoints/
```

Selection rule:

1. highest validation mIoU
2. within 0.5 percentage points, fewer parameters
3. if still tied, lower output spike rate

### Ten combinations

```text
v01_std_unet_light
  Standard convolutions, two additive skips, no context module.
  Accuracy-oriented reference; highest convolution cost.

v02_dw_light
  Depthwise spatial convolution + pointwise channel mixing.
  Smallest plain convolutional baseline.

v03_dw_dilated
  Depthwise/pointwise blocks plus one dilated context block.
  Tests larger receptive field without parallel branches.

v04_dw_multiscale
  Parallel depthwise dilation 1/2/4 context.
  Tests local, medium, and broad event context.

v05_dw_multiscale_affine
  v04 plus foldable per-channel gain.
  Hardware-friendly alternative to BatchNorm.

v06_dw_multiscale_bn
  v04 plus BatchNorm.
  Training-stability reference; BN must be folded before deployment.

v07_dw_multiscale_gap
  v05 plus GAP/sigmoid channel recalibration.
  Tests whether global channel selection offsets depthwise isolation.

v08_dw_multiscale_aux
  v05 plus an auxiliary decoder head.
  Tests deeper supervision and gradient stability.

v09_dw_single_skip
  v05 with only the high-resolution skip and adaptive thresholds.
  Lower feature-buffer and decoder cost.

v10_fpga_hybrid
  Multiscale depthwise context, foldable affine gain, two additive skips,
  residual paths, adaptive thresholds, and auxiliary supervision.
```

## Train one selected architecture

Default:

```bash
docker compose run --rm train-ddd17
```

PowerShell override:

```powershell
$env:DDD17_ARCHITECTURE="v05_dw_multiscale_affine"
$env:DDD17_SEED="17"
docker compose run --rm train-ddd17
```

## Promote and evaluate the benchmark winner

```bash
docker compose run --rm promote-winner
docker compose run --rm eval-ddd17
```

The promoted checkpoint is:

```text
artifacts/checkpoints/ddd17_best.pt
```

Visual validation is written to:

```text
artifacts/Validation/
```

Each image contains:

1. the two event-histogram channels
2. ground-truth semantic mask
3. predicted semantic mask
4. maximum class-spike confidence

## Final architecture cleanup

Do not delete the ten presets after one short run. First:

1. run all ten on the same seed
2. retrain the top candidates at higher resolution
3. reproduce the winner with at least two additional seeds
4. freeze the result in `docs/RESULTS.md`

After those checks, remove the losing presets and checkpoints, replace `DEFAULT_ARCHITECTURE` with the winner, and keep only the winner's layers in `model.py`.

## Active source tree

```text
src/eventscnn/model.py     ten temporary SNN segmentation variants
src/eventscnn/data.py      Ev-SegNet DDD17 loader (train/test; test = held-out)
src/eventscnn/train.py     smoke, single-model, benchmark, and promotion commands
src/eventscnn/evaluate.py  mIoU evaluation and visual summaries
src/eventscnn/metrics.py   confusion matrix, mIoU, and pixel accuracy
src/eventscnn/hardware.py  fixed-point helpers for the later FPGA stage
```
