# DDD17 semantic architecture ablation

## Objective

Use the completed neuron-mechanism screen to freeze the most promising SNN dynamics, then compare width, early receptive field, encoder depth, and context strategy without changing neuron rules between contenders.

## Evidence used

Low-budget mechanism screen: seed 17, 5 epochs, 256 train, 128 held-out, 64×64, 8 internal timesteps.

- best: `f05_v02_light_peer_membrane_inhibition`, mIoU 0.1991
- threshold adaptation improved the controlled v10 comparison slightly
- `winner_peer` inhibition caused near-dead deep encoder activity and ranked last
- peer-membrane inhibition preserved deeper activity and ranked first

## Fixed dynamics for all current contenders

- PLIF
- learnable base threshold
- affine channel scaling
- residual paths
- auxiliary semantic head
- stem-only `peer_membrane` inhibition
- encoder/context `triangular_threshold` adaptation
- output semantic class WTA
- inhibition strength init 0.20
- threshold-adaptation strength init 0.20
- adaptation-duration init 5.0

## Current contenders

1. `f01_base24_multiscale`: 24/48/96, 3×3, multiscale context
2. `f02_wide32_multiscale`: 32/64/128, 3×3, multiscale context
3. `f03_early5x5_multiscale`: 24/48/96, 5×5 stem + first depthwise block
4. `f04_deep4_dilated`: 24/48/96/128, four encoder scales, single dilation-2 context
5. `f05_compact16_dilated`: 16/32/64, three encoder scales, single dilation-2 context

## Fairness contract

- all five use exactly the same neuron/inhibition/adaptation configuration
- same seed, data subset, resolution, timestep count, optimizer, loss, and class weighting in one benchmark run
- no contender-specific hyperparameter tuning
- summary must record mIoU, per-class IoU, pixel predictions, parameter count, and layer spike rates

## Acceptance

The low-budget round ranks structures only. The leader must later be rerun with the larger training budget and seeds 17, 101, and 2026 before canonical promotion. Quantized neuron dynamics and hardware-cost estimates are required before FPGA selection.

## Commands

```powershell
docker compose run --rm lint
docker compose run --rm test
docker compose run --rm benchmark-top-five
```
