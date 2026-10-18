# ASIC hardware sources

This folder contains hardware **source code and build recipes**. The finished analog layout, module consumption reports and circuit evidence are in [`artifacts/analog_asic`](../artifacts/analog_asic/index.html). The active implementation is the original-float EventSpikeSeg140k mapped to GF180 analog/mixed-signal circuitry.

## What remains here

- `analog/`: GF180 categorical event/address/control RTL, retained control revisions and their dependencies, and the `modules.spice` behavioral reference used by `scripts/build_analog_modules.py`. This folder does not contain every native analog cell; their delivered GDS/SPICE and source snapshots are under `artifacts/analog_asic/components/`.
- `analog/orfs/`: retained GF180 synthesis/layout configurations. The final control roots are `gf180_full25_packet_fabric_v1/config_power_v5.mk`, `gf180_full25_actor_ingress_v2/config.mk`, and `gf180_full25_accumulation_dispatch_v1/config.mk`. Earlier artifact paths inside recipes are provenance and may require resolution/restoration before replay.
- `rtl/`: reusable and historical digital SystemVerilog blocks, retained because existing exporters, source lists and tests still use them. These do not replace the active analog membrane design.
- `scripts/`, `tools/`, and top-level ORFS configuration files: digital reference build/analysis utilities and their dependencies. Digital 140k/XL campaigns remain paused; their documentation packages are `artifacts/ASIC/final/` and `artifacts/ASIC_XL/final/`.

## Cleanup and recovery — 2026-10-15

Archived 38 files (171,273 bytes) from 223 originals: superseded GF180 control revisions/build attempts, early SKY130 experiments, a provisional OTA source and Windows folder metadata. Kept 185 original files, including this README, which was updated after its original was backed up. No permanent deletion, staging, commit or simulation was performed.

Review: [`archive inventory`](../bin/asic_source_cleanup_20261015T115233Z/index.html). The bin contains a SHA256 manifest, integrity audit, `restore_sources.ps1`, and `before_changes.zip` with the original README, seven project docs and artifact locator. Restoring source files refuses to overwrite differing existing files. Original paths also resolve through `scripts/resolve_asic_artifact_path.py`.

Use [`docs/ACTIVE_TASKS.md`](../docs/ACTIVE_TASKS.md) and [`docs/project_spec.yaml`](../docs/project_spec.yaml) for current scope. This cleanup reduces clutter; the original source tree was only about 0.84 MiB.
