# Results

Reset-noise correction (2026-09-27): historical reset-only and combined reset/comparator replay figures below are invalid because the old replay replaced the PLIF's subtractively reset state with noise. The corrected full-frame results and zero-noise control appear in the final section. Comparator-only studies were not affected by this specific bug, but their independent-noise assumptions remain provisional.

First-touch follow-up (2026-09-29): an idealized corrected full-float replay clamps every untouched membrane to model zero and introduces one independent pair kT/C draw only on its first nonzero weighted-current update. On two selected full validation frames, a100µm pair proxy (20.31µV RMS) gives mean present-class IoU0.20398/0.20271 versus float0.20573/0.19892; a10µm pair proxy (199.76µV) gives0.19710/0.20109. About82% of neuron locations are touched in these replays. Despite similar aggregate IoU,100µm pair pixel agreement is only78.68%/77.51% and final-fusion spike mismatch is5.02%/5.24%; the10µm pair has64.35%/62.86% pixel agreement and8.57%/8.87% spike mismatch. Three seeds and two frames cannot establish dataset accuracy. The software first-touch detector uses a nonzero summed-current test and ideal switching; it does not simulate local route delay, simultaneous cancellation, noise covariance, reset/threshold hardware or the full physical schedule. Corrected per-case results are collected by `scripts/analyze_sky130_readout_architecture_boundary.py` into `artifacts/analog_asic/results/sky130_readout_architecture_boundary.json`.

A bounded nominal TT physical screen uses a10µm differential SKY130 MIM pair, two PDK transmission gates that clamp both nodes to0.9V, and a10.5ns positive MOS event. Opening the clamp0.2,0.5,1,2 or10ns before onset retains16.68µV event-minus-no-event at3.02µs, the same as a reference released500ns early. Opening at onset retains156.72µV, and opening1ns after onset retains3215.53µV: overlap is unacceptable. The no-event differential at3.02µs is0.066–0.152µV for these early-release cases, versus4.48µV after500ns of free drift. These are simulator-subtracted measurements with ideal clocks, deterministic devices and no thermal/transient noise; they show required ordering, not a hardware reference cancellation or qualified state accuracy. The event route needs guaranteed break-before-inject timing across PVT/mismatch and the full population before first-touch can be selected. Evidence: `scripts/test_sky130_ms_first_event_clamp.py`, `artifacts/analog_asic/results/sky130_ms_first_event_clamp_tt.json`.

The same early-release ordering preserves each corner's own reference charge across selected SS/FF at0/85°C, but fixed ideal gate fraction0.6 changes the single-event step from3.77µV (SS/0°C) to140.59µV (FF/85°C), a37.3× range; TT/27°C is16.68µV. At-onset and late release amplify charge at every selected corner. An exploratory *externally set* gate fraction0.687 at SS/0°C gives16.39µV, and0.449 at FF/85°C gives16.72µV, showing tunability for this one event. No on-chip calibration circuit, weight transfer curve, local mismatch model, voltage corners or temperature compensation has been implemented; these tuned points cannot qualify actual float-weight encoding. The passive MIM/R/C cards remain typical while MOS corner and temperature vary. Evidence: the `physical_first_event_pvt_gate_transfer_screen` and `physical_first_event_selected_gate_tuning_probe` fields in the architecture boundary JSON.

First-touch area/noise follow-up: reducing both state MIM squares from10µm to3µm cuts bare pair area across30,976,000 logical states from6,195.2 to557.568mm², excluding TGs, devices and routing. The independent-pair thermal proxy rises from199.76 to639.12µV. A corrected full-frame first-touch replay at3µm gives mean present-class IoU0.14377/0.15201 on validation records0/1 versus0.20573/0.19892 float, with44.34%/44.09% pixel agreement and14.19%/14.50% final-fusion spike mismatch. The3µm geometry has not been checked against PDK layout rules. This two-frame sensitivity indicates first-touch alone does not permit that area reduction with task fidelity; it is not a dataset-level acceptance result or proof of the ultimate minimum capacitance. Evidence: `sky130_readout_architecture_boundary.json` (`first_touch_mim_area_noise_tradeoff` and corrected replay rows).

An intermediate5µm pair occupies1,548.8mm² bare and gives392.40µV independent-pair proxy. The same two-frame first-touch replay produces mean IoU0.17081/0.17796, pixel agreement52.62%/51.53%, and final-fusion spike mismatch11.79%/12.21%. This maps a monotonic area/noise sensitivity trend across3/5/10µm in the sampled records; it is not an acceptable design point, a layout-rule check, or a measured noise result.

Local SKY130 capacitor inventory check: the installed `sky130_fd_pr` snapshot contains MIM and two fixed VPP capacitor families. The VPP test references report10.28076fF and41.82767fF for LEF footprints4.38×4.59µm and8.58×7.84µm, or0.511/0.622fF/µm². This is lower footprint capacitance density than the approximate2fF/µm² MIM area term already used in the state sweep. VPP therefore does not offer a denser supported resident-state capacitor in this PDK snapshot. This is a local library inventory calculation, not a full process technology survey or extracted comparison; no MOS varactor/nonvolatile analog store is qualified here.

The10µm first-touch proxy was extended to validation records2/3, with mean IoU0.19994/0.20149 versus float0.20090/0.20258; pixel agreement65.23%/65.73% and final-fusion spike mismatch8.42%/8.34%. Across four selected frames, the average per-frame mean IoU is0.19991 versus0.20203 baseline. This broadens the idealized sensitivity check but does not establish dataset-wide accuracy, event-routing feasibility, or a practical6,195.2mm² bare MIM store.

Exact-zero membrane occupancy was counted from the verified epoch-58 full-float checkpoint on complete validation records0/1, all25 deployed PLIFs and ten updates. Immediately after the first5ms update,75.22%/75.93% of30,976,000 membranes are nonzero; after the tenth,82.06%/82.45% are nonzero (25.42/25.54 million states). Thus a lossless scheme that allocates analog storage only to exact nonzero membranes would still need most of the population on these records, before tags, addressing, routing, adaptation and contention. This is software occupancy, not a physical sparse-store implementation or a dataset-wide bound. Evidence: `scripts/analyze_sky130_float_membrane_occupancy.py`, `artifacts/analog_asic/results/sky130_float_membrane_occupancy_validation_0.json`, and `_validation_1.json`.

Single-cap/shared-reference first-touch sensitivity (2026-09-29): replacing the independent-pair kT/C proxy with one local MIM and an ideal noiseless shared reference reduces estimated RMS to277.47µV at5µm and141.25µV at10µm. On complete validation records0/1, the5µm proxy gives mean IoU0.18572/0.19370, versus baseline0.20573/0.19892, with58.60%/57.25% pixel agreement. The10µm proxy gives0.20431/0.20651 mean IoU and68.77%/67.78% pixel agreement. Bare one-cap area over30,976,000 states is774.4mm² at5µm or3,097.6mm² at10µm, before switches/routing. No physical shared-reference noise, distribution, single-ended readout offset or retention was measured. This is a mathematical topology comparison, not an accepted storage architecture; `sky130_readout_architecture_boundary.json` collects all four corrected replay reports.

Injector calibration follow-up (2026-09-29): the physical10µm MIM/TG first-touch bench was rerun at gate fractions0.4 and0.6 with ngspice `reltol=1e-5`, `abstol=1e-15`, and `vntol=1e-9`. The early-release event steps are0.691/16.287µV at TT/27°C,0.142/3.915µV at SS/0°C, and8.268/140.524µV at FF/85°C. The0.4-to-0.6 step ratio varies0.0364–0.0588, a1.62× normalized-shape spread. Thus a single multiplicative gain correction cannot align even these two points across selected corners. For the sub-µV0.4 point, tightening the transient step from0.5ns to0.1/0.05ns gives TT0.6909/0.6912µV and SS0.1406/0.1412µV; looser solver results differed substantially, so use the tight two-point report for this comparison. The wider16-case gate curves remain exploratory and should not define small-weight calibration until their solver sensitivity is resolved. No physical DAC, replica/reference trim, local mismatch, supply corner or full-float weight transfer is qualified. Evidence: `sky130_readout_architecture_boundary.json` (`physical_injector_two_point_tight_pvt_shape`).

Tight per-case gate sweep: `scripts/characterize_sky130_ms_first_event_pvt_curve.py` measures fractions0.1–0.95 with0.1ns transient steps in the same physical10µm MIM/TG bench. Each selected corner is monotonic, but the common measured charge window is only0.0986–1165.34µV across TT/27°C, SS/0°C and FF/85°C. At the illustrative0.9V-per-stage headroom derived from three64×64 float patches, this fixed10.5ns window covers66.74% of the143,728 PLIF folded float static synaptic weights; the separate96-weight class-current head is excluded. Final fusion has90.42% static coverage, enc1.standard54.34%. Fractions near0.1 produce charges far below the estimated membrane reset-noise scales and are not physically precision-qualified. These are static-weight counts, not event-weighted task accuracy or a calibrated hardware encoding. Evidence: `sky130_ms_first_event_pvt_transfer_curve_tight.json` and `sky130_ms_pvt_float_weight_charge_coverage.json`.

A fixed **per-stage** pulse-width extension is a bounded range probe, distinct from encoding each weight by a long duration. At SS/0°C gate fraction0.95, measured10.5/50/100/150/300/450ns events deliver1.165/5.543/11.083/16.622/33.233/49.833mV; the450ns value is0.22% below the10.5ns linear extrapolation at zero differential state. Scaling each stage's pulse width to cover its largest static weight at the slow corner would require at most444.1ns in this three-patch scale. Sampled active-fanin p99 times that fixed stage width gives at most15.74µs optimistic serial pulse service for any stage; it excludes routing, control, readout, reset, graph waits and actual full-frame extremes. Under an *unverified linear low-end extrapolation*,0.343% of PLIF static weights would fall below the scaled common charge floor. At450ns, a prepared initial differential of−0.9…+0.9V changes event-minus-no-event charge from51.150 to48.483mV, a5.35% span relative to the zero-state step; physical TG preparation itself adds millivolt-scale no-event differential offset at these nonzero states. This state dependence and the lack of low-event noise/DAC/mismatch validation prevent weight-transfer acceptance. Evidence: the boundary report's `physical_injector_tight_curve_and_float_coverage` and `physical_long_pulse_state_dependence_screen` fields.

Repeated signed event screen: a bounded physical10µm MIM/TG/MOS bench applies ten equal events at SS/0°C with0.95 gate fraction. At450ns width and600ns spacing, isolated positive/negative events give±49.7408mV; ten same-sign events give±493.3179mV,0.822% below linear ten-event prediction. Alternating `pn`/`np` sequences leave∓0.2657mV after matched no-event subtraction. At40ns width and100ns spacing, isolated events give±4.4269mV, ten same-sign totals±44.2368mV (0.0731% low), and alternating residuals∓2.135µV. At the illustrative0.9V-per-stage float scaling, sampled final-fusion effective threshold minimum is18.67µV, so even the shorter alternating residual is about11% of that threshold; this compares unlike stress and model cases and is only a risk indicator. The nominal positive/negative symmetry follows mirrored identical PDK devices, not mismatch robustness. The bench has no actual float-weight mixture, beta/reset/adaptation, comparator, thermal noise or task replay. Evidence: `scripts/test_sky130_ms_first_touch_long_event_sequence.py` and `sky130_readout_architecture_boundary.json` (`physical_first_touch_repeated_signed_event_screen`).

## Full-float pulse-duration mapping and service screen — 2026-09-24

The analog reference is `EventSpikeSeg140k_seed17_best.pt`, epoch 58 / best epoch 58 of the 80-epoch run, `is_best=true`, SHA-256 `c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7`. Exported parameter arrays and sampled software traces use the original float inference path; no QAT, quantized weights, fake quantization or Q7.16-derived values were used. The epoch-80 file is not the best checkpoint and is not the analog reference.

`scripts/analyze_sky130_pulse_float_mapping.py` folds exported ChannelAffine gains into each float convolution weight and compares them with the measured 0.9V SKY130 TT pulse curve (50ns/500us logical width, 7x positive pulse-duration factor). Each layer is independently scaled so its largest effective coefficient fits the largest tested pulse; this is only a sensitivity point, not a selected voltage encoding. The resulting median positive pulse widths are 69us to 306us in sampled stages. Per-layer median learned threshold voltages under those scales range from about 0.23mV (final_fuse) to 4.23mV (stem), illustrating that scale selection alone has not resolved threshold/noise headroom.

For the three recorded real-DSEC patch traces, active convolution inputs were replayed through absolute effective-weight pulse durations. Assuming output neurons operate in parallel but each neuron's incoming contributions serialize, median/p90/p99 service is 0.19/1.64/7.83ms for stem, 2.99/16.81/37.14ms for enc1.standard, and 10.28/48.17/115.39ms for final_fuse.standard. Before setup or settling, 2.28%, 37.98% and 58.79% of active destinations respectively exceed 5ms. This optimistic model shows that one serial pulse lane per postsynaptic membrane does not meet the bin budget for later sampled stages at the max-weight-fit scales. Parallel fan-in, complete-model accuracy and global scheduling remain untested; this result does not prove pulse duration cannot work with a substantially parallel cell array. It is sufficient to start the planned switched-capacitor fallback comparison. Evidence: `artifacts/analog_asic/results/sky130_float_pulse_mapping_screen.json` and `artifacts/analog_asic/model_reference/float_patch_trace.npz`.

The pulse-reset follow-up used a per-initial-state quadratic fit from three calibration widths, then SPICE-tested held-out threshold steps of 0.08/0.12/0.14V from initial states 0.75/0.90/1.05V. All nine cases pass the provisional 15% step-error bound; the maximum relative error is 0.0152%. This is a calibration-conditioned TT schematic result requiring a known initial membrane voltage. It does not establish an on-chip state estimator, comparator/reset coupling, PVT/mismatch robustness, extraction or model spike equivalence. Evidence: `artifacts/analog_asic/results/sky130_ms_soft_reset_calibration.json`.

## SKY130 switched-capacitor packet topology screen — 2026-09-24

A first direct-sharing cell uses a PDK MIM packet capacitor, 100µm×100µm MIM membrane and SKY130 CMOS transmission gates. A precharged packet is connected to the membrane for one event; tested packet squares are 10/30/100µm and membrane starts are 0.75/0.90/1.05V. All six sign/size variants transfer in the commanded direction, but absolute packet magnitude is strongly state-dependent. Across the tested states the max/min magnitude ratio is 3.0–4.6×; the 10µm packet's positive magnitude ranges 1.00–4.66mV and the 100µm packet's ranges 74.7–225mV. Thus direct sharing does not implement a fixed signed weighted contribution and is rejected as the standalone cell. This does not reject switched-capacitor injection generally; a bootstrapped/sample-compensated transfer or virtual summing node is next. No weight coding, repeated-event schedule, amplifier, PVT/mismatch, extraction or PLIF acceptance was tested. Evidence: `artifacts/analog_asic/results/sky130_sc_charge_share.json`, bench `scripts/test_sky130_sc_charge_share.py`.

The MOS virtual-summing-node candidate in `asic/analog/sky130_sc_charge_integrator.spice` uses a two-stage MOS OTA, PDK MIM feedback/packet capacitors, TG packet isolation and a separate TG to reset the isolated packet capacitor between events. The test fixture initially used the wrong MIM initial-condition reference; with the capacitor's differential state initialized as `Vstate−VCM`, the 0.75/0.90/1.05V states are preserved to within 3.14mV before packet injection. With ±0.3V packet steps, 1/3/10µm square capacitors deliver about 32.8µV/0.296mV/3.095mV for positive input and 48.3µV/0.307mV/3.105mV for negative input. Packet variation across the three start states is ≤1.84% at 1µm, ≤0.24% at 3µm, and ≤0.012% at 10µm. Positive/negative gain mismatch is about 47% at 1µm, 3.7% at 3µm and 0.33% at 10µm, so the smallest cap needs a differential switch/offset correction. The inverting topology requires reversing digital sign-to-packet mapping. The sampled virtual-node error is up to 1.74mV. A 90% response-time screen is 3.3–10.9ns after the input step; this excludes switch setup, packet-cap selection/reset and fanout. The 30-case wider sweep exceeded its 60s bound; the completed 18-case sweep covers 1/3/10µm, three states and both signs. Physical initialization, weight-cap selection, bias generation, full PLIF reset, and PVT/mismatch/extraction remain unqualified. Bias rails are ideal, and no float-model spike equivalence is claimed. Evidence: `artifacts/analog_asic/results/sky130_sc_charge_integrator.json`, bench `scripts/test_sky130_sc_charge_integrator.py`.

The packet capacitor must be isolated from the membrane while its charge is reset. A 12-case two-event sequence screen explicitly separates those phases. At 10µm packet size, the largest error from adding two independently measured packets is 27.14µV; the largest P→N versus N→P order difference is 0.268µV. Absolute cancellation error is ~23–25µV, comparable to or larger than the small residual, so relative cancellation error is not meaningful. Per-event input-to-input spacing is 2.5µs in this provisional schedule, including a break-before-make packet-cap reset phase; this remains a one-cell TT timing screen, not an integrated throughput claim. Evidence: `artifacts/analog_asic/results/sky130_sc_charge_integrator_accumulation.json`, bench `scripts/test_sky130_sc_charge_integrator_accumulation.py`.

Combining sampled active fan-in counts with a provisional 2.5µs packet cycle (the initial bench action window, not a validated repeating schedule) gives serial per-output service p50/p90/p99/max of 10/45/90/138µs for stem, 120/185/223/275µs for enc1.standard and 530/685/790/925µs for final_fuse.standard. No sampled destination exceeds 5ms under this optimistic dedicated-output assumption. This is a throughput indication only: it omits weight-cap selection, cap reset/precharge, arbitration, restore/ADC and whole-chip routing, and covers three patches from one record. A separate full-float range-to-cap sensitivity maps the final_fuse maximum effective weight to a ~30.5µm capacitor at 0.3V candidate headroom, but its 0.1-percentile weight would require a ~1.4nm square capacitor under linear area extrapolation, below the 1µm smallest tested device. At that same sensitivity scale, the learned threshold is ~10.9µV and the 0.1-percentile candidate-to-threshold margin is ~0.18µV. A uniform 1µV threshold offset changes about 0.28–0.29% of sampled final_fuse spike bits; 10µV changes 1.4–2.5%. These are model sensitivity estimates, not analog noise or mismatch results; small weights may be behaviorally unimportant, but pruning is not authorized. Evidence is included in `sky130_float_pulse_mapping_screen.json`.

## SKY130 Q7.16 restore/mux and writeback controller — 2026-09-23

The current 24-bit R-2R + MIM restore/multiplex schematic smoke passes the **coarse** 3mV rail-window criterion, tested-code monotonicity, and A→B→A round-trip after applying a uniform +12,544-code offset and a +2.553424mV DAC rail shift. The center state is within 46µV of 0.9V; the worst tested error is 2.863mV, or 938.05 declared Q7.16 voltage LSBs; `q716_half_lsb_accuracy_pass=false`. Applying the code offset only to nonnegative codes caused the earlier discontinuity. These are provisional TT schematic corrections, not analog Q7.16 accuracy or ENOB evidence. The 1k/2k values remain ideal and unqualified for physical implementation.

Evidence: `artifacts/analog_asic/results/sky130_ms_restore_mux_24bit.json`. The separate 23-bit weight-magnitude voltage-transfer rerun passes its 5mV coarse limit and tested monotonicity on the regenerated 1k/2k ideal ladder; worst tested error is 3.592mV. It does not test MOS injection current or analog precision (`sky130_weight_q716_dac_screen.json`).

The synthesizable SAR/slot controller passed an Icarus Docker RTL smoke: low/offset/full-scale ideal codes yielded expected clipped Q7.16 endpoints over 72 comparator decisions and phase outputs did not overlap. Its decode now inverts the restore path's uniform common-mode code offset. Test source: `scripts/tb_sky130_ms_slot_controller.sv`; RTL: `asic/analog/sky130_ms_slot_controller.sv`; machine report: `artifacts/analog_asic/results/sky130_ms_slot_controller_rtl.json`. Comparator feedback was an ideal code-level model. This is still not an analog-integrated ADC/writeback result; measured restore error remains hundreds of Q7.16 LSBs.

At 30,976,000 membrane identities and 24 sequential SAR decisions per identity, a single lane needs 743,424,000 comparisons per 5ms update. Even at 100MHz this implies at least 1,487 parallel lanes before setup, settle, injection/leak, and routing overhead. This throughput bound blocks any one/few-channel population claim until the architecture is revised or an adequate parallel implementation is demonstrated.

## PDK review — 2026-09-23

Continue with SKY130 for this prototype: the local PDK provides the transistor and MIM models already exercised by the channel/restore benches. IHP SG13G2 is a credible analog/mixed-signal alternative with MIM devices and ngspice support, but IHP labels its open PDK a preview; adopting it would require a fresh model, extraction, and flow qualification. GF180MCU is another open option, but its upstream PDK is also marked experimental preview. A PDK change would not fix the 938-LSB restore precision gap, the direct MOS current-DAC dead zone, or the SAR lane-count lower bound, so the current problems do not justify migration. Sources: [IHP Open PDK](https://github.com/IHP-GmbH/IHP-Open-PDK), [GF180MCU PDK](https://github.com/google/gf180mcu-pdk).

## Digital ORFS stopped — 2026-09-23

User ordered mixed-signal-only: host ORFS workers killed, `eventspikeseg-hm-*` containers removed, journal `running_orfs`→`paused` (2 stem masters). Counts: 18 complete / 128 OOM / 2 paused. Artifacts preserved. Evidence: `artifacts/ASIC/digital_stop_20260923/`.

## SKY130 weight DAC + β↔leak screen — 2026-09-23

| Check | Result |
| --- | --- |
| 23-bit Q7.16 magnitude DAC codes 0/1/2/8/68 | monotonic; regenerated 1k/2k ladder max coarse transfer error 3.592mV over 0.9–1.8V |
| β↔leak τ cal | τ≈18.9 µs from 5 µs leak residual |
| β targets 0.35 / 0.60 / 0.90 | abs err ≈ 0.104 / 0.029 / 0.004 (smoke lim 0.12) |

The β/leak mapping evidence is schematic only (`artifacts/analog_asic/results/sky130_ms_weight_beta_screen.json`). Weight evidence now comes from `sky130_weight_q716_dac_screen.json`; it is a voltage-transfer test and does not qualify the injector current, extracted layout, or Q7.16 ENOB. The old executable 4-bit injector loop was removed from the combined screen.

The original TT operating-point screen (`sky130_weight_q716_injector_screen.json`) tested Q7.16 magnitudes 0, 1, 8, and 68 with both signs and found low-code leakage-floor response and severe sign mismatch. The fresh integrated 1k/2k R-2R/MOS sweep is also unsuitable for weight injection: it remains near cutoff through 25% code, then rises sharply; strict monotonicity fails and full-scale positive/negative current ratio is 0.859. This is DC schematic evidence only, not pulse charge or PLIF accuracy. Keep this direct gate-DAC injector out of acceptance.

Sequential accumulation was screened on a single PDK MIM membrane using the pulse-duration channel: two identical positive events summed to within 0.00045%; mixed positive/negative events in either order were within 0.53% of the independent-pulse sum, and order changed the residual by 0.54%. This supports charge accumulation for the tested TT operating point and event size. It does not establish small-signal linearity, simultaneous events, corners, mismatch, or a weight-code mapping (`sky130_ms_pulse_width_accumulation.json`).

A separate analog injection candidate, `synapse_pulse_width_mos`, keeps the membrane as a capacitor and encodes signed weight by gate-pulse duration. Its full PLIF-channel TT transient screen uses the SKY130 PDK MIM model at 100µm×100µm, and is monotonic across seven logical durations from 0.05 to 4µs. With a 7× longer positive pulse scale, the normalized positive/negative gain ratio is 0.957; worst per-sign slope deviation is 0.36%. A separate single-pulse 5ms hold test on the same channel variant shows 15–18µV drift with leak disabled, passing a provisional 3mV limit. This remains a circuit-level candidate, not Q7.16 weight accuracy: no mismatch, PVT, extracted parasitics, event multiplicity, or population scheduling has been checked. At a hypothetical 100MHz timer, 4µs and 28µs provide only 400 and 2,800 pulse-width ticks (about 8.6 and 11.5 bits of timing levels); the seven-point screen does not establish 24-bit charge precision. The next analog step is to characterize weight-code-to-charge mapping and event accumulation; the restore/writeback DAC monotonicity failure remains a separate blocker.

## SKY130 mixed-signal analog PLIF channel smoke — 2026-09-23

| Bench | Result |
| --- | --- |
| MOS inject + 5ms MIM hold | pass (post-inject ≈1.149V; drift ≈−0.65mV) |
| MOS leak toward vcm | pass (1.149V → 0.961V) |
| Threshold capture → spike | pass (state≈1.40V > thr 0.98V; spike high) |

`channel_smoke_pass=true`. Evidence: `artifacts/analog_asic/results/sky130_ms_plif_screen.json` and bench logs. This validates a representative schematic channel only; multiplexing one/few channels across 31M identities is not throughput-feasible under the 5ms update based on the SAR lower bound above. A sufficiently parallel alternative is not yet sized. ASAP7 analog membrane storage remains unaccepted.

## ASAP7 MOSCAP storage gate — 2026-09-23

The complete bounded Docker run (`python scripts/test_asap7_mos_storage.py --only all`) verified corrected D-G-S-B terminal order and the leakage-subtracted Ceff method:

| Bench | Result | Interpretation |
| --- | --- | --- |
| 4-finger C-V | Median 0.27035 fF total; 0.06759 fF/finger | Positive schematic Ceff; voltage-dependent, not a linear/MIM capacitor |
| 8-finger retention, 5.002 ms | 0.41969 V → 0.22255 V; drift −0.19714 V (−2.816 model units) | Fails provisional ±0.02-unit gate decisively |
| 8-finger drain/adjust | write 0.41379 V; drain 0.34439 V; rewrite 0.44766 V | Bounded write/drain/rewrite checks pass |

Option B is **not accepted as a storage candidate** because retention fails despite successful reset/rewrite. No scaling, layout or physical qualification follows from these small schematic tests. Readiness remains `full_orfs_ready=false` with missing physical macro inventory, DRC/LVS/extraction, model-conserving assembly preflight and ORFS collateral. Machine-readable results: `artifacts/analog_asic/asap7/capacitor_qualification.json`, `results/mos_storage_checks.json`, and `readiness.json`.

### Retention isolation and alternate device polarity

Same-switch controls show that a sub-fF ideal capacitor also loses substantial charge (−0.2260 V), while 1pF and 20pF ideal controls drift −0.01514 V and −0.000804 V under this stimulus. The 8/32-finger nMOS Cgg structures drift −0.17675/−0.13992 V. A pMOS Cgg structure tied D/S/B to VDD is a better small-count result at 8 fingers (−0.01094 V, or −0.156 model units) but still fails the 0.02-unit limit; 32 and 128 fingers drift +0.04154 and +0.15020 V. Current scaling does not yield a passing pMOS point and these schematic counts are not layout estimates. The no-switch floating-node controls are invalid because the simulator initialized at about 0.77 V rather than the requested 0.42 V. See `artifacts/analog_asic/results/mos_retention_diagnosis.json` (diagnostic script: `scripts/diagnose_asap7_mos_retention.py`). No MOS Cgg option is accepted. Later analog diagnostics refined the failure cause and tested a low-common-mode nMOS variant. Direct OSDI `IGTOT` is ≈0.93pA per pMOS storage instance at 0.28V (≈7.41pA for eight). Interior off-gate pMOS bias was not retention: it converges toward an input-dependent equilibrium, and adversarial 0.28↔0.42V transitions show large drift. The open ASAP7 collateral has no MIM/MOM device card or PCell. A low-common-mode nMOS-only check (diagnostic contract Vcm=0.15V, states 0.08/0.15/0.22V) produced:

| Diagnostic | Result | Interpretation |
| --- | --- | --- |
| Standalone eight-instance Cdiff | 0.5415 / 0.5439 / 0.5756 fF | AC admittance at 100kHz and 1MHz agrees; schematic MOS Cgg only |
| Intrinsic gate-leak rate by state | 0.124 / 0.413 / 0.822 V/s | Only 0.08V is below provisional 0.28V/s criterion |
| Complete access-path rate across six state/input pairs | 0.124–4.03 V/s | Several combinations exceed criterion; no 5ms hold cell passes |

This diagnostic changes common-mode and range for isolation only; it does not replace the 0.35V Stage-2 encoding or qualify a cell. Evidence: `results/low_common_mode_nmos_only_dc.log`, `results/nmos_cap_standalone_ac_*.dat`, and the corresponding bench decks under `benches/`. No scaling or layout.

| Low-common-mode nMOS-only screen | Measured result | Interpretation |
| --- | --- | --- |
| Standalone eight-instance storage Cdiff at 0.08/0.15/0.22V | 0.5415/0.5439/0.5756 fF | AC admittance at 100kHz and 1MHz agrees; schematic MOS Cgg only |
| Intrinsic gate-leak rate at those states | 0.124/0.413/0.822 V/s | Only 0.08V is below provisional 0.28V/s criterion |
| Full access-path rate across six state/input points | 0.124–4.03 V/s | Several combinations exceed criterion; no 5ms hold cell passes |

This variant changes common-mode/voltage range and is only an analog diagnostic; it does not replace the 0.35V Stage-2 encoding or pass the full storage gate. Evidence: `results/low_common_mode_nmos_only_dc.log` and `results/nmos_cap_standalone_ac_*.dat`. No scaling or layout.

## Stage 2 circuit contracts (ASAP7 analog) — 2026-09-23

Machine-readable contracts only; no new transistor PPA. Key numbers from quantized 140k export:

| Quantity | Value | Notes |
| --- | --- | --- |
| VDD / vcm | 0.7 V / 0.35 V | ASAP7 smoke encoding |
| Smoke volts per state unit | 0.07 | Prototype benches only; not per-layer qualified |
| Beta | 0.3227..0.9748 | UQ1.23 across 25 actors |
| Threshold | 0.2863..0.7661 | Q7.16 |
| Weight absmax | 68.375 | Q7.16 decode; final_fuse largest |
| Stem inhibition strength | ≈0.01418 | Single enabled population |
| Adaptation strength / duration | ≈0.0116..0.0137 / 4.83..5.22 bins | 15 layers |
| Smoke state-error gate | 0.02 | Labelled smoke-only; not workload accuracy |
| Prior ASAP7 PLIF smoke max error | ≈0.00897 | Behavioral logistic compare |

Files: `artifacts/analog_asic/asap7/circuit_contract.json`, `asap7/stimuli/manifest.json`, updated `design.yaml`. Physical PLIF / ORFS still not ready.


## ASAP7 open-source bring-up update — 2026-09-23

ngspice 45.2 was built from official tag 45.2 (724dc77b9153dc75eaec474b1f7a44f1fcf5f362) with OSDI. Berkeley original BSIM-CMG 107.0.0 was downloaded from https://www.bsim.berkeley.edu/BSIMCMG/BSIMCMG107.0.0_20130712.tar.gz and compiled using OpenVAF 23.5.0. UC Berkeley copyright/license notices are retained; acknowledge UC Berkeley for this model implementation. This supersedes the earlier inference that only model111 was available. No commercial simulator/license was needed for basic device checks.

ASAP7 TT/SS/FF physical card parameters are preserved in generated OSDI syntax; NFIN=3 is the declared smoke geometry. Model selector/version metadata are adapted to the compiled 107 implementation. EOTACC's validation bound was widened from [0.1n:inf) to (0:inf) because the compiled original rejects ASAP7's 1e-10 value at that bound; equations and numerical card values are unchanged. This adaptation is documented in model_source_changes.json and is not HSPICE cross-validation.

Accepted TT checks: DC inverter transfer and transient switching. Five-millisecond retention tests with ideal external clocks and capacitors complete: 1pF drifts 15.149mV (0.2164 normalized units), 10pF 1.590mV (0.02271), 20pF 0.805mV (0.01149). Only 20pF meets the provisional 0.02-unit smoke limit for this one stimulus. This is not a chosen physical capacitor, general accuracy guarantee or layout area estimate. Dielectric leakage, mismatch and extracted parasitics are absent.

Codex 2026-09-23 `python scripts/test_asap7_analog.py` final `sampled_plif_external` JSON:
`{"bench": "sampled_plif_external", "simulation_completed": true, "exit_code": 0, "final_independent_value": 8e-05, "max_state_error": 0.008970758018200853, "spike_sequence_pass": true, "provisional_state_error_pass": true}`
Suite `all_simulations_completed=true`, exit 0. ASAP7 PLIF provisional smoke accepted (schematic; not extracted/layout). Prior soft k=50 midrail compare on bin-3 overdrive left commit under-subtracting θ; scale-normalized k=2000 plus capture track-hold fixed spike+state. SKY130 `sampled_plif` still passes (`max_state_error≈0.011`). Evidence: artifacts/analog_asic/asap7/results/compatibility_checks.json. full_orfs_ready remains false. Retention 1pF/10pF still fail provisional 0.02-unit ideal-C limit.


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

- Reused existing inhibition/adaptation physical checkpoints. Accepted 9/9 activity cases with zero unannotated pins. Six cases use 64 midpoint samples; inhibition 16, energy64 8, and energy128 4 are short smoke proxies after bounded timeouts. No synthesis/reroute; 120 s/stage limit unchanged.
- Mechanism-only scaled proxies at 200 bins/s: 0.010328 W dynamic and 41.909 W leakage. Short-sample energies are especially uncertain; not full-chip power.
- Hierarchy inventory conserved under `artifacts/ASIC/hard_hierarchy/` (160 masters with RTL generated, 1,579,600 instances). First exact actor master complete: `base_hm_actor__detail_stem__out_1x1__halo_2x2__offset__1__1` (3/480 views). Report: `artifacts/ASIC/primitive_characterization/base_140k_inventory/GATE_RESULTS.md`.

## 2026-09-21 — Existing 140k readout gate-power completion

The one-pixel six-class readout passes 49 checks after fixing testbench sampling to match the pre-edge reference trace. No RTL or layout change was required. Extracted-layout dynamic energy is approximately 194.782 pJ per ten-bin pixel prediction under the synthetic trace; leakage is 1.347116 uW. VCD annotates 45,229 pins; two unannotated coordinate outputs are verified zero. PLIF, convolution and readout results and explicitly partial scaling are recorded in `artifacts/ASIC/primitive_characterization/base_140k_inventory/GATE_RESULTS.md`. Full-chip layout remains incomplete; XL physical evidence remains secondary and unchanged.

> Current scope (2026-09-21): EventSpikeSeg140k epoch-80 seed-17 is the primary ASIC layout/simulation/estimate target. Useful XL layouts and reports are preserved for secondary work; XL figures are not 140k evidence. See [target policy](AGENTS.md#current-asic-target-policy--2026-09-21). Older entries are historical where superseded.

> **ASIC scope notice (2026-09-21):** Earlier full-DAG replay, native-profile,
> and representative-DSEC simulation entries below are retained only as
> historical audit evidence. They are retired from the active flow. Current
> ASIC results use full-model structural layout/inventory and routed per-block
> activity power multiplied by exact instance and operation counts; no
> full-model simulation result is active.

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

The top-ten, top-five, and top-three registries are all trained through `eventspikeseg.train`. Historical suites are pinned to the objective used for the recorded architecture-search results (`0.5 CE + 0.5 focal + 0.75 Dice`, plus historical auxiliary supervision). The final suite keeps total CE coefficient 1.0 but dynamically transfers weight from pixel CE to equal target-present-class macro CE, ramps Dice/boundary supervision up, and ramps auxiliary CE down by completed epoch fraction. Validation-on-train-holdout best-checkpoint selection and the canonical refinement schedule remain active. The old standalone `benchmark_top_three.py` runner is retired; its unique protocol has been represented in the shared trainer/launch configuration.


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
| `EventSpikeSegXL` | 978,559 |

Historical repeated-static experiments do not show a positive correlation between parameter count and mIoU: the 21,491-parameter structural model beat the 77,751- and 107,131-parameter alternatives, and the 24,211-parameter dual-path model beat the 63,147- and 108,781-parameter alternatives. This is evidence that parameter count alone was not the plateau cause, but it is not a ranking under the current temporal protocol. The balanced 978,559-parameter XL model is an unmeasured software capacity experiment, not a 50% mIoU claim. The current ASIC target is the 149,835-parameter, six-class `EventSpikeSeg140k` v8 model at native 440x640 resolution; this implementation choice is not a new accuracy result.

No new mIoU, pixel accuracy, spike-rate, latency, power, or FPGA-resource result is claimed for temporal-v2 yet.

## 2026-08-31 — ASIC/RTL verification results

The then-active epoch-35 six-class checkpoint exported 143,824 int8 convolution weights and 25
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

## 2026-09-01 — Native 440x640 real-event short-interval activity

The first 5 ms of the supplied `zurich_city_13_a/events.h5` was executed through the complete
25-actor integer DAG regenerated from the current epoch-40/seed-17 six-class V4 checkpoint
(training strategy v12). A provenance guard compares six checkpoint identity fields before every
profile so a replaced `.pt` cannot silently reuse stale weights. Because the sample does not
include its matching `rectify_map.h5`, coordinates were conservatively left unrectified and cropped
from sensor rows 0..479 to native model rows 0..439. This makes the run useful for implementation
stress and preliminary activity, but not publication-grade DSEC spatial preprocessing.

| metric | native 5 ms result |
| --- | ---: |
| retained input events | 41,839 |
| exact synaptic additions | 138,562,457 |
| actor-output spikes | 646,175 |
| final live sparse-state entries | 5,869,959 |
| Python bit-exact host runtime | 349.53 s |
| bottleneck actor | `final_fuse.standard` |
| bottleneck serial RTL service floor | 277,279,611 cycles |
| latency floor at 97.31 MHz tile clock | 2.849 s / 5 ms bin |
| deadline miss floor | 569.9x |
| ideal independent lanes/banks required floor | 570 |

The 97.31 MHz value comes from the isolated routed SKY130 actor tile and is not a full-chip clock.
The cycle result is a conservative bound derived from the implemented single-1RW-lane FSM and exact
native activity, not a full-native cycle-accurate RTL measurement. It is nevertheless sufficient to
reject the present one-lane actor organization for real-time operation. No full-model power number is
reported: the native graph has not been routed with characterized scale-suitable SRAM macros and no
post-route DSEC VCD/SAIF exists.

### Conflict-aware parallel-bank service result

The implemented parallel scatter and actor-local bank wrappers were configured from the same
native activity, then reprofiled by physical bank until every busiest-bank service floor met the
project's `U <= 0.8` engineering target. Ordinary actors use channel-by-spatial banks;
mechanism-enabled actors use spatial-only banks so inhibition/adaptation still updates all peer
channels atomically. The final manifest contains 1,718 independent actor lanes across the 25
resident populations, including 800 lanes for `final_fuse.standard`, 412 spatial lanes for
`down2.standard`, and 134 spatial lanes for `stem`.

| metric | measured configured-bank result |
| --- | ---: |
| exact synaptic additions (unchanged) | 138,562,457 |
| actor-output spikes (unchanged) | 646,175 |
| total configured actor lanes | 1,718 |
| `final_fuse.standard` lanes | 16 channel x 50 spatial = 800 |
| busiest configured actor/bank | `enc2_extra.depthwise` |
| busiest-bank service floor | 388,589 cycles |
| service-interval floor at 97.31 MHz | 3.993 ms |
| utilization floor | 0.79866 |
| hard real-time floor gate (`U <= 1`) | pass |
| engineering floor gate (`U <= 0.8`) | pass |

The lane-manifest SHA-256 is
`8ff8673edbe91a72142aaa95f6b91d530808013110f662700fcb3a92ff6c0519`; it matches the
native bank-activity profile and is embedded in the generated 25-actor top. This establishes a
conflict-aware lower bound on the sustainable bin service interval for this one unrectified 5 ms
sample. It is not cycle-accurate end-to-end DAG latency: completion-token critical-path delay,
inter-actor FIFO occupancy, routing timing, and full-chip clock degradation remain unmeasured.
It is also not a power or area result; 1,718 independently ported state/queue banks require a
scale-suitable characterized SRAM architecture and physical design before PPA can be reported.

### FIFO-buffered reduced-DAG replay

The generated graph now inserts an ordered depth-two FIFO on all 53 non-prediction edges. The
epoch-40 reduced 8x8 replay remains bit-exact after buffering and simultaneous full-FIFO pop/push
support. It completes in 12,186 steady-state cycles, eight cycles more than the prior 12,178-cycle
unbuffered replay. Seventeen edges reach occupancy two; the remaining 36 reach at most one. This
proves lossless ordering/backpressure and supplies a reduced-fixture lower limit for edge depth.
It does not size native-resolution FIFOs or change the native 388,589-cycle busiest-bank floor.

### Completion-token critical-path correction and reprofile

The PLIF commit for an actor begins only after every required same-bin upstream completion token
has arrived. Therefore, the longest dependency-path sum of configured-bank commit costs is a
response-latency lower bound even though current collection can overlap upstream activity. On the
1,718-lane throughput configuration this floor is 1,050,545 cycles (10.796 ms at 97.31 MHz), so
that configuration cannot meet a 5 ms single-bin response deadline.

A candidate with additional spatial banks on eight critical actors was generated from measured
commit imbalance with a 1.10 extrapolation safety factor, then rerun through the exact full native
integer event profile. The accepted mapping contains 1,966 lanes.

| metric | exact reprofiled 1,966-lane result |
| --- | ---: |
| retained input events | 41,839 |
| exact synaptic additions | 138,562,457 |
| actor-output spikes | 646,175 |
| busiest complete actor bank | `final_fuse.standard` |
| busiest-bank service floor | 384,334 cycles |
| busiest-bank interval at 97.31 MHz | 3.950 ms (`U=0.78992`) |
| commit-only completion critical path | 349,094 cycles |
| commit-only latency floor at 97.31 MHz | 3.587 ms (`U=0.71749`) |
| hard/80% floor gates | pass / pass |

The accepted mapping SHA-256 is
`172121ae49208c034d95314ab65b1cf6cb1975f7a7166d78f558f830f6ff003d` and is embedded in the
generated top. This is stronger than the prior bottleneck-throughput result but still is not a
cycle-accurate full-DAG latency measurement: collection backpressure, 53 edge FIFOs, routing/join
logic, temporal readout, and full-chip physical timing are excluded. The same unrectified,
single-bin sample limitation applies.

### Native edge serialization floor

Graph-conserved edge accounting finds 657,634 data events on
`final.concat -> final_fuse.standard`; its ordered completion token is packet 657,635. Since the
implemented generated edge is scalar, this alone requires at least 657,635 clocks, or 6.758 ms at
97.31 MHz (`U=1.35163`). It fails the 5 ms hard deadline despite the state-bank service and
commit-path floors passing. At least two packet lanes are required at that clock; alternatively,
the scalar link requires at least 131.527 MHz for the hard deadline or 164.409 MHz for the 80%
engineering target. These are volume/clock bounds, not routed timing or FIFO occupancy results.

### Cost-refined 200 MHz target mapping

The target ASIC clock in the predictive ASAP7 flow is 200 MHz, providing 1,000,000 hard cycles or
800,000 cycles at the 80% engineering limit. A first 917-lane cost candidate was rejected by exact
native reprofiling (`stem`: 1,176,798 cycles; completion chain: 897,040 cycles). The second
iteration uses 924 lanes and passes all independently measurable workload floors:

| metric | exact 924-lane activity result at 200 MHz |
| --- | ---: |
| busiest complete actor bank | `final_fuse.standard` |
| busiest-bank service floor | 781,772 cycles / 3.909 ms (`U=0.78177`) |
| commit-only completion critical path | 737,691 cycles / 3.688 ms (`U=0.73769`) |
| scalar edge serialization floor | 657,635 cycles / 3.288 ms (`U=0.65764`) |
| hard/80% floor gates for all three | pass / pass |
| configured independent actor lanes | 924 |

The mapping SHA-256 is
`81f8381ec225b82d5f03965e5a9415bb7e07b1126a4072497906f4037860f257`; it matches the exact
candidate-2 profile and generated full top. Compared with the 1,966-lane 97.31 MHz mapping, this
reduces independent lane count by 53.0%. It is conditional on full-chip 200 MHz timing closure and
does not yet combine collection stalls, scatter contention, FIFO occupancy, joins, and readout in
one cycle schedule. The routed 200 MHz evidence remains the reduced SRAM-free ASAP7 actor
prototype, so these numbers are implementation targets and workload floors—not measured full-chip
latency or power.

The maximum of the three independent floors is 781,772 cycles, implying at least 156.354 MHz for
the hard deadline or 195.443 MHz for the 80% target. Thus 200 MHz has only 2.28% frequency margin
over the independent-floor target. This envelope still does not combine contention or
backpressure, so it is a go/no-go prerequisite rather than the final timing result.

### Event-order scatter/bank timing result

The next profiler models the implemented scatter and bank-ready sequence for every event instead
of comparing aggregate counts independently. The 924-lane target is rejected:

| actor | isolated collection | collection + busiest commit | time at 200 MHz |
| --- | ---: | ---: | ---: |
| `down2.standard` | 40,097,168 cycles | 40,107,810 cycles | 200.539 ms |
| `stem` | 6,560,029 cycles | 6,593,614 cycles | 32.968 ms |
| `final_fuse.standard` | 1,842,152 cycles | 1,875,150 cycles | 9.376 ms |

This is not yet whole-DAG timing, but it is sufficient to reject the current collection fabric.
Mechanism actors serialize same-pixel output channels behind one spatial contribution port, while
ordinary actors allow one busy bank to hold the single pending-event bitmap. The implied 10.027 GHz
80%-target clock for the current `down2.standard` organization is physically irrelevant and is
reported only as proof that frequency scaling is not the remedy. Accumulation must be
channel-by-spatial banked and decoupled; peer-channel atomicity is required at mechanism commit,
not at every synaptic addition.
# Resident full-model elaboration boundary (2026-09-02)

The checkpoint-authoritative resident generator emitted the complete 25-PLIF actor DAG with all
143,824 int8 synaptic weights. A bounded native Icarus elaboration attempt was killed by the 8 GB
Docker memory limit (exit 137) before event simulation. Therefore there is currently **no valid
native resident latency or power number**. Reduced actor and routing tests establish RTL behavior,
and representative synthesis establishes synthesizability only; neither is a full-chip PPA result.

## Resident 8x8 spatial partition inventory (2026-09-02)

| quantity | exact value |
| --- | ---: |
| PLIF actors | 25 |
| nominal spatial tile | 8x8 locations |
| spatial actor tiles | 20,410 |
| logical PLIFs | 30,976,000 |
| resident state | 1,590,476,800 bits |
| byte-equivalent resident state | 198,809,600 bytes |
| actor convolution weights | 143,728 int8 |
| temporal-readout weights | 96 int8 |

These are inventory values, not SRAM capacity or PPA. The state bits are dedicated local current,
membrane, and (where enabled) adaptation elements. The ignored derived manifest is
`artifacts/ASIC/resident_tile_plan_8x8.json`; its generator and conservation test are tracked.

## Preliminary routed 2x2 `detail_stem` resident unit (2026-09-02)

This checkpoint-exact ASAP7 run uses all 144 trained actor weights and 32 resident PLIFs. It is a
characterization unit, not the production 8x8 tile and not a full-model result.

| routed quantity | result |
| --- | ---: |
| standard-cell instance area | 7,247.19 um^2 |
| core area / utilization | 21,139.7 um^2 / 34% |
| sequential cells | 1,337 |
| multi-input combinational cells | 56,841 |
| extracted setup / hold violations | 0 / 0 |
| reported internal fmax | 772.241 MHz |
| global routing overflow / detailed-route DRC | 0 / 0 |
| vectorless power at 0.77 V, 200 MHz | 30.9699 mW |
| worst VDD drop | 3.579 mV (0.46%) |
| final max-slew violations | 68 |

The run is **not timing-clean**: violating internal slews are 321.65--360.29 ps against 320 ps.
It also copied the older SDC before the resident-specific port constraints were introduced. Power
uses default vectorless switching, not the Zurich DSEC trace. Therefore the area/routability result
is usable as preliminary evidence, while latency and power remain non-publication estimates pending
a resident-SDC rerun with slew over-repair and an activity-annotated run.

## Clean routed 2x2 `detail_stem` resident unit (2026-09-02)

The accepted checkpoint-exact ASAP7 characterization uses the same 144 trained int8 weights and
32 resident PLIFs, the resident-port SDC, and a 50% OpenROAD slew-repair margin. The margin is an
integer percentage; exploratory 1.2% and 20% runs left 27 and 8 extracted slew violations.

| routed quantity | accepted result |
| --- | ---: |
| standard-cell instance area | 7,311.29 um^2 |
| core area / utilization | 21,139.7 um^2 / 34.59% |
| sequential cells | 1,337 |
| multi-input combinational cells | 56,841 |
| timing-repair buffers | 970 |
| extracted setup / hold violations | 0 / 0 |
| max slew / fanout / capacitance violations | 0 / 0 / 0 |
| worst max-slew margin | +90.03 ps against 320 ps |
| reported internal fmax | 639.636 MHz |
| global routing overflow / detailed-route DRC | 0 / 0 |
| vectorless power at 0.77 V, 200 MHz | 30.9607 mW |
| worst VDD drop | 4.453 mV (0.58%) |

This closes the physical implementation check for the 2x2 characterization unit only. The power
uses OpenROAD's default vectorless activity, not DSEC switching, and cannot be multiplied by 20,410
tiles into a defensible full-chip result. Likewise, 639.636 MHz is an internal tile clock result,
not measured 25-actor DAG throughput or event latency. Full-model layout and
per-block activity-annotated energy remain open.

## Retired history: exact XL 50 ms integer actor-DAG run (2026-09-08)

The implementation and generated outputs for this whole-model simulation were removed on
2026-09-21. This section remains only as an audit record and is not an active workflow or artifact.

The epoch-1 structural XL export completed all 44 actors for ten chronological 5 ms bins in the
CPU verification Docker image. This is an exact fixed-point functional/activity result for the
exported graph, not dense RTL timing, trained-model accuracy, or ASIC power.

| quantity | result |
| --- | ---: |
| retained input events | 428,367 |
| bins / physical interval | 10 / 50 ms |
| actor executions | 440 |
| synaptic contributions | 22,175,363,899 |
| actor output spikes | 53,988,002 |
| summed per-actor maximum live state entries | 45,516,001 |
| host workers | 4 |
| host execution time | 15,308.731 s (4.252 h) |
| final prediction | 440x640 `uint8` |
| prediction raw-array SHA-256 | `6b5854b29c157134d43fecb998548ac1341b16e70838868525133021c2c25385` |

The predicted class histogram is `{0: 29975, 1: 10306, 4: 4046, 5: 143409,
6: 17878, 7: 17804, 8: 44122, 9: 14060}`. Classes 2, 3, and 10 receive no winning pixels in
this epoch-1 sample. The source used an unrectified sensor-coordinate crop because no rectify map
or aligned label accompanied the sample, so no mIoU/pixel-accuracy claim is possible. The JSON
sets `cycle_latency_available`, `power_activity_available`, and `capacity_claim` to false.

## Revised current-precision two-tile ASAP7 result (2026-09-08)

| routed quantity | result |
| --- | ---: |
| precision | Q7.16 weights, int32 Q15.16 combined accumulator |
| resident PLIFs / child tiles | 64 / two 2x2 tiles |
| standard-cell area | 18,018.2 um^2 |
| core area / utilization | 52,373.2 um^2 / 34.4034% |
| reported internal fmax | 589.378 MHz |
| setup / hold slack at 5 ns | +3,303.3 ps / +38.2417 ps |
| setup/hold/slew/cap/fanout/DRC violations | 0 / 0 / 0 / 0 / 0 / 0 |
| vectorless power at 0.77 V, 200 MHz | 700.516 mW |
| worst VDD drop | 49.2562 mV |

This supersedes the earlier lower-precision two-tile result for current implementation decisions.
Its default-toggle power cannot be treated as event-driven energy or extrapolated to the complete
140k/XL graph. The retained reproducibility bundle contains final ODB, GDS, DEF, SPEF, Verilog,
SDC, and reports; regenerable stage databases and the duplicate merged GDS were removed.

## Exact receptive-halo wiring inventory (2026-09-02)

The production 8x8 resident wrapper now statically connects each tile only to input locations that
can reach one of its outputs under the actor's exported kernel, stride, padding, and dilation.

| checkpoint-derived 25-actor inventory | exact value |
| --- | ---: |
| resident output tiles | 20,410 |
| receptive-halo tile-input bit endpoints | 51,871,626 |
| full-bitmap-per-tile bit endpoints avoided baseline | 73,444,096,000 |
| logical endpoint reduction | 99.929% |

The endpoint counts include input channels and tile overlap. They quantify elaborated static
connectivity, not unique source bits or physical routed wire length. No power or latency reduction
is claimed until a representative multi-tile wrapper and ultimately the complete graph are routed
and exercised with DSEC switching activity. All 96 Python tests, 47 cocotb RTL groups, Verilator
lint, and 40-top compile check pass with this wiring.

A checkpoint-exact two-column `detail_stem` hierarchy (two 2x2 tiles, 64 resident PLIFs, all 144
trained actor weights) also passes Yosys process lowering, memory lowering, optimization, and
structural checking. This establishes synthesis legality across a real tile boundary; it is not a
routed area, frequency, power, or latency result.
## Full-float analog reference and first real-data trace — 2026-09-24

### Switched-capacitor float mapping update — 2026-09-24

Corrected a bookkeeping error in the earlier pulse/SC mapping screen: the analog parameter archive's `weight__*` arrays already include the exported ChannelAffine gain, so multiplying by `affine_gain__*` a second time understated/warped the effective coefficients. `scripts/analyze_sky130_pulse_float_mapping.py` now uses those arrays directly. The full-float inference replay separately reads raw checkpoint convolution weights and applies the runtime affine once, so its circuit sensitivity cases were not using QAT or quantized values. The corrected pulse service medians are 0.19/6.58/15.94ms for stem/enc1/final_fuse; 61.6% and 77.6% of active enc1/final_fuse destinations exceed 5ms before setup. This makes the pulse-only path still less suitable than the superseded screen suggested.

The corrected full-software replay applies the 1/3/10µm measured switched-capacitor packet curve only to `final_fuse.standard`, omitting coefficients whose needed packet is below the 1µm measured floor. On three 64×64 patches from one real DSEC training frame, candidate headroom 0.15/0.30/0.60V gives 53.23/36.55/25.92% omitted static coefficients, 6.41/4.53/3.08% final-fusion spike-bit mismatch, and 89.01/92.33/93.84% pixel argmax agreement against the float software model. This is not segmentation accuracy and does not measure a fabricated circuit; the cap-area curve is based on three TT schematic sizes, all earlier network layers remain ideal software, and there is no noise, mismatch, PVT, physical minimum-cap or extracted parasitic model. It shows a material sensitivity to the measured packet floor that must be reduced before claiming an analog match. Data: `model_reference/float_patch_trace.json` (`measured_mim_cap_floor_software_replay`) and `results/sky130_float_pulse_mapping_screen.json`.

The top-plate swing characterization was repeated with each amplitude isolated and a matched same-phase no-event integrator to subtract startup/feedthrough drift (~7.38µV). After this subtraction, both signs are monotonic from 5 to 300mV and their magnitudes converge: at 5mV the increments are −0.542/+0.778µV (35.8% pair mismatch), at 40mV −5.293/+5.541µV (4.6%), and at 300mV −40.372/+40.651µV (0.69%). This indicates usable fine charge in the schematic after baseline removal, but the baseline cell is not implemented or mismatch-qualified; at the 5mV point the remaining sign asymmetry is material relative to learned threshold margins. A same-phase no-event-subtracted 0.25/0.5/0.75/1/3/10µm MIM geometry sweep at ±0.3V is monotonic for both signs: response magnitudes grow from 4.48/4.64µV at 0.25µm to 40.37/40.65µV at 1µm and 3.100/3.101mV at 10µm. The PDK model accepts fractional geometry parameters, but the local checkout lacks MIM physical design rules/PCell evidence; sub-1µm structures remain schematic sensitivities only. The corrected full-float final-fusion replay uses the baseline-subtracted 1/3/10µm curves: at 0.15/0.30/0.60V headroom, 54.6/37.4/26.1% of static coefficients remain below the 1µm packet floor; final-stage spike mismatch is 5.28/3.77/2.55%, with 91.87/93.55/94.17% pixel argmax agreement on three patches. An SC-plus-pulse hybrid still assigns no sub-floor coefficients to pulses because the measured 0.05µs pulse minimum exceeds the required same-headroom fine charge. A follow-up at 0.75/0.90/1.05V initial state shows the no-event term varies only 7.291–7.440µV (~0.15µV span); corrected 20mV packets are −2.570…−2.588µV / +2.796…+2.801µV and corrected 300mV packets are −40.234…−40.372µV / +40.651…+40.670µV. This is nominal TT repeatability using ideal `.ic` state setup, not physical init or PVT. The physical init/hold follow-up changes the gate: direct TG initialization followed by always-connected OTA causes 0.259–0.326V state error at the pre-packet sample. A new held-output/VCM-summed-node variant reduces this to 0.050–0.117V in its default bias, but its no-event drift is 1.6–2.0mV. A 3×3 output-stage/tail-bias sweep and a finer 4×2 sweep from Vbp=0.84–0.90V found no satisfactory point: the best state match (4.3mV error at Vbp=0.90V, Vbn=0.65V) drifts 49.4mV over the same interval; the lowest-drift point in the fine sweep (7mV at Vbp=0.84V, Vbn=0.65V) still has 62mV state error. Thus the baseline-subtracted packet transfer is a useful local transfer sensitivity only; state initialization/hold is currently failing and blocks a real analog mapping. Next debug the OTA output operating point and state-isolation phase before optimizing offset cancellation. Evidence: `results/sky130_sc_packet_original_init_sweep.json`, `results/sky130_sc_packet_state_sweep.json`, `results/sky130_sc_output_bias_sweep.json`, `results/sky130_sc_output_bias_fine_sweep.json`, and the experimental `sky130_sc_charge_integrator_held` subcircuit in `asic/analog/sky130_sc_charge_integrator.spice`. The matched-baseline correction remains a candidate, pending physical implementation and variation testing. Evidence: `results/sky130_sc_packet_amplitude.json`, `results/sky130_sc_packet_original_init_sweep.json`, `results/sky130_sc_packet_state_sweep.json`, `results/sky130_sc_output_bias_sweep.json`, `results/sky130_sc_small_cap_geometry.json`, `results/sky130_float_pulse_mapping_screen.json`, and `model_reference/float_patch_trace.json`.

The analog reference now uses `EventSpikeSeg140k_seed17_best.pt` (best epoch 58 of the 80-epoch run; `is_best=true`), SHA-256 `c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7`. Epoch 80 remains a comparator (`is_best=false`, SHA-256 `c9d1edee4ee3742c65c39111859fb76d81706fd80cdbe941bc377a8e7940704d`). The checkpoint metadata lacks ASIC-QAT fields; the analog exporter explicitly disables the model's QAT path and exports float32 arrays directly. No quantized exporter or quantized checkpoint is used. It contains folded effective weights for the exact 25 inference actors (143,824 synaptic weights), channel-affine gains, learned beta/threshold, applicable inhibition/adaptation values, and the temporal readout: `model_reference/eventspikeseg140k_float_reference.json` + `.npz`. The model source hash and archive are in the manifest.

One bounded software forward used a real training record (`zurich_city_00_a`, frame 1), split into low/median/high event-density 64×64 patches, retaining all 10 updates of the 50 ms record. Selected-stage spike rates were 10.7% (`stem`), 21.3% (`enc1.standard`) and 26.1% (`final_fuse.standard`). Absolute weighted-current p50/p90/p99/p99.9 were respectively [0, 7.23, 47.8, 143.5], [7.39, 48.5, 108.7, 150.7], and [268.6, 775.0, 2,426.3, 3,072.3] model units across the combined patches and timesteps. This establishes that the current input scale is large and activation dependent; it does not yet say how many individual synaptic pulses are needed, whether analog clipping changes spikes, or whether the sample is representative. Reproduce with `scripts/analyze_sky130_float_patch.py`; data and selected-stage traces are in `model_reference/float_patch_trace.json` + `.npz`.

The extended pulse-width operating-range screen completed for 24 cases: starting membrane voltages 0.75/0.90/1.05V, both signs, logical widths 0.05/4/100/500µs. Both polarities remained correctly signed and monotonic at all three starting voltages. At 500µs logical duration (3.5ms physical positive, 500µs negative), positive deltas were 0.658–0.664V and negative deltas −0.588 to −0.652V. The sign gain and state dependence are not yet matched to float model contributions; long pulses use much of a 5ms bin and the result is a single-pulse TT screen only. Bench/report: `scripts/test_sky130_ms_pulse_width_operating_range.py`, `sky130_ms_pulse_width_operating_range.json`.

Model equation correction from source inspection: the float PLIF uses SpikingJelly with `decay_input=False`, hence `candidate = beta * previous_post_reset_state + weighted_current` (beta attenuates prior state only). The current is a signed sum of synaptic weight × presynaptic activity; raw event ingress can carry multiplicity. Analog weights will be calibrated to this full-float behavior. QAT and Q7.16 precision are not the analog requirement.

Reset semantics are another concrete gap. The float checkpoint uses subtractive reset (`candidate - threshold`), while the existing PLIF SPICE variants use a transmission gate that returns the membrane to VCM. Replaying the captured `final_fuse.standard` float currents with subtractive reset reproduces all 1,966,080 recorded spike bits; replacing it with hard reset-to-VCM changes 32,278 bits (1.64%) in that fixed-current, 10-step trace. A new pulse-duration soft-reset channel variant and bounded negative reset-charge screen were added. With one nominal reset-width slope, 9 cases across three starting states and 60/100/150mV reset steps had up to 15.9% reset-step error; the provisional 15% screen narrowly fails. This is not full-model equivalence; the reset path needs state-dependent calibration or a different reset circuit. Evidence: `model_reference/float_patch_trace.json` (`reset_semantics_screen`) and `sky130_ms_soft_reset_pulse.json`.









Updated physical-init sequence results (2026-09-24) supersede the held-variant init failure described above. The physical init TG was held for 2.5µs, followed by a 0.5µs guard before OTA reconnection; this removes the old init/OTA overlap and gives the large 100×100µm² feedback capacitor adequate settling time. Across 0.75/0.90/1.05V requested states, physical init error is ≤109µV. With OTA and packet switches disabled, 5ms idle retention error is ≤0.247mV. A signed ±0.3V event after the 5ms hold and corrected phase order (connect, settle, raise packet top plate, open packet-bottom and OTA switches, then return top plate) produces −41.0…−41.3µV / +41.1…+41.2µV corrected state increments on the 1µm packet. A 10µm diagnostic produces ±3.102mV. Returning the top plate while the packet bottom remains connected reverses/cancels the contribution; the packet bottom must disconnect first. Reconnect common-mode drift is 17.5–30.2µV across starting states and is removed here only by a matched no-event simulator control, not an implemented calibration circuit. Evidence: `results/sky130_sc_packet_state_sweep.json`, `results/sky130_sc_physical_retention_sweep.json`, `results/sky130_sc_physical_retention_packet_sweep.json`. These nominal TT schematic tests establish neither PVT/mismatch/noise performance nor MIM layout legality, extracted retention, 140k workload precision or silicon readiness. Next test repeated signed packets/order/reset and compare measured state changes against the short full-float trace.

The subsequent two-packet physical sequence test reuses the transistor-initialized held-output cell, with packet reset to VCM between events and phase-safe packet-bottom/OTA disconnect before each top-plate return. For `pp`/`nn`/`pn`/`np` pairs from each 0.75/0.90/1.05V start, corrected same-sign changes are about −82.2…−82.5µV / +82.4…+82.9µV; mixed-sign residuals are within 0.43µV. Relative to two 1µm single-event increments (±41.15µV nominal), maximum accumulation error is 0.621µV; `pn` versus `np` order difference is 0.075µV. Physical init error remains ≤109µV. Evidence: `results/sky130_sc_physical_accumulation.json`. This establishes short-interval repeated-event accumulation/reset reuse only: events are microseconds apart, not spread through a 5ms bin, and the no-event drift is removed with a matched simulator control. The next analog check is to space two packets across a realistic bin before using these values in the full-float error sensitivity screen.

The 5ms-spaced sequence (`sky130_sc_physical_long_bin_accumulation.json`) uses events at 0.5ms and 4.5ms, with a sample after the second event at 5ms. The first-event increment changes by at most 0.56µV during the intervening ~4ms isolated hold. After a matched no-event simulator subtraction, same-sign totals are −65.32/+65.27µV, mixed-sign residuals +2.31/−1.90µV, maximum sum error against two ±41.15µV single-packet increments 17.03µV, and `pn`/`np` order difference 4.20µV. Each no-event OTA reconnect contributes large state offset; two windows move the membrane output by −15.67mV, which this analysis removes only with a simulator reference. This blocks mapping without a real cancellation or revised reconnect topology.

Two bounded reconnect experiments did not remove that error. A 0.5µs OTA feedback tail after packet return reduces the first-packet hold change to 0.56µV, but total sum error grows to 17.03µV (`sky130_sc_physical_long_bin_accumulation.json`, updated run). Sleeping the OTA by switching both bias inputs during hold lowers that drift to 0.24µV, but retains −14.64mV common reconnect shift and 17.37µV sum error (`sky130_sc_physical_long_bin_sleep_accumulation.json`). A 0.5µs ramp on the bias rails lowers hold drift to 0.10µV but retains −14.54mV common shift and 16.90µV sum error (`sky130_sc_physical_long_bin_sleep_ramp_accumulation.json`). Precharging the OTA output to the membrane while awake destabilizes the held state (711.7mV common shift, 36.01µV max sum error); combining precharge with bias sleep is worse (890.36mV shift, 44.60µV sum error). These are experimental schematic variants; the underlying OTA reconnection/offset issue remains open.

The float replay now anchors its 1µm packet point to the physically initialized/held packet test: 41.156µV positive-step magnitude and 41.168µV negative-step magnitude. Mapping only `final_fuse.standard` on the same three real training-record patches gives 5.325/3.947/2.605% final-stage spike mismatch and 91.805/93.319/94.092% pixel argmax agreement at 0.15/0.30/0.60V headroom. This is still a cap-floor software sensitivity replay, not analog-model accuracy. Evidence is in `model_reference/float_patch_trace.json`; the exact physical sequence and failed alternatives are in the JSON reports under `results/sky130_sc_physical_*`.

The matched differential-reference circuit (`scripts/test_sky130_sc_differential_reference.py`) duplicates the physical-init held integrator and runs a no-packet reference beside each packet-driven signal cell. Its four-resistor SKY130 OTA readout is referenced to VCM and measures `VCM + reference − signal`. Continuously connected readout has <0.83µV output relation error, but its input loading shifts the same-sign two-packet transfer to 57–59µV and mixed-sign order residual to as much as 9.1µV. A late-switched version keeps both membrane nodes isolated during accumulation, then connects the readout at 4.5025ms. All `pp`, `nn`, `pn` and `np` runs completed in TT: same-sign differential changes are −63.839/+63.540µV, mixed-sign residuals +1.635/−1.821µV, and readout relation error is 0.50–0.54µV. Same-sign transfer is within ~2% of the unloaded 65.2µV result; the common reconnect shift remains about 15.4mV on each cell and is rejected at the VCM-referenced output. This is the best analog approach so far, but its readout is sampled once at the end of the bin and requires phase timing. A bounded replay of the ordinary full-float best checkpoint and same three DSEC patches, anchored at half the sampled readout swing per event (31.65µV positive, 32.03µV negative), gives final-fuse spike mismatch of 4.414/3.155/1.782% and pixel argmax agreement of 92.773/93.791/94.393% at 0.15/0.30/0.60V headroom. This is local sensitivity, not task accuracy or full analog inference. Evidence: `results/sky130_sc_differential_reference_sampled_{pp,nn,pn,np}.json`, `model_reference/float_patch_trace_sampled_diffreadout.json` + `.npz`, and the direct-readout reports. Nominal TT only; mismatch, PVT, noise, layout/extraction, area, energy and throughput remain unqualified.

A limited process-corner follow-up exposes a calibration requirement. At gain ratio 1.0, the sampled readout tracks `pp` within 0.61µV in TT and 1.68µV in FF, but under-gains SS by 17.37µV. At SS, ratio 1.35 reduces the error to +1.07µV; the same ratio in TT over-gains by 21.49µV. Resizing the OTA input stage between 10/20/4, 12/24/5 and 11/22/4.5µm did not provide a single solution across corners. Therefore a fixed readout ratio is not qualified: either use a selectable per-die gain calibration or replace the readout with a more robust low-loading topology. The present 1GΩ resistor network is an ideal SPICE element without resistor geometry, so it has no area or layout feasibility evidence. This is now the active blocker before mismatch/layout qualification. Evidence: `results/sky130_sc_differential_reference_sampled_ss_pp.json`, `..._sampled_ss_pp_g1p35.json`, `..._sampled_tt_pp.json`, `..._sampled_tt_pp_g1p35.json`, and `..._sampled_ff_pp.json`.

## Capacitor-only readout and OTA sensitivity — 2026-09-25

Tested a passive MIM differential sampler as an alternative to the ideal 1GΩ OTA readout (`scripts/test_sky130_sc_cap_differential_sample.py`). In the 10µm case (203.8fF estimated from typical SKY130 MIM area/perimeter density), the bottom-plate sequence disturbs the membrane differential by 2.5–3.9µV during the 100µs sample/hold window. The output includes a large nominal feedthrough offset (about −0.466mV in the no-event case); a VCM-only dummy does not cancel it within a run. Across four packet orders, subtracting a separate no-event simulator control from the paired real-minus-dummy reading recovers the corresponding state change to 0.05–0.09µV at TT. This is only an offline control subtraction, not an implemented baseline circuit. A smaller 1µm sampler shows severe feedthrough (about −27.1mV) and is rejected. At 30µm (1.811pF estimate), the `pp` output/control delta agrees with the state delta within 0.14µV, with an 8.1µV differential disturbance; however, its estimated kT/C voltage scale at 300K is still 47.8µV RMS, close to the ~55µV two-packet signal. The 10µm kT/C scale is 142.6µV RMS, above the signal. These are thermal-noise estimates, not simulated transient-noise results; larger caps reduce this noise but increase membrane loading. Passive sampling is not accepted as a low-noise solution.

A direct OTA input-sensing screen (`scripts/test_sky130_sc_ota_diff_sensitivity.py`) avoids a passive sampling capacitor at the input. With the present 10/20/4µm input stage and tuned 2/27.8µm second stage, a ±64µV differential at 0.9V common mode moves the output by −314/+323mV (incremental gain about −4.9k to −5.0k V/V). At ±250µV the output approaches 0.18/1.70V and is strongly nonlinear; this is a high-gain detector, not a linear state readout. Next tune a closed-loop or time-integrating differential readout for useful range and offset handling, then characterize its noise and corners. Evidence: `results/sky130_sc_cap_differential_sample_{pp,nn,pn,np,zero}_10p0um_bp.json`, corresponding `.dat` waveforms, `results/sky130_sc_cap_differential_sample_{pp,zero}_30p0um_bp.json`, and `results/sky130_sc_ota_diff_sensitivity.json`.

### Late OTA comparator timestep and event-order follow-up — 2026-09-25

The minimum-width (`win=0.5µm`) late-switched OTA comparator was rechecked at a 10ns maximum timestep with input-gate precharge set to the measured 5ns membrane common mode (0.8882V), rather than accepting the earlier optimistic 100ns result. In `pp`/`nn` same-sign cases, the comparator-minus-matched-reference output has the correct state sign and membrane differential disturbance is −0.158/−0.190µV. In mixed `pn`/`np` cases, disturbances are −0.170/−0.172µV, but the near-zero `np` state (−1.953µV at comparison) is reported positive: output difference is +6.162mV. `pn` (state +1.634µV) is reported positive with +6.848mV output difference. Thus the current paired-reference comparator does not reliably resolve the mixed residual; a millivolt-level output baseline difference dominates the sign, while the sampled state kick is itself close to the previously inferred ~0.18µV full-float sensitivity margin. The apparent near-zero disturbance at 100ns did not reproduce at finer timesteps. Evidence: `results/sky130_sc_ota_plif_comparator_{pp,nn,pn,np}_w0.5_t1.5us_p0p8882_s10n.json` and `scripts/test_sky130_sc_ota_plif_comparator.py`.

This blocks the present direct late-sampling comparator, not the SC integration path. Continue with an explicit threshold/reference and offset-zeroing phase, seeking a decision margin at the learned float threshold while keeping membrane kick below its measured error budget. Then use a fast representative integration-window test, event-order replay and full-float sensitivity before corner/mismatch work. These results are nominal TT schematic evidence only: no device mismatch, transient noise, extracted parasitics or physical layout qualification.

### Buffered threshold readout and matched-baseline calibration — 2026-09-25

The direct late OTA sign comparator and direct threshold-shifted comparator were not reliable at 10ns; mixed `np` was wrong-sign even after a +10.9µV reference shift. A different readout was tested while preserving the switched-capacitor membrane integrator: late-connect the two held membrane outputs to separate unity-feedback OTA buffers, then use a physical SKY130 xhigh-poly feedback OTA and a matched same-common-mode baseline OTA. Open the membrane sample transmission gate before reconnecting the gate precharge (100ns nonoverlap) and keep OTA bias on across that interval. This phase ordering reduced the mixed-state membrane kick and isolates feedback resistors from the membrane nodes.

At a 10ns timestep, with the reference membrane initialized +10.9µV above the signal cell (the prior median final-fusion threshold estimate at 0.30V candidate headroom), gain trim 10.1, and 1MΩ/approximately 9.1MΩ xhigh-poly feedback network, the two mixed orders both remain below threshold and have the correct baseline-subtracted output sign:

| order | differential before readout (µV) | at comparison (µV) | after (µV) | readout relation error (µV out) | input-equivalent error (µV) | decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `pn` | −7.955 | −7.976 | −7.917 | +1.155 | +0.114 | below threshold |
| `np` | −11.688 | −11.652 | −11.600 | +1.101 | +0.109 | below threshold |

The largest mixed-case membrane shift from before to comparison plus input-equivalent readout error is 0.145µV, just below the provisional 0.18µV error margin. The after-window state kick is 0.038/0.088µV. With the same 10.1 gain, 100ns coarse `pp`/`nn` tests report below-/above-threshold signs correctly at −74.704/+55.752µV; these high-margin same-sign decisions have 0.647/0.521µV end-window disturbance and are not fine-step qualified. Fine-step gain-10.2 screens at threshold10.9 also got all four signs right, but 10.1 is preferred by the finer mixed-case calibration. Data: `results/sky130_sc_ota_buffered_diffreadout_{pn,np}_s10n_rg1m_g10.1_bw4p0_th10.9uv.json` and `results/sky130_sc_ota_buffered_diffreadout_{pp,nn}_s100n_rg1m_g10.1_bw4p0_th10.9uv.json`; runner: `scripts/test_sky130_sc_ota_buffered_diffreadout.py`.

These were the provisional analog readout results at that checkpoint, not a qualified neuron. The threshold reference in those specific runs was an ideal initial voltage shift, the same-common-mode baseline was a second amplifier rather than a fabricated auto-zero circuit, and the two same-sign traces used100ns integration steps. The later physical-DAC threshold screen is described below; mismatch, transient noise, PVT, extracted layout, area/power, full-float weight replay and population timing remain open. The direct comparator, input-chopped OTA and narrower-buffer variants remain failed experiments; retain their results but do not select them.

### Full-float spike sensitivity using the measured mixed-case error envelope

The measured worst combined membrane shift plus input-equivalent readout relation error (0.145µV) was applied as a uniform threshold perturbation to the recorded full-float `final_fuse.standard` candidate/threshold/spike tensors from the best checkpoint. The exact NumPy replay (`scripts/analyze_sky130_buffered_readout_sensitivity.py`) gives 0.0423%/0.0395% spike-bit mismatch for positive/negative error at 0.30V candidate headroom, 0.0818%/0.0920% at0.15V, and 0.0218%/0.0176% at0.60V. This supports continuing with 0.30V or greater headroom in this sampled-stage sensitivity screen; 0.15V approaches the provisional 0.1% spike-bit budget. This is a uniform static-error perturbation on three 64×64 patches from one DSEC training frame, not a circuit replay or segmentation metric; dynamic kick, threshold DAC spread, other layers, PVT, mismatch and noise are not included. Evidence: `results/sky130_buffered_readout_float_sensitivity.json` and `model_reference/float_patch_trace.json`.

### ABBA chopped buffered readout with physical membrane pair — 2026-09-25

The amp-only ABBA chopper was checked at both polarities and 0.8884V common mode. With the old feedback length3078µm, the circuit delivered ~9.4× rather than the intended10.1×; this explained the apparent ~0.1–0.16µV readout error. A feedback length3445µm brings amp-only gain closer to target. At 1.411µV input differential, tuned TT/SS/FF process, TT high/low xhigh-poly resistor, and TT −40/125°C screens all retained sign; maximum input-equivalent error relative to10.1× was0.068µV. These amp-only corner tests have no physical membrane or mismatch/noise/extraction.

The corrected ABBA phase schedule was integrated with the physical switched-capacitor membrane and run over the 5ms two-event `pn` and `np` sequences at10ns maximum timestep. High-precision `wrdata` captures the two membrane nodes, two unity-buffer outputs, and chopped amplifier output. `pn`: membrane mean1.43461µV, buffer mean1.43487µV, chopped output14.57595µV, input-equivalent total error+0.00855µV, membrane disturbance−0.02314µV. `np`: membrane mean−2.21192µV, buffer mean−2.16119µV, chopped output−22.39289µV, input-equivalent total error−0.00520µV, disturbance+0.01995µV. This confirms sign and near-threshold transfer for these two nominal sequences; it does not cover same-sign events or the full float threshold distribution. The first physical bench attempt sampled phase edges, a follow-up had the OTA bias ending before the final phase, and the next phase-table revision left B floating during its second sample. Those testbench defects are corrected in `scripts/test_sky130_sc_physical_chopped_readout.py`; their interim reports must not be treated as circuit results.

Using a conservative0.091µV static perturbation (0.068µV worst amp-only corner error plus0.023µV nominal maximum read kick) in the recorded full-float `final_fuse.standard` tensors yields0.0271%/0.0228% spike-bit mismatch at0.30V headroom,0.0518%/0.0492% at0.15V, and0.0151%/0.0107% at0.60V. Reproduce with `scripts/analyze_sky130_buffered_readout_sensitivity.py --error-uv=0.091`; artifact: `results/sky130_buffered_readout_float_sensitivity_e0.091uv.json`. This remains a uniform static perturbation on three64×64 patches from one DSEC training frame; it is not an analog-noise simulation, a complete network replay, segmentation score, or pass for any acceptance gate. No mismatch, physical threshold source, extracted layout, area, energy, or actor-wide 5ms operation is established.

### Full-float learned threshold on the physical switched-capacitor membrane — 2026-09-25

The float checkpoint's median final-fusion threshold maps to a10.914µV membrane offset at0.30V candidate headroom. The first physical DAC reports using code3243 are invalid: DAC-mode `.ic` still contained the desired threshold, signal-cell edits were applied after that cell had been copied into the deck, and a precharged OTA variant railed under event drive. Do not use those reports as threshold or event evidence. Standalone R-2R calibration is still only an unloaded control voltage and is not the physical membrane mapping.

The corrected test uses no threshold `.ic`; signal membrane initialization comes from VCM, the separate threshold/reference cell is initialized through the transistor R-2R DAC, and its held OTA output is clamped to VCM. In no-event bins both OTA channels are disabled, consistent with no packet needing accumulation. The full5ms no-event screen calibrates code2711 to a mean−10.831µV signal-minus-reference differential versus−10.914µV target (83nV state difference). ABBA input-equivalent error is−0.078µV and read disturbance is−0.033µV; combining the observed mean state with the readout error gives about−10.909µV, 5nV from the target in this TT screen. This uses a calibrated analog threshold-setting code from the full-float parameter, not a quantized model or QAT path.

For event-driven cases the signal and reference OTA phases are matched, the reference packet input stays at VCM, and packet polarity is inverted because the integrator is inverting: positive float weights must raise membrane voltage. With code2711 and equal0.05V test packets, `pp` reaches+1.191µV (ABBA error−0.022µV, read disturbance+0.007µV) and `nn` reaches−20.878µV (error−0.064µV, disturbance−0.073µV), both correct signs. Mixed `pn` and `np` remain below threshold at−10.216µV and−9.486µV (ABBA errors−0.038/−0.037µV; disturbances+0.055/+0.011µV). The0.730µV mixed-order difference and unequal positive/negative event transfer exceed the sampled full-float ~0.18µV q0.1 threshold margin, so this candidate is not accepted. These are nominal TT schematic results at50ns timestep with two equal toy packets, not full-float weight replay, mismatch/noise/PVT, segmentation accuracy or layout evidence. Reports share prefix `sky130_sc_physical_chopped_readout_{zz,pp,nn,pn,np}_abba_rf3445_dac2711_p0.05v_s50n_init10u_pre20u_heldotavcm_singledac`; signed event reports also include `_pinswap_matchota`.


### Passive SKY130 switched-capacitor membrane: first order and retention screen — 2026-09-25

A bounded alternative was added in `scripts/test_sky130_passive_sc_membrane.py`: one 100µm-square SKY130 MIM membrane capacitor, one 1µm-square MIM packet capacitor, physical transmission gates for packet connect/reset and state initialization, and a 1e15Ω schematic leakage path. The OTA is absent during accumulation. With a ±50mV packet top-plate step, `pn` gives +5.6µV then −5.6µV, while `np` gives −5.6µV then +5.5µV. Both sequences finish at0.8999949V from0.8999949V initial to the report's 0.1µV precision. The first packet changes by only 0.0–0.1µV over the subsequent ~4ms isolated hold. Reports: `results/sky130_passive_membrane_{pn,np}_p0.05v_s100n.json`; decks/logs/data use the same prefix.

This cleanly removes the millivolt-scale OTA enable/reconnect artifact observed in the earlier active virtual-summing-node integrator. In a separate always-on OTA variant, the membrane/reference difference drifted by −2.62mV over the bin; with event-window OTA gating, reconnect shifts were ~6mV despite changing packet step 50mV→53.5mV changing the reference state by only ~0.4µV. Those results disqualify the OTA-integrator transfer as a reliable packet calibration in its current form. Follow-up transfer sweeps with a 100µm state capacitor give one-event steps of 5.6/16.8/33.6µV at ±50/±150/±300mV for a 1µm packet; this is linear over the tested range. A 3µm packet at ±300mV gives 267.7–268.2µV per event, but mixed `pn`/`np` final states differ by1.0µV. A 10µm packet at ±300mV gives 2.943mV then2.915mV for same-sign events, with2.4µV first-event hold movement; large packet/state ratios therefore introduce measurable state-dependent transfer. With the passive reference physically initialized through the transistor R-2R24 DAC and no `.ic`, code3060 sets signal-minus-reference to−11.0µV at100µs and holds that through4.9ms; the DAC output is+11.0µV versus the full-float target+10.914µV. Mixed `pn`/`np` packets at ±300mV with the same physical reference finish at−10.9/−10.8µV, respectively, or+0.014/+0.114µV from the target, within the provisional0.18µV static margin before comparator/read kick. This improves the initialization evidence but is not circuit acceptance. The passive result remains nominal TT schematic only: no comparator/ABBA readout, actual float weight mapping, threshold distribution, effective thermal noise, device mismatch, PVT, extraction, layout, or 140k throughput. The 3/10µm steps also exceed the provisional mixed-order margin. Next map real full-float per-event weights to a shared safe packet-amplitude/capacity range, then measure threshold decisions and read disturbance on passive state.


### Passive packet state-range and full-float replay — 2026-09-25

The 0.9V transfer curve is not a state-independent weight law. With the top-plate packet baseline fixed at0.9V and a ±150mV step, the 1µm cap shifts state by+62.3µV for `p` and+29.9µV for `n` from0.75V; from1.05V, `p` gives−32.0µV (wrong sign) and `n` gives−62.0µV. A10µm cap gives+2.868mV / +0.227mV for `p`/`n` from0.75V, but−0.174mV /−2.932mV from1.05V. The existing sample interval reaches roughly this range at0.30V candidate headroom, so fixed-VCM packet drive cannot serve the model. Tracking the packet common mode to the initial state makes the first 10µm event sign-correct (+1.337mV at0.75V, +1.361mV at1.05V for `p`;−1.316/−1.379mV for `n`), but gain still varies by about7–9%, and state drifts≈±119µV during the following4ms. Raising the explicit state shunt from1e15Ω to1e18Ω did not reduce that drift, indicating another device/off-state path dominates. The top-plate tracking here is a static initial-state test, not a live state-following circuit.

`analyze_sky130_passive_float_mapping.py` replays the three sampled full-float traces with measured passive-cap slopes, a0.30V top-plate range, an optimistic ideal continuously variable analog weight input, and a0.18µV per-event error floor. The underlying NumPy convolution reconstructs stored float currents within0.000061/0.000122/0.001709 model units for stem/enc1/final_fuse. At0.30V candidate headroom,1/3/10µm packet capacitors yield spike-bit mismatch of6.693/1.988/0.081% for stem,10.536/8.957/0.308% for enc1, and10.966/5.676/1.283% for final_fuse. The10µm case avoids packet-range clipping for nearly all final-fuse coefficients, but5.95% lie below the assumed per-event floor; these results assume linear transfer and omit the measured state-range effects above, dynamic analog weight generation, noise, comparator kick, PVT and mismatch. A2.5µs per-event service assumption gives sampled p99 active-destination service of90µs/222.5µs/790µs for stem/enc1/final_fuse, with maxima135/275/925µs; this is an optimistic3-patch timing screen, not full population throughput. Overall, passive storage is not accepted. Next build a live common-mode packet driver or test a direct signed current injector, characterize off-state retention, and replay float weights before any physical-view work. Evidence: `results/sky130_passive_float_mapping_screen.json`, `results/sky130_passive_membrane_{pn,np}_p0.3v_s100n_dac3060.json`, and `results/sky130_passive_membrane_{pp,nn}_p0.15v_s100n_{v0.75,v1.05}.json`.

### Packet event-time dependence and kT/C sensitivity — 2026-09-25

The physical ABBA readout's matched no-event baseline is−10.831µV. One-event controls using the threshold DAC, corrected polarity and a50ns maximum timestep measure positive contribution +6.514µV at0.5ms (`pz`) and +6.796µV at4.5ms (`zp`) for a0.05V packet. Negative contribution is−5.175µV at0.5ms (`nz`) and−5.313µV at4.5ms (`zn`) for a0.0564V packet. The positive and negative gains are asymmetric, and each changes with hold time; the residual change is0.14–0.28µV per event. Opposite-sign two-event runs with the polarity-calibrated amplitudes retain about0.56µV order dependence, above the provisional0.18µV full-float q0.1 threshold margin. The current amplitude calibration cannot remove this timing effect. The `--bipolar-charge-buckets` experiment is invalidated for now: in the `np` case, one active OTA bucket holds an early event while the other receives the late event, giving a−424.65µV residual. It does not test an isolated passive dual bucket.

`scripts/analyze_sky130_cap_kTC_float_sensitivity.py` replays the recorded full-float final-fusion PLIF with candidate state noise added before threshold/reset. Zero-noise replay reproduces all recorded spikes. For64 Monte Carlo trials at0.30V candidate headroom,0.1µV RMS independent per-update noise yields0.09264% spike mismatch;0.18µV yields0.16845%; area-scaled100µm MIM kT/C (14.26µV per cap) yields1.952%, and a20.16µV differential-pair scale yields2.226%. Static per-neuron offset at0.1µV gives0.21678%. At0.60V, the same physical noise still yields1.54% (one-cap sigma) and1.72% (differential pair). The capacitance estimate scales the measured203.8fF/10µm sample capacitor by area to20.38pF for100µm and applies kT/C at300K; it is only an estimate and excludes OTA/device noise. The replay freezes upstream stage spikes and tests only three64×64 patches in `final_fuse.standard`; it is not a full-network or task-accuracy result. A0.18µV single-cap kT/C target would require about7.92mm-square MIM under the same density assumption, which is not viable per neuron. Thus simple per-neuron analog MIM state is not qualified; explore charge-domain/regenerative approaches and event-time compensation before layout or population scaling. Evidence: `results/sky130_cap_kTC_float_sensitivity.json`, the four new `sky130_sc_physical_chopped_readout_{pz,zp,nz,zn}_abba_rf3445_dac2711_p0.05v_*` reports, and the matched `zz` report.


### First event-time compensation attempt — 2026-09-25

The early/late single-event transfer ratios suggested scaling only the first packet in a mixed bin: early positive ×1.0433 and early negative ×1.0267. Re-running physical pn and np sequences at50ns reduces their mean-state order difference from0.563µV (same amplitudes, no timing trim) to0.203µV. Corrected pn and np mean differentials are−10.2726µV and−10.4759µV; the average is+0.4566µV relative to the matched no-event baseline−10.8308µV. This indicates the single-event timing ratio does not completely predict two-event interaction, and the remaining order term is still slightly larger than the provisional0.18µV sensitivity margin. Reports: sky130_sc_physical_chopped_readout_{pn,np}_abba_rf3445_dac2711_p0.05v_pos0.05_neg0.0564_earlypos1.0433_earlyneg1.0267_s50n_init10u_pre20u_heldotavcm_singledac_pinswap_matchota.json.

The same noise-screen JSON now includes a geometry-only inventory bound. At the assumed100µm×100µm state-cap size, one MIM per30,976,000 states occupies about0.31m² and totals about631µF. Matching0.18µV single-cap kT/C under the same MIM density requires a7.92mm square cap per state, or about1,940m² aggregate capacitor area before any helper circuit. This is not a floorplan or a technology signoff, but it rules out solving the theoretical noise estimate simply by enlarging every per-neuron MIM. The analog architecture now needs a state representation/front end that avoids one precision capacitor per PLIF, while preserving the float PLIF update order. Evidence: results/sky130_cap_kTC_float_sensitivity.json.

### Membrane MIM area and noise correction (2026-09-25)

The earlier 100 um square capacitor area figure was a SPICE bench scenario scaled to all 30,976,000 logical PLIF states; it was not a selected cell size. Likewise, the 0.18 uV point came from local final-fusion spike sensitivity and is not a specified capacitor kT/C requirement. Those assumptions overstated the implication that an analog MIM state array must exceed memory area.

Using the measured 10 um MIM value (203.8 fF) as an area-density estimate (~2.038 fF/um2), simple one-cap-per-state scenarios are: 1 um squares: ~31.0 mm2 total and ~1.43 mV kT/C; 10 um squares: ~3,098 mm2 and ~143 uV; 100 um squares: ~309,760 mm2 and ~14.3 uV. These are geometric/noise scenarios only; 1 um may not satisfy PDK minimum geometry, and switches, routing, guards, peripheral circuits, and layout spacing are excluded. The 100 um point is only the existing bench cap.

Conclusion: MIM area can indeed be well below a same-capacity digital state implementation. Area alone does not rule out analog membrane storage. The unresolved engineering question is whether a realizable smaller capacitor plus circuit noise, leakage, event charge, restore, and readout preserves full-float network behavior. The local 0.18 uV sensitivity result must not be used as a universal kT/C requirement or as an area floor.

### SKY130 MIM geometry and packet-resolution screen (2026-09-25)

Read the local SKY130 model (`cap_mim_m3_2`): nominal typical parameters are `camimc=2.00 fF/um2` and `cpmimc=0.19 fF/um`. For a square width w, the model is approximately C=2.00w^2+0.76w fF (before process offsets). The shipped 1um model test gives 2.642 fF. One MIM per each of 30,976,000 logical states would occupy 30.976 mm2 at 1um squares, 3,097.6 mm2 at 10um, 12,390.4 mm2 at 20um, 77,440 mm2 at 50um, and 309,760 mm2 at 100um, excluding all other layout. Thus the earlier 100um bench assumption is much too pessimistic for raw capacitor area; the 1um scenario is materially smaller, although a true physical density comparison with same-capacity SRAM still needs matched macros and layout overhead.

The area benefit creates a packet-resolution issue. The existing passive cell uses a 1um packet MIM and 0.3V top-plate steps to produce about 41uV on a 100um state MIM. Preserving that step under ideal capacitive scaling would require roughly 75mV with a 50um state cap, 3mV with 10um, and 0.08mV with 1um, using the same 1um packet. The smallest-state cases therefore need a much smaller packet capacitor, a low-noise fine analog pulse source, or another charge scaling method. This is a design tradeoff, not evidence that the large membrane cap is required.

A first matched 50um/1um, 75mV switched-capacitor ABBA transient did not complete within the bench's 180s Docker timeout. No circuit behavior is claimed from that run. Next try the same bounded case with a coarser maximum time step and characterize a 10um/1um case; then choose the smallest cap whose physical packet path meets full-float transfer sensitivity, retention, and throughput. The nominal MIM equations are model estimates, not DRC-qualified geometries.

### Passive MIM membrane size sweep and area comparison (2026-09-25)

The SKY130 typical MIM model gives approximately C=2.00w^2+0.76w fF for square side w in um; the shipped 1um device test is 2.642fF. For 30,976,000 membrane states, capacitor-only area is 30.98mm2 at 1um, 123.90mm2 at 2um, 774.40mm2 at 5um, 3,097.60mm2 at 10um, 12,390.40mm2 at 20um, and 309,760mm2 at 100um. The previous 100um SPICE bench assumption is therefore not a design choice. The prior digital isolated-PLIF footprint is 46,647.068mm2 for the same state population before synapses, clock, power and routing (`docs/PROGRESS.md`, 2026-09-22 section). Thus 10um MIM area is about 15x lower than that direct-standard-cell digital PLIF footprint; 5um is about 60x lower. These are unlike physical flows and capacitor-only area, so they do not prove full-chip area. Packet capacitors, switches, comparator/readout, DAC distribution, spacing and routing are excluded.

The physical bench now has a true passive-cell option: packet-cap bottom connects directly to the stored membrane output; the OTA is absent during accumulation and the state capacitor is tied to VCM. This differs from the older OTA integrator, where the packet bottom connected to the summing node and signed events included OTA wake/reconnect shifts. At 50um state / 1um packet, a 75mV top-plate packet gives about +/-33.6uV vs matched no-event; 91.8mV packets produce two same-sign events totalling +82.8uV, and mixed pn/np sequences finish within about 0.5uV of the no-event control. This is accurate but 77,440mm2 of MIM alone, larger than the cited digital PLIF footprint.

At 10um state / 1um packet, a 4.0mV nominal packet plus 1.14 early-event amplitude trim produces +81.5uV for two same-sign events. Mixed pn and np end at -0.06uV and +0.04uV relative to the matched no-event trace (order difference about 0.10uV). The paired ABBA readout disturbs the state by about 1.1-2.0uV. All are nominal SKY130 TT schematic results using 50ns maximum timestep; `.ic` still establishes initial state, and there is no mismatch, transient noise, extraction or DRC. The 1.14 trim is a first two-event calibration, not a general event-time compensation law.

At 5um, an area-scaled packet and small read buffer lower the no-event ABBA read disturb to ~0.7uV, but the measured early event changes by about 80uV immediately and only ~53uV remains relative to no-event after 4ms in the compared trace. This 34% loss is not acceptable as an uncorrected 5ms-bin contribution. At 1um, the estimated kT/C is 1.23mV and an 82uV input packet is almost completely lost when the read OTA is permanently connected (less than 1uV measured event differential); the standard switched readout kicks the state by ~6uV. 1um is area attractive but not a passing cell.

The full-float local final-fusion replay, with upstream spikes frozen, estimated kT/C reset-noise spike mismatch at about 3% for 5-10um and 5% for 1um at 0.30V candidate headroom (8 Monte Carlo trials); injecting the same noise independently every update gives about 4% for 5-10um and 8% for 1um. This is a local sensitivity screen, not segmentation accuracy or circuit noise validation. Next compare a regenerative threshold readout and event-time retention/compensation at 5um, then map the measured 10um transfer into the full-float trace. Do not use the QAT export.
## 2026-09-25 — full-float all-stage mapping exposes input-range and read-kick gate

Extended the bounded real-DSEC float trace from 3 to all 25 inference `SpikingStage` actors (same checkpoint, same three 64×64 patches, same training frame); exported grouped-convolution/dilation metadata and taught the local mapping replay dense, grouped and depthwise operators. The physical transfer calibration uses a 10×10µm state MIM and 1×1µm packet MIM, with signed top-plate amplitudes through ±0.512V. Positive sweep from 1mV to 0.512V is linear to about 0.01% in state transfer; the ±0.512V events differ by about 0.4% in magnitude after subtracting the matched no-event state. TT schematic only, 50ns maximum transient step.

The all-stage float replay uses continuous weights (no QAT or quantization floor), captured full-float thresholds and fixed recorded presynaptic spikes. At 0.15V per-stage candidate headroom, the least represented weight fraction is 97.31%; worst local spike mismatch is 0.1225% in `context2.depthwise` (2.69% of that stage's weights need more than the measured ±0.512V range). At 0.30V headroom, the least represented fraction falls to 78.99% and worst local mismatch rises to 2.7677% in `context2.depthwise`; at 0.60V it falls to 49.48% with 8.9038% worst mismatch. Baseline replay with recorded float currents already differs by up to 0.0806% in `stem`, whose post-reset peer-inhibition feedback is not recomputed in this local mapping script. These are layer-local, frozen-input screens, not a closed-loop network or task-accuracy result. Exact per-stage results are in `results/sky130_passive_float_mapping_screen.json`; all-stage source traces are in `model_reference/float_patch_trace_all.json` and `.npz`.

At a 0.512V positive packet step, the membrane changes about +4.57mV relative to matched no-event; the negative step changes about −4.56mV. The present permanently connected read buffer causes roughly −50.7/+45.4µV membrane disturbance at these large test signals. After correcting the stale fixed-10.1 readout conversion to use each run's measured gain (~9.21×), the ABBA input-equivalent readout relation error is about −3.2/+3.3µV. The weight range and large-signal read kick are now the analog decision gate. No circuit remedies have been tested in this step. Continue only after authorization to explore a circuit change; preserve the analog path and do not use QAT/digital fallback.
# 2026-09-25 — multi-event loading and direct-injector bench correction

The passive switched-capacitor cell was extended from two events to a 100-event equal-sign train using `scripts/test_sky130_sc_physical_chopped_readout.py`. The 20µm MIM state / 2µm MIM packet cell with ±64mV packet steps ended at 33.36mV; the isolated single-event transfer implies about 52mV for 100 linear contributions. This ≈64% linear response confirms substantial charge-sharing compression as the membrane moves. The earlier two-event sign/time trims (sub-microvolt residuals) do not establish operation at the sampled model fan-in (final-fuse active-destination p50=212, p99=316, max=370). This is TT schematic evidence; it is not a closed-loop float-network replay or a qualified cell.

The direct pulse-current multi-event bench initially reported an impossible >1.8V no-pulse state. A capacitor-only control traced this to the `.ic` value under `uic`: `.ic v(state)=0.9` initializes the 20µm MIM membrane to about 1.8V when VCM=0.9V. Changing the bench to `.ic v(state)=0` establishes a 0.9V starting point; the isolated MIM drifts about 0.001mV over 5ms, and the gated injector bench's no-pulse reference drifts about 0.0011mV. The old above-rail results are invalid and must not be used as evidence of injector leakage.

With corrected initialization and a two-stage long-channel isolation TG, one 0.14µs p/n gate pulse moves the 20µm membrane by +19.16/+19.72mV from the matched baseline. For 100 equal-sign pulses at 49µs intervals, final changes are +152.70mV (p) and +170.09mV (n), while isolated-pulse linear extrapolation gives +1.916/+1.972V. This is strong state-dependent compression and rail-range limitation, so the direct injector is not accepted either. The bench uses supply-gated MOS devices and no explicit regulated current bias; subsequent exploration should compare smaller per-event charge and a source-degenerated/cascode or differential current-integrator variant, then use actual float event/state traces. No PVT, mismatch, noise, extraction, comparator, or network feedback is included. Artifacts: `results/sky130_passive_sc_membrane_*multi*json`, `results/sky130_ms_pulse_width_many_events_*json`, and `benches/mim_init_isolated.cir`.

Reducing logical pulse width from 20ns to 2ns (14ns physical p/n pulse after the local 7× correction; 5ns transient maximum step) lowers the isolated event to +6.87/+7.04mV. Twenty same-sign events still reach only +67.49/+69.74mV versus +137.46/+140.88mV linear extrapolation (about 50.5% short). Thus simply shortening the pulse does not restore linear accumulation over a meaningful event count. A nominal saturation-bias gate level (pMOS 1.2V, nMOS 0.6V) also failed to improve 100-event accumulation: +160.96/+143.30mV versus isolated-pulse linear extrapolations +1.952/+1.768V, ≈92% short. Doubling injector length to 20µm changed the same-sign response by little (≈158/178mV vs ≈1.94/1.99V extrapolated); adding 1MΩ source degeneration also did not materially improve it (≈161/163mV vs ≈1.95/1.91V). This variant still lacks a separate regulated current-source device and cannot be called a proper current source; the drive gate level merely changes the injector MOS operating point. A trial shrinking transistor width below the SKY130 model's valid bin produced no valid device model and was rejected as a simulation, not a circuit result. The next useful current-injection experiment needs explicit current bias plus pulse steering and a separate off switch, keeping device sizes within the model range; compare state dependence over the actual float event distribution. The 2ns logical pulse is currently a transient-time-resolution screen, not a feasible 5ms scheduler or extracted timing result.

## 2026-09-25 — differential MIM integration reduces single-ended compression

Added `scripts/test_sky130_ms_diff_current_many_events.py`: two matched 20µm MIM capacitors start at 0.9V, and signed events steer complementary pMOS-source/nMOS-sink currents so the nodes move in opposite directions. A no-event pair stays matched and drifts about 0.147mV over 5ms. At TT, 10µm injector length, pMOS gate=0.72V, nMOS gate=0.60V and 10.5ns physical pulse width, one event changes the differential by 1.873mV with only 0.034mV common-mode shift. In a 100-event equal-sign train, differential change is 173.97mV versus 187.28mV from the isolated event (7.1% low); common mode moves −2.98mV relative to the no-event pair. An alternating 50/50-sign train leaves −2.69mV differential residual and −3.08mV common-mode shift. At 7ns the same circuit is 23.7% high after 100 events; at 14ns it is 17.8% low. Thus differential storage improves greatly over the single-ended 90%+ compression, but still has pulse-width/state nonlinearity, polarity-order residual, common-mode motion and unqualified PVT/mismatch. Bias values and width are one-point nominal TT calibration only. The test uses direct MOS gates, no explicit reference-current mirror, read amplifier, threshold, reset/leak, physical layout or network feedback; it is a promising topology screen, not an accepted circuit.

Additional equal-charge stress: the same pMOS/nMOS biases and 10.5ns pulses were run at 316 events (the sampled final-fuse p99 active-destination fan-in) and 370 events (the sampled maximum), spread across the 5ms interval. The 316-event same-sign differential change was 608.21mV versus 592.28mV extrapolated (+2.69%); alternating 158/158 signs left +0.183mV differential residual. At 370 events the change was 700.47mV versus 693.48mV extrapolated (+1.01%); alternating signs left −0.423mV residual. Same-sign final node voltages were 1.197/0.589V at 316 and 1.241/0.541V at 370; common mode shifted −6.90/−8.84mV relative to the no-event reference. These are equal-width same-sign stress trains, not the model's mixed signed weight/activity sequence, so they do not qualify transfer accuracy. Reverse alternating order at 100 events flips the residual from −2.687mV to +2.687mV, identifying event-order nonlinearity rather than a static sign offset. Results: `sky130_ms_diff_current_many_events_n100_*` and `n316_*`/`n370_*` in `artifacts/analog_asic/results/`.

Burst timing screen: 370 events were also packed 15ns apart with 10.5ns pulse width, completing in about 5.55µs inside the same 5ms bin. Same-sign differential change was 585.11mV versus 587.19mV linear expectation (0.35% low), with final nodes 1.188/0.603V. A 185/185 alternating train left 0.108mV differential residual. This shows the gate pulses can be serviced far faster than the earlier passive packet cycle in this schematic, though event-width resolution, control distribution and actual weighted event timing remain unqualified.

The follow-up explicit current-source plus TG-steering variant is not the lead. With one-stage ordinary switches it drifted about0.20V in the no-event 5ms reference; two-stage long-channel switches reduced reference drift to about4µV, but charge injection/current during one 14ns pulse produced excessive differential steps (about0.62V with 10/20µm TGs, about59mV with 1/2µm TGs) and large common-mode shifts. Lengthening the current-source devices to50µm did not improve the one-pulse transfer (about85mV). Thus the separate-source TG topology remains a failed schematic attempt; retain the direct differential MOS injector as the current leading candidate for full-float mapping. Results/logs: `sky130_ms_diff_steered_current_*`.

### Fixed-width MOS gate-amplitude mapping and weighted event sequence — 2026-09-25

The direct differential MOS injector was extended with a fixed 10.5 ns pulse whose pMOS/nMOS gate magnitude carries each full-float weight. Gate transfer is calibrated using the SKY130 TT devices and a matched 20 µm MIM pair. Directly measuring `v(vp)-v(vn)` avoids the 0.1 µV quantization created by subtracting separately printed ~0.9 V node voltages. The calibration transient uses a 0.5 ns maximum step and initializes both the external MIM nodes and each model's internal series-resistance capacitor plate to VCM; outer-node initialization alone leaves the internal capacitor state inconsistent and invalidates that earlier sweep/sequence. With corrected initialization, a maximum-strength isolated event changes the differential by 1.596 mV and common mode by about −6.8 µV at the end of a 200 µs screen.

Using that measured curve to map the full-float `final_fuse.standard` coefficients, no weights exceed the measured transfer range at 0.30 V candidate headroom; 0.017% of static coefficients are below the lowest tested gate fraction. An ideal continuous gate map gives 0.00051% local spike-bit mismatch on the three frozen DSEC patches. Uniform 12-bit gate-fraction coding gives 0.0111% mismatch. These are ideal digital-code replay estimates, not a built gate DAC or programmed analog weight storage; there is no noise, mismatch, PVT, extraction, full-network or task-accuracy evidence.

A representative maximum-fan-in location from the recorded full-float presynaptic tensor expands to 370 weighted events and a −17.485 mV target at this scale. Events spread uniformly across 5 ms and mapped through the single-event curve produce −17.256 mV in negative-first order, −18.079 mV in reverse order and −18.578 mV in one deterministic shuffled order. Forward/reverse order differs by 0.823 mV, while shuffled total-charge error is −6.25%. The differential-pair common mode ends near 0.906 V in these 10.5 ns runs. This demonstrates that isolated-event calibration is not enough for full-float accumulation; the current cell is not accepted.

A fixed 128 ns pulse made the same weighted sequence worse: shuffled output −2.964 mV and reverse output −25.110 mV versus −17.485 mV target, with 22.0 mV order spread. The run's JSON inherited an old scope sentence saying 10.5 ns; its actual deck used 128 ns. A scaled long-channel device (`Wp=4.5 µm`, `Wn=3 µm`, `L=30 µm`) also failed: shuffled output −11.939 mV (31.7% error), reverse/forward span 37.45 mV, and common mode near 1.03 V. Retain the `L=10 µm`, 10.5 ns direct differential injector as the best current branch, but keep it provisional. Next compare a 10 µm MIM pair to test a lower-area state capacitor under the same full-float weighted sequence, then investigate current-source/common-mode regulation if transfer still varies with membrane state. Do not use QAT or the quantized export.

Artifacts: `scripts/characterize_sky130_ms_diff_gate_amplitude.py`, `scripts/analyze_sky130_ms_diff_gate_dac_resolution.py`, `scripts/test_sky130_ms_diff_weighted_sequence.py`, `results/sky130_ms_diff_gate_dac_resolution_float_screen.json`, and `results/sky130_ms_diff_weighted_sequence_fullfloat_n370_idx16_o0_y61_x1_H0.3_w10.5n_l30_s2n.json` (long-channel test). The base 10 µm-device sequence report predates the later unique suffix and has the same `fullfloat_n370_idx16_o0_y61_x1_H0.3_s2n` name; the earlier incorrect-initialization result with that prefix is superseded. The 128 ns report is `results/sky130_ms_diff_weighted_sequence_fullfloat_n370_idx16_o0_y61_x1_H0.3_w128n_s2n.json`.
## Corrected differential MOS weighted-event replay and coding comparison — 2026-09-26

An audit found that the original weighted-event waveform generator printed 5ms PWL timestamps with too few significant digits. All older 370-event weighted-sequence logs contain thousands of ngspice “non-increasing PWL time points” warnings; their electrical outputs are superseded and their JSON reports are tagged invalid. Isolated-event calibration curves did not use those long timestamp sequences and remain valid. `scripts/test_sky130_ms_diff_weighted_sequence.py` now prints 12 significant digits, uses a matched no-event MIM/injector reference, and compares event-induced differential change. The corrected run has zero non-increasing-PWL warnings.

The best corrected screen uses the original full-float `final_fuse.standard` location (370 signed weighted events; batch/time index16, output0, y61/x1), two20um SKY130 MIM capacitors, L=10um differential MOS injectors, fixed10.5ns gate pulses, and0.15V candidate headroom. A0.965 gate-target trim was applied based on the matched single-event curve. Pulses are serialized at15ns intervals from50.000 to55.535us, then the state is held to5ms. Against the same-deck no-event reference, the target is−8.74237mV and final event-induced changes are−8.65885mV (forward, +0.955% error),−8.66726mV (reverse, +0.859%), and−8.67199mV (deterministic random, +0.805%). Forward/reverse order span is8.413uV. The matched no-event differential at5ms is0.216nV. No-event common mode is0.918425V; the weighted event train shifts the common mode by−8.262 to−8.269mV, ending near0.91016V. This is a nominal TT schematic result with ideal gate drivers and a single maximum-fan-in site, not a PLIF/readout or full-network acceptance result. Weight storage/DAC, threshold/reset, noise, mismatch, PVT, extracted layout and task accuracy are absent.

The same fixed-width gate-amplitude injector at0.15V headroom without the0.965 trim gave−8.93973/−9.20225/−9.05440mV across forward/reverse/random orders versus−8.74237mV target, with0.263mV order span. A trim improves the total error in this case, while burst timing at15ns improves order sensitivity. Earlier0.30V weighted screens with corrected timestamps gave−17.83827/−18.36335/−18.04992mV for unit gain versus−17.48474mV target, and−17.26286/−17.81217/−17.52512mV at0.97 gain. These screens establish that fan-in ordering and operating scale matter; they do not establish the full weight-to-gate DAC or a general trim for other actors.

`scripts/analyze_sky130_ms_diff_gate_dac_resolution_c20_dense.py` replays the measured single-event curve on three frozen64×64 DSEC patches. At0.30V headroom, ideal continuous gate control yields0.00148% local spike mismatch and ideal12-bit gate-fraction coding yields0.00849%; this omits multi-event device behavior and physical DAC errors. The main corrected weighted-event test is the more relevant electrical check, but remains one location and three event orderings.

Fixed-bias pulse-duration coding was evaluated as the direct implementation alternative using `scripts/characterize_sky130_ms_diff_pulse_width.py` and `scripts/test_sky130_ms_diff_weighted_duration_sequence.py`. The 20um differential pair's calibrated positive and negative width curves are nearly unchanged when initialized at0.918V versus0.900V, so the common-mode initial-state adjustment does not explain the weighted result. With full p/n gate bias (0.72/0.60V),0.15V headroom and a30ns event period, the370-event sequence gives−67.3mV against−8.742mV target (about6.70× the intended change). Eleven weights use the minimum-width region. A lower fixed gate bias (0.936/0.48V) requires widths up to338ns; at750ns event spacing the276.75us train gives−298.2mV, about33.1× the target. Both are valid negative schematic screens for this unregulated topology. The fixed-width gate-amplitude path is currently preferable.

A synchronous cascode gate-amplitude calibration at the same20um MIM pair produces only0.170mV stable final transfer at maximum event amplitude and10.5ns pulse, versus1.599mV in the direct injector; it relaxes from0.541mV shortly after the pulse. It is not a better candidate at the tested bias point. A separate cascode weighted run used temporary1Megohm bleeders while the cascode transistors remained on, creating a DC load from the membrane to the rails; that report is explicitly invalid as performance evidence.

Next extend the corrected fixed-width gate-amplitude replay to other high-fanin outputs and state/common-mode points, then include physical readout, learned threshold, reset and beta/hold behavior before doing local spike replay. Measure gate-DAC implementation error, off-state common-mode drift, noise/mismatch, supported PVT and area before any layout/scaling claim. No QAT or quantized parameters are used.

### Multi-site gain trim and membrane-size follow-up — 2026-09-26

The same maximum-fan-in site was replayed with gate-target gain0.986. The 370-event target is−8.74237mV; forward/reverse/random event-induced results are−8.88330/−8.85984/−8.87333mV (−1.61/−1.34/−1.50%), with23.46µV forward/reverse order spread. At the full-float near-threshold site (fanin321, candidate margin3.29e−5 model units), gain0.986 instead maps the2.11181µV event contribution to2.11557/2.11191/2.11214µV, only+0.178/+0.005/+0.016% error. Gain0.965 was closer and more order-stable on the large-sum site (0.81–0.96%,8.41µV spread), but misses the near-threshold event by44–51nV; the float threshold margin at the selected near-threshold site maps to just0.358nV. No single global trim therefore solves both the large-sum and near-threshold cases. These are local voltage comparisons without physical threshold/readout or closed-loop layer replay.

A 10µm MIM pair was checked at the same maximum-fan-in event sequence using its own isolated-event calibration and0.965 gain trim. The differential result is6.25–6.60% below target, and the no-event common mode ends at0.96962V from a0.900V initial condition; event-bearing common mode then shifts a further−11.35mV. This is a negative result for directly shrinking the state capacitor with the same injector and timing. Capacitor-only geometric area falls by4× from20µm to10µm squares, but the small-cap operating point/transfer is not acceptable as screened.

To separate instantaneous state sensitivity from accumulation history, the20µm injector was recalibrated with both membranes initialized at0.918V common mode and−4mV differential, representative of the weighted trajectory. At gate fractions0.4,0.6,0.8 and1.0, its isolated-event transfer matches the0.900V/zero-differential curve to the reported precision (largest visible difference is about16nV at the1.0 endpoint). Thus the trim conflict is not explained by this tested static common-mode/differential offset alone; cumulative device history and event ordering remain stronger suspects. This is one isolated-event sweep, not proof of full trajectory invariance. Report: `sky130_ms_diff_gate_amplitude_c20_w10.5n_pg0.72_ng0.6_wp1.5_wn1_l10_d-0.004v_cm0.918v_t200u_n4_fr0.4-1_h05d85a05de_step2n.json`.

An ideal behavioral common-mode transconductor was added as an upper-bound isolation test (equal current into each membrane node proportional to average common-mode error;1nS per node, referenced to0.9V). At20µm it holds the matched baseline at0.900016V and event common mode within20µV, but the weighted differential errors are+1.11/+0.52/+0.67% and order spread rises to52.16µV. At10µm the same servo holds common mode at0.899976V but leaves the total charge6.33–6.67% low, with9.13µV order span. It removes common-mode movement but changes the transistor transfer/order behavior; it is not a physical servo implementation or a pass. The follow-up should calibrate the injector over membrane differential/common-mode trajectory and test a transistor-level or multiplexed common-mode regulator before another global-trim selection.

The weighted-sequence script now accepts `--membrane-cap-um` (10 or20 for available calibration data) and `--cm-servo-s` for this explicitly behavioral upper-bound test. Relevant JSON/logs use unique `c10`/`c20` and `cm` tags in `artifacts/analog_asic/results/`; PWL precision remains12 significant digits with matched no-event references. The selected site field is the time index, not a flattened batch index. Neither trim nor capacitor size is accepted for layout; digital/QAT artifacts remain out of scope.

With the20µm cell and0.965 trim, lengthening inter-event spacing does not monotonically improve accumulation. At30ns (19.5ns off time), sequence errors are+0.78/+1.11/+0.36% and order span28.68µV. At60ns they are+0.65/+0.86/+0.32% and span17.59µV. Spreading the370 events across the full5ms bin (13.2µs interval) gives+1.18/−1.05/−0.052% and a194.33µV order span. All runs use matched no-event controls and12-significant-digit PWL timestamps; the 5ms distributed screen puts the final event at4.9208ms. The large change in order sensitivity means spacing alone is not a robust correction. Results are the tagged `p30n`, `p60n` and `p13200n` JSON reports. Next evaluate whether passive charge packets, whose event updates are naturally additive, reduce this history/order error under actual full-float weights.

### Matched passive packet transfer and weighted-sequence audit — 2026-09-26

The older passive-cell reports measured packet response against the pre-event node voltage, which includes a physical initialization offset. A new sweep uses a matched zero-top-plate control with the same initialization, reset and TG switching; the packet bottom is reset to VCM, disconnected from the membrane100ns before the top plate returns, then reset. With20µm state/1µm packet capacitors, a50mV top-plate step transfers+167.7µV/−167.8µV (ratio0.003354/0.003356), and the response is linear from5 to180mV to the report precision. With10µm/1µm,50mV transfers+642.1/−642.3µV (ratio≈0.01284). These are TT schematic slopes, not layout-qualified transfer. The earlier raw142.8µV/140.1µV measurements are superseded for gate/weight mapping because they do not subtract initialization and switch-control offset. Calibration reports are `sky130_passive_sc_packet_transfer_m{10,20}_c1_*_matched_state_reset.json`.

The corrected20µm/1µm packet was mapped to the full-float maximum-fanin site at0.15V headroom, using the measured0.003354 ratio and a matched zero-weight event-control sequence. With the packet bottom reset to fixed VCM, the370-event, full5ms schedule yields−16.359mV forward, +3.837mV reverse and−3.822mV randomized, versus−8.742mV target: errors−87.1%, +143.9% and+56.3%, with20.20mV order span. An optimistic software compensation that adds the ideal accumulated float state to each packet command improves the totals to−12.798/−2.325/−6.337mV (errors−46.4/+73.4/+27.5%; order span10.47mV). That upper-bound correction is not a physical state sensor or circuit, and remains inadequate. The live-state packet-reset experiment was rejected as a switching sequence because its post-packet reset reconnects the packet capacitor to the membrane and cancels charge. Reports use `sky130_passive_sc_weighted_sequence_*_resetvcm_statecomp{0,1}_t20n.json`.

Thus the passive charge packet does not presently outperform the direct MOS injector. The 20µm cell needs a state-dependent baseline compensation or another packet-storage/reset protocol to avoid the VCM-to-membrane offset accumulating with event order. The direct MOS branch remains provisional and also order-sensitive; do not infer the real network's event ordering from the binned traces. Next characterize several randomized within-bin orders and investigate measured-state compensation on the MOS lead, while preserving this passive result as a failed fallback screen. No QAT, digital fallback, layout or task-accuracy claim.


### Full-bin randomized order and fan-in-site follow-up — 2026-09-26

The direct 20um differential MOS injector was screened with events uniformly spaced across the 5ms bin (13.2us spacing), 10.5ns pulses, 0.15V mapping headroom, 0.965 gain correction, matched no-event controls, and independent permutations of the saved weighted event multiset. The max-fanin site (370 events) has seven shuffled trials including seed140: mean error −0.083%, sample SD 0.279%, range −0.651% to +0.241%. The forward/reverse difference is much larger than the shuffled residual (roughly224–290uV across these runs).

At the p99 site (316 events), five shuffled orders (seeds140,1–4) have mean error +0.131%, sample SD 0.102%, range −0.005% to +0.273%; forward/reverse spread averages151uV. At the cancellation-heavy median-fanin site (291 events; ideal net +118.95uV), five shuffled orders (seeds140,1–4) have mean relative error −7.94%, sample SD4.46%, range −14.58% to −2.39%; absolute error is about2.8–17.3uV. Its forward/reverse ordering spread averages194uV, exceeding the intended net signal. Thus high-fanin aggregate sums look well calibrated under random permutations, while cancellation-heavy sums remain order-sensitive in absolute terms.

These permutations are proxies only: the saved trace has within-bin event multiplicity but no activation timestamps, so it cannot establish actual temporal order. Each result is a single frozen final_fuse location, nominal SKY130 TT, ideal gate sources, and a schematic differential pair. It omits a weight DAC, learned threshold/readout/reset/beta, physical common-mode control, mismatch/noise/PVT, extraction, closed-loop upstream activity and task-level inference. It is not module acceptance. Result JSONs use `qseed1`–`qseed6` for max fan-in and `qseed1`–`qseed4` for p99/median; prior seed140 reports are the baseline. Next recover or instrument within-bin event chronology if available; meanwhile test a physical transistor-level common-mode/trajectory compensation and include the actual PLIF threshold decision in a small replay.


### Differential branch charge balance and common-mode audit — 2026-09-26

An audit of `scripts/characterize_sky130_ms_diff_gate_amplitude.py` found that its isolated-event `*_common_mode_change_mv` field was half of the actual change in `(vp+vn)/2`; the script multiplied the average-node shift by `0.5e3` rather than `1e3`. The differential transfer fields and later weighted-sequence common-mode measurements are unaffected. The reporter is corrected; older isolated-event common-mode fields must be doubled if used. A corrected 23-point TT calibration is `sky130_ms_diff_gate_amplitude_c20_w10.5n_pg0.72_ng0.6_wp1.5_wn1_l10_d0v_cm0.9v_t200u_n23_fr0.1-1_h0abd11cedc_step2n.json`.

A branch-balanced gate mapping independently interpolates pMOS and nMOS gate fractions so an isolated signed event raises one membrane by half the requested differential change and lowers the other by half. It uses the corrected TT isolated-event transfer; both gate drives are still ideal voltage sources. On the370-event 15ns burst, common-mode movement shrinks from about−8.3mV to−24uV. Forward/reverse/random errors become+0.512/+0.353/+0.102% versus the−8.742mV target; forward/reverse spread is13.9uV. This confirms branch current imbalance was a major common-mode source.

On a full-bin13.2us schedule, the same balanced mapping moves common mode by only−17uV but produces forward/reverse/random errors+0.870/−1.892/−0.462%, with241uV order spread. At the cancellation-heavy median-fanin site, common mode moves−51uV, yet errors are+153.3/−22.9/+59.0% against a+118.95uV net target, with210uV order spread. The balance therefore does not solve time/state dependent cancellation, and no balanced mapping is selected. These are TT schematic results with ideal gate amplitudes and matched no-event controls, not physical DAC/readout/threshold or network acceptance. Reports carry `_bal1_` in their names. Next compare scheduling of signed events within the 5ms bin and evaluate the PLIF threshold decision; a physical circuit is warranted only after a replay demonstrates benefit beyond common-mode correction.


### Binned scheduling, threshold scale and attached OTA readout — 2026-09-26

`SpikingStage.forward` computes the convolution current from the presynaptic tensor and calls the PLIF once per timestep; the full-float model has no within-bin contribution order. The hardware event controller chooses its serialization order, subject to upstream completion and throughput. A greedy upper-bound scheduler that keeps the partial weighted sum near a linear ramp was tested at the cancellation-heavy median-fanin site over the full bin. It gives+7.57% charge error (about+9.0uV) versus+118.95uV target, comparable in magnitude to five shuffled trials (−2.39% to−14.58%). It needs advance knowledge of the signed event multiset, so no hardware schedule is accepted from this result.

At0.15V candidate headroom, the observed `final_fuse.standard` absolute candidate maximum is13,801 model units, giving10.869uV/model unit. Its learned thresholds0.2863–0.5885 units therefore map to only3.112–6.397uV. Among the captured final-fusion candidates,1.14% have a threshold margin below1uV. Replaying three frozen64x64 full-float patches with a fixed threshold offset (including subsequent PLIF state/reset feedback) changes about0.25% of this stage's spike bits at ±0.1uV and about1.45% at ±1uV; the exact positive/negative values are in `sky130_ms_diff_readout_float_sensitivity.json`. This is local spike sensitivity, not segmentation accuracy or a physical comparator offset measurement.

The existing physical SKY130 OTA has nominal open-loop DC gain around−5,060 V/V at0.918V common mode for ±0.1 to±6uV input differentials. A0.1uV input changes its output by about0.506mV in the ideal-voltage-source screen. Its zero-input output changes4.80mV between0.900V and0.918V common mode, equivalent to about0.95uV at this gain. It needs an offset/reference treatment for a microvolt-scale threshold; gain alone is insufficient. TT DC report: `sky130_sc_ota_diff_sensitivity_cm0p918_u0p0-0p1-m0p1-1p0-m1p0-3p0-m3p0-6p0-m6p0.json` and the matching0.900V report.

A new 20um differential MIM pair bench connects those OTA gates directly to the stored nodes and uses a physical20us TG initialization. Before the switches open, a prepared differential is retained to within roughly0.02uV. The zero-differential control is about−0.115uV 0.1us after disconnect, then reaches−13.906uV at100us and−13.828uV at4.9ms. A prepared+6uV differential ends at−8.432uV; relative to the matched zero control,0.1/1/6uV prepared signals retain about0.090/0.899/5.395uV after4.9ms (about90% small-signal transfer). The matched OTA output changes about0.456mV per0.1uV prepared input. An `.ic`-only startup screen was worse, retaining only about6.6% of the prepared differential by100us. The physical-init offset builds after disconnect during OTA settling, rather than at the TG edge; it is larger than the mapped learned threshold and is not canceled in hardware. `sky130_ms_diff_ota_state_hold_{tg_init,ic_init}.json` are nominal TT, ideal-bias schematic screens with no comparator decision, weight events, noise, mismatch or PVT.

Using the typical model estimate of815.2fF per20um MIM, independent differential-pair reset kT/C at300K is about100.8uV RMS. An eight-trial full-float local final-fusion replay that injects this as independent initial/post-spike reset noise yields3.185% mean spike-bit mismatch at0.15V headroom. This is a software noise bound, not ngspice transient noise, task accuracy or proof that every update incurs that noise. The same source file reports deterministic threshold-offset sensitivity. The combined results make a physical offset-canceled readout and noise/task-accuracy study the next gate before any layout; neither the direct MOS injector nor this OTA is an accepted PLIF module.


### Full-float three-patch task sensitivity to the 20um reset-noise proxy — 2026-09-26

`scripts/analyze_sky130_ms_diff_task_sensitivity.py` reruns the original full-float checkpoint, with QAT disabled, on three64×64 event-density-selected DSEC patches per record. It adds independent Gaussian noise of100.8uV RMS differential-pair equivalent at `final_fuse.standard` initialization and after each spike reset only, then carries altered spikes through the remaining float network to segmentation logits. This is a software proxy: it does not inject measured ngspice noise, upstream actor errors, correlated noise, comparator offset or full physical PLIF behavior.

On the original sampled training frame, three deterministic seeds give3.181–3.191% final-fusion spike mismatch,91.47–91.77% pixel argmax agreement with baseline and47.02–47.26% labeled-pixel accuracy versus47.96% float baseline on the selected patches. Three held-out checkpoint validation frames show substantial variation. At validation indexes0/117/233, mean spike mismatches are4.104%/4.218%/2.856% and pixel agreements are68.02%/90.68%/88.43%. Baseline labeled-pixel accuracies on those patches are27.88%/39.27%/51.81%; noise-proxy means are43.93%/39.73%/51.60%. The first-frame apparent improvement is a small-sample class-decision effect, not a design benefit. These four frames do not establish dataset accuracy, but they show that the task response cannot be inferred from spike mismatch alone. JSON reports are `sky130_ms_diff_task_sensitivity_{training_0,validation_0,validation_117,validation_233}.json`. Broader validation and an actual physical noise/offset model are needed before setting analog acceptance criteria.


### Physical OTA baseline sample and ideal learned-threshold offset — 2026-09-26

A bounded front end now uses two20um MIM membrane capacitors, physical TG state initialization (0–20us), a continuously connected SKY130 OTA, a separate20um MIM that samples its settled output through a physical TG (100–110us), and a second physical OTA to compare live and held outputs. A single signed direct-MOS event arrives at150us. The learned-threshold offset is represented by an **ideal series voltage source** at the second OTA input; there is no threshold DAC yet. Ideal bias and gate-amplitude sources remain. The sample capacitor is extra area and its kT/C/noise are not included.

The initial0.5ms TT screen without a threshold offset distinguishes signed f=0.6 gate events: at450us, +/− events retain about+/−3.06uV differential relative to a matched zero-event cell and shift live-minus-held output by about−15.3/+15.5mV. A stronger positive f=0.65 event retains+6.63uV and shifts it by−33.1mV. The small positive event decays from+4.12uV shortly after injection to+3.06uV at450us, so the front end has significant event-signal loss even after baseline sampling.

With a15.5mV ideal output-domain threshold offset (roughly3.1uV input equivalent at the nominal OTA gain), the **2ns-step 5ms TT** run yields at4.9ms: zero event differential reference0 and second-OTA output1.797V; f=0.6 positive event+3.013uV and second-OTA output1.694V; f=0.65 positive event+6.532uV and second-OTA output0.0227V. The zero-event live-minus-held output is−0.00044mV at4.9ms. This nominally separates the tested near/beyond-threshold cases if a digital threshold is placed between the high and low OTA outputs. It does not establish calibrated learned thresholds across channels, signs, histories or process variation. The physical first-OTA input loading and state loss remain.

A coarse20ns transient step is invalid for this 10.5ns pulse: it predicts+3.79uV retained for f=0.6 at450us instead of+3.06uV at2ns and changes the comparator classification. A5ns step gives+3.15uV and places the second OTA in its transition region. The full5ms four-case2ns deck hit its180s timeout after2.69ms; the completed full-bin result uses only zero and two positive cases and a400s bound. Reports: `sky130_ms_diff_ota_autozero_th0.json` (0.5ms), `sky130_ms_diff_ota_autozero_th15p5.json` (0.5ms2ns), and `sky130_ms_diff_ota_autozero_th15p5_t5000u_s2n_zero-pos06-pos065.json` (5ms). No layout, noise, mismatch, physical threshold DAC, beta/reset, weighted fan-in or closed-loop network acceptance follows from this screen. Next characterize SS/FF and temperature sensitivity, then build a calibrated physical threshold reference and repeat with weighted events.


### MOS process and temperature gate for sampled OTA readout — 2026-09-26

The one-event500us readout was repeated at2ns transient step with identical0.65/0.75V ideal OTA biases,15.5mV ideal second-OTA threshold source and typical passive R/C model, changing only the SKY130 MOS corner or simulator temperature. The result is a partial MOS-corner screen, not full PVT. At27C, SS/TT/FF retain respectively1.98/3.06/4.97uV for the same f=0.6 positive pulse at450us. Its second-OTA output remains high in SS/TT (1.790/1.731V) and goes low in FF (0.032V), so the decision flips. The f=0.65 case retains4.12/6.63/10.95uV and stays low in all three MOS corners.

At TT MOS and0C, f=0.6/0.65 retained events fall to1.19/2.73uV, while the comparator is low even for zero event (~0.011V). At TT MOS and85C, they rise to15.43/30.58uV, while the comparator remains high even for both events (~1.701V). The live-minus-held first-OTA shift for f=0.6 is only−3.45mV at0C and−1.63mV at85C, versus roughly−15.5mV at27C. Fixed ideal OTA biases, charge mapping and threshold offset therefore fail this basic process/temperature screen. These are named corner/temperature JSON reports from `scripts/test_sky130_ms_diff_ota_autozero.py`; no mismatch, passive corner, physical reference or chip calibration is represented. The nominal TT one-event result must not be promoted to a PLIF pass. Next search a bias operating region over temperature; if none supports a calibrated low-input-offset threshold, replace the OTA/readout method while staying analog.


### Bias trim and shared OTA input-mux feasibility — 2026-09-26

A DC scan of the existing physical SKY130 OTA across0/85C found temperature-specific ideal bias points near0.9V output at0.918V input common mode: `Vbn=0.65V`, `Vbp≈0.733V` at0C gives roughly−5,400V/V local gain, while `Vbp≈0.795V` at85C gives roughly−3,900V/V. In the500us physical baseline-sample transient, those biases restore a high no-event second-OTA output at both temperatures. At0C, gate fractions0.65 and0.66 retain+2.74/+3.24uV and produce high/low comparator outputs1.757/0.0307V. At85C, even fraction0.50 retains+4.04uV and places the comparator in its transition region (~0.380V);0.525 retains+5.63uV and drives it low (~0.060V). The same weight needs a large temperature-dependent gate correction as well as OTA bias/threshold calibration. All biases and gates here are ideal voltage sources, the comparator threshold remains an ideal15.5mV source, and no mismatch or full passive corner is included. The first0C bias point with lower tail drive had large no-event drift and failed; the higher-tail setting is a more useful operating screen, not a physical bias generator.

The nominal two-OTA baseline-sampled one-state prototype draws25.38uA from1.8V at450us in the no-event case, or about45.7uW before any bias/reference distribution. If replicated with continuous bias for all30,976,000 logical PLIF states, simple current scaling is roughly1.4kW; this is an architectural upper-cost scenario, not measured chip power. Three20um square MIMs per logical state (two membrane, one output sample) occupy37,171mm2 of raw square area, excluding all spacing, devices and routing. Two membrane capacitors alone occupy24,781mm2. This explains why the output sample and OTAs should be shared if the analog state array is to save physical area.

A new bounded shared-readout experiment keeps only the two20um MIM states per logical neuron. A readout channel's OTA gates are clamped to0.918V, its output baseline is sampled onto one20um MIM immediately before reading, and two physical TGs connect an isolated state pair at4.900ms. The second OTA compares live/held output with the same ideal15.5mV threshold offset. In TT, prepared3/6uV differentials are2.934/5.868uV before connection. At5us after connection they are2.520/5.040uV, with only−3.17/−6.34mV signal relative to zero; neither comparator has fired. With a50us connection window, at49us they are2.035/4.073uV. The3uV case stays high (~1.797V), while the6uV case is low (~0.031V). The stronger case is still high at10us, transitional at20us (~1.68V), and low by30us (~0.045V). A repeat at5ns versus10ns transient step reproduces the retained differential within~0.003uV and the same decisions. This readout loses about32% of the prepared differential by49us and has no actual synaptic pulse in the deck. Reports: `sky130_ms_diff_mux_readout_s{10,5}n_r50u.json`.

At30us per state decision, updating all30,976,000 logical states in5ms requires at least185,856 parallel readout channels even with perfect scheduling; actor dependencies and routing can only increase the demand. The test deck's three active channels draw76.53uA total at4.905ms, about25.51uA/channel. Keeping the optimistic minimum channel count continuously biased would be about8.5W at1.8V before DACs, routing and event circuitry. Sharing one20um sample capacitor per channel adds a raw minimum~74mm2 rather than12,390mm2 for a sample per state. These are arithmetic scaling bounds from a TT schematic, not extracted area or chip power. The current shared readout is still too slow and disturbs state for unqualified near-threshold accuracy; its PVT, mismatch/noise, physical threshold DAC and integration with the weighted injector/reset/beta remain open. Next optimize preamp settling/loading or replace it with a faster calibrated dynamic sense path, then evaluate full actor service time and physical area.

### Smaller shared input and faster compensation — 2026-09-26

The same physical MIM/TG/two-OTA shared readout with a2um first-OTA input pair instead of10um retains2.715/5.430uV of prepared3/6uV differential after49us connected, or92.5% of the preconnection2.934/5.868uV. With the original100fF OTA compensation, the6uV comparator is low by30us while3uV stays high. Reducing both OTA compensation capacitors to20fF makes the6uV case low by5us (0.0605V), with3uV still high (1.797V). The 6uV state is5.500uV at5us and5.404uV at49us. This is a faster nominal TT schematic screen; stability, device mismatch and physical capacitor implementation are unqualified. The20fF deck's three channels draw96.96uA at5us, approximately32.32uA/channel.

The bench now has a signed direct-MOS 10.5ns event option. At TT, readout starts500us and the event occurs400us after initialization; the +0.65 and−0.65 gate-fraction pulses leave +9.542/−9.542uV relative to matched no-event states immediately before reading at1ns transient resolution. At5us read time, positive comparator is0.0228V and negative/no-event comparators remain1.797V. Repeating at2ns changes the pre-read amplitude by~0.014uV and preserves both decisions. The full5ms/2ns three-case deck stopped before readout (return137, no measurements), so the short signed-event run and separate5ms prepared-state run are distinct evidence, not a demonstrated5ms integrated event path. Results: `sky130_ms_diff_mux_readout_weighted_at500u_s{1,2}n_r10u_win2_cc20.json`; prepared20fF result: `sky130_ms_diff_mux_readout_prepared_s10n_r50u_win2_cc20.json`.

At27C, prepared-state SS and FF MOS corners keep zero/3uV high and6uV low by9us using fixed0.65/0.75V ideal OTA biases and15.5mV ideal threshold; SS is transitional at5us (0.985V), FF is already low (0.0537V). Temperature with fixed bias fails: at TT0C all three cases go low, at TT85C all remain high. Ideal Vbp trims to0.733V at0C and0.795V at85C restore zero/3uV high and6uV low by9us; at5us the6uV outputs remain transitional (0.413/1.387V). There is no physical bias generator, calibrated threshold DAC, mismatch/noise or full passive-corner result. At10us/state, all-state service within5ms needs at least61,952 channels before actor dependencies. Nominal20fF channel bias~58.2uW implies~3.6W continuously biased under that optimistic count; measured current varies substantially over PVT. One20um sample cap/channel adds~24.8mm2 raw square area at this channel count. None of these scaling figures are a chip PPA result. Next build physical calibration/reference, characterize near-threshold noise/offset and multi-event+reset/beta behavior before architecture selection or layout.

### Physical capacitor threshold-offset mechanism — 2026-09-26

Replaced the ideal series threshold source in a bounded deck with a physical20um MIM output-sample cap and a small MIM connected to its comparator-reference top plate. After sampling the OTA baseline, dropping the small cap's bottom plate from an ideal programmed voltage to0 capacitively lowers the held reference. A1.7um square offset MIM with1.8V bottom swing creates10.47mV nominal pre-read offset at TT27C, not the15.5mV first-order target; switch/device parasitics matter. It still keeps prepared0/3uV comparators high and drives6uV low by5us. The same physical offset path with one ±0.65,10.5ns MOS event at400us gives ±9.555uV before read at2ns resolution and positive/negative/no-event comparator outputs0.0228/1.797/1.797V at5us. Reports are the `sky130_ms_diff_mux_readout_*capacitive1p7*.json` files.

At27C SS/FF and with ideal Vbp trims at TT0/85C, the1.7um capacitor likewise separates prepared3/6uV by9us. Pre-read offset is9.18mV at0C,10.47mV at27C,15.79mV at85C, and10.19/13.27mV at SS/FF27C. A2.1um offset cap gives17.65mV pre-read at TT and fails to resolve6uV even by9us. A3um cap with ideal0.5/0.7/1.0/1.5V bottom drive gives pre-read offsets7.41/12.08/19.03/30.19mV; only0.5 and0.7V split the tested3/6uV states by9us, and0.5V leaves the3uV output at1.784V, close to the comparator transition. This establishes programmability in principle, not a physical voltage DAC or a tolerance window. Actual MIM minimum geometry/DRC, bottom-drive source impedance, mismatch, thermal and flicker noise, offset calibration, and readout loading remain open.

The float checkpoint has1,856 static threshold parameters across25 actors, but encoder/context triangular adaptation adds a location-dependent penalty by summing active per-neuron processes (`src/eventspikeseg/model_components.py`, `_triangular_threshold_penalty` and `_threshold_tensor`). A shared static per-channel DAC alone cannot reproduce that dynamic threshold. The20um state pair has about100.8uV differential kT/C at300K, much larger than the3.112–6.397uV mapped final-fuse static thresholds; these nominal noiseless comparator outcomes cannot establish physical spike accuracy. The earlier reset-noise replay only samples one noise mechanism. Quantify dynamic-threshold implementation and circuit-aware noise at task level before treating this small-cap solution as viable.

### Per-decision thermal-noise task sensitivity — 2026-09-26

Extended the frozen-checkpoint task replay with independent Gaussian noise added to the effective final-fusion threshold on every update, equivalent to a differential pair's kT/C in voltage using the current0.15V/13,801-unit mapping. On three selected64x64 patches from validation record0, the20um pair's100.81uV sigma gives24.6% final-fuse spike mismatch and only41.3–41.8% segmentation argmax agreement to noiseless float. Reset-only noise on the same pair gives4.10% final-fuse spike mismatch and~68% argmax agreement; comparator-only plus reset gives17.0% and50.1–50.7%. This per-update comparator injection is a conservative stress, not measured readout noise. Output-sample-cap noise is not input-referred by this test; actual OTA transistor noise remains unmeasured.

Increasing only the ideal MIM width scales the assumed kT/C but produces a severe raw-area trade. At100um width, pair sigma20.31uV gives20.0% spike mismatch and~46.3% argmax agreement; at200um,10.17uV gives14.9% mismatch and~56.4% agreement; at1000um,2.03uV gives0.78% mismatch and~78.1% agreement. Replicating the two square MIMs across30,976,000 states would take about0.62m2,2.48m2 and61.95m2 of raw capacitor area at those respective widths, before spacing and circuitry. The1000um run is a noise scaling illustration, not a practical cell proposal. A shared single differential capacitor only improves the theoretical independent-pair kT/C from100.81 to71.28uV; the three-patch replay changes little (24.6% to24.0% spike mismatch and~41.5% pixel agreement). These comparator-only cases are stress tests, not candidate circuit results.

Membrane kT/C is modeled separately as one random offset at initialization and after each spike reset. Applying that noise to all25 active PLIF populations on five complete validation frames (record indices0,58,117,175,233; frame indices1,59,118,176,234) produces19.3% mean final-fuse spike mismatch and33.9% pixel argmax agreement. Mean labeled accuracy goes from37.38% noiseless to40.75% noisy across these five frames, while individual frame accuracy moves both directions; noise changes most output labels even when the mean accuracy rises. These five held-out frames are not a dataset-level estimate or evidence that noise is beneficial. A final-fuse-only reset-noise run on three other complete frames gives5.61% final-stage spike mismatch,59.2% argmax agreement, and mean labeled accuracy drops37.87→28.08%, showing that downstream population noise matters. Result files use `sky130_ms_diff_task_sensitivity_validation_*reset_only_independent_pair_mim20um_full_all_neurons_h0.15v.json`.

A software-only range sweep on one record yields final-fuse spike mismatch21.1/18.9% and argmax agreement44.6/48.4% at0.6/0.9V maximum candidate range, versus24.6%/41.3% at0.15V in a final-stage comparator stress. This modest improvement does not validate larger physical headroom; MOS injector linearity/common-mode, supply margin and the other actors are not simulated here. Next compare a correlated differential-storage/reset scheme and an active low-noise current/charge integrator, while preserving original full-float spike thresholds/adaptation. Any analog co-scaling must be tested against real weighted events and full-frame noise; no QAT was used.

### PDK OTA noise and brief-sample isolation tradeoff — 2026-09-26

Added ngspice `.noise` analysis using SKY130 TT/SS/FF transistor models for the same open-loop OTA used in the shared readout. At27C with20fF compensation and2um input width, integrated input-referred RMS noise from1Hz to100kHz is100.3uV TT,105.8uV SS,95.4uV FF; TT noise remains89.8uV over100Hz–100kHz,79.9uV over1–100kHz and62.9uV over10–100kHz. Raising input width to5/10/20um reduces TT noise to64.9/47.9/36.3uV over1–100kHz. This is an open-loop small-signal PDK result with ideal sources and biases, not transient input noise from the switched circuit. Gain at1kHz is4.12k/4.24k/4.81k/4.82k V/V for2/5/10/20um input width.

The larger 20um input pair loads the MIM more strongly and cannot meet the ideal threshold in9us when continuously connected. Adding a physical input TG sample phase (1us state connection) followed by gate isolation, plus a1.7um offset MIM whose bottom drive is ideally programmed to0.85V, preserves2.26/4.52uV of prepared3/6uV differential and drives the6uV comparator low by5us while3uV remains high. The corresponding state drops by~25% on sampling; noise still exceeds the mapped3–6uV threshold at0.15V headroom. No full-float weighted sequence, physical DAC, mismatch or transient-noise deck is included.

To map the 36.27uV TT/20um OTA estimate into model sensitivity at0.9V headroom, independent per-update threshold noise was applied to all25 active PLIF populations in three full-frame records. Baseline/noisy labeled accuracy is49.82/33.82%,32.92/29.90%,30.86/25.02%; mean37.87/29.58%. Pixel argmax agreement is57.7/53.0/55.1%; final-fuse spike mismatch is about13.1/11.2/9.9%. This is a conservative independent-noise model based on integrated small-signal OTA noise; actual sampling correlation and the closed-loop second stage may change it. It still indicates that current readout noise and input loading compete directly with the small mapped state signal. Full-frame noise reports: `sky130_ms_diff_task_sensitivity_validation_*comparator_only_independent_pair_mim20um_full_all_neurons_n36p27uv_h0p9v.json`. OTA sweeps: `sky130_ms_diff_ota_noise_*.json`.

### Two-phase OTA chopping screen — 2026-09-26

The existing physical MIM/OTA chopped comparator was run at a 100ns maximum transient step for representative positive, negative and near-zero states. It compares the same sampled state in opposite input polarities and subtracts the two output phases, suppressing static OTA output baseline. For the two large-packet cases, the state was about−64.72uV and+65.82uV during readout; chopped outputs were−7.215mV and+13.493mV, with the decision sign matching the state. Readout disturbed the differential by only+0.141uV and−0.056uV in these TT schematic runs. A near-zero−1.25uV case produced a2.716mV chopped output but the sign decision was wrong, showing that chopping alone has not established the few-microvolt threshold resolution needed by the mapped final-fuse model. This confirms baseline cancellation at large signal, not a noise reduction result: no mismatch, transient noise, PVT, calibrated common-mode/precharge, or full actor replay is included. Report files: `sky130_sc_ota_plif_comparator_chopped_{pp,nn,np}_s100n.json`.

Next gate: quantify chopped residual noise versus phase spacing using the physical OTA spectrum and a switched transient model, then run a bounded small-signal threshold sweep around the actual float-mapped thresholds. If the residual cannot separate those thresholds with adequate margin, keep exploring a low-noise charge/current integrator with the same full-float reference before any layout decision.
### Noise-aware analog path update — 2026-09-26

Exported the SKY130 OTA input-noise spectrum through 10MHz and estimated same-amplifier chop residual for ideal two-sample and boxcar-average cases. With the 20um input pair, a 1.5us phase separation gives about226uV RMS for two ideal samples; averaging each phase for1us still leaves about53.2uV. Widening the input pair to100um lowers the 1us-aperture estimate only to44.25uV (about17%); a200um device width fails PDK model bin selection. These estimates assume stationary open-loop noise and ideal boxcar sampling, so they are screens, not switched readout noise measurements.

A 53.18uV independent per-update threshold-noise replay on all25 active PLIF populations across one complete float validation frame lowers accuracy from49.82% to30.8%, with about47.5% pixel argmax agreement. At44.25uV, accuracy is31.4–32.6% across three noise seeds, pixel agreement54.3–55.6%, versus49.82% noiseless. Increasing OTA width alone is therefore not a sufficient remedy. The comparator-only replay is a conservative independent-noise approximation and omits real temporal/spatial correlation, but current chopper plus OTA does not have adequate measured or modeled margin.

Next pursue an event-charge accumulation path with a correlated/reference state and a narrow-band or end-of-update decision, reusing the existing physical switched-capacitor packet and integrator screens. Keep full-float thresholds and update semantics. Acceptance still requires actual weighted events, reset/beta and adaptation, complete-frame replay with a credible noise model, and service/area accounting before layout.

### Synapse event encoding selection — 2026-09-26

Retain fixed-width presynaptic event pulses and encode signed weight in the analog injected-current/charge amplitude. The nominal SKY130 direct differential MOS injector summed an actual370-event full-float final-fusion fan-in to within0.81–0.96% of the ideal target across forward, reverse and shuffled event orders using10.5ns pulses. The same fan-in encoded as pulse duration overshot the target by about6.7x at a30ns minimum pulse and about33x at750ns minimum, despite preserving event order. This makes amplitude-coded charge transfer the current analog candidate; pulse duration remains an explored but rejected encoding for this operating point. Evidence is one TT schematic neuron with ideal gate drivers and no noise, PVT, mismatch, physical per-weight storage, threshold/reset or network feedback. It does not qualify the full design.

The active bottleneck is membrane/readout noise: ideal two-phase OTA chopping improves static baseline cancellation but the OTA spectrum still implies44–53uV RMS per-update noise after an ideal1us phase average, and full-frame float replay remains far below baseline accuracy. Next integrate the amplitude-coded event charge on a differential state, investigate reference-correlated/band-limited sensing, and quantify area/service/noise before accepting the cell.

### Sample-isolated shared OTA readout with transient input noise — 2026-09-26

A second, topology-aware readout experiment supersedes the direct chopped-comparator near-zero failure for this candidate: the 20um differential MIM state is read through a 20um-input first OTA for1us, isolated onto a physical20um MIM output sample, and compared by a 2um-input/20fF second OTA using the physical1.7um MIM threshold-offset cap. Its bottom plate is driven by an ideal0.85V source. The read starts at500us; the comparator is observed5us after read start. A second-OTA equivalent transient voltage source uses ngspice TRNOISE at50ns updates; 330uV per sample approximately matches the high-frequency PDK input-noise density (~63.6nV/√Hz at10MHz), but the injected source is white and excludes flicker and device mismatch.

Across13 seeds at the calibrated source level, prepared3uV and6uV states remained on opposite comparator sides at5us. Their sampled states are about2.29uV and4.54uV; the first OTA's output-sense differences are about−4.1mV and−8.5mV from the zero state, creating several millivolts of comparator input margin after analog gain. Stress runs at2x/4x/8x source amplitude and16x/32x also preserved the decision for one seed each. This is a small bounded sample, not an error-rate or noise-yield estimate.

The topology also passed a direct weighted-event screen: one10.5ns differential MOS event at±0.65 gate fraction leaves approximately±7.1uV state; no event leaves zero. Across four independent TRNOISE seeds, positive state drove the comparator low, negative state drove it high, and zero stayed high. Thus fixed-width amplitude-coded MOS charge injection plus sample-isolated OTA readout is the strongest current analog candidate. It remains an ideal-threshold-drive, single-event/single-neuron TT schematic result; there is no flicker noise, mismatch, PVT, beta/reset, dynamic triangular adaptation, weighted fan-in through the complete readout, shared-channel schedule, or full-float network validation.

The earlier 44.25uV-per-update full-float replay adds noise directly at PLIF thresholds for all actors. That stress is not calibrated to this two-stage gain-and-sample topology, whose decision margin appears at millivolts after the first OTA. It remains evidence that direct floating-state thresholds are fragile; update the task replay to use measured state-to-comparator transfer and the sampled readout's actual margin before using it to accept/reject this candidate. Keep layout gated.

The earlier chopped-comparator attempt that placed an ideal noise source before the sample TG moved the membrane state by about44uV; it contaminated the stored state and is invalid as a comparator-only noise test. Do not use that result. The new test injects the equivalent noise at the second OTA after the state sample is isolated.

### First-stage noise invalidates the sampled-readout noise pass; buffered path follow-up — 2026-09-26

The second-stage-only TRNOISE screen above is not a complete readout-noise result. Adding a white-noise proxy at the first OTA output, before its physical output-sample MIM, exposes a compensation-capacitor path that feeds noise back into the membrane while the input TG is closed. With a1us state connection, the prepared 3/6uV states became strongly contaminated and decision outcomes varied; shortening that connection to0.1us yielded3/4 correct seeds, while10ns preserved prepared-state decisions across four seeds but caused large, seed-dependent state movement (approximately−19 to+30uV for the tested states). This output TRNOISE deliberately approximates integrated open-loop noise as160mV per50ns and is not a faithful colored/flicker transient model; it is evidence of a feedback-coupling hazard, not a quantitative noise yield. The preceding13-seed second-stage-only result must not be cited as system noise qualification.

A physical closed-loop unity-buffer alternative was re-run on a bounded `pn` MIM membrane sequence with a3.01uV offset reference,10.1x xhigh-poly gain stage, and10ns event timestep. At2um buffer input width, read disturbance was+0.012uV and the offset-cancelled output relation error was0.667uV. At4um, disturbance was−0.041uV and relation error improved to0.389uV. The4um case is the better current nominal point, but sub-microvolt error is still material against the mapped3–6uV final-fusion threshold and these simulations have no device-noise transient, mismatch, or extraction. The 100ns version is invalid for resolving the 10.5ns event sequence and gave a different result. Reports: `sky130_sc_ota_buffered_diffreadout_pn_s10n_rg1m_g10.1_bw2p0_th3.01uv.json` and `_bw4p0_th3.01uv.json`.

The follow-up computes noise through the closed-loop buffer's PDK transfer function with ideal sampled apertures; it shows that buffering alone is not sufficient. Finite switch loading still needs a transient model before accepting a readout or starting layout.

The follow-up PDK `.noise` analysis now uses the OTA wired as a physical unity-feedback buffer (signal is connected to its inverting input, matching the existing buffer cells). Boxcar estimates use dense frequency integration so the sampling sinc response is resolved. The4um/20fF buffer integrates to197uV RMS over1Hz–10MHz; ideal boxcar weighting gives87.2uV for one1us sample and123.3uV differential for two independent buffers. At20um/100fF these are48.9/69.1uV; at100um/100fF they are35.3/49.9uV. Increasing aperture to1ms still leaves15.2uV differential for the100um buffer pair. Reusing one amplifier sequentially gives estimated correlated chop residual44.0uV for100um devices,1.5us phase spacing and1us apertures. These calculations use the closed-loop small-signal PDK noise spectrum and ideal boxcar/sample correlation; they omit TG noise, settling, nonlinear behavior, mismatch, layout and actual state transfer. The1us noise estimates exceed the mapped final-fusion threshold range (about3–26uV at0.15–0.60V candidate headroom), and the1ms sample aperture would require over6million parallel channels to visit all30.98million states within each5ms update, before schedule overhead. Larger devices or simple buffering alone do not resolve the noise bottleneck. Reports: `sky130_ms_diff_ota_noise_tt_temp27_w{4,20,100}_cc{20,100}_f1-1e+07_unity.json`.

Accordingly, do not promote the closed-loop buffer as the selected readout. The next analog comparison is same-amplifier correlated sampling/autozero and a narrower-band event-charge decision, with actual switch/aperture loading and PDK noise transfer. If credible sampled noise cannot be brought below the full-float threshold margins within the5ms service budget, retain the amplitude-coded synapse result but reconsider the state/readout representation before layout.

The 100um/100fF unity buffer was also checked at SS/FF27C and TT125C with the same ideal biases. Its1us-aperture single-buffer estimates are41.5/30.6/36.6uV RMS (SS/FF/TT125C); two independent buffers give58.7/43.3/51.8uV differential. The TT27C differential estimate is49.9uV. Closed-loop gain remains approximately unity in these small-signal runs. This does not include bias startup, transient settling, switch noise or PVT-dependent state loading; it confirms the noise margin problem is not limited to the TT27C point. Per-corner result files use `sky130_ms_diff_ota_noise_{ss,ff}_temp27_w100_cc100_f1-1e+07_unity.json` and `sky130_ms_diff_ota_noise_tt_temp125_w100_cc100_f1-1e+07_unity.json`.

### Passive shared differential sampling-cap tradeoff — 2026-09-26

A physical capacitor-only differential sampler was compared at30/50/100/200um square MIM widths after the5ms state accumulation. At30um, the sample cap is1.811pF with47.8uV single-cap kT/C; it kicks the stored differential by8.09uV and the matched real-minus-dummy output differs from the post-sample membrane by about3.43uV. At50um,5.019pF lowers kT/C to28.73uV, but state disturbance rises to19.95uV; same-run real-minus-dummy transfer is within0.41uV of the post-sample membrane. At100um,20.038pF reduces single-cap kT/C to14.38uV but disturbs the stored differential by42.96uV; the raw sample relation error is−2.79uV. At200um, the80.076pF transient deck exceeded the bounded60s runner timeout, so no transfer or kick result is accepted; its ideal single-cap kT/C would be7.19uV. The sample width that improves kT/C loads the20.076pF state increasingly strongly. At the tested~49.4us sample aperture, reading all30.976million states within5ms needs about310,000 parallel channels; just two raw sample capacitors per channel would occupy about558/1,549/6,195/24,781mm² at30/50/100/200um width, before switches, OTA, routing or spacing. Shorter service is not demonstrated. Results are TT schematic only; no transistor buffer, switch noise, mismatch, extraction or task replay.

This shared-cap route is not a replacement for a low-noise isolated readout as presently connected. The30um signal is readily kicked and kT/C exceeds the mapped threshold; the100um cap loads state substantially; the200um case is too slow for this bounded deck. Next compare a differential active charge bucket or regenerative threshold path that does not directly share charge with membrane state, and include its area/service cost. Keep all findings scoped; no layout.

### Clocked regenerative comparator first-pass screen — 2026-09-26

Ran `scripts/test_sky130_regenerative_comparator.py` in the bounded ngspice Docker image. With TT symmetric devices, ideal DC inputs, an ideal clock and20fF per output, a cross-coupled latch regenerates ±3, ±6 and ±26µV input differences to the correct output polarity by the first sampled point at105ns (5ns after the ideal clock edge), for 1/2/4µm input-pair widths. Zero differential resolves to an arbitrary startup polarity for 2/4µm and is not a valid decision; the 1µm zero case remains near balanced. The first sample is already rail-like because this setup has no realistic input acquisition, parasitic loading or noise.

This is only a latch logic/speed smoke, not evidence that it resolves a real 3µV membrane state. The PDK checkout exposes no verified statistical mismatch model in this bench; no offset/noise, switch kick, source capacitance/impedance, threshold DAC, PVT or extraction was included. Next test a proper sampled differential interface with physical MIM source caps and switches, and establish offset/noise cancellation before comparing decision margins. Keep regenerative sensing unqualified and do not start layout.

### MIM sample-to-latch interface screen — 2026-09-26

Added a physical MIM plus SKY130 transmission-gate interface ahead of the regenerative latch. This first direct sampler is not viable as drawn: before latch evaluation, the nominal ±3µV differential is swamped by switch/reset feedthrough. For 5/10/20µm sample caps, the measured zero-input differential at90ns is +34.9/−2.8/−2.0µV; the corresponding ±3µV cases sit at roughly ±32/±0.2/±1.0µV around those offsets, with sign sensitivity varying by cap size. Therefore the ideal latch screen does not transfer to a physical sampling input. The 20µm cases show incorrect sign under this sequence. This is a nominal TT screen with ideal DC-clamped source nodes, so it omits source impedance, realistic membrane event history, mismatch, noise and extraction; do not interpret the offset values as a final sampler characterization.

Next reuse the existing bottom-plate differential sampler and matched dummy/reference concept, then measure residual input differential immediately before latch evaluation and test both signs at3/6µV. The direct reset-and-sample interface remains rejected; regenerative sensing remains an unqualified option. No layout.

### Bottom-plate sampler plus latch — 2026-09-26

A six-case bounded TT run connected the existing bottom-plate physical MIM sampler and a matched dummy directly to the regenerative comparator. The10µm sample-cap option had about+0.10µV zero-input residual at the pre-latch nodes, but source differentials of±3µV became only about±0.08µV at those nodes. The ideal latch followed the sampled input polarity, but this transfer leaves almost no practical margin for comparator offset/noise. At30µm, the zero-input differential rose to about+59.8µV and the−3/+3µV cases produced about−60/+59.5µV, so one polarity is dominated by sampler feedthrough. The first15-case deck exceeded the60s Docker limit; the reduced six-case deck completed in about12s.

This small run has an ideal clamped source, identical schematic dummy, nominal TT devices and no mismatch, noise or parasitic extraction. Its cap-size-dependent transfer and offset need a sampler-only calibration against the existing membrane source topology before attributing the full residual to a valid circuit result. Current status: neither direct nor bottom-plate sampling is qualified for the3µV threshold; keep the regenerative latch as an exploration only. Next bound a sampler-only ±3/6µV transfer sweep, establish how the physical source MIM capacitance and switch sequence affect signal gain and offset, then reattach the latch only if the sampled margin survives.

### Transfer calibration follow-up — 2026-09-26

A higher-signal ±100µV run did not agree with the earlier ±3µV screen: the10µm sampler-plus-latch input showed near-unity magnitude with reversed sampler polarity and a few-microvolt zero residual, while the30µm cases were strongly asymmetric with tens of microvolts of offset. Tightening ngspice convergence below the normal PDK settings caused transient timestep collapse at the ideal DC source branch; the raw data file was incomplete and is not evidence. The transfer is therefore uncalibrated across signal scales. The sampler scripts now preserve separate ±3µV and ±100µV results and report the tighter run as a failed diagnostic rather than accepting partial data. Next isolate one sampler cell from the latch, calibrate ±3/6/100µV with looser stable tolerances, then add source MIM and latch loading in separate steps.

### Corrected switch order supersedes the first bottom-plate result — 2026-09-26

The earlier bottom-plate sampler benches opened the signal-side and reference-side switches together. Correct sequencing opens both together and turns the signal-side switch off first, followed by the reference-side switch0.5ns later. With that correction, a sampler-only TT bench using a10µm physical MIM, PDK TGs, a matched dummy and a20pF source MIM preserves the differential from−100 to+100µV with transfer gain−0.9982 and zero-input residual≈0 at the saved precision. At±3 and±6µV, residuals are within about0.01µV of the linear relation. The sampler-only transfer is now promising under ideal clamped-source conditions; the previous conclusion that bottom-plate sampling itself was unusable is superseded.

Reattaching the regenerative latch gives a different result: at±3µV both signs are resolved correctly in the five-point single-channel screen, but−6µV is resolved with the wrong latch polarity while+6µV is correct. The sampled input is otherwise near±6µV, so this points to a latch start-up/decision-boundary asymmetry that must be isolated. The latch has no statistical mismatch or noise in this model; do not treat this as a measured silicon offset distribution. Next isolate the latch decision boundary over a denser signed input sweep and vary precharge/evaluation timing, then combine it with the calibrated sampler. Still no noise/PVT/extraction qualification and no layout.

### Regenerative latch boundary and sampler-attached behavior — 2026-09-26

A dense ideal-input SKY130 TT boundary screen at2µm input width resolved all nonzero differentials from±2µV through±10µV to the correct polarity by the first sampled point5ns after evaluation; exact zero remained arbitrary. That confirms the ideal latch topology itself can resolve below the mapped±3µV level in this deterministic simulation.

In the corrected, single-channel bottom-plate sampler-plus-latch bench, the±3µV cases resolved correctly, but the−6µV case selected the wrong latch polarity while+6µV selected correctly. At90ns the sampler output-minus-dummy values were approximately+5.59, +3.16, +0.23, −3.14 and−6.05µV for source inputs−6, −3, 0, +3 and+6µV respectively. Thus the isolated sampler transfer is nearly ideal, while the connected latch exhibits polarity asymmetry dependent on phase history/startup. This is not an analog acceptance pass; device mismatch and noise are absent. Next apply correlated input autozero/precharge and sweep the delay from sample isolation to evaluation, then see if the decision boundary becomes symmetric. Keep the sampled readout unqualified; no layout.

### Clock-gated latch correction and sample-noise gate — 2026-09-27

The prior regenerative latch was invalid as a clocked comparator: its cross-coupled NMOS devices were permanently tied to ground, and its outputs had already resolved to opposite rails before the evaluation clock. Added a clocked footer to that pair in `scripts/test_sky130_regenerative_comparator_clocked.py`. With the corrected10µm bottom-plate MIM sampler and matched dummy, both latch outputs are1.8V and matched within0.01µV just before evaluation. The sampled input is ±2.95/±5.90µV for ±3/±6µV source differences. All four nonzero signed cases resolve with the expected polarity; the first 0.5V differential decision occurs about3.5–3.7ns after the clock edge at both65ns and100ns evaluation timings. Exact zero remains unresolved. The older ideal-latch 5ns claim and sampler-attached asymmetric decisions came from the always-active latch and are superseded. This is TT deterministic schematic logic only with ideal clamped source; no statistical mismatch, transient noise, PVT, finite source impedance or extraction.

The physical10µm sample MIM is approximately203.8fF. At300K its unavoidable isolated-capacitor kT/C estimate is142.6µV RMS; two independent real/dummy samples give approximately201.6µV RMS differential before switch/latch noise, about67 times a3µV signal. Nominal resolution therefore does not establish a viable near-threshold readout. The earlier final-fusion three-patch replay already shows3.72% spike mismatch for a141µV independent per-update state-noise proxy at0.30V headroom; it is a sensitivity bound, not this circuit's complete task accuracy. Achieving3µV RMS differential kT/C alone would require roughly920pF per sample capacitor (~678µm square at2fF/µm²), before helper circuitry and service constraints. This is a conditional3µV noise target, not a model-derived acceptance limit.

Next pursue a front end that develops gain before thermal sampling or senses the membrane directly with a clocked comparator, and measure its state disturbance and noise with the physical storage capacitor. Account for reset, beta, adaptation, throughput and area before any layout acceptance. The clocked10µm sampler/latch remains a nominal functional reference, not the chosen implementation.

### Direct physical-MIM clocked readout and early isolation — 2026-09-27

A direct readout screen initialized matched100µm physical MIM state/reference capacitors through PDK TGs for2.5µs, then connected them to the corrected clock-gated latch. The prepared differentials reached−6/−3/0/+3/+6µV. Keeping the read TGs on through full regeneration makes the correct nominal latch decision but changes the stored differential by about69.48µV, sign-dependent. This destroys membrane retention at the mapped few-microvolt margin.

Opening the read TGs0.5ns before evaluation removed measured state disturbance in this deterministic run. Opening0.5/1/2ns after the clock edge left maximum absolute disturbance about0.004/0.005/0.049µV across the five input cases while keeping all nonzero decision signs. Opening3ns after the edge raised disturbance to0.759µV at a3µV state and1.519µV at6µV. At2ns, the latch had developed about1.63mV output differential from3µV state input before isolation, so this is a plausible gain-before-isolation sequence. It remains one TT schematic timing screen with ideal clocks and no mismatch, transient noise, PVT, extraction, reset/beta/adaptation or complete SNN event sequence.

The isolated latch input capacitance is only about4.07fF at0.9V precharge bias in a PDK AC admittance screen (stable from0.1–10MHz). Its kT/C scale at300K is approximately1.01mV RMS per input, or1.43mV for an independent differential pair if the read TG's opening leaves a full thermal sample. This is an estimate, not a transient-noise measurement of the dynamic latch; it blocks treating the nominal early-isolation decisions as noise-qualified. The100µm MIM state itself is about20pF and has≈14.4µV one-cap kT/C in the existing geometry screen; replicating one per30,976,000 logical states implies≈309,760mm² bare MIM area before routing and support. The analog architecture must solve state storage as well as comparator noise. Continue investigating shared charge-domain gain or a process-supported dense analog state store, and quantify service/area before layout.

### Corrected full-float reset-noise replay and readout boundary — 2026-09-27

The prior reset-only and combined reset/comparator full-float sensitivity results are **invalid**. The replay code replaced the subtractively reset PLIF membrane with pure random noise after a spike, including at zero noise. `scripts/analyze_sky130_ms_diff_task_sensitivity.py` now adds the sampled perturbation to the actual post-reset state. A full 440×640 zero-noise validation-frame control reproduces the original float final-fusion spike bits, pixel classes and logits exactly. Comparator-only replays were unaffected by this particular bug, but still have their own noise-model limits. New reports carry `_corrected_subtractive_reset.json` and `reset_noise_preserves_subtractive_state=true`; the old reset-only/both-mode files must not support architecture decisions.

Using the best full-float epoch-58 checkpoint, all 25 PLIF populations, 0.9V candidate headroom, three seeds and complete validation frames, an independent-pair reset-noise proxy for a 10µm MIM pair (199.76µV RMS) gives mean labeled accuracy 30.49% on record 0 versus 49.82% float baseline, 45.33% pixel agreement and 15.59% final-fusion spike mismatch. A 100µm pair (20.31µV RMS) still gives 35.67% accuracy, 62.15% pixel agreement and 11.97% spike mismatch on record 0; record 1 gives 34.86% versus 48.18% baseline, 61.79% agreement and 11.89% spike mismatch. An artificial 0.18µV case on record 0 gives 49.76% versus 49.82% baseline, 87.84% pixel agreement and 2.28% spike mismatch. These are bounded task sensitivities for independent reset perturbations, not measurements of a built cell, a dataset-wide accuracy estimate, or an acceptance target. They show that enlarging per-state SKY130 MIM capacitors to 100µm square does not close the sampled task sensitivity, while bare one-cap-per-state geometry is already approximately 0.31m².

At a 2ns read-TG cutoff after latch evaluation, injected opposing current pulses on the isolated latch inputs provide a deterministic margin stress. The measured opposing input shift for the +3µV state is 1.20/2.22/3.25/4.27mV at 40/80/120/160nA. Both ±3µV decisions survive 40nA but flip at 80nA; ±6µV survive through 120nA and flip at 160nA. This does not sample transistor or switch noise and cannot be converted into yield. The evidence summary is `artifacts/analog_asic/results/sky130_readout_architecture_boundary.json`; its readout-noise, state-storage and full-architecture acceptance flags remain false. Next compare a shared active differential charge bucket with process-supported analog state storage and its 5ms service/area cost. Any further latch work needs credible switched-noise and mismatch characterization before task acceptance.

Even granting the measured3.705ns nominal decision time as the entire service interval, one read of each of30,976,000 identities within5ms requires at least23 simultaneous channels (count × service time / deadline, rounded up). This optimistic arithmetic omits input acquisition, precharge, switching, beta/reset/adaptation, graph joins and routing. It shows that a fast shared latch could be economical if the complete acquisition cycle remains short. Sharing a comparator does not eliminate the independent state-storage requirement or prove the schedule.

For illustrative **total** service times of10ns/100ns/1µs/10µs per state, the same arithmetic requires62/620/6,196/61,952 channels. These are conditional concurrency counts, not circuit measurements. The dominant unresolved question for sharing is the complete switched acquisition and state-update cycle, especially its noise and stored-state disturbance.

The existing `sky130_sc_charge_integrator` is not a ready shared bucket. Its nominal two-packet OTA feedback screen reports up to27.14µV error against independently measured packets, and later full-bin reconnect experiments move the output by about14.5–15.7mV despite sleep or soft-start variants. Reusing that enable/reconnect path would overwhelm the few-microvolt final-fusion decisions. The next charge-domain candidate must keep an explicit differential charge reference across the whole bin or physically cancel each reconnect transient, while preserving a separate state for every logical neuron. Its weighted-event sequence, noise and state transfer need physical evidence before it can replace the direct-MOS branch.

### Correlated state reset and alternate open-PDK capacitance screen — 2026-09-29

For two equal100µm SKY130 MIM state caps, the independent-pair thermal reset proxy is20.31µV RMS. If their reset errors have correlation coefficient `rho`, the differential RMS is `20.31*sqrt(1-rho)` µV. Illustrative differential levels of3µV and1µV would require `rho≥0.9782` and `rho≥0.9976`, respectively. Neither level is a model-derived acceptance target. Device matching does not create thermal-noise correlation; a candidate shared reset/reference sequence must demonstrate the covariance physically, including its switches and timing. Two100µm caps per30,976,000 states occupy≈0.620m² bare MIM area, twice the previously quoted one-cap lower bound.

Checked published open-PDK capacitor densities before proposing a process migration: SKY130 MIM3 and MIM4 are each nominally2fF/µm² and may be stacked ([SkyWater device details](https://skywater-pdk.readthedocs.io/en/main/rules/device-details.html)); GF180MCU offers1.0/1.5/2.0fF/µm² MIM options ([GF180 electrical specifications](https://gf180mcu-pdk.readthedocs.io/en/latest/analog/spice/elec_specs/elec_specs_6_4.html)); IHP SG13G2 lists1.5fF/µm² ([IHP process control parameters](https://ihp-open-pdk-docs.readthedocs.io/en/latest/process_specs/02_process_control_params.html)). Thus the checked process options do not offer an order-of-magnitude density improvement over the active SKY130 MIM; even ideal two-layer SKY130 stacking would at most halve this bare-area bound. This is a capacitance-density comparison, not a foundry/process selection or a full storage-cell comparison. The next analog work should address reset/readout noise covariance and per-state storage topology before investing in a new PDK port.

Ran the corrected full-float replay at illustrative differential reset-noise levels using the same 0.9V candidate headroom, all25 PLIF populations, complete440×640 validation records and three seeds. At3µV RMS, record0 mean labeled accuracy is49.59% versus49.82% baseline, pixel agreement81.59%, and final-fusion spike mismatch3.99%; record1 gives48.32% versus48.18%, pixel agreement79.84%, and spike mismatch4.29%. At1µV on record0, mean accuracy is49.53%, pixel agreement83.28%, and spike mismatch3.39%. The non-monotone small accuracy changes across these two frames are not a task-level win or loss estimate; roughly16–20% changed pixel classes and3–4% changed spike bits still matter. These injected Gaussian reset proxies omit physical noise correlation, readout noise, mismatch and event-transfer errors. Consequently the3µV/1µV covariance examples are circuit probes only; neither can be declared sufficient from two records or from labeled-pixel accuracy alone. Reports use `sky130_ms_diff_task_sensitivity_validation_{0,1}_reset_only_independent_pair_mim100um_full_all_neurons_n{1,3}uv_h0.9v_corrected_subtractive_reset.json` where present.

Added six-class IoU to the corrected replay, averaging classes whose ground-truth/predicted union is nonzero in each frame. At3µV RMS, record0 mean IoU is0.20503 versus0.20573 baseline; record1 is0.19931 versus0.19892. Replaying the actual100µm independent-pair kT/C proxy (20.31µV RMS) on the same frames drops mean IoU to0.11938 and0.11726, from0.20573 and0.19892 respectively. Thus the original100µm MIM reset-noise scenario is poor even by the segmentation task metric on these two records; the3µV proxy is much closer but remains a two-record software sensitivity, with about4% spike mismatch and unmeasured circuit noise. Do not call the3µV point accepted or extrapolate these per-frame IoUs to the validation set.

The float PLIF subtracts threshold charge after a spike; it does not hard-reset the membrane to a rail. A charge-subtraction implementation could avoid a fresh full-capacitor thermal sample on every spike. To separate that effect, the replay now supports `--noise-mode init-only`, injecting one independent state perturbation at record start and none after spikes. At20.31µV RMS, mean IoU is0.12120/0.11591 on validation records0/1, versus0.11938/0.11726 with the earlier initialization-plus-post-spike proxy. Pixel agreement is62.67%/62.01%, and final-fusion spike mismatch11.87%/11.87%. Thus in these two frames, noisy initialization alone explains most of the loss; avoiding post-spike resampling is necessary for faithful subtractive reset but insufficient to rescue this100µm pair. The proxy still assumes independent initial noise and omits physical reference correlation, readout, mismatch and event transfer. The new reports are `sky130_ms_diff_task_sensitivity_validation_{0,1}_init_only_independent_pair_mim100um_full_all_neurons_n20.3132uv_h0.9v_corrected_subtractive_reset.json`.

### MIM area/correlation sweep and physical baseline-reference check — 2026-09-29

The existing SKY130 typical MIM geometry sweep now reports two-cap full-inventory bare area alongside the reset-noise correlation needed for an illustrative3µV differential RMS. A10µm pair is about199.76µV independent RMS, occupies≈6,195mm² of bare caps across all states, and would require `rho≥0.999774`. A20µm pair is100.81µV,≈24,781mm² and `rho≥0.999114`. A100µm pair is20.31µV,≈619,520mm² and `rho≥0.978189`. The1µm pair would occupy≈62mm² but has1.73mV independent RMS and would require `rho≥0.999997`. These are thermal/geometry calculations at300K, excluding helpers and routing. The3µV level is a full-float two-frame design probe, not an accepted noise specification; matching alone cannot provide the listed correlation.

Extended the existing physical20µm MIM/OTA output-baseline-sample bench with controlled initial state differences of−20/0/+20µV, keeping the same positive10.5ns MOS event. TT physical TGs and MIMs were used with ideal OTA bias, clock and threshold; no thermal noise or mismatch was simulated. The measured pre-event state differences are−32.109/−13.945/+4.199µV because initialization/sense loading adds a common offset. The no-event output-minus-held relation after the event window is+0.856/+0.373/−0.045mV, a0.901mV span. The event adds≈4.12µV of state in all three cases, and its **simulator-subtracted** event-minus-no-event output is−0.769/−0.743/−0.745mV. That subtracted event transfer is fairly stable, but the actual held-output baseline varies more than the small event response and all three second-OTA outputs remain high with the ideal15.5mV threshold. The sampled baseline therefore does not demonstrate a usable per-state correlated reference or near-threshold decision. It also requires an extra output MIM and an OTA per case in this bench. Do not promote this circuit or infer thermal covariance from the deterministic sweep. Machine-readable results: `artifacts/analog_asic/results/sky130_readout_architecture_boundary.json` (`correlated_state_geometry_tradeoff`, `physical_autozero_initial_offset_screen`).

By400µs,250µs after the event, the simulator-subtracted event response has slowly grown to about−15.4mV, but second-OTA outputs are still high or transitional (1.18–1.77V) across the three initial offsets. The no-event held-output relation still spans about0.90mV. This slow settling and offset dependence further disqualify this per-state OTA/output-sample cell as a shared 5ms readout without substantial redesign; the signal must be decided at the real completion time, not inferred from subtraction of separate simulation cases.

A bounded near-threshold sweep makes the failure explicit. At gate fraction0.601, the same positive10.5ns event adds≈4.18–4.20µV relative to a no-event control under−20/0/+20µV initial state offsets. The event-minus-no-event output at400µs is approximately−15.72/−15.71/−15.63mV, yet the **actual** second-OTA outputs are1.756/1.609/0.230V respectively. Using0.9V as the nominal logic boundary, the first two stay high and the+20µV case goes low. This is a deterministic decision flip from initial offset, with physical MIM/TG/OTA devices but ideal clocks, bias and threshold. It confirms that event-transfer stability after simulator subtraction does not imply a robust hardware threshold decision. No thermal-noise distribution or yield is claimed. The architecture report records `physical_autozero_near_threshold_initial_offset_screen` with `all_initial_offsets_same_decision=false`.

### First-touch physical replay of actual float fan-in — 2026-09-29

The SS/0°C,10µm MIM/TG/four-MOS injector now receives actual signed folded float weights and activation multiplicities from the epoch58 checkpoint at three selected final-fusion sites. The fixed pulse is40.253ns with50.253ns event spacing, derived from the stage's sampled maximum static weight under illustrative0.9V headroom. Gate levels are ideal voltage sources. The selected maximum-fanin site has370 events and an ideal−52.45418mV current contribution. A sparse measured10.5ns single-event charge curve with linear charge interpolation gives−49.97680/−50.42191/−50.18166mV for forward/reverse/shuffled orders (3.87–4.72% magnitude deficit). A directly measured40.253ns curve with the same linear interpolation gives−50.04443/−50.49053/−50.24976mV (3.74–4.59% deficit). Log-charge interpolation of the40.253ns curve gives−51.58534/−52.24758/−51.88725mV (0.39–1.66% deficit), but the forward/reverse/shuffled order span is0.66224mV. Thus interpolating a steep transfer curve is material, and large-sum state/order effects remain. These are physical schematic simulations with tight solver, not calibrated silicon.

At a high-cancellation site,322 actual events sum ideally to+7.491nV. The log-mapped schematic yields+6.904/−6.133/−1.278nV; two individual weights are below the measured low gate point and clipped. Nanovolt sign changes are not a useful claim of device precision or noise robustness. At a second high-fanin site selected for current near a typical threshold scale,329 actual events contribute ideally+32.62296µV and physically+32.64535/+32.63152/+32.63544µV. The latter errors are about9–22nV, with13.83nV order spread. This near-threshold-scale current is **not** a complete neuron threshold test: saved membrane state, beta, subtractive reset and dynamic threshold are absent. The isolated10µm pair has an approximately200µV independent thermal-noise proxy and physical switched/readout noise is unmeasured; deterministic nanovolt agreement cannot qualify decisions. Evidence: `sky130_ms_first_event_ss_stage_width_transfer.json`, the `sky130_ms_first_touch_float_fanin_ss0*.json` results, and `sky130_readout_architecture_boundary.json` in `artifacts/analog_asic/results/`. Next isolate weight-DAC resolution and calibrated gate-transfer stability, then connect a physically valid readout and update loop before any full-float network replay or layout.

The same370-event site was also run at TT/27°C and FF/85°C after measuring separate40.253ns gate curves at each corner. With each corner's own *ideal externally supplied* log-interpolated map, TT produces−51.57901/−52.23565/−51.87812mV and FF−51.75894/−52.44067/−52.06918mV for forward/reverse/shuffled order, versus−52.45418mV ideal. The errors remain0.03–1.67% in magnitude but ordering still spans0.657–0.682mV. Holding the SS map fixed at TT instead yields−141.3421 and−147.8873mV in separately completed forward/reverse decks, or2.69–2.82× the intended magnitude. The combined TT deck's shuffled circuit suffered a timestep collapse at13.85µs and is excluded. At FF with the SS map held fixed, forward/reverse/shuffled results are+25.593/−596.009/−482.443mV, including a sign reversal; this is a completed schematic transient with large overdrive, not a usable operating point. The contrast demonstrates that the ideal per-corner gate table is indispensable. No on-chip sensor, analog reference, gate programming, interpolation, trim, mismatch or live tracking exists. Source JSONs use `sky130_ms_first_touch_float_fanin_{tt27,ff85}*.json` and are summarized by `physical_first_touch_weight_map_corner_screen` in the architecture boundary report.

### Physical analog weight gate storage — 2026-09-29

A bounded SS/0°C sample-and-hold bench programs two physical SKY130 MIM capacitors through TGs to the p/n injector gate levels, holds them, then applies one40.253ns positive event to a10µm first-touch membrane pair. Directly switching a10µm stored gate capacitor onto the MOS gate causes large charge sharing: after a short hold the stored p/n nodes move about+122/−47mV during the event, and the delivered differential is101.61µV versus408.94µV with ideal direct drive. After5ms, the programmed p/n levels have drifted−2.984/+38.624mV before connection. A20µm pair reduces but does not remove this error. With a100µm pair and a longer10µs programming window,5ms drift is−0.033/+0.420mV, yet the event still differs from direct drive by−11.87µV (−2.90%). Two100µm capacitors per143,728 folded PLIF weights alone require≈2,874.56mm² bare MIM area, excluding the96 head weights, switches and routing. The1µs programming window used in the first100µm run was too short; only the10µs result is used for its area/error comparison.

The alternative holds the weight capacitors continuously on the MOS gates and steers current at the drains. With idle drain nodes clamped to rails, a gate-off event switch still moves the membrane differential≈21.93mV, compared with≈3.19mV of gate-dependent contribution at fraction0.5. Clamping the idle drain nodes to VCM reduces the gate-off switching contribution to≈0.351µV and the ideal gate-dependent contribution to≈2.837µV, but produces continuous idle current (the four-cell comparison bench draws≈1.9µA from its shared1.8V supply just before the event; this cannot be divided into a validated per-weight power figure). After5ms at fraction0.5, the gate-dependent contribution is+91% over the ideal-gate value with a10µm pair, +20% with20µm, +3.1% with50µm and +0.77% with100µm. The corresponding bare two-cap areas across folded PLIF weights are28.75,114.98,718.64 and2,874.56mm². At10µm, hold intervals100/500/1000µs give approximately−5.0/+0.7/+8.4% error relative to an ideal-gate event; the nonmonotonic result includes programming offset and cannot justify a simple500µs refresh schedule. This is a deterministic one-weight, one-event schematic screen without thermal noise, local mismatch, refresh hardware, many-weight mapping, full-fanin accumulation, readout or extraction. Machine evidence is `sky130_ms_weight_gate_storage_boundary.json` and `physical_analog_weight_gate_storage_screen` in `sky130_readout_architecture_boundary.json`.

The existing physical two-stage OTA was then screened as a shared unity-gain gate buffer at SS/0°C. With ideal `Vbn=0.65V` and `Vbp=0.733V`, DC follower error is about−0.024mV at0.936V p-gate command, but−1.246mV at0.48V and−2.672mV at0.30V n-gate commands; these errors are not calibrated out. With the direct injector MOS gate capacitances connected, an ideal simultaneous step from off rails to0.936/0.48V at1µs settles the p output near command by1.1µs, while the n output remains near0.013V at1.1µs, overshoots to0.563V at5µs and reaches near its final0.47875V around7–9µs. The two-OTA bench, including MOS drain loads tied to ideal VCM, draws about15µA from1.8V; this is not an isolated buffer-only power figure. A shared buffer with prefetch and calibrated low-voltage response remains a circuit option, but the current OTA cannot be treated as a50ns per-event driver. This is DC plus one loaded step only, with no sampled weight capacitor, mux, switching charge, noise, mismatch, event injection or population service. Evidence: `sky130_ms_weight_gate_unity_buffer_ss0.json`, `sky130_ms_weight_gate_ota_buffer_settle_ss0_f0p8.json` and `physical_analog_weight_gate_buffer_screen` in the architecture boundary report.
