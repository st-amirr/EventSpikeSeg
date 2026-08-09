# Architecture

## Active task

Six-class semantic segmentation of the Ev-SegNet DDD17 six-channel event-statistic representation. Input is `[T,N,6,H,W]`; direct encoding repeats one six-channel sample over `T` internal SNN updates.

## File separation

- `model.py`: canonical production model only (`v10_fpga_hybrid` until promotion)
- `model_components.py`: shared convolution, encoder/decoder, PLIF, inhibition, and threshold-adaptation primitives
- `top_ten_models.py`: frozen completed ten-model structural benchmark
- `top_five_models.py`: completed five-model structural search
- `top_three_models.py`: current accuracy-oriented three-model search

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
+ output class winner-take-all
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

The learned output remains fully spiking. Six class LIF populations accumulate spike counts over time; local class WTA is applied in the semantic head and final class selection is temporal spike-count argmax. There is no analog softmax inference head.

## Hardware interpretation

The completed top-five and current top-three runs use floating-point training. Before FPGA promotion, learned beta, thresholds, inhibition strength, threshold-adaptation strength, and adaptation duration must be quantized and checked against an integer reference. Larger kernels, wider channels, and a fourth encoder level must also be compared by estimated/synthesized memory and event-addition cost rather than mIoU alone.


## Current accuracy-oriented top three

The completed structural round established three useful facts: the compact three-stage/single-dilation path was the strongest overall, the wide path helped `object`, and the four-stage path recovered the best aggregate rare-class signal. The next round therefore tests feature preservation and fusion rather than simply adding parameters.

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
