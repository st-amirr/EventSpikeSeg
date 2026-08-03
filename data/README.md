# Local dataset mounts

Datasets and generated samples are ignored by Git. Use real directory symlinks here,
not macOS Finder alias files.

Expected MEVDT layout:

```text
data/mevdt -> /absolute/path/to/MEVDT
data/mevdt/sequences/{train,test}/...
data/mevdt/labels/{detection_labels,tracking_labels}/...
data/mevdt/data_splits/MEVDT_org_rate_{train,test}.csv
```

Override the default location with `make train-mevdt-smoke MEVDT_ROOT=/path/to/MEVDT`.
The loader uses the official split CSV and reads raw sequence-level event CSV streams;
it does not use APS images for model input.
