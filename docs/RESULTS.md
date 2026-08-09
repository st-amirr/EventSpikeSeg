# Results

## 2026-08-06 — Completed round-one ten-model benchmark

Protocol: seed 17, 10 epochs, 2,048 training samples, 512 held-out samples, 64×64 output, 20 internal SNN steps, batch size 4.

| rank | architecture | mIoU | pixel accuracy | parameters | spike rate |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `v10_fpga_hybrid` | 0.3130 | 0.7871 | 44,016 | 0.1412 |
| 2 | `v03_dw_dilated` | 0.2970 | 0.7711 | 40,824 | 0.1125 |
| 3 | `v02_dw_light` | 0.2850 | 0.7808 | 30,744 | 0.1305 |
| 4 | `v08_dw_multiscale_aux` | 0.2591 | 0.7488 | 44,016 | 0.1051 |
| 5 | `v04_dw_multiscale` | 0.2444 | 0.7556 | 42,552 | 0.1188 |
| 6 | `v01_std_unet_light` | 0.2396 | 0.8005 | 193,824 | 0.0849 |
| 7 | `v09_dw_single_skip` | 0.2392 | 0.7521 | 43,728 | 0.1168 |
| 8 | `v07_dw_multiscale_gap` | 0.2182 | 0.7775 | 48,456 | 0.0933 |
| 9 | `v05_dw_multiscale_affine` | 0.2015 | 0.7688 | 43,728 | 0.0786 |
| 10 | `v06_dw_multiscale_bn` | 0.1730 | 0.4855 | 44,904 | 0.1271 |

### Winner per-class IoU

| class | IoU |
| --- | ---: |
| flat | 0.6083 |
| construction+sky | 0.8021 |
| object | 0.0000 |
| nature | 0.1510 |
| human | 0.0000 |
| vehicle | 0.3168 |

The benchmark establishes `v10_fpga_hybrid` as the round-one structural incumbent only. It does not establish a satisfactory six-class model because two classes have zero IoU.

### Interpretation

- `v03` showed that one dilated context block can outperform the heavier parallel multiscale baseline.
- `v02` retained strong mIoU with the lowest parameter count among the leaders.
- `v08` suggests auxiliary supervision is useful enough to carry into round two.
- BN achieved low training loss but poor held-out mIoU, so training loss was not a reliable selection metric.
- GAP and static affine gain did not justify their cost as standalone additions in this run.


## 2026-08-07 — First PLIF/homeostasis top-five completed and rejected

Protocol matched round one: seed 17, 10 epochs, 2,048 training samples, 512 held-out samples, 64×64, 20 internal steps, batch size 4.

| rank | architecture | mIoU | pixel accuracy | parameters | spike rate |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `f01_v10_plif_long` | 0.2464 | 0.7729 | 45,204 | 0.1432 |
| 2 | `f05_dilated_aux_plif_long` | 0.2340 | 0.7571 | 43,092 | 0.1063 |
| 3 | `f03_v03_dilated_plif_long` | 0.2293 | 0.7584 | 41,814 | 0.1089 |
| 4 | `f02_v10_plif_inst_long` | 0.1754 | 0.6933 | 45,204 | 0.1290 |
| 5 | `f04_v02_light_plif_inst_long` | 0.0167 | 0.1004 | 31,542 | 0.0000 |

The best v1 contender was 0.0667 mIoU below the incumbent. Hard hidden competition was harmful, fixed `T_thresh=4` did not adapt to the data, and global `amax` homeostasis could suppress a whole channel after one spike. These are measured failures, not evidence that PLIF itself is unsuitable.


## 2026-08-07 — Completed retinotopic/neuron-mechanism screening run

Protocol recorded in the saved checkpoints: seed 17, 5 epochs, 256 training samples, 128 held-out samples, 64×64 output, 8 internal SNN timesteps.

| rank | architecture | mIoU | pixel accuracy | parameters | spike rate |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `f05_v02_light_peer_membrane_inhibition` | 0.1991 | 0.7607 | 33,455 | 0.0616 |
| 2 | `f02_v10_plif_threshold_adaptation` | 0.1459 | 0.7395 | 46,422 | 0.0470 |
| 3 | `f01_v10_plif_threshold_wta` | 0.1402 | 0.7334 | 46,392 | 0.0457 |
| 4 | `f04_v03_dilated_threshold_adaptation` | 0.1366 | 0.7217 | 42,830 | 0.0513 |
| 5 | `f03_v10_plif_winner_peer_inhibition` | 0.1233 | 0.7384 | 46,437 | 0.0415 |

### Mechanism interpretation

- Adding triangular threshold adaptation to the same v10 family gave a small improvement over PLIF+threshold alone (`0.1459` vs `0.1402`).
- Hidden `winner_peer` inhibition was harmful: its encoder spike rates fell from `0.0474` at enc1 to `0.00306` at enc2 and `0.000149` at enc3, indicating feature starvation.
- Stem-only `peer_membrane` inhibition did not cause that collapse and produced the best mIoU. Its encoder spike rates remained `0.0770`, `0.0363`, and `0.0239`.
- The winning checkpoint learned mean inhibition strength `0.2082`, threshold-adaptation strength `0.1879`, and adaptation duration `5.196`, close to their initial values `0.20`, `0.20`, and `5.0`.
- All five still failed badly on rare classes under this small-data screen. The winner's per-class IoUs were flat `0.4113`, construction+sky `0.7825`, object `0.0006`, nature `0`, human `0`, vehicle `0`.

Because this run used only 256 training samples, it is used to choose neuron dynamics, not to replace the full-budget `v10_fpga_hybrid` incumbent.

## 2026-08-08 — Structural top-five completed

Protocol: seed 17, 8 epochs, 2,048 train samples, 512 held-out samples, 64×64, 15 internal timesteps, batch 14, learning rate 0.002.

| rank | architecture | mIoU | pixel accuracy | parameters | spike rate |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `f05_compact16_dilated` | **0.2596** | **0.7822** | **21,491** | 0.1093 |
| 2 | `f02_wide32_multiscale` | 0.2284 | 0.7763 | 77,751 | 0.0965 |
| 3 | `f04_deep4_dilated` | 0.2079 | 0.6792 | 107,131 | 0.1495 |
| 4 | `f01_base24_multiscale` | 0.1626 | 0.7294 | 46,423 | 0.0497 |
| 5 | `f03_early5x5_multiscale` | 0.1482 | 0.6719 | 49,111 | 0.0670 |

### Per-class evidence driving the next round

| architecture | object | nature | human | vehicle |
| --- | ---: | ---: | ---: | ---: |
| `f02_wide32_multiscale` | **0.0141** | 0.0390 | 0.0000 | 0.0000 |
| `f04_deep4_dilated` | 0.0049 | **0.0712** | 0.0060 | **0.1230** |
| `f05_compact16_dilated` | 0.0002 | 0.0346 | **0.0181** | 0.0757 |

Interpretation:

- `f05` establishes that a small three-stage single-dilation backbone can outperform much larger structures.
- `f02` supports retaining some capacity for feature diversity because it produced the best object IoU.
- `f04` supports retaining deep semantic information because it produced the best aggregate rare-class coverage, especially nature and vehicle.
- `f03` rejects early 5×5 processing.
- the multiscale-average models did not beat the single-dilation models, motivating branch concatenation rather than averaging.
- none of the five beat the historical `v10_fpga_hybrid` result of 0.3130 mIoU.

## Current top-three accuracy experiment — pending DDD17 measurement

| architecture | main hypothesis | parameters |
| --- | --- | ---: |
| `t01_spike_pyramid_concat` | preserve d1/d2/d4 branch identity; binary channel selection; concat decoder | 63,147 |
| `t02_dualpath_detail` | preserve small-class/boundary evidence with a narrow high-resolution spike path | 24,211 |
| `t03_deep_attention_fpn` | retain deep rare-class semantics with low-resolution spike-mask attention + FPN restoration | 108,781 |

No top-three mIoU values are recorded yet. Results must come from `artifacts/ablation/top_three/summary.json`; do not promote a model from synthetic tests or training loss alone.


## Completed top-three accuracy search — seed 17

Protocol: 8 epochs, 2,048 training samples, 512 held-out samples, 64×64 output, 15 internal timesteps, learning rate 0.002.

| Rank | Architecture | mIoU | Pixel accuracy | Parameters | Mean spike rate |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `t02_dualpath_detail` | **0.2728** | **0.7952** | **24,211** | 0.1395 |
| 2 | `t01_spike_pyramid_concat` | 0.1671 | 0.6122 | 63,147 | 0.1145 |
| 3 | `t03_deep_attention_fpn` | 0.1555 | 0.7151 | 108,781 | **0.0592** |

T2 per-class IoU: flat 0.6190, construction+sky 0.8169, object 0.0095, nature 0.0221, human 0.0000, vehicle 0.1691. These are measured benchmark results only. No accuracy result is yet recorded for `final_dualpath_wide32`.
