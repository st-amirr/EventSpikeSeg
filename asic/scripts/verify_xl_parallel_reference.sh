#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
docker run --rm --platform linux/amd64 \
  --workdir /workspace --env PYTHONPATH=/workspace/src \
  --volume "${PROJECT_DIR}:/workspace:ro" \
  "${ASIC_CPU_IMAGE:-eventspikeseg:torch2.2.2-cpu-verification}" \
  python scripts/verify_parallel_dag_reference.py \
    artifacts/ASIC_XL/model_spec.yaml --workers 4
