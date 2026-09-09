#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
EXPORT_DIR="${XL_ASIC_EXPORT:-artifacts/ASIC_XL}"
CHECKPOINT="${XL_CHECKPOINT:-artifacts/model_checkpoints/dsec_XL/EventSpikeSegXL_seed17_epoch001.pt}"
EVENT_FILE="${XL_EVENT_FILE:-/dsec_sample/zurich_city_13_a/events.h5}"
OUTPUT="${XL_SIM_OUTPUT:-artifacts/RTL/profile/xl_epoch001_zurich_city_13_a_native_50ms.json}"
LOG="${XL_SIM_LOG:-artifacts/RTL/profile/xl_epoch001_zurich_city_13_a_native_50ms.log}"
RESUME="${XL_SIM_RESUME:-artifacts/RTL/profile/xl_epoch001_zurich_city_13_a_native_50ms.resume.pkl}"
PREDICTION="${XL_SIM_PREDICTION:-artifacts/RTL/profile/xl_epoch001_zurich_city_13_a_native_50ms_prediction.npy}"
# Typed dense temporal state removes Python-object growth while exact actor
# scatter remains parallel over disjoint output-channel ranges.
THREADS="${XL_SIM_THREADS:-4}"
IMAGE="${ASIC_CPU_IMAGE:-eventspikeseg:torch2.2.2-cpu-verification}"

cd "${PROJECT_DIR}"
docker run --rm --platform linux/amd64 \
  --workdir /workspace \
  --env PYTHONPATH=/workspace/src \
  --env OMP_NUM_THREADS="${THREADS}" \
  --env MKL_NUM_THREADS="${THREADS}" \
  --env OPENBLAS_NUM_THREADS="${THREADS}" \
  --env XL_ASIC_EXPORT="${EXPORT_DIR}" \
  --env XL_CHECKPOINT="${CHECKPOINT}" \
  --env XL_EVENT_FILE="${EVENT_FILE}" \
  --env XL_SIM_OUTPUT="${OUTPUT}" \
  --env XL_SIM_LOG="${LOG}" \
  --env XL_SIM_RESUME="${RESUME}" \
  --env XL_SIM_PREDICTION="${PREDICTION}" \
  --volume "${PROJECT_DIR}:/workspace:ro" \
  --volume "${PROJECT_DIR}/artifacts:/workspace/artifacts" \
  --volume "${PROJECT_DIR}/artifacts/DSEC_sample:/dsec_sample:ro" \
  "${IMAGE}" bash -lc '
set -o pipefail
mkdir -p "$(dirname "${XL_SIM_OUTPUT}")" "$(dirname "${XL_SIM_LOG}")"
python scripts/profile_asic_dsec.py \
  --export "${XL_ASIC_EXPORT}" \
  --checkpoint "${XL_CHECKPOINT}" \
  --event-file "${XL_EVENT_FILE}" \
  --start-ms 0 --duration-ms 50 --progress --workers "${OMP_NUM_THREADS}" \
  --resume-checkpoint "${XL_SIM_RESUME}" \
  --prediction-output "${XL_SIM_PREDICTION}" \
  --output "${XL_SIM_OUTPUT}" 2>&1 | tee -a "${XL_SIM_LOG}"
'
