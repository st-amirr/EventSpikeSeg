# EventSpikeSeg-FPGA

Lightweight fully-spiking semantic segmentation for the Ev-SegNet semantic extension of DDD17, with a later sparse fixed-point FPGA target.

## Project layout

```text
src/eventscnn/model.py              canonical model only (`v10_fpga_hybrid` for now)
src/eventscnn/model_components.py   shared spiking layers and neuron dynamics
src/eventscnn/top_ten_models.py     frozen completed ten-model structural benchmark
src/eventscnn/top_five_models.py    completed five-model structural search
src/eventscnn/top_three_models.py   current accuracy-oriented three-model search
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

## Current top three: accuracy-oriented search

`top_three_models.py` contains three intentionally different hypotheses rather than minor variants:

```text
t01_spike_pyramid_concat       63,147 params
  24→48→96 encoder
  d1/d2/d4 depthwise spike branches
  CONCAT instead of branch averaging
  binary spike-count channel selection
  1×1 spiking fusion
  concatenative decoder skip fusion

t02_dualpath_detail            24,211 params
  compact 16→32→64 semantic encoder
  single dilation-2 semantic context
  persistent 16-channel high-resolution spiking detail path
  final semantic + shallow + detail CONCAT
  binary spike-count channel selection

t03_deep_attention_fpn        108,781 params
  24→48→96→128 four-stage encoder
  low-resolution dilation-2 context
  32-channel / 4-head binary spike-mask attention
  no dense spatial softmax attention
  concatenative FPN decoder restoring x4→x3→x2→x1 information
```

All three preserve binary spike transmission between learned stages and use depthwise spatial convolution plus pointwise channel mixing where practical. Attention is deliberately spike-oriented: the channel selector uses spike counts and a hard binary gate, while the deep model uses Q/K binary coincidence, integer-like accumulation, a learned comparator threshold, and V masking at low resolution.

The round uses the same fixed benchmark protocol as the completed structural five and writes only to:

```text
artifacts/ablation/top_three/summary.json
artifacts/ablation/top_three/checkpoints/
```

Run it with:

```powershell
docker compose run --rm benchmark-top-three
```

## Selection rule

Use mIoU as the primary metric. Also inspect per-class IoU, predicted-pixel counts, layer spike rates, and parameter count. A low-budget winner must be rerun with the larger protocol and multiple seeds before replacing `model.py`.
