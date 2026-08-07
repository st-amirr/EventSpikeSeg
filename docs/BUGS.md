# Bugs and limitations

## Dataset representation limitation

The Ev-SegNet semantic download contains six aggregate event-statistic channels rather
than raw asynchronous events. This limits direct claims about temporal sparsity and
event-addressed FPGA execution. Raw-event validation requires original DDD17 recordings
aligned to the published semantic labels.

## Resolved: loader uses the known Desktop layout only

The loader no longer searches parent mounts or walks the tree. It reads only:

```text
events/{train,test}/*.npy
labels/{train,test}/*.png
```

from the embedded root `C:/Users/stamir/Desktop/Dataset/DDD17`, pairs files by stem, and
uses `test` as the held-out set. Preview folders such as `events_images` and
`labels/test_colored` are ignored.

## 2026-08-06 — Rare classes collapse to zero IoU

**Status:** open diagnostic issue.

**Evidence:** object IoU is zero for the round-one winner and nearly all variants; human IoU is zero for all ten variants.

**Possible causes:** severe class imbalance, too few class-containing samples in the fixed subset, loss weighting limits, disappearance of small regions at 64×64, or class-prediction collapse.

**Required diagnostic:** record ground-truth pixels per class, samples containing each class, post-resize class counts, predicted pixels per class, and the full confusion matrix before final architecture promotion.
