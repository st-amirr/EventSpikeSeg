# EventSpikeSeg-FPGA

Lightweight fully-spiking semantic segmentation for the Ev-SegNet semantic extension of DDD17, with a later sparse fixed-point FPGA target.

## Project layout

```text
src/eventscnn/model.py              canonical model only (`v10_fpga_hybrid` for now)
src/eventscnn/model_components.py   shared spiking layers and neuron dynamics
src/eventscnn/top_ten_models.py     frozen completed ten-model structural benchmark
src/eventscnn/top_five_models.py    current five-model structural search
```

`model.py` is not changed until a contender beats the incumbent and passes wider validation.

## DDD17 input

Host dataset:

```text
C:/Users/stamir/Desktop/Dataset/DDD17/
├── events/{train,test}/*.npy
└── labels/{train,test}/*.png
```

Docker mounts it at `/datasets/DDD17`. Each sample is the Ev-SegNet six-channel event-statistic representation and is applied for `T` internal SNN updates.

Classes: `flat`, `construction+sky`, `object`, `nature`, `human`, `vehicle`. Label `255` is ignored.

## Basic commands

```powershell
docker compose run --rm inspect-ddd17
docker compose run --rm lint
docker compose run --rm test
docker compose run --rm benchmark-top-five
```

Benchmark defaults are defined directly in `compose.yaml`:

```text
seed=17
epochs=8
time_steps=15
train_samples=2048
validation_samples=512
height=64
width=64
batch_size=14
learning_rate=0.002
```

Edit `compose.yaml` directly when intentionally changing these defaults. The project does not use a `.env` file.

## Measured structural incumbent

The completed ten-model benchmark used seed 17, 10 epochs, 2,048 train samples, 512 held-out samples, 64×64 output, and 20 internal steps.

```text
v10_fpga_hybrid
mIoU            0.3130
pixel accuracy  0.7871
parameters      44,016
spike rate      0.1412
```

This remains the canonical model.

## Completed neuron-mechanism comparison

The latest five-model mechanism run used seed 17, 5 epochs, 256 train samples, 128 held-out samples, 64×64 output, and 8 internal steps. It was intentionally a low-budget screening run.

```text
f05_v02_light_peer_membrane_inhibition  mIoU 0.1991
f02_v10_plif_threshold_adaptation       mIoU 0.1459
f01_v10_plif_threshold_wta              mIoU 0.1402
f04_v03_dilated_threshold_adaptation    mIoU 0.1366
f03_v10_plif_winner_peer_inhibition     mIoU 0.1233
```

The useful mechanism conclusions are:

- keep PLIF and learnable base thresholds;
- keep local triangular threshold adaptation;
- keep `peer_membrane` inhibition, restricted to the stem;
- reject hidden `winner_peer` gating for dense segmentation;
- keep affine channel scaling, residual paths, auxiliary supervision, and semantic output class WTA.

The winning model learned approximately `inhibition_strength=0.208`, `threshold_adaptation_strength=0.188`, and `adaptation_duration=5.20`, close to the chosen initial values `0.20`, `0.20`, and `5.0`.

## Current top five: structural search

All five now use the same selected neuron dynamics above. The experiment therefore varies architecture rather than mixing architecture and inhibition rules.

```text
f01_base24_multiscale
  24→48→96, 3×3 spatial kernels, three encoder scales, multiscale context

f02_wide32_multiscale
  32→64→128, 3×3 spatial kernels, three encoder scales, multiscale context

f03_early5x5_multiscale
  24→48→96, 5×5 stem + first depthwise block, then 3×3, multiscale context

f04_deep4_dilated
  24→48→96→128, four encoder scales, 3×3 kernels, single dilated context

f05_compact16_dilated
  16→32→64, three encoder scales, 3×3 kernels, single dilated context
```

Approximate trainable parameter counts are respectively `46,423`, `77,751`, `49,111`, `107,131`, and `21,491`.

Outputs are written to:

```text
artifacts/ablation/top_five/summary.json
artifacts/ablation/top_five/checkpoints/
```

## Selection rule

Use mIoU as the primary metric. Also inspect per-class IoU, predicted-pixel counts, layer spike rates, and parameter count. A low-budget winner must be rerun with the larger protocol and multiple seeds before replacing `model.py`.
