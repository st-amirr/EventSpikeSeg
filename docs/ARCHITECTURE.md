# Architecture

## Active task

Six-class semantic segmentation of the Ev-SegNet DDD17 six-channel event-statistic representation. Input is `[T,N,6,H,W]`; direct encoding repeats one six-channel sample over `T` internal SNN updates.

## File separation

- `model.py`: canonical post-ablation high-accuracy candidate (`final_dualpath_wide32`)
- `model_components.py`: shared convolution, encoder/decoder, PLIF, inhibition, and threshold-adaptation primitives
- `top_ten_models.py`: frozen completed ten-model structural benchmark
- `top_five_models.py`: completed five-model structural search
- `top_three_models.py`: frozen completed accuracy-oriented three-model search
- `train.py`: the single training/benchmark engine for historical suites and the final model

## Shared neuron dynamics carried into the structural and accuracy rounds

The completed top-five held these dynamics fixed, and the top-three keeps the same spike-neuron basis while changing feature fusion/attention structure:

```text
PLIF with learnable per-channel beta
+ learnable per-channel base threshold
+ stem-only peer-membrane inhibition
+ encoder/context triangular threshold adaptation
+ affine channel scaling
+ residual paths
+ auxiliary semantic supervision
+ historical structural/top-three output class winner-take-all
```

`peer_membrane` inhibition preserves simultaneous suprathreshold feature spikes but subtracts a learned retinotopic membrane-energy-scaled amount from peer membrane states. Hidden one-winner gating is not used in the current search because the completed mechanism run showed severe deep-layer sparsification with `winner_peer`.

Triangular threshold adaptation is local in `(x,y)`: activity starts a threshold process that rises for `adaptation_duration`, falls for another `adaptation_duration`, then returns to zero. The adaptation strength and duration remain learnable continuous training parameters and require later fixed-point/shift-compatible conversion.

## Structural configuration support

`SegmentationArchitecture` now supports:

- explicit `channel_schedule` with three or four encoder scales;
- configurable `stem_kernel_size`;
- configurable `first_block_kernel_size`;
- existing depthwise/pointwise blocks;
- `none`, single-dilated, or parallel multiscale context.

Three-scale models retain the original state/module layout. Four-scale models add `down4`, `enc4`, `project4`, and `refine3`, with a deep skip into the decoder. Validation diagnostics include `enc4_spikes` when present.

## Completed structural top five

| model | channels | early kernels | encoder scales | context | purpose |
| --- | --- | --- | ---: | --- | --- |
| `f01_base24_multiscale` | 24/48/96 | 3×3 | 3 | multiscale 1/2/4 | controlled baseline |
| `f02_wide32_multiscale` | 32/64/128 | 3×3 | 3 | multiscale 1/2/4 | capacity test |
| `f03_early5x5_multiscale` | 24/48/96 | 5×5 stem + first block | 3 | multiscale 1/2/4 | larger early event receptive field |
| `f04_deep4_dilated` | 24/48/96/128 | 3×3 | 4 | dilation 2 | depth/context test |
| `f05_compact16_dilated` | 16/32/64 | 3×3 | 3 | dilation 2 | FPGA-efficiency test |

All later spatial depthwise/standard kernels remain 3×3; pointwise projections and semantic heads remain 1×1.

## Semantic readout

The learned output remains fully spiking. Historical benchmark models retain their recorded class-head behavior. The canonical `final_dualpath_wide32` uses six independent spiking class populations with no hard per-timestep class WTA; final class selection is temporal spike-count argmax. There is no analog softmax inference head.

## Hardware interpretation

The completed top-five and current top-three runs use floating-point training. Before FPGA promotion, learned beta, thresholds, inhibition strength, threshold-adaptation strength, and adaptation duration must be quantized and checked against an integer reference. Larger kernels, wider channels, and a fourth encoder level must also be compared by estimated/synthesized memory and event-addition cost rather than mIoU alone.


## Completed accuracy-oriented top three

The completed structural round established three useful facts: the compact three-stage/single-dilation path was the strongest overall, the wide path helped `object`, and the four-stage path recovered the best aggregate rare-class signal. That round therefore tested feature preservation and fusion rather than simply adding parameters.

### `t01_spike_pyramid_concat` — 63,147 parameters

- encoder: `24 → 48 → 96`, all 3×3 spatial processing;
- context bottleneck: `96 → 48`;
- three depthwise spike branches at dilation `1/2/4`;
- branch outputs are concatenated, not averaged;
- binary spike-count channel attention selects concatenated channels;
- a spiking 1×1 stage fuses the selected channels back to the semantic width;
- decoder merges projected semantic and shallow skip spikes by concatenation before depthwise/pointwise spiking refinement.

The hypothesis is that the earlier multiscale implementation destroyed branch-specific sparse evidence by averaging and that additive skip fusion mixed spatial and semantic features too early.

### `t02_dualpath_detail` — 24,211 parameters

- semantic encoder: compact `16 → 32 → 64`;
- semantic context: single depthwise dilation-2 path;
- parallel 16-channel high-resolution spiking detail path remains near the input resolution;
- final fusion concatenates semantic, shallow encoder, and detail spikes;
- binary spike-count channel selection precedes the final spiking fusion.

The hypothesis is that `object`, `human`, and thin vehicle boundaries are disappearing during downsampling. A narrow detail stream is cheaper than widening the entire encoder.

### `t03_deep_attention_fpn` — 108,781 parameters

- encoder: `24 → 48 → 96 → 128`;
- low-resolution dilation-2 semantic context;
- a 32-channel, four-head spike-driven binary-mask attention block at the deepest low-resolution stage;
- Q/K spike coincidence is accumulated within each head and compared against a learned threshold; the resulting hard binary mask gates V spikes;
- no dense spatial `N×N` softmax attention matrix is formed;
- decoder is a concatenative FPN that progressively restores `x4 → x3 → x2 → x1` information;
- auxiliary semantic supervision is retained.

This tests whether the rare-class semantics seen in the four-stage top-five model can be retained when the decoder explicitly restores high-resolution features. The attention block is kept only at low spatial resolution to control memory and event-addition cost.

## Spike-oriented fusion and attention rule

Concatenation is treated as wiring/channel routing and does not itself require multiply-accumulate operations. Learned fusion occurs afterward through spiking 1×1 projections. Channel attention uses spike counts and a hard binary gate in the forward path. Deep attention uses binary Q/K coincidence, accumulation, comparison, and V masking rather than conventional floating-point softmax attention. These operations remain compatible with an eventual counter/comparator/accumulator FPGA mapping, subject to later quantization and bit-accurate validation.


## Canonical `final_dualpath_wide32`

The current EventSpikeSeg architecture is the 237,597-parameter high-capacity spike-native revision assembled after the completed top-ten/top-five/top-three searches. It scales capacity without adding a fourth downsampling stage.

```text
input 6
  → stem 32
  → encoder 32 + residual DW/PW refinement
  → stride-2 main path + 1×1 PLIF projected residual → encoder 64
  → stride-2 main path + 1×1 PLIF projected residual → encoder 128
  → serial residual dilation-2 context ×2
  → residual parallel DW d1/d2/d4 context → concat → PLIF 1×1 fusion
  → one bottlenecked 32-channel / 4-head spike-mask attention residual
  → deep auxiliary semantic head (training only)
  → project/upsample + CONCAT encoder64 → DW/PW PLIF fusion/refinement 64
  → mid auxiliary semantic head (training only)
  → project/upsample to 32
  → CONCAT semantic32 + shallow32 + persistent detail32
  → 96→96 spike-driven 1×1 projection + PLIF selector gate
  → DW/PW 96→32 + residual refinement
  → six independent spiking class populations
  → temporal spike-count argmax
```

The high-resolution detail stream is persistent from the shallow 32-channel feature and contains DW/PW residual refinement plus a spike-native asymmetric `3×1 → 1×3 → 1×1` residual block. The parallel multiscale context is not the failed historical branch *average*: branch identities are concatenated and mixed by a learned spiking 1×1 stage, while the simpler serial dilation-2 path remains intact.

The low-resolution attention block is also not the failed T3 architecture as a whole. Only one bottlenecked residual block is used at the deepest 128-channel scale. Q/K are binary PLIF spike streams; coincidence is accumulated per head and compared with a learned threshold; the resulting binary mask gates V spikes. There is no dense spatial softmax or analog NxN attention matrix.

### Neuron/runtime contract

- PLIF with learnable per-channel beta and base threshold;
- stem-only `peer_membrane` fInst;
- downsampled encoder/context triangular fLong/TThresh;
- no hard hidden `winner_peer` gating;
- independent output class spiking populations;
- temporal spike-count class decision;
- affine channel scaling rather than BatchNorm;
- PyTorch for tensors/autograd/optimizer;
- SpikingJelly convolution/PLIF/surrogate infrastructure where compatible;
- project-specific fInst/fLong/reset ordering remains explicit for hardware translation.

Auxiliary heads are optimization-only: they are computed while `model.training` is true and skipped in evaluation/inference. This does not change deployed logits and avoids unnecessary inference state.

### Canonical training refinement

Only the final model exposes the late refinement schedule: joint training through 70% of epochs; freeze stem/semantic encoder/context during 70–90% while detail path, decoder/fusion, selector, auxiliary heads, and class head continue; then unfreeze all layers for the final 10% with an additional `0.25×` LR multiplier on top of cosine decay.

The final loss profile uses CE coefficient `1.0`, focal `0.5`, Dice `0.75`, the existing activity regularizer, mid auxiliary CE/focal `0.15/0.15` normally and `0.30/0.30` during frozen-backbone refinement, and deep auxiliary CE/focal `0.10/0.10` normally and `0.20/0.20` during refinement. Historical suites are pinned separately to their recorded CE coefficient `0.5`.

### Training/evaluation data protocol

For the final suite, best-checkpoint selection uses a deterministic holdout from the DDD17 training split (`--validation-fraction`) rather than the official test split. The official test split remains for final reporting. Omitting `--height/--width` preserves the stored dataset resolution. Historical architecture-search suites continue to use their recorded official-test benchmark protocol for reproducibility.

## Historical architecture registries

`top_ten_models.py`, `top_five_models.py`, and `top_three_models.py` preserve the measured ablation definitions and checkpoint-facing behavior. All three are dispatched through `train.py`; there is no separate top-three training implementation. Historical results remain in `RESULTS.md` and the design interpretation in `DECISIONS.md`.


## fLong scope and native-resolution memory

The canonical model uses triangular fLong only on semantic encoder/context stages (`f_long_scope=encoder_context`). The full-resolution stem and custom detail branch remain PLIF with learnable thresholds but do not allocate per-pixel triangular fLong age/amplitude state. Historical benchmark presets retain the older `encoder` scope semantics for reproducibility. During training the canonical forward returns scalar activity rates for regularization instead of retaining full hidden TNCHW spike sequences.
