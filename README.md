# EventSpikeSeg-FPGA

Lightweight spiking semantic segmentation for the Ev-SegNet semantic extension of DDD17, with a later sparse fixed-point FPGA implementation target.

## Current model organization

The experiment and production code are now separated:

```text
src/eventscnn/model.py              canonical model only
src/eventscnn/model_components.py   shared convolution, decoder, LIF, PLIF, f_inst, f_long
src/eventscnn/top_ten_models.py     frozen round-one ten-model definitions
src/eventscnn/top_five_models.py    active round-two neuromorphic contenders
```

`model.py` currently contains the measured round-one winner, `v10_fpga_hybrid`. It must not accumulate experimental presets again. After the top-five round is confirmed, replace only the canonical architecture in `model.py`.

## Dataset

Host layout:

```text
C:/Users/stamir/Desktop/Dataset/DDD17/
├── events/{train,test}/*.npy
├── labels/{train,test}/*.png
├── images/
└── events_images/       # previews, ignored
```

Docker mounts this directory at `/datasets/DDD17`.

Each event sample is a fixed six-channel statistic image:

```text
2 polarity histograms
2 normalized timestamp means
2 normalized timestamp standard deviations
```

The training tensor is `[T,N,6,H,W]`. Direct encoding repeats the same six-channel sample for `T` internal LIF/PLIF updates. `T` is not a physical camera rate and does not mean timesteps per second.

Classes are `flat`, `construction+sky`, `object`, `nature`, `human`, and `vehicle`; label `255` is ignored.

## Build, inspect, and test

```powershell
docker compose build
docker compose run --rm inspect-ddd17
docker compose run --rm lint
docker compose run --rm test
```

## Round-one benchmark: completed top ten

The preserved benchmark is in:

```text
artifacts/ablation/summary.json
```

The measured ranking by mIoU was:

| rank | architecture | mIoU | parameters | spike rate |
| ---: | --- | ---: | ---: | ---: |
| 1 | `v10_fpga_hybrid` | 0.3130 | 44,016 | 0.1412 |
| 2 | `v03_dw_dilated` | 0.2970 | 40,824 | 0.1125 |
| 3 | `v02_dw_light` | 0.2850 | 30,744 | 0.1305 |
| 4 | `v08_dw_multiscale_aux` | 0.2591 | 44,016 | 0.1051 |
| 5 | `v04_dw_multiscale` | 0.2444 | 42,552 | 0.1188 |

The full ten definitions remain in `top_ten_models.py` for reproducibility. They are no longer mixed into `model.py`.

The round-one results also showed class collapse: class `object` had zero IoU for nearly all models and class `human` had zero IoU for all ten. Treat `v10` as the structural incumbent, not a finished six-class model. Before final publication, inspect ground-truth class counts, images containing each class, predicted class counts, and the confusion matrix.

## Round-two top five

The active contenders combine the strongest round-one structures with spike-native neuron mechanisms:

```text
f01_v10_plif_long
  v10 structure + PLIF + f_long + T_thresh; no hidden f_inst

f02_v10_plif_inst_long
  f01 plus hidden cross-channel f_inst competition

f03_v03_dilated_plif_long
  efficient v03 single-dilation context + PLIF + f_long/T_thresh

f04_v02_light_plif_inst_long
  smallest v02 structure + PLIF + f_inst + f_long/T_thresh

f05_dilated_aux_plif_long
  v03-style dilated context + v08/v10 auxiliary supervision + affine gain + PLIF + f_long
```

All five use PLIF. `f_long` raises feature-map thresholds after firing. `T_thresh=4` holds the adaptive threshold before decay. `f_inst` is tested only in two contenders because forcing a single winning channel at every pixel can improve sparsity but may remove semantic feature combinations.

Run the active second round:

```powershell
docker compose run --rm benchmark-top-five
```

`benchmark-ddd17` is an alias for the same active top-five run:

```powershell
docker compose run --rm benchmark-ddd17
```

Outputs:

```text
artifacts/ablation/top_five/summary.json
artifacts/ablation/top_five/checkpoints/
```

The old suite can be reproduced separately:

```powershell
docker compose run --rm benchmark-top-ten
```

## Train one model

Canonical current model:

```powershell
$env:DDD17_MODEL_SUITE="final"
$env:DDD17_ARCHITECTURE="v10_fpga_hybrid"
docker compose run --rm train-ddd17
```

A top-five contender:

```powershell
$env:DDD17_MODEL_SUITE="top-five"
$env:DDD17_ARCHITECTURE="f01_v10_plif_long"
docker compose run --rm train-ddd17
```

Reset temporary PowerShell variables with:

```powershell
Remove-Item Env:DDD17_MODEL_SUITE -ErrorAction SilentlyContinue
Remove-Item Env:DDD17_ARCHITECTURE -ErrorAction SilentlyContinue
```

## Promote and evaluate

Do not promote until the top-five run is complete and the leading model is checked across seeds 17, 101, and 2026.

```powershell
docker compose run --rm promote-winner
docker compose run --rm eval-ddd17
```

The promotion command reads `artifacts/ablation/top_five/summary.json` by default.

## Hardware interpretation

The intended FPGA path remains:

```text
active spike address
→ shared-kernel weight lookup
→ affected output-address generation
→ weight addition to current/membrane state
→ leak
→ adaptive threshold and optional f_inst
→ spike and subtractive reset
```

PLIF is trained with a continuous per-channel retention value. It is not yet directly hardware-exact; after selection, its learned retention must be quantized to a power-of-two leak or another documented fixed-point form and revalidated.
