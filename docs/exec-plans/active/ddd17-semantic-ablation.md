# DDD17 semantic architecture ablation

## Objective

Increase six-class DDD17 mIoU without abandoning a spike-oriented, FPGA/neuromorphic-friendly datapath. The current round focuses on preserving sparse multi-scale evidence, small-object spatial detail, and deep semantic information rather than simply increasing model size.

## Evidence accumulated so far

### Round 1 — structural baseline

`v10_fpga_hybrid` remains the incumbent at mIoU 0.3130 with 44,016 parameters under the original 10-epoch/20-timestep benchmark.

### Neuron-mechanism screen

The low-budget mechanism screen selected PLIF + learnable base threshold + stem-only `peer_membrane` inhibition + encoder triangular threshold adaptation. Hidden `winner_peer` inhibition nearly silenced the deep encoder and is excluded.

### Completed structural top five

Protocol: seed 17, 8 epochs, 2,048 train, 512 held-out, 64×64, 15 internal timesteps, batch 14, LR 0.002.

1. `f05_compact16_dilated`: mIoU **0.2596**, 21,491 params
2. `f02_wide32_multiscale`: mIoU 0.2284, 77,751 params
3. `f04_deep4_dilated`: mIoU 0.2079, 107,131 params
4. `f01_base24_multiscale`: mIoU 0.1626, 46,423 params
5. `f03_early5x5_multiscale`: mIoU 0.1482, 49,111 params

Findings:

- compact single-dilation processing was the strongest accuracy/parameter point;
- width helped `object` detection somewhat;
- four encoder stages produced the best aggregate rare-class coverage, especially nature/vehicle, but the old decoder failed to turn that into strong overall mIoU;
- early 5×5 processing is rejected;
- averaging parallel dilation branches is rejected for the next round because it mixes sparse receptive-field evidence before the model can learn how to use it.

## Round 4 — active top-three accuracy search

All three are defined in `src/eventspikeseg/top_three_models.py` and use the same benchmark protocol as the completed structural five.

### T1 — `t01_spike_pyramid_concat`

- 24/48/96 encoder, 3×3 spatial kernels
- 48-channel bottleneck
- depthwise d1/d2/d4 spike branches
- concatenate branch outputs instead of averaging
- binary spike-count channel selection
- spiking 1×1 branch fusion
- concatenate projected decoder skips before DW/PW spiking refinement
- 63,147 trainable parameters

Hypothesis: multiscale information existed in previous models but was destroyed by branch averaging and early additive skip fusion.

### T2 — `t02_dualpath_detail`

- compact 16/32/64 semantic path
- single dilation-2 semantic context
- persistent 16-channel high-resolution spiking detail branch
- concatenate semantic + shallow + detail features
- binary spike-count channel selection before final spiking fusion
- 24,211 trainable parameters

Hypothesis: tiny object/human regions and boundaries are lost by repeated downsampling; a narrow detail path should recover them more efficiently than widening the whole network.

### T3 — `t03_deep_attention_fpn`

- 24/48/96/128 encoder
- low-resolution depthwise dilation-2 context
- 32-channel, four-head spike-driven binary mask attention
- Q/K binary coincidence -> channel accumulation -> learned threshold comparison -> binary V mask
- no dense spatial softmax matrix
- concatenative FPN restoration from x4 to x1
- auxiliary semantic head retained
- 108,781 trainable parameters

Hypothesis: the four-stage top-five model already found rare-class semantics, but a better decoder and low-resolution long-range interaction are required to preserve them.

## Hardware-oriented design contract

- learned feature transmission remains spiking/binary between stages;
- prefer depthwise spatial convolution and 1×1 channel mixing;
- concatenation is wiring/routing, followed by a learned spiking fusion layer;
- attention must use binary gates/masks or low-resolution spike coincidence, not dense softmax attention;
- continuous learned beta/threshold/adaptation/attention-threshold values must later be quantized and validated against an integer reference;
- parameter count is secondary to mIoU up to roughly 100k parameters, but smaller wins when accuracy is equivalent.

## Fairness contract

- seed 17
- 8 epochs
- 2,048 training samples
- 512 held-out samples
- 64×64 resolution
- 15 internal timesteps
- batch 14
- LR 0.002
- same optimizer/loss/class weighting for all three
- no contender-specific tuning in the ranking run

Record mIoU, per-class IoU, predicted-pixel counts, pixel accuracy, parameter count, layer spike rates, and learned neuron/attention diagnostics.

## Commands

```powershell
docker compose run --rm lint
docker compose run --rm test
docker compose run --rm benchmark-top-three
```

Output:

```text
artifacts/ablation/top_three/summary.json
artifacts/ablation/top_three/checkpoints/
```

Do not replace `model.py` from this single run. The winner still needs a larger-budget confirmation, seeds 17/101/2026, timestep sensitivity, and quantized/integer-reference validation.
