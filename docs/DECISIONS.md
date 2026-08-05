# Decisions

## 2026-08-05 — Reset from MEVDT tracking to DDD17 segmentation

The active task is semantic segmentation. Tracking, attention-centroid decoding, box calibration, and MEVDT-specific metrics were retired from the active package.

## 2026-08-05 — Use the Ev-SegNet DDD17 format exactly

The selected download contains six event-statistic channels, not raw event timestamps. The loader therefore preserves six channels and direct-encodes them over internal SNN timesteps. It does not reshape them into three artificial two-polarity timesteps.

## 2026-08-05 — Search ten controlled architecture variants

The search measures the benefits and costs of standard convolution, depthwise/pointwise convolution, dilation, multiscale context, channel affine gain, BatchNorm, GAP channel gating, auxiliary supervision, skip count, residuals, and adaptive thresholds.

## 2026-08-05 — Delay destructive finalization

Losing variants will be deleted only after the winner is reproduced at higher resolution and across at least three seeds.

## 2026-08-06 — Embed the local DDD17 path and fixed layout

The host root is embedded as `C:/Users/stamir/Desktop/Dataset/DDD17`. Loading only
reads `events/{train,test}/*.npy` and `labels/{train,test}/*.png` paired by stem.
`test` is the held-out set. Manifests, archives, split-first layouts, and train
carve-outs were removed.
