# Results

## 2026-08-06 — Completed round-one ten-model benchmark

Protocol: seed 17, 10 epochs, 2,048 training samples, 512 held-out samples, 64×64 output, 20 internal SNN steps, batch size 4.

| rank | architecture | mIoU | pixel accuracy | parameters | spike rate |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `v10_fpga_hybrid` | 0.3130 | 0.7871 | 44,016 | 0.1412 |
| 2 | `v03_dw_dilated` | 0.2970 | 0.7711 | 40,824 | 0.1125 |
| 3 | `v02_dw_light` | 0.2850 | 0.7808 | 30,744 | 0.1305 |
| 4 | `v08_dw_multiscale_aux` | 0.2591 | 0.7488 | 44,016 | 0.1051 |
| 5 | `v04_dw_multiscale` | 0.2444 | 0.7556 | 42,552 | 0.1188 |
| 6 | `v01_std_unet_light` | 0.2396 | 0.8005 | 193,824 | 0.0849 |
| 7 | `v09_dw_single_skip` | 0.2392 | 0.7521 | 43,728 | 0.1168 |
| 8 | `v07_dw_multiscale_gap` | 0.2182 | 0.7775 | 48,456 | 0.0933 |
| 9 | `v05_dw_multiscale_affine` | 0.2015 | 0.7688 | 43,728 | 0.0786 |
| 10 | `v06_dw_multiscale_bn` | 0.1730 | 0.4855 | 44,904 | 0.1271 |

### Winner per-class IoU

| class | IoU |
| --- | ---: |
| flat | 0.6083 |
| construction+sky | 0.8021 |
| object | 0.0000 |
| nature | 0.1510 |
| human | 0.0000 |
| vehicle | 0.3168 |

The benchmark establishes `v10_fpga_hybrid` as the round-one structural incumbent only. It does not establish a satisfactory six-class model because two classes have zero IoU.

### Interpretation

- `v03` showed that one dilated context block can outperform the heavier parallel multiscale baseline.
- `v02` retained strong mIoU with the lowest parameter count among the leaders.
- `v08` suggests auxiliary supervision is useful enough to carry into round two.
- BN achieved low training loss but poor held-out mIoU, so training loss was not a reliable selection metric.
- GAP and static affine gain did not justify their cost as standalone additions in this run.


## 2026-08-07 — First PLIF/adaptation top-five completed and rejected

Protocol matched round one: seed 17, 10 epochs, 2,048 training samples, 512 held-out samples, 64×64, 20 internal steps, batch size 4.

| rank | architecture | mIoU | pixel accuracy | parameters | spike rate |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `f01_v10_plif_long` | 0.2464 | 0.7729 | 45,204 | 0.1432 |
| 2 | `f05_dilated_aux_plif_long` | 0.2340 | 0.7571 | 43,092 | 0.1063 |
| 3 | `f03_v03_dilated_plif_long` | 0.2293 | 0.7584 | 41,814 | 0.1089 |
| 4 | `f02_v10_plif_inst_long` | 0.1754 | 0.6933 | 45,204 | 0.1290 |
| 5 | `f04_v02_light_plif_inst_long` | 0.0167 | 0.1004 | 31,542 | 0.0000 |

The best v1 contender was 0.0667 mIoU below the incumbent. Hard hidden competition was harmful, a fixed four-step adaptation duration did not adapt to the data, and global `amax` adaptation could suppress a whole channel after one spike. These are measured failures, not evidence that PLIF itself is unsuitable. Table identifiers retain their original experiment names.


## 2026-08-07 — Completed retinotopic/neuron-mechanism screening run

Protocol recorded in the saved checkpoints: seed 17, 5 epochs, 256 training samples, 128 held-out samples, 64×64 output, 8 internal SNN timesteps.

| rank | architecture | mIoU | pixel accuracy | parameters | spike rate |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `f05_v02_light_peer_membrane_inhibition` | 0.1991 | 0.7607 | 33,455 | 0.0616 |
| 2 | `f02_v10_plif_threshold_adaptation` | 0.1459 | 0.7395 | 46,422 | 0.0470 |
| 3 | `f01_v10_plif_threshold_wta` | 0.1402 | 0.7334 | 46,392 | 0.0457 |
| 4 | `f04_v03_dilated_threshold_adaptation` | 0.1366 | 0.7217 | 42,830 | 0.0513 |
| 5 | `f03_v10_plif_winner_peer_inhibition` | 0.1233 | 0.7384 | 46,437 | 0.0415 |

### Mechanism interpretation

- Adding triangular threshold adaptation to the same v10 family gave a small improvement over PLIF+threshold alone (`0.1459` vs `0.1402`).
- Hidden `winner_peer` inhibition was harmful: its encoder spike rates fell from `0.0474` at enc1 to `0.00306` at enc2 and `0.000149` at enc3, indicating feature starvation.
- Stem-only `peer_membrane` inhibition did not cause that collapse and produced the best mIoU. Its encoder spike rates remained `0.0770`, `0.0363`, and `0.0239`.
- The winning checkpoint learned mean inhibition strength `0.2082`, threshold-adaptation strength `0.1879`, and adaptation duration `5.196`, close to their initial values `0.20`, `0.20`, and `5.0`.
- All five still failed badly on rare classes under this small-data screen. The winner's per-class IoUs were flat `0.4113`, construction+sky `0.7825`, object `0.0006`, nature `0`, human `0`, vehicle `0`.

Because this run used only 256 training samples, it is used to choose neuron dynamics, not to replace the full-budget `v10_fpga_hybrid` incumbent.

## 2026-08-08 — Structural top-five completed

Protocol: seed 17, 8 epochs, 2,048 train samples, 512 held-out samples, 64×64, 15 internal timesteps, batch 14, learning rate 0.002.

| rank | architecture | mIoU | pixel accuracy | parameters | spike rate |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `f05_compact16_dilated` | **0.2596** | **0.7822** | **21,491** | 0.1093 |
| 2 | `f02_wide32_multiscale` | 0.2284 | 0.7763 | 77,751 | 0.0965 |
| 3 | `f04_deep4_dilated` | 0.2079 | 0.6792 | 107,131 | 0.1495 |
| 4 | `f01_base24_multiscale` | 0.1626 | 0.7294 | 46,423 | 0.0497 |
| 5 | `f03_early5x5_multiscale` | 0.1482 | 0.6719 | 49,111 | 0.0670 |

### Per-class evidence driving the next round

| architecture | object | nature | human | vehicle |
| --- | ---: | ---: | ---: | ---: |
| `f02_wide32_multiscale` | **0.0141** | 0.0390 | 0.0000 | 0.0000 |
| `f04_deep4_dilated` | 0.0049 | **0.0712** | 0.0060 | **0.1230** |
| `f05_compact16_dilated` | 0.0002 | 0.0346 | **0.0181** | 0.0757 |

Interpretation:

- `f05` establishes that a small three-stage single-dilation backbone can outperform much larger structures.
- `f02` supports retaining some capacity for feature diversity because it produced the best object IoU.
- `f04` supports retaining deep semantic information because it produced the best aggregate rare-class coverage, especially nature and vehicle.
- `f03` rejects early 5×5 processing.
- the multiscale-average models did not beat the single-dilation models, motivating branch concatenation rather than averaging.
- none of the five beat the historical `v10_fpga_hybrid` result of 0.3130 mIoU.

## Completed top-three accuracy search — seed 17

Protocol: 8 epochs, 2,048 training samples, 512 held-out samples, 64×64 output, 15 internal timesteps, learning rate 0.002.

| Rank | Architecture | mIoU | Pixel accuracy | Parameters | Mean spike rate |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `t02_dualpath_detail` | **0.2728** | **0.7952** | **24,211** | 0.1395 |
| 2 | `t01_spike_pyramid_concat` | 0.1671 | 0.6122 | 63,147 | 0.1145 |
| 3 | `t03_deep_attention_fpn` | 0.1555 | 0.7151 | 108,781 | **0.0592** |

T2 per-class IoU: flat 0.6190, construction+sky 0.8169, object 0.0095, nature 0.0221, human 0.0000, vehicle 0.1691. These are measured benchmark results only. No accuracy result is yet recorded for `final_dualpath_wide32`.

## TIMESTEP SWEEP SUMMARY

| Timesteps (T) | Mean IoU (mIoU) | Pixel Accuracy (acc) | Mean Spike Rate | Inference Time (s) |
|:-------------:|:---------------:|:--------------------:|:---------------:|:------------------:|
| 12            | 0.2408          | 0.8284               | 0.08029         | 523.2              |
| 15            | 0.2349          | 0.8220               | 0.06780         | 688.4              |
| 10            | 0.2330          | 0.8211               | 0.06075         | 452.2              |
| 8             | 0.2316          | 0.8189               | 0.08601         | 356.4              |
| 6             | 0.2003          | 0.7826               | 0.06168         | 278.0              |
| 4             | 0.0180          | 0.1082               | 0.00000         | 196.2              |

Performance improves with more timesteps up to T=12, after which gains diminish while runtime continues to increase.


## Reproducibility note

The top-ten, top-five, and top-three registries are all trained through `eventspikeseg.train`. Historical suites are pinned to the objective used for the recorded architecture-search results (`0.5 CE + 0.5 focal + 0.75 Dice`, plus historical auxiliary supervision). The final suite intentionally uses CE coefficient `1.0`, validation-on-train-holdout best-checkpoint selection, and the canonical refinement schedule. The old standalone `benchmark_top_three.py` runner is retired; its unique protocol has been represented in the shared trainer/launch configuration.


## 2026-08-14 — Temporal-v2 implementation validation

The repeated-static data protocol was retired after diagnosis of the ~0.24 mIoU plateau in the long final-model run. Previous mIoU/timestep numbers above remain historical measurements of that obsolete protocol and must not be interpreted as temporal-v2 accuracy.

Measured software validation for the replacement implementation:

- `pytest -q`: **37 passed**;
- sequential windows preserve chronological frame order;
- sequence boundaries and frame-index gaps block window construction;
- validation train/holdout sequence IDs are disjoint;
- chronological event-bin loading preserves interval order and polarity-channel identity;
- manifest schema/sequence validation and exact holdout reconstruction are covered;
- both final models accept the two-channel event-bin representation;
- the final verified suite passes **45 tests** and Ruff with no errors.

Real dataset inspection found **2,887** train event tensors and **10,001** train masks. No temporal-v2 mIoU should be treated as representative until the missing training event tensors/recordings are restored.

### Capacity assessment for event-bin input

Exact two-channel parameter counts are:

| model | parameters |
| --- | ---: |
| canonical `EventSpikeSeg140k` | 140,089 |
| `EventSpikeSegXL` | 236,445 |

Historical repeated-static experiments do not show a positive correlation between parameter count and mIoU: the 21,491-parameter structural model beat the 77,751- and 107,131-parameter alternatives, and the 24,211-parameter dual-path model beat the 63,147- and 108,781-parameter alternatives. This is evidence that parameter count alone was not the plateau cause, but it is not a ranking under the current temporal protocol. The current ASIC target is the 149,835-parameter, six-class `EventSpikeSeg140k` v8 model at native 440x640 resolution; this implementation choice is not a new accuracy result.

No new mIoU, pixel accuracy, spike-rate, latency, power, or FPGA-resource result is claimed for temporal-v2 yet.

## 2026-08-31 — ASIC/RTL verification results

The active epoch-35 six-class checkpoint exports 143,824 int8 convolution weights and 25
permanent PLIF actors. Derived persistent state is 189.60 MiB. Direct-index 24-bit same-bin
current plus touched flags raise the exact logical memory to 281.92 MiB before touched-address
queues; this is a capacity result, not a characterized SRAM area or power result.

The SRAM-integrated reduced 8×8, ten-bin RTL smoke replay used four deterministic input events.
The CPU-only Docker image's Icarus 12 completed the full 25-actor DAG in 206.88 seconds of host
test runtime and matched the
integer reference for all 64 semantic output pixels and the bin-10 completion tag with no RTL
fault. The generated ingress gate excluded 1,024 SRAM-initialization cycles. Measured
steady-state latency was 12,135 cycles total, or 1,213.5 cycles per 5 ms bin. At the explicitly
assumed 100 MHz simulation clock this is 121.35 us per ten-bin frame and 12.135 us/bin,
0.2427% timing-budget utilization, and 412.03x timing headroom. The largest individual
bin-ingress interval was 956 cycles.

The larger integer profile used 160 events and produced 37,065 current rows, 37,068 membrane
rows, and 3,707 spikes. All 23 cocotb RTL component groups, the generated-top contract tests,
and complete-top compilation with both behavioral and macro-selected SRAM paths pass. These
reduced-geometry results verify behavior and simulated cycle latency only; they do not establish
native-resolution throughput, energy, power, or chip area. Full-model routed PPA remains unreported
until native memory banking and representative DSEC activity are available; the later SKY130 result
closes only a reduced actor-tile characterized-SRAM integration check.

Replay profiling now records buffer occupancy directly. The deterministic reduced four-event
smoke fixture observed at most 287 touched-queue entries in one actor and one stored event in
one residual union. The reduced 160-event stress fixture observed maxima of 1,018 and 158.
These measurements explain why the 64-entry default is sufficient for the smoke replay but not
for that stress fixture. The complete smoke replay passes with the actual 64-entry generated-top
default and no overflow; neither fixture is a native DSEC capacity bound.

The final CPU-only implementation-container regression passes 89 Python tests, Ruff, all 23
cocotb component groups, representative Yosys synthesis, and the full exported-DAG replay.
The built image reports Torch `2.2.2+cpu`, no CUDA build, and no available CUDA runtime.

## 2026-08-31 — Predictive OpenROAD actor-prototype result

The official OpenROAD Flow Scripts image completed synthesis, floorplanning, placement, clock
tree synthesis, detailed routing, parasitic extraction, power-grid analysis, and GDS generation
for the integrated `convolution_plif_actor` with 4x4 output/state geometry. The ASAP7 clock was
constrained to 5,000 ps (200 MHz); ASAP7 Liberty units are picoseconds.

| metric | post-route result |
| --- | ---: |
| setup / hold TNS | 0 / 0 ps |
| worst setup slack | 3,887.94 ps |
| worst hold slack | 36.61 ps |
| reported minimum period / nominal fmax | 1,112.06 ps / 899.23 MHz |
| die / core area | 4,006.51 / 3,502.74 um2 |
| non-filler standard-cell area | 1,254.57 um2 |
| non-filler standard cells / sequential cells | 10,023 / 1,553 |
| standard-cell utilization | 35.82% |
| detailed-route DRC violations | 0 |
| maximum-slew / fanout / capacitance violations | 0 / 0 / 0 |
| vectorless power estimate | 1.335 mW |
| worst VDD / VSS IR drop | 0.531 / 0.544 mV |

This is a predictive control/datapath implementation result, not full-model PPA. Public ASAP7
has no characterized SRAM macros, so the reduced state arrays were synthesized into standard
cells; the reported area and vectorless power must not be extrapolated to the 25-actor model or
presented as event-driven inference power. The 899.23 MHz value is an actor-only nominal result,
not end-to-end model throughput. Article-grade PPA still requires a manufacturable PDK with
compiled SRAMs, representative native-resolution event activity for VCD/SAIF power, removal of
the Apple-silicon emulation workaround through a native-x86 run with post-CTS timing repair
enabled.

The clean driver result uses a 64-sink design maximum fanout. It replaced a rejected 280 ps
global transition guardband experiment, which changed mapping enough to increase extracted
library-slew failures. Targeted fanout splitting reduced the routed maximum degree from 136 to
65 and produced +47.64 ps worst slew margin against ASAP7's 320 ps library limit.

## 2026-09-01 — Reduced full-DAG actor-state trace result

The epoch-35 SRAM-integrated 8x8 smoke replay now compares every accepted actor-output spike
against `golden_layer_spikes.npz`, in addition to checking the final semantic frame and
completion tag. All 25 permanent actors were checked by `(bin_tag, channel, y, x)`. The
fixture emitted five actor-spike rows and all matched exactly; actors with no expected output
were also required to remain silent.

The first membrane-trace attempt detected one-unit differences after multi-bin idle periods.
The Python oracle had rounded `beta**delta` in coefficient space and then multiplied membrane
once. The RTL—and the intended repeated 5 ms update contract—rounds membrane after every beta
application. After correcting the integer oracle and regenerating the unchanged four-event
fixture, RTL exactly matched **1,532 accumulated-current rows**, **1,538 candidate/membrane/
spike transition rows**, and all five emitted spike rows. The replay completed successfully
in 211.97 seconds of Icarus host runtime, and the regression suite now contains 88 tests.

The trace monitors do not change architectural timing: 1,024 initialization cycles remain
excluded and steady-state frame completion remains 12,135 cycles. The extended replay also
matches adaptation age and amplitude exactly for all **126 adaptation-enabled commit rows**;
the Icarus gate passes in 209.55 seconds of host runtime. This result strengthens routing and
actor-state equivalence for the deterministic reduced fixture only. It is not evidence for
native DSEC activity, throughput, queue capacity, power, or energy.

## 2026-09-01 — Manufacturable SKY130 SRAM actor-tile integration

The official OpenROAD Flow Scripts image completed merged GDS for the reduced 4x4
`convolution_plif_actor` on SKY130HD with two characterized
`sky130_sram_1rw1r_80x64_8` macros. One macro holds the 66-bit packed PLIF state and the
other holds the touched-address queue. The clock was constrained to 20 ns (50 MHz).

| metric | post-route result |
| --- | ---: |
| SRAM macros | 2 x 80x64 |
| setup / hold TNS | 0 / 0 ns |
| worst setup / hold slack | 5.009 / 0.449 ns |
| reported minimum period / nominal fmax | 10.277 ns / 97.31 MHz |
| die / core area | 1,679,210 / 1,574,100 um2 |
| SRAM macro area | 363,942 um2 |
| non-filler standard-cell area | 52,935.8 um2 |
| sequential cells | 363 |
| total instance / standard-cell utilization | 26.48% / 4.37% |
| detailed-route DRC / antenna violations | 0 / 0 |
| maximum-slew / fanout / capacitance violations | 0 / 0 / 0 |
| vectorless power estimate | 8.295 mW |
| worst VDD / VSS IR drop | 0.114 / 0.102 mV |

OpenROAD reports every VDD and VSS shape connected, and the merged layout has matching GDS
for every LEF cell with no orphan cells. This closes the actor-tile characterized-SRAM
integration check, not full-model physical implementation. The two shallow macros waste most
rows/bits and cannot be extrapolated into full-chip area. The nominal fmax is an isolated actor
result, and vectorless power is not event-driven inference power. Full-model banking and
capacity require the complete native DSEC activity profile; activity-based power requires
representative checkpoint-derived switching. The Apple-silicon run also skips post-CTS timing
repair because the emulated amd64 binary raises `SIGILL`, so native-x86 rerun is required before
publication-grade timing or power claims.
