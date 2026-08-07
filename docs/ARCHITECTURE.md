# Architecture

## Input and output

The Ev-SegNet sample is `[N,6,H,W]`; direct encoding presents it to the SNN as `[T,N,6,H,W]`. The semantic head emits `[T,N,6,H,W]` class spikes and sums them into `[N,6,H,W]` class activity.

## Source separation

```text
model_components.py
  Shared depthwise/pointwise and standard spiking blocks, multiscale context,
  additive decoder, HardwareLIF, ParametricLIF, f_inst, and f_long/T_thresh.

top_ten_models.py
  Frozen definitions of the completed ten-model benchmark.

top_five_models.py
  Active second-round PLIF/homeostasis/competition contenders.

model.py
  Canonical runtime architecture only; currently v10_fpga_hybrid.
```

## Common encoder-decoder

```text
6-channel spiking stem
→ high-resolution encoder
→ stride-2 encoder
→ stride-2 semantic encoder
→ none / dilated / multiscale context
→ nearest-neighbor upsample + projection
→ additive skip and refinement
→ nearest-neighbor upsample + high-resolution skip
→ six-class spiking 1×1 head
```

Convolutions are bias-free. Depthwise convolution performs spatial filtering per channel; pointwise convolution mixes channels. Decoder skips use addition rather than concatenation.

## Neurons

### HardwareLIF

```text
leaked membrane = membrane - membrane / 2^q
candidate = leaked membrane + synaptic current
spike = candidate >= effective threshold
reset = candidate - effective threshold for firing neurons
```

### PLIF

`ParametricLIF` learns one membrane-retention coefficient per feature channel. This tests whether different event features need different temporal integration. The continuous value is a training mechanism; hardware export must later quantize it and measure the accuracy change.

### f_inst

At each spatial location, channels above threshold compete and only the channel with the largest candidate membrane fires. It reduces duplicate activity and encourages specialization, but may be too restrictive for semantic segmentation, so it is enabled only in selected contenders.

### f_long and T_thresh

A feature map that fires receives an adaptive threshold increment. `T_thresh` keeps that adaptation active for a configured number of internal steps; decay begins when the timer expires. State is per feature map, not per pixel, to keep FPGA state small.

## Current canonical model

`model.py` contains the measured round-one winner `v10_fpga_hybrid`: depthwise/pointwise multiscale context, affine channel gain, two additive skips, residual paths, auxiliary training head, and adaptive LIF thresholds.

The canonical model is provisional until the top-five neuromorphic benchmark and multi-seed confirmation are complete.
