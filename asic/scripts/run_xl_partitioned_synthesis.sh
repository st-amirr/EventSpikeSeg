#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ARTIFACTS_DIR="${EVENTSPIKESEG_ARTIFACTS_DIR:-${PROJECT_DIR}/artifacts}"
cd "${PROJECT_DIR}"
[[ -d "${ARTIFACTS_DIR}" ]] || { printf "Artifact store not found: %s\n" "${ARTIFACTS_DIR}" >&2; exit 2; }
docker run --rm --platform linux/amd64 \
  --memory "${XL_SYNTH_CONTAINER_MEMORY:-26g}" --memory-swap "${XL_SYNTH_CONTAINER_MEMORY:-26g}" \
  --cpus "${XL_SYNTH_CPUS:-4}" --ulimit core=0 \
  --workdir /project --env PYTHONPATH=/project/src \
  --env XL_CHECKPOINT="${XL_CHECKPOINT:-artifacts/model_checkpoints/dsec_XL/EventSpikeSegXL_seed17_epoch001.pt}" \
  --env XL_ASIC_EXPORT="${XL_ASIC_EXPORT:-artifacts/ASIC_XL}" \
  --env XL_SYNTH_TILE_WIDTH="${XL_SYNTH_TILE_WIDTH:-1}" \
  --env XL_SYNTH_TILE_HEIGHT="${XL_SYNTH_TILE_HEIGHT:-1}" \
  --env XL_SYNTH_RESUME="${XL_SYNTH_RESUME:-1}" \
  --env XL_SYNTH_WORKERS="${XL_SYNTH_WORKERS:-3}" \
  --env XL_SYNTH_WORKER_MEMORY_GIB="${XL_SYNTH_WORKER_MEMORY_GIB:-8}" \
  --env XL_SYNTH_RETRY_MEMORY_GIB="${XL_SYNTH_RETRY_MEMORY_GIB:-16}" \
  --volume "${PROJECT_DIR}:/project:ro" --volume "${ARTIFACTS_DIR}:/workspace/artifacts" \
  "${ASIC_CPU_IMAGE:-eventspikeseg:torch2.2.2-cpu-verification-guarded}" bash -lc '
set -euo pipefail
case "${XL_CHECKPOINT}" in artifacts/*) XL_CHECKPOINT="/workspace/artifacts/${XL_CHECKPOINT#artifacts/}" ;; esac
case "${XL_ASIC_EXPORT}" in artifacts/*) XL_ASIC_EXPORT="/workspace/artifacts/${XL_ASIC_EXPORT#artifacts/}" ;; esac
export XL_CHECKPOINT XL_ASIC_EXPORT
bash asic/scripts/prepare_xl_asic.sh
resume_args=()
if [[ "${XL_SYNTH_RESUME}" != "1" ]]; then resume_args+=(--no-resume); fi
exec python -u scripts/synthesize_asic_partitions.py "${XL_ASIC_EXPORT}" \
  --tile-width "${XL_SYNTH_TILE_WIDTH}" --tile-height "${XL_SYNTH_TILE_HEIGHT}" \
  --workers "${XL_SYNTH_WORKERS}" --worker-memory-gib "${XL_SYNTH_WORKER_MEMORY_GIB}" \
  --retry-memory-gib "${XL_SYNTH_RETRY_MEMORY_GIB}" "${resume_args[@]}"
'
