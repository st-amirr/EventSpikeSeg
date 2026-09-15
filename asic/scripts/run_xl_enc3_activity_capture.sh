#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
EXPORT_DIR="${XL_ASIC_EXPORT:-artifacts/ASIC_XL}"
CHECKPOINT="${XL_CHECKPOINT:-artifacts/model_checkpoints/dsec_XL/EventSpikeSegXL_seed17_epoch001.pt}"
EVENT_FILE="${XL_EVENT_FILE:-/dsec_sample/zurich_city_13_a/events.h5}"
PROFILE_DIR="${XL_ACTIVITY_PROFILE_DIR:-artifacts/RTL/profile}"
ACTIVITY_DIR="${XL_ACTIVITY_DIR:-artifacts/ASIC_XL/activity/enc3_pointwise_1x1}"
TRACE="${XL_ACTIVITY_TRACE:-${ACTIVITY_DIR}/exact_actor_trace.json}"
RESUME="${XL_ACTIVITY_RESUME:-${PROFILE_DIR}/xl_enc3_pointwise_trace.resume.pkl}"
PROFILE="${XL_ACTIVITY_PROFILE:-${PROFILE_DIR}/xl_enc3_pointwise_trace_profile.json}"
LOG="${XL_ACTIVITY_LOG:-${PROFILE_DIR}/xl_enc3_pointwise_trace_profile.log}"
THREADS="${XL_SIM_THREADS:-4}"

cd "${PROJECT_DIR}"
docker run --rm --platform linux/amd64 \
  --workdir /workspace \
  --env PYTHONPATH=/workspace/src \
  --env OMP_NUM_THREADS="${THREADS}" \
  --env MKL_NUM_THREADS="${THREADS}" \
  --env OPENBLAS_NUM_THREADS="${THREADS}" \
  --volume "${PROJECT_DIR}:/workspace:ro" \
  --volume "${PROJECT_DIR}/artifacts:/workspace/artifacts" \
  --volume "${PROJECT_DIR}/artifacts/DSEC_sample:/dsec_sample:ro" \
  "${ASIC_CPU_IMAGE:-eventspikeseg:torch2.2.2-cpu-verification-guarded}" bash -lc "
set -euo pipefail
mkdir -p \"$(dirname "${PROFILE}")\" \"${ACTIVITY_DIR}\"
python scripts/profile_asic_dsec.py \\
  --export \"${EXPORT_DIR}\" \\
  --checkpoint \"${CHECKPOINT}\" \\
  --event-file \"${EVENT_FILE}\" \\
  --start-ms 0 --duration-ms 50 --progress --workers \"${THREADS}\" \\
  --resume-checkpoint \"${RESUME}\" \\
  --prediction-output \"${ACTIVITY_DIR}/prediction.npy\" \\
  --actor-trace enc3.pointwise --actor-trace-output \"${TRACE}\" \\
  --output \"${PROFILE}\" 2>&1 | tee -a \"${LOG}\"
python scripts/run_xl_actor_activity_vcd.py \\
  --trace \"${TRACE}\" --export \"${EXPORT_DIR}\" \\
  --checkpoint \"${CHECKPOINT}\" --event-file \"${EVENT_FILE}\" \\
  --output-dir \"${ACTIVITY_DIR}\"
"
