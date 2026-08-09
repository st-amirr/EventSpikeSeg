# EventSpikeSeg-FPGA

Lightweight fully-spiking semantic segmentation for the Ev-SegNet semantic extension of DDD17, with a later sparse fixed-point FPGA target.

## Project layout

```text
src/eventscnn/model.py              canonical high-accuracy candidate (`final_dualpath_wide32`)
src/eventscnn/model_components.py   shared spiking layers and neuron dynamics
src/eventscnn/top_ten_models.py     frozen completed ten-model structural benchmark
src/eventscnn/top_five_models.py    completed five-model structural search
src/eventscnn/top_three_models.py   frozen completed accuracy-oriented three-model search
```

`model.py` now contains the post-ablation high-accuracy candidate. Historical benchmark registries remain frozen; the new canonical model still requires larger-budget/multi-seed validation before its accuracy is claimed.

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
docker compose run --rm benchmark-top-three
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

This remains the **measured historical incumbent**, but it is no longer the architecture installed in `model.py`.

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

## Completed top five: structural search

The structural round used seed 17, 8 epochs, 2,048 train samples, 512 held-out samples, 64×64 output, 15 internal timesteps, batch 14, and learning rate 0.002. All five used the same selected neuron dynamics so width/depth/kernel/context could be compared fairly.

| Rank | Architecture | mIoU | Pixel accuracy | Params | Spike rate |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `f05_compact16_dilated` | **0.2596** | 0.7822 | **21,491** | 0.1093 |
| 2 | `f02_wide32_multiscale` | 0.2284 | 0.7763 | 77,751 | 0.0965 |
| 3 | `f04_deep4_dilated` | 0.2079 | 0.6792 | 107,131 | 0.1495 |
| 4 | `f01_base24_multiscale` | 0.1626 | 0.7294 | 46,423 | 0.0497 |
| 5 | `f03_early5x5_multiscale` | 0.1482 | 0.6719 | 49,111 | 0.0670 |

The main findings were more useful than the ranking alone:

- the compact `16→32→64` single-dilation model was both the most accurate and the smallest, so parameter count alone is not the current bottleneck;
- the wide `32→64→128` model produced the best `object` IoU in this round (`0.0141`), so some extra channel diversity can help rare features;
- the four-stage model produced the strongest aggregate rare-class signal, especially `nature=0.0712` and `vehicle=0.1230`, suggesting that the deep path contains useful semantics which the old decoder does not preserve well;
- early `5×5` processing hurt accuracy and is dropped;
- averaged parallel dilation branches did not justify their cost. The next round preserves each sparse receptive-field branch by concatenating it before learned spiking fusion.

None of these five displaced the historical `v10_fpga_hybrid` incumbent at `0.3130` mIoU.

## Completed top three: accuracy-oriented search

The top-three benchmark completed under the same seed-17 / 2,048-train / 512-held-out / 64×64 / 15-step protocol used for the structural round.

| Rank | Architecture | mIoU | Pixel accuracy | Params | Spike rate |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `t02_dualpath_detail` | **0.2728** | **0.7952** | **24,211** | 0.1395 |
| 2 | `t01_spike_pyramid_concat` | 0.1671 | 0.6122 | 63,147 | 0.1145 |
| 3 | `t03_deep_attention_fpn` | 0.1555 | 0.7151 | 108,781 | **0.0592** |

T2 validated the persistent high-resolution detail-path hypothesis. T1 showed that parallel dilation concat/channel selection was not sufficient by itself. T3 retained deep spike activity but collapsed its predictions toward the two dominant classes, so the final design does not add a fourth downsampling level or low-resolution attention.

## Canonical post-ablation model

`final_dualpath_wide32` scales the successful dual-path idea without importing the failed complexity:

```text
semantic path: 32 → 64 → 128
per-scale residual depthwise/pointwise refinement
persistent high-resolution 32-channel detail path
two serial dilation-2 residual context blocks
stronger 128→64→32 decoder
mid-level additive skip + late semantic/shallow/detail concatenation
PLIF 1×1 cross-channel selector (spike-driven synaptic mixing + PLIF binary gating)
independent spiking class neurons; final decision is temporal spike-count argmax
PLIF + learnable threshold + stem-only peer_membrane fInst
encoder/context triangular fLong homeostasis
```

The model has approximately 141k trainable parameters. It is intentionally kept spike/circuit friendly: no BatchNorm dependence, dense softmax attention, GAP/MLP inference gate, or analog classifier is present in the canonical path.

Training uses the existing weighted CE/focal/Dice objective with the main CE coefficient set to `1.0`. The final model additionally exposes a late refinement schedule: joint training through 70% of epochs, semantic-backbone freeze during 70–90% while detail/decoder/heads continue training, then full low-LR unfreeze for the final 10%.

## Selection rule

Use mIoU as the primary metric. Also inspect per-class IoU, predicted-pixel counts, layer spike rates, and parameter count. The new canonical candidate must beat the measured `v10_fpga_hybrid` baseline under a larger protocol and seeds 17/101/2026 before it is treated as the validated final architecture or frozen for hardware.
