# Architecture

## Active task

Six-class semantic segmentation of the Ev-SegNet DDD17 six-channel event-statistic representation. Input is `[T,N,6,H,W]`; direct encoding repeats one six-channel sample over `T` internal SNN updates.

## File separation

- `model.py`: canonical production model only (`v10_fpga_hybrid` until promotion)
- `model_components.py`: shared convolution, encoder/decoder, PLIF, inhibition, and threshold-adaptation primitives
- `top_ten_models.py`: frozen completed ten-model structural benchmark
- `top_five_models.py`: current five-model structural search only

## Shared neuron dynamics selected for the new top five

All current contenders use the same mechanism combination so width/kernel/depth comparisons are controlled:

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

`peer_membrane` inhibition preserves simultaneous suprathreshold feature spikes but subtracts a learned retinotopic membrane-energy-scaled amount from peer membrane states. Hidden one-winner gating is not used in the current five because the completed mechanism run showed severe deep-layer sparsification with `winner_peer`.

Triangular threshold adaptation is local in `(x,y)`: activity starts a threshold process that rises for `adaptation_duration`, falls for another `adaptation_duration`, then returns to zero. The adaptation strength and duration remain learnable continuous training parameters and require later fixed-point/shift-compatible conversion.

## Structural configuration support

`SegmentationArchitecture` now supports:

- explicit `channel_schedule` with three or four encoder scales;
- configurable `stem_kernel_size`;
- configurable `first_block_kernel_size`;
- existing depthwise/pointwise blocks;
- `none`, single-dilated, or parallel multiscale context.

Three-scale models retain the original state/module layout. Four-scale models add `down4`, `enc4`, `project4`, and `refine3`, with a deep skip into the decoder. Validation diagnostics include `enc4_spikes` when present.

## Current structural contenders

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

The current top-five run is still floating-point training. Before FPGA promotion, learned beta, thresholds, inhibition strength, threshold-adaptation strength, and adaptation duration must be quantized and checked against an integer reference. Larger kernels, wider channels, and a fourth encoder level must also be compared by estimated/synthesized memory and event-addition cost rather than mIoU alone.
