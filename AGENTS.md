# EventSpikeSeg-FPGA Agent Instructions

## Mission

Build a lightweight event-camera SNN for six-class DDD17 semantic segmentation, select a strong spike-native architecture, then map the confirmed model to sparse fixed-point VHDL.

## Source-of-truth order

1. `project_spec.yaml`
2. `AGENTS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DECISIONS.md`
5. active ablation plan
6. tests and executable commands

## Model-file contract

```text
model.py              canonical architecture only
top_ten_models.py     frozen completed ten-model benchmark
top_five_models.py    one active five-model structural search
model_components.py   shared tested primitives
```

Do not put experimental registries back into `model.py`. Do not create versioned active top-five registries; measured old results belong in `RESULTS.md`, not in the active model registry.

## Current evidence

- full-budget structural incumbent: `v10_fpga_hybrid`, seed-17 mIoU 0.3130
- latest low-budget mechanism screen: seed 17, 5 epochs, 256 train, 128 held-out, 64×64, 8 timesteps
- mechanism-screen winner: `f05_v02_light_peer_membrane_inhibition`, mIoU 0.1991
- controlled v10 comparison: triangular threshold adaptation slightly improved PLIF+threshold (`0.1459` vs `0.1402`)
- hidden `winner_peer` inhibition ranked last (`0.1233`) and nearly silenced deep encoder activity
- selected hidden mechanism: stem-only `peer_membrane` inhibition plus encoder/context triangular threshold adaptation

The low-budget screen selects dynamics only; it does not supersede the 0.3130 full-budget incumbent.

## Active neuron-dynamics contract

All current structural contenders use:

- PLIF with learnable per-channel beta
- learnable per-channel base threshold
- affine channel scaling
- residual paths
- auxiliary semantic supervision
- stem-only `peer_membrane` inhibition
- local triangular threshold adaptation in encoder/context
- output semantic class WTA

`peer_membrane` preserves simultaneous suprathreshold feature spikes while reducing peer membrane state using retinotopic membrane energy. Do not use hidden `winner_peer` gating in the active top five.

The triangular threshold process uses learnable threshold-adaptation strength and continuous adaptation duration. These are training parameters only until fixed-point quantization and integer-reference regression pass.

## Active top-five structural search

The five current contenders differ structurally while keeping neuron dynamics identical:

- `f01_base24_multiscale`: 24/48/96, 3×3, multiscale context
- `f02_wide32_multiscale`: 32/64/128, 3×3, multiscale context
- `f03_early5x5_multiscale`: 24/48/96, 5×5 stem + first depthwise block
- `f04_deep4_dilated`: 24/48/96/128, four encoder scales, dilation-2 context
- `f05_compact16_dilated`: 16/32/64, dilation-2 context

Fairness rule: no contender-specific neuron, optimizer, loss, data, timestep, or warm-up tuning during one benchmark comparison.

## Diagnostics

Every top-five run must record:

- mIoU and per-class IoU
- ground-truth and predicted pixels per class
- pixel accuracy
- trainable parameter count
- per-layer spike rates, including `enc4_spikes` when present
- learned beta, threshold, inhibition strength, threshold-adaptation strength, and adaptation duration

## Finalization gates

Do not replace canonical `model.py` from one low-budget seed. Require a larger-budget rerun, seeds 17/101/2026, timestep sensitivity, rare-class diagnostics, quantized neuron validation, and hardware-cost comparison.
