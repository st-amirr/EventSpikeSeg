# EventSpikeSeg Agent Instructions

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
model_components.py   shared tested primitives
top_ten_models.py     frozen completed ten-model benchmark
top_five_models.py    frozen completed structural top-five
top_three_models.py   frozen completed accuracy top-three
train.py              single trainer/benchmark engine for every suite
```

Do not put experimental registries back into `model.py`. Keep completed top-ten/top-five/top-three definitions reproducible. `model.py` now contains only the post-ablation canonical candidate. Measured results belong in `RESULTS.md`, not in the canonical model registry.

## Current evidence

- full-budget structural incumbent: `v10_fpga_hybrid`, seed-17 mIoU 0.3130
- mechanism screen selected PLIF + learnable threshold + stem-only `peer_membrane` inhibition + local triangular threshold adaptation; hidden `winner_peer` inhibition caused severe feature starvation
- completed structural top-five winner: `f05_compact16_dilated`, mIoU 0.2596 with only 21,491 parameters
- `f02_wide32_multiscale` produced the best object IoU in that round (0.0141)
- `f04_deep4_dilated` produced the strongest aggregate rare-class signal, especially nature (0.0712) and vehicle (0.1230)
- early 5×5 processing was harmful; averaged parallel multiscale context did not beat the simpler dilated path
- none of the completed top-five models superseded the 0.3130 incumbent
- completed top-three: T2 dual-path detail 0.2728 mIoU, T1 0.1671, T3 0.1555
- T2 validates a persistent high-resolution detail path; T3 extra depth/attention collapsed toward dominant classes
- canonical candidate is `final_dualpath_wide32` (237,597 params); `v10_fpga_hybrid` remains the measured baseline until the new model is validated

The active question is now whether the scaled dual-path candidate can exceed the 0.3130 measured incumbent under larger/multi-seed training.

## Active neuron-dynamics contract

All current structural contenders use:

- PLIF with learnable per-channel beta
- learnable per-channel base threshold
- affine channel scaling
- residual paths
- auxiliary semantic supervision
- stem-only `peer_membrane` inhibition
- local triangular threshold adaptation in encoder/context
- independent output semantic class spikes with final temporal count argmax

`peer_membrane` preserves simultaneous suprathreshold feature spikes while reducing peer membrane state using retinotopic membrane energy. Do not use hidden `winner_peer` gating in the canonical model.

The triangular threshold process uses learnable threshold-adaptation strength and continuous adaptation duration. These are training parameters only until fixed-point quantization and integer-reference regression pass.

## Completed top-three accuracy search

The three completed contenders intentionally tested different accuracy mechanisms while preserving a hardware-oriented spiking datapath:

- `t01_spike_pyramid_concat`: 24/48/96 encoder; concatenate d1/d2/d4 depthwise spike branches, apply binary spike-count channel selection, fuse with spiking 1×1, and concatenate decoder skips before spiking refinement.
- `t02_dualpath_detail`: compact 16/32/64 semantic path plus a persistent 16-channel high-resolution spiking detail path; concatenate semantic/shallow/detail evidence before binary selection and final spiking fusion.
- `t03_deep_attention_fpn`: 24/48/96/128 encoder; low-resolution binary Q/K coincidence attention with accumulation/comparison/V masking; concatenative FPN restores x4→x3→x2→x1 detail.

Parameter counts are 63,147 / 24,211 / 108,781. A ~100k model is acceptable when it provides a meaningful accuracy gain, but prefer the smaller model when accuracy is effectively equivalent.

Do not introduce dense softmax spatial attention. Attention forward behavior should remain expressible as spike counts, binary masks, accumulators, comparators, and sparse/1×1 projections that can later be quantized.

Fairness rule used: all three used the same seed, data subset, resolution, timestep count, optimizer/loss, and benchmark budget. Do not tune one contender differently during the ranking run.

## Canonical post-ablation candidate

`final_dualpath_wide32` is the 237,597-parameter EventSpikeSeg candidate. It uses a 32/64/128 semantic path, projected PLIF residual bridges across downsampling, residual DW/PW refinement, a persistent 32-channel high-resolution detail path with asymmetric refinement, serial dilation-2 context plus residual concatenated d1/d2/d4 context, one bottlenecked low-resolution spike-mask attention residual, concatenative mid-decoder fusion, and late semantic/shallow/detail concatenation. Final channel selection is a spike-driven 96→96 1×1 projection into PLIF selector neurons. No fourth downsampling level, dense softmax attention, GAP/MLP inference gate, BatchNorm dependency, or hard hidden WTA is used.

Use SpikingJelly public `activation_based` infrastructure where compatible: SpikingJelly convolution/PLIF/surrogate behavior backs the software model, while project code keeps per-channel beta, dynamic threshold, fInst/fLong, and exact reset/order explicit for later integer/RTL/circuit reproduction.

Auxiliary heads are training-only and must be skipped in eval/inference. Canonical training schedule only: 0–70% joint, 70–90% semantic backbone frozen while detail/decoder/selector/heads refine, 90–100% all layers unfrozen at lower LR. Historical benchmark suites do not inherit this schedule. Historical suites are pinned to CE=0.5; the final suite uses CE=1.0.

There is one training implementation: `eventspikeseg.train`. Do not recreate suite-specific training loops. Historical registries define models only. Final best-model selection uses a holdout from the training split, not the official test set.

## Diagnostics

Every active benchmark run must record:

- mIoU and per-class IoU
- ground-truth and predicted pixels per class
- pixel accuracy
- trainable parameter count
- per-layer spike rates, including deep-stage activity when present
- learned beta, threshold, inhibition strength, threshold-adaptation strength, and adaptation duration

## Finalization gates

`model.py` now contains the post-ablation candidate by explicit project decision, but do not call it the validated final architecture from design reasoning alone. Require a larger-budget rerun, seeds 17/101/2026, timestep sensitivity, rare-class diagnostics, quantized neuron validation, and hardware-cost comparison before hardware freeze or accuracy claims.
