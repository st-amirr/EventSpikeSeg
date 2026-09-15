#!/usr/bin/env bash
set -euo pipefail

# Keep Git Bash/MSYS from rewriting Linux paths passed to Docker.
export MSYS_NO_PATHCONV=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VARIANT="xl_enc1_depthwise_1x1_beta48"
RESULTS="artifacts/OpenROAD/results/asap7/resident_actor_tile_pnr_top/${VARIANT}"
TRACE="${XL_ENC1_TRACE:-artifacts/ASIC_XL/activity/enc1_depthwise_1x1/exact_actor_trace.json}"
OUT="${XL_ENC1_GATE_POWER_DIR:-artifacts/ASIC_XL/activity/enc1_depthwise_1x1_beta48_gate}"
CHECKPOINT="${XL_CHECKPOINT:-artifacts/model_checkpoints/dsec_XL/EventSpikeSegXL_seed17_epoch001.pt}"
EVENT_FILE="${XL_EVENT_FILE:-artifacts/DSEC_sample/zurich_city_13_a/events.h5}"
ORFS_IMAGE="${ORFS_IMAGE:-openroad/orfs:latest}"
SIM_IMAGE="${ASIC_CPU_IMAGE:-eventspikeseg:torch2.2.2-cpu-verification-guarded}"

cd "${PROJECT_DIR}"
mkdir -p "${OUT}"
OUT_ABS="$(cd "$(dirname "${OUT}")" && pwd)/$(basename "${OUT}")"
docker run --rm --platform linux/amd64 --workdir /workspace \
  --env PYTHONPATH=/workspace:/workspace/src \
  --volume "${PROJECT_DIR}:/workspace:ro" --volume "${OUT_ABS}:/out" \
  "${SIM_IMAGE}" python scripts/prepare_xl_enc1_gate_power.py prepare \
  --trace "/workspace/${TRACE}" --model-spec /workspace/artifacts/ASIC_XL/model_spec.yaml \
  --checkpoint "/workspace/${CHECKPOINT}" --event-file "/workspace/${EVENT_FILE}" \
  --rtl-results "/workspace/$(dirname "${TRACE}")/results.xml" \
  --odb "/workspace/${RESULTS}/6_final.odb" --spef "/workspace/${RESULTS}/6_final.spef" \
  --sdc "/workspace/${RESULTS}/6_final.sdc" --netlist "/workspace/${RESULTS}/6_final.v" \
  --output-dir /out

cat >"${OUT}/write_sdf.tcl" <<'EOF'
set platform /OpenROAD-flow-scripts/flow/platforms/asap7
foreach lib [glob $platform/lib/NLDM/*RVT*TT*.lib*] { read_liberty $lib }
read_db /workspace/artifacts/OpenROAD/results/asap7/resident_actor_tile_pnr_top/xl_enc1_depthwise_1x1_beta48/6_final.odb
read_sdc /workspace/artifacts/OpenROAD/results/asap7/resident_actor_tile_pnr_top/xl_enc1_depthwise_1x1_beta48/6_final.sdc
read_spef /workspace/artifacts/OpenROAD/results/asap7/resident_actor_tile_pnr_top/xl_enc1_depthwise_1x1_beta48/6_final.spef
write_sdf -include_typ -digits 6 -no_timestamp -no_version /out/enc1_depthwise_beta48.sdf
puts "SDF_GENERATION_PASS"
EOF

docker run --rm --platform linux/amd64 \
  --volume "${PROJECT_DIR}:/workspace:ro" --volume "${OUT_ABS}:/out" \
  "${ORFS_IMAGE}" bash -lc '
set -euo pipefail
OR=/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad
"$OR" -no_init -exit /out/write_sdf.tcl 2>&1 | tee /out/write_sdf.log
grep -q SDF_GENERATION_PASS /out/write_sdf.log
mkdir -p /out/stdcells
cp /OpenROAD-flow-scripts/flow/platforms/asap7/verilog/stdcell/asap7sc7p5t_*_RVT_TT_*.v /out/stdcells/
'
docker run --rm --platform linux/amd64 --workdir /workspace \
  --env PYTHONPATH=/workspace:/workspace/src \
  --volume "${PROJECT_DIR}:/workspace:ro" --volume "${OUT_ABS}:/out" \
  "${SIM_IMAGE}" bash -lc 'python scripts/prepare_xl_enc1_gate_power.py validate-sdf \
  --log /out/write_sdf.log --sdf /out/enc1_depthwise_beta48.sdf \
  > /out/sdf_generation_summary.json'

docker run --rm --platform linux/amd64 --workdir /workspace \
  --env PYTHONPATH=/workspace:/workspace/src \
  --volume "${PROJECT_DIR}:/workspace:ro" --volume "${OUT_ABS}:/out" \
  "${SIM_IMAGE}" python scripts/make_iverilog_sdf_compat.py \
  --sdf /out/enc1_depthwise_beta48.sdf --stdcells /out/stdcells \
  --output-dir /out/sim_models

docker run --rm --platform linux/amd64 --workdir /out \
  --volume "${PROJECT_DIR}:/workspace:ro" --volume "${OUT_ABS}:/out" \
  "${SIM_IMAGE}" bash -lc '
set -euo pipefail
  iverilog -g2012 -gno-specify -s xl_enc1_depthwise_gate_tb \
  -o gate_sim_functional.vvp sim_models/stdcells/*.v \
  /workspace/artifacts/OpenROAD/results/asap7/resident_actor_tile_pnr_top/xl_enc1_depthwise_1x1_beta48/6_final.v \
  xl_enc1_depthwise_gate_tb.sv 2>&1 | tee compile_functional.log
vvp -N gate_sim_functional.vvp 2>&1 | tee gate_functional_replay.log
'
docker run --rm --platform linux/amd64 --workdir /workspace \
  --env PYTHONPATH=/workspace:/workspace/src \
  --volume "${PROJECT_DIR}:/workspace:ro" --volume "${OUT_ABS}:/out" \
  "${SIM_IMAGE}" bash -lc 'python scripts/prepare_xl_enc1_gate_power.py validate-sim \
  --log /out/gate_functional_replay.log --vcd /out/enc1_depthwise_beta48_gate.vcd \
  > /out/gate_replay_summary.json'

cat >"${OUT}/activity_power.tcl" <<'EOF'
set platform /OpenROAD-flow-scripts/flow/platforms/asap7
foreach lib [glob $platform/lib/NLDM/*RVT*TT*.lib*] { read_liberty $lib }
read_db /workspace/artifacts/OpenROAD/results/asap7/resident_actor_tile_pnr_top/xl_enc1_depthwise_1x1_beta48/6_final.odb
read_sdc /workspace/artifacts/OpenROAD/results/asap7/resident_actor_tile_pnr_top/xl_enc1_depthwise_1x1_beta48/6_final.sdc
read_spef /workspace/artifacts/OpenROAD/results/asap7/resident_actor_tile_pnr_top/xl_enc1_depthwise_1x1_beta48/6_final.spef
read_vcd -scope xl_enc1_depthwise_gate_tb/dut /out/enc1_depthwise_beta48_gate.vcd
report_activity_annotation > /out/activity_annotation.rpt
report_activity_annotation -report_unannotated > /out/activity_unannotated.rpt
report_power -digits 9 > /out/activity_power.rpt
puts "ACTIVITY_POWER_PASS"
EOF

docker run --rm --platform linux/amd64 \
  --volume "${PROJECT_DIR}:/workspace:ro" --volume "${OUT_ABS}:/out" \
  "${ORFS_IMAGE}" bash -lc '
set -euo pipefail
/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad -no_init -exit \
  /out/activity_power.tcl 2>&1 | tee /out/activity_power.log
'
docker run --rm --platform linux/amd64 --workdir /workspace \
  --env PYTHONPATH=/workspace:/workspace/src \
  --volume "${PROJECT_DIR}:/workspace:ro" --volume "${OUT_ABS}:/out" \
  "${SIM_IMAGE}" bash -lc 'python scripts/prepare_xl_enc1_gate_power.py validate-power \
  --log /out/activity_power.log --report /out/activity_power.rpt \
  --annotation-report /out/activity_annotation.rpt \
  > /out/activity_power_summary.json'
printf 'Validated checkpoint-exact enc1.depthwise beta48 gate activity power: %s\n' "${OUT}"
