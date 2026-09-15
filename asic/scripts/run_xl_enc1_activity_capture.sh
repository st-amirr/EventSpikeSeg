#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
EXPORT_DIR="${XL_ASIC_EXPORT:-artifacts/ASIC_XL}"
CHECKPOINT="${XL_CHECKPOINT:-artifacts/model_checkpoints/dsec_XL/EventSpikeSegXL_seed17_epoch001.pt}"
EVENT_FILE="${XL_EVENT_FILE:-/dsec_sample/zurich_city_13_a/events.h5}"
ACTIVITY_DIR="${XL_ACTIVITY_DIR:-artifacts/ASIC_XL/activity/enc1_depthwise_1x1}"
TRACE="${XL_ACTIVITY_TRACE:-${ACTIVITY_DIR}/exact_actor_trace.json}"
RESUME="${XL_ACTIVITY_RESUME:-artifacts/RTL/profile/xl_enc1_depthwise_trace.resume.pkl}"
PROFILE="${XL_ACTIVITY_PROFILE:-artifacts/RTL/profile/xl_enc1_depthwise_trace_profile.json}"
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
mkdir -p \"${ACTIVITY_DIR}\" \"$(dirname "${PROFILE}")\"
python scripts/capture_xl_actor_trace.py \\
  --export \"${EXPORT_DIR}\" --checkpoint \"${CHECKPOINT}\" \\
  --event-file \"${EVENT_FILE}\" --actor enc1.depthwise --duration-ms 50 \\
  --workers \"${THREADS}\" --resume-checkpoint \"${RESUME}\" \\
  --trace-output \"${TRACE}\" --profile-output \"${PROFILE}\"
python scripts/run_xl_enc1_depthwise_activity_vcd.py \\
  --trace \"${TRACE}\" --export \"${EXPORT_DIR}\" \\
  --checkpoint \"${CHECKPOINT}\" --event-file \"${EVENT_FILE}\" \\
  --output-dir \"${ACTIVITY_DIR}\"
"
