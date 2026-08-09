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
top_five_models.py    completed five-model structural search
top_three_models.py   one active three-model accuracy search
model_components.py   shared tested primitives
```

Do not put experimental registries back into `model.py`. Keep completed top-ten/top-five definitions reproducible and place the active accuracy search only in `top_three_models.py`. Measured results belong in `RESULTS.md`, not in the canonical model registry.

## Current evidence

- full-budget structural incumbent: `v10_fpga_hybrid`, seed-17 mIoU 0.3130
- mechanism screen selected PLIF + learnable threshold + stem-only `peer_membrane` inhibition + local triangular threshold adaptation; hidden `winner_peer` inhibition caused severe feature starvation
- completed structural top-five winner: `f05_compact16_dilated`, mIoU 0.2596 with only 21,491 parameters
- `f02_wide32_multiscale` produced the best object IoU in that round (0.0141)
- `f04_deep4_dilated` produced the strongest aggregate rare-class signal, especially nature (0.0712) and vehicle (0.1230)
- early 5×5 processing was harmful; averaged parallel multiscale context did not beat the simpler dilated path
- none of the completed top-five models superseded the 0.3130 incumbent

The active question is now feature preservation/fusion, not another inhibition sweep.

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

`peer_membrane` preserves simultaneous suprathreshold feature spikes while reducing peer membrane state using retinotopic membrane energy. Do not use hidden `winner_peer` gating in the active search.

The triangular threshold process uses learnable threshold-adaptation strength and continuous adaptation duration. These are training parameters only until fixed-point quantization and integer-reference regression pass.

## Active top-three accuracy search

The three current contenders intentionally test different accuracy mechanisms while preserving a hardware-oriented spiking datapath:

- `t01_spike_pyramid_concat`: 24/48/96 encoder; concatenate d1/d2/d4 depthwise spike branches, apply binary spike-count channel selection, fuse with spiking 1×1, and concatenate decoder skips before spiking refinement.
- `t02_dualpath_detail`: compact 16/32/64 semantic path plus a persistent 16-channel high-resolution spiking detail path; concatenate semantic/shallow/detail evidence before binary selection and final spiking fusion.
- `t03_deep_attention_fpn`: 24/48/96/128 encoder; low-resolution binary Q/K coincidence attention with accumulation/comparison/V masking; concatenative FPN restores x4→x3→x2→x1 detail.

Parameter counts are 63,147 / 24,211 / 108,781. A ~100k model is acceptable when it provides a meaningful accuracy gain, but prefer the smaller model when accuracy is effectively equivalent.

Do not introduce dense softmax spatial attention. Attention forward behavior should remain expressible as spike counts, binary masks, accumulators, comparators, and sparse/1×1 projections that can later be quantized.

Fairness rule: all three use the same seed, data subset, resolution, timestep count, optimizer/loss, and benchmark budget. Do not tune one contender differently during the ranking run.

## Diagnostics

Every active benchmark run must record:

- mIoU and per-class IoU
- ground-truth and predicted pixels per class
- pixel accuracy
- trainable parameter count
- per-layer spike rates, including deep-stage activity when present
- learned beta, threshold, inhibition strength, threshold-adaptation strength, and adaptation duration

## Finalization gates

Do not replace canonical `model.py` from one low-budget seed. Require a larger-budget rerun, seeds 17/101/2026, timestep sensitivity, rare-class diagnostics, quantized neuron validation, and hardware-cost comparison.
