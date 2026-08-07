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

## Round two

No top-five PLIF/f_long/f_inst result has been measured yet. Results must be written to `artifacts/ablation/top_five/summary.json` before changing the canonical model.

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

## Revised top-five v2

No real DDD17 result yet. The new output location is `artifacts/ablation/top_five_v2/summary.json`. Do not overwrite the v1 results.
