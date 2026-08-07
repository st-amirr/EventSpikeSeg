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

## 2026-08-07 — Resolved design flaw: binary feature-map homeostasis

**Former behavior:** `amax` reduced a complete feature map to 0/1, so one spike and dense firing caused the same threshold increment. A fixed integer timer repeatedly held the threshold high.

**Correction:** revised contenders use mean spike rate and learnable continuous adaptation tau, strength, and target rate. Silent channels can lower their threshold; overactive channels raise it.

## 2026-08-07 — Resolved design flaw: global hard f_inst

**Former behavior:** one winning channel per pixel was enforced through all hidden stages, causing feature loss and complete collapse in the lightweight contender.

**Correction:** revised competition is grouped top-2 and scoped to encoder or stem only. Competition is disabled during the first 30% of training.

## 2026-08-07 — Open: revised real-data outcome

The revised mechanisms pass unit and synthetic training tests but have not yet demonstrated improved DDD17 mIoU. Promotion remains blocked until the real benchmark and multi-seed confirmation finish.
