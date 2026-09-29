## Passive SC state-range and full-float mapping challenge — 2026-09-25

The new passive membrane captures signed events cleanly only near VCM. At0.75/1.05V states, a fixed0.9V packet baseline causes sign collapse/inversion; a static packet baseline tied to the initial state restores first-event polarity but still has7–9% gain variation for10µm packets and≈119µV hold drift over4ms, unchanged when the explicit shunt is raised from1e15Ω to1e18Ω. A full-float trace sensitivity using ideal continuous packet-amplitude control, linear measured slopes and a0.18µV per-event floor gives final_fuse spike mismatch1.283% for10µm packets at0.30V candidate headroom (stem0.081%, enc1 0.308%). It does not include nonlinear state-range transfer, physical DAC noise, mismatch, PVT or comparator kick, so this is optimistic and fails the provisional final-stage0.1% budget. A2.5µs packet-service assumption yields sampled p99 90/222.5/790µs across stem/enc1/final_fuse patches, but is not a full-population throughput result. Next test a live membrane-following packet baseline or direct signed analog current injection, then retry actual float replay; passive candidate and layout remain unaccepted. See `docs/RESULTS.md`.

## Passive switched-capacitor membrane candidate — 2026-09-25

Debugging isolated the physical OTA integrator's reconnect transient as the dominant event error: waking its OTA moves state by ~6mV and is barely changed by packet adjustment from50mV to53.5mV; leaving both OTAs continuously on drifts by −2.62mV over5ms. A passive 100µm MIM membrane plus 1µm packet capacitor and physical TGs, with no OTA during accumulation, gives ±5.6µV for ±50mV packet steps. `pn` and `np` both return to0.8999949V within0.1µV reported precision; the first contribution drifts by0.0–0.1µV across the next~4ms. The passive path is linear at5.6/16.8/33.6µV per event for ±50/±150/±300mV on1µm packet caps. Three-micrometre caps give≈268µV but have a1.0µV `pn`/`np` residual;10µm caps give≈2.9mV but show≈28µV packet variation and2.4µV hold shift. Physical R2R24 code3060 initializes a passive threshold reference through TGs to−11.0µV signal-minus-reference, stable through4.9ms; ±300mV `pn`/`np` trials end0.014/0.114µV from the−10.914µV float target. This is nominal TT only, with no comparator/readback, actual full-float weight replay, mismatch/noise/PVT or extraction. Next map the full-float event weights onto the passive transfer, then integrate/measure threshold decision and read disturbance. Details: `docs/RESULTS.md`.

# Progress

## Full-float threshold initialization and ABBA membrane readout — 2026-09-25

Integrated the full-float median threshold offset (+10.914µV at0.30V headroom) with the physical SKY130 SC membrane. A testbench audit invalidated the early code3243 result because the intended offset remained in `.ic` and one cell edit was appended too late. The corrected no-event test uses no threshold `.ic`, VCM signal initialization, and a separate threshold DAC. Code2711 retains−10.831µV signal-minus-reference through5ms (83nV state difference); ABBA input-equivalent error is−0.078µV and read disturbance−0.033µV. With matched OTA phase timing and corrected pulse polarity, equal-packet `pp`/`nn` cases end at+1.191/−20.878µV; mixed `pn`/`np` end at−10.216/−9.486µV. Their0.730µV order difference and sign-asymmetric charge exceed the sampled ~0.18µV q0.1 threshold margin. Nominal TT,50ns schematic evidence only; full-float weight replay, noise, mismatch, PVT, threshold spread and extracted layout remain open. Next tune signed packet charge/order effects, then replay actual full-float membrane/spike traces. Details and reports: `docs/RESULTS.md`.

## Analog readout follow-up — 2026-09-25

Passive SKY130 MIM sampling was screened at 1/10/30µm and rejected as the preferred low-noise readout: estimated kT/C is 1.32mV/142.6µV/47.8µV RMS, respectively, versus ~55–64µV packet signals; 10µm bottom-plate sampling itself adds 2.5–3.9µV differential disturbance, while the 30µm case adds 8.1µV and requires an offline event/no-event subtraction to remove output offset. The 30µm `pp` differential transfer matched the baseline-subtracted state change within 0.14µV nominal TT, but there is no physical baseline circuit or transient-noise result. The existing OTA directly senses ±64µV with about ∓0.31V output movement (≈5,000V/V) and is already near rails by ±250µV, so open-loop direct readout is not linear enough. The selected next step is an active closed-loop or time-integrating OTA differential readout with gain matched to the full-float state range, followed by offset/noise/corner work. Evidence and scope are documented in `docs/RESULTS.md` and `docs/ACTIVE_TASKS.md`.

## Analog weight-delivery review — 2026-09-24

Retained signed charge per incoming event. The primary reference is the best-validation full-float checkpoint (epoch 58 of 80), with verified SHA-256; epoch 80 is only a non-best comparison. Exported executed float synapse/neuron arrays and traced real-DSEC samples without QAT, quantization or decoded fixed-point weights. The pulse-duration sensitivity screen uses already-folded effective float weights and maps each layer's largest effective weight to the maximum tested TT pulse. Optimistic serial fan-in replay over three real convolution traces predicts 0.19ms/6.58ms/15.94ms median service per active destination in stem/enc1/final_fuse, before setup; 61.6% and 77.6% of active enc1/final-fuse destinations exceed 5ms. Serial pulse delivery therefore misses the preliminary throughput screen. Direct packet-cap sharing varies 3.0–4.6× over 0.75–1.05V and is rejected. The transistor-level virtual-summing-node candidate, with corrected MIM differential initial conditions, delivers 32.8/296/3095µV positive and 48.3/307/3105µV negative through 1/3/10µm packet caps. State variation is under 1.84%; the 1µm point has ~47% polarity gain mismatch. A two-event screen with explicit isolated packet-cap reset is within 27.14µV of independent packet sums; P→N/N→P differs by 0.268µV. A provisional 2.5µs per-packet service estimate from sampled real fan-in yields 10–925µs p50-to-max across stem/enc1/final-fuse outputs, with none above 5ms in these three patches; weight-cap selection, true repeating cycle and whole-chip scheduling are excluded. The 0.3V final-fuse headroom sensitivity gives a ~10.9µV threshold and ~0.18µV q0.1% threshold margin; a uniform 1µV shift changes 0.28–0.29% of sampled final-fuse spike bits. This demands a precision/noise study; it is not a measured noise result. Physical reset/init and float-model spike equivalence remain untested. The float model uses subtractive reset; hard reset-to-VCM differs on 1.64% of sampled final-stage spike bits. A per-start-state quadratic reset calibration passes nine held-out steps at three start voltages (max relative error 0.0152%) assuming the start state is known. Existing restore/ADC and population-throughput blockers remain. No layout or digital/XL restart.


## SKY130 Q7.16 restore/mux and SAR controller — 2026-09-23

Current source uses the 24-bit R-2R offset-binary restore DAC and signed Q7.16 digital storage. With the generated ideal 1k/2k ladder, Docker restore/mux smoke now passes coarse range, tested monotonicity, and A→B→A after a uniform +12,544-code offset plus +2.553424mV DAC rail shift. Center error is 46µV; largest tested error is 2.863mV = 938.05 Q7.16 voltage LSB, so half-LSB precision remains unqualified. Applying the code offset only to nonnegative values caused the earlier zero discontinuity; the SAR RTL decode now subtracts the uniform offset but remains ideal-comparator only. Regenerated weight-magnitude voltage transfer passes the coarse screen; direct R-2R/MOS current injection fails. A new `synapse_pulse_width_mos` is integrated in `analog_plif_channel_pulse_duration` and passes a bounded SKY130 PDK MIM transient screen across 0.05–4µs with 7× positive duration scaling, 0.957 positive/negative gain ratio, and ≤0.36% slope deviation. A separate 5ms hold check shows 15–18µV drift with leak disabled. This remains a TT schematic candidate without Q7.16 mapping, mismatch/PVT, extracted layout, event-multiplicity, or scale feasibility evidence. See the restore, current-DAC, pulse-width, and retention JSON reports under `artifacts/analog_asic/results/`.

Added synthesizable `sky130_ms_sar24_writeback` plus `sky130_ms_slot_controller` in `asic/analog/sky130_ms_slot_controller.sv`. Bounded Docker Icarus smoke checks zero/mid/full-scale conversion, 24 sequential comparison decisions per code, expected Q7.16 endpoints, phase coverage, and no phase overlap. Comparator behavior is an ideal code-level testbench, not integrated transistor-level SAR evidence. The population throughput lower bound is 743,424,000 SAR comparisons per 5ms update; at 100MHz that needs at least 1,487 lanes before analog setup/leak and routing overhead. Do not claim one/few-channel full-population feasibility.

## Digital ORFS stopped — mixed-signal only — 2026-09-23

User directed: proceed with mixed-signal only; stop and remove digital ORFS runs. Killed host `_run_one_140k_hard_macro_orfs.py` workers, `docker stop/rm` of `eventspikeseg-hm-*`, journal running stem masters → `paused`, `campaign_status=stopped_user_mixed_signal_only`. Counts: 18 complete / 128 OOM / 2 paused. Digital artifacts preserved (no GDS/LEF/RTL deletion). Evidence: `artifacts/ASIC/digital_stop_20260923/`.

## SKY130 weight DAC + β↔leak mapping — 2026-09-23

β/leak mapping remains the prior schematic result: β=0.35/0.60/0.90 via `t_leak=-τ ln(β)`. The old combined script's 4-bit injector path was stale and no longer runs; its weight check delegates to the Q7.16 coarse DAC transfer test. A separate MOS injector operating-point screen now exercises both polarities, and fails due to dead low-code response and asymmetric current. No injection accuracy, mismatch, extracted layout, or PPA claim.

## SKY130 mixed-signal analog PLIF channel — 2026-09-23

Prototyped mixed-signal PLIF on SKY130 (MIM membrane, MOS synaptic current, MOS leak, MOS comparator) with digital membrane codes / routing. This representative channel is not yet a population-scale architecture: 24-bit SAR throughput requires at least 1,487 concurrent lanes at 100MHz before analog overhead. ASAP7 analog storage remains rejected; ASAP7 digital ORFS stopped/preserved (not running).

Docker `python scripts/test_sky130_analog_plif.py` → `channel_smoke_pass=true`:
- inject then 5ms MIM hold (drift ≈−0.65mV)
- MOS leak moves state toward vcm
- capture/compare asserts spike above theta

Sources: `asic/analog/sky130_ms_plif.spice`, results `artifacts/analog_asic/results/sky130_ms_plif_screen.json`. Next: programmable weight bias, beta↔leak mapping, digital restore/glue.

## ASAP7 MOSCAP bounded qualification — 2026-09-23

After correcting D-G-S-B wiring and leakage-subtracted Ceff analysis, the complete small-count Docker rerun (`python scripts/test_asap7_mos_storage.py --only all`) completed all three benches. Four-finger C-V median is 0.27035 fF total (0.06759 fF/finger). Eight-finger write/drain/rewrite passes its bounded voltage checks. Eight-finger MOSCAP retention from 0.41969 V to 0.22255 V over 5.002 ms drifts −0.19714 V (−2.816 model units), failing the provisional 0.02-unit limit by a wide margin. Therefore `accepted_as_option_b_candidate=false`; drain/adjust success does not qualify storage. No sizing, layout or ORFS work is authorized by this result. Next work is to diagnose/redesign the storage and hold path, then repeat multi-condition 5 ms validation before scaling. Evidence: `artifacts/analog_asic/asap7/capacitor_qualification.json`, `results/mos_storage_checks.json`, and the three bench logs/traces.

### Retention isolation follow-up

`python scripts/diagnose_asap7_mos_retention.py` ran bounded Docker controls with the same transmission-gate stimulus. The sub-fF ideal-cap control (8× measured nMOS per-finger Ceff) drifted −0.2260 V; 1pF and 20pF ideal controls drifted −0.01514 V and −0.000804 V respectively. Eight- and 32-finger nMOS Cgg drifted −0.17675 V and −0.13992 V. An 8-finger pMOS Cgg cell improved drift to −0.01094 V (−0.156 model units), still 7.8× beyond the ±0.02-unit smoke gate; 32- and 128-finger pMOS arrays drifted +0.04154 V and +0.15020 V. Rail current on the common-mode/reference rail is in `results/mos_retention_diagnosis.json`; these are schematic diagnostics, not a physical design. Floating-node runs are invalid controls because ngspice initialized the state near 0.77 V rather than the requested 0.42 V. No tested ASAP7 MOS Cgg option qualifies. Continue analog-only debugging; digital/XL stay paused unless the user explicitly requests a switch. A later pMOS interior-bias trace that appeared stable at one endpoint was an input-dependent attracting equilibrium, not retention: high initial states drifted 68–145mV in adversarial cases. The DC bias map found minimum pMOS storage clamp current 6.787pA at stored 0.28V, versus an approximate 0.328fA budget for 1.17fF and 1.4mV/5ms. Direct OSDI `IGTOT` at 0.28V measured −0.9265pA for one pMOS instance (≈−7.412pA for eight), confirming modeled gate current as the dominant low-state branch rather than current-print quantization. A bounded low-common-mode nMOS-only screen used state 0.08/0.15/0.22V, eight NFIN=3 storage instances tied D/S/B=0, and one nMOS access path. Standalone AC admittance measured Cdiff=0.5415/0.5439/0.5756fF; summed intrinsic gate leakage corresponds to 0.124/0.413/0.822V/s, passing the provisional 0.28V/s rate only at the lowest state. The six state/input DC combinations also include access-current cases exceeding the rate limit (worst ≈4.03V/s). This low-common-mode diagnostic is not the project PLIF encoding and is not a hold-cell pass. The open ASAP7 files/survey contain no discrete MIM/MOM device model or PCell; do not invent a capacitor model or physical density. Readiness correctly remains false with `capacitor_qualification_candidate_not_accepted`. Diagnostic artifacts: `results/low_common_mode_nmos_only_dc.log`, `results/nmos_cap_standalone_ac_*.dat`, `results/mos_cap_igtot_bias_survey.json`, and `results/mos_off_bias_reachability.json`.

## Stage 2 model-to-circuit contracts — 2026-09-23

Froze EventSpikeSeg140k ASAP7 analog interface contracts without restarting digital/XL ORFS or claiming physical PLIF readiness. Inspected HardwareLIF forward order (advance adaptation age → charge → threshold → subtractive reset → peer inhibition → adaptation refresh → beta once under ASIC-QAT), `model_spec.yaml` quantization tables, 25 parameter files, and 143,824 Q7.16 weights.

Export ranges (quantized, not float checkpoint): beta 0.323..0.975 (UQ1.23); threshold 0.286..0.766 (Q7.16); stem inhibition strength ≈0.0142; 15 adaptation layers strength ≈0.0116..0.0137 and duration ≈4.83..5.22 bins; weight float decode min/max ≈−63.4..+68.4 (final_fuse absmax largest). Encoding: VDD=0.7 V, vcm=0.35 V, smoke volts/state=0.07 (prototype only); capacitor options 1/10/20 pF under consideration with prior ideal retention notes. Acceptance: 0.02 is smoke-only; module criteria and workload accuracy separated. Behavioral placeholders itemized under `pending_physical` (logistic compare, finite-gm sense, ideal C, B-source synapses, etc.).

Artifacts: `artifacts/analog_asic/design.yaml` (circuit_contract/asap7_encoding/pending_physical), `asap7/circuit_contract.json`, `asap7/parameter_ranges.json`, `asap7/weight_ranges.json`, `asap7/stimuli/*`. Generator: `scripts/export_analog_stage2_contracts.py`. Stage 3 next.


## Full analog implementation delegation — 2026-09-23

The user now authorizes Grok to perform the full ASAP7 analog/mixed-signal workflow, including design, debug, per-module simulation, physical macro generation, full assembly and ORFS execution once readiness passes. `docs/ACTIVE_TASKS.md` is the authoritative staged task plan. Earlier Grok-test-only and blanket no-ORFS instructions are superseded. Keep digital/XL jobs paused and all artifacts preserved. Use existing docs and YAML only. Approximate research estimates are allowed with explicit evidence/coverage; full layout still requires real implemented macros and validated assembly.

The accepted starting point was refreshed from the current files: sampled_plif_external completes 80us, spike sequence passes and maximum provisional state error is 0.008970758. It uses a logistic comparator/captured decision and behavioral driver; the transistor comparator and physical macro views remain incomplete. No simulation or layout campaign was launched during this documentation handoff. The nine-stage plan covers circuit completion, capacitor qualification, all module families, extraction/PPA, assembly, readiness, full ORFS and final estimates.


## ASAP7 open-source bring-up update — 2026-09-23

ngspice 45.2 was built from official tag 45.2 (724dc77b9153dc75eaec474b1f7a44f1fcf5f362) with OSDI. Berkeley original BSIM-CMG 107.0.0 was downloaded from https://www.bsim.berkeley.edu/BSIMCMG/BSIMCMG107.0.0_20130712.tar.gz and compiled using OpenVAF 23.5.0. UC Berkeley copyright/license notices are retained; acknowledge UC Berkeley for this model implementation. This supersedes the earlier inference that only model111 was available. No commercial simulator/license was needed for basic device checks.

ASAP7 TT/SS/FF physical card parameters are preserved in generated OSDI syntax; NFIN=3 is the declared smoke geometry. Model selector/version metadata are adapted to the compiled 107 implementation. EOTACC's validation bound was widened from [0.1n:inf) to (0:inf) because the compiled original rejects ASAP7's 1e-10 value at that bound; equations and numerical card values are unchanged. This adaptation is documented in model_source_changes.json and is not HSPICE cross-validation.

Accepted TT checks: DC inverter transfer and transient switching. Five-millisecond retention tests with ideal external clocks and capacitors complete: 1pF drifts 15.149mV (0.2164 normalized units), 10pF 1.590mV (0.02271), 20pF 0.805mV (0.01149). Only 20pF meets the provisional 0.02-unit smoke limit for this one stimulus. This is not a chosen physical capacitor, general accuracy guarantee or layout area estimate. Dielectric leakage, mismatch and extracted parasitics are absent.

Codex 2026-09-23: finite-gm tanh sense, continuous logistic `Btarget`, 50ns phase edges, and an ASAP7-only continuous compare path keep `sampled_plif_external` through 80us. Soft k=50 compare left spike midrail on bin-3 (~0.55mV overdrive), so θ was only partly subtracted at commit and state error cascaded. Replaced with scale-normalized logistic (k=2000 on model units) plus capture-gated track-hold. Provisional smoke now passes: `spike_sequence_pass=true`, `max_state_error≈0.009`. SKY130 sampled_plif still passes (`max_state_error≈0.011`). MOSFET compare at 0.7V with capture-edge regeneration remains open. No ORFS launch. Digital/XL remain stopped.

Reproduce: python scripts/build_asap7_analog_modules.py ; python scripts/test_asap7_analog.py .


## ASAP7 analog readiness — 2026-09-23

The user requested ASAP7 and eventual full ORFS preparation. The complete PDK has now been fetched and pinned: umbrella d24f8b857ff74cf5b21ab18a7e1b11a3954c449b, device PDK 58d72c9d291e186a77468586ab0c43d8a21eda6a. Its unmodified TT card declares HSPICE level 72, BSIM-CMG version 107. A one-inverter probe fails in installed ngspice 36 with unsupported model level; no ASAP7 transistor result is accepted. Host/WSL/container checks found no HSPICE, Calibre, Xyce or OpenVAF.

An open-source path exists through ngspice >=39 OSDI/OpenVAF, but the currently inspected VA-Models tree supplies BSIM-CMG 111.2.1, not the original 107 card's model version. Do not silently change the model level/version or drop unsupported parameters and call it validated ASAP7. Establish a compatible model implementation/parameter mapping and benchmark before analog PPA claims. User tool-access clarification is pending; commercial tools are not assumed available.

The PDK's Calibre DRC/LVS/PEX directories contain download instructions rather than the rule decks. A physically qualified capacitor, completed analog macro netlists/layouts, LEF/Liberty views, extraction evidence and a conserving full-model assembly remain missing. ORFS accepts hardened macro views; it does not synthesize the behavioral SPICE library into analog layouts. Full ORFS is NOT ready, and no launch command is advertised as ready. Check: `python scripts/check_asap7_analog_ready.py` (expected exit 2 and explicit missing prerequisites). Evidence: artifacts/analog_asic/asap7/readiness.json and results/device_probe.log. The check is intentionally read-only with respect to physical campaigns and cannot launch a placeholder chip.

Preserve the SKY130 prototype as a separate experiment and all digital checkpoints. No extra Markdown documents were created. Next: resolve tool/model path, implement and qualify ASAP7 analog macros, then prepare/validate the ORFS assembly. Do not route empty boxes or use SKY130 physical views on ASAP7.

Sources: https://ngspice.sourceforge.io/osdi.html ; https://github.com/The-OpenROAD-Project/asap7 ; https://openroad-flow-scripts.readthedocs.io/en/latest/user/FlowVariables.html .


## Analog module implementation update — 2026-09-23

Codex is the design owner; Grok is test/debug only. Initial module library in asic/analog/modules.spice now covers sampled PLIF, membrane hold, signed synapse, leak target, threshold/subtractive reset, square/root energy, triangular adaptation, peer inhibition, class integration and argmax, plus CMOS primitives. The design YAML binds roles and learned exported constants to all 25 actors. It is a mixed-level prototype: only switches/inverters/comparator use actual SKY130 transistor models; behavioral components are not physically implemented or power-complete.

Five bounded ngspice benches pass. The first integrated PLIF attempt exposed destructive charge sharing between state and snapshot capacitors. A labelled ideal isolation buffer fixes functional charge transfer; its transistor implementation remains required. Eight-bin maximum state error is 0.004235 model units with a provisional 0.02 smoke tolerance, not an accuracy target. Two capacitors plus a buffer are currently required by this prototype; do not count it as one bare capacitor per neuron.

Comparator stimulus mean VDD power is 1.48973 uW over 5 us, at SKY130 TT and 1.8 V. This excludes bias/reference generation and layout parasitics; do not scale it as whole-model or whole-PLIF power. All other behavioral modules retain unknown physical power/area/latency. Result evidence: artifacts/analog_asic/results/test_results.json and per-bench logs/traces. No physical analog layout, DRC/LVS, extracted PPA, 5 ms retention test or whole-model accuracy validation exists.

Models: https://github.com/google/skywater-pdk-libs-sky130_fd_pr at f62031a1be9aefe902d6d54cddd6f59b57627436; preserved upstream files/licenses. SKY130 is a feasibility choice, distinct from digital ASAP7; cross-technology numbers are not direct architecture comparisons.


## Active approach override — 2026-09-23

User authorized analog/mixed-signal 140k feasibility as the active approach. Follow docs/ARCHITECTURE.md and write outputs to artifacts/analog_asic. Digital-only/register-state rules below now describe the preserved digital fallback, not restrictions on this analog experiment. Analog approximations and scaled estimates are allowed with explicit limitations; distinguish ideal, schematic, extracted and full-chip evidence. Preserve all digital/XL artifacts and keep their jobs paused. Prior active work is in docs/PROGRESS.md.


## 2026-09-22 — Bounded 140k mechanism checks (complete)

- Reused existing inhibition/adaptation physical checkpoints and existing block directories. No whole-model simulation, new synthesis, or rerouting was performed. The 120-second per-stage limit was not increased.
- Accepted 9/9 activity cases with zero unannotated pins. Six cases use 64 midpoint samples; inhibition/energy64/energy128 completed as 16/8/4-sample smoke proxies after 64-sample timeouts. Those three plus penalty_lane use global-route estimated parasitics; five adaptation cases use detailed-route parasitics.
- Mechanism-only scaled proxies: 0.010328 W dynamic and 41.909 W leakage at 200 bins/s. The short-sample energies are especially uncertain and are not full-chip power.
- Exact hierarchy inventory conserved: 25 actors, 54 edges, 30,976,000 PLIFs, 1,579,600 physical instances, 160 masters with RTL generated. First exact actor master routed: corner `detail_stem` 1x1 (3/480 views; +3473 ps setup, 654.9 MHz fmax, 3434.3 um² cells).
- Report: `artifacts/ASIC/primitive_characterization/base_140k_inventory/GATE_RESULTS.md`.

> Current scope (2026-09-21): EventSpikeSeg140k epoch-80 seed-17 is the primary ASIC layout/simulation/estimate target. Useful XL layouts and reports are preserved for secondary work; XL figures are not 140k evidence. See [target policy](AGENTS.md#current-asic-target-policy--2026-09-21). Older entries are historical where superseded.

## 2026-09-21 — Simple layout/block-simulation milestone (latest)

User requested small steps, storage cleanup, and reuse of layouts for per-block simulation/power rather than prolonged full-model simulation and repeated physical retries.

- Removed 16.44 GiB of redundant OpenROAD database checkpoints and compiled simulation executables. Final views, all reports, latest unfinished-run databases, source RTL and training/checkpoint data are preserved; deletion manifests are under `artifacts/ASIC/`.
- Reused the 140k ordinary-PLIF and conv9 final layouts. Post-route functional gate simulations passed 65 and 255 output-snapshot checks; extracted-SPEF power has zero unannotated pins for both.
- Current compact results: `artifacts/ASIC/primitive_characterization/base_140k_inventory/GATE_RESULTS.md` and `gate_results.json`. These supersede the corresponding input-only power measurements for this workload, not all other blocks or the entire model.
- Prior PLIF annotation covered 116 pins with 12,869 unannotated; the old 2.013376 W subtotal must not be presented as validated full-chip power.
- Full 25-actor layout remains incomplete. Existing GDS files are isolated blocks. Readout now passes 49 gate-level reference checks after correcting pre-edge versus post-edge testbench sampling. Its existing layout supplied extracted power; 45,229 pins have VCD activity and only the two verified-zero coordinate outputs are unannotated. RTL and physical files were unchanged.
- XL training was observed running in `eventspikeseg-train-dsec-xl-run-0abd58c1b591` and was not interrupted. No ASIC container remains running from this milestone.

## Working now

- 2026-09-21: whole-model simulation and replay are retired for both 140k and XL.
  Their executors, generated RTL/profile artifacts, checkpoint-purpose simulation
  export, and activity-derived whole-model estimate were removed. Historical entries
  below are retained only as an audit record and do not identify available artifacts
  or an approved workflow. Current simulation is isolated per block; full-model work
  is layout/hierarchy, with power assembled from exact instance counts.
- 2026-09-21: the checkpoint-exact one-pixel 16-to-6 temporal readout completed
  ASAP7 route/extraction and VCD activity power. Adding its exact 281,600-pixel
  multiplication changes the current covered 140k dynamic subtotal to 1.922314 W;
  inhibition and adaptation mechanism blocks remain uncovered.
- 2026-09-21: the exact 32-channel stem-inhibition group closed synthesis,
  placement, timing, and congestion-free global routing with zero TNS. Its
  checkpoint-derived 128-vector VCD power multiplied over 70,400 groups adds
  0.091062 W, raising the covered subtotal to 2.013376 W. Detailed route exceeded
  the bounded 12 GiB limit, so this result is labeled global-route power.

- 2026-09-20: the primary ASIC implementation target is the canonical six-class
  `EventSpikeSeg140k` v8 epoch-80 seed-17 checkpoint. XL physical work is retained
  as reference but paused.
- checkpoint-exact isolated ordinary-PLIF and real `detail_stem` 3x3-kernel
  primitives completed ASAP7 route/extraction with zero flow errors and zero
  setup/hold TNS; VCD annotation produced 496.166227 pJ per ordinary PLIF bin and
  0.207547 pJ per dense synapse-term evaluation under their synthetic traces;
- the exact base inventory is 25 actors, 54 graph edges, 30,976,000 PLIF state
  identities, 3,730,918,400 actor terms and 27,033,600 readout terms per dense bin;
  the current measured dynamic subtotal is 1.916467 W at 20 fps and ten bins, with
  the documented mechanism/interconnect/clock/activity exclusions;
- results are generated by `scripts/inventory_140k_physical_primitives.py` under
  `artifacts/ASIC/primitive_characterization/base_140k_inventory/`; full-chip
  floorplanning, routing, extraction, and power remain pending.

- XL training continues at 979,179 registered parameters for eleven classes; epoch 1 now
  supplies a structural ASIC export and generated 44-actor RTL bring-up target, but no final
  QAT accuracy or synthesis result is claimed
- active DSEC target merged from eleven source labels into six broad semantic classes
- manifest-backed DDD17 temporal loading: consecutive two-channel histogram bins or six-channel windows
- `model.py` exposes dual ASIC targets: baseline `EventSpikeSeg140k` and expanded `EventSpikeSegXL`
- frozen completed ten-model structural benchmark in `top_ten_models.py`
- completed structural top-five registry in `top_five_models.py`
- completed/frozen accuracy-oriented top-three registry in `top_three_models.py`
- PLIF with learnable beta and base thresholds
- local triangular threshold adaptation
- stem-only peer-membrane inhibition
- native 440x640 DSEC input with learned stride-2 semantic stem
- 8-channel native detail path and memory-bounded 32/64/128 semantic path
- continuous temporal class-current readout after binary-spiking hidden features
- equal-per-present-class macro CE/focal without static class weights in every suite
- ordinary-sized checkpoints without captured membrane/adaptation runtime tensors
- explicit 3- or 4-stage channel schedules
- configurable stem and first-block kernel size
- dynamic `enc4_spikes` activity/evaluation diagnostics for the deep contender
- active 140k resident RTL now uses one signed int32 Q15.16 combined accumulator/state per PLIF
  and signed int24 Q7.16 weights; clocked adaptation uses 6-bit integer-bin age plus
  19-bit Q3.16 amplitude
- XL exporter/topology/RTL support now covers 44 PLIF actors, 11-class readout, projected
  bridges, three-branch context, and fully-spiking four-head Q/K-coincidence V-gating attention

## Completed evidence

### 2026-09-07 combined-state implementation

- changed ordinary and retinotopic resident PLIF RTL from separate int24 current plus int16
  membrane arrays to one signed int32 Q15.16 accumulator that is thresholded/reset at completion and
  pre-leaked for the next fixed 5 ms bin;
- reduced adaptation age from 16-bit Q10 to a lossless 6-bit integer-bin counter; the
  accuracy-first formats retain 16 fractional bits using 19-bit Q3.16 amplitude/strength and
  21-bit Q5.16 duration, with 24-bit Q7.16 weights/membrane/threshold and 24-bit UQ1.23 beta;
- inspected the completed epoch-80 140k checkpoint: 15 enabled populations have learned
  duration 4.82625..5.22349 bins and strength 0.185593..0.219574; no XL checkpoint exists yet;
- updated export, capacity, tile-planning, top-generation, and integer-reference contracts;
  the new 140k logical state is 150.89 MiB-equivalent, while a future XL mapping calculates
  to 347.66 MiB-equivalent and remains outside the active export target;
- added a common final-model QAT phase: by default the last three epochs of both 140k and XL
  retain FP32 master parameters and gradients while every deployed forward operation uses the
  ASIC fixed-point grids; best-checkpoint selection restarts at QAT entry so the exported best
  is selected by deployment-precision validation rather than an earlier FP32 score; the QAT
  phase explicitly unfreezes the semantic backbone and PLIF/mechanism parameters;
- validation passes: 83 focused Python/generated-RTL tests, all 107 Python tests, Ruff on every
  changed Python file, and all 47 cocotb RTL tests (one non-functional cocotb runner API warning).

### Historical structural incumbent

`v10_fpga_hybrid`: mIoU 0.3130, pixel accuracy 0.7871, 44,016 parameters, output spike rate 0.1412 under the full round-one protocol.

### Latest neuron-mechanism screen

Protocol: seed 17, 5 epochs, 256 train, 128 held-out, 64×64, 8 internal timesteps.

| architecture | mIoU | pixel accuracy | spike rate |
| --- | ---: | ---: | ---: |
| `f05_v02_light_peer_membrane_inhibition` | 0.1991 | 0.7607 | 0.0616 |
| `f02_v10_plif_threshold_adaptation` | 0.1459 | 0.7395 | 0.0470 |
| `f01_v10_plif_threshold_wta` | 0.1402 | 0.7334 | 0.0457 |
| `f04_v03_dilated_threshold_adaptation` | 0.1366 | 0.7217 | 0.0513 |
| `f03_v10_plif_winner_peer_inhibition` | 0.1233 | 0.7384 | 0.0415 |

Selected mechanism base: PLIF + learnable threshold + stem peer-membrane inhibition + encoder triangular threshold adaptation.

## Completed structural top five

Protocol: seed 17, 8 epochs, 2,048 train, 512 held-out, 64×64, 15 timesteps, batch 14, LR 0.002.

| architecture | mIoU | parameters | useful evidence |
| --- | ---: | ---: | --- |
| `f05_compact16_dilated` | **0.2596** | **21,491** | best overall/efficiency |
| `f02_wide32_multiscale` | 0.2284 | 77,751 | best object IoU in round |
| `f04_deep4_dilated` | 0.2079 | 107,131 | strongest aggregate rare-class signal |
| `f01_base24_multiscale` | 0.1626 | 46,423 | weak controlled baseline |
| `f03_early5x5_multiscale` | 0.1482 | 49,111 | early 5×5 rejected |

None beat the 0.3130 historical result under the then-current repeated-static input protocol. The architecture evidence remains useful, but those mIoU values are not direct baselines for the current temporal input protocol.

## Completed accuracy top three

- `t02_dualpath_detail` — **0.2728 mIoU**, 24,211 params; winner and evidence for a persistent high-resolution spiking detail stream.
- `t01_spike_pyramid_concat` — 0.1671 mIoU, 63,147 params; parallel multiscale concat did not recover accuracy.
- `t03_deep_attention_fpn` — 0.1555 mIoU, 108,781 params; extra depth/attention collapsed predictions toward dominant classes.

## Canonical native-resolution candidate implemented

- native 2→8 standard-convolution PLIF detail stem and 8-channel detail refinement;
- learned standard 5×5 stride-2 2→32 PLIF semantic stem before spatial reduction;
- standard 32-channel early feature block and standard stride-2 32→64 transition;
- 32/64/128 semantic path with deeper residual DW/PW refinement and dilation-2 context;
- additive quarter/half encoder skips and late semantic32/detail8 concatenation;
- concatenative quarter-scale 128->64 standard 1x1 PLIF fusion;
- multiplicity-preserving half-scale spike skip;
- standard 3x3 40->16 native semantic/detail fusion before one PLIF threshold;
- continuous 16→11 temporal class-current readout rather than a ten-level class-spike count;
- training-only quarter-scale semantic auxiliary head and native boundary head;
- SpikingJelly `Conv2d`/PLIF/surrogate infrastructure where compatible, with project-specific per-channel beta, peer inhibition, threshold adaptation, and operation order preserved;
- canonical-only 70/20/10 joint → backbone-frozen refinement → low-LR joint-unfreeze schedule;
- exact 10-way replay in the DSEC compose service so each backward replay holds one 5 ms update.

## Validation/cleanup state

- all architecture suites now dispatch through `train.py`; the duplicate standalone top-three trainer is retired;
- every suite uses macro per-present-class CE (and macro focal where configured); static class-weight estimation is removed from training;
- the generated `ddd17_temporal_manifest.json` is the required chronology source; the runtime neither generates it nor infers sequence boundaries from filenames;
- `timestamp-events` is the sole input representation; HDF5/raw and multi-file window paths are removed;
- one 50 ms record is scheduled over ten 5 ms input clocks and PLIF state persists across consecutive records;
- final best-checkpoint selection uses whole held-out sequences when available, otherwise one contiguous block;
- checkpoints fingerprint the manifest/split/physical-clock protocol and reject all older input protocols;
- auxiliary heads are skipped in evaluation/inference;
- native-resolution checkpoints are supported by `evaluate.py` when `output_size` is `None`;
- single-sequence contiguous validation and exact checkpoint holdout reconstruction are covered by regression tests; limited per-epoch training preserves temporal order;
- obsolete `benchmark_top_three.py`, MEVDT/EventSCNN scripts, the dead `rtl-test` PowerShell wrapper, and checked-in `.ruff_cache` were removed; the completed DDD17 architecture-search plan is archived under `docs/exec-plans/completed/`.

## Open issues

- rare-class IoU remains the dominant accuracy limitation;
- the completed top-three hypotheses are measured only under the removed repeated-static protocol; the scaled canonical candidate has not yet been measured under the current temporal protocol;
- the installed training data is incomplete: 2,887 event tensors versus 10,001 masks, leaving only one event recording usable;
- with an 11-class DSEC head, XL registers 237,115 parameters and executes 226,767 at inference;
- learned continuous neuron dynamics and learned attention thresholds remain unquantized;
- the native-resolution v7 140k checkpoint has not yet completed a training epoch, so its 50% target remains unmeasured.

## Next action

Run the native 440x640 11-class `EventSpikeSeg140k` configuration from scratch. Verify
that loss, gradients, class prediction shares, and rare-class IoUs move during epoch 1
before committing to the full 80 epochs. Then validate its revised fixed-point export.

## 2026-08-23 — native-resolution accuracy revision

- retained the public `EventSpikeSeg140k` FPGA target and checkpoint directory;
- changed DSEC training geometry from 241x351 to native 440x640;
- added an 8-channel native detail route and learned 5x5 stride-2 semantic stem;
- changed the early 32-channel block and 32->64 downsample to standard convolution;
- moved the semantic bottleneck to 55x80, preserving a three-level 32/64/128 hierarchy;
- replaced the spiking class head with continuous temporal class-current accumulation;
- added a training-only native boundary objective at coefficient 0.1;
- set DSEC replay chunks to 10 so each gradient replay retains only one update graph;
- revised FPGA export to 25 PLIF actors plus one current readout;
- revised state accounting to 30,976,000 membranes and 10,982,400 adaptation states.

## 2026-08-15 timestamp-stream v3

- one dataset item is one 50 ms NumPy interval and its same-record indexed mask;
- stored `hist0,hist1,mean0,std0,mean1,std1` is decoded into per-polarity activity/mean/std;
- mean and mean±std schedule conserved synaptic activity before the first PLIF layer;
- DataLoader order is chronological, batch size is one, and fractions are contiguous;
- recurrent numeric state carries across records; training detaches its graph after each record;
- SpikingJelly's internal PLIF `v`/`w` references are also detached, removing a retained-graph RAM peak;
- `--internal-updates` defaults to 10 and is frozen into each checkpoint protocol;
- HDF5/raw readers, event-bin/sequential window datasets, T/stride flags, and raw compatibility commands are removed;
- model parameter count depends on class-head width: XL is 236,445 for six classes and 237,115 for eleven.


## 2026-08-22 — 140k static-actor FPGA Iteration 0

- froze `EventSpikeSeg140k` as the only FPGA target: 140,589 registered / 134,807
  executed inference parameters, 127,456 executed convolution weights, 37 PLIF actors;
- initially selected Alveo U55C, then superseded it with conventional Nexys Video
  XC7A200T when the no-accelerator-card requirement was clarified;
- fixed the topology to 37 permanent layer actors with no cross-layer compute sharing,
  reconfiguration, or partial reconfiguration;
- assigned local initialized weight ROM, convolution addressing, accumulator lanes,
  PLIF/mechanism logic, and output queue to every actor;
- corrected `project2` state to its actual pre-upsample half resolution and measured the
  exact fixed-step incompatibility: about 192.44 MiB dense membrane/adaptation state versus 1.604 MiB XC7A200T BRAM (~120x); the earlier 470.31 MiB figure included a now-superseded 32-bit timestamp per membrane;
  no external/onboard DDR is allowed, so lossless sparse live
  state must pass a measured hard-capacity gate before full deployment is feasible;
- added `src/eventspikeseg/fpga`: fixed formats, deterministic 37-actor export,
  affine-folded int8 ROMs, per-actor parameters, integer PLIF, and sparse state profiler;
- FPGA export hard-rejects XL and omits dead `refine2`, auxiliary training head, and
  surrogate gradients;
- added the canonical externally state-backed, ready/valid PLIF RTL lane with learned
  retention coefficient, integer rounding, saturation, soft reset, and backpressure;
- 72 Python tests and all 6 GHDL/cocotb RTL groups pass in Docker.

## 2026-08-22 — 140k static-actor FPGA Iteration 1 state bank

- added a ready/valid, set-associative, zero-default sparse neuron-state bank in VHDL;
- stores address tags, membrane, last timestamp, adaptation age, and adaptation amplitude;
- supports exact hit update, missing-address reset reads, and exact dead-state reclamation;
- forbids live-state eviction: a full set raises an explicit capacity overflow without
  altering resident state;
- added collision/reclamation cocotb coverage; all 7 GHDL RTL groups pass and Python lint
  passes in the CPU-only Docker verification service;
- next integration is state-bank read -> lazy-retention selection -> PLIF update ->
  state-bank writeback inside one actor-local event lane.
- the epoch-2 one-record sparse profile reached 27,182,700 live entries (37.32% of all
  logical membranes) and 320.08 MiB of tagged state, requiring 295.98x the usable Artix-7
  state budget after weights and reserve; even one bit for every logical membrane would
  require 8.68 MiB, so an exact no-DDR XC7A200T deployment is now rejected rather than
  treated as a likely compression target.

## 2026-08-19 FPGA implementation direction (superseded target/platform details)

- public model names remain `EventSpikeSegXL` and `EventSpikeSeg140k`; XL is the active implementation target;
- XL DSEC accounting: 237,115 registered / 232,059 training-forward / 226,767 inference-forward parameters;
- FPGA deployment omits inherited dead `refine2` and the training-only auxiliary head;
- primary hardware target is custom VHDL-2008 on Xilinx ZCU104;
- PLIF membrane/current/beta/threshold/adaptation are digital fixed-point SNN states, not physical voltages/currents;
- convolution kernels remain shared synaptic weights, while emitted hidden spikes are event addresses that trigger weight additions;
- no softmax exists in the canonical deployed path;
- coarse-grained synaptic-accumulator + PLIF processing elements are time-multiplexed across spatial tiles/channels/stages while persistent state stays in banked memory;
- first hardware milestone is bit-exact integer/RTL equivalence; sparse touched-address/lazy-decay/clock-enable optimizations follow only after exactness;
- DSEC training and baseline FPGA runtime both use ten fixed 5 ms updates per 50 ms record; sparse synaptic work is retained inside each update;
- memory-bounded replay forms one complete-record objective before propagating its gradients through chronological chunks;
- remaining RTL-sensitive mechanisms are fixed-step PLIF decay, peer-membrane inhibition, triangular threshold adaptation, and the local PLIF selector;
- XL adds projected bridge joins, parallel-context joins, local Q/K/V rendezvous, and an external-DDR state-store requirement;
- evaluation flow is RTL simulation -> synthesis/place-route -> post-implementation timing -> representative SAIF/VCD Vivado power -> optional ZCU104 measurement.

### 2026-08-20 logical-state accounting

- compact-reference accounting separates 37 executed PLIF populations from the ~140k shared parameter count;
- general membrane formula: `(672+Nclass)*H*W + 480*H2*W2 + 1280*H4*W4`;
- six-class 212x282 DDD17 requires **51,089,456 independent membrane values**;
- threshold-adaptation scopes cover **9,836,800 logical neurons** at that resolution, each with adaptation age and amplitude;
- implementation contract: static/shared weights and channel parameters, persistent per-`(layer,c,y,x)` neuron state, temporary current accumulators, sparse event FIFOs;
- exact sparse layer execution accumulates all weight contributions for a timestep before one PLIF threshold/reset update, then writes persistent state back and emits only fired addresses;
- a small physical PE array may be time-multiplexed, but logical state addresses may not be aliased; fixed 5 ms state advancement is part of the bit-exact DSEC baseline.

### 2026-08-21 XL DSEC implementation accounting

- then-active resized DSEC dimensions: 241x351 -> 121x176 -> 61x88 (historical XL accounting; current v7 uses native 440x640);
- 50 inference PLIF populations and 226,767 executed inference parameters;
- 85,639,973 membrane states plus 40,049,152 threshold-adaptation age/amplitude values;
- the fixed-step baseline does not require a per-membrane last-update timestamp; layer/tile state can remain resident across t0..t9;
- historical timestamped-prototype persistent store estimate: 566.42 MiB (not the current fixed-step state format);
- historical XL implementation assumption: external DDR backing store with banked on-chip active-tile cache; XL is not the current FPGA target.


### 2026-08-22 fixed 50 ms FPGA runtime decision

- one DSEC semantic record = 50 ms = ten chronological 5 ms SNN updates;
- baseline FPGA runtime now matches this trained timing contract rather than direct per-event asynchronous propagation;
- preferred hardware order is layer-major across the full T=10 record: load/cache one layer or spatial state tile, process t0..t9, write state back once, then advance to the next layer;
- sparse event-addressed convolution remains active inside each 5 ms slice;
- one segmentation output is produced per 50 ms record after temporal class-spike counting;
- baseline fixed-step state no longer requires one 32-bit timestamp per membrane; lazy step-tagging is future optional optimization;
- sustained real-time target is 20 records/s, with optional double buffering of acquisition and compute.

## 2026-08-23 — v7 fixed-step Artix-7 implementation iteration 2

- rebased hardware docs on the native 440x640 v7 `EventSpikeSeg140k` graph;
- canonical deployment is 25 PLIF stages + stateless 16->11 temporal current readout;
- documented 30,976,000 membrane states and 10,982,400 adaptation-enabled neurons;
- recorded the state-first trade: +6.4% synaptic weights versus v6, but -40.5% logical membranes and -35.2% dense persistent state;
- made Artix-7 XC7A200T the explicit FPGA target, using Nexys Video only as the reference carrier board;
- removed `last_timestamp_us` from the integer reference and sparse RTL state record;
- changed exact PLIF RTL/reference to consume learned beta once per fixed 5 ms step;
- replaced the old shift-only local LIF baseline with a learned-beta local PLIF lane;
- added `fixed_record_controller.vhd` for 27-layer x 10-step layer-major scheduling;
- added signed class-current argmax RTL for the new non-spiking readout;
- updated exporter manifest timing/state contracts and sparse-state entry accounting;
- v7 full-sequence sparse occupancy/BRAM fit remains the next hard feasibility measurement.


## 2026-08-23 — FPGA iteration 3: streaming 5 ms bins and lazy state tags

- replaced the active 50 ms layer-major scheduling contract with bin-major end-to-end execution;
- added a streaming runtime reference with configurable prediction windows (default 10 bins / 50 ms);
- added explicit real-time metrics `U=C_bin/(f_clk*5ms)` and `H=1/U`, with hard `U<=1` and target `U<=0.8`;
- added 24-bit `last_bin_tag` to sparse neuron state and restored exact touched-neuron lazy leak semantics without microsecond timestamps;
- changed the integer PLIF reference to repeated learned-beta decay for `delta_bins`;
- changed `plif_update.vhd` to a multi-cycle iterative lazy-leak lane;
- changed the sparse state bank to store/read the compact bin tag;
- added `streaming_bin_controller.vhd`; its actor-count generic is now configured for actor 0..24 bin-major scheduling, cycles/bin instrumentation, deadline/target flags, global bin tags and prediction-due;
- the old `fixed_record_controller` schedule is superseded;
- v8 exact dense touched-state reference is 189.60 MiB including a dense 24-bit tag, while conservative sparse aligned entries remain budgeted at 12 bytes non-adaptive / 16 bytes adaptive;
- full actor integration, ping-pong ingress storage, sparse class-current storage, and GHDL/Vivado verification remain open.

## 2026-08-25 — FPGA iteration 4: streaming integration lanes

- added a lossless two-bank event ingress that overlaps capture with processing, preserves empty 5 ms bins, and forbids reuse until end-to-end release;
- added an actor-local touched-neuron lane sequencing sparse lookup, modular bin-tag distance, iterative learned-beta PLIF update, and exact live-state writeback/reclamation;
- corrected the sparse missing-entry contract so adaptation age resets to the canonical inactive value `-1`;
- added a weight-independent 11-class current-update lane with signed saturation, temporal prediction flush, sparse-state-live output, and first-index tie behavior;
- updated superseded timestamp/retention cocotb tests to the active bin-tag/beta interfaces;
- added executable coverage for the streaming controller, class argmax, ingress buffer, touched-neuron lane, and class-current update;
- all 12 RTL unit groups pass with GHDL 6.0.0 and cocotb 1.9.2; the updated cocotb sources pass Ruff;
- next integration is exported weight ROM + convolution destination accumulation into 25 instantiated actor lanes, followed by exact inhibition/adaptation, sparse per-pixel readout storage/flush, full-graph equivalence, and measured occupancy/cycles per bin.

## 2026-08-25 — ASIC iteration 5: autonomous tap-scatter PLIF actor

- changed the primary hardware direction from globally scheduled FPGA execution to 25 permanent ASIC actors connected by spike and completion-token channels;
- defined the exact 3x3 mapping as nine parallel presynaptic tap projections feeding one canonical postsynaptic current/membrane array;
- added `presynaptic_tap_array.vhd` with padding, stride divisibility, dilation, bounds, signed shared weight, and zero-weight suppression;
- added `asynchronous_plif_actor.vhd` with duplicate contribution accumulation, a first-touch commit queue (no dense destination sweep), actor-local direct-indexed state, lazy learned-beta PLIF updates, and lossless spike/completion backpressure;
- added cocotb tests for 3x3 address fanout, border/zero suppression, completion-gated firing, shared membrane accumulation, and channel backpressure;
- both new VHDL blocks pass GHDL 6 synthesis elaboration, and all 14 RTL unit groups pass with cocotb 1.9.2;
- added a VHDL-preserving GHDL-to-Verilog flow and an ASAP7 ORFS actor configuration for open predictive PPA;
- documented that full-model PPA is blocked on explicit actor-local SRAM macros and a scale-suitable 22 nm-or-better manufacturable PDK; behavioral arrays may be used only for control/equivalence prototypes.

## 2026-08-25 — Native SystemVerilog ASIC implementation

- replaced the VHDL/FPGA hardware tree with native synthesizable SystemVerilog under `asic/rtl`;
- integrated static convolution kernel taps with the actor-local PLIF current/membrane/tag population in `convolution_plif_actor`;
- retained autonomous ready/valid spike traffic and ordered completion-token commits, with no global layer scheduler or runtime reconfiguration;
- migrated exporter, fixed-point contracts, capacity accounting, and integer reference from `eventspikeseg.fpga` to `eventspikeseg.asic`;
- removed obsolete FPGA scheduler, ingress, sparse-bank, lane, accumulator, and VHDL simulation sources;
- changed local RTL verification to Icarus Verilog + cocotb and the open PPA front end to native SystemVerilog + Yosys/OpenROAD;
- all eight native RTL groups pass, including an integrated nine-tap-to-nine-membrane convolution/PLIF test;
- full 25-actor channel fanout, SRAM macro wrappers, mechanism integration, graph equivalence, and routed PPA remain the next implementation stage.
- preserved the complete retired FPGA feasibility/scheduling history inside `project_spec.yaml` under `legacy_fpga_history`, with detailed chronology in the decision/progress logs and sources recoverable from Git history;
- clarified ASIC ingress as timestamp-ordered raw-event synaptic accumulation with no dense bin preload, while retaining one touched-PLIF commit at each trained 5 ms completion boundary.

## 2026-08-25 — Explicit non-linear ASIC DAG contract

- re-fetched the current v8 `EventSpikeSeg140k` forward graph before editing;
- corrected the ASIC interpretation: the 25 PLIF populations are permanent actors in a
  directed acyclic graph, not a sequential `actor0 -> ... -> actor24` pipeline;
- added `src/eventspikeseg/asic/topology.py` with the exact actor nodes, directed edges,
  input/detail-semantic fork, residual bypass joins, `x1`/`x2` skip fanout, 2x event
  upsample routes, decoder/final channel remaps, and multiplicity-preserving `project2+x1`;
- changed export schema to 2.1.0 and made `layer_order` explicitly a deterministic
  topological/export order only; `layer_graph.json` now carries nodes, edges, join semantics,
  and graph kind;
- added SystemVerilog `event_fork2`, `event_join2`, and correctness-reference
  `binary_event_union2` primitives so completion tokens can fork and same-bin branches can
  rendezvous without pretending the graph is linear;
- residual joins are explicitly binary-OR/deduplicating, while decoder `project2+x1` keeps
  coincident events as multiplicity two;
- full 25-actor DAG instantiation, model-scale channel fanout/remap, scalable residual dedup,
  SRAM macro replacement, full-DAG equivalence, and activity-based PPA remain open.

## 2026-08-26 — Channel-aware sparse routing and convolution scatter

- added executable cocotb coverage for the lossless fork, same-bin join, and residual
  binary-OR/dedup blocks, including fail-closed mismatched completion tags;
- added fixed channel-ID offset routing for concatenation and nearest-neighbor 2x event
  expansion that forwards each completion token exactly once;
- added channel-aware standard, grouped, and depthwise convolution scatter with static
  weights flattened in PyTorch `[out][in/groups][ky][kx]` order;
- retained stride, padding, dilation, bounds, channel-group, and zero-weight filtering without
  a dense sliding scan;
- all 16 native Icarus/cocotb RTL groups pass, including separate standard, grouped, and
  depthwise channel-routing cases;
- the next integration boundary is channelized actor-local state/parameter access followed by
  physical instantiation and wiring of the exported 25-actor DAG.

## 2026-08-26 — Channelized convolution/PLIF actor integration

- extended the autonomous PLIF state engine with compile-time per-output-channel beta and
  threshold tables while retaining its scalar compatibility interface;
- integrated channel-aware convolution projections into one canonical actor-local state index
  for every `(output_channel,y,x)` destination and decoded spikes back to event coordinates;
- verified independent membrane persistence and different thresholds for two channels at the
  same spatial coordinate across consecutive completion-tagged epochs;
- extended export with one 16-bit beta ROM image and one signed 16-bit threshold ROM image per
  PLIF actor, alongside the existing JSON parameters and int8 weight ROM;
- all 17 native Icarus/cocotb RTL groups pass;
- next is the generated structural top that instantiates the 25 permanent actors and their
  exact fork/join/concat/upsample DAG routes.

## 2026-08-26 — Generated full DAG, mechanisms, and temporal readout

- added one unified packed event/completion stream wrapper around permanent PLIF actors;
- added a manifest-driven SystemVerilog generator that instantiates all 25 actors and inserts
  every exact fork, residual OR, multiplicity join, concat offset, and 2x upsample route;
- verified a generated reduced-state 25-actor graph compiles and carries two ordered bins
  through the complete non-linear topology to a prediction frame completion;
- added atomic retinotopic all-channel commits for mechanism-enabled actors, including summed
  triangular threshold processes and shared-RMS peer-membrane inhibition;
- added the non-spiking signed temporal class-current bank, configurable ten-bin window, dense
  pixel argmax enumeration, and prediction reset;
- added a technology-independent synchronous single-port 1RW state-memory boundary with behavioral simulation and a
  compiled-SRAM black-box branch;
- 22 cocotb RTL groups plus the generated-DAG compile/simulation test pass locally;
- real-checkpoint export/equivalence and physical SRAM binding remain gated separately from the
  completed structural RTL reference.

## 2026-08-26 — Legacy 11-class trained v4 checkpoint ASIC export

- exported `artifacts/checkpointsV4/dsec/EventSpikeSeg140k_seed17_best.pt` in the pinned
  PyTorch/SpikingJelly container;
- revalidated 150,245 registered parameters, 149,503 executed parameters, 143,904 int8
  synaptic weights, 25 PLIF actors, and 30,976,000 logical membrane states;
- emitted exactly 143,904 weight-ROM words plus beta/threshold ROMs and mechanism parameters
  for every actor; the export enables peer inhibition in one actor and triangular adaptation
  in fifteen actors;
- generated the historical real weighted 370 KiB 11-class SystemVerilog DAG top;
- the complete pinned-container regression passes 79 tests and Ruff reports no issues;
- full-chip implementation is now bounded by characterized SRAM binding, scalable residual
  capacity proof, golden-stream bit-exact replay, and an accessible manufacturable PDK—not by
  missing graph, weight, or actor RTL generation.

## 2026-08-29 — Active six-class export and CPU-only implementation verification

- added `compose_ASIC.yaml` and `docker/app/dockerfile_ASIC`, independent of the
  CUDA training image;
- pinned CPU PyTorch 2.2.2, CPU torchvision 0.17.2, upstream Icarus Verilog 12, cocotb,
  and Yosys in the implementation image;
- exported the trained six-class v4 checkpoint to `artifacts/ASIC` with
  149,835 registered parameters, 149,423 executed parameters, 143,824 weight words,
  25 PLIF actors, one inhibition actor, and fifteen adaptation actors;
- generated the active weighted 25-actor SystemVerilog DAG top;
- removed an unpacked combinational effective-age temporary that crashed Icarus and replaced
  it with equivalent per-channel scalar recomputation;
- the CPU implementation image passes 87 Python/structural tests, 23 cocotb RTL groups,
  Ruff, and the representative Yosys synthesis gate;
- the prior 11-class result remains documented as historical evidence but is not retained in
  the active artifacts tree;
- full-chip physical completion still requires a characterized SRAM compiler/library,
  a selected manufacturable PDK, real golden event streams, and routed activity data.

## 2026-08-31 — Epoch-35 provenance, memory contract, and full-DAG replay

- verified that the then-active checkpoint was epoch 35/seed 17 and exactly matched the epoch-35
  tensor state, then regenerated all weights, neuron parameters, and the structural top;
- quarantined the two remaining epoch-19 replay directories so they cannot be reported as
  evidence for the current checkpoint;
- derived 487 logical actor-local banks at a maximum 65,536 rows: persistent state is
  189.60 MiB, exact direct-index current plus touched flags add 92.32 MiB, and a worst-case
  full-depth touched queue is reported separately rather than hidden;
- added a synthesizable initialized single-port bank that zeroizes all banks in parallel at
  sequence start, blocks events until completion, and takes at most 65,536 cycles (327.68 us
  at the current 200 MHz research target);
- changed generated weight constants to bounded SystemVerilog concatenation chunks while
  preserving exact ROM word order, eliminating Icarus scanner overflow on trained weights;
- regenerated an epoch-35 160-event integer-oracle profile and a four-event RTL smoke replay;
  the full 25-actor smoke top matched all 64 final semantic pixels and bin-10 completion in
  Icarus 12 (191.66 s host simulation time);
- 87 Python tests, all 23 component cocotb groups, Ruff, representative Yosys synthesis, and
  the dedicated full-DAG replay pass in the CPU-only implementation image;
- per-actor RTL trace comparison, native DSEC occupancy/activity measurement, characterized
  SRAM binding, and routed PPA remain open and must not be inferred from the smoke replay.

## 2026-08-31 — ASIC actor-local SRAM integration

- replaced destination-scale behavioral current/membrane/tag arrays in ordinary and
  mechanism-enabled actors with packed single-port read-modify-write SRAM state;
- moved touched-address queues, retinotopic touched markers, signed temporal class-current
  scores, and exact residual-union event storage behind the same technology boundary;
- partitioned large logical memories into at most 65,536-row banks and verified parallel
  scrub plus tail-bank decoding; actors reject events until every owned bank is initialized;
- retained exact 5 ms completion-token semantics: raw events cause sparse signed-weight
  accumulation, while each touched PLIF thresholds/resets exactly once after completion;
- derived a 338.07 MiB direct-index SRAM correctness upper bound excluding the 0.137 MiB
  weight ROM; this includes worst-case full-depth queues and is not an area/power result;
- passed Icarus self-checks for ordinary PLIF persistence, grouped peer inhibition, temporal
  readout, residual deduplication, and multibank SRAM, plus all-top compilation and
  representative Yosys synthesis;
- propagated one generated-top SRAM macro selector through all 35 memory-owning blocks and
  added replay-side cycle/bin, utilization, and headroom capture;
- gated generated-top ingress on all 25 actor initialization signals plus readout
  initialization, so no event can be buffered while owned SRAM is being scrubbed;
- reran the complete SRAM-integrated 25-actor smoke DAG: all 64 semantic pixels and the
  bin-10 completion tag matched, no fault asserted, and 1,024 initialization cycles were
  excluded from 12,135 steady-state cycles (1,213.5 cycles/bin, 0.2427% of a 5 ms bin at
  100 MHz, 412.03x timing headroom) in the reduced 8x8 case;
- all 23 component cocotb groups, generated-top contract tests, and both behavioral and
  macro-selected complete-top compilations pass after the initialization-gate change.
- added per-actor touched-queue and per-residual-join high-watermarks to the existing replay
  profile instead of creating another artifact family; the deterministic reduced four-event
  smoke fixture observes maxima of 287 touched entries and one residual entry, while the
  160-event stress fixture observes 1,018 and 158 respectively;
- removed the smoke runner's 2,048-entry residual-capacity override so full-DAG verification
  exercises the generated top's actual 64-entry default; fixture observations remain explicitly
  non-native and are not a safe production capacity bound;
- reran the complete smoke DAG with that 64-entry default: all 64 pixels and bin-10 completion
  still match with no fault or overflow, while the architectural metrics remain 12,135 cycles
  per ten-bin frame after excluding 1,024 initialization cycles;
- built and ran `compose_ASIC.yaml`: 87 Python tests, Ruff, 23 cocotb groups, representative
  Yosys synthesis, and the complete exported-DAG replay pass in the CPU-only image; the image
  identifies itself as Torch 2.2.2+cpu with no CUDA build or available CUDA runtime;
- reconciled the stale final-loss regression/YAML with the newer committed v12 implementation:
  pixel CE 1.0, macro CE 0.0, Dice 0.30, region consistency 0.0, auxiliary CE 0.10, and
  boundary 0.02.

## 2026-08-31 — OpenROAD routed actor prototype

- completed the official ORFS ASAP7 flow through parasitic extraction and final GDS for a
  reduced 4x4 integrated convolution/PLIF actor at a 5 ns (200 MHz) clock constraint;
- post-route timing has zero setup and hold violations, 3.888 ns setup slack, 36.61 ps hold
  slack, and a reported minimum period of 1.112 ns (899.23 MHz nominal actor-only fmax);
- the 63.297 x 63.297 um die has 4,006.51 um2 die area, 3,502.74 um2 core area, and
  1,254.57 um2 non-filler standard-cell area at 35.82% utilization;
- detailed routing completed with zero DRC violations and the flow reported zero fatal errors;
- replaced a rejected global 280 ps slew guardband with a targeted 64-sink fanout constraint;
  the routed maximum net degree fell from 136 to 65 and extracted maximum-slew, fanout, and
  capacitance violations are all zero, with +47.64 ps worst slew margin;
- public ASAP7 supplies no characterized SRAM macros, therefore this experiment expands the
  tiny 4x4 memories into 1,553 sequential cells and cannot be scaled into a full-model area or
  power claim;
- OpenROAD's vectorless estimate is 1.335 mW and is retained only as a tool sanity result, not
  article evidence for event-driven model power; representative checkpoint/event activity and
  characterized SRAMs remain required;
- the amd64 ORFS image ran under Apple-silicon emulation with documented post-CTS timing repair
  skipped after that phase reproducibly raised SIGILL; native-x86 rerun must restore it before
  publication;
- `run_orfs.sh` now uses the installed official Docker image when `ORFS_ROOT` is unset and keeps
  every generated physical-design file under the Git-ignored `artifacts/OpenROAD` tree.
- `run_orfs.sh` now validates the extracted JSON and detailed-route report after Docker exits;
  any nonzero setup, hold, slew, fanout, capacitance, DRC, or flow-error count fails the command
  even when OpenROAD itself returns success.

## 2026-09-01 — Per-actor RTL current, membrane, and spike equivalence

- extended the existing epoch-35 full-DAG replay without adding RTL debug ports or a new
  artifact family: cocotb observes each generated actor's accepted output stream internally;
- compared bin tag, channel, y, and x for every emitted spike against the existing integer
  oracle for all 25 permanent PLIF actors, including exact silence checks;
- the reduced four-event 8x8 fixture matched all five emitted actor-spike rows exactly, while
  retaining the final 64-pixel semantic-frame and bin-10 completion-tag checks;
- trace monitoring does not alter the established latency result: initialization remains
  1,024 excluded cycles and steady-state completion remains 12,135 cycles;
- the first direct membrane comparison exposed a genuine one-LSB lazy-leak oracle defect:
  Python formed a rounded beta-power coefficient and multiplied membrane once, whereas RTL
  correctly rounds the membrane after each elapsed 5 ms beta update;
- corrected `IntegerPLIF` and the mechanism-enabled DAG reference to repeat membrane decay in
  RTL order, added a signed three-bin rounding regression, and regenerated the same fixture;
- the final replay exactly matches 1,532 accumulated-current rows, 1,538 candidate/membrane/
  spike transition rows, and five actor-output spike rows across all 25 actors;
- extended the existing membrane artifact and non-synthesizable monitors to compare adaptation
  age and amplitude without adding RTL ports or another artifact family; all 126 commits from
  adaptation-enabled actors match exactly;
- the final extended replay passes in 209.55 seconds of Icarus host runtime; the focused 37-test
  ASIC/training regression and Ruff pass after the trace extension, while the prior complete
  88-test regression remains the latest full-suite result;
- the five-spike smoke fixture is not a native-resolution activity or capacity bound.

## 2026-09-01 — Native DSEC activity-profile path

- added a narrow native integer-DAG profiler using the existing `artifacts/RTL/profile`
  output family; no new RTL implementation hierarchy or report claim was introduced;
- bound record selection to the active checkpoint's exact held-out sequence membership:
  all 234 records of `zurich_city_02_a`, with PLIF state retained across its 2,340 bins;
- preserve integer event multiplicity when converting the dataset's ten 5 ms count planes
  back to ingress events, and report per-actor live-state, touched-queue, output-spike, and
  residual-union high-watermarks;
- partial runs are explicitly marked `capacity_claim: false`; untimed integer execution also
  marks cycle latency and power activity unavailable;
- the complete Python regression now passes 89 tests and Ruff;
- native execution awaits a mounted DSEC tree; the active checkpoint is present locally, but
  no raw DSEC dataset is installed on this Mac and the repository sample directory is empty.

## 2026-09-01 — SKY130 SRAM-backed actor-tile layout

- bound the technology-independent actor memory boundary to two characterized
  `sky130_sram_1rw1r_80x64_8` OpenRAM macros: one stores the 66-bit packed PLIF state and one
  stores the touched-address queue for the reduced 4x4 actor;
- added a dedicated SKY130HD ORFS configuration, fixed macro adapter, and explicit power grid
  connecting the macros' lowercase met3 `vdd`/`gnd` pins to the met4/met5 core grid;
- completed synthesis, macro placement, CTS, detailed routing, extraction, connected-power
  analysis, and merged GDS using the official ORFS image;
- the final flow contains exactly two SRAM macros, has zero setup/hold/driver violations,
  zero detailed-route DRC, zero antenna violations, and no orphan LEF/GDS cells;
- at a 20 ns constraint, extracted setup and hold slack are 5.009 ns and 0.449 ns, with a
  reported 97.31 MHz nominal actor-tile fmax;
- die/core area is 1,679,210/1,574,100 um2, comprising 363,942 um2 of SRAM macros and
  52,935.8 um2 of non-filler standard cells; this deliberately wasteful pair of 80x64 SRAMs
  validates integration, not the eventual native actor banking policy;
- vectorless power is 8.295 mW and worst VDD/VSS IR drop is 0.114/0.102 mV; both are tool
  sanity values without checkpoint-derived DSEC switching activity and are not article
  event-driven power evidence;
- normalized the shared report checker across ASAP7 picosecond and SKY130 nanosecond report
  units and made the SKY130 flow fail unless exactly two macros survive;
- verified 66-bit write/readback and read-valid timing against the exact bundled OpenRAM
  functional model; its declaration-order issue required only a temporary Icarus-compatible
  copy, while the checked-in adapter remains unchanged;
- added the external-SRAM actor branch to the normal Icarus and representative Yosys gates;
- post-CTS timing repair remains skipped only for the documented Apple-silicon amd64-emulation
  `SIGILL`; native-x86 rerun with repair enabled is still required before publication.

## 2026-09-01 — Native real-event full-DAG short-interval execution

- rebuilt the CPU-only ASIC image with the declared HDF5 compression plugin and read the supplied
  `zurich_city_13_a/events.h5` directly; no CUDA training image is involved;
- executed the first complete 5 ms interval through all 25 checkpoint-exported actors at native
  440x640 geometry, retaining event multiplicity and actor-local state while disabling only the
  enormous diagnostic row trace;
- the raw file contains 42,764 indexed events in the first 5 ms; the unrectified native crop keeps
  41,839, so this is a sample-only activity run until the matching DSEC rectification map is added;
- regenerated all ASIC weights, parameters, memory manifest, and the 25-actor top after a
  provenance guard detected that the current checkpoint is epoch 40/seed 17 strategy v12 rather
  than the previous epoch-35 export; profiling now refuses any such mismatch;
- the corrected bit-exact run completed in 349.53 host seconds, performed 138,562,457 synaptic
  additions, emitted 646,175 actor spikes, and ended with 5,869,959 live actor-state entries;
- `final_fuse.standard` is the present single-lane RTL bottleneck: 88,597,529 additions,
  1,401,431 touched destinations, and 275,576 spikes imply a conservative 277,279,611-cycle
  actor-service floor;
- using the routed SKY130 actor tile's non-full-chip nominal 97.31 MHz only as a clock reference,
  that floor is 2.849 s per 5 ms bin (at least 569.9x over deadline) and requires at least 570
  ideal conflict-free lanes/banks before routing and SRAM conflicts;
- this is full-model native functional activity plus an RTL-FSM lower bound, not a cycle-accurate
  full-native RTL run or a routed full-chip power/latency result. Activity-based power remains open.

## 2026-09-01 — Banked actor implementation resume point

- keep the 25 permanent actor DAG and exact bin-completion semantics; the performance defect is
  intra-actor serialization, not runtime layer reconfiguration;
- retain `asynchronous_plif_actor.sv` as the one-lane oracle and implement an ordinary-actor bank
  wrapper first, with `global_destination % lane_count` routing and disjoint local SRAM/queue state;
- required wrapper behavior: selected-lane input backpressure, global/local address conversion,
  fair spike merge, one same-tag completion only after every lane completes, error aggregation, and
  all-lane initialization gating;
- after ordinary-lane equivalence, replace the single-output convolution scatter bottleneck with
  parallel contribution streams, then bank retinotopic mechanism actors by spatial address so all
  channels at one location remain atomic;
- verification gates are one-lane equivalence, collision/no-loss tests, independent-bank overlap,
  completion rendezvous, randomized integer-oracle comparison, synthesis, and native workload lane
  sizing. Do not claim the ideal 570-lane floor as an implemented result.

### Completed ordinary-actor banking stage

- regenerated the reduced smoke and 160-event profiles from the epoch-40/seed-17 strategy-v12
  export; the reduced full-DAG RTL replay passes exact output plus 1,540 current, 1,542 membrane,
  five spike, and adaptation trace comparisons in 12,178 steady-state cycles;
- added `banked_asynchronous_plif_actor.sv`, which interleaves global destinations across disjoint
  local state/queue SRAMs and never duplicates a membrane/current entry;
- added global-stride/offset parameter lookup to the retained single-lane actor so an interleaved
  local row still selects the correct global output-channel beta and threshold;
- implemented selected-bank input backpressure, local/global address conversion, deterministic
  spike merge, all-lane completion/tag rendezvous, initialization gating, and fault aggregation;
- integrated ordinary banking beneath `channelized_convolution_plif_actor` and
  `streaming_channelized_plif_actor` with `STATE_LANE_COUNT=1` as the equivalence-preserving default;
- four lanes accept eight round-robin-bank contributions on eight consecutive clocks; same-bank
  accesses correctly backpressure, and global-channel parameter/spike-address tests pass;
- all 25 component cocotb groups pass after integration. The next resume point is parallel
  convolution scatter: the current scalar contribution output still caps the actor at one addition
  per clock even when state banks are available.

### Completed parallel scatter and mechanism-aware actor banking

- added a vector convolution scatter that emits at most one ordered contribution per
  channel-by-spatial bank each clock and retains the remaining projection bitmap under
  backpressure; per-bank projection order matches the scalar reference so signed saturation
  behavior is unchanged;
- added the end-to-end ordinary parallel actor with disjoint state/queue memories and verified
  simultaneous contributions to different channel/spatial banks, state retention across bins,
  global coordinate reconstruction, and completion rendezvous;
- added spatially interleaved retinotopic banks. Every lane owns all channels for its pixels, so
  inhibition and threshold adaptation remain atomic across peer channels while different pixels
  execute independently;
- integrated both ordinary and mechanism-enabled parallel actors beneath the unified stream
  interface. Reference, four-bank ordinary, and two-bank inhibited stream configurations pass;
- corrected the stream testbench to hold a completion packet until the completion-specific ready
  signal accepts it; the former zero-latency assumption could drop a token while parallel scatter
  work was draining;
- the next resume point is full-DAG generation: export per-actor lane factors, instantiate the
  parallel stream paths in the generated 25-actor top, then derive conflict-aware lane sizing from
  the native epoch-40 activity rather than presenting the 570 ideal floor as implemented latency.

### Completed native conflict-aware lane sizing

- extended the full-DAG generator with an external per-actor lane manifest and emitted explicit
  parallel-state, channel-lane, and spatial-lane parameters for all 25 actors; generated RTL embeds
  the exact manifest SHA-256;
- added low-memory bank counters to the integer DAG reference. They count all additions, touched
  entries, and spikes by the same modulo mapping used in RTL without retaining a 138-million-row
  contribution trace;
- require per-bank counts to conserve the aggregate actor totals before accepting a service result,
  and added a synthetic imbalance regression;
- iterated the one-bin native profile against actual modulo-bank imbalance. The final manifest owns
  1,718 independent actor lanes; ordinary actors split channel and spatial dimensions, while the 15
  mechanism actors split only spatial locations;
- the final exact activity totals remain 138,562,457 additions, 646,175 actor spikes, and 5,869,959
  live sparse state entries. Manifest, profile, and generated top share SHA-256
  `8ff8673edbe91a72142aaa95f6b91d530808013110f662700fcb3a92ff6c0519`;
- the busiest configured bank is `enc2_extra.depthwise` at a 388,589-cycle service floor, 3.993 ms
  at the isolated tile's 97.31 MHz reference, and `U=0.79866`; both the hard `U<=1` and engineering
  `U<=0.8` service-floor gates pass for this sample;
- do not report this as end-to-end latency or power. Next resume point: add generated-top FIFO depth
  sizing and a tractable cycle-accurate critical-path/full-DAG validation, then bind the 1,718 bank
  interfaces to scale-suitable characterized SRAM macros before full-chip PPA.

### Completed lossless elastic DAG-edge buffering

- added `event_stream_fifo.sv`, a synthesizable ordered ready/valid queue for the unified payload,
  completion flag, and bin tag; full queues backpressure and never discard or reorder packets;
- inserted a configurable FIFO on every non-prediction edge generated for the exact 25-actor DAG,
  breaking direct combinational ready chains while guaranteeing completion stays behind its bin's
  spikes;
- verified full/backpressure behavior and ordered spike/token drain in cocotb, and compiled plus
  token-simulated the complete reduced generated DAG with all edge FIFOs present;
- added per-edge occupancy/high-watermark registers and reran the epoch-40 reduced 8x8 replay. It
  remains bit-exact for all current, membrane, spike, and adaptation traces and completes in 12,186
  cycles; the FIFO insertion adds eight cycles relative to the 12,178-cycle unbuffered replay;
- 17 of 53 edges reach the depth-two default on that fixture, so none of those edges may be reduced
  to depth one from current evidence. Full queues can pop and accept a replacement in one clock;
- the default depth is still a reduced-fixture timing choice, not a native occupancy claim. Next
  resume point: obtain native cycle traffic or a calibrated event-level schedule before selecting
  deeper per-edge buffers or reporting end-to-end latency.

### Completed completion-token latency-floor sizing

- split each configured bank's service estimate into collection and post-token PLIF-commit terms;
  because a downstream actor cannot commit before all required same-bin tokens arrive, a
  topological longest-path sum of commit terms is a strict response-latency floor;
- the 1,718-lane throughput configuration fails that test at 1,050,545 cycles, 10.796 ms at the
  isolated 97.31 MHz tile reference, or 2.159 times the 5 ms deadline. This corrects the possible
  misreading of its 3.993 ms busiest-bank service interval as end-to-end latency;
- added `plan_asic_latency_lanes.py`, which adds spatial banks using observed commit imbalance and
  an explicit safety factor. Its output is labelled a candidate and cannot become a measurement
  until the exact native event profile is rerun;
- exact reprofiling accepted a 1,966-lane mapping. It leaves the `final_fuse.standard` service
  bottleneck at 384,334 cycles (3.950 ms, `U=0.78992`) and reduces the commit-only critical path to
  349,094 cycles (3.587 ms, `U=0.71749`), passing both 5 ms and 80% floor gates on this sample;
- the accepted manifest/profile/generated-top SHA-256 is
  `172121ae49208c034d95314ab65b1cf6cb1975f7a7166d78f558f830f6ff003d`; the prior 1,718-lane
  manifest is retained locally as the throughput-only baseline;
- post-change verification passes: lint, 94 Python tests, 32 cocotb RTL groups, representative
  Yosys synthesis, and the previously completed bit-exact FIFO-buffered replay;
- this remains a lower bound, not measured end-to-end latency. Next resume point: account for
  native edge traffic, FIFO/backpressure, route/join/readout cycles, then characterize the
  1,966-bank SRAM organization and run full-chip physical PPA.

### Completed native edge-volume gate

- derived every edge's exact one-bin data volume from actor outputs and route semantics, validating
  each actor input count against its incoming graph stream; the generated graph has 53 FIFO edges;
- the busiest edge is `final.concat -> final_fuse.standard` with 657,634 data events plus one
  completion token. A scalar link therefore has a 657,635-cycle serialization floor: 6.758 ms and
  `U=1.35163` at 97.31 MHz, failing both hard and 80% gates;
- the minimum volume-only width is two packets per clock at 97.31 MHz. Occupancy is still unknown
  because volume alone has no arrival/departure timing and is not used to resize the FIFOs;
- removed the avoidable empty cycle between parallel-scatter inputs: when every pending projection
  handshakes, the next presynaptic spike can replace it on the same rising edge; focused RTL
  back-to-back acceptance passes;
- next resume point: either implement and verify a two-packet hot-path interface or demonstrate a
  routed full-chip clock of at least 164.41 MHz for the scalar volume/80% gate, then run a timed
  native backpressure model. The current 97.31 MHz result cannot support a real-time claim.

### Completed 200 MHz lane-cost refinement

- evaluated the existing architectural 200 MHz target, whose 800,000-cycle 80% budget allows the
  scalar hot edge to pass without adding a second packet network;
- rejected the first 917-lane candidate after exact reprofiling: `stem` reached 1,176,798 cycles
  and the commit chain reached 897,040 cycles, demonstrating that ideal/projection sizing was
  insufficient;
- fed those measured conflicts into a second exact iteration. The 924-lane result passes the three
  independent floors: busiest bank 781,772 cycles (`U=0.78177`), completion-token commit path
  737,691 cycles (`U=0.73769`), and scalar edge 657,635 cycles (`U=0.65764`);
- promoted the 924-lane mapping to the generated full top and preserved the 1,966-lane 97.31 MHz
  mapping locally. Manifest, exact profile, and top share SHA-256
  `81f8381ec225b82d5f03965e5a9415bb7e07b1126a4072497906f4037860f257`;
- this promotion is a target configuration, not a full-chip latency claim. Next resume point:
  timed scatter/bank/FIFO backpressure analysis and full-chip 200 MHz physical closure with
  scale-suitable SRAM macros; failure of either requires wider links or more lanes.

### Event-order collection timing rejected the spatial-only mechanism datapath

- instrumented exact event order, same-cycle scatter replacement, ordinary three-cycle bank
  cadence, mechanism five-cycle cadence plus first-spatial-touch write, and completion admission
  only after every bank returns to collect;
- the promoted 924-lane mapping fails before inter-actor FIFOs are considered. `down2.standard`
  requires 40,097,168 collection cycles and 40,107,810 cycles including its busiest commit bank
  (200.539 ms at 200 MHz); `stem` needs 6,593,614 total isolated cycles;
- `final_fuse.standard` also rises from its bank-count floor to 1,875,150 isolated cycles because a
  single pending-event bitmap stalls all otherwise independent banks when any destination bank is
  busy;
- the mechanism failure is structural: spatial-only contribution ports serialize all output
  channels that target the same pixel. More spatial modulo banks cannot fix this same-pixel
  serialization;
- next resume point: separate mechanism accumulation banking from mechanism commit atomicity.
  Channel-by-spatial current/state ports must collect independently, then one spatial coordinator
  must read peer channels, apply inhibition/adaptation atomically, and write them together. Ordinary
  actors also need multiple pending scatter contexts or per-bank projection queues.

### Ordinary actor scatter decoupling in progress

- added an ordered depth-four contribution FIFO between each ordinary scatter output and its
  destination state bank; each queue stores destination channel/coordinate and signed weight;
- full queues backpressure only their corresponding scatter bank, simultaneous pop/push has no
  bubble, and completion cannot enter until the scatter plus every contribution FIFO is empty;
- integrated tests accept four consecutive presynaptic events while the three-cycle accumulator
  banks are busy, then prove the expected spikes and clean completion with no routing fault;
- this is a functional decoupling step, not a new native timing result. FIFO depth and ordinary
  actor timing must be reprofiled after the mechanism channel-by-spatial collection path exists.

### Register-resident PLIF replacement started

- added `resident_plif_population.sv`: every logical ordinary neuron owns local current and
  membrane state elements, parallel contribution lanes accumulate directly into those elements,
  and one completion edge updates the whole population in parallel;
- the resident primitive has no state-memory request/response interface, touched queue, scrub pass,
  or last-bin tag. Applying one beta update to every neuron on every 5 ms completion is numerically
  equivalent to lazy elapsed-bin leakage while state remains continuously resident;
- a four-neuron/two-channel test accepts two different destination contributions in one clock and
  produces the exact two-neuron spike bitmap on the following completion transaction;
- Icarus and Yosys pass; Yosys explicitly reports the current and membrane arrays replaced by
  registers, confirming that this primitive does not infer SRAM. Full regression now contains 33
  RTL groups;
- next resume point: create the resident retinotopic population with per-channel current/membrane/
  adaptation state, parallel peer-channel inhibition/adaptation at completion, then replace the
  generated actor stream with direct spike bitmaps and remove superseded SRAM actor paths.

### Direct resident actor datapath implemented

- added `resident_retinotopic_plif_population.sv`; every mechanism-enabled PLIF now owns
  resident current, membrane, adaptation-age, and adaptation-amplitude state, while each
  spatial peer group performs its inhibition/adaptation commit atomically and in parallel;
- added `resident_convolution_synapses.sv`; a binary presynaptic spike bitmap gates the
  compile-time int8 convolution weights and forms the complete postsynaptic current-delta
  vector without weight-ROM or state-memory transactions;
- added `resident_channelized_plif_actor.sv` to bind the static synapse fabric to either the
  ordinary or mechanism-enabled resident population. Repeated bitmap transactions preserve
  event multiplicity, and the completion token commits the resident population;
- focused cocotb verification covers direct grouped convolution, simultaneous peer-channel
  accumulation, inhibition/adaptation, and an end-to-end resident actor transaction;
- next resume point: change the generated 25-actor graph and its join/fanout representation
  from scalar event streams to resident spike-vector transactions, then establish full-model
  elaboration feasibility before removing the superseded SRAM actors.

### Resident graph routing and readout primitives implemented

- added `streaming_resident_channelized_plif_actor.sv`, which accepts one or more spike-vector
  pulses followed by a completion token and emits one result vector followed by the matching
  completion token;
- added `resident_event_ingress_adapter.sv`; every raw `(channel,y,x)` event becomes a one-hot
  pulse transaction, so timestamp order and repeated-event multiplicity are preserved without
  constructing or preloading a 5 ms input bin;
- added bitmap-native channel-offset, nearest-neighbor 2x upsample, and binary residual-OR
  blocks. The residual block rendezvous-checks bin tags and emits coincident spikes once;
- added a storage-free two-way vector fork that retains only branch-acceptance bits while the
  source holds its vector stable, avoiding a duplicate feature-map register bank at fanout;
- added `resident_temporal_class_readout.sv`; signed class currents are local resident elements
  over the prediction window and first-index-tie argmax enumerates the semantic map;
- updated `docs/AGENTS.md`, which still mandated the superseded SRAM/tag design, to match the
  higher-priority resident-state project specification;
- next resume point: make resident bitmap generation the default path in
  `scripts/generate_asic_top.py`, infer every intermediate vector shape from the exported graph,
  compile the complete 25-actor reduced fixture, then attempt native checkpoint elaboration.

### Resident 25-actor generator completed; native elaboration exceeded 8 GB

- `scripts/generate_asic_top.py` now defaults to the resident architecture and infers every
  actor/route channel-height-width vector shape from the exported non-linear graph. The old path
  remains available only as `--architecture legacy_sram` for replay/equivalence history;
- the geometry-preserving reduced fixture generates and compiles all 25 resident actors, nine
  bitmap residual unions, three bitmap upsamplers, both concats, the multiplicity join, and the
  resident temporal readout. Icarus event simulation of even that fully parallel graph is too
  slow for the normal gate, so behavior remains covered by bounded primitive/actor cocotb tests;
- generated the checkpoint-authoritative native top at
  `artifacts/ASIC/eventspikeseg140k_resident_dag_top.sv` (ignored, 387,139 bytes), containing all
  25 actors and 143,824 exported int8 synaptic weights;
- native Icarus elaboration under the configured 8 GB Docker limit was killed with exit 137 after
  roughly 79 seconds. No native simulation began, so this produces no latency or power result;
- next resume point: introduce a spatially tiled hierarchical resident implementation and
  characterize one exact tile per actor configuration. State remains register/latch-local to each
  PLIF; tiling may reduce tool object expansion but cannot erase the 1.59-billion resident state
  bits or guarantee that full-chip synthesis will fit in 8 GB.

### Register-resident spatial tile boundary established

- added output-tile coordinates and dimensions to the resident convolution, direct actor, and
  streaming actor. A tile evaluates the original global convolution coordinates but instantiates
  state only for the PLIFs physically owned by that tile;
- actor-level cocotb proves that a tile covering global x=2..3 responds to those source
  coordinates and returns its two local PLIF results;
- changed the vector-to-completion edge to retain only one phase bit. The producer holds its result
  bitmap and tag stable through the data and completion handshakes, avoiding a second wide register;
- added `scripts/plan_asic_resident_tiles.py`. The checkpoint export's nominal 8x8 plan contains
  20,410 tiles and conserves all 30,976,000 PLIFs. Resident state is 1,590,476,800 bits
  (198,809,600 byte-equivalent): 24-bit current plus 16-bit membrane for every PLIF, plus 16-bit
  adaptation age and 16-bit adaptation amplitude where enabled;
- the 25 PLIF actors own 143,728 int8 convolution weights; the remaining 96 of the model's 143,824
  weights belong to the temporal readout. The derived ignored manifest is
  `artifacts/ASIC/resident_tile_plan_8x8.json`;
- next resume point: add a lockstep tile-array wrapper and compile a reduced multi-tile actor, then
  synthesize representative exact 8x8 actor tiles. Scaled tile PPA remains an estimate, not a
  substitute for full-chip placement and routing.

### Resident tile hierarchy integrated; emulated PPA front-end bounded

- added `tiled_resident_channelized_plif_actor.sv`. Every child tile accepts input and completion
  atomically with its peers, retains its own state, and contributes its local bitmap back to the
  actor's global channel-major output. A two-tile test proves one event/completion/result transaction;
- the streaming resident actor now defaults to explicit 8x8 spatial children, and the native
  checkpoint top was regenerated with the tile dimensions embedded for all 25 actors;
- added a PPA-top generator that uses the real checkpoint weights, beta, and threshold. This avoids
  the invalid zero-weight optimization that would otherwise erase the synapse fabric;
- bounded ASAP7 attempts under amd64 emulation did not reach routing: the 8x8 `detail_stem` tile was
  stopped after more than ten minutes in Yosys canonicalization; the 4x4 tile canonicalized in 58 s
  at 329 MiB peak but was stopped after more than twenty minutes in technology-map optimization.
  Both exited 137 because their disposable containers were deliberately stopped, not because the
  8 GB limit was exhausted. Neither attempt provides latency, area, or power;
- next resume point: route a checkpoint-exact 2x2 characterization unit, then use its result only as
  a standard-cell scaling datum while improving the structural synapse/leak elaboration.

### Checkpoint-exact 2x2 resident unit routed with a slew-cleanup failure

- disabled optional ASAP7 full-adder extraction for this characterization flow; under x86
  emulation it dominated runtime without changing the RTL state or arithmetic contract;
- Yosys mapped the 32-PLIF `detail_stem` unit with its 144 trained int8 weights. Synthesis took
  271 s and peaked at 1,456 MiB; detailed routing completed and peaked at 7,568 MiB;
- the routed unit contains 1,337 sequential cells and 56,841 multi-input combinational cells.
  Final standard-cell instance area is 7,247.19 um^2 in a 21,139.7 um^2 core (34% utilization);
- setup/hold, max capacitance, max fanout, global congestion, detailed-route DRC, power connectivity,
  and GDS orphan-cell checks pass. Reported internal fmax is 772.241 MHz;
- final validation still fails on 68 internal max-slew endpoints: 321.65--360.29 ps against the
  320 ps limit. The completed run also used the previously copied SDC with stale input names, so
  timing is not accepted for publication;
- vectorless power is 30.9699 mW at 0.77 V and 200 MHz, with 0.003579 V (0.46%) worst VDD drop.
  This is preliminary default-toggle tile power, not DSEC activity-based power and not full-chip
  power. The next run uses the resident-port SDC and corrected integer-percentage slew repair.

### Checkpoint-exact 2x2 resident unit reaches clean routed sign-off checks

- the resident-specific SDC rerun reduced but did not eliminate extracted max-slew failures:
  1.2% repair margin left 27 violations and 20% left 8. OpenROAD's `SLEW_MARGIN` is an integer
  percentage, not a multiplier;
- the accepted run uses a conservative 50% pre-route slew margin. Placement repair resized 140
  cells and inserted 175 buffers; global-route repair resized 2 more cells and inserted 117 more
  buffers. Final standard-cell area is 7,311.29 um^2 in the unchanged 21,139.7 um^2 core
  (34.59% utilization);
- extracted setup and hold violation counts are zero, max-slew/max-capacitance/max-fanout counts
  are all zero, and worst slew has 90.03 ps positive margin against the 320 ps ASAP7 limit.
  Detailed-route DRC is empty, global congestion is zero, both power nets are connected, and GDS
  merging reports neither missing nor orphan cells;
- reported internal fmax is 639.636 MHz. Default vectorless power is 30.9607 mW at 0.77 V and
  200 MHz; worst VDD drop is 4.453 mV (0.58%). These are clean physical-characterization results
  for one checkpoint-exact 2x2/32-PLIF `detail_stem` unit, not full-model latency or power and not
  DSEC activity-based energy;
- next resume point: replace full-layer bitmap broadcast at the production tile wrapper with each
  tile's exact convolution receptive halo, verify global-to-local coordinate equivalence, and then
  characterize the reduced inter-tile fanout. Full-chip PPA remains blocked by native scale.

### Production resident tiles use exact receptive halos

- replaced full-input bitmap replication at `tiled_resident_channelized_plif_actor` with a
  compile-time clamped receptive rectangle for every output tile. The synapse fabric subtracts the
  halo origin after applying the checkpoint's global stride, padding, and dilation geometry;
- the local bitmap contains input spike bits only. Every tile still owns exactly its original
  output PLIF current, membrane, and optional adaptation registers, so the change adds neither
  runtime state addressing nor duplicated PLIF state;
- a cross-tile 3x3 cocotb case proves that the second output tile receives an input pixel from the
  neighboring receptive border and produces the same three global outputs as untiled convolution.
  The focused tests, all 47 cocotb groups, 96 Python tests, Verilator lint, and compilation of all
  40 SystemVerilog tops pass;
- the checkpoint-derived 8x8 plan now counts 51,871,626 tile-input bit endpoints versus
  73,444,096,000 endpoints for replicating every complete actor input bitmap to every tile: a
  99.929% logical endpoint reduction. This is a static wiring/fanout inventory, not routed wire
  length, capacitance, power, or full-chip PPA;
- next resume point: synthesize a representative boundary-aware multi-tile wrapper and compare its
  net fanout/area against the isolated interior unit. Full native graph simulation and PPA remain
  blocked by the 8 GB elaboration boundary and physical model scale.

### Checkpoint-exact two-tile synthesis gate added

- extended the resident physical-design top generator with explicit tile rows/columns. Its default
  remains the accepted isolated interior unit; multi-tile mode keeps the actor's real padding and
  stride and instantiates the production receptive-halo wrapper;
- generated and synthesized a two-column `detail_stem` top containing all 144 trained int8 weights,
  64 resident PLIFs, and two 2x2 child tiles. Yosys `proc`, memory lowering, optimization, and
  structural `check` complete successfully;
- the first synthesis exposed an unintended latch on the procedural tag-check loop index. The index
  is now assigned on every combinational path; the same synthesis and tiled cocotb regression pass.
  A small tiled-wrapper case is included in `check_synthesis.sh` so this class of issue is gated;
- next resume point: produce a separate OpenROAD configuration for the two-tile boundary top and
  obtain routed fanout/area/timing data. Keep it distinct from the accepted single-unit result and
  do not extrapolate either result to full-chip power or latency.

### Two-tile boundary PPA reaches detailed-route memory boundary

- the separate checkpoint-exact `detail_stem` two-column (two 2x2 child tiles, 64 resident PLIFs,
  all 144 actor weights) ASAP7 flow completed synthesis, floorplan, placement, CTS, and global
  routing after the multi-tile ready/valid loop was removed;
- completed intermediate values: 13,492.10 um^2 synthesized standard-cell area; 38,466.18 um^2
  core at 35% target utilization; 13,226 um^2 after CTS; 118,367 CTS instances; 2,674 clock sinks;
  197 clock buffers; global-route area 13,271 um^2; +3,502.265 ps global-route setup slack at the
  5 ns constraint. These are not extracted final results;
- detailed routing began with 1,024,833 guides and reached 10% of its first optimization pass with
  zero violations, then the amd64-on-Apple container stopped at 7,764,480 KB peak memory, which is
  effectively the configured 8 GB Docker limit. No `6_report.json`, detailed-route DRC report,
  extracted timing, IR-drop, GDS, or power report was produced;
- next resume point: run this same configuration on a host with more than 8 GB Docker memory (or a
  native x86 host) before reporting any two-tile PPA. Do not shrink/replace the checkpoint-exact
  hierarchy merely to obtain a routed result.

### Checkpoint-exact two-tile boundary PPA completes on the expanded-memory host

- reran the identical two-column `detail_stem` boundary top on Docker Desktop with 30.61 GiB
  available memory. The run completed routing, extraction, IR analysis, GDS generation, and final
  report generation; the prior 8 GiB detailed-route stop is superseded for this configuration;
- final ASAP7 result: 13,271.30 um^2 standard-cell area in a 38,466.2 um^2 core (34.50%
  utilization), 653.704 MHz internal fmax, +3,470.26 ps setup slack, and +35.6615 ps hold slack
  at the 5 ns constraint. The design contains 64 resident PLIFs across two 2x2 tiles and all 144
  trained `detail_stem` int8 weights;
- final checks pass: zero setup/hold, max-slew, max-capacitance, max-fanout, and detailed-route
  DRC violations; `finish__flow__errors__count` is zero. Worst VDD drop is 3.2908 mV (0.43% of
  0.77 V). Default vectorless power is 55.7057 mW at 0.77 V and 200 MHz;
- retain the reproducibility bundle under
  `artifacts/OpenROAD/{logs,reports,results}/asap7/resident_actor_tile_pnr_top/resident_detail_stem_2x2x2`.
  The reports include `6_report.json`, `6_finish.rpt`, final GDS/DEF/SPEF/netlist, timing/power
  summaries, and layout images. This is a checkpoint-exact two-tile characterization only—not a
  full-model area, latency, or activity-based power result;
- next resume point: use the expanded-memory host to regenerate and verify the complete 25-actor
  resident spike-vector graph, then record routed resources, timing, activity-based power, and
  latency on a scale-suitable ASIC platform. Do not substitute additional per-layer samples for
  this project-specification milestone or extrapolate any tile result to full-chip PPA.

### 2026-09-08 — exact XL 10-bin actor-DAG simulation completes

- exported the epoch-1 `EventSpikeSegXL` structure as `artifacts/ASIC_XL` and executed its exact
  44-actor integer DAG in Docker over ten consecutive 5 ms bins from
  `zurich_city_13_a/events.h5`; 428,367 retained input events produced one 440x640 `uint8`
  prediction after the complete 50 ms window;
- every actor output is routed to its documented successors within each bin, while membrane,
  adaptation, and temporal class-current state persist between bins. Four workers parallelize
  disjoint output-channel ranges without changing event/contribution order; a full-graph
  serial-versus-parallel equality gate passes;
- replaced Python-object neuron dictionaries with fixed-width NumPy state planes holding the
  same int32 membrane, int8 age, int32 amplitude, int32 bin tag, and valid bit. Four-worker
  Docker memory fell from an unsafe 28.84/30.61 GiB to about 1.98 GiB at the measured encoder
  point. Atomic per-bin checkpoints made the run restartable and were removed after success;
- total CPU-oracle time was 15,308.731 s (4.252 h), with 22,175,363,899 synaptic contributions,
  53,988,002 actor output spikes, and 45,516,001 summed per-actor maximum live entries. The final
  prediction and profile are
  `artifacts/RTL/profile/xl_epoch001_zurich_city_13_a_native_50ms_prediction.npy` and
  `artifacts/RTL/profile/xl_epoch001_zurich_city_13_a_native_50ms.json`;
- the prediction is a functional epoch-1 structural result, not an accuracy result: this sample
  lacked its rectification map and aligned label. It is also not RTL timing or energy evidence;
  the profile explicitly reports `power_activity_available: false`. Full RTL/gate switching
  activity and post-route power remain required;
- removed the obsolete GDrive prelink junctions, renamed the XL export from
  `ASIC_XL_epoch001` to `ASIC_XL`, and pruned OpenROAD from 5.917 GB to 0.89 GB. The retained
  revised two-tile result keeps final ODB/GDS/DEF/SPEF/netlist/SDC and compact reports/logs.

### Revised Q7.16/int32 two-tile OpenROAD result

- the current-precision ASAP7 `detail_stem` two-tile run is
  `resident_detail_stem_q7_16_acc32_2x2x2`: 18,018.2 um^2 standard-cell area in a 52,373.2
  um^2 core (34.4034%), 589.378 MHz reported fmax, +3,303.3 ps setup slack, and +38.2417 ps
  hold slack at the 5 ns constraint;
- setup/hold, max-slew, max-capacitance, max-fanout, detailed-route, and flow-error counts are
  zero. Default vectorless power is 700.516 mW at 0.77 V/200 MHz and worst VDD drop is
  49.2562 mV. These values supersede the old-precision two-tile implementation but remain a
  small-block default-toggle characterization, not XL/full-model power or inference energy.

### 2026-09-09 — XL synthesis continuation after ASIC_sol interruption

- At this continuation point, the active source was
  `C:\Users\stamir\Desktop\EventSpikeSeg` and its artifact junction resolved to the external
  `C:\Users\stamir\Desktop\EventSpikeSeg-artifacts` store. This was later migrated into the
  project-local `artifacts` directory as recorded below.
- Recovered six completed actor partitions plus attention. The interrupted `stem` log ended
  in Yosys `PROC_MUX`, expanding packed bitselwrite assignments; no synthesis process survived.
- Refactored the resident retinotopic population into constant-index generated neuron blocks.
  Each neuron retains its distinct accumulator, age and amplitude registers, with the same
  parallel completion, arithmetic widths, routing and handshake behavior. This does not
  serialize the mechanism, reduce the model, or establish new numeric accuracy claims.
- Validation: all 16 resident cocotb runner cases pass; all 41 ASIC RTL tops and the external
  SRAM actor compile. A saved old/new comparison passes 2,000 deterministic randomized cycles
  at production state widths, checking every output and all accumulator/age/amplitude state.
  It exercises dense and sparse contributions, invalid destinations, reset, completion and
  backpressure. Evidence is in `artifacts/ASIC_XL/resident_codegen_validation`.
- Resumed the exact existing 44-actor 2x2 partition synthesis procedure in named Docker
  container `eventspikeseg-xl-partitioned-resume`. Its source-signature gate invalidates actor
  logs affected by the RTL change. The container is retained on exit for status/log inspection.
  Completion remains to be verified in `ASIC_XL/partitioned_synthesis_2x2/summary.tsv`.
- This is an actor-tile structural synthesis gate, not full-native RTL simulation, technology
  mapping, full-chip PPA, or activity-based inference energy. The completed ten-bin integer
  profile remains functional reference evidence only.

### 2026-09-09 — bounded parallel XL synthesis enabled

- The generated-neuron stem completed with zero structural problems: 953.12 user CPU seconds,
  7.91 system seconds, 7256.65 MB peak memory. Eight actor partitions passed before switching
  from the sequential runner; only the incomplete `enc1.pointwise` work was restarted.
- Added `scripts/synthesize_asic_partitions.py` for prepared exports. Three independent Yosys
  jobs run concurrently with an 8 GiB per-process address-space limit. Failed jobs retry
  sequentially at 24 GiB after all parallel jobs exit. The Docker container has a 26 GiB
  memory/swap-total cap. These limits bound aggregate use; the larger retries may use one CPU.
- Existing source signatures are compatible: the three-actor reuse smoke test passed without
  resynthesis. Each job owns distinct files; one coordinator atomically rewrites summary.tsv.
  A file lock prevents simultaneous parallel-runner instances from owning this export.
- Active container: `eventspikeseg-xl-parallel`; previous sequential container is stopped.
  Invocation inside the verification image: `python -u scripts/synthesize_asic_partitions.py
  /workspace/artifacts/ASIC_XL --workers 3 --worker-memory-gib 8 --retry-memory-gib 24`.
- A task heartbeat checks every ten minutes and reports verified completion or actionable
  failure. Parallel-pass FAIL rows may be awaiting the scheduled sequential retry.

### 2026-09-09 — XL partition synthesis stopped by artifact I/O failure

- Container `eventspikeseg-xl-parallel` exited with code 1 at 19:19:31 UTC. After the
  24 GiB `bridge23` retry failed, the coordinator could not write `summary.tmp`:
  `OSError: [Errno 5] Input/output error`. Docker reports no container OOM kill.
- Audited all 45 distinct summary rows. Nineteen actor PASS results plus attention have
  matching source/top SHA-256 signatures and successful Yosys completion markers, with
  no ERROR lines. No recorded PASS failed this audit. Twenty-five actors remain unresolved;
  FAIL rows include both exhausted retries and actors whose larger-memory retry never ran.
- Confirmed completed 24 GiB failures include enc2.pointwise, enc2_extra.pointwise,
  down3.pointwise and bridge23. Previous errors were allocation failures, separate from
  the final status-file I/O exception. The host C drive had about 8.06 GB free when checked;
  the root cause of the I/O failure has not been established.
- The automatic monitor is paused because this run has exited. Preserve completed results.
  Before another run, diagnose Docker bind-mount/storage writes and reduce synthesis memory
  demand or provide a larger-memory host for failed actors. No full-chip PPA or XL energy
  result was produced by this structural tile synthesis run.

### 2026-09-10 — synthesis storage and elaboration failures fixed

- Diagnosed the status-file I/O failure as host disk exhaustion caused by WSL crash capture.
  Ten `_usr_bin_yosys-6.dmp` files occupied 142,669,914,104 bytes (132.9 GiB); the final
  20.47 GB dump completed one second before the failed `summary.tmp` write. Removed exactly
  those ten dumps after recording their paths, sizes, and timestamps in
  `artifacts/ASIC_XL/yosys-crash-dump-cleanup-20260910.json`. Free C-drive space increased
  from about 7.5 GiB to about 140 GiB, and an artifact create/read/rename/remove probe passed.
- Added a guarded verification image whose post-exec preload constructor applies
  `PR_SET_DUMPABLE=0` inside Yosys. This is necessary because WSL's piped crash handler ignored
  `RLIMIT_CORE=0` in a controlled probe. A guarded SIGABRT probe reported no core and created
  no WSL dump. The ordinary zero core-size limit remains enabled as a second boundary.
- Reworked resident convolution current formation into constant-index elaboration-time tap
  chains and split ordinary/retinotopic resident state into constant-index neuron processes.
  The actor remains fully parallel, keeps every physical neuron state distinct, and preserves
  the original signed 32-bit contribution order and fixed-point commit arithmetic.
- Validation passes: 16 resident cocotb cases, all 41 ASIC tops plus the external-SRAM actor,
  27 runner recovery tests, and lint. Saved old/new tests covered 10,000 randomized ordinary
  population cycles and 2,000 convolution vectors across five standard/grouped/depthwise,
  boundary, stride/dilation, and saturation configurations. The prior retinotopic comparison
  covered 2,000 randomized cycles including all resident state words.
- `enc2.pointwise`, which previously exhausted a 24 GiB virtual-address-space limit, now
  completes at the 8 GiB limit in 158.6 seconds wall time with a 1,730.54 MB Yosys peak and
  zero structural problems. This validates the elaboration-memory fix on the known blocker.
- Started full guarded recovery in `eventspikeseg-xl-recovery` with three 8 GiB workers and
  serial 24 GiB fallback. Source-bound journals, completion markers, atomic summary writes,
  bounded storage retries, and final failure classification protect resumability. A ten-minute
  heartbeat verifies progress, crash-dump absence, and final signatures before reporting.

### 2026-09-10 — XL synthesis resumed as 1x1 spatial partitions

- Stopped the first guarded recovery intentionally when the 2x2 `enc3_extra.standard` serial
  retry reached about 22.6 GiB while Yosys was still deriving the convolution. No new WSL crash
  dump or artifact-storage failure occurred.
- Confirmed the remaining pressure is inherent elaboration scale: the dense 128-to-128 3x3
  actor creates 512 destinations and 589,824 conditional 32-bit addition stages in a 2x2
  partition. Packing the intermediate sum vector removed inferred-memory lowering but could
  not remove those nodes. The 8 GiB 2x2 and 1x1 probes both stopped cleanly at their address-space
  boundary.
- Switched the standard recovery configuration to 1x1 spatial partitions. This retains all
  channels and the complete retinotopic peer group at one coordinate while reducing the worst
  convolution to 147,456 stages. Three 8 GiB workers handle ordinary actors in parallel;
  memory-limited actors retry one at a time at 16 GiB inside a 26 GiB guarded container.
- Started `eventspikeseg-xl-recovery-v2`. The early live summary reached 20 PASS rows (attention
  plus 19 actors), with no failures or storage errors. Completion must be audited from
  `ASIC_XL/partitioned_synthesis_1x1/summary.tsv`; these results are spatial-partition synthesis
  evidence and must not be reported as full-chip PPA or exact full-model energy.
- `eventspikeseg-xl-recovery-v2` completed with exit code 0. All 44 distinct actors plus the
  attention block report PASS; five dense actors that exceeded the 8 GiB parallel limit passed
  their serial 16 GiB retries.
- A fresh guarded resume audit regenerated every 1x1 top and reported REUSE for all 44 actors,
  proving that each saved log has the current source/top signature, an `End of script` marker,
  and no `ERROR:` line. The audited summary contains 45 PASS rows and no duplicate actor, and
  the WSL crash directory contains no Yosys dump. This is checkpoint-exact 1x1 spatial-partition
  synthesis evidence only, not full-chip PPA or exact full-model energy.

### 2026-09-11 — XL representative physical design started

- Confirmed that the completed XL result stops at structural partition synthesis. Existing final
  GDS/DEF/SPEF and OpenROAD power reports belong to earlier small `detail_stem` prototypes; their
  power is vectorless and cannot be used as XL or representative-event power.
- Added an ASAP7 ORFS configuration for the checkpoint-exact XL `enc3.pointwise` 128-to-128
  pointwise actor at one spatial coordinate. This actor provides meaningful XL datapath coverage
  while remaining substantially smaller than the 14.18 GiB structural-synthesis stress actors.
- Started guarded container `eventspikeseg-xl-enc3-pointwise-pnr` with a 5 ns clock, 35% target
  core utilization, extracted timing/DRC checks, and a 28 GiB container limit. The flow will emit
  per-partition GDS/DEF/SPEF/netlist and vectorless power if routing closes. Representative-event
  VCD/SAIF power and any full-chip composition remain separate required work.
- Added selective `enc3.pointwise` input/output capture to the exact integer DAG, including
  checkpoint/model/event SHA-256 provenance, deterministic busiest-coordinate selection, atomic
  per-bin resume state, ten-bin RTL output checking, and bounded VCD scopes. Three focused trace
  tests pass and the changed Python files are lint-clean. The capture replay is queued after
  OpenROAD because the earlier completed profile contains aggregate counts only and cannot
  reconstruct ordered actor vectors.

### 2026-09-11 — routed XL partition and artifact-store migration

- The full checkpoint-exact XL `enc3.pointwise` 1x1 actor completed structural synthesis, but
  two ASAP7 technology-mapping attempts exceeded the 28 GiB protected container limit. The full
  `enc3.depthwise` actor reached detailed routing; both 14-thread and 6-thread attempts exceeded
  the same limit at about 80%, showing that the detailed-routing database, rather than thread
  count alone, dominated memory.
- The smaller full checkpoint-exact XL `enc1.depthwise` 1x1 actor completed ASAP7 synthesis,
  placement, clocking, detailed routing, extraction, and stream-out. The checked report gives
  +3656.58 ps setup slack, +45.8272 ps hold slack, 744.37 MHz reported fmax, 10159.8 um^2
  standard-cell area, and 435.888 mW vectorless power. Final GDS, DEF, SPEF, and netlist exist.
  These are per-partition figures, not full-chip PPA or representative-event power.
- The user replaced the former `artifacts` junction with a real project-local directory. After
  stopping the exact activity replay at its completed-bin checkpoint, all missing or newer files
  from `C:\Users\stamir\Desktop\EventSpikeSeg-artifacts` were merged into
  `C:\Users\stamir\Desktop\EventSpikeSeg\artifacts`. The synthesis launcher now defaults to
  this project-local directory; `EVENTSPIKESEG_ARTIFACTS_DIR` remains an optional override.

### 2026-09-11 — checkpoint activity verification found and repaired PLIF overflow

- Exact ten-bin `enc3.pointwise` RTL replay exposed a real state-retention mismatch at bin 3.
  Both resident PLIF implementations held the Q15.16 membrane times Q0.23 beta product in a
  32-bit SystemVerilog `integer`, although the operation needs 48 signed bits. The product now
  uses `longint signed` through rounding and shifting in both implementations.
- The activity runner now removes stale JUnit output and requires a nonempty cocotb result with
  zero failures or errors before it reports a verified VCD. Focused XML-result tests, lint, and a
  checkpoint-scale resident-state cocotb regression pass.
- The repaired saved-trace replay has passed the former bin-3 failure and continues in
  `eventspikeseg-xl-enc3-vcd-verify-fix`; it reuses the completed exact DAG trace. The original
  activity VCD is invalid evidence and must not be used.
- The RTL change invalidates all 44 prior structural-synthesis signatures and the routed
  `enc1.depthwise` result. Resume-mode signature checks correctly classify 0/44 actor results for
  reuse, so the next synthesis run must rebuild all actors. The earlier layout and vectorless
  figures remain historical pre-fix results until the corrected RTL is rerouted.

### 2026-09-12 — corrected XL synthesis complete and beta48 layout started

- `eventspikeseg-xl-44-synth-beta48` completed with exit code 0. All 44 corrected 1x1 actors
  passed; five memory-heavy actors passed their bounded serial 16 GiB retries. The summary has
  45 PASS rows including attention, every log has an `End of script` marker and no `ERROR:` line,
  and a fresh resume audit reported REUSE for all 44 current source/top signatures.
- Added a separate ASAP7 variant `xl_enc1_depthwise_1x1_beta48`, preserving the earlier pre-fix
  physical result as historical evidence. Started guarded container
  `eventspikeseg-xl-enc1-depthwise-pnr-beta48` with a 20 GiB memory limit, eight CPUs, no core
  dumps, project-local artifacts only, a 5 ns clock, and the existing 35% utilization target.

### 2026-09-12 — beta48 layout, gate equivalence, and event-activity power complete

- The corrected `enc1.depthwise` beta48 route completed with final GDS/DEF/ODB/SPEF/netlist/SDC,
  zero detailed-route DRC and antenna violations, +3366.98 ps setup WNS, +47.67 ps hold WNS,
  612.363 MHz reported fmax, and 12,423.9 um^2 standard-cell area. Its 855.057 mW vectorless
  result is retained only as the default-toggle comparison.
- A saved-trace mismatch at bin 4 was an oracle defect rather than an RTL defect. The sparse DAG
  trace omitted idle-bin firings, while the governing resident contract thresholds/resets and
  beta-advances every destination on every 5 ms completion. The resident combined-accumulator
  oracle now derives expected vectors from the saved input bitmaps. Exact RTL replay passes all
  ten bins with 108 output spikes and trace digest
  `d38500dfd912d81e49e30a80fb23698291bb88f2ab042a461c09699d4a8fa4fd`.
- The routed standard-cell netlist passes all ten exact vectors in 33 simulated cycles with no
  X/Z, tag, data, or error mismatch and produces a 47,978,356-byte gate-scoped VCD. Icarus cannot
  perform a complete OpenSTA SDF replay for this ASAP7 library: it rejects interconnect,
  conditional, escaped-instance, and timing-check constructs. The reproducible flow therefore
  uses post-route functional gate simulation for activity and keeps extracted OpenSTA/SPEF as the
  timing authority; simulator-only cell copies initialize unsupported timing notifiers.
- OpenROAD mapped all 372,491 reported pin activities from that VCD with zero unannotated pins.
  Routed activity power is 3.062088275 mW total: 1.405026997 mW internal, 1.645694370 mW
  switching, and 0.011367122 mW leakage. This is checkpoint-exact evidence for one selected real
  coordinate of one routed 1x1 `enc1.depthwise` partition, not full-actor or full-chip power.
- Focused trace/power regression contains 16 passing tests, and the touched Python files are
  Ruff-clean. All evidence is project-local under
  `artifacts/ASIC_XL/activity/enc1_depthwise_1x1_beta48_gate`.

### 2026-09-13 — native XL full-chip elaboration reaches host memory limit

- A checkpoint-bound preflight verified the current beta48 model/top digests, all 44 permanent
  actors, 49,610 resident 8x8/boundary tiles, 78,707,200 logical PLIFs,
  2,916,390,400 resident-state bits, and all 45 PASS rows in the current 1x1 partition journal.
- Guarded Yosys full-top hierarchy/elaboration attempts exited 137 at 8, 16, and 24 GiB. The
  24 GiB attempt reached 23.97 GiB while still deriving the native temporal-readout/top hierarchy;
  it did not produce a complete structural netlist.
- OpenROAD full-chip placement/routing was not started because its required complete native
  netlist does not exist. Starting from a reduced actor, SRAM substitute, truncated dimensions,
  or an extrapolated tile composition would violate the active resident-state architecture and
  full-chip PPA reporting gate.
- Machine-readable preflight, per-tier logs/status, and the capacity decision are in
  `artifacts/ASIC_XL/full_chip_layout`. The next valid execution needs a host that can give Yosys materially more
  than 24 GiB, after which the flow may proceed to complete placement, routing, extraction,
  timing, and representative-activity power.

### 2026-09-14 — exact hard hierarchy and full native simulation resumed

- Replaced the full native readout's monolithic elaboration with an exact 55x80
  grid of 8x8 resident score tiles. This preserves 440x640 output, all 281,600
  pixels, 11 class scores per pixel, ten-bin accumulation, and row-major output.
- The first 8x8 readout leaf exposed a Yosys multiwrite-memory priority explosion.
  Packed score storage with one constant writer per score preserves saturation,
  strict-greater argmax ties, reset, per-pixel clear, and ready/valid behavior.
  Focused cocotb passed; structural Yosys completed in about five minutes with
  zero inferred memories and a 3649.98 MB peak.
- Generated 235 exact actor hard-macro RTL variants covering all 49,610 actor
  tiles. Variant identity includes output shape, clipped receptive halo, boundary
  offset, true stride/padding/dilation, and tile origin. The hard-hierarchy
  catalog conserves 49,610 actor tiles plus 4,400 logical 8x8 readout tiles:
  54,010 nominal tiles and 281,600 readout pixels. Its active physical readout
  implementation groups four exact 4x4 macros per logical tile, giving 17,600
  readout macros, 67,210 physical instances overall, 236 unique masters, and
  708 required LEF/GDS/Liberty views.
- The exact packed-register 8x8 readout master passed structural Yosys, but its
  ASAP7 ORFS technology mapping reached 11.99/12 GiB while full simulation and
  training were active. The run was stopped before OOM, so it produced no routed
  8x8 physical views. The 8x8 result remains exact structural and capacity
  evidence; the active readout physical master is the exact packed 4x4 variant,
  whose ORFS run was launched with a 10 GiB guard.
- Generated the fixed macroized native assembly from the catalog and instance map. Forty-four
  fixed actor wrappers select all 235 exact actor masters by compile-time output/halo/offset
  geometry, preserve lockstep ready/valid and completion tags, and reconstruct every global
  channel-major bitmap. The fixed readout wrapper instantiates 17,600 exact 4x4 leaves and retains
  global row-major prediction and frame-completion arbitration. A digest-bound JSON preflight
  conserves 49,610 actor macros, 78,707,200 actor PLIF outputs, 113,717,706 receptive-halo input
  bits, 4,400 logical readout tiles, 281,600 pixels, and 67,210 physical instances. Soft routing,
  joins, attention, and the native 440x640 interface are unchanged. Physical assembly remains
  gated by the missing catalogued LEF/GDS/Liberty views.
- Epoch-11 complete 50 ms native simulation initially exceeded 8 and 14 GiB
  because consumed graph streams remained live for the whole bin. Consumer-count
  reclamation and zero-offset list reuse preserve computation while releasing
  intermediates. The corrected four-worker, 16 GiB run later completed all ten
  bins; the 2026-09-15 entry below records its audited result.
- Training remains active and reached epoch 19/80; epoch 18 is the latest complete
  checkpoint observed. Physical work remains bound to the epoch-1 provisional
  export until a final checkpoint is selected.

### 2026-09-15 — exact 50 ms native XL simulation completed; 4x4 readout ORFS retried

- The epoch-11 exact 440x640, 44-actor integer DAG completed all ten 5 ms bins
  with exit zero and no OOM under four CPUs and a 16 GiB limit. Host runtime was
  27,619.365 seconds. It processed 428,367 input events, 225,609,186 actor input
  events, 102,959,737 actor output spikes, and 33,653,694,655 synaptic
  contributions.
- The saved uint8 prediction covers all 281,600 pixels and has SHA-256
  `679beb38969b94bffd9c2c78f4789ca7a3eb67ffd7f59f560da0109bf9b792d7`.
  The checkpoint, model-spec, and event digests are recorded with the profile.
  The completed container and obsolete resume files were removed after audit.
- The evidence is a complete 50 ms unrectified sample, not a rectified full
  validation sequence, hardware-cycle simulation, or publication-grade power
  result. It is retained for later full-graph activity mapping.
- The first exact packed 4x4 readout ORFS attempt was OOM-killed at its 12 GiB
  cgroup limit during ABC. After the native simulation released memory, the
  unchanged target was restarted with a 20 GiB memory limit, 40 GiB swap limit,
  and 8 CPUs. Audit then found that external retry used the generic physical
  top-cell name `resident_readout_tile_pnr_top`, which cannot bind to the
  catalogued macro `xl_hm_readout__out_4x4`; it was stopped and journaled before
  wasting more route time. RTL generation, the ORFS `DESIGN_NAME`, catalog,
  blackbox, and port contract now use the exact catalog name. The corrected
  resumable run is active at the same resource limits. Actor-master generation
  stays sequential after this view is validated and staged.


### 2026-09-15 — exact readout physical hierarchy reduced to 2x2 after 4x4 OOM

- The catalog-identity-correct 4x4 ASAP7 ORFS run was OOM-killed during ABC at its 20 GiB cgroup limit; no physical view was staged. The readout physical master is now `xl_hm_readout__out_2x2` while the logical model remains exact 440x640.
- Regenerated the catalog, 120,010-row instance map, blackboxes, view bindings, master-generation table, fixed macro wrappers, macroized top, and conservation preflight. The hierarchy retains 4,400 logical 8x8 tiles, subdivides each into sixteen 2x2 leaves, instantiates 70,400 readout macros, and covers all 281,600 pixels exactly once.
- The wrapper tile selector is now geometry-derived and 17 bits wide for 70,400 leaves. Actor counts, 78,707,200 PLIF identities, receptive halos, graph routing, frame behavior, and row-major predictions are unchanged. The 236 unique masters still require 708 LEF/GDS/Liberty files before full-chip placement.

### 2026-09-15 — first exact hard-macro view accepted; actor characterization started

- The exact 2x2 readout completed placement, CTS, routing, extraction, timing,
  and GDS with zero final DRC and antenna violations. Extracted setup slack is
  +1252.43 ps, hold slack is +48.5815 ps, and reported fmax is 266.839 MHz.
- ORFS abstract generation initially followed a stale read-only SDC prerequisite.
  The resumable runner now validates completed route evidence and calls
  `do-generate_abstract` directly. It also accepts ORFS quoted Liberty cell names.
  Hash-verified LEF, GDS, and Liberty are staged for `xl_hm_readout__out_2x2`,
  completing the first master and 3 of 708 required view files.
- Started the lowest-complexity exact actor master, clipped-boundary
  `detail2.vertical` 8x8 output with a 9x8 halo, under the same 20 GiB/40 GiB/8
  CPU limits. Hard-macro work remains sequential while training runs.

### 2026-09-15 — exact actor hierarchy changed to adaptive physical leaves

- The first exact 8x8 `detail2.vertical` actor master exhausted its 20 GiB ORFS
  limit during technology mapping, so no actor view was accepted from that run.
- Regenerated the hard hierarchy with a deterministic conservative policy tied
  to static convolution complexity and the passing exact 1x1 synthesis inventory:
  seven light depthwise actors use 4x4 leaves, fourteen moderate actors use 2x2
  leaves, and twenty-three dense actors use 1x1 leaves. Boundary leaves remain
  globally positioned and clipped with exact stride, padding, dilation, and halo.
- The unchanged 49,610 logical 8x8 actor tiles now contain 952,720 physical actor
  leaves: 80,320 at 4x4, 335,600 at 2x2, and 536,800 at 1x1. Together with 70,400
  exact 2x2 readout leaves, the native hierarchy contains 1,023,120 physical
  instances and 275 unique masters requiring 825 LEF/GDS/Liberty files.
- Dependency-free conservation and interface preflight passes: 44 actors,
  78,707,200 PLIF identities, 440x640 geometry, 281,600 readout pixels, every
  logical-to-physical tile grouping, every receptive halo, all soft graph modules,
  and the native top interface are preserved. The accepted readout contributes
  3 of 825 views. Obsolete failed 8x8 journal entries are archived outside the
  current master set and cannot block the resumable driver.

### 2026-09-15 — feasible hierarchy and representative full-model estimator

- The exact `detail2.vertical` 4x4 actor subsequently exhausted its 20 GiB
  guarded ORFS allocation during ABC. It produced no accepted netlist or physical
  view. The layout policy now prohibits 4x4 actors and uses 2x2 leaves for all 21
  depthwise/moderate actors and 1x1 leaves for all 23 dense actors.
- Regenerated the catalog, 1,264,000-row instance map, master-generation table,
  blackboxes, view bindings, wrappers, macroized top, and conservation preflight.
  The exact hierarchy has 1,193,600 actor leaves (656,800 at 2x2 and 536,800 at
  1x1), 70,400 readout leaves, 273 unique masters, and 819 required physical
  views. All 44 actors, 78,707,200 PLIF identities, 2,916,390,400 state bits,
  281,600 output pixels, and the original soft graph are conserved.
- Added `asic/xl_representative_ppa.yaml` and
  `scripts/estimate_xl_full_model_ppa.py`. The estimator combines exact hierarchy
  and graph inventories, the completed native ten-bin activity profile, routed
  `enc1.depthwise` activity power, and routed readout area/leakage. Per-actor and
  interconnect inventories plus the aggregate result are written under
  `artifacts/ASIC_XL/full_model_estimate/`.
- The first central proxy is 358,175.19 mm^2 standard-cell area, 3.122 mJ actor
  dynamic energy per 50 ms sample, and 258.26 W average power at 20 predictions/s.
  The configured 0.5x..3.0x band is a sensitivity range. This is useful early
  feasibility evidence, but only one actor has routed activity power and the
  top-level clock/routing/interconnect power and wirelength are still absent.
- The existing layout check is confirmed as a complete structural/conservation
  preflight. Physical layout evidence is complete only for the exact 2x2 readout
  master and a representative `enc1.depthwise` 1x1 partition; no top-level
  floorplan, placement, routing, or extracted full-chip result exists yet.
- Started the common-interior exact 2x2 `detail2.vertical` master
  `xl_hm_actor__detail2_vertical__out_2x2__halo_4x2__offset_0_0` in
  `eventspikeseg-hm-c7859b999d` with 20 GiB memory, 40 GiB swap, and 8 CPUs.
  This is the next representative calibration and a required full-layout master.
- The 2x2 master reached 70% of the first detailed-routing optimization, peaked
  at 20,980,348 KiB, and was OOM-killed. Its log and journal are preserved; only
  the stopped container was removed.
- Regenerated the exact hierarchy with 1x1 leaves for every actor: 3,163,600
  actor instances plus 70,400 readout instances, 3,234,000 total instances, 335
  unique masters, and 1,005 required views. Structural/conservation preflight
  passes and the representative estimator was refreshed. The central estimate
  is unchanged because it scales logical work and state rather than partition
  boundaries.
- Moved the required 182-file epoch-11 simulation export intact from the stray
  `artifacts/ASIC_XL_epoch011_sim` sibling to
  `artifacts/ASIC_XL/checkpoint_exports/epoch011_sim`. The contents were not
  deleted or merged with the different provisional epoch-1 constants.
- Started the common-interior 1x1 `detail2.vertical` master
  `xl_hm_actor__detail2_vertical__out_1x1__halo_3x1__offset_0_0` with the same
  20 GiB memory, 40 GiB swap, and 8-CPU guard.
- The common-interior 1x1 `detail2.vertical` master completed and staged valid
  LEF/GDS/Liberty. It has +3511.53 ps setup slack, +49.886 ps hold slack,
  671.833 MHz reported fmax, 5,478.9 um^2 standard-cell area, 193.208 mW
  vectorless power, and zero reported timing violations.
- The refreshed representative estimate uses routed area/leakage for
  `enc1.depthwise` and `detail2.vertical`: 359,018.34 mm^2 central standard-cell
  area and 258.86 W central average power at 20 predictions/s. Six of 1,005
  required physical views are present; routed actor-population coverage is 2/44.
- Started the common-interior 1x1 `detail2.horizontal` master
  `xl_hm_actor__detail2_horizontal__out_1x1__halo_1x3__offset_0_0` under the
  established 20 GiB/40 GiB/8-CPU guard.
- The common-interior 1x1 `detail2.horizontal` master completed and staged valid
  LEF/GDS/Liberty. It has +3399.8 ps setup slack, +48.181 ps hold slack,
  624.923 MHz reported fmax, 5,629.28 um^2 standard-cell area, and 194.046 mW
  vectorless power.
- The representative estimate now uses three routed actor populations and counts
  staged views directly. Its central proxy is 359,903.83 mm^2 and 259.49 W at
  20 predictions/s; 9 of 1,005 physical views are present and actor-population
  route coverage is 3/44.
- Started the common-interior 1x1 `detail1.depthwise` master
  `xl_hm_actor__detail1_depthwise__out_1x1__halo_3x3__offset_0_0` under the same
  resource guard.
- The common-interior 1x1 `detail1.depthwise` master completed with +3452.41 ps
  setup slack, +50.7703 ps hold slack, 646.167 MHz fmax, 6,218.14 um^2 area,
  and 439.23 mW vectorless power. The estimator now covers 4/44 routed actor
  populations and 12/1,005 staged views.
- The first `down2.depthwise` launch stopped immediately because the ORFS actor
  source list omitted `retinotopic_mechanism_update.sv`. The runner now includes
  that checked-in dependency; the same exact master was relaunched.

### 2026-09-20 — isolated primitive area and activity-power characterization started

- Completed a DRC-clean extracted ASAP7 route for one ordinary resident PLIF
  cell. The design has 238.762 um^2 standard-cell area, 921.968 MHz reported
  fmax, positive setup/hold slack, and 0.205748 uW TT leakage.
- Generated a deterministic ten-bin cycle trace and used its VCD to drive
  OpenSTA power through the routed netlist. Dynamic energy is 33.8188 pJ per
  PLIF bin update. At ten bins per prediction and 20 predictions/s, multiplying
  the exact 60,544,000 ordinary-cell count gives 0.4095 W dynamic, 12.4568 W
  leakage, and 14,455.61 mm^2 cell area before top-level physical overhead.
- Completed a DRC-clean extracted route and 128-vector VCD power run for one
  fully connected 3x3 convolution output containing nine hardwired synapse
  terms. The block has 28.7372 um^2 standard-cell area and 62.2855 uW dynamic
  power at one new vector per 5 ns. Normalized values are 3.19302 um^2,
  0.0346031 pJ per bin evaluation, and 2.37704 nW leakage per term.
- Added `scripts/inventory_xl_physical_primitives.py` output fields for both
  measurements and the exact 9,125,811,200 synapse-term and 60,544,000 ordinary
  PLIF multipliers. These are early component totals; actor-specific routed
  samples remain the better calibration for adder depth and local wiring.
- Stopped and removed a partial four-channel experiment that enabled adaptation
  and inhibition simultaneously because no model actor uses that combination.
  The next valid isolated runs keep the inhibition-only stem and adaptation-only
  encoder mechanisms separate.


## Digital ASIC work — paused 2026-09-23

Digital layout is paused by the user for the analog experiment. Preserve all ASIC and ASIC_XL artifacts. Resume evidence is in artifacts/ASIC/digital_pause_20260923: original container configurations, workers, journal, logs, and hashes of durable stage outputs.

Three stopped containers exist in Created state. All three original containers were removed during shutdown by existing cleanup paths and were recreated, without starting them, from saved image IDs, commands and mounts. Durable outputs were bind-mounted on the host and are preserved. The 2f1919ca16 journal had changed to OOM; user-requested stop exit codes must not be treated as new OOM evidence. No live process memory is saved: resume from the last verified completed stage, rerunning an interrupted stage as needed. Check partial output validity and make dependencies before restart. Do not blindly run the worker wrapper, which rewrites inputs and removes containers. Validate route reports and stage physical views with existing helper functions before marking complete.

Digital and XL training/physical runs must not automatically restart. Analog failure triggers a user decision about fallback.

## Archived active log — historical, not current execution instructions

# Active work and resume order

## 2026-09-22 — Bounded 140k mechanism checks (complete)

- Reused existing inhibition/adaptation physical checkpoints and existing block directories. No whole-model simulation, new synthesis, or rerouting was performed. The 120-second per-stage limit was not increased.
- Accepted 9/9 activity cases with zero unannotated pins. Six cases use 64 midpoint samples; the previously timed-out cases completed as shorter smoke proxies: inhibition 16 samples, energy64 8 samples, energy128 4 samples. Those three remain global-route estimated parasitics; five adaptation cases use detailed-route parasitics; penalty_lane remains global-route. Three penalty-reducer roles share one physical design.
- Mechanism-only scaled proxies: 0.010328 W dynamic and 41.909 W leakage at 200 bins/s, using exact 140k counts. The 4/8/16-sample energies are especially uncertain. These omit the resident state/learned-beta update circuitry around mechanism populations as well as graph/control, top-level clocks/routing, and measured spike sparsity. They are not full-chip power.
- Exact 140k hard-hierarchy inventory is conserved under `artifacts/ASIC/hard_hierarchy/`: 25 actors, 54 graph edges, 30,976,000 PLIF identities, 1,579,600 physical instances, 160 unique masters. All 160 master RTL files are generated. Layout progress: 18 masters complete (54/480 views); all nine `detail_stem` and all nine `detail1.standard` are done. Overnight 8 GiB parallel sweep OOM'd most remaining masters (~128); that 8 GiB orchestrator was stopped. `stem` failed detailed route at 12 GiB (peak ~12.0 GiB) and is retrying at 16 GiB. `enc1` still needs exclusive ≥20 GiB. Prefer 12–16 GiB retries over more 8 GiB attempts. Design constraints unchanged. Macroized assembly not yet generated; full-chip layout incomplete.
- Report: `artifacts/ASIC/primitive_characterization/base_140k_inventory/GATE_RESULTS.md`; detailed audit: `mechanism_gate_results.json`, `mechanism_gate_manifest.json`, and `mechanism_gate_status.json` in the same directory.

## Current ASIC target policy — 2026-09-21

All primary ASIC layout, block simulation, power, area, timing, and inventory work is based on **EventSpikeSeg140k v8, epoch 80, seed 17**: six classes, 440x640, 25 permanent PLIF actors, 54 graph edges, 30,976,000 resident PLIF identities, and 143,824 deployed synaptic weights. Primary exports/results live under `artifacts/ASIC/`; the latest accepted small gate-simulation results are in `artifacts/ASIC/primitive_characterization/`.

**EventSpikeSegXL is secondary/reference work.** Preserve useful accepted XL GDS/LEF/Liberty views, final routed ODB/DEF/netlist/SDC/SPEF files, checkpoint-specific constants, hierarchy catalogs/instance maps/preflight, and validation/power reports. Keep them under `artifacts/ASIC_XL/` and their existing named OpenROAD result directories. Retain the latest useful unfinished-run database and failure summaries; redundant intermediate databases and rebuildable simulation binaries need not be retained. Never relabel XL measurements or its 44-actor inventory as 140k results. Reuse an XL physical view for 140k only after proving matching RTL, constants, geometry, interfaces and constraints.

XL physical expansion remains paused behind 140k work. Preserve independent XL training and checkpoints. Neither model has a completed full-chip layout; existing routed blocks and structural hierarchy data must be labeled accordingly. Current work uses small per-block simulations and extracted-layout measurements; whole-model simulation remains retired. Historical entries below retain their original model and date and do not change this priority.


## 2026-09-21 — Simple layout/block-simulation milestone (latest)

User requested small steps, storage cleanup, and reuse of layouts for per-block simulation/power rather than prolonged full-model simulation and repeated physical retries.

- Removed 16.44 GiB of redundant OpenROAD database checkpoints and compiled simulation executables. Final views, all reports, latest unfinished-run databases, source RTL and training/checkpoint data are preserved; deletion manifests are under `artifacts/ASIC/`.
- Reused the 140k ordinary-PLIF and conv9 final layouts. Post-route functional gate simulations passed 65 and 255 output-snapshot checks; extracted-SPEF power has zero unannotated pins for both.
- Current compact results: `artifacts/ASIC/primitive_characterization/base_140k_inventory/GATE_RESULTS.md` and `gate_results.json`. These supersede the corresponding input-only power measurements for this workload, not all other blocks or the entire model.
- Prior PLIF annotation covered 116 pins with 12,869 unannotated; the old 2.013376 W subtotal must not be presented as validated full-chip power.
- Full 25-actor layout remains incomplete. Existing GDS files are isolated blocks. Readout now passes 49 gate-level reference checks after correcting pre-edge versus post-edge testbench sampling. Its existing layout supplied extracted power; 45,229 pins have VCD activity and only the two verified-zero coordinate outputs are unannotated. RTL and physical files were unchanged.
- XL training was observed running in `eventspikeseg-train-dsec-xl-run-0abd58c1b591` and was not interrupted. No ASIC container remains running from this milestone.

Read this after `project_spec.yaml`, `docs/AGENTS.md`, `docs/ARCHITECTURE.md`, and
`docs/DECISIONS.md`. Update it whenever a long-running stage starts, completes,
fails, or changes the next valid stage. Detailed history belongs in
`docs/PROGRESS.md`.

## Current processes

### EventSpikeSeg140k full-model ASIC implementation

- State: primary active physical target as of 2026-09-20. Use the canonical
  epoch-80 seed-17 six-class checkpoint export in `artifacts/ASIC/`; keep all
  XL estimates and views separate.
- Exact inventory: 25 permanent PLIF actors, 54 graph edges, 30,976,000 direct
  register/latch-resident PLIF identities, 143,824 deployed weights,
  3,730,918,400 expanded actor synapse terms per dense bin, and 27,033,600
  readout terms per dense bin.
- Isolated mechanism/PLIF/conv/readout gate checks are complete for existing
  blocks. Hard-hierarchy catalog conserved with 160 masters and all master RTL
  generated; physical views 27/480 after all nine `detail_stem` masters completed
  ASAP7 route and abstract generation.
- Active ORFS: three parallel `detail1.standard` masters at 8 GiB / 5 CPUs via
  `scripts/run_140k_hard_macro_parallel.py` / `_run_one_140k_hard_macro_orfs.py`;
  state in `artifacts/ASIC/hard_hierarchy/orfs_state/`. XL training remains paused.
- Reproducible results and capacity multiplication:
  `artifacts/ASIC/primitive_characterization/base_140k_inventory/`.
- Full-model layout is not complete. The isolated PLIF footprint multiplied over
  all 30,976,000 state identities is a capacity bound of 46,647.068 mm^2 of die
  footprint before mechanism variants, synapses, clock, power, and routing.

### EventSpikeSegXL training

- State: paused by user on 2026-09-22 to free host RAM/CPU for parallel 140k
  hard-macro layout. Do not resume without explicit authorization.
- Prior container `eventspikeseg-train-dsec-xl-run-62c318acc6b4` was stopped.
- Resume later from the latest durable XL checkpoint under
  `artifacts/model_checkpoints/dsec_XL/`.

### XL full-chip physical implementation

- State: paused as a secondary/reference target while the 140k base model is the
  primary physical target. The exact 1x1 `down2.depthwise` route completed after adding its missing
  retinotopic-mechanism RTL dependency. The preceding 1x1 `enc1.depthwise`,
  `detail1.depthwise`, `detail2.vertical`, and `detail2.horizontal` routes and the
  exact 2x2 readout route are also complete. The hierarchy was regenerated after
  8x8, 4x4, and 2x2 actor capacity failures; every actor now uses exact 1x1 leaves.
- Current physical checkpoint: epoch-1 seed-17 provisional ASIC export.
- No XL actor ORFS process is active. Preserve the accepted views and reports
  below for secondary work; do not resume the XL master campaign as the primary flow.
- Completed physical view: exact readout master `xl_hm_readout__out_2x2`.
  Its route has zero final DRC and antenna violations, +1252.43 ps setup slack,
  +48.5815 ps hold slack, and 266.839 MHz reported fmax. Its hash-verified LEF,
  GDS, and Liberty are staged in `artifacts/ASIC_XL/hard_hierarchy/views/`.
- Exact inventory: 44 actors, 49,610 logical 8x8 actor tiles, 3,163,600 exact
  physical actor leaves, 4,400 logical readout tiles, 70,400 physical 2x2 readout
  leaves, 3,234,000 total hard-macro instances, 335 unique masters, 78,707,200
  PLIFs, 2,916,390,400 resident-state bits, and all 281,600 output pixels.
- Actor partitioning is deterministic and constrained by measured capacity: all
  44 actors use 1x1 leaves. No 2x2, 4x4, or 8x8 actor remains in the layout.
- Sources and gates:
  `artifacts/ASIC_XL/resident_macro_variants/manifest.json` and
  `artifacts/ASIC_XL/hard_hierarchy/`.
- The fixed macroized native top, wrappers, and conservation preflight preserve
  all 44 actor replacements, the readout, and the original soft graph.
- Physical-view readiness remains false until all 335 masters have LEF, GDS, and
  Liberty. The current representative actor routes cover 5/44 actor populations;
  the complete top-level route has not been run.

### Secondary XL isolated primitive characterization

- State: ordinary one-cell PLIF and one fully connected nine-term 3x3 convolution
  output are complete through ASAP7 placement, detailed routing, extraction, and
  VCD-driven OpenSTA power. Outputs are under
  `artifacts/ASIC_XL/primitive_characterization/` and are aggregated by
  `scripts/inventory_xl_physical_primitives.py`.
- Ordinary PLIF: zero final detailed-route violations, 238.762 um^2 standard-cell
  area, 921.968 MHz fmax, 33.8188 pJ dynamic per bin update, and 0.205748 uW TT
  leakage. Multiplying 60,544,000 ordinary cells at 200 updates/s gives 0.4095 W
  dynamic, 12.4568 W leakage, and 14,455.61 mm^2 standard-cell area before shared
  routing, clocks, power grid, pads, and top-level whitespace.
- Nine-term convolution block: zero flow errors, 28.7372 um^2 standard-cell area,
  and 62.2855 uW dynamic under 128 pseudorandom vectors at one vector/5 ns.
  Normalized values are 3.19302 um^2, 0.0346031 pJ per bin evaluation, and
  2.37704 nW leakage per hardwired term. The exact model has 9,125,811,200 terms.
- A combined adaptation-plus-inhibition experiment was stopped and its partial
  outputs removed because no actor uses both mechanisms. Valid characterization
  must keep inhibition-only stem groups and adaptation-only encoder groups separate.

## Preserved secondary XL evidence

- All 45 rows in
  `artifacts/ASIC_XL/partitioned_synthesis_1x1/summary.tsv` pass for corrected
  beta48 RTL. Legacy stride-2 and normalized boundary results are not exact
  hard-macro views.
- The corrected `enc1.depthwise` 1x1 route, exact gate replay, and
  activity-annotated power remain valid for that stride-1 interior partition.
- The exact actor macro generator distinguishes output shape, receptive halo,
  clipped boundary offset, true stride, padding, dilation, and tile origin. Its
  334 exact 1x1 actor masters conserve all 49,610 logical 8x8 tiles and every
  one of the 78,707,200 PLIF identities.
- The packed exact 8x8 readout master passes focused cocotb and structural Yosys.
- Flat full-top attempts at 8, 16, and 24 GiB produced no complete netlist. Reuse
  them only as XL capacity evidence; full 140k assembly remains separate work.

## Next valid execution

1. Mechanism characterizations and six-class readout gate checks are complete for
   the existing isolated blocks. Graph-control primitives remain uncovered.
2. Exact 25-actor base hard-hierarchy inventory is conserved under
   `artifacts/ASIC/hard_hierarchy/`. All 160 catalog master RTL files are generated.
   First exact actor master is routed and staged (3/480 views). Continue resumable
   master ORFS for remaining masters, then macroized native assembly/wrappers/preflight.
3. Route required base masters resumably, reusing only digest-matching views.
   Physical-view readiness is currently 0/480.
4. Run top-level floorplanning, placement, CTS, routing, extraction, timing,
   physical checks, GDS integrity, and IR analysis. Compute power by multiplying
   accepted per-block activity results by the exact physical inventory.
5. Keep the XL hierarchy paused and separate until the 140k target reaches those
   gates or the user explicitly changes the primary target. Full native 1x1
   direct-state layout remains a large campaign (~46,647 mm² ordinary-PLIF
   footprint proxy); do not change resident-state mapping without an explicit choice.

## Process rules

- Primary 140k work preserves exact 440x640 dimensions, all 25 permanent actors,
  all 54 graph edges, and all 30,976,000 local register/latch PLIF identities.
- Secondary XL evidence preserves its own 44 actors and 78,707,200 PLIF identities;
  these counts must never be used as the 140k implementation inventory.
- The 8x8 value is the retained logical hierarchy boundary; exact 1x1
  physical leaves subdivide it without reducing the model or score map.
- Inspect containers, logs, status JSON, manifests, and digests before launching.
- Use bounded, non-dumpable containers and preserve restart artifacts.
- Do not create scheduled tasks for this flow.
- Do not recreate full-model simulation, replay, native activity profiling, or
  activity-derived whole-model estimates for 140k or XL. Simulate and measure
  blocks independently, then multiply by the exact full-layout inventory.
- Never substitute SRAM, truncate dimensions, share actor compute, drop boundary
  variants, or call extrapolated tile measurements full-chip PPA.
# 2026-09-24 — corrected full-float mapping and packet-floor sensitivity

The mapped parameter archive already folds ChannelAffine into `weight__*`; the earlier screen multiplied that gain twice. Corrected the screen and retained the true checkpoint/runtime-gain replay. With only final_fuse remapped through the baseline-corrected cap-area curve and sub-1µm responses dropped, the three-patch full-graph software sensitivity is 91.87–94.17% pixel argmax agreement and 2.55–5.28% final_fuse spike-bit mismatch across 0.6–0.15V headroom. No task accuracy or analog qualification follows. Matched same-phase no-event subtraction removes a ~7.38µV startup/feedthrough offset; both packet signs are monotonic from 5–300mV and magnitude mismatch drops from 35.8% at 5mV to 0.69% at 300mV. The 0.25–10µm corrected geometry curve is monotonic for both signs, though sub-1µm physical legality remains unproven. The later physical sequence reported below supersedes the earlier init-failure conclusion. Active candidate remains SC virtual-ground charge integration; no QAT/quantized weights are involved.

## 2026-09-24 — physical SC init, retention and packet ordering

Fixed the held-integrator bench sequence after tracing two setup errors: the original init pulse overlapped OTA reconnection, and the short nonoverlap pulse did not allow the large 100×100µm² membrane capacitor to settle. A 2.5µs TG init pulse followed by a 0.5µs guard initializes 0.75/0.90/1.05V states within 109µV. With OTA and packet switches held off, the state changes by no more than 0.247mV over 5ms. After that hold, reconnecting the OTA and applying a ±0.3V top-plate packet on the 1µm packet capacitor gives corrected signed state increments −41.0…−41.3µV / +41.1…+41.2µV across the three states. The 10µm diagnostic gives ±3.102mV. Packet bottom and OTA switches must open before the top plate returns to VCM; returning the top plate while the packet remains connected cancels its integrated charge. The bench artifacts are `sky130_sc_packet_state_sweep.json`, `sky130_sc_physical_retention_sweep.json`, and `sky130_sc_physical_retention_packet_sweep.json`. This is nominal TT schematic evidence only; no PVT, mismatch, noise, extracted parasitics, physical MIM legality or float-model accuracy is established. Next: repeated signed packets, order sensitivity, reset and short float-trace sensitivity with the corrected phase order.

## 2026-09-24 — physical two-packet reset reuse

The physical held-output cell now has a repeatable two-packet sequence with transistor TG state init, packet-cap reset between events, and disconnect-before-top-plate-return phase ordering. Across four sign sequences (`pp`, `nn`, `pn`, `np`) and initial states 0.75/0.90/1.05V, same-sign sums are about ±82µV, mixed-sign residuals ≤0.43µV, max error against the two single-packet reference steps 0.621µV, and `pn`/`np` order difference 0.075µV. Physical init remains within 109µV. This is only a short-interval TT schematic screen; realistic packet spacing within a 5ms bin remains the next check. Evidence: `artifacts/analog_asic/results/sky130_sc_physical_accumulation.json`.

## 2026-09-24 — 5ms-spaced packet sequence and OTA reconnect kick

A physical-init two-packet test spaced events at 0.5ms and 4.5ms. The first-event contribution drifts ≤0.56µV relative to a same-phase no-event cell over the intervening ~4ms hold; final same-sign accumulation is −65.32/+65.27µV versus an ±82.30µV reference (17.03µV max error), and `pn`/`np` differ by 4.20µV. The no-event path shifts by −15.67mV across the two OTA reconnect windows, so the corrected charge result depends on a simulator control that does not exist in the circuit. The post-packet settle tail lowers hold drift but increases accumulation error; OTA bias sleep lowers hold drift to 0.24µV but leaves −14.64mV common shift; a 0.5µs soft-start of both bias rails improves hold drift to 0.10µV but leaves −14.54mV common shift and 16.90µV accumulation error; OTA-output precharge variants destabilize the state (−711.7mV and −890.36mV common shifts). These variants do not solve the reconnect kick.

The physical ±41.16µV 1µm packet measurement was used to anchor the cap-floor replay on the full-float 140k best checkpoint and the same three real DSEC training patches. Final_fuse spike mismatch is 5.325/3.947/2.605% and pixel argmax agreement is 91.805/93.319/94.092% at 0.15/0.30/0.60V candidate headroom. This remains local software sensitivity, not model accuracy or a complete analog inference. Next investigate a reconnect topology with a physical common-mode correction path. Reports: `sky130_sc_physical_long_bin_accumulation.json`, `sky130_sc_physical_long_bin_sleep_accumulation.json`, `sky130_sc_physical_long_bin_precharge_accumulation.json`, `sky130_sc_physical_long_bin_sleep_precharge_accumulation.json`, and `model_reference/float_patch_trace.json`.

2026-09-24 analog continuation: a matched no-packet membrane reference and a
VCM-referenced OTA difference amplifier, switched on after the final packet,
cancel the ~15.4mV common reconnect shift while keeping both membrane outputs
isolated during accumulation. For `pp`/`nn`/`pn`/`np` across a 5ms bin, same-sign
changes are −63.839/+63.540µV, mixed residuals are +1.635/−1.821µV, and readout
tracking error is ≤0.54µV. Full-float sensitivity replay on three patches gives
1.78–4.41% final-fuse spike mismatch and 92.77–94.39% pixel argmax agreement at
0.15/0.30/0.60V headroom. This is schematic TT plus a local software replay,
not task accuracy or qualified analog inference. Next check timing and settling
across supported corners and mismatch, then lay out and extract the macro.
Evidence: `artifacts/analog_asic/results/sky130_sc_differential_reference_sampled_*`
and `artifacts/analog_asic/model_reference/float_patch_trace_sampled_diffreadout.json`.

## 2026-09-24 — differential reference bounds common reconnect shift

The full-float best checkpoint is the only analog model reference; QAT and quantized exports are unnecessary. Matched-reference runs for `pp`, `nn`, `pn`, and `np` packets spanning a 5ms bin cancel the nominal 15.66mV OTA reconnect shift in raw signal-minus-reference output. Differential event totals are −65.202/+65.133µV for same-sign packets and +2.019/−1.974µV for mixed signs. This agrees with the old matched-control correction but now compares two physical simulated cells. It is not yet a physical readout: transistor subtraction, mismatch, PVT, loading, headroom, noise, layout and extraction remain untested. Same-sign accumulation remains about 17µV below the idealized target. Next: transistor-level differential readout and full-float spike-sensitivity evaluation. Evidence: `sky130_sc_differential_reference.json`.
## Analog readout blocker — 2026-09-25

Rechecked the minimum-width late OTA comparator at 10ns with a 0.8882V gate precharge based on fine-step membrane common mode. State disturbance was 0.158–0.190µV over `pp`/`nn`/`pn`/`np`; `np` remained wrong-sign (+6.162mV output difference for a −1.953µV state residual). The old 100ns near-zero-kick result was timestep-dependent. Direct paired-reference sign sensing is not accepted. Next implement explicit threshold reference and switched offset-zeroing, preserving SC integration and the full-float reference, then measure learned-threshold decision margin and kickback. Detailed data and limits are in `docs/RESULTS.md` and `docs/ACTIVE_TASKS.md`.\n## Buffered readout provisional candidate — 2026-09-25

The direct late OTA sign comparator and direct threshold-shifted variant fail fine-step mixed-order decisions. A buffered closed-loop path now looks more promising: two unity-feedback OTA buffers isolate the physical membrane outputs, a 1MΩ/9.1MΩ poly-feedback OTA reads their difference, and a matched baseline amplifier removes the shared output common mode. Fine 10ns mixed `pn`/`np` threshold runs at gain10.1 and +10.9µV reference both decide below threshold correctly. Maximum combined membrane shift/readout error is 0.145µV, near the provisional0.18µV margin. Same-sign event orders have correct threshold decisions only at100ns so far. Next measure fine-step threshold transfer, PVT/mismatch/noise, and full-float sensitivity with the measured mapping; no module/layout acceptance yet.\n## Full-float sensitivity replay — 2026-09-25

Applied the measured 0.145µV mixed-case total error envelope to recorded float `final_fuse.standard` candidates. Spike-bit mismatch is 0.0423%/0.0395% at0.30V headroom and 0.0818%/0.0920% at0.15V. Keep 0.30V as the provisional minimum for further calibration. This does not measure analog circuit noise or whole-model segmentation. Results and scope are recorded in `docs/RESULTS.md`; reproduce with `scripts/analyze_sky130_buffered_readout_sensitivity.py`.\n
## 2026-09-25 — tuned ABBA readout and physical membrane test

A same-amplifier A–B–B–A polarity swap replaces the separate matched-baseline amplifier and suppresses offset/drift. The nominal 3078µm feedback resistor produced only ~9.1× gain; 3445µm gives ~10.16× effective physical gain. Corrected 10ns 5ms physical membrane screens for `pn`/`np` have correct polarity, +0.009/−0.005µV total input-equivalent transfer error, and −0.023/+0.020µV membrane read disturbance. Tuned amp-only TT/SS/FF, high/low resistor and −40/125°C screens retain sign with ≤0.068µV input-equivalent error at 1.411µV differential. A conservative0.091µV full-float threshold perturbation replay gives 0.0271%/0.0228% spike mismatch at0.30V headroom on three64×64 patches from one record. This is still a candidate, not module acceptance: no device mismatch, noise, physical learned-threshold generator, extraction, layout, energy or population timing. See `docs/RESULTS.md`, `docs/DECISIONS.md` and `docs/ACTIVE_TASKS.md`.

## State-noise and event-time follow-up — 2026-09-25

Continued from the ABBA buffered readout into packet calibration and state-noise analysis. With the physical DAC threshold baseline (`zz` −10.831µV), a0.05V positive packet shifts state +6.514µV at0.5ms and+6.796µV at4.5ms. A0.0564V negative packet shifts−5.175µV early and−5.313µV late. The approximately0.14–0.28µV event-time drift exceeds the provisional0.18µV q0.1 margin in some cases; matched opposite-sign order remains around0.56µV. The previous \"bipolar_charge_buckets\" bench gives a−424.65µV \"np\" residual because the early active OTA bucket holds its event for4ms, so it is invalid as a split-bucket candidate.

`scripts/analyze_sky130_cap_kTC_float_sensitivity.py` gives zero-noise exact replay and evaluates64 trials per noise case with captured full-float currents and actual PLIF beta/threshold/reset order. At0.30V headroom,14.26µV area-scaled100µm MIM single-cap kT/C creates1.952% final-fusion spike mismatch;20.16µV differential-pair noise creates2.226%. Even0.1µV independent noise gives0.0926%, and static per-neuron0.1µV gives0.2168%. This estimates model sensitivity, not physical SPICE noise; three64×64 patches of one stage are included and upstream spikes are frozen. Keep the current ABBA readout provisional and the passive analog state cell unaccepted. Next compare regenerative/differential charge handling and event-time-dependent packet calibration. Evidence: `artifacts/analog_asic/results/sky130_cap_kTC_float_sensitivity.json` and the one-event reports referenced in `docs/RESULTS.md`.


## Event-time trim and capacitor-area bound — 2026-09-25

The first early-event scaling attempt uses ×1.0433 for positive and ×1.0267 for negative packets, estimated from one-event timing screens. Physical mixed pn/np mean-state order difference shrinks from0.563µV to0.203µV at50ns, but mean state remains+0.457µV from the no-event baseline; this is not a pass. The single-event correction does not fully predict two-event interaction. The updated kT/C JSON projects one100µm-square MIM capacitor per30,976,000 PLIF states as0.31m² and631µF total; forcing the estimated single-cap kT/C down to0.18µV would take7.92mm-square capacitors and roughly1,940m² aggregate area. This is a scaling bound and assumes the existing MIM density, not a layout. The present per-neuron capacitive state cell cannot be rescued by merely enlarging its capacitor. Next stay within analog research and examine regenerative/differential charge-domain paths plus event-time trim, without QAT or digital fallback restart.


## Corrected 370-event analog injector screen — 2026-09-26

An audit found a PWL timestamp formatting bug in earlier long weighted sequences; all those numerical reports are marked invalid because the logs warn about collapsed time points. The direct differential injector was rerun with precise timestamps and a matched no-event MIM reference. On one full-float final-fusion output with370 events,20um MIM pair,0.15V state scale and0.965 gate-target trim, fixed10.5ns gate-amplitude pulses at15ns spacing finish in5.535us. After a5ms hold, event-induced voltage is within0.81–0.96% of the−8.742mV target over forward/reverse/randomized orders, with8.4uV forward/reverse spread. This is nominal SKY130 TT schematic evidence, not a qualified PLIF module. Common mode shifts about−8.3mV; threshold/readout/reset, beta, noise, mismatch, PVT, extraction, full network and task accuracy are outstanding. Fixed-bias pulse-duration coding produced6.7–33x accumulation error on the same weighted site and is not selected. See the corrected reports and next steps in `docs/RESULTS.md` and `docs/ACTIVE_TASKS.md`.

## Multi-site trim and state-cap follow-up — 2026-09-26

Gain0.986 improves one full-float near-threshold event to <0.18% charge error, but drives the corrected370-event maximum-fanin site to1.34–1.61% error and23.5uV order spread; gain0.965 had the opposite tradeoff. A10um MIM pair gives6.25–6.60% weighted error even when an ideal behavioral1nS common-mode servo holds the state near0.9V. A20um isolated-event calibration initialized at0.918V CM and−4mV differential matches the0.9V baseline curve at tested gate fractions, suggesting cumulative history/order effects matter more than this static voltage offset. The same ideal servo at20um lowers CM motion but increases order span to52.2uV. No trim or capacitor size is accepted. Continuing with a longer event-spacing sweep and transfer-history characterization before adding threshold/readout/reset.

The fixed-width injector was then tested at30ns,60ns and13.2µs event spacing, including a full5ms distributed event train. Wider gaps do not monotonically improve order sensitivity; the full-bin schedule's order span grows to194.3uV. A passive 20um membrane/1um packet calibration and weighted-event alternative are now being explored as the lower-history charge-domain branch.


## Randomized full-bin order and fan-in screens — 2026-09-26

The20um direct MOS lead was replayed with full-bin13.2us event spacing and independent random permutations at max (370), p99 (316) and median (291) fan-in. Across five randomized orders, max-fanin mean error is−0.083% (SD0.279%); p99 mean is+0.131% (SD0.102%). At the cancellation-heavy median site, the net target is only+118.95uV: shuffled absolute errors are about2.8–17.3uV, with a−7.94% mean relative error. Forward/reverse spreads average150.9uV at p99 and193.8uV at the median site. Randomized high-fanin sums are nominally encouraging, but cancellation and order sensitivity keep the cell provisional. The trace does not contain within-bin activation timestamps, so permutations do not establish actual event order. Continue analog circuit exploration with a physical state/common-mode compensation and include threshold/readout/reset; no QAT, digital switch, layout or acceptance. Detailed scopes and report names are in `docs/RESULTS.md`.


## Branch-balanced direct MOS screen — 2026-09-26

Corrected a factor-of-two reporting error in isolated-event common-mode change; weighted-sequence results remain valid. A new pMOS/nMOS gate-fraction mapping balances isolated signed charge and cuts the370-event burst common-mode shift from about−8.3mV to−24uV, with shuffled charge error+0.102%. Across the full5ms schedule it still has241uV forward/reverse spread, and a cancellation-heavy median site misses by+59.0% in shuffled order. This is nominal TT with ideal gate sources. Branch balance is useful for common-mode management but not an accepted fix for order-dependent signed integration. Continue with event scheduling and physical threshold/readout evaluation.


## Differential OTA readout gate — 2026-09-26

The full-float SNN sums convolution contributions once per timestep, so any within-bin serial event order belongs to the hardware controller. A greedy neutral schedule did not improve the cancellation-heavy site beyond shuffled-order magnitude. At0.15V mapping headroom, learned final-fusion thresholds are only3.11–6.40uV. Fixed threshold offsets ±0.1uV and ±1uV cause about0.25% and1.45% local final-fusion spike mismatch on three frozen patches. A physical SKY130 OTA gives ~5,060V/V nominal gain, but continuously connected readout on a20um MIM pair develops a−13.8uV startup differential after TG initialization, while retaining only about90% of the prepared small differential. A20um pair's estimated reset kT/C is100.8uV RMS; eight local float sensitivity replays average3.185% spike mismatch. No physical readout or PLIF is accepted. Next pursue offset cancellation and quantify full-task tolerance/noise before physical scaling.


## Full-float task noise sensitivity — 2026-09-26 (reset-noise results invalidated 2026-09-27)

Historical result, superseded 2026-09-27: this reset-noise patch replay used the same incorrect replacement of subtractively reset membrane state. Its spike, pixel and accuracy numbers are invalid. The physical MIM/OTA offset was uncorrected in that earlier circuit; use the corrected full-frame replay at the end of this log for reset-noise sensitivity.


## Physical baseline-sampled readout prototype — 2026-09-26

A20um MIM output sample through a physical TG, followed by a second SKY130 OTA, removes the first OTA's nominal settled baseline in a bounded one-event screen. With an ideal15.5mV threshold offset, a2ns-step 5ms TT run distinguishes tested +3.01uV and+6.53uV retained events at4.9ms: second-OTA outputs1.694V and0.0227V versus1.797V no-event. The f=0.6 event falls from+4.12uV immediately after injection to+3.01uV at4.9ms, so readout loading and pulse history remain. The sample capacitor adds area; no physical threshold DAC, noise/mismatch/PVT, weighted sequence or full PLIF reset/beta is qualified. Coarser20ns stepping misclassifies the short pulse and is rejected. Next bounded gate: process/temperature spread and physical threshold-source precision.


## Process and temperature screening rejects fixed OTA bias — 2026-09-26

The sampled MIM/OTA readout's nominal threshold separation does not survive basic process/temperature changes. At27C, f=0.6 event voltage varies1.98uV SS to4.97uV FF and its comparator decision flips. At TT/0C the zero-event comparator falsely goes low; at TT/85C tested positive events remain high, with first-OTA signal gain badly reduced. Passives stayed at typical, so this is only a partial PVT screen. Continue analog work by checking whether regulated bias/calibration can keep both OTAs in range; no readout/module acceptance or layout.


## Temperature trim and shared analog readout screen — 2026-09-26

Ideal temperature-specific OTA biases restore nominal short-window baseline stability at0/85C, but the same MOS gate fraction delivers strongly different charge; both weight drive and readout need calibration. The dedicated two-OTA-plus-sample cell draws25.38uA at1.8V; a continuous copy for every30.98m state would scale to~1.4kW and three20um MIMs/state have37,171mm2 raw capacitor area. A shared prebiased two-OTA channel with one sample cap can instead read an isolated state via physical input TGs. At TT, a prepared6uV signal falls to4.07uV after49us connected and crosses the ideal15.5mV threshold by30us; a prepared3uV signal stays high. The channel count lower bound is185,856 for30us service of all states in5ms, corresponding to~8.5W continuously biased at the measured25.51uA/channel, before actor/routing overhead. This remains a nominal schematic and arithmetic scaling screen, not an accepted PLIF. Next improve settling/state disturbance and implement physical calibrated threshold/bias circuits, then test actual weighted events and full actor throughput.

## Faster shared readout and signed-event screen — 2026-09-26

Reduced the shared first OTA's input width10→2um and both compensation caps100→20fF. In the5ms TT prepared-state run, differential retention after49us improves from about68% to about92%; a prepared6uV case crosses the ideal15.5mV threshold by5us while3uV stays high. A bounded500us TT signed direct-MOS event run produces ±9.54uV before read for ±0.65 gate fraction; the positive case goes low and negative/no-event stay high by5us. The1ns and2ns pulse runs agree within0.014uV. At SS/FF27C and trimmed TT0/85C,6uV needs up to9us to settle low. Fixed TT OTA bias fails at0/85C. The full5ms/2ns combined event deck stopped without valid output, so5ms hold and short-event integration are separate evidence. Continue with physical OTA bias/reference calibration and near-threshold mismatch/noise; full actor service, reset/beta, layout and chip PPA remain open. Details and artifact paths are in `docs/RESULTS.md`.

Per-update threshold noise at the20um differential-pair kT/C level (~100.8uV) causes~24.6% final-fuse spike mismatch and only~41% pixel argmax agreement in a selected three-patch validation replay. A200um pair still gives~15% mismatch and56% agreement for ~2.48m2 raw all-state cap area; an1000um illustration reduces spike mismatch below1% but costs~62m2 in raw pair capacitors. Increasing analog headroom from0.15→0.9V modestly improves the one-stage noisy replay but does not establish injector linearity or PVT operation. The fixed MIM/shared readout is therefore not noise-qualified. Next compare correlated differential state storage and an active low-noise integrator, then rerun task sensitivity and weighted sequence checks before keeping this architecture.

## Full-frame membrane kT/C sensitivity across active PLIFs — 2026-09-26

Historical result, superseded 2026-09-27: the reset-only and combined-mode replay code replaced the subtractively reset membrane with noise, even at zero noise. Its reset-noise spike, pixel and accuracy figures in this paragraph are invalid. Comparator-only figures were unaffected by this particular bug but remain proxy stresses. Use the corrected full-frame subtractive-reset results at the end of this log and the `_corrected_subtractive_reset.json` artifacts.

The PDK open-loop OTA noise calculation is now available alongside reset kT/C. TT/SS/FF 2um input-pair integrated noise is about100/106/95uV RMS over1Hz–100kHz; a20um input pair falls to36uV but loads the state enough to require a1us sample/isolate phase and programmed threshold offset. The prepared 3/6uV state test then decides by5us, but the device noise remains comparable to the larger0.9V-mapped thresholds. Applying36.27uV independently at every active PLIF comparator on three full validation frames reduces mean labeled accuracy37.87→29.58%, with55.3% pixel agreement. It is a conservative mapping of open-loop small-signal noise, but a real analog readout noise risk. Next assess low-noise sampling/correlated readout and analog scaling; no layout until the switched OTA noise is understood.

### Noise-aware analog direction — 2026-09-26

Astra-free continuation: the OTA noise PSD now exports through10MHz. Ideal chop subtraction estimates ~53uV RMS for a1us averaged phase at20um input and ~44uV at100um; widening alone is insufficient, while200um exceeds the PDK model bin. Full-float complete-frame replay with44.25uV per-update noise across all25 populations gives31.4–32.6% labeled accuracy versus49.82% baseline. Deprioritize OTA chopping as final decision circuitry. Next explore correlated differential event-charge accumulation with a slower/narrower-band decision and compare its physical packet/readout noise and area to the floating MIM path; remain analog and full float.

### Sample-isolated readout status — 2026-09-26

The two-stage shared OTA candidate passed prepared3/6uV and a single signed MOS event only with second-stage white transient noise; that is not complete readout-noise qualification. First-OTA output noise can couple through compensation into the stored membrane. A physical closed-loop buffer alternative gives low nominal state disturbance; at4um input width its10ns `pn` screen gives−0.041uV disturbance and0.389uV output-relation error, versus+0.012uV/0.667uV at2um. Closed-loop PDK noise with ideal1us boxcar sampling estimates35–87uV per buffer for4–100um widths and50–123uV differential for independent pairs; sequential correlated sampling at100um still estimates44.0uV. These are small-signal bounds without switch/noise transient or mismatch, but exceed mapped threshold margins. Next compare same-amplifier correlated sampling/autozero and narrow-band event-charge sensing against5ms service and full-float margins. Keep analog/full-float; no QAT or layout.

At100um input width and100fF compensation, the1us differential noise estimate spans43.3–58.7uV across FF/SS at27C and TT at125C; the tested unity-buffer gain remains near1.0. This modest corner spread leaves the readout above the mapped margins across the sampled PDK conditions. The next experiment remains correlated sample/autozero or charge-domain threshold sensing, with transient switch effects included before replay.

A capacitor-only shared differential sampler also trades read kick for kT/C:30um gives47.8uV single-cap kT/C and8.09uV state disturbance;50um gives28.73uV and19.95uV;100um gives14.38uV and42.96uV; the200um transient exceeded its60s bound. The simple sampler is therefore not accepted. Next compare active differential charge buckets and regenerative threshold sensing, preserving full-float weights and analog operation.

2026-09-26: Added an ideal-input SKY130 clocked-latch smoke. A symmetric TT regenerative comparator resolves ±3µV and larger differences to the expected polarity by 5ns after evaluation across three input widths; zero input is intentionally indeterminate. This has no realistic sample network, source loading, noise or mismatch, so it establishes circuit polarity and ideal regeneration only. Next gate is a switched physical-MIM sampling interface and offset/noise characterization.

2026-09-26: The physical-MIM/TG direct input sampler failed the first latch interface check. Switch/reset feedthrough exceeds the3µV target: measured zero-input offsets were +34.9/−2.8/−2.0µV for 5/10/20µm capacitors, and the20µm case misresolved ±3µV. The next bounded experiment uses the existing bottom-plate sequence and a matched dummy/reference to reduce feedthrough before evaluating the latch.

2026-09-26: Bottom-plate sampler plus matched dummy reduced the10µm zero residual to~0.10µV, but also delivered only~0.08µV from a±3µV source. A30µm cap showed~60µV feedthrough and lost one ±3µV decision polarity. The latch follows its immediate input correctly; the sampler transfer/offset is the unresolved issue. Next calibrate sampler-only transfer with physical source capacitance before further latch claims.

2026-09-26: Follow-up sampler calibration exposed scale-dependent results: ±100µV and ±3µV screens disagree, and tighter ngspice tolerances trigger timestep collapse with ideal DC sources. The sampler response is not calibrated; partial transient output is excluded. Next isolate sampler-only transfer, then reintroduce source capacitance and latch loading individually.

2026-09-26: Corrected the bottom-plate switch order. The sampler-only 10µm MIM path now gives approximately−0.998 gain and near-zero offset across ±3/6/100µV, so prior sampler-failure numbers are superseded. The attached latch resolves ±3µV but gives asymmetric results at ±6µV (−6 wrong, +6 correct). Next isolate latch decision threshold and precharge/evaluation timing before adding mismatch/noise.

2026-09-26: The ideal 2µm latch resolves ±2µV and larger inputs by5ns, but the sampler-attached latch still has an asymmetric boundary: ±3µV pass,−6µV fails and+6µV passes. The isolated sampler itself is clean. Next test correlated input autozero and sample-to-evaluate dead time to identify the latch interface offset.

2026-09-27: Found the regenerative latch was active during its supposed precharge phase. A clocked NMOS footer now holds both outputs high until evaluation and resolves ±3/±6µV nominal sampled inputs in3.5–3.7ns. The10µm real/dummy MIM samples still imply≈202µV RMS differential kT/C, far above3µV; nominal logic is not noise-qualified. Next measure a direct or preamplified clocked readout on the physical membrane, including state kick and service cost.

2026-09-27: Direct read of a properly initialized100µm physical membrane confirms the timing tradeoff. A read TG held on through latch regeneration causes≈69.5µV state disturbance. Cutting it0.5–2ns after evaluation preserves nominal ±3/6µV decisions with≤0.05µV disturbance;3ns cutoff gives≈0.76µV disturbance at3µV. The isolated latch node is≈4.07fF and has≈1mV single-node kT/C scale, so the nominal pass cannot justify architecture acceptance. One100µm MIM per30.976m identities is≈0.31m² bare capacitor area. Next bound shared charge-domain preamplification and storage cost.

2026-09-27: Corrected a full-float replay bug: reset-noise injection previously replaced the PLIF's subtractively reset membrane with noise. The full-frame zero-noise control now matches baseline spikes, classes and logits exactly. Corrected independent-pair reset-noise proxies across all25 populations lower selected-frame labeled accuracy from49.82% to30.49% at10µm MIM and35.67% at100µm MIM; a second100µm frame falls48.18%→34.86%. Prior reset-only and combined-mode replay numbers are invalid; comparator-only results are unaffected by this bug but remain proxies. With a2ns read-TG cutoff, opposing deterministic perturbations of2.22mV at the isolated latch input flip the±3µV decisions; this is not noise yield. The analog readout/state-store architecture remains unqualified. Evidence and source filenames are in `docs/RESULTS.md` and `artifacts/analog_asic/results/sky130_readout_architecture_boundary.json`; next bound a shared active differential charge bucket and physical analog state-storage cost before layout.

2026-09-29: Added an analytical shared-latch service screen and correlated-reset requirement to the readout boundary report. The measured3.705ns nominal decision alone implies23 ideal channels for one visit to all30.976m states in5ms; complete10ns/100ns/1µs/10µs service scenarios imply62/620/6,196/61,952 channels. These omit acquisition, reset and DAG dependencies. For a100µm MIM pair, illustrative3µV and1µV differential reset-noise levels require correlation at least0.9782 and0.9976 from the20.31µV independent-pair proxy; no physical covariance has been measured. Published SKY130, GF180MCU and IHP SG13G2 MIM densities are all around1.5–2fF/µm², so a simple open-PDK switch does not remove the area/noise issue. Keep SKY130 for the next physical reset/readout experiment, with direct-MOS event injection as the provisional baseline; no layout acceptance.

2026-09-29: Ran bounded corrected full-float complete-frame reset-noise probes at3µV RMS on validation records0/1 and1µV on record0, each with three seeds, all25 PLIFs and0.9V candidate headroom. At3µV, mean labeled accuracy remains near baseline (49.59% versus49.82%;48.32% versus48.18%) while pixel agreement is81.59%/79.84% and final-fusion spike mismatch3.99%/4.29%. At1µV on record0, pixel agreement is83.28% and spike mismatch3.39%. These are software-only independent Gaussian reset perturbations, not measured correlated circuit noise or a task-level acceptance result. Do not pick a reset-noise limit from two frames; next physical work must demonstrate noise covariance and readout timing before broader task replay.

2026-09-29: Extended the corrected replay to report six-class per-frame IoU and reran the two3µV probes plus their20.31µV physical100µm MIM-pair proxy comparisons. Baseline mean IoU is0.20573/0.19892 for validation records0/1;3µV gives0.20503/0.19931, while20.31µV gives0.11938/0.11726. These two-frame task metrics show why independent100µm MIM reset noise remains unqualified and why low-microvolt correlated reset merits physical testing. No accepted noise threshold, extracted cell or dataset-level accuracy claim follows.

2026-09-29: Separated initialization noise from post-spike noise to match the PLIF's subtractive reset semantics. With the20.31µV100µm-pair proxy injected only once at record start, mean IoU is0.12120/0.11591 on validation records0/1, close to0.11938/0.11726 when additional noise is injected after each spike. Initial state uncertainty dominates this bounded comparison. Avoiding hard reset sampling remains architecturally appropriate, but a low-noise/correlated initial reference is still required. This is software sensitivity, not a physical reset-noise measurement.

2026-09-29: Extended the architecture report with a two-cap SKY130 MIM area versus required reset-correlation sweep. At10µm square, one pair per state occupies≈6,195mm² bare and needs illustrative `rho≥0.999774` to reach3µV differential RMS; at100µm it occupies≈619,520mm² and needs`rho≥0.978189`. A bounded physical20µm MIM/OTA output-baseline-sample screen with−20/0/+20µV prepared differential gives a0.901mV no-event held-output span while a real MOS event produces only≈0.74–0.77mV output change after simulator no-event subtraction. All tested second-OTA comparator outputs remain high. This nominal deterministic circuit does not cancel the initial offset sufficiently; it has no thermal-noise/mismatch proof. Keep layout gated and continue to a different physical initial-reference/state-store topology.

2026-09-29: A finer gate-fraction0.601 physical MIM/OTA screen turns the initial-offset concern into a decision failure. Nearly equal≈4.18–4.20µV event-induced state changes produce1.756/1.609/0.230V final comparator outputs for−20/0/+20µV prepared offsets; only+20µV crosses the nominal0.9V logic boundary. The current held-output baseline scheme is rejected as an offset-robust threshold cell. This is deterministic TT with ideal bias/threshold, not a measured noise or mismatch yield.

2026-09-29: Added a corrected full-float first-touch mode: untouched membranes stay at exact model zero until their first nonzero current update, then receive one independent-pair kT/C draw. At20.31µV100µm-pair proxy, two-frame mean IoU is0.20398/0.20271 versus float0.20573/0.19892; at199.76µV10µm proxy,0.19710/0.20109. Pixel/spike agreement remains substantially imperfect, and only two frames/three seeds were tested. Added all four cases to the architecture boundary JSON. A bounded physical10µm SKY130 MIM/TG/MOS clamp experiment demonstrates that opening the clamp0.2–10ns before a10.5ns MOS event gives≈16.68µV retained event contribution, but opening at onset or1ns after gives≈157µV or3.22mV. Nominal ordering works only with an early local release. Next measure switched noise, PVT/mismatch timing, retention and service, then extend task replay; architecture/layout remain unqualified.

2026-09-29: Ran selected SS/FF MOS corners at0/85°C in the first-touch bench. Early clamp release preserves each corner's own free-reference event step; fixed gate fraction0.6 gives3.77–140.59µV across the extremes, a37.3× spread. Ideal external gate tuning to fraction0.687 at SS/0°C and0.449 at FF/85°C gives16.39/16.72µV, close to TT16.68µV for a single weight. No on-chip trim, weighted transfer curve, local mismatch, supply variation or switched noise was tested. The fixed gate-amplitude injector cannot be considered PVT-weight-accurate; next investigate a physical calibration/reference or more stable charge source before layout.

2026-09-29: Ran first-touch full-float sensitivity on validation records0/1 for a3µm MIM pair. The proxy is639.12µV differential RMS, with mean IoU0.14377/0.15201 versus0.20573/0.19892 baseline, pixel agreement44.34%/44.09%, and final-fusion spike mismatch14.19%/14.50%. Bare two-cap area at30.976m states is557.568mm² versus6,195.2mm² at10µm. The small geometry is not layout-rule qualified. First-touch initialization reduces one noise mechanism but does not by itself solve the storage area/fidelity tradeoff. Machine summary updated in the readout architecture boundary JSON.

2026-09-29: Added the intermediate5µm first-touch sensitivity on both selected validation frames. The392.40µV pair proxy yields mean IoU0.17081/0.17796, pixel agreement52.62%/51.53%, and final-fusion spike mismatch11.79%/12.21%, with1,548.8mm² bare pair area across all states. This fills in the sampled3/5/10µm tradeoff but does not provide a practical storage choice or measured circuit noise.

2026-09-29: Extended the10µm first-touch full-frame proxy to validation records2/3: mean IoU0.19994/0.20149 versus float0.20090/0.20258; pixel agreement65.23%/65.73%. Across four selected frames, average per-frame mean IoU0.19991 versus0.20203 baseline. The software result is encouraging for first-touch initialization, but the required local sequencing, fixed-gate PVT compensation, readout noise and6,195.2mm² bare pair area remain unqualified. Local SKY130 fixed VPP cells provide only≈0.51–0.62fF/µm² from reference capacitance/LEF area and do not improve on MIM density.

2026-09-29: Measured exact nonzero full-float membrane occupancy on complete validation records0/1 across all25 deployed actors and ten5ms updates. The occupancy starts75.22%/75.93% after update0 and reaches82.06%/82.45% after update9, or25.42/25.54m nonzero states. A dynamically allocated exact-zero analog store would still retain most states, while adding addresses and routing; this is not a clear area escape. The per-update, per-actor counts are in `sky130_float_membrane_occupancy_validation_0.json` and `_1.json`, and the architecture boundary report now summarizes them.

2026-09-29: Compared a mathematical one-local-cap/ideal-shared-reference first-touch proxy with independent pairs. At5µm, one-cap RMS277.47µV gives two-frame mean IoU0.18572/0.19370 and774.4mm² bare all-state area. At10µm, RMS141.25µV gives0.20431/0.20651 but3,097.6mm² bare. This halves the pair area and improves the software noise proxy, yet does not solve storage area or qualify reference noise, physical single-ended readout, routing and retention. Added four replay rows to the architecture boundary report.

2026-09-29: Extended the fixed-width differential MOS gate sweep to selected TT/SS/FF temperatures, then found sub-µV responses moved with solver settings and the multi-case deck composition. Repeated gate fractions0.4/0.6 in the physical clamp bench with tight ngspice tolerances; TT steps are0.691/16.287µV, SS/0°C0.142/3.915µV, FF/85°C8.268/140.524µV. The0.4/0.6 ratio changes1.62× across corners, so one scalar gain trim does not align even two weights. TT/SS low-point measurements converge within≈1% under0.1/0.05ns steps. No complete calibrated transfer table, on-chip trim, local mismatch or float-weight accuracy exists. Architecture boundary JSON records the qualified scope and source results.

2026-09-29: Built a solver-controlled per-case positive-event PVT charge curve for gate fractions0.1–0.95 and screened all143,728 PLIF float static weights against it. The common fixed10.5ns charge range0.0986–1165.34µV covers66.74% at an illustrative0.9V headroom per stage derived from three64×64 patches. A per-stage fixed width to cover the largest static weight at SS/0°C is at most444.1ns; observed SS fraction0.95 charge is linear within0.22% through450ns from zero state, and sampled p99 serialized pulse time is≤15.74µs before overhead. Prepared±0.9V differential changes that450ns event by5.35% end-to-end, and the physical TG state preparation has millivolt offset. Thus the range extension does not yet provide state-independent, noise-qualified weight transfer. Detailed bounds are in `sky130_ms_pvt_float_weight_charge_coverage.json` and the architecture boundary JSON.

2026-09-29: Added a bounded physical signed ten-event screen using first-touch TG initialization at SS/0°C. For450ns pulses, isolated ±49.7408mV events sum to±493.3179mV (0.822% low), while alternating order leaves∓0.2657mV. At40ns, isolated±4.4269mV events sum to±44.2368mV (0.0731% low), but alternating order leaves∓2.135µV. This residual is≈11% of the sampled minimum final-fusion threshold under the illustrative0.9V scaling; that cross-case comparison is a concern, not task loss. It uses ideal gate control and matched simulator subtraction; no real float-weight mix, mechanism updates, switched noise or mismatch. The architecture boundary JSON now includes both sequences.

2026-09-29: Replayed three actual epoch58 float final-fusion weighted fan-ins through physical10µm MIM/TG/MOS first-touch SS/0°C decks with40.253ns fixed pulses. The maximum-fanin site has370 events and−52.454mV ideal contribution. Interpolating the measured 10.5ns curve linearly gives−49.977/−50.422/−50.182mV by forward/reverse/shuffled order; measuring the curve at40.253ns and using log-charge interpolation improves this to−51.585/−52.248/−51.887mV (0.39–1.66% magnitude deficit), with0.662mV order spread. The measured-width linear interpolation stays3.74–4.59% low, so the steep-curve interpolation is the larger error here. A high-cancellation322-event site targets+7.49nV and produces+6.90/−6.13/−1.28nV; these nanovolt differences are beneath physical noise qualification. A329-event site targeting+32.623µV yields+32.645/+32.632/+32.635µV. All are deterministic ideal-gate tests at one corner; no physical gate DAC, switched noise, mismatch, threshold, beta/reset/adaptation or full-model task replay. No architecture/layout acceptance.

2026-09-29: Extended the370-event physical weighted sequence to TT/27°C and FF/85°C. Using a separately measured ideal gate map at each corner keeps the magnitude error0.03–1.67% across the selected conditions, with≈0.66–0.68mV event-order spread. Holding the SS gate map fixed instead makes TT forward/reverse sums−141.34/−147.89mV against−52.454mV target, while FF gives+25.59/−596.01/−482.44mV over three orders. The combined TT mismatched-map run aborted from a timestep collapse, so TT values come from separate completed order decks. This is strong evidence against a static uncalibrated gate map, not proof a realizable adaptive calibration exists. The architecture boundary JSON records both cases; physical reference, gate driver, noise, mismatch and closed-loop PLIF remain open.

2026-09-29: Tested physical analog weight-gate storage at SS/0°C with PDK MIM/TG/MOS and a5ms hold. Directly connecting a sampled10µm gate capacitor to the injector loses≈75% of a408.94µV reference event even after a short hold because of gate-node charge sharing; a100µm pair with10µs programming still has−2.90% event error after5ms and costs≈2,874.56mm² bare across143,728 PLIF weights. Steering current with gates left connected avoids that connection step, but rail-idle drain switching injects≈21.93mV even for an off-gate event. VCM-idle precharge reduces the switch-only term to≈0.351µV, yet the gate-dependent event shifts+91/+20/+3.1/+0.77% after5ms for10/20/50/100µm weight-cap pairs and creates continuous idle current. A short-refresh sweep is nonmonotonic from initial programming offset. Neither route is qualified; next bound a shared buffered gate path or a real low-leak refresh/reference scheme before full-fanin integration. Machine evidence is `sky130_ms_weight_gate_storage_boundary.json`.

2026-09-29: Screened the existing SKY130 OTA as a shared analog weight-gate buffer at SS/0°C. At ideal bias0.65/0.733V, DC follower error is≈−0.024mV at0.936V but−1.246mV at0.48V and−2.672mV at0.30V. With physical injector gate loads, an off-rail-to-weight step lets the p output reach command in≈0.1µs, while the n output does not settle near its final0.47875V until≈7–9µs and overshoots at5µs. The two-OTA plus MOS-load bench draws≈15µA at1.8V. This cannot directly replace ideal gate drivers for50ns-spaced events; a prefetched/shared buffer would need its own mux, calibration, noise and service proof. Architecture boundary JSON updated; no storage or layout acceptance.
