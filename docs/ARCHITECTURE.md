# Architecture

The temporary model family accepts direct-encoded Ev-SegNet samples:

```text
[T,N,6,H,W]
```

The six input channels are histogram/mean/std features for two polarities. They are fixed over the internal SNN timestep axis.

All variants share:

```text
stem -> encoder stage 1 -> downsample stage 2 -> downsample stage 3
     -> optional context -> shallow decoder -> six-channel spiking class head
```

The ten variants isolate standard vs depthwise convolution, dilation, multiscale branches, foldable affine gain, BatchNorm, GAP gating, auxiliary supervision, skip count, residual paths, and adaptive thresholds.

The final architecture has not been selected. See `docs/RESULTS.md` after benchmark execution.
