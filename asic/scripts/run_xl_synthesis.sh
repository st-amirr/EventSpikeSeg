#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CHECKPOINT="${XL_CHECKPOINT:-artifacts/model_checkpoints/dsec_XL/EventSpikeSegXL_seed17_epoch001.pt}"
EXPORT_DIR="${XL_ASIC_EXPORT:-artifacts/ASIC_XL}"

cd "${PROJECT_DIR}"

# Run inside the already-loaded CPU verification image. This is the full structural
# elaboration gate, not a PPA claim. The native XL graph owns 78,707,200 resident
# states, so it is never launched by preparation/tests and requires explicit approval.
docker run --rm --platform linux/amd64 \
  --workdir /workspace \
  --env PYTHONPATH=/workspace/src \
  --env XL_CHECKPOINT="${CHECKPOINT}" --env XL_ASIC_EXPORT="${EXPORT_DIR}" \
  --volume "${PROJECT_DIR}:/workspace:ro" \
  --volume "${PROJECT_DIR}/artifacts:/workspace/artifacts" \
  "${ASIC_CPU_IMAGE:-eventspikeseg:torch2.2.2-cpu-verification}" \
  bash -lc 'bash asic/scripts/prepare_xl_asic.sh && yosys -l "${XL_ASIC_EXPORT}/xl_full_synthesis.log" -p "
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
    ${XL_ASIC_EXPORT}/generated_eventspikesegxl_dag_top.sv;
  hierarchy -top eventspikesegxl_dag_top;
  proc; memory; opt; check
"'
