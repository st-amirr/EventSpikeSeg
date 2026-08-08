# Decisions

## 2026-08-05 — Reset from MEVDT tracking to DDD17 segmentation

Tracking, box decoding, alpha-beta tracking, global classification, and MEVDT metrics are inactive. The task is six-class semantic segmentation using the Ev-SegNet DDD17 representation.

## 2026-08-05 — Preserve the six event-statistic channels

The six channels are polarity histogram, timestamp mean, and timestamp standard deviation pairs. They are repeated as direct current over internal SNN steps and are not reinterpreted as chronological bins.

## 2026-08-06 — Preserve the completed ten-model experiment separately

Round one completed with `v10_fpga_hybrid` highest at mIoU 0.3130. The complete preset registry is moved to `top_ten_models.py`; it remains reproducible but is no longer part of the canonical production module.

## 2026-08-06 — Keep model.py canonical-only

`model.py` contains one architecture interface. It currently installs the measured round-one incumbent. Experimental architectures belong in explicit experiment files and may not be added back to `model.py`.

## 2026-08-06 — Run a spike-native top-five round

The second round tests combinations derived from v10, v03, v02, and v08 using PLIF, feature-map `f_long`, explicit `T_thresh`, and selected hidden-layer `f_inst`. Ordinary BN and GAP gating are not included because this round targets mechanisms that remain meaningful during neuromorphic inference.

## 2026-08-06 — Do not enable f_inst in every contender

Cross-channel winner-take-all may improve sparsity but can remove simultaneous semantic features. It is therefore isolated to two of five contenders rather than treated as automatically beneficial.

## 2026-08-06 — Treat PLIF as trainable, not yet hardware-exact

PLIF learns continuous per-channel retention. The eventual FPGA model must quantize it to an integer-friendly leak, then run accuracy and bit-exact regression tests before PLIF can be claimed as deployed.

## 2026-08-06 — Round-one zero-IoU classes are an open data/training issue

Object and human class performance cannot be solved by architecture ranking alone. Before final selection, record class pixel counts, image-presence counts, prediction counts, and confusion matrices at the benchmark resolution.

## 2026-08-07 — Reject the first PLIF/homeostasis top five as final models

The first round-two winner reached only mIoU 0.2464 versus the incumbent 0.3130, and the lightweight `f04` emitted zero output spikes. Preserve the definitions/checkpoints for diagnosis but do not promote them.

## 2026-08-07 — Replace fixed T_thresh with learnable continuous adaptation persistence

A discrete integer hold timer cannot receive useful gradients through standard backpropagation. Revised rate homeostasis learns a bounded continuous `tau`, with retention `exp(-1/tau)`, plus per-channel adaptation strength and target firing rate. Quantize these only after architecture selection.

## 2026-08-07 — Make homeostasis bidirectional and rate-based

Use spatial mean spike rate instead of feature-map `amax`. Threshold adaptation may become negative for silent channels and positive for overactive channels, bounded around the learnable base threshold.

## 2026-08-07 — Remove hard class-head WTA from revised contenders

Independent output class neurons accumulate spikes and compete only through final temporal argmax. This preserves a fully spiking learned output while allowing gradients to reach rare classes.

## 2026-08-07 — Restrict f_inst rather than apply it globally

Only grouped top-2 competition is allowed, and only in the encoder or stem of selected contenders. Global one-winner competition caused severe information loss and dead-layer behavior.

## 2026-08-07 — Separate revised results from failed top-five results

Write the rerun to `artifacts/ablation/top_five_v2/`. Keep `artifacts/ablation/top_five/` unchanged for reproducibility.

## 2026-08-07 — Use the completed mechanism screen to freeze neuron dynamics for structural search

The completed five-model screen used seed 17, 5 epochs, 256 training samples, 128 held-out samples, 64×64 output, and 8 internal timesteps. `f05_v02_light_peer_membrane_inhibition` ranked first at mIoU 0.1991. `f02` threshold adaptation alone ranked second at 0.1459, while hidden `winner_peer` inhibition ranked last at 0.1233 and drove `enc3` spike rate to approximately 0.00015.

Decision: the next top-five holds neuron dynamics constant as PLIF + learnable threshold + stem-only `peer_membrane` inhibition + encoder triangular threshold adaptation. Keep affine scaling, residual paths, auxiliary supervision, and semantic output class WTA. Do not use hidden `winner_peer` gating in the active five.

Reason: this separates the next question—network width, receptive field, depth, and context—from the already-screened inhibition question. The low-budget run is sufficient for mechanism selection but not for promotion accuracy claims.

## 2026-08-07 — Make width, early kernel size, and encoder depth explicit architecture variables

Add explicit channel schedules, configurable stem/first-block kernel sizes, and optional fourth encoder scale to the shared segmentation backbone. Preserve the original three-scale module layout for the canonical/top-ten models.

The active five are:

- `f01_base24_multiscale`: 24/48/96, 3×3, multiscale context
- `f02_wide32_multiscale`: 32/64/128, 3×3, multiscale context
- `f03_early5x5_multiscale`: 24/48/96, 5×5 stem and first depthwise block
- `f04_deep4_dilated`: 24/48/96/128, four encoder scales, single dilated context
- `f05_compact16_dilated`: 16/32/64, single dilated context

This replaces the previous active top-five definitions; there is only one active `TOP_FIVE_PRESETS` registry.
