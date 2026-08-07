# EventSpikeSeg-FPGA Agent Instructions

## Mission

Build a lightweight event-camera SNN for six-class DDD17 semantic segmentation, identify the best spike-native architecture, and map the confirmed model to sparse fixed-point VHDL.

## Source-of-truth order

1. `project_spec.yaml`
2. `AGENTS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DECISIONS.md`
5. active execution plan
6. tests and executable commands

## Model-file contract

```text
model.py              canonical architecture only
top_ten_models.py     frozen completed round-one definitions
top_five_models.py    active round-two contenders
model_components.py   shared tested primitives
```

Do not add experimental preset registries back into `model.py`.

## Current experiment state

Round one is complete. `v10_fpga_hybrid` is the incumbent at mIoU 0.3130, but object and human IoU are zero. Round two compares five PLIF models combining the strongest v10/v03/v02/v08 structures with `f_long`, explicit `T_thresh`, and selected `f_inst`.

Run top-five experiments with identical data, seed, resolution, timesteps, optimizer, loss, class weights, and sample budgets. Record the suite name in checkpoints. Do not overwrite the preserved top-ten results.

## Neuron requirements

- `HardwareLIF`: power-of-two leak, subtractive reset
- `ParametricLIF`: learnable per-channel retention for software ablation
- `f_inst`: one winning channel per spatial location when enabled
- `f_long`: per-feature-map adaptive threshold
- `T_thresh`: hold timer before adaptive-threshold decay

PLIF is not hardware-final until its retention is quantized and revalidated against the floating model.

## Finalization

Do not replace the canonical model based on one seed. Require:

- complete top-five benchmark
- rare-class diagnostics
- confirmation with seeds 17, 101, and 2026
- timestep sensitivity check
- quantized-leak validation for a PLIF winner

Keep `README.md`, `project_spec.yaml`, `ARCHITECTURE.md`, `DECISIONS.md`, `PROGRESS.md`, `RESULTS.md`, `BUGS.md`, and the active execution plan synchronized.
