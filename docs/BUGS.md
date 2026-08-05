# Bugs

## Resolved — Python 3.9 annotation import failure

- Reproduction: collect `tests/test_sparse_conv.py` under Python 3.9.
- Root cause: runtime evaluation of Python 3.10 `X | Y` annotations.
- Fix: postpone annotations in the sparse reference and keep declared Python 3.9 support.
- Regression: the full Python suite collects and passes under Python 3.9.6.

## Resolved — cocotb simulations used one-second precision

- Reproduction: `make rtl-test` initially failed every nanosecond timer.
- Root cause: RTL files omitted a timescale declaration.
- Fix: declare ``timescale 1ns/1ps`` in every unit and use safe pytest IDs/results paths.
- Regression: all five RTL unit simulations pass under Icarus Verilog 13.0.

## Resolved — signed event accumulation saturated positive

- Reproduction: four additions of signed int8 weight `-3` produced `8388601`.
- Root cause: a concatenated sign extension participated in an unsigned expression.
- Fix: explicitly widen both accumulator and weight into signed 25-bit intermediates.
- Regression: cocotb verifies four additions produce `-12`, then clear produces zero.

## Repository hygiene risk — tracked virtual environment

While this run was active, external commit `070fa2d` appeared and included the initial
`.venv` bootstrap files. `.gitignore` now excludes `.venv/` and future generated files,
but removing already tracked environment files requires a deliberate index cleanup in a
subsequent commit; this run did not rewrite or undo the concurrent commit.

## Resolved — non-static VHDL aggregate rejected by GHDL

- Reproduction: `make rtl-test` during the VHDL migration; four units passed and
  `f_inst_top1.vhd` failed elaboration at its minimum-signed-value aggregate.
- Root cause: the aggregate used a variable-derived index together with `others`, which
  GHDL correctly rejected as a non-locally-static mixed choice.
- Fix: initialize all bits to zero and assign the sign bit explicitly.
- Regression: all five VHDL-2008 entities pass GHDL 6.0.0/cocotb.

## Resolved — MEVDT directory scan disagreed with official split

- Reproduction: directory discovery found 10,132 train labels while the official CSV
  listed 10,067.
- Root cause: extra label files exist outside the published object-detection index.
- Fix: use `MEVDT_org_rate_{train,test}.csv` as the authoritative index.
- Regression: 10,067 train and 2,627 test frames are indexed across 51 and 12 disjoint
  sequences respectively.

## Resolved — surrogate gradient erased by detached threshold mask

- Reproduction: a 32-step MEVDT run changed Conv1 weights by only `4.77e-7`.
- Root cause: with competition disabled, surrogate spikes were multiplied by a detached
  hard-threshold mask, zeroing subthreshold gradients.
- Fix: emit the surrogate spike directly in the `f_inst` ablation path.
- Regression: a unit test checks positive subthreshold gradient; the same 32-step run
  changes Conv1 weights by `0.02015`.

## Resolved — valid MEVDT border box rejected

- Reproduction: label `1581956310656316936.txt` contains x_max
  `240.00000000000003`.
- Root cause: interpolation floating-point noise exceeded the exact 240-pixel bound.
- Fix: clip only boundary error within `1e-6`; larger invalid boxes still fail.
- Regression: all 7,816 indexed train boxes and 2,010 indexed test boxes parse.

## Resolved — relative symlink root broke checkpoint metadata

- Reproduction: training through `data/mevdt` completed updates but failed while making
  absolute label paths relative to the unresolved root.
- Fix: resolve the dataset root once at training entry.
- Regression: the 1,024-step run saved `mevdt_baseline_1024.pt` successfully.

## Superseded architecture — learned objectness did not form useful MEVDT boxes

- Reproduction: the 1,024-step baseline has held-out best-proposal mean IoU `0.06236`
  and recall@0.5 `0.0` on 64 positive frames.
- Diagnosis: connected components are small and fragmented; dense filled-box map loss
  is poorly aligned with sparse event-edge activity and component decoding.
- Resolution: replace filled-box objectness/ROI inference with event-supported pixel
  attention, predicted-attention classification, and centroid tracking. Regression tests
  cover the new mechanics. Real-data quality remains unmeasured until a new checkpoint
  is trained; the old checkpoint was deleted as an incompatible generated artifact.

## Resolved — attention loss made the 50-step target unreachable

- Reproduction: user-run v1 attention checkpoint had recall `0.002084` and only 28.1%
  positive windows emitted attention.
- Root cause: a binary any-time target of 1.0 was compared with mean spike rate, whose
  first nonzero value over 50 steps is 0.02; background loss favored total silence.
- Fix: clamped window-spike presence, sparse-positive balancing, Conv1 support loss,
  variance-scaled initialization, and threshold 0.25.
- Regression: window-presence and sparse-support tests; repaired 1,024-step `f_inst`
  checkpoint measures pixel IoU `0.536611` and 100% centroid detection.

## Resolved — bounded training was biased by dataset order

- Reproduction: the original bounded selector alternated the first positive and negative
  records without shuffling.
- Root cause: official CSV ordering concentrated a bounded run in early sequences.
- Fix: seeded within-class shuffle followed by deterministic balancing; checkpoint stores
  the policy and exact selected records.
- Regression: selection is repeatable, balanced, and differs from prefix order.

## Resolved — f_long vanished on large sparse maps

- Reproduction: one spike on a 90×120 map contributed `1/10800`, less than one adaptation
  decay step.
- Root cause: spatial mean normalization conflicted with sparse per-map homeostasis.
- Fix: per-channel any-spike reduction and threshold-relative increment/decay, serialized
  in checkpoints.
- Regression: a single spike on a large map raises adaptation by the configured increment.

## Resolved — class-level f_inst starved the vehicle output neuron

- Reproduction: train the fully spiking readout for 1,024 balanced samples with `f_inst`
  inherited by the two class LIF neurons. Held-out classification was `0.5234375`; on a
  32-positive diagnostic slice, mean class spikes were `4.0625` for background and
  `0.71875` for vehicle.
- Root cause: spatial backbone competition is useful for feature sparsity, but applying
  winner-take-all inhibition across independent semantic class accumulators suppresses
  the weaker class before the window-level decision.
- Fix: retain `f_inst` in the backbone and make class LIF neurons independent; apply
  competition once through deterministic spike-count argmax after the temporal window.
- Regression: unit tests freeze disabled class `f_inst/f_long`; the repaired 1,024-step
  checkpoint reaches `0.828125` held-out predicted-attention classification and `1.0`
  oracle-attention classification.

## Workaround active - native Windows cocotb/GHDL VPI load failure

- Reproduction: run `make rtl-test` with WinGet GHDL 6.0.0 and the Windows Python 3.11
  environment; VHDL analysis/elaboration succeeds, then GHDL cannot load
  `cocotbvpi_ghdl.dll` (an isolated probe reports a side-by-side configuration error).
- Root cause boundary: the failure is in the native Windows simulator/VPI runtime ABI,
  not in VHDL analysis or the five testbench assertions.
- Workaround: on Windows run `scripts/run_rtl_tests_docker.ps1` (or use
  `make rtl-test-docker` where GNU Make is installed); the repository is mounted
  read-only into a Debian container with GHDL and cocotb.
- Regression: all five simulations pass in Docker with GHDL 2.0.0/cocotb 1.9.2.
- Status: native execution remains unresolved; Docker is the verified RTL path on this
  machine.

## Resolved - seed-sensitive spiking classifier saturated and collapsed to background

- Reproduction: train the fully spiking `f_inst` baseline for 4,096 balanced MEVDT
  samples with seed 101, then evaluate all frozen validation sequences.
- Evidence: attention IoU is `0.735156`, but predicted and oracle-attention
  classification F1 are both `0.0`; no vehicle predictions or tracks are emitted.
- Root cause evidence: matched trace exports show this is saturation, not output silence.
  On positive frames, the failed seed averages `48.125` background and `46.125` vehicle
  spikes over 50 timesteps. Its mean class currents are approximately `5.640` and
  `0.565`, while its peak candidate membranes reach approximately `100.486` and `8.208`
  against a `0.25` threshold. One subtractive reset per timestep cannot drain that
  accumulated current, so both neurons remain near their 50-spike ceiling and background
  wins narrowly. Oracle attention reproduces the failure, excluding the attention head.
- Fix: scale the bias-free classification synaptic current
  by the exactly hardware-mappable power-of-two divisor 32 (five-bit arithmetic shift),
  preserve independent output LIF neurons and spike-count decoding, and retrain seed 101.
- Regression: the repaired 4,096-sample seed-101 checkpoint completed all 10 validation
  sequences with classification F1 `0.929260`, HOTA `0.469137`, and tracking success AUC
  `0.567106`; all three automated gate conditions pass. Preserve
  `mevdt_seed101_4096.pt` as the frozen failed checkpoint.
- Status: resolved. Retain the mandatory loop below as the workflow for any future zero
  core metric.
- Mandatory fix loop:
  1. Reproduce the zero metrics with the frozen checkpoint and complete validation split.
  2. Export per-class synaptic current, peak membrane, threshold crossing, and spike-count
     traces for matched positive and negative samples from seeds 17 and 101.
  3. Add a regression test for the identified saturation/root-cause condition.
  4. Apply the smallest training-side fix that preserves bias-free synapses and
     spike-count inference; do not hide saturation with a different argmax tie rule.
  5. Retrain the failed seed and run complete chronological validation.
  6. Repeat until classification F1, HOTA, and tracking success AUC are all nonzero, then
     continue the unchanged third-seed run and compare all three seeds.
- Automated gate: full `docker compose run --rm eval-mevdt` evaluation uses
  `--require-nonzero-core-metrics` and exits nonzero when any of those three metrics is
  zero, routing the active milestone back to this loop.

## Workaround active - native Windows cocotb/GHDL VPI load failure

- Reproduction: run `make rtl-test` with WinGet GHDL 6.0.0 and the Windows Python 3.11
  environment; VHDL analysis/elaboration succeeds, then GHDL cannot load
  `cocotbvpi_ghdl.dll` (an isolated probe reports a side-by-side configuration error).
- Root cause boundary: the failure is in the native Windows simulator/VPI runtime ABI,
  not in VHDL analysis or the five testbench assertions.
- Workaround: run `make rtl-test-docker`; the repository is mounted read-only into a
  Debian container with GHDL and cocotb.
- Regression: all five simulations pass in Docker with GHDL 2.0.0/cocotb 1.9.2.
- Status: native execution remains unresolved; Docker is the verified RTL path on this
  machine.
