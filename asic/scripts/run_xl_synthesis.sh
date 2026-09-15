#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CHECKPOINT="${XL_CHECKPOINT:-artifacts/model_checkpoints/dsec_XL/EventSpikeSegXL_seed17_epoch001.pt}"
EXPORT_DIR="${XL_ASIC_EXPORT:-artifacts/ASIC_XL}"
ARTIFACTS_DIR="${EVENTSPIKESEG_ARTIFACTS_DIR:-${PROJECT_DIR}/artifacts}"
FULL_CHIP_DIR="${ARTIFACTS_DIR}/ASIC_XL/full_chip_layout"

cd "${PROJECT_DIR}"
mkdir -p "${FULL_CHIP_DIR}"

# Run inside the already-loaded CPU verification image. This is the full structural
# elaboration gate, not a PPA claim. The native XL graph owns 78,707,200 resident
# states, so it is never launched by preparation/tests and requires explicit approval.
docker run --rm --platform linux/amd64 \
  --name "${XL_FULL_SYNTH_CONTAINER_NAME:-eventspikeseg-xl-full-synthesis-beta48}" \
  --memory "${XL_FULL_SYNTH_MEMORY:-8g}" --memory-swap "${XL_FULL_SYNTH_MEMORY:-8g}" \
  --cpus "${XL_FULL_SYNTH_CPUS:-4}" --ulimit core=0 \
  --workdir /project \
  --env PYTHONPATH=/project/src \
  --env LD_PRELOAD=/opt/eventspikeseg/no_core_dump.so \
  --env XL_FULL_SYNTH_MEMORY="${XL_FULL_SYNTH_MEMORY:-8g}" \
  --env XL_FULL_SYNTH_CPUS="${XL_FULL_SYNTH_CPUS:-4}" \
  --env XL_CHECKPOINT="${CHECKPOINT}" --env XL_ASIC_EXPORT="${EXPORT_DIR}" \
  --volume "${PROJECT_DIR}:/project:ro" \
  --volume "${ARTIFACTS_DIR}:/workspace/artifacts" \
  "${ASIC_CPU_IMAGE:-eventspikeseg:torch2.2.2-cpu-verification-guarded}" \
  bash -lc 'set -euo pipefail
case "${XL_CHECKPOINT}" in artifacts/*) XL_CHECKPOINT="/workspace/artifacts/${XL_CHECKPOINT#artifacts/}" ;; esac
case "${XL_ASIC_EXPORT}" in artifacts/*) XL_ASIC_EXPORT="/workspace/artifacts/${XL_ASIC_EXPORT#artifacts/}" ;; esac
export XL_CHECKPOINT XL_ASIC_EXPORT
out="${XL_ASIC_EXPORT}/full_chip_layout"
mkdir -p "${out}"
python scripts/preflight_xl_full_chip.py "${XL_ASIC_EXPORT}" \
  --output "${out}/preflight.json"
started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
set +e
yosys -l "${out}/full_synthesis.log" -p "
  read_verilog -sv \
    asic/rtl/event_fork2.sv asic/rtl/event_join2.sv \
    asic/rtl/resident_convolution_synapses.sv \
    asic/rtl/resident_plif_population.sv \
    asic/rtl/retinotopic_mechanism_update.sv \
    asic/rtl/resident_retinotopic_plif_population.sv \
    asic/rtl/resident_channelized_plif_actor.sv \
    asic/rtl/tiled_resident_channelized_plif_actor.sv \
    asic/rtl/streaming_resident_channelized_plif_actor.sv \
    asic/rtl/resident_event_ingress_adapter.sv \
    asic/rtl/resident_spike_vector_channel_offset.sv \
    asic/rtl/resident_spike_vector_edge.sv \
    asic/rtl/resident_spike_vector_fork2.sv \
    asic/rtl/resident_spike_vector_union2.sv \
    asic/rtl/resident_spike_vector_upsample2x.sv \
    asic/rtl/resident_spike_mask_attention.sv \
    asic/rtl/resident_temporal_class_readout.sv \
    asic/rtl/tiled_resident_temporal_class_readout.sv \
    ${XL_ASIC_EXPORT}/generated_eventspikesegxl_dag_top.sv;
  hierarchy -top eventspikesegxl_dag_top;
  proc; memory; opt; check
"
rc=$?
set -e
finished="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
status=FAILED
if [[ "${rc}" -eq 0 ]] && grep -q "End of script" "${out}/full_synthesis.log"; then status=PASS; fi
python - "${out}/full_synthesis.status.json" "${status}" "${rc}" "${started}" "${finished}" <<PY
import json, pathlib, sys
path, status, code, started, finished = sys.argv[1:]
data = {"schema_version": "1.0.0", "stage": "full_structural_elaboration", "status": status, "exit_code": int(code), "started_utc": started, "finished_utc": finished, "memory_limit": "${XL_FULL_SYNTH_MEMORY:-8g}", "cpu_limit": "${XL_FULL_SYNTH_CPUS:-4}", "claim_boundary": "Structural elaboration is a prerequisite and is not full-chip PPA."}
target = pathlib.Path(path)
tmp = target.with_suffix(target.suffix + ".tmp")
tmp.write_text(json.dumps(data, indent=2) + "\n")
tmp.replace(target)
PY
[[ "${status}" == PASS ]]'
