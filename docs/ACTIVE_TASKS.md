# Active tasks

Updated2026-10-14. Article layout, representative consumption and PNG/SVG views are delivered.

## Current deliverables

- Analog article package: `artifacts/analog_asic/final/index.html`.
- Final hierarchical GDS: `artifacts/analog_asic/final/layout/EventSpikeSeg140k_GF180_Analog.gds` (537,103,416bytes; SHA256fb28eeb6bbc8901ad8594dcd4b5cc14450b7cae438bd5f239096c587f96d1d92).
- Figures: `artifacts/analog_asic/final/images/`, including the three true-vectorSVGs and PNGs.
- Consumption: `artifacts/analog_asic/final/consumption/summary.json`,22 required families/74 rows. Per-instance transients, reused rail traces, RMS DC samples and digital-library estimates are explicitly distinguished.
- Digital140k andXL documentation: `artifacts/ASIC/final/index.html` and `artifacts/ASIC_XL/final/index.html`. No digital full-chip completion claimed.

## Scope and limitations

Original epoch58 full-float analog topology and54,630,400 state identities including30,976,000 membranes remain preserved. External analog/control interfaces are documented. The full1024-state page lacks complete connected power/transient evidence; partition and leaf consumption are supplied. No compact die, calibrated accuracy, full-chip power, globalRC/IR/EM, manufacture or full-population5ms acceptance is claimed. Further circuit optimization is optional.

## Cleanup completed; user bin review pending

Review bin: `bin/asic_cleanup_2026-10-14_20261014T145109Z/`. All64,814 original files accounted for; retained originals are SHA256-verified. No deletions performed. Original evidence bytes/hashes are preserved; `artifacts/asic_artifact_index.json` maps old paths to retained or binned files. restore_artifacts.ps1 and the move inventory are in the bin. Do not delete the bin without explicit user instruction. Archive the seven docs before future edits. No new simulations or Docker images were started during cleanup.
