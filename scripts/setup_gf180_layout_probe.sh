#!/bin/sh
# Build official Magic/Netgen technology collateral only; not a full PDK install.
set -eu
task_source=/workspace/artifacts/analog_asic/pdk/gf180_open_pdks_source
task_prefix=/workspace/artifacts/analog_asic/pdk/gf180_layout_probe_install
cd "$task_source"
test "$(git rev-parse HEAD)" = "801834fcbf9119e6fd4462f97da9e637f284539a"
./configure --enable-gf180mcu-pdk --with-gf180mcu-variants=D --prefix="$task_prefix" \
    --disable-primitive-gf180mcu --disable-verification-gf180mcu --disable-io-gf180mcu \
    --disable-sc-7t5v0-gf180mcu --disable-sc-9t5v0-gf180mcu --disable-sram-gf180mcu \
    --disable-alpha-gf180mcu --disable-osu-sc-gf180mcu --disable-ocd-sc-gf180mcu \
    --disable-avalon-sc-gf180mcu --disable-re-efuse-gf180mcu --disable-ocd-io-gf180mcu \
    --disable-ocd-sram-gf180mcu --disable-klayout --disable-irsim --disable-librelane \
    --disable-qflow --disable-xschem --disable-xcircuit
make -C gf180mcu magic-D netgen-D
magic --version
