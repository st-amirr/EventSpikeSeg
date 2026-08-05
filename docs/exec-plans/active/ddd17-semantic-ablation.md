# DDD17 semantic architecture ablation

## Objective

Compare ten lightweight SNN segmentation combinations on the Ev-SegNet DDD17 release using one controlled seed and protocol.

## Acceptance criteria

- dataset inspection recognizes six-channel event images
- all tests and lint pass in Docker
- all ten variants complete identical training/validation budgets
- `artifacts/ablation/summary.json` records every result
- top candidates are re-run at higher resolution
- final winner is reproduced with seeds 17, 101, and 2026
- only then are losing presets and checkpoints removed

## Commands

```bash
docker compose build
docker compose run --rm inspect-ddd17
docker compose run --rm test
docker compose run --rm lint
docker compose run --rm benchmark-ddd17
```

## Current state

Implementation and synthetic tests are complete. Real dataset execution remains to be run on the user's machine.
