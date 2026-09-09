#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CHECKPOINT="${XL_CHECKPOINT:-artifacts/model_checkpoints/dsec_XL/EventSpikeSegXL_seed17_epoch001.pt}"
EXPORT_DIR="${XL_ASIC_EXPORT:-artifacts/ASIC_XL}"
IMAGE="${ASIC_CPU_IMAGE:-eventspikeseg:torch2.2.2-cpu-verification}"
TILE_WIDTH="${XL_SYNTH_TILE_WIDTH:-2}"
TILE_HEIGHT="${XL_SYNTH_TILE_HEIGHT:-2}"

cd "${PROJECT_DIR}"

docker run --rm --platform linux/amd64 \
  --workdir /workspace \
  --env PYTHONPATH=/workspace/src \
  --env XL_CHECKPOINT="${CHECKPOINT}" --env XL_ASIC_EXPORT="${EXPORT_DIR}" \
  --env XL_SYNTH_TILE_WIDTH="${TILE_WIDTH}" \
  --env XL_SYNTH_TILE_HEIGHT="${TILE_HEIGHT}" \
  --volume "${PROJECT_DIR}:/workspace:ro" \
  --volume "${PROJECT_DIR}/artifacts:/workspace/artifacts" \
  "${IMAGE}" bash -lc '
set -euo pipefail
bash asic/scripts/prepare_xl_asic.sh
log_dir="${XL_ASIC_EXPORT}/partitioned_synthesis_${XL_SYNTH_TILE_WIDTH}x${XL_SYNTH_TILE_HEIGHT}"
mkdir -p "${log_dir}"
summary="${log_dir}/summary.tsv"
printf "actor\tstatus\tlog\n" > "${summary}"

rtl_sources="asic/rtl/resident_convolution_synapses.sv \
asic/rtl/resident_plif_population.sv \
asic/rtl/retinotopic_mechanism_update.sv \
asic/rtl/resident_retinotopic_plif_population.sv \
asic/rtl/resident_channelized_plif_actor.sv \
asic/rtl/tiled_resident_channelized_plif_actor.sv"

attention_log="${log_dir}/attention.log"
yosys -q -l "${attention_log}" -p "
  read_verilog -sv asic/rtl/resident_spike_mask_attention.sv;
  hierarchy -top resident_spike_mask_attention;
  proc; opt; check
"
printf "attention\tPASS\t%s\n" "${attention_log}" >> "${summary}"

mapfile -t actors < <(python -c "
import json, os
from pathlib import Path
spec = json.loads((Path(os.environ[\"XL_ASIC_EXPORT\"]) / \"model_spec.yaml\").read_text())
print(*spec[\"graph\"][\"actor_topological_order\"], sep=\"\\n\")
")
if [[ "${#actors[@]}" -ne 44 ]]; then
  printf "Expected 44 XL actors, found %s.\n" "${#actors[@]}" >&2
  exit 2
fi

failed=0
i=0
for actor in "${actors[@]}"; do
  safe_name="${actor//./_}"
  top="${log_dir}/${safe_name}_tile.sv"
  log="${log_dir}/${safe_name}.log"
  printf "[%s/%s] synthesizing %s\n" "$((i+=1))" "${#actors[@]}" "${actor}"
  python scripts/generate_resident_tile_pnr_top.py \
    "${XL_ASIC_EXPORT}/model_spec.yaml" "${top}" \
    --actor "${actor}" --tile-width "${XL_SYNTH_TILE_WIDTH}" \
    --tile-height "${XL_SYNTH_TILE_HEIGHT}"
  if yosys -q -l "${log}" -p "
    read_verilog -sv ${rtl_sources} ${top};
    hierarchy -top resident_actor_tile_pnr_top;
    proc; memory; opt; check
  "; then
    printf "%s\tPASS\t%s\n" "${actor}" "${log}" >> "${summary}"
  else
    printf "%s\tFAIL\t%s\n" "${actor}" "${log}" >> "${summary}"
    failed=1
  fi
done

cat "${summary}"
exit "${failed}"
' 
