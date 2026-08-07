# DDD17 semantic architecture ablation

## Objective

Preserve the completed ten-model benchmark and run a second controlled five-model comparison focused on spike-native temporal and homeostatic mechanisms.

## Completed round one

- ten architectures completed with seed 17
- winner: `v10_fpga_hybrid`, mIoU 0.3130
- definitions moved to `top_ten_models.py`
- measured results preserved in `artifacts/ablation/summary.json`
- object and human class collapse identified as an open issue

## Active round two

Compare exactly these five definitions from `top_five_models.py`:

- `f01_v10_plif_long`
- `f02_v10_plif_inst_long`
- `f03_v03_dilated_plif_long`
- `f04_v02_light_plif_inst_long`
- `f05_dilated_aux_plif_long`

All use PLIF and `f_long/T_thresh`; two isolate hidden-layer `f_inst`.

## Fairness contract

- same seed, records, shuffle order, resolution, timesteps, optimizer, schedule, class weights, and loss
- no contender-specific tuning during the first top-five pass
- output to `artifacts/ablation/top_five/`
- select by mIoU; within 0.5 points prefer fewer parameters then lower spike rate

## Acceptance criteria

- Docker lint and tests pass
- all five finish without non-finite loss
- summary contains per-class IoU for every contender
- class-frequency and prediction-count diagnostics are run before promotion
- leading model is repeated with seeds 101 and 2026
- PLIF winner is checked with a quantized power-of-two leak

## Commands

```powershell
docker compose run --rm lint
docker compose run --rm test
docker compose run --rm benchmark-top-five
```

## Next concrete action

Run the top-five benchmark using the completed round-one budget, then inspect whether PLIF/homeostasis improves object, human, and vehicle IoU rather than only aggregate mIoU.
