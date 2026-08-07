# DDD17 semantic architecture ablation

## Objective

Preserve the completed top-ten and failed top-five-v1 experiments, then run a revised five-model comparison that fixes the measured neuron-dynamics failures.

## Preserved evidence

- top-ten winner: `v10_fpga_hybrid`, mIoU 0.3130
- top-five-v1 winner: `f01_v10_plif_long`, mIoU 0.2464
- v1 lightweight `f04` output spike rate: 0.0000
- old results remain in `artifacts/ablation/top_five/`

## Revised contenders

- `f01r_v10_plif_threshold`
- `f02r_v10_plif_ratehomeo`
- `f03r_v10_plif_grouped_inst`
- `f04r_v03_dilated_plif_ratehomeo`
- `f05r_v02_light_recovered`

## Corrections under test

- learnable per-channel base threshold in addition to PLIF beta
- learnable continuous adaptation tau replacing integer `T_thresh`
- rate-based bidirectional homeostasis using mean spike rate
- learnable adaptation strength and target firing rate
- independent output class spikes; final temporal argmax only
- grouped top-2 scoped f_inst instead of global WTA
- dynamics warm-up and higher learning rate for neuron parameters
- complete-subset class weights, focal/CE/Dice loss, and activity-floor regularization

## Reproducibility contract

- same seed 17, 2,048 train samples, 512 held-out samples, 64×64, 20 steps, 10 epochs
- all five share the same revised training protocol
- output only to `artifacts/ablation/top_five_v2/`
- preserve old checkpoints and summaries

## Acceptance criteria

- Docker lint and tests pass
- all five complete without non-finite loss
- no contender has zero output spike rate
- summary records per-class IoU, class support/predictions, per-layer rates, and learned beta/threshold/tau
- leader beats or meaningfully approaches mIoU 0.3130 without rare-class regression
- leader is repeated with seeds 101 and 2026 before promotion
- learned dynamics are quantized and revalidated before FPGA claims

## Commands

```powershell
docker compose run --rm lint
docker compose run --rm test
docker compose run --rm benchmark-top-five
```

## Next concrete action

Run the revised benchmark and inspect whether object, human, and vehicle predictions increase rather than only flat/construction accuracy.
