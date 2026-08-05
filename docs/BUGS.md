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
