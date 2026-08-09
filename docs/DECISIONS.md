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

This rerun was temporarily separated from the failed first attempt for diagnosis. That versioned active-directory convention is now retired: the completed structural five lives in `artifacts/ablation/top_five/` and the active three lives in `artifacts/ablation/top_three/`.

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

This replaced the previous top-five definitions. `TOP_FIVE_PRESETS` is now the single completed structural registry; the active search moved to `TOP_THREE_PRESETS`.

## 2026-08-08 — Complete the structural top-five and move the search toward feature preservation

The fixed-dynamics structural benchmark completed with seed 17, 8 epochs, 2,048 training samples, 512 held-out samples, 64×64 output, 15 internal timesteps, batch 14, and learning rate 0.002.

Measured ranking:

- `f05_compact16_dilated`: mIoU 0.2596, 21,491 parameters
- `f02_wide32_multiscale`: mIoU 0.2284, 77,751 parameters
- `f04_deep4_dilated`: mIoU 0.2079, 107,131 parameters
- `f01_base24_multiscale`: mIoU 0.1626, 46,423 parameters
- `f03_early5x5_multiscale`: mIoU 0.1482, 49,111 parameters

Decision: do not promote any of these models. `v10_fpga_hybrid` remains the 0.3130 mIoU incumbent.

Findings used for the next round:

- compact `16/32/64` + a single dilated context gives the strongest overall accuracy/parameter tradeoff, so more parameters alone are not the answer;
- moderate width helped feature diversity and produced the best object IoU in the round (`0.0141`);
- the four-stage model produced the best aggregate rare-class signal, especially nature (`0.0712`) and vehicle (`0.1230`), so the deep encoder is extracting useful semantics that are being lost during decoding;
- early 5×5 processing is rejected;
- averaged multiscale branches are rejected for the next round because they erase branch identity and underperformed the simpler single-dilation path.

## 2026-08-08 — Create a separate top-three accuracy search

Create `top_three_models.py` instead of modifying the canonical model or the completed top-five registry. The three models isolate three accuracy hypotheses:

- `t01_spike_pyramid_concat`: preserve dilation-1/2/4 branch identity with channel concatenation, binary spike-count channel selection, and a spiking 1×1 fusion; use concatenative decoder skip fusion.
- `t02_dualpath_detail`: retain the compact semantic path but add a narrow persistent high-resolution spiking detail stream for small classes and boundaries.
- `t03_deep_attention_fpn`: retain four-stage semantic depth, add low-resolution spike-driven binary-mask attention, and use a concatenative FPN decoder to restore shallow spatial information.

The parameter targets are approximately 63k, 24k, and 109k respectively. Around 100k parameters is acceptable for an accuracy candidate, but fewer parameters win when validation accuracy is effectively equivalent.

## 2026-08-08 — Keep attention spike-oriented

Do not introduce conventional dense softmax self-attention into the active FPGA/neuromorphic search. The top-three may use:

- spike-count channel selection with a hard binary forward gate;
- low-resolution Q/K binary coincidence, channel accumulation, learned comparison threshold, and V masking;
- concatenation followed by spiking 1×1 mixing.

This is informed by SLTNet's evidence for multi-receptive-field event features, channel interaction, multi-level decoder restoration, and spike-driven masked attention, but the project tests smaller hardware-oriented modules rather than reproducing the full SLTNet network.


## 2026-08-09 — Complete the top-three search and select the dual-path mechanism

The accuracy-oriented top-three benchmark completed at seed 17 with 8 epochs, 2,048 training samples, 512 held-out samples, 64×64 output, and 15 internal timesteps. Results were `t02_dualpath_detail` mIoU 0.2728 / 24,211 parameters, `t01_spike_pyramid_concat` 0.1671 / 63,147, and `t03_deep_attention_fpn` 0.1555 / 108,781. T2 therefore provides the strongest new structural evidence: preserve a persistent high-resolution detail stream and fuse semantic + shallow + detail spikes late. T3's extra depth/attention is rejected for the canonical model because its predictions collapsed toward the two dominant classes.

## 2026-08-09 — Install a scaled spike-native dual-path canonical candidate

Replace the old `v10_fpga_hybrid` architecture in `model.py` with `final_dualpath_wide32`, while preserving `v10` in the frozen top-ten registry as the measured 0.3130 mIoU incumbent. The new candidate uses a 32/64/128 three-scale semantic encoder, extra residual depthwise/pointwise refinement per scale, a persistent 32-channel high-resolution detail path, two serial dilation-2 context blocks, a stronger decoder, and late semantic/shallow/detail concatenation. Do not add a fourth spatial scale, early 5×5 processing, averaged parallel multiscale context, dense softmax attention, or the failed T3 mask-attention path. The candidate is not yet an accuracy claim; it requires larger-budget and multi-seed validation.

## 2026-08-09 — Prefer comparator-only spike-count selection and independent class spikes

For the canonical circuit-oriented path, replace the top-three count-domain MLP channel selector with one learned activity threshold per fused channel. Inference is spike counting, comparison, and binary AND gating only. Also disable hard per-timestep semantic class WTA in the canonical head: six independent spiking class populations accumulate evidence and final segmentation uses temporal spike-count argmax. This remains fully spiking while avoiding early suppression of rare class evidence. Historical benchmark definitions remain unchanged.

## 2026-08-09 — Use SpikingJelly as the PLIF/convolution infrastructure layer

Keep PyTorch as the tensor/autograd/optimizer substrate, but use SpikingJelly public `activation_based` components where they match the hardware contract. `SpikingStage` uses the SpikingJelly `Conv2d` wrapper when available, and `ParametricLIF` delegates its charge equation to SpikingJelly `ParametricLIFNode`. Preserve the already-benchmarked per-channel beta by feeding a per-channel reciprocal-tau tensor into the SpikingJelly PLIF charge equation. Custom dynamic threshold, `peer_membrane` fInst, triangular fLong/TThresh, reset ordering, and hardware-visible state remain explicit project code. A mathematically equivalent fallback remains for lightweight tests without SpikingJelly.

## 2026-08-09 — Add late decoder/detail refinement training

The canonical model trains all layers jointly through 70% of epochs. From 70% to 90%, freeze only the semantic backbone (stem, encoder, and semantic context) while keeping the high-resolution detail path, decoder/fusion, auxiliary head, and class head trainable; auxiliary CE/focal coefficients rise from 0.15 to 0.30 during this phase. At 90%, unfreeze all layers and apply an additional 0.25 learning-rate multiplier on top of the existing cosine decay for final joint tuning. Completed benchmark models have no refinement schedule and retain their original training behavior. The main segmentation CE coefficient is 1.0.


## 2026-08-09 — Replace comparator-only final selector with PLIF cross-channel selector

The comparator-only selector was more circuit-minimal but discarded T2's learned cross-channel relationships. The canonical `final_dualpath_wide32` therefore uses a spike-driven 96→96 1×1 synaptic projection followed by PLIF selector neurons. Selector spikes are reduced to binary per-channel enables and gate the fused semantic/shallow/detail spikes. This preserves cross-channel learned selection while keeping inference spike-native: active input spikes cause stored 1×1 weights to be accumulated into PLIF membranes, followed by threshold/fire gating. No dense count-domain MLP or softmax is used. Historical T2 remains unchanged for reproducibility. The canonical model is now approximately 141k trainable parameters.
