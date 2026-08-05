# EventSpikeSeg-FPGA Agent Instructions

## Mission

Build and validate a lightweight SNN for semantic segmentation using the Ev-SegNet semantic extension of DDD17, then map the winning architecture to a sparse fixed-point FPGA design.

## Current input contract

The downloaded Ev-SegNet dataset stores one six-channel event-statistic image per sample:

```text
[N, 6, H, W]
```

The six channels represent polarity histograms, normalized timestamp means, and normalized timestamp standard deviations. For direct SNN training, repeat this fixed current over the configured internal timestep count:

```text
[T, N, 6, H, W]
```

Do not claim that these are raw chronological event bins. Raw asynchronous DDD17 replay is a later milestone requiring the original recordings and label alignment.

## Output contract

```text
[T, N, 6, H, W] class spikes
[N, 6, H, W] accumulated class logits
```

Classes are:

```text
flat, construction+sky, object, nature, human, vehicle
```

Ignore label is `255`.

## Architecture search

Maintain exactly ten temporary presets until a winner is demonstrated. Every benchmark run must freeze seed, records, shuffle order, resolution, class weights, optimizer, loss, and timestep count.

Choose by validation mIoU. Within 0.5 percentage points, prefer fewer parameters, then lower output spike rate.

Do not delete the preset registry after a smoke run. Finalize only after a high-resolution check and at least three winner seeds.

## Hardware constraints

Prefer:

- depthwise + pointwise convolution
- additive skips
- nearest-neighbor upsampling followed by convolution
- foldable affine gains
- residual membrane paths
- integer-friendly LIF leak and adaptive thresholds

Treat BatchNorm, GAP/sigmoid gating, and parallel multiscale branches as measured ablations, not assumed FPGA choices.

Avoid transformer attention, transposed convolution, concatenation-heavy decoders, and operations without a clear fixed-point mapping unless an accuracy gain justifies them.

## Required records

Keep these synchronized:

```text
docs/ARCHITECTURE.md
docs/DECISIONS.md
docs/PROGRESS.md
docs/RESULTS.md
docs/BUGS.md
docs/exec-plans/active/ddd17-semantic-ablation.md
```

Never record unmeasured accuracy, power, latency, FPGA utilization, or throughput.
