## 2026-10-18 - Microelectronics Journal adaptation

Final delivery check (18 October 2026): rebuilt and visually reviewed the 10-page manuscript and 5-page reusable figures; corrected GDS-to-PDF coordinate precision. Editable source bundle and submission_manifest.json are in article/submission/. Abstract, highlight lengths and citation keys checked; no LaTeX warnings. Author declarations/data deposit remain pending.

Converted the current article to Elsevier `elsarticle`, refined the circuit-focused presentation and completed a bounded reviewer edit from existing evidence. Added journal-specific highlights, numbered references, separate artwork, data/funding/conflict/contribution/AI sections and supplied author metadata/ORCIDs. Replaced low-resolution conceptual artwork with an editable vector redraw and preserved historical figures. Journal choice and remaining author submission items are recorded in ACTIVE_TASKS, RESULTS, DECISIONS and project_spec.yaml. Backup: `artifacts/article_work/microelectronics_20261018/before_changes.zip`. No circuit simulation, Docker operation, GDS edit, staging, commit or submission.

## Article reviewer pass and final figures - 2026-10-15

Corrected Figure 1 in the original illustration style and removed the historical appendix duplicate. Added the full GDS hierarchy overview to the manuscript; generated `_publication.svg/.png` variants next to the original exports and regenerated native KLayout panels with darker outlines. Added plots of all 2,360 retained selected-state transient samples, the 54,630,400-state breakdown, typical 3.3 V / 27 C conditions, and the 59/6/3/3/3 result-method breakdown. Updated the area discussion to the final bank geometry. Both PDFs compile and were visually reviewed (9/5 pages). Full GDS SHA256 remains unchanged. No new simulation, permanent deletion, staging or commit. Backup: `artifacts/article_work/before_article_review_20261015T161841.zip`.

## ASIC source cleanup — 2026-10-15

`asic/` is retained hardware source/build input; final results remain in `artifacts/analog_asic/`. Archived 38 superseded/provisional/metadata files (171,273 bytes) to `bin/asic_source_cleanup_20261015T115233Z`; 185 original source/configuration files remain. Final GF180 control roots and retained digital tool/test dependencies are preserved; the older parallel scatter source stays because the pw128 wrapper uses it. All 223 original hashes were checked after the move; the README was then refreshed with its original in before_changes.zip. Bin includes inventory, restore script and audit; artifact resolver handles archived original paths. No tests/simulations, permanent deletion, staging or commit.

## Wire-hidden device views and full model figures — 2026-10-15

The user requested regeneration with invisible wiring in PLIF/injector panels and visible wiring in the native 64-state bank. KLayout now hides metal1–5 and via1–4 for panels (a)/(c), with enlarged device windows; bank panel (b) is unchanged. Source GDS files are not modified. Renderer: scripts/render_article_gds_devices.py; source hashes, windows and hidden layer pairs: article/figures/gds_device_manifest.json. These are device-layer illustrations, not complete connectivity views. Full current 140k architecture is restored to the main model section (page 3) as an editable vector TikZ diagram. Original 140k_v4.png is preserved in the appendix (page 8), explicitly identified as the earlier detail32/selector96/spike-count topology. Current model detail8/fusion40-to-16/continuous16-to-6 remains authoritative. Both appear in Blocks_figures.tex. Article: 8 pages; reusable figures: 5 pages; compiled and visually reviewed. No circuit changes or new simulations.

## Model detail preservation and section figures — 2026-10-15

Restored detailed model and training content alongside GF180 implementation results; added the 25-actor layer/state table and corrected the residual-block caption to distinguish standard from DW/PW variants. KLayout produced five device-section PNGs with exact source hashes/cell coordinates. PDF visual review corrected float placement/alignment. Final article: 7 pages; reusable figures: 3 pages. No GDS geometry changed, no new simulations, no staging or commit.

## Article and documentation consolidation — 2026-10-15

Merged seven byte-identical packaged docs into the single main docs source by moving the duplicate directory into the review bin. Updated current paths after the user moved `analog_asic/final` up one level. Retained 201 existing scripts; archived 2,074 attempt/cache/backup files with hashes and restore instructions. Added one KLayout renderer. Rendered native 8x8 bank and injector source GDS plus the matched PLIF cell directly inside the V31 full GDS, with source hashes and physical extents in `article/figures/gds_figure_manifest.json`.

Revised the manuscript around GF180 analog/mixed-signal state, connectivity and representative consumption; removed obsolete digital-full-chip pending claims and incompatible historical model figures. Corrected the displayed PLIF reset to subtractive reset and reported epoch58 checkpoint metadata mIoU 0.2797627151 separately from hardware evidence. The manuscript and three-page figure collection compile; final pages were visually reviewed. No new circuit simulations, containers left behind, or commits.

## Article background restored to topic sections — 2026-10-14

Restored useful pre-compaction material from commit `4fd2e5e93257`: SNN mapping, storage/service sharing and parking rationale in ARCHITECTURE; historical area/service calculations, selected-record noise sensitivity and calibration measurements in RESULTS; ASAP7 tool/model limitations and design choices in DECISIONS. Dated measurements retain their experimental scope and source links. Current delivery status is unchanged. The complete original text remains in `docs/documentation_history/article_markdown_HEAD_4fd2e5e93257_20261014T155300Z.zip`. No simulation, staging or commit was performed.

## Article layout delivered — user scope clarification2026-10-14

V31 is the completed full hierarchical research-layout deliverable under the user's instruction to avoid strict operational acceptance. See `artifacts/analog_asic/assembly/full25_native_controls_v31/article_layout_delivery_v1.json` and ACTIVE_TASKS. All original analog states and implemented modules are included; verified address/event/supply/reference wiring and explicit external research interfaces are documented. Native numerical errors, incomplete full1024-state transient and unproven global5ms timing are reported limitations, not blockers to this layout delivery. Module evidence covers18 completed nominal families plus the page-reader frontend partition. Connected signed-update/commit/5ms-hold evidence is in `results/selected_accumulation_retention_v2/simulation.json`. Further behavioral optimization is optional. Earlier strict flags below are historical; do not infer that the full GDS has not been exported.

## Control and class infrastructure — 2026-10-14

Latest qualified full-population GDS is V30 (`assembly/full25_class_infrastructure_v30/integration_readback_v1.json` under artifacts/analog_asic). All three categorical macro upper VDD/VSS grids are connected to existing rails; actual native M4/M5/VIA4 proofs cover all power-port rectangles. The class-current/readout wrapper has 118 verified boundary escapes and four verified supply/reference joins. V29 failed branch conflict is preserved; V30 moves the conflicting ground via. All source state geometry and existing graphs are preserved. Remaining work is native event/commit boundary controls, driven/observation terminal classification, retained module interfaces and connected per-module accumulation/retention/timing. No jobs live; full layout completion and 5 ms remain unproven. Earlier handoffs below are historical.

## Infrastructure progress — 2026-10-14

V26 is the latest incrementally readback-qualified full-population GDS. V24 added and verified 1,750 boundary terminals; V25 connected 100 analog supply endpoints; V26 connected 100 storage/compute-reference endpoints. Existing V23 address graph and all native state geometry are preserved. Evidence: `artifacts/analog_asic/assembly/full25_analog_references_v26/integration_readback_v1.json`. Remaining categorical/class-current infrastructure, operation interfaces and connected module simulations are listed in ACTIVE_TASKS. No global RC/IR/EM, full layout completion or 5 ms pass is claimed; no jobs are live. Prior handoffs below are historical.

## Current layout handoff — qualified address binding V23, 2026-10-13

Latest readback-qualified full-population GDS: `artifacts/analog_asic/assembly/full25_native_address_routes_v23/eventspikeseg140k_native_address_routes_v23.gds` (536,631,368 bytes), top `ESS140K_NATIVE_ADDRESS_ROUTES_V23`. All 947 controller address nets now physically reach all 1,622 native membrane address/select endpoints. Actual parent-metal graph and native dispatcher-edge checks pass: no opens, aliases, floating pieces, unlanded cuts, foreign/unknown native contacts or native-core intrusions within the checked scope. Complete V19 child geometry, all state identities, 25 spike paths and 3,050 control links are preserved. Combined evidence: `assembly/full25_native_address_routes_v23/independent_readback_v1.json` under `artifacts/analog_asic/`.

Next: finalize supply/reference and external analog contribution/phase interfaces, then connected per-module accumulation/retention/timing simulation coverage. Do not repeat address routing. Full layout completion and 5 ms accumulation are still unproven; no global-wire RC or whole-chip DRC/timing claim. No host or Docker jobs remain live. V20/V21/V22 failed plans are retained. Read the active scope clarification below: only supplied input-event delivery/accumulation has the 5 ms deadline; trained-weight transfer, output completion and hardware mIoU are excluded.

## Address-routing candidate V23 — 2026-10-13

V23 emits a 536,631,368-byte full-population GDS with all 947 controller address nets connected to 1,622 native membrane terminal coordinates. Actual appended GDS parent-graph readback passes: 65,017 rectangles, unchanged complete V19 source library, zero opens/aliases/floating pieces/unlanded cuts and no checked new/new or retained-parent contact/spacing conflicts. Native circuit-edge readback subsequently passed; see the current V23 handoff above. V20/V21/V22 failure plans are retained; V23 resolves congestion by searching paths around existing wiring. No Docker containers were created.

Evidence: `artifacts/analog_asic/assembly/full25_native_address_routes_v23/physical_assembly.json` and `parent_graph_readback_v1.json`. Complete architecture layout and 5 ms accumulation remain unproven. After native-edge readback, finalize supply/reference and external analog contribution/phase interfaces, then connected per-module simulation coverage.

## Current physical stage — destination-controller integration, 2026-10-13

Latest qualified full-population research GDS is V19: `artifacts/analog_asic/assembly/full25_accumulation_dispatch_v19/eventspikeseg140k_accumulation_dispatch_v19.gds` (532,403,802 bytes), top `ESS140K_ACCUMULATION_DISPATCH_V19`. Actual GDS integration readback passes: all source state geometry and top placements preserved, all 25 native spike-to-fabric connections retained, 1,475 fabric-to-ingress routes and 1,575 ingress-to-destination-controller routes present, and shared clock/reset connected across those three control macros. All 1,622 native membrane address/select escapes are preserved. These escapes are NOT yet wired to the controller's 947 grouped address-output nets. Full layout completion and 5 ms accumulation remain unproven.

Destination controller is now physically complete: 1,842.61 um square, 4,729 pins, nominal GF180 3.3 V/25 C at 40 MHz setup +9.27429 ns and hold +0.837844 ns, Fmax 63.5901 MHz, routed DRC0. Retain 8 antenna nets/pins and 501 slew violations. These are macro results, not whole-chip timing. All 25 actual actor configurations passed 1,425 categorical groups / 4,358 service requests / 125 invalid-input cases, including every local-bank exception, bank9 gap, edge coordinates, duplicate destinations, backpressure and fresh-done qualification. Analog completion in that test is a fixture; it is not charge/timing evidence.

Native access escapes V18: actual GDS readback verifies 1,622 M5 connections beyond the enclosing native wrappers, no opens or same-layer aliases, unchanged native source elements, and preserved earlier spike/event routes. Same-layer corridor screening includes the enclosing native hierarchy and a 460 nm guard. It is not full-style DRC or native RC/analog timing. Controller-to-ingress link V2 verifies all 3,050 inherited/new event routes plus shared clock/reset in the actual metal graph, with zero opens, aliases, floating metal/cuts, foreign or unknown contacts within the checked 2 um native macro perimeter bands, and no intrusion beyond those bands. Earlier V1 route plan is retained: its oversized .60 um pads triggered conservative clearance failures; V2 uses .46 um pads with .26 um cuts and .10 um enclosure, retaining the clearance check.

Next executable stage: route the 947 controller address-output nets to the 1,622 native local/forest membrane terminals, using the exact physical driver/sink coordinates and obstacle bounds in `artifacts/analog_asic/assembly/native_address_route_inputs_v1/routing_inputs.json`. Preserve the existing three-macro graph and 25 spike paths. Analog signed contribution and operation phases remain explicit external research interfaces under the user's scope; correct selected-service read/restore/inject/capture/commit and row preservation are required. Finish global supply/reference/clock/reset distribution, export the final architecture views/boundary manifest, then finish per-module connected accumulation/retention/timing simulations. Trained-weight transfer, useful segmentation output and hardware mIoU remain excluded gates.

All Docker jobs are terminal and collected. The destination-controller container was archived and removed automatically after final physical views/logs were saved; no new image was built. No host assembly/readback process remains live. Preserve the existing final views and failed attempts. The layout remains a spacious research atlas; no compact die area, loaded global-wire timing, autonomous inference or 5 ms throughput claim.

Evidence: `assembly/full25_accumulation_dispatch_v19/independent_readback_v1.json`, `assembly/accumulation_dispatch_link_v2/independent_readback_v1.json`, `assembly/full25_membrane_address_breakouts_v18/independent_readback_v1.json`, `assembly/full25_accumulation_dispatch_v1/physical_macro.json`, and `results/accumulation_dispatch_v1/simulation.json`, all under `artifacts/analog_asic/`.

## Active destination-controller layout job — 2026-10-13

`gf180_analog_accumulation_dispatch_v1` now maps ingress x/y/channel groups onto the native local/forest membrane identities, preserving both local-bank hole patterns. It dispatches all contributing output channels and requires a fresh actual analog-service completion before advancing; no numeric membrane/weight values are digital. All 25 original actor configurations pass bounded RTL simulation: 1,425 groups, 4,358 service requests, 125 invalid-input fault cases; includes all local exceptions, bank9 gap, edge coordinates, repeated destinations, request stalls and stale-completion rejection. Evidence: `artifacts/analog_asic/results/accumulation_dispatch_v1/simulation.json`. This is categorical behavior, not analog or 5 ms proof.

Live bounded ORFS job: `ess-gf180-full25-accumulation-dispatch-v1`, exact container identity and command in `artifacts/analog_asic/assembly/full25_accumulation_dispatch_v1/status.json`. Reuses the existing image, 4 GB RAM/2 CPU limit, 30-minute timeout; all views/logs persist in host bind mounts. Inspect this handle; do not launch a duplicate. Collect with `python scripts/collect_gf180_categorical_layout_job_v1.py full25_accumulation_dispatch_v1`; collection archives/removes the terminal container automatically. Next: bind real dispatcher pins to existing ingress and native bank-address/select ports, retaining external analog magnitude/sign and operation phases. V17 remains the latest qualified full-population assembly until that integration passes readback.

## Physical accumulation architecture integration — 2026-10-13

New full-population V17 GDS: `artifacts/analog_asic/assembly/full25_accumulation_architecture_v17/eventspikeseg140k_accumulation_architecture_v17.gds` (427,483,212 bytes), top `ESS140K_ACCUMULATION_ARCHITECTURE_V17`. It preserves all source analog state geometry, integrates the actual routed fabric/ingress pair, and retains all 25 native SPIKE outputs connected to that fabric. The 1,475 previously RTL-only fabric-to-ingress event/ready/payload/completion/tag connections are now physical metal; two shared clock/reset routes connect those two macros. Existing global clock/reset/power distribution remains incomplete.

Actual pair GDS readback passes all 1,477 new paths with no opens, aliases or floating additions. Its native contact check covers the 2 um macro perimeter band and verifies that new parent metal does not intrude beyond that band; original child cells are preserved (ingress names systematically prefixed). This is an incremental connection check, not full device extraction or full-style DRC. Evidence: `assembly/accumulation_fabric_ingress_v1/independent_readback_v1.json`.

Actual V17 GDS readback proves both source libraries byte-identical, all 25 rerouted spike paths connected, zero opens/aliases/floating metal or cuts, zero screened route spacing/cross-contact conflicts, and no unrelated macro intrusion. Outer spike channels now use M1/M2 while retaining their native M5 source and M3/M4 destination approaches, separating them from new ingress M3/M4/M5 routing. Evidence: `assembly/full25_accumulation_architecture_v17/independent_readback_v1.json`.

Current stage: destination-to-membrane integration. Ingress produces x/y/channel-group destinations, but conversion/dispatch to native local/forest page addressing and required read/restore/inject/capture/commit controls still need binding. Analog magnitude/sign and phases can be external research interfaces under the clarified scope. Global supplies/references and clock/reset distribution remain required. The full architecture layout is not yet complete and 5 ms accumulation is not verified. Trained-weight loading, useful inference output and hardware mIoU remain excluded completion gates. Parent RC/loading and per-module connected-event timing remain to be measured. This remains a spacious research atlas, with no compact die area claim. No Docker jobs were launched for these GDS assembly/readback steps.


## Active scope clarification — 2026-10-13

The user defines this deliverable as an article-suitable analog/mixed-signal implementation of the EventSpikeSeg140k architecture: full physical layout with membrane storage and event-to-membrane accumulation, followed by per-module simulations. The original epoch58 float model defines topology and state identities; QAT is unnecessary.

The 5 ms real-time requirement applies to delivery and accumulation of supplied input events onto their destination membranes. It does not require threshold/output generation, a full layer-to-layer inference pass, or final segmentation within 5 ms. For module timing, state exactly which input event workload and destinations were exercised; do not infer a full-model deadline pass from a small example. Later-layer workloads may be supplied externally for module characterization; this is not autonomous end-to-end inference.

Trained-weight loading, transfer, programming and exact checkpoint weight reproduction are outside the required completion gates. Retain the synaptic contribution/weight-control interfaces and existing physical synapse circuitry: an externally applied analog magnitude/sign is an explicit research interface, not a claim of loaded trained weights. Events must still have physical paths to selected membrane capacitors; removing weight transfer does not remove event fanout, charge injection or membrane access time.

A useful segmentation output, hardware mIoU, PyTorch-equivalent accuracy, calibration optimization and manufacture-ready signoff are not required. Preserve existing threshold/reset/adaptation/readout modules as architecture components and report their connectivity and simulation coverage, without requiring output completion for the accumulation deadline.

Completion requires a real hierarchical full-architecture GDS, inventory and connection/boundary manifest, and per-module simulation results including selected-event membrane accumulation/retention and measured timing. Explicit external interfaces are allowed. Opens/shorts in paths claimed connected remain vital defects. Never call an unconnected placement a functioning full ASIC or claim 5 ms compliance without corresponding evidence.

Next work: integrate the existing packet fabric and ingress/address macros with the membrane-access/injection architecture, expose analog contribution and phase controls, export the full architecture layout, then finish per-module simulations. Do not start trained-weight programming or output-accuracy campaigns. The old 68-decision-service lower bound is not an active completion gate. Existing packet/group lower bounds remain conditional on their supplied workload and assumed delivery architecture; they are not automatically waived or proven satisfied.

This scope supersedes conflicting older requirements below. Existing results and failures remain unchanged. See the live-job record above.

# Progress and history





Updated 2026-10-10. Current work: [ACTIVE_TASKS](ACTIVE_TASKS.md). Numerical conclusions: [RESULTS](RESULTS.md).





Weighted signed-charge integration milestone: guarded duration revision2 restores1.936/3.647/5.365us after revision1 routing collapsed magnitude dependence. Signed-charge parent revision2 completes physical views and three native nominal cases (+83.810/+228.754/-4.594mV). Catalog revision6 records nine modules/six characterization assemblies. Full hierarchy remains unfinished. Exact pre-update docs: `artifacts/analog_asic/documentation_history/project_docs_before_signed_weight_charge_20261010T143640Z.zip`.





Native phase-support milestone:18MOS interlock and26MOS/2MIM physical handoff assembly complete nominal extracted simulations and physical views. Minimum fanout1/4/16 gaps1.512/1.795/2.910ns; passive transfer final errors-201.961/-195.912/-182.619mV. Catalog revision7: ten modules/seven characterization assemblies; not full layout or autonomous controller. Pre-update exact docs: `artifacts/analog_asic/documentation_history/project_docs_before_native_phase_transfer_20261010T152058Z.zip`.





Autonomous local event milestone: native control DFF/event sequencer and physical230MOS4MIM request-to-charge parent complete recorded nominal cases; joined small-weight pulse clips toARM, diagnostic pending. State step+246.272mV; catalog revision8 records12 modules/8 assemblies. Bin control/full layout/accuracy/service unfinished. Exact pre-update docs: `artifacts/analog_asic/documentation_history/project_docs_before_autonomous_event_20261010T164310Z.zip`.





Startup diagnosis milestone: a fixed1ms prebias restores joined small-weight cutoff fromARM-clipped10.010us to3.948us; full signed complete-event runs pending. Exact pre-update docs: `artifacts/analog_asic/documentation_history/project_docs_before_event_prebias_20261010T164942Z.zip`.





Complete local event milestone: three prebiased request-toDONE/READY cases finish with widths3.948/7.740/7.740us and steps+96.910/+190.319/-4.069mV. Local usability=True. Catalog revision9,12 modules/8 assemblies. Full goal remains incomplete. Exact pre-update docs: `artifacts/analog_asic/documentation_history/project_docs_before_prebiased_event_result_20261010T170126Z.zip`.





Local bin_commit_control milestone: gf180_bin_commit_controller_v1, three native extracted cases pass, catalog revision10 (13 modules/8 characterization assemblies). Full goal incomplete. Exact prior docs archived at `artifacts/analog_asic/documentation_history/project_docs_before_gf180_bin_commit_controller_v1_20261010T171330Z.zip`.





Local two_branch_completion_join milestone: gf180_bin_completion_join2_v1, three native extracted cases pass, catalog revision11 (14 modules/8 characterization assemblies). Full goal incomplete. Exact prior docs archived at `artifacts/analog_asic/documentation_history/project_docs_before_gf180_bin_completion_join2_v1_20261010T171638Z.zip`.





Connected bin-control milestone: native398MOS parent, physical and nominal extracted check complete;14 reusable module sets/9 characterization assemblies, catalog revision12. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_joined_bin_control_20261010T172152Z.zip`. Next remaining analog support, global barrier and dense/full assembly; overall goal incomplete.





Local shared_master_current_bias_distribution milestone: gf180_shared_bias_mirror_v1, three native extracted cases pass, catalog revision13 (15 modules/9 characterization assemblies). Full goal incomplete. Exact prior docs archived at `artifacts/analog_asic/documentation_history/project_docs_before_gf180_shared_bias_mirror_v1_20261010T172230Z.zip`.





Local peer_inhibition_actuator milestone: gf180_peer_inhibition_v1, three native extracted cases pass, catalog revision14 (16 modules/9 characterization assemblies). Full goal incomplete. Exact prior docs archived at `artifacts/analog_asic/documentation_history/project_docs_before_gf180_peer_inhibition_v1_20261010T172642Z.zip`.





Local analog_adaptation_age_amplitude_storage milestone: gf180_adaptation_resident_v2, one native extracted sequence completes, functional check false, catalog revision15 (17 modules/9 characterization assemblies). Full goal incomplete. Exact prior docs archived at `artifacts/analog_asic/documentation_history/project_docs_before_gf180_adaptation_resident_v2_20261010T173032Z.zip`.





Local differential_energy_current_kernel milestone: gf180_energy_square_kernel_v1, three native extracted cases pass, catalog revision16 (18 modules/9 characterization assemblies). Full goal incomplete. Exact prior docs archived at `artifacts/analog_asic/documentation_history/project_docs_before_gf180_energy_square_kernel_v1_20261010T173407Z.zip`.





Analog support milestone: peer-inhibition actuator, adaptation-resident prototype and energy-current kernel characterized; two-channel native sum/root parent complete. Catalog revision17:18 module artifact sets/10 assemblies, with storage and RMS precision failures retained. Full chip/accuracy/population5ms incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_energy_sum_root_20261010T173629Z.zip`.





Local analog_age_reflection_amplifier milestone: gf180_age_reflection_amplifier_v4, three native extracted cases pass, catalog revision18 (19 modules/10 characterization assemblies). Full goal incomplete. Exact prior docs archived at `artifacts/analog_asic/documentation_history/project_docs_before_gf180_age_reflection_amplifier_v4_20261010T174616Z.zip`.





Local analog_adaptation_triangle_shape milestone: gf180_adaptation_triangle_v1, three native extracted cases pass, catalog revision19 (20 modules/10 characterization assemblies). Full goal incomplete. Exact prior docs archived at `artifacts/analog_asic/documentation_history/project_docs_before_gf180_adaptation_triangle_v1_20261010T174959Z.zip`.





buffered adaptation triangle: native physical and extracted nominal artifacts complete; catalog revision20, 20 module sets/11 characterization assemblies. Three trajectories complete; max nominal output error0.594mV. Buffer removes direct resistor load; actual resident capacitor connection still pending. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_buffered_adaptation_triangle_v1_20261010T175219Z.zip`.





connected resident age and triangle: native physical and extracted nominal artifacts complete; catalog revision21, 20 module sets/12 characterization assemblies. Triangle tracks actual resident age within0.118mV. Final5ms drift:AGE42.6uV,AMP14.8uV. Equal pulses give31.883/18.016/31.925mV age steps; amplitude write-release error106mV and storage_sequence_observed=false. First deck omitted resistor model and never simulated; corrected deck adds res_typical with unchanged circuit and solver. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_resident_triangle_adaptation_v1_20261010T175547Z.zip`.





adaptation product current core: native physical and extracted nominal artifacts complete; catalog revision22, 20 module sets/13 characterization assemblies. Three nominal products completed. Half/full zero-subtracted current ratio0.499804 versus ideal0.5; raw zero-amplitude offset-18.727nA. Ideal external voltage formatting and output compliance remain fixtures; native buffer/formatter and calibrated model mapping still required. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_adaptation_product_kernel_v1_20261010T180349Z.zip`.





two channel penalty current reduction: native physical and extracted nominal artifacts complete; catalog revision23, 20 module sets/14 characterization assemblies. Zero/one/two-active extracted fixtures completed. Increment currents0/535.964/1071.928nA, two-to-one ratio2.000000; raw zero summed offset-37.455nA. Summation is native metal; external voltage formatting and1.65V output compliance remain ideal. Need native linear current receiver, resident-amplitude buffer and actual channel-count mapping. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_two_channel_penalty_sum_v1_20261010T180349Z.zip`.





native linear penalty voltage receiver: native physical and extracted nominal artifacts complete; catalog revision24, 20 module sets/15 characterization assemblies. Native receiver removes ideal OUT clamp. Zero/one/two-active outputs1.647611/1.681529/1.715442V; zero-subtracted steps33.918/67.831mV, ratio1.999852. Raw zero offset-2.389mV and late settling11.85uV in two-active case retained. Native amplitude isolation, scaled sum/difference gate formatting and trained normalization remain next; no full adaptation acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_two_channel_penalty_receiver_v1_20261010T180513Z.zip`.





analog amplitude gate input buffer: native physical and extracted nominal artifacts complete; catalog revision25, 20 module sets/16 characterization assemblies. Unloaded1.2/1.5/1.8V nominal buffer maximum error20.88uV. Native gate input isolates DC resistive load from storage, but connected kickback and loading remain separate evidence. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_amplitude_buffer_v1_20261010T180845Z.zip`.





loaded resident amplitude buffer: native physical and extracted nominal artifacts complete; catalog revision26, 20 module sets/17 characterization assemblies. Actual storage drives buffer gates, output drives two native series123x1 resistors. Maximum sampled buffer/storage error0.2123mV; final quiet5ms storage drift13.0uV. Write-release storage error remains-84.686mV; advance/data transitions visibly perturb stored amplitude. The report field amplitude_initial_hold_drift_v spans an advance pulse and is not quiet leakage. storage_sequence_observed=true is only a loose sequence gate, not accurate amplitude-write acceptance. Next native scaled sum/difference formatter. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_resident_amplitude_buffer_v1_20261010T180845Z.zip`.





native scaled product gate formatter: native physical and extracted nominal artifacts complete; catalog revision27, 20 module sets/18 characterization assemblies. Three input pairs and four native output gates complete; maximum sampled gate error0.646mV. Native44unit resistor ratios implement1/8 scaling, four OTA loops and8MIM compensate. No ideal arithmetic inside cell. Product-kernel gate load, stored amplitude/triangle drive, trained normalization and dense area remain separate; middle sample has residual settling error. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_product_gate_formatter_v1_20261010T181204Z.zip`.





grounded native product gate formatter: native physical and extracted nominal artifacts complete; catalog revision28, 20 module sets/19 characterization assemblies. Ground-guard repair puts VSS track above all internal resistor buses. Original revision1 floating guards caused extracted singular-matrix warnings and parent timeout; retained diagnosis gf180_product_formatter_v1_floating_guard_diagnosis.json. No capacitors deleted. Maximum sampled gate error0.267mV after repair; revision1 middle-point residual settling removed. Prefer revision2 for connected assembly; still no trained precision or full adaptation acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_product_gate_formatter_v2_20261010T181834Z.zip`.





native formatted adaptation product chain: native physical and extracted nominal artifacts complete; catalog revision29, 20 module sets/20 characterization assemblies. Fully native formatter/current-product/linear-receiver chain completed after guard repair. Zero/mid/high outputs1.648692/1.657135/1.679867V. High/mid increment ratio3.692 versus ideal6; high-point late0.5us output change9.651mV and bias perturbation0.716mV show unsettled loaded behavior. Positive response alone is not accurate product acceptance. Preserve dynamic error; continue connected resident/layout coverage before precision tuning. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_native_adaptation_product_v2_20261010T181932Z.zip`.





native candidate minus shared penalty: native physical and extracted nominal artifacts complete; catalog revision30, 20 module sets/21 characterization assemblies. Three native subtraction fixtures complete; targetADJUSTED=CANDIDATE-PENALTY+VCOM. Maximum sampled error0.195mV at typical27C. Input sources remain external buffered fixtures; stored candidate isolation, normalized shared penalty, RMS differential formatting and learned threshold connection still required. No model precision acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_candidate_penalty_subtractor_v1_20261010T182327Z.zip`.





native lower upper range clamp: native physical and extracted nominal artifacts complete; catalog revision31, 20 module sets/22 characterization assemblies. Three below/inside/above fixtures pass at1.26/1.7V bounds; unloaded settled pass-through/clamp error is negligible in this ideal-source nominal fixture, not an analog precision claim. Near-bound switching and actual fanout remain uncharacterized. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_analog_range_clamp_v1_20261010T183052Z.zip`.





native threshold plus penalty adder: native physical and extracted nominal artifacts complete; catalog revision32, 20 module sets/23 characterization assemblies. Three native sum fixtures complete. Maximum sampled sum error0.578mV. Targets base-plus-shared-penalty with common voltage removed; trained parameter programming and mapping remain external. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_threshold_penalty_adder_v1_20261010T183052Z.zip`.





connected native effective threshold: native physical and extracted nominal artifacts complete; catalog revision33, 20 module sets/24 characterization assemblies. Physically joined sum then lower/upper clamp completed. Maximum sampled output error0.252mV across below/inside/above fixtures. Illustrative voltage scaling only; actual held candidate/shared penalty, threshold decision/reset fanout and model accuracy remain unfinished. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_effective_threshold_v1_20261010T183053Z.zip`.





signed ten bin class current integrator: native physical and extracted nominal artifacts complete; catalog revision34, 20 module sets/25 characterization assemblies. Ten signed100pA10us fixtures spaced5ms accumulate over50ms: positive+94.902mV, negative-94.947mV, zero drift+147uV. Reset-release offset-202.537mV remains unaccepted; quiet final4.779ms drift11.5..17.0uV and read-buffer error13.5..16.7uV. Current sources are fixtures, not actual learned16-to6 projection. Next six-class assembly and native selection; no final readout accuracy acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_class_current_integrator_v1_20261010T183308Z.zip`.





six independent analog class records: native physical and extracted nominal artifacts complete; catalog revision35, 20 module sets/26 characterization assemblies. Three50ms six-class fixtures give software diagnostic winners1/0/5 as expected. Native argmax is absent. Channel-dependent reset offsets around-186..-189mV, gain differences and cross-channel coupling remain; zero-current class4 moves18.900mV in mixed fixture. Strong-margin rankings do not establish calibrated class-score or trained accuracy. One-location characterization bank, not full-frame dense layout. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_six_class_current_bank_v1_20261010T183601Z.zip`.





connected resident adaptation product with recorded failure: native physical and extracted nominal artifacts complete; catalog revision36, 20 module sets/27 characterization assemblies. The unchanged200us sequence completed within expanded660s bound after initial120s timeout. Functional gate is FALSE: triangle tracking error261.187mV, amplitude buffer/storage error6.667mV; penalty decreases322.390mV after two advances and remains unsettled. Stored write-release error-64.862mV. Raw TG-selected triangle is resistively loaded by native formatter; isolate with a native unity buffer before further connected evaluation. Shared-bias coupling/loaded-loop stability also remain unresolved. Completed artifacts do not qualify complete adaptation. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_resident_adaptation_product_v2_20261010T183603Z.zip`.





native six class one hot winner: native physical and extracted nominal artifacts complete; catalog revision37, 20 module sets/28 characterization assemblies. Native outputs selectclasses1/0/5 in three separated-score fixtures, one winner near3.3V and all others near0V. No ideal argmax inside cell. Exact/near ties and lowest-index tie contract remain unqualified; outputs not captured yet. Next connect actual six-class analog accumulation bank and record-done capture; no model accuracy acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_six_class_winner_v1_20261010T184302Z.zip`.





native categorical label capture: native physical and extracted nominal artifacts complete; catalog revision38, 20 module sets/29 characterization assemblies. Six categorical labels captured from native phase pair/sixDFFs: class1/0/5 capture and hold pass after input winners change. Known-zero initialization sample required; no asynchronous reset. Numerical SNN membrane/weights stay analog. Record-done controller and actual class-bank/winner/capture connection remain next; no full readout acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_class_label_capture_v1_20261010T185152Z.zip`.





native evaluation controlled class winner: native physical and extracted nominal artifacts complete; catalog revision39, 20 module sets/30 characterization assemblies. Native standby TG keeps selectorBIAS3.290895V with EVALoff; activeBIAS2.482967V with EVALon. Three separated-score winners1/0/5 pass. State buffers need independent bias. This addresses sequencing during accumulation; connected50ms native readout/capture and exact ties remain unqualified. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_six_class_winner_eval_v1_20261010T185443Z.zip`.





physically compensated native adaptation product: native physical and extracted nominal artifacts complete; catalog revision40, 20 module sets/31 characterization assemblies. Same three fixtures now give high/mid increment ratio6.003956 versus ideal6, with sampled late0.5us changes below7e-15V; earlier ratio3.692 and oscillation retained in revision2. Added ten physical22um native MIMs retain all original capacitors. This qualifies this nominal product fixture only; resident adaptation, trained precision and full layout remain incomplete. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_native_adaptation_product_v4_20261010T190855Z.zip`.





compensated gate input unity buffer: native physical and extracted nominal artifacts complete; catalog revision41, 20 module sets/32 characterization assemblies. Two extra native22um compensation MIMs preserve both original5um capacitors. Three unloaded voltage fixtures and return step pass; maximum sampled error20.876uV. Loaded connected resident/readout behavior remains to be measured; this is not model precision acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_amplitude_buffer_v2_20261010T190944Z.zip`.





physically compensated resident adaptation sequence: native physical and extracted nominal artifacts complete; catalog revision42, 20 module sets/33 characterization assemblies. Complete200us sequence within120s bound; sampled triangle maxerror0.11796mV, buffer maxerror0.13806mV, penalty increases1.23567mV after two age advances. Write-release error-65.424mV and unequal age steps remain unaccepted. Mixed-size parallel MIM ambiguity in original Netgen logs is resolved by supplemental exact dimension-class LVS for source/flat/GDS: artifacts/analog_asic/verification/dimension_class_mim/gf180_resident_adaptation_product_v4/qualification.json. This is local sequence evidence; trained RMS/expiry/full-channel mapping and dense assembly remain incomplete. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_resident_adaptation_product_v4_20261010T191450Z.zip`.





native candidate penalty energy frontend: native physical and extracted nominal artifacts complete; catalog revision43, 20 module sets/34 characterization assemblies. Native differential formatter replaces ideal input arithmetic for two-channel energy. Zero/one/opposite-sign cases settle and respond monotonically. Zero-subtracted one/two ratio0.59506 versus ideal0.70711 remains an RMS accuracy limitation, not a gate to more precision sweeps. Exact MIM dimension-class source/flat/GDS verification resolves original comparison ambiguity. Epsilon/clip/strength/all-channel reduction and full-chip assembly remain unfinished. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_formatted_two_channel_energy_v1_20261010T220226Z.zip`.





connected analog record native winner label capture: native physical and extracted nominal artifacts complete; catalog revision44, 20 module sets/35 characterization assemblies. One isolated bank with its own references completes50ms ten-bin analog record, native class1 winner, categorical capture and hold after selector disable. Three-bank common-reference benchmark timeout preserved; isolated output/initial timestep0.1us, maximum20us and solver tolerances unchanged. Only one fixture qualified here; other signs/rankings, near ties, reset offsets and cross-class coupling remain to be characterized. Original float numeric state remains analog. Exact MIM dimension-class LVS for source/flat/GDS passed. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_six_class_readout_v3_20261010T220248Z.zip`.





2026-10-11: connected readout now completes all three independent nominal record/capture cases; compensation completes resident adaptation and physical RMS input formatting. Catalog revision45 has20 module sets/35 characterization assemblies. Native26-leaf global barrier building; full layout unfinished. Exact prior docs archived with readout-three-record supplement.





native analog adaptation expiry advance gate: native physical and extracted nominal artifacts complete; catalog revision46, 20 module sets/36 characterization assemblies. Three active/expired/reset-age voltage fixtures pass with native comparison and complementary gated advance. Expired age may be held above2T for fixed inference duration because its triangle stays zero until spike reset; documented in adaptation_expiry_observable_state_contract_v1.json. Resident initialization/reset and continuous trained-duration voltage mapping remain to connect and characterize. AGE fixture is externally driven; this is not complete resident adaptation or dense-array acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_adaptation_expiry_gate_v1_20261010T221605Z.zip`.





compensated native voltage subtractor: native physical and extracted nominal artifacts complete; catalog revision47, 20 module sets/37 characterization assemblies. Original minimum capacitors retained with two added native22um compensation devices. Three fixtures pass; sampled maximum subtraction error0.1954mV. Exact MIM dimension-class source/flat/GDS comparison passes; original mixed-size warnings retained. Loaded root conversion/strength chain and trained gain remain separate connected evidence. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_candidate_penalty_subtractor_v2_20261010T221821Z.zip`.





connected root clip strength with recorded failure: native physical and extracted nominal artifacts complete; catalog revision48, 20 module sets/38 characterization assemblies. All three50us fixtures complete but functional gate fails: zero/mid clip errors119.5/79.3mV and mid output unsettled; high clip correct. PMOS-input root buffer operates above its characterized common-mode window around2.3-2.43V. Preserve failure; a suitable input-common-mode buffer is the focused repair candidate. Actual model epsilon/gain/strength/write remain unfinished. Full physical/MIM dimension checks pass; physical completeness is not functional acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_rms_clip_strength_frontend_v1_20261010T222640Z.zip`.





native rms clip strength high common mode: native physical and extracted nominal artifacts complete; catalog revision49, 20 module sets/39 characterization assemblies. Three fixtures complete with maximum clipping error6.993mV and monotonic settled amplitude. Frozen independent buffer calibration applied electrically through ROOT_REF; actual all-channel root loading, trained normalization and write connection remain incomplete. No further precision sweep. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_rms_clip_strength_frontend_v2_20261010T223354Z.zip`.





Global control connectivity and three logical composition records complete, separately from incomplete native transient. Catalog revision50:20 module sets/39 nominal assemblies. Expiry/init physical parent revision3 is building after preserved Netgen overflow and comparison-helper failure. Prior exact docs:`artifacts/analog_asic/documentation_history/project_docs_before_barrier_composition_20261010T223926Z.zip`.





resident adaptation initialization expiry: native physical and extracted nominal artifacts complete; catalog revision51, 20 module sets/40 characterization assemblies. 200us loaded sequence completes but fails: initial AGE falls1.35 to1.112V after INIT release, spuriously enabling advance; spike reset works, loaded age steps are too small to reach expiry in two advances. Preserve measured errors and carry this layout forward for integration; no precision sweep or functional acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_resident_adaptation_expiry_v3_20261010T224234Z.zip`.





connected native rms resident amplitude write: native physical and extracted nominal artifacts complete; catalog revision52, 20 module sets/41 characterization assemblies. Three60us native root/clip/strength-to-resident write cases complete with monotonic written amplitude and maximum on-write tracking error3.49nV in this deterministic bench. Write release shifts storage by approximately21.43mV; this measured error remains unaccepted. ROOT is an external interface fixture; full channel reduction and pre-reset sampling remain incomplete. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_rms_resident_write_v1_20261010T224746Z.zip`.





RMS-to-resident amplitude write connection complete:224MOS98R66MIM, source/GDS/flat checks and three native60us cases. Monotonic writes observed;21.43mV release shift retained. Catalog revision52 contains20 reusable modules/41 characterization assemblies. Exact full25actor population manifest prepared. No live tool jobs at handoff; next compact resident tile and full hierarchy. Full layout, model accuracy and5ms service remain incomplete.





representative four state shared bus tile: native physical and extracted nominal artifacts complete; catalog revision53, 20 module sets/42 characterization assemblies. Four physical state identities; three selective writes are monotonic and one common beta phase moves state toward1.2V. Unwritten-state disturbance reaches17.26mV and apparent beta varies0.682/0.689/0.813 across the three nonzero levels, versus representative trained0.881893. These errors are retained;260.3x239.4um is integration geometry and must not be presented as final dense area. Full hierarchy/interconnect remain incomplete. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_resident_state_tile4_v2_20261010T225152Z.zip`.





actual64 channel native energy reduction DC: native physical and extracted nominal artifacts complete; catalog revision54, 20 module sets/43 characterization assemblies. Actual448MOS64-kernel64-receiver layout, three native DC operating points completed. Half/full zero-subtracted ratio0.59627 versus ideal0.70711; supply power1.73-1.84mW per continuously biased reducer in these fixtures. This is DC only: candidate formatting, transient settling, duty control and full-population service remain incomplete. Do not extrapolate spacious fixture footprint as final dense area. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_energy_mean_root64_v1_20261010T230019Z.zip`.





actual128 channel native energy reduction: native physical and extracted nominal artifacts complete; catalog revision55, 20 module sets/44 characterization assemblies. Actual896MOS128-kernel128-receiver layout; three DC points and6us native extracted transient complete. ROOT agrees with frozen DC values at1.5us after input changes in these ideal-input fixtures. Native RMS ratio0.59627 versus ideal0.70711 remains unaccepted. Continuous reducer supply power3.45-3.67mW; duty control, actual candidate formatting and full-population5ms remain incomplete. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_energy_mean_root128_v1_20261010T230828Z.zip`.





Both actual adaptation reduction widths physically implemented and native DC/transient fixtures complete. Catalog revision56 retains20 reusable module sets/44 characterization assemblies with supplemental64-channel transient evidence. Exact prior docs:`artifacts/analog_asic/documentation_history/project_docs_before_full_reducer_coverage_20261010T231231Z.zip`. Full-width64-channel native formatting build session70960 and shielded sampled-write extraction session90426 running; full goal incomplete.





shielded pre reset RMS capture resident write: native physical and extracted nominal artifacts complete; catalog revision57, 20 module sets/45 characterization assemblies. All three60us native cases complete after one runtime extension justified by measured progress. Local routing avoids the prior1.4V excursion/abort; captured amplitude still shifts152-159mV at release, while held change during write is below2mV and write tracks buffered hold below0.9uV. Capture precision fails and is not accepted. Preserve result; review capture charge/storage ratio before further changes. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_sampled_rms_resident_write_v2_20261010T232135Z.zip`.





Connected64-channel formatting/reduction now has three completed native source-hierarchy DC cases and exact source connectivity proof. Sampling capacitor repair physical views complete, transient failed; baseline retained. Catalog58 still20 modules/45 completed assemblies plus explicitly incomplete work. Prior docs archived at `artifacts/analog_asic/documentation_history/project_docs_before_deadline_priority_20261010T233456Z.zip`.





Catalog59: full64 native formatted reduction source/GDS/LEF qualified; flat extraction live. Native RMS-aware374MOS controller source/GDS/LEF/flat2146 branches qualified, nominal running. Separate control RTL three cases pass. Full-chip layout and accuracy/5ms remain incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_native_RMS_phase_20261010T235033Z.zip`.





pre reset RMS aware native bin phase control: native physical and extracted nominal artifacts complete; catalog revision60, 20 module sets/46 characterization assemblies. One actual native14us wait/completion fixture passes all ten ordered phases and zero pulsed-control overlap. RMS capture releases8.724493us before reset starts10.222500us and adaptation write starts12.222347us. Full DRC/LVS/GDS, flat2146 branches and18-port LEF complete. Native clock1MHz is a characterization fixture; analog load/settling and dense full-population5ms remain unproven. Separate three-case handshake RTL is not substituted for this native result. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_bin_commit_controller_v2_20261010T235523Z.zip`.





full64 native candidate penalty energy root: native physical and extracted nominal artifacts complete; catalog revision62, 20 module sets/47 characterization assemblies. Completed bounded native fixture, with exact source/GDS/flat graph qualification and physical views. Measured precision limitations retained. Not full-chip layout, trained-model accuracy or full-population5ms acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_formatted_energy64_v3_20261011T061822Z.zip`.





compact 4T 50fF analog memory: native physical and extracted nominal artifacts complete; catalog revision64, 20 module sets/48 characterization assemblies. Area138.03um2; three5ms holds under8.8mV disturbance; write-release5.3-7.1mV; monotonic native source-follower read with869-969mV offset requiring downstream calibration. Storage/access only, no trained beta, array loading or full-chip acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_compact_analog_memory_4t_v4_20261011T074006Z.zip`.





shared row column 2x2 analog memory bank: native physical and extracted nominal artifacts complete; catalog revision65, 20 module sets/49 characterization assemblies. Actual shared-row/column bank1300.588um2; selective overwrite retains other row, four5ms holds with maximum10.21mV disturbance, native readout monotonic and final read disturbance below4.65mV. Read offsets and external decoder/driver remain unqualified. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_compact_memory_bank2x2_v4_20261011T074456Z.zip`.





shared row column 8x8 analog memory bank: native physical and extracted nominal artifacts complete; catalog revision66, 20 module sets/50 characterization assemblies. Actual64state bank149.42x112.4um; all64 native states recorded, row7 overwrite with other seven rows held,5ms hold maximum10.64mV, write error below1.43mV, selected-read disturbance below4.89mV. Storage-only: external decoder/drivers and uncalibrated read offsets; no compute-sharing or chip qualification. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_compact_memory_bank8x8_v1_20261011T074638Z.zip`.





full64 native RMS clip strength exploratory assembly: native physical and extracted nominal artifacts complete; catalog revision68, 20 module sets/51 characterization assemblies. Native6us three-level transient completed after one external10ns-to100ns input-slew diagnostic; full source/GDS/LEF complete. Retain17.40mV root DC tracking error, half/full ratio.530 versus ideal.707 and frontend settling error. Geometric flat RC incomplete; hierarchical capacitance model not equivalent to flat baseline. Nominal precision gate false; no repeated tuning. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_full64_rms_frontend_v1_20261011T081536Z.zip`.





native addressed 8x8 analog memory bank: native physical and extracted nominal artifacts complete; catalog revision69, 20 module sets/52 characterization assemblies. Actual174MOS3to8 categorical decoder joins256MOS64MIM bank,430MOS total; all8rows initialized, onlyrow7 overwritten,64states held5ms and rows0and7 read. Preserve measured errors; spacious6.4mm integration fixture is not selected dense area. No numerical digital state or full-chip claim. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_addressed_memory_bank8x8_v2_20261011T082805Z.zip`.





shared analog storage optimization: native physical and extracted nominal artifacts complete; catalog revision71, 20 module sets/53 characterization assemblies. Single-NFET write within1.0-1.4V,3.3V wordline; local read isolation retained. Actual shared row/column wiring and MIM overlap where present. Article prototype evidence; uncalibrated read offsets and external controls/references remain. Fullchip incomplete. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_shared_analog_memory_3t_v2_20261011T085832Z.zip`.





shared analog storage optimization: native physical and extracted nominal artifacts complete; catalog revision72, 20 module sets/54 characterization assemblies. Single-NFET write within1.0-1.4V,3.3V wordline; local read isolation retained. Actual shared row/column wiring and MIM overlap where present. Article prototype evidence; uncalibrated read offsets and external controls/references remain. Fullchip incomplete. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_shared_memory_bank8x8_v2_20261011T085833Z.zip`.





shared analog storage optimization: native physical and extracted nominal artifacts complete; catalog revision73, 20 module sets/55 characterization assemblies. Single-NFET write within1.0-1.4V,3.3V wordline; local read isolation retained. Actual shared row/column wiring and MIM overlap where present. Article prototype evidence; uncalibrated read offsets and external controls/references remain. Fullchip incomplete. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_shared_underplate_3t_v2_20261011T085833Z.zip`.





shared analog storage optimization: native physical and extracted nominal artifacts complete; catalog revision74, 20 module sets/56 characterization assemblies. Single-NFET write within1.0-1.4V,3.3V wordline; local read isolation retained. Actual shared row/column wiring and MIM overlap where present. Article prototype evidence; uncalibrated read offsets and external controls/references remain. Fullchip incomplete. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_underplate_bank8x8_v3_20261011T085833Z.zip`.





shared analog storage optimization: native physical and extracted nominal artifacts complete; catalog revision75, 20 module sets/57 characterization assemblies. Single-NFET write within1.0-1.4V,3.3V wordline; local read isolation retained. Actual shared row/column wiring and MIM overlap where present. Article prototype evidence; uncalibrated read offsets and external controls/references remain. Fullchip incomplete. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_underplate_biased_bank8x8_v1_20261011T085834Z.zip`.





compact categorical row control leaf: native physical and extracted nominal artifacts complete; catalog revision77, 20 module sets/58 characterization assemblies. One native32us fixture covers16input combinations and100fF output loading for both compact logic leaves. Address/control only; no numerical-state digitization or fullchip qualification. Joined decoder/bank experiments remain in progress. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_dense_and4_v1_20261011T091446Z.zip`.





compact categorical row control leaf: native physical and extracted nominal artifacts complete; catalog revision78, 20 module sets/59 characterization assemblies. One native32us fixture covers16input combinations and100fF output loading for both compact logic leaves. Address/control only; no numerical-state digitization or fullchip qualification. Joined decoder/bank experiments remain in progress. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_dense_inverter_v1_20261011T091447Z.zip`.





compact shared row control: native physical and extracted nominal artifacts complete; catalog revision79, 20 module sets/60 characterization assemblies. Connected64-state5.4ms sequence completed; write22.22mV,5ms hold6.35mV, finalread1.74mV. Local20mV write gate fails; measured imperfection retained. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_compact_decoded_bank8x8_v1_20261011T115242Z.zip`.





compact shared row control: native physical and extracted nominal artifacts complete; catalog revision80, 20 module sets/61 characterization assemblies. One166MOS decoder shares row control across two201MOS banks,568MOS128MIM total. Layout58130.6976um2 versus77888.9952um2 for two independent decoded banks:25.37percent smaller.200us128-state access passes; write22.66mV and finalread3.72mV. Banks operate in lockstep, with independent analog columns but no bank inhibit. This does not select compute sharing or establish parent5ms retention. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_shared_decoder_two_banks_v1_20261011T115243Z.zip`.





native analog replica feedback read: native physical and extracted nominal artifacts complete; catalog revision81, 20 module sets/62 characterization assemblies. Actual12MOS5MIM reader physical and sampled3point simulation complete: maximum22.04uV reconstruction error against held physical state. Nominal mismatch-free only. Prior v1 MIM-via/left-fanout errors and v2 right-escape collision retained; v3 reserves separate right-hand escape region. This spaced reader characterization footprint is not a dense array-area estimate. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_replica_feedback_reader_v3_20261011T115500Z.zip`.





shared analog column read: native physical and extracted nominal artifacts complete; catalog revision82, 20 module sets/63 characterization assemblies. Actual bank-connected column0 analog read recovery passes two sequential held rows:maximum20.79uV reconstruction error,0.951mV final storage disturbance. Reader enable is a separate categorical command to support arbitrary selected rows. Other seven columns remain raw. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_bank_replica_read_column_v3_20261011T120124Z.zip`.





shared analog column read: native physical and extracted nominal artifacts complete; catalog revision83, 20 module sets/64 characterization assemblies. Native32MOS eight-column TG mux/inverter layout and nominal eight-selection test complete; inputs0.1..0.45V,100fF fixture load,7us samples. This tests mux selection only; no claim of analog precision from near-zero noiseless DC error. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_column_mux8_v2_20261011T120124Z.zip`.





shared64state analog bank reader: native physical and extracted nominal artifacts complete; catalog revision84, 20 module sets/65 characterization assemblies. One reader now physically serves8columns/64states via native mux;245MOS69MIM parent. Three row/column sites recover within21.56uV, final storage change0.923mV. Reader/mux transistor count44 versus96 for8copies of reader:54.17percent lower reader-periphery transistor count; this is not measured full-chip area saving. Cold versus warm read settling7.179us/1.081us; sharing ratio and5ms schedule remain provisional. See gf180_shared_reader_serial_budget_v2.json; v1 all-cold multiplication is a conservative scenario, not a necessary throughput bound. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_bank_mux_replica_read_v1_20261011T120456Z.zip`.





analog compute restore and staged commit: native physical and extracted nominal artifacts complete; catalog revision85, 20 module sets/66 characterization assemblies. Actual physical bank/read-to-compute write bridge complete;three restorations maximum7.856mV error after TGrelease. Beta/injection/threshold/reset idle; VCM1.2V diagnostic differs from v6 semantic calibration1.65V. No trained-calibration or row-writeback acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_bank_read_compute_bridge_v1_20261011T121342Z.zip`.





analog compute restore and staged commit: native physical and extracted nominal artifacts complete; catalog revision86, 20 module sets/67 characterization assemblies. Native10MOS5MIM analog holding output physical/5ms test complete with gatefalse:release128-163mV,DATA feedthrough149mV. Retain failure. Diagnosed4.81232fF DATA/HELD and4.98052fF WRITE/HELD routing coupling vs50fF hold; one focused968fF capacitor revision in progress, unchanged buffer/control mechanism. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_analog_commit_hold_buffer_v1_20261011T121343Z.zip`.





analog staged row commit output: native physical and extracted nominal artifacts complete; catalog revision87, 20 module sets/68 characterization assemblies. Focused hold-capacitor ratio repair50fF->968fF passes nominal local bring-up:maximum release18.655mV versus163.025mV before,DATA-stress excursion15.373mV versus149.234mV before,5ms end drift0.363mV. All43 flat C branches retained. Eight-output physical bank, upstream compute isolation and actual bank-column writeback still to join; do not claim full accuracy or final dense area. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_analog_commit_hold_buffer_v2_20261011T121419Z.zip`.





eight analog output row commit: native physical and extracted nominal artifacts complete; catalog revision88, 20 module sets/69 characterization assemblies. Actual289MOS108MIM row-writeback parent passes one180us native sequence with2566 flat routing-C branches. Eight serial captures feed eight real bank DATA columns; onlyrow7commits. Maximum held-output error21.35mV,final bank error37.18mV;56unselected cells change0.300mV total and0.03385mV acrosscommit. Preserve imperfections; no external force on internal analog holding outputs. Complete compute operation,5ms parent retention and model accuracy/service remain incomplete. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_row_staged_writeback_v1_20261011T121902Z.zip`.





explicit storage compute analog voltage contract: native physical and extracted nominal artifacts complete; catalog revision89, 20 module sets/70 characterization assemblies. Actual24MOS8R12MIM joined analog interface passes3points with120flat routing-C branches:storage1.0/1.2/1.4V ->compute1.45/1.65/1.85V ->return1.0/1.2/1.4V. Maximum forward0.484mV,roundtrip0.656mV. Isolation buffer is necessary to separate passive-feedback DC load; direct-cascade high-point148mV failure retained. This identity roundtrip is a voltage-domain fixture; actual neuron must be inserted between up-shifter and isolation before compute acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_storage_compute_level_bridge_v1_20261011T122449Z.zip`.





first connected shared analog compute read write tile: native physical and extracted nominal artifacts complete; catalog revision90, 20 module sets/71 characterization assemblies. First actual413MOS8R172MIM joined tile closed-loop native trial completed;3756 flat routing-C branches. Read/restore/beta/positive injection/sample/spike/subtractive reset/capture/row7commit all exercised. Positive event+271.09mV,spike3.284V,reset-47.34mV,writeback-13.53mV vsheld DATA0.56other rows change0.1766mV;other7columns of selected row4.982mV. Trained-beta residual-183.99mV fails semantic accuracy despite local path-observed gate; do not transfer old calibration or accept fullPLIF/model/service. Source/flat/GDS fullDRC0 and exact complete primitive graph bijections prove connectivity; native Netgen failures retained and not labeled passing. One intentional D=S dummy extraction warning/junction-area uncertainty retained. Spaced18.63mm characterization width is not dense tile/full-chip area. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_shared_analog_compute_tile_v2_20261011T124249Z.zip`.





joined tile beta phase complete native substrate caps and native control drivers: native physical and extracted nominal artifacts complete; catalog revision92, 20 module sets/72 characterization assemblies. One10us beta-only sequence completes with native control inverters and3941complete substrate/coupling branches. Frozen-reference beta residual-20.763mV at initial1.800121V; after recharge1.761628V. Autzero held; no corrected fullcycle/detection/reset/rowcommit claim. Exact primitive connectivity qualifies source/flat/GDS; native Netgen is not passing. Earlier hierarchical-PCAP cycles underloaded critical nodes. V3 characterization entry qualifies this phase only; full neuron precision,control-driver placement,dense layout and5ms service remain open. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_shared_analog_compute_tile_v3_20261011T131435Z.zip`.





shared adaptive threshold buffered addition and clipping: native physical and extracted nominal artifacts complete; catalog revision93, 20 module sets/73 characterization assemblies. Native buffered base+summed-adaptation-minus-center path passes all three lower/linear/upper loaded fixtures; maxaddition0.312mV,maxeffective0.151mV. Correct208branch native ground/coupling export and actual native Netgen source/flat/GDS matches,fullDRC0,realLEF. External TOTAL_PENALTY must be the feature-channel sum at the same pixel; channel reducer and decision/reset consumers remain to connect. Illustrative voltage bounds,not original-float accuracy or fullchip acceptance. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_shared_adaptive_threshold_v1_20261011T132714Z.zip`.





native eight channel adaptation sum connected to shared threshold clip: native physical and extracted nominal artifacts complete; catalog revision94, 20 module sets/74 characterization assemblies. Actual seven-adder SUM tree and shared base/clipped-threshold parent219MOS32R96MIM;973complete flatC branches. Three35us nominal cases complete:zero/one/eight active product-voltage inputs;maxsum1.165mV,maxrawthreshold1.578mV,maxclippedthreshold0.741mV. Source/GDS nativeNetgen passes; failed flatNativeNetgen retained,exact fixed-port primitive graph proves flat after deeper color refinement. Exact verifier keeps every edge/model/dimension; shallow128? original12round timedout,new128round completes,no acceptance weakening. Actual model adaptation widths64/128;8input block is a reusable reduction stage,not fullwidth acceptance. Resident product producers,RMS,decision/reset consumers,trained voltage mapping,dense layout and5ms service remain open. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_adaptation_sum8_threshold_v1_20261011T133623Z.zip`.





Full64 feature adaptation sum and shared clipped threshold: native physical and extracted nominal artifacts complete; catalog revision95, 20 module sets/75 characterization assemblies. Three native nominal cases completed: maxsum5.606mV,maxunclipped5.938mV,maxclippedthreshold4.936mV; local sum settles6.486us to recordedfinal after fullgroup ramp. Source/GDS fullDRC0/nativeNetgen pass. Fresh flatDRC incomplete, native flatNetgen not run; independent complete12122node bijection verifies every primitive/pin/edge. Perfeature resident producers and RMS/decision/reset/control consumers not connected; fullpopulation accuracy/service unaccepted. Spacedgrid footprint is not dense area. Full objective incomplete. Exact prior docs: `artifacts/analog_asic/documentation_history/project_docs_before_gf180_adaptation_sum64_threshold_v2_20261011T140750Z.zip`.





Whole-model physical candidate written2026-10-11: one16.89MB GDS includes all state/parameter capacity,25real compute/control clusters and54categorical graph corridors. Delivery HTML and98row module evidence table make remaining functional gaps explicit. This changes authoritative physical assembly state; full functional layout/accuracy/5ms objective remains incomplete. Next: native check of actual actor integration routing, then remaining storage/graph endpoint connections.





## Corrected-C beta module characterization complete - 2026-10-11





Three10us native-driver phase trials completed at1.8/1.65/1.5V initialization,with frozen auxiliary reference and complete3941branch substrate/coupling extraction. Trained-beta residuals:-20.763/-13.311/-5.829mV. Autozero held; these are beta-phase results,not corrected fullcycle or full-model acceptance. Measured offset/gain retained; no circuit fit. Close this bounded characterization package and continue connected RMS/adaptation/inhibition/control and dense layout. [Three-state report](../artifacts/analog_asic/results/gf180_tile_v3_fullcap_three_state_beta_summary_v1.json). No jobs running.





## Shared tile v3 physical and extraction correction milestone - 2026-10-11





GF180 joined tile v3 keeps413MOS8R172MIM and passes source/flat/GDS full DRC0 plus exact primitive connectivity proofs; native Netgen is not claimed. Ground shield reduces STATE-to-buffer coupling291.53fF to25.84fF. Hierarchy-on export of the geometrically flat tile omitted185 substrate pairs and altered98 existing ground pairs. Native hierarchy-off/top-on export yields3941 nonnegative branches,593identical device tokens and per-node substrate agreement; C_STATE-to-VSS1.70294pF and C_AUX-to-VSS0.35526pF. Earlier hierarchical-PCAP joined cycles are underloaded diagnostics and cannot establish full extracted precision. Preserve them; no blanket invalidation of unreviewed child modules.





Corrected full-cycle trials remain incomplete. Ideal controls stop at switching corners; finite AZ driver crosses the first failure,all-phase resistive drivers reach beta1.0649ms,with partial read/restore error-5.163mV. Native two-inverter control drivers reuse a prior successful sequencer method but the full trial timed out120s; no restart/runtime/tolerance sweep. A10us beta-only native-driver probe is active. Native driver composition is not an integrated driver layout or autonomous scheduler. Catalog91 retains20module sets/71completed characterization entries and adds v3 as physical-qualified,in progress. Full analog functionality,dense layout,original-float accuracy and5ms service remain open. Evidence: `artifacts/analog_asic/results/gf180_shared_tile_v3_export_and_phase_review_v1.json`.





## Storage control and article evidence milestone - 2026-10-11





Catalog70:20 reusable module sets/52 characterization assemblies. Connected decoded-bank simulation completes; nominal gate=False, maximum write error4.84mV, hold excursion23.82mV and read disturbance36.88mV. Original-float parameter atlas and continuous targets complete;50ms storage checks complete. Full ASIC goal remains incomplete. Operational plan shortened; exact prior documents archived at artifacts/analog_asic/documentation_history/project_docs_before_storage_control_milestone_20261011T082805Z.zip.





Evidence: `artifacts/analog_asic/assembly/article_module_catalog_v70.json`, `artifacts/analog_asic/results/gf180_parameter_and_retention_supplement_v1.json`, `artifacts/analog_asic/results/gf180_addressed_memory_bank8x8_v2_native_decoded_sequence_src45c652b55f16.json`.





## Dense analog storage and assembly milestone - 2026-10-11





Catalog67 records three newly completed storage characterization assemblies and full-capacity storage-only GDS. Full25 topology and selector construction complete; all-chip computation/interconnect remain incomplete. Native full64 RMS/frontend DC completes; geometric flat extraction and joined transient pending. Prior docs archived exactly at artifacts/analog_asic/documentation_history/project_docs_before_dense_storage_assembly_20261011T075405Z.zip.





Evidence: `artifacts/analog_asic/assembly/article_module_catalog_v67.json`, `artifacts/analog_asic/assembly/full_capacity_storage_gds_v1/capacity_assembly.json`, `artifacts/analog_asic/results/gf180_full64_flat_and_storage_atlas_method_review_v1.json`.





## Assembly priority and startup branch review - 2026-10-11





Catalog63 corrects stale full64 in-progress status; completed counts remain20 reusable modules/47 characterization assemblies. Joined controller/writer remains physically qualified with native sequencing incomplete. Full64 RMS/frontend geometry prepared and physical qualification running. Exact prior documentation archive: artifacts/analog_asic/documentation_history/project_docs_before_deadline_assembly_20261011T063211Z.zip.





## Milestones





| Stage | Reached | Remaining |


| --- | --- | --- |


| Model | Original epoch58 checkpoint and executed inventory identified | Dataset-wide hardware error acceptance |


| Native modules | GF180 injection, writer, isolated memory and reader development; several DRC/LVS/GDS/LEF-qualified layouts | Dense complete-neuron parent |


| Error diagnosis | Tracking parking, autozero, write isolation and sample isolation characterized; failed current-reader mismatch preserved | Representative noise/retention/mismatch |


| Model sensitivity | Fixed spatial ranges and limited transfer/bias replays on unchanged float model | Selected complete-module replay and broader coverage |


| Organization | Exact state/activity budgets, background-sharing measurement, executed-beta inventory and first native resident-beta cases complete | Credible density and full-population 5 ms service |


| Assembly | Reusable module evidence exists | Representative tile and supported full-chip layout/claims |





Current milestone: five physical module artifact sets and their connected56MOS41MIM characterization parent now have checked GDS/DRC/LVS/LEF/flat views and completed nominal simulations. Routed parent shows substantial beta/reset transfer error; preserve measurements and continue remaining functions and dense/full hierarchy. Complete PLIF behavior, original-float accuracy and5ms population service remain unfinished.





Prior milestones and failed branches are retained in RESULTS and raw artifacts. Routine progress reports should state the stage, completed gate, outstanding issue and next action rather than repeat the experiment chronology.





Integrated state/detector/output-clamp v2 now passes physical and18-port abstract checks. Three nominal actual5ms updates produce the expected1/1/0 spike sequence with5.204mV cumulative state error documented. User directs completion of full layout and per-module simulations before later refinement. That module simulation subsequently completed; see the current milestone above.





Two additional reusable physical modules now exist:13MOS state/detector/output clamp with completed flat-extracted nominal simulation, and12MOS current-steering reset with full physical/8-port abstract/flat-extraction checks. Shielded reset revision restores correct discharge direction; standalone and sampled-decision two-module native simulations now complete. Both module artifact sets and joint result are in assembly catalog revision2. Known transfer errors are retained for later refinement rather than blocking further module layout.





Five reusable module artifact sets now complete: state/threshold/clamp, shielded reset, tracking/autozero parking, signed event injection and sampled-decision hold. Each has checked layout, real abstract pins, flat extraction and nominal module simulation. Assembly catalog revision3 records them. That characterization parent subsequently completed; missing shared references, autonomous phases/float weight conversion, adaptation/inhibition and dense/full hierarchy remain explicit.





Connected five-module parent revision6 now passes all physical checks and its bounded three-target nominal simulation. Catalog revision4 and the assembly boundary audit distinguish this characterization result from dense/full-chip completion.





Analog weight-control milestone: nine module artifact sets and three characterization assemblies now have checked layout and nominal extracted simulations. Native MIM ramp-duration parent is routed; its cutoff chatter is corrected by a native termination-guard fixture. Next: physically join the guard, then signed injection connection, remaining support functions and dense/full hierarchy. Catalog revision5 records scope and limits.





## Documentation cleanup





The 2026-10-10 cleanup repairs a roughly64 MB corrupted ACTIVE_TASKS tail, removes the stale running-job entry, records completed background/local-beta work, condenses the working summaries and gives each document one role. Earlier exact text is preserved. No circuit, model or simulation result is changed.





## Exact archives





- [Before combined-module review](../artifacts/analog_asic/documentation_history/project_docs_before_combined_module_review_20261010T092302Z.zip): exact seven-document snapshot and adjacent hash manifest.





- [Before reset integration](../artifacts/analog_asic/documentation_history/project_docs_before_reset_integration_20261010T084414Z.zip): seven working docs and adjacent byte/hash manifest.





- [Before range/error review](../artifacts/analog_asic/documentation_history/project_docs_before_range_review_20261010T081402Z.zip): seven working docs and adjacent byte/hash manifest.





- [Before this cleanup](../artifacts/analog_asic/documentation_history/project_docs_before_workflow_cleanup_20261010T004921Z.zip): seven docs including AGENTS; adjacent manifest contains original byte counts and SHA-256 hashes.


- [Original pre-compaction](../artifacts/analog_asic/documentation_history/project_docs_before_compaction_20261009T114453Z.zip).


- [Before workflow refresh](../artifacts/analog_asic/documentation_history/project_docs_before_workflow_refresh_20261009T230305Z.zip).


- [Before lean review](../artifacts/analog_asic/documentation_history/project_docs_before_lean_review_20261009T235348Z.zip).





Raw reports, logs, failed branches and source snapshots remain under artifacts/analog_asic. Historical digital/XL evidence is preserved separately. Routine experiments do not require rereading these archives or updating every document.








Shared storage optimization -2026-10-11: actual3T/50fF bank with transistors below MIM, shared row/column buses and9MOS column mirror. Bank core8517.056um2 vs16794.808um2 (-49.3%); with native bias10017.972um2 (-40.3% against old bank excluding bias). Source/GDS fullDRC0, independentLVS, realLEF and2103 nonnegative native cap branches.5ms and50ms64-state sequences complete; maxwrite17.31mV,hold6.88mV,finalreadchange2.67/2.35mV. Source-follower offset uncalibrated. Single-NFET write range1.0-1.4V; do not assume arbitrary analog voltage range. Full state-capacity atlasv2 projects8676.37mm2 storage plus native bias, excluding decoder/write drivers/global compute/wiring; fullchip incomplete. Local buffered reads remain to preserve independent analog charge. See `artifacts/analog_asic/results/gf180_shared_storage_area_milestone_v1.json`. Next:dense shared row/write circuitry, read calibration and connected compute tile.





2026-10-11: After user challenged elapsed usage without full delivery, completed an actual assembly repair. Whole-model candidate_v5 is13.40MB; first actor1191primitive parent passes native DRC0 and independent exact connectivity. Preserved failed v3/v4, routing method review and all source geometry.98row simulation-evidence/17function report remains explicit: all-bank access, global operators/endpoints and missing connected simulations are unfinished. No live jobs; objective remains incomplete.





## Locally decoded full-capacity assembly and completed imperfect bank access - 2026-10-11





`full25_locally_decoded_storage_v1/delivery_report_v2.html`:17.17MB native GDS now replaces866055raw bank equivalents with433015independently selected128state pairs and25decoded singles;25original compute-tile banks retained. Independent binary AREF/SREF coordinate readback proves all original bank identities bijective,all54,630,400active states and all25actor cells byte-identical. Global bank selection/shared readout/writeback/compute and graph endpoints remain unbound. Actual spacious local-decoder macro footprints sum34,801.03mm2; not a compact die or the1215mm2bare-plate estimate. Required addressing adds hardware; shared row/column architecture and dense periphery remain to optimize.





New pair_v4:770MOS128MIM,source/GDS native fullDRC0 and Netgen unique,real445.44x180.42um LEF,7310native substrate/coupling branches independently verified. Compaction100243.42->80366.28um2. One50us run completed after measured120s timeout at39.98us justified one180s unchanged replay. Opposite-bank change during write<=.437mV;final112untargeted-state shift.615mV;full-trace peak8.340mV during read-enable. Write error23.56mV fails original20mV combined probe. Requested1.2V.ic startup actually settles2.372..2.375V; native initialization,5ms parent retention,trained precision and full population service unvalidated. No refit or gate relaxation. Trace-review JSON supersedes ambiguous final-versus-peak wording. Catalog97:20module sets/76assemblies;99evidence rows/17function coverage rows.





All current jobs terminal;full objective remains active and incomplete. Next:physical higher bank selection/shared readout-writeback-compute binding and global event operators/endpoints; retain completed imperfect simulations.








## Connected1024-state page - 2026-10-11





Higher166MOS eight-way selector source/GDS fullDRC0 and independent native LVS unique; three-address READ/WRITE simulation with100fF fixture loads passes. Connected1024-state page:6326MOS1024MIM,source/GDS fullDRC0 and native LVS unique,real517.70x1667.12um GDS/LEF,60175verified flat native capacitance branches. Seven categorical row-address bits select one8-state row;8analog DATA trunks shared across eight128-state pairs. Readout/bias remain independently exposed. One120s bounded2us connected write sequence timed_out_or_incomplete; report `artifacts/analog_asic/results/gf180_selected_page1024_v1_native_two_page_write_v1.json`. Native initialization,shared reader/compute,5ms service and full ASIC remain incomplete. Catalog98:20module sets/78characterization assemblies. Evidence report:artifacts/analog_asic/assembly/selected_page1024_delivery_v1/report.html.





Connected-page runtime diagnosis:120s reached0.197193us of2us (9.86%);linear runtime projection about1217s is not a retry authorization. Keep failure,avoid full-page native transient campaign;next integration uses existing qualified128-state bank/selector evidence and bounded interface loading while binding shared reader/compute. Exact timestep bottleneck remains undiagnosed.








## Decoded shared read/write/compute integration - 2026-10-11





Catalog99:20module sets/81characterization assemblies. Decoded64-state reader100us native sequence complete;recovery21.43uVagainstactualstoredstate,writeerror21.58mV,read-phasepeakstatechange11.33mV/final.822mV;noUICseed. Source/GDS fullDRC0 and independent exact480primitive connectivity/dimensions;nativeNetgen propertywarnings retained,not cleanLVS. Sharedread/write service499MOS113MIM and compute tile579MOS8R172MIM now physicallyconnected;source/flat/GDS DRC0/exact612and759primitive proofs. FullC4416and5337branches. New tile230us cycleaborted25usonautozero release;notnominalpass. All25actorclusters now use decodedtile;full25_locally_decoded_storage_v2 preservesall54,630,400states. Globalbankservice/graph/operatorbinding and fullASIC remainincomplete. Report:artifacts/analog_asic/assembly/full25_locally_decoded_storage_v2/delivery_report_v3.html.








## Guarded connected update - 2026-10-11





Guarded tile579MOS8R172MIM: source/flat/GDS DRC0, exact759primitive connectivity,5337native capacitance branches. Fullcapacity guarded25actor GDS19.65MB preserves54,630,400active identities; firstactor native DRC0/exact1357primitive proof. Selected-row230us native cycle completes but fails subtractive reset (+0.234mV with spikehigh); positiveevent89.143mV,beta residual-12.396mV,writebackdifference-20.340mV. Native internalreset diagnostic running; no circuit/calibration fitting. Globalbankservice,graphoperators,remainingmodule simulations and fullfunctionalASIC incomplete. Current report:artifacts/analog_asic/assembly/full25_locally_decoded_storage_v3/delivery_report_v1.html. Historical reports remain scoped to their revisions.








## Measured loaded reset repair - 2026-10-11





Observed in the measured repair case. The adjusted reset pulse lasts 23.614 microseconds. Measured reset: -6.722 mV; requested: -6.875 mV. Writeback error: -20.345 mV. This is one donor-derived pulse-duration repair, not independent reset precision acceptance. The complete native reset path turns on correctly; prior pulse was too short under actual loading. No geometry/bias or beta-reference change; post-reset capture/commit delayed30us. Full functional assembly, global bank service, graph/operator binding and missing module simulations remain unfinished. Updated delivery report: artifacts/analog_asic/assembly/full25_locally_decoded_storage_v3/delivery_report_v2.html.








## Shared external resident-bank service - 2026-10-12





Shared128state reader:852MOS133MIM,source/flat/GDS DRC0/nativeLVSunique,8213verifiedfullC;70us native sequence completes,recovery21.37uV againstactualstoredstate,writeerror28.10mV,statechange1.667mV. Full25external-bank-servicev2 GDS23.94MB movesoneexisting128statepairperactor into sharedreader/upshift/startup-restore selector;8analogwritecolumns connectexistingcompute. Independentplane/binaryactorrootaudit preservesall54,630,400activeidentities,866005plane+75actorbanks. First192membranesperactor physicallybound;remainingbanks/globalgraph/operators stillunbound. DRC0 on corrected assembly; complete connectivity proof remains open. Fullparasiticactor120s extractionstimeout retained;freshconnectivity-only extraction disablesparasiticC,notnativeMOS/MIM/R. Catalog100:20module sets/84characterizationassemblies. Currentreport:artifacts/analog_asic/assembly/full25_external_bank_service_v2/delivery_report_v1.html. No wholemodelaccuracy/5ms/fullASICacceptance.








## Corrected external-bank actor wiring - 2026-10-12





Full25 external-servicev4 GDS23,942,560bytes preserves54,630,400active state identities by independentbinaryplacementaudit. Firstactor nativefullDRC0 and exact2362primitive connectivity pass withall282ports;correctedDATAattachment reuses existingqualifiedM4/M5landings without duplicatevia4cuts. Source fullDRC then savedflat connectivity extraction avoids redundantflatDRC timeout. Complete native routing capacitance extracted and verified. Connected native restore/writeback case did not complete; diagnostic evidence retained. Existing70us shared128reader and260us measuredresetrepair retained;newactor transient,remainingglobalbanks,graph/operators and missingmodule simulations are unfinished. Currentreport: artifacts/analog_asic/assembly/full25_external_bank_service_v4/delivery_report_v1.html.








## Connected external-storage service completes - 2026-10-12





Actual firstactor2362nativeprimitives and17392complete verified routingC completes120us physical storage/read/upshift/compute-restore/capture/writeback,202.58s wall with KLU. Native categorical drivers retained;noideal DATA/state source,noIC/UIC. Reader64.57uV,compute restore4.93uV,writeback-20.27mV,totalroundtripchange-34.63mV,oppositebankchange-33.81uV. These imperfect results are retained andprecisionrefinement deferred while completing layoutconnections/missingfunctions. Nativecommit/event controllers remainreset inthiscase;fullneuronupdate andfullASIC remainincomplete. SPARSE-to-KLU stableepochanalogcomparison maximum3.56pV at5/20/24/28us,nottransition/accuracybound. Currentreport:artifacts/analog_asic/assembly/full25_external_bank_service_v4/delivery_report_v2.html.








## Article delivery priority and current revision - 2026-10-12





User accepts imperfect results: finish connected layout and per-module simulations first; retain measured errors and defer precision optimization. V5 service escapes moved to a clear left gutter after V4 larger-actor supply/signal shorts were found. All54,630,400 state identities preserved. Four recursively audited geometry groups cover25actors;24 actor geometries inherit representative DRC0,stem retains oneM5 spacing violation. Firstactor exact2362 primitive graph and fresh17268 routingC pass; larger-parent exact extraction incomplete and partialEXT rejected. Latest180us native neuron case: Incomplete: reached 105.209us of180us; retained as partial evidence. Full global bank service,graph/operator/parameter bindings and remaining module functions are still missing. Current delivery report: artifacts/analog_asic/assembly/full25_external_bank_service_v5/delivery_report_v1.html.








## Completed analog cycle and128-channel integration - 2026-10-12





180us analog physical partition completes159.67s wall:1832native primitives,14365complete verified routingC,DRC0/exact independentgraph. Only two categorical controllers removed from this characterization;fullASIC V6 retains them. Restore8.38uV,beta step-26.900mV,positiveevent+143.160mV,spike3.294V,reset-6.467mV,writeback error-20.341mV. Programmed pulse-width termination andprecision remain unaccepted; no ideal DATA/state orUIC/IC. Full128 SUM/threshold nativeprimitive40us threecase nominal completes:sum10.464mV,threshold9.671mV errors,localsettling7.503us. Source/GDS exact3099MOS512R1536MIM;routeC excluded andcompleteRC remains open. One240s extension justified by measured120s reaching22.1866us/40us,216.35s projection;no circuit/tolerance tuning. V6 actual9actor ROOT joins reuse existing two64halves;exact896primitive sharedROOT composition equals native128 reducer andnewrepresentativeDRC0. All54,630,400active identities preserved;globalbankservice/graph/parameter/producerbindings,loadedRMS128 andfullASIC remain incomplete. Report:artifacts/analog_asic/assembly/full25_shared_ROOT128_v6/delivery_report_v1.html.








## Shared1024state page and completed reader partition - 2026-10-12





Actual1024state page6818MOS1029MIM:sourceGDS DRC0,exact7847primitive graph,71802complete verifiedroutingC. Onefeedbackreader serves8bankpairs. Whole34us transient timedout120.59s at3.996us nearfirstaddressedge; retained,not a pass. New physical frontend partition354MOS5MIM preservesparentroutes/decoder/readTG/mux/reader:DRC0,exact359graph,9498verifiedC.40us A-B-A sequence completes36.41s;sampled recoveryerror22.03uVmax,Areturnchange2.514nV. Frozenmeasured nativebankRAW100ohmfixtures;notwholepage sourceimpedance/startup/retention/serviceproof. Continuefullphysicalbindings,retainimperfectresults,avoidprecision/runtimecampaigns. FullV6assembly unchanged;allmodelglobalservice stillincomplete. Catalog101:20modules86characterizationassemblies. Report:artifacts/analog_asic/assembly/shared_reader_page1024_v1/article_report_v1.html.








## Full25actor shared1024page physical integration - 2026-10-12





V8actualGDS moves200existingresidentpairs into25shared1024pages. NativepageDATA0..7 connectexistingcompute writecolumns;nativelevelshift/gatedrestore joins existingcompute numericalinput. Original64+128state service retained:1216routedsites/actor,30400total. Independentbinaryreadback provesall54630400activeidentities/866080banks withoutduplication;865605plane banks remainglobalserviceunbound. Fourexactrootgeometrygroups cover25actors;representativeDRC:15 actors with0 recorded DRC errors, 1 actors with1 recorded DRC errors, 9 actors withDRC incomplete. V7restoreTG shared-x M4escape short diagnosed;V8separateM3escapes implemented. V7flat/V8hierarchical120sextractions bothincomplete;no newparentexactwiring pass. Methodreviewrequires actualinterconnectpartition/qualifiedchildcomposition insteadofblindlargeretry. Completedimperfectmodule results retained;accuracy/5ms unproven. Report:artifacts/analog_asic/assembly/full25_shared_page1024_v8/delivery_report_v1.html.








## All25actor sharedpage boundary composition verified - 2026-10-12





Independent exactmetal/MIMcontact graph checksalloriginal/newmoduleterminal anchors. Fourexactgeometry+TEXT+sourcebinding groups cover25actors;every qualifiednativechildGDS cell byteverified afternamespace mapping. No shorts,opens,floatingadditions,unknownchildcontacts orrootporterrors. KnownbadV7control correctlydetects sixshortednets. GF180VIA4 withinCAPM contactsMIMtop75,notM4;earliernaive verifierinvalidated/retained. Streaminghierarchy avoids2GB exit137 fromexpandedcache;largestcase2724428rectangles/2364anchors completes31.41s. All25actor circuitboundary composition nowqualified,includingnineRMS128ROOTjoins. ThisisnotcompletedflatnativeLVS/RC/loadednominal. DRC15actorszero,stemoneerror,nineRMS128DRCincomplete remain. Nextglobalbankservice/graph/parameterbinding andmissingloadedmodulecoverage. Report:artifacts/analog_asic/assembly/full25_shared_page1024_v8/delivery_report_v2.html.








## Globalpage selection and fullpopulation address mapping - 2026-10-12





Native8way higherselector230MOS source/GDS DRC0/nativeLVSunique,2332complete verifiedroutingC.40us0-7-0 command/readout sequence completes12.06s;allWRITE/READ/ENABLE onehotchecks correct. Static100ohm childRECOVfixtures frozenfromnativefrontend,100fFloading provisional;notfulltree service/precision. V1export lacked.subckt;V2explicitrootwrapper fixesexport withoutcircuitredesign. Canonicalrank/inverse/base8 mapping exhaustivelychecks865605remainingbanks andall54630400activestates incl30400routed:54105leaf1024pages,7837higherselectors,75extra inactivebanks. Physicalglobaltree notyetbuilt. Nextactualrecursivehierarchy with8DATAperchild TG isolation,uniformaddressdepth/no tailaliases,originalidentitypreservation;thenmembrane/AGE/AMP/classcompute interfaces. Catalog102:20modules87characterizationassemblies. Report:artifacts/analog_asic/assembly/full_population_page_access_v1/foundation_report_v1.html.








## Full-population shared-access assembly V9 - 2026-10-12





ActualGDS replaces56rawplane rootinstances with54105native1024pages and7837higherselectors;25existingcomputeclusters/parametercapacity/protocolgeometry retained.54600000foreststates+30400actorstates=54630400active analogidentities. Binaryhierarchy verifies501568DATA-TG and62696inverters;15leafhierarchycells byteidentical. All33template exactparent/interface metalgraphs pass:0shorts/opens/unknowncontacts/floatingadditions/porterrors;parentroutes avoid opaquechildregions andnativeleafchildbounds independentlychecked. Staticbounding-volume indexing avoidslong-wire gridexplosion;55.16s complete. V1checker anchorquery included unconnectednewpaint beforeaddition;V2limitsbaselineanchors correctly,retainedV1 ischeckerfailure,notcircuitfailure. Newtop oldrawplanes absent fromreachablehierarchy. No newtransient run. Spaciousatlas only;fullnewtop identitybinding,forestcompute/adaptation/class/operator/parameter links,loading/DRC/RC,accuracy/5ms remainopen. Userprioritizes completionwithimperfectresults,precisioncampaigns deferred. Report:artifacts/analog_asic/assembly/full25_page_forest_v9/article_report_v1.html.








## Full membrane compute access V10 - 2026-10-12





Actual25wrapperGDS bindsall30976000membranes:forestRECOV throughnative16MOSupshift/2MOSgatedrestore toexistingactorEXTERNAL_COMPUTE_DATA,8sharedanalogwritecolumns returntoforest. All25boundarymetal/contactproofs pass withactualactorrootpaint andallnativechildsubtrees intersectingnewwire bounds;disjointsubtrees safelyexcluded,forestopaquearea guarded. Allinheritedchildcells byteidenticaltoV9. V2proof fixesindex0truthiness omissionandchecksaddedvia metalcontacts;retainedV1 notauthoritative. Independentbinarytopcensus proves56forestrootoccurrences/25actors/54130native1024pagesincl25localpages;actualallgeometry/TEXT/arraybounds fitdisjointplacement. Active54630400identitycontract inheritedunchanged. One374MOSselector+64DATA-TG+8inverter40us0-7-0nativechildcapboundarycase completes32.812s;allcommandsonehot,unselectedDATAchange11.702uVmax,selectederror2.075nV withstiff100ohm/100fFfixtures,notfulltreeprecision. ParentatlaswireRC excluded. No activeprocess. NextAGE/AMP/classplanevoltage/restore/writeback interfaces,then graph/parameter/sequencer/missingfunctions. FullfunctionalASIC,accuracy/5ms incomplete. Report:artifacts/analog_asic/assembly/full25_membrane_service_v10/article_report_v1.html.








## Adaptation shared access and release-coupling review - 2026-10-12





New172MOS84MIM IO:2restoreTG,oneAGEbuffer,16analoghold/outputbuffers. Source/GDSDRC0 andexact256primitive/pin/net/edge/dimensionproofs pass V1/V2/V4;nativeNetgen mismatchesretained. CompleteC2296/2296/2196branches. Three110us nativeIO+resident(131MOS48R34MIM)A-B-Acases complete27.84/25.38/23.27s withoutIC/UIC;frozen100ohmRECOVboundaryfixtures,100fFoutputs. RestoreONnearzeroerror/captureerrors cannotacceptcorruptedworkingstate. AfirstAGE/AMPreleasechange:V1-295/-367mV,V2-26/-45mV,V4-39/-60mV. M4guards reducecontrolC133.86/137.56to12.624/17.992fF;localstateM4route shortening leavesresidualCunchanged andreducesVSSloading. V3AGE/VDDportaliasrejectedbeforetransient,V4actualbbox/escapechannelclearancefixpassesexactgraph. NexttargetactualparallelM5horizontalendpointescapes withgroundM5guards,keepV4localstate/M4guards. No moreblindspacing/bias/runtimecampaign. IO notfullpopulationbound;15AGE/AMPforestpairs,classcurrent/globalfunctions remainopen. V10all30976000membraneconnections unchanged. Report:artifacts/analog_asic/assembly/adaptation_shared_state_io_review_v1/article_report_v1.html.








## Repaired adaptation IO and fullpopulation access V12 - 2026-10-12





V6same172MOS84MIM withgroundM5horizontalguards(source/GDSDRC0/exact256graph,2196completeverifiedC). V5guard0.40umwidthrejected,corrected0.44umV6;nativeNetgen mismatchretained.110usnativeIO+residentA-B-A completes19.969s;postreleaseAGEabout-4.24mV,AMPabout-5.12mV(Afirst),allcase4-6mV retained. Capture91.42uVmax,heldslotchangebelow0.1uV. Frozen100ohmRECOV/100fFDATAfixtures;noIC/UIC. Carryimperfectresultforward,notfloataccuracy/expiry/8slotserviceacceptance. V11actual15wrapperlayout generated;V12addslocalM4risergroundguards toavoidrecreatingcoupling. NewlinearGDSnamespaceimport preservesnativecellswithoutquadraticconcatenation;assembly4.41s. V12routes21964800AGE/AMPstates:forestRECOVâ†’IOrestoreâ†’existingresidentAGE/AMPLITUDE,AGEbuffer/existingAMP_BUFâ†’16holdbuffersâ†’8DATAeachplane. All15actualboundarymetal/contactproofs pass;aliases independentlyderivedfromunchangedV10actorpins,allnativechildrenbyteverified. Independenttopcensus/portcontract/disjointbboxreadback:56forestroots/25actors/54130nativepages,all54630400activeidentitycontracts retained;30976000membranepaths inheritedunchanged. ParentRC/calibratedAGEadvance/expiry/allchannelproducerbindings unqualified. Classcurrent1689600states stillneedcomputeaccess;globaloperators/parameters/sequencing andaccuracy/5ms open. Catalog103:20modules/88characterizationassemblies. Report:artifacts/analog_asic/assembly/full25_adaptation_service_v12/article_report_v1.html.








## Class-score shared access V13 - 2026-10-12





All54,630,400analogstate identities now have physical shared access paths:30,976,000membrane,21,964,800AGE/AMP and1,689,600class-current. V13classforest joins existing six-class readout through native120MOS8R48MIMIO; source/GDSDRC0/exact176primitiveproofs,2787completeC. Readout complete2620Cexport preserves488nativeprimitives.180usnativeA-B-Arestore/mux/downshift/capture completes18.625s,restore7.97mV/roundtrip22.32mV errors retained;firstheldslotchange0.033uV,unselectedclasschange3.37mV. Explicit100ohmRECOV/100fFDATAfixtures;EVAL/SAMPLEinactive,prior three50mswinnercases retained. Firstdecknamecollision failedparsing andpreserved;V2fixchanges names/duplicateendpoint only. Parentexact62568baseline+3947newrectangles/145anchors proofpasses without shorts/opens/floating/unknowncontacts. Independentbinarycensus preserves56forestroots/25actors/54130nativepages;existingreadout appears exactlyonce,allV12topchildren unchanged;geometry/TEXT/AREFbounds disjoint. GDS55.23MB. NativeNetgen mismatch retained separatelyfromindependentexactproof. Allnumericaccess built doesnotcomplete globalgraph/operators,trainedparameters,phase/addresssequencing,parentRC/loadedservice/accuracy/5ms. Catalog104:20modules/89characterizationassemblies. Report:artifacts/analog_asic/assembly/full25_class_current_service_v13/article_report_v1.html.





## 128-channel depthwise categorical scatter - 2026-10-12





The weight-address scatter now scans only output channels connected to the incoming channel group. A 128-channel depthwise 3x3 event emits all nine legal taps in nine handshakes rather than examining 1,152 channel/tap combinations. Grouped and depthwise RTL regressions pass. The depthwise configuration is synthesized and routed as a standalone GF180 macro: ORFS detailed routing reaches zero violations; final CTS setup/hold counts are zero; Magic flattened GDS full-style DRC is zero; LEF/Liberty abstracts import into OpenROAD. Routed controller area is 48,641 um2. It is not yet bound into actor roots or continuous analog weight arrays; no full graph, original-float accuracy, or 5 ms service acceptance follows. Evidence: artifacts/analog_asic/results/gf180_analog_weight_event_scatter_depthwise128_v1.json.








## GF180 graph fanout macro - 2026-10-12





Completed the reusable `event_fork2` graph fanout macro: bounded Icarus stream/backpressure simulation, saved GF180 ORFS GDS/DEF/SPEF and reusable LEF/Liberty, flattened Magic DRC 0, and abstract import pass. The first ORFS attempt wrote to an ephemeral container directory; it is retained only as a failed persistence attempt. The persisted rerun is authoritative. Next: qualify the remaining graph operators, then bind actor endpoints and the continuous analog parameter/state interfaces. The full graph and chip remain incomplete.








## GF180 graph upsampling macro - 2026-10-12





Completed physical and functional qualification of the graph's nearest-neighbor 2x event upsampler, alongside the previously completed lossless event fork. The upsampler emits four spatial addresses for each event and one completion token per bin. GDS/DEF/SPEF and reusable LEF/Liberty are saved; flat Magic DRC is zero. Continue with fixed graph joins/channel remaps and residual semantics, then bind actor endpoints. The full graph and chip are not complete.








## GF180 graph join macro - 2026-10-12





Completed the physical and functional event-join macro. It preserves both streams and waits for two equal-tag completion tokens; a mismatched pair fails closed. The existing three reusable categorical operator macros now cover multicast, 2x event fanout, and two-input lossless merge. The binary residual-OR operator and complete actor/graph bindings are still outstanding.








## GF180 binary residual operator - 2026-10-12





Replaced the fixed-capacity event-list approach for the new analog residual operator with a one-head-per-input sorted merge. Functional and physical macro checks pass, including flat GDS DRC and LEF/Liberty import. This removes event-count storage growth but introduces a concrete producer contract: analog actors must serialize unique output addresses in ascending canonical order. That contract is now the next integration item; it is not yet proven.








## GF180 graph channel remap macro - 2026-10-12





Completed a registered GF180 channel-offset macro for the decoder concat leg, with DRC-clean GDS and importable LEF/Liberty. The categorical operator package now has physically routed implementations for lossless multicast, upsample, two-input join, channel offset, and bounded-state residual OR. The next integration dependency is a physically plausible actor-side spike-event serializer that supplies strictly ordered addresses.





Actor event-output milestone - 2026-10-12: selected the 32-lane shift-register serializer after single 128-lane candidates repeatedly timed out in detailed routing. The standalone bank now has routed GF180 GDS/LEF/Liberty, Magic full-style flat DRC zero and 50 MHz nominal scan timing; its OpenROAD route report retains two Metal2 spacing entries requiring future disposition. A four-bank 128-neuron page with sorted merge tree passes simulation for sparse sorted output, completion/tag propagation, partial tail lanes, and invalid lane count. Analog actor binding, parent layout and full graph service remain open. Evidence: `artifacts/analog_asic/results/gf180_analog_spike_event_serializer32_v1.json`.


128-neuron actor output page milestone - 2026-10-12: Four 32-lane ascending analog-comparator-output scanners and a three-node sorted merge tree pass integrated sparse-page simulation, matching completion tags, partial tails and invalid-count fail-closed. Flattened page parent has routed GDS/SPEF/LEF/Liberty, imported 249-terminal abstract, OpenROAD detailed-route violations 0 and Magic flat DRC0. Macro is 1.227 mm2; 50 MHz scan design meets 119.74 MHz STA Fmax. ORFS reports 120 max-slew violations; no setup/hold errors. This layout stops at the page-level comparator bitmap interface. Actual analog neuron binding, full graph layout and full 5 ms/accuracy acceptance remain incomplete. Evidence: `artifacts/analog_asic/results/gf180_analog_spike_event_page128_v1.json`.





## Analog neuron output to event-page handoff - 2026-10-12





Added and ran a repeatable mixed simulation bridge using the existing routed five-module GF180 neuron output trace and the routed 128-neuron categorical page. At the sampling point, near/high/low arms output 6.151 mV / 3.294 V / 0.194 mV. Applying the 2.31 V input-high boundary yielded one active lane; the page emitted address 4001 and the matching completion tag. The result advances the actor interface contract while keeping its limitations explicit: no extracted analog-to-digital wire, no 128-channel loaded analog bank, no full graph/accuracy/5 ms acceptance. The page V1 slew warnings were traced to 120 clock pins (3.20-3.22 ns vs 2.80 ns), absent from CTS and global-route reports; repair-enabled V2 crashed inside CTS and remains an unsuccessful experiment. Evidence: `artifacts/analog_asic/results/gf180_neuron_spike_to_page128_v1.json`.








## GF180 one-neuron physical event-page link - 2026-10-12





Assembled the characterized five-module analog neuron GDS with the routed 128-lane event page. Added an M5/via4/M4 route from neuron `SPIKE` to page `spike_bitmap_i[0]`. The first flat full-style DRC found one M5 minimum-width violation at the inside corner of an L bend; filling the corner square removed it. Final flattened Magic full-style DRC: **0**. Magic hierarchical extraction completed and confirmed both child subcircuits map the endpoints to the same extracted net, `gf180_neuron_five_module_parent_v6_0/SPIKE`. Parent GDS is 34,306,724 bytes and extracted SPICE 2,174,045 bytes. This is one physical channel handoff, not a 128-neuron physical bank, full graph, model-accuracy result, or whole-system 5 ms acceptance. Evidence and source: `scripts/assemble_gf180_one_neuron_page_link_v1.py`, `artifacts/analog_asic/assembly/gf180_one_neuron_page_link_v1/qualification.json`.








## GF180 analog neuron to pointwise weight-selector path - 2026-10-12





Replaced the expensive 26-bit flat-address division decoder after its merged physical route accumulated thousands of detailed-route violations. The selected interface now treats a page as the 128 channel bits at one spatial pixel; channel comes directly from the sorted bitmap lane and one 13-bit pixel index is decoded into x/y. The integrated page/decoder/pointwise-scatter top routed to final GF180 GDS, LEF, Liberty and SPEF; final detailed-route violations 0, antenna violations 0, setup/hold clean, mapped area 271,156 ÂµmÂ² (0.271 mmÂ²), die 1.82958 mm square (~3.35 mmÂ²). Flat full-style Magic DRC on the routed digital GDS: 0.





Composed the five-module analog neuron with that routed page/scatter macro. Physical M5/via4/M4/via3/M3 connection from neuron `SPIKE` to page `spike_bitmap_i[0]` passes flattened full-style Magic DRC0; hierarchical extraction confirms the endpoints share `gf180_neuron_five_module_parent_v6_0/SPIKE`. Mixed simulation using the measured 3.294347 V analog SPIKE sample (CMOS VIH 2.31 V) passes through channel 0 at pixel (21,10), yielding the expected pointwise selector tuple, multiplicity and tag. Parent GDS is ~22.85 MB. The selected analog weight value/read circuit and signed charge injection are not in this path; lanes 1â€“127, whole-model accuracy, full graph and 5 ms service remain open. Evidence: `scripts/assemble_gf180_neuron_page_scatter_link_v1.py`, `scripts/cosim_gf180_neuron_page_scatter_v1.py`, `artifacts/analog_asic/assembly/gf180_neuron_page_scatter_link_v1/qualification.json`, `artifacts/analog_asic/results/gf180_neuron_page_scatter_cosim_v1.json`.








## Signed float-weight transfer diagnosis â€” 2026-10-13





Resumed from the current Desktop checkout and preserved the routed analog-neuron-to-128-lane page-to-spatial-decoder-to-PW128-selector results. No Docker run was live at resume. The next analog stage had no stored-weight read wired into the injector, and its saved negative-event current was roughly50x below positive at the same voltage. Used the existing extracted230-MOS/4-MIM native sequencer/injector to diagnose the actual analog transfer.





Measured the negative branch at NPROGRAM0.45V (too weak),0.8V (saturated),0.67V and0.62V; the0.613V shared bias gave +/-1.8V steps +190.319/-189.570mV with one complete sequencer cycle each. Then identified the low-magnitude dead zone: the native ramp reset was1.2V while the continuous parameter range begins1.0V. Setting the external ramp reference to1.0V gives no event at1.0V, +31.828mV at1.1V and +125.616mV at1.4V. A full-scale negative1.4V event delivers-125.435mV; pulse-width and charge magnitudes match positive within0.15% nominally. The0.25 normalized point carries25.34% of full-scale charge. No QAT codes or digital membrane values are used.





The original-float parameter archive has143,824 weights across26 tensors. Using each tensor's max magnitude as an analog normalization leaves13.53% of values below1% of that tensor's maximum. Their estimated ideal pulse widths are under about51ns; this short-pulse region, actual addressed weight readout, network-level spike/segmentation error, and5ms population throughput remain unqualified. The1.0-1.4V mapping is a candidate only. The full chip and goal remain incomplete. See `artifacts/analog_asic/results/gf180_weight_delivery_float_mapping_v1.json`.








Routed per-bank scale-source milestone — 2026-10-13: fixed parent LVS by adding via4 at the child metal5 port, not only at the upper rail. `gf180_membrane_scale_current_cell_v6` passes DRC0, unique LVS and GDS-readback checks. Its extracted-parent 5ms reader run reproduces min/median normalized scale-current fractions within about1.2%/2.9% nominally; gate drifts7–8mV. Parent bbox780.3x414.2um; replication for490,240 banks is not area-qualified. Continue with footprint/sharing analysis and connect scale to the signed event update. Full original-float replay,5ms population service and full-chip layout remain incomplete. Exact pre-update docs: `artifacts/analog_asic/documentation_history/project_docs_before_scale_macro_v6_20261013T032321Z.zip`.






Scale sharing analysis milestone - 2026-10-13: range-only grouping shows 16x16 banks reduce the number of voltage-scale values 3.88x, with a storage-error proxy above 5% in 1.466% of states; 32x32 leaves 3.264% above 5%. No inference accuracy result yet, so 8x8 remains the baseline. Compact physical cell v1/v2 is still DRC-failing. Exact pre-update docs: `artifacts/analog_asic/documentation_history/project_docs_before_scale_coarsening_v2_20261013T033139.zip`.



Eight-record scale-bank replay milestone - 2026-10-13: all baseline hashes match. A deterministic per-update bound stress for16x16 banks reduces mean IoU0.0206-0.0495; this is a conservative surrogate, not measured device noise. Keep8x8; exact device error and physical scale routing remain open. Exact pre-update docs: `artifacts/analog_asic/documentation_history/project_docs_before_scale_error_replay_20261013T035150.zip`.


2026-10-13 compact scale progress: v16 fixes the earlier routed parent short by spacing the TG and PFET instances farther apart. Full-style DRC0, unique LVS, GDS roundtrip DRC0/LVS unique; extracted 5ms hold values are within 1.1mV at three voltage points. Nineteen-point PFET read-current transfer is monotonic but strongly nonlinear (1.56uA to 1.42nA across 0.75–2.55V), so original-float current mapping still needs calibration. Evidence and limits are recorded in RESULTS.md and project_spec.yaml.


2026-10-13: compact scale parent v23 preserves v16 DRC/LVS/GDS readback and extracted 5ms/19-point simulation, while shortening rails reduces bbox area 4.7x to 0.02708mm2. Current transfer is monotonic but strongly nonlinear; calibration against the 490,240 original-float bank ranges and signed membrane update remains next.


2026-10-13 routed packet milestone: compact parent v12 now passes full DRC/LVS/GDS readback at0.04925mm2. Direct child-pin control exposure removes long-bus control coupling; routed center-state packet calibration gives+8.01/-8.10mV signed updates with0.04mV drift at5ms. Staggered endpoint run completes, but handoff errors reach13.9mV and prior sparse packet maps miss target at low/high states. Continue state-conditioned beta/baseline/packet calibration and original-float replay; no full-chip layout or 25-actor service pass yet. Exact pre-update docs: `artifacts/analog_asic/documentation_history/project_docs_before_routed_sc_packet_20261013T091833.zip`.


## Physical switched-capacitor voltage mapping - 2026-10-13

The physically routed auxmetal_v1 switched-capacitor parent adds 5.52fF by enlarging existing M4/M5 plates from 100 to 240um2, with no bounding-box growth (0.04925mm2). DRC/LVS/GDS readback pass. Extracted calibrated low/high packets deliver +7.987/-7.935mV and +7.960/-8.000mV; endpoint hold drift <=0.191mV over 5ms. Seven initial states and -8/0/+8mV commands (21 cases, 130us) yield <=0.330mV packet error under interpolation of external calibration anchors. Handoff displacement improves to <=7.50mV but learned beta is not qualified. Prior MOS-cap screens are diagnostic only; body-at-VCM variants do not establish a standard substrate implementation. Actual linear metal plates are the carried-forward design. External ideal references/phases, UIC startup, original-float precision, PVT/noise, physical producer bindings and full-population 5ms remain open. Evidence: `artifacts/analog_asic/layout/gf180_sc_state_packet_auxmetal_v1/qualification.json`, `artifacts/analog_asic/results/gf180_sc_state_packet_auxmetal_v1_beta_noaux_calibrated_packet_map_v1.json`, `artifacts/analog_asic/results/gf180_sc_state_packet_auxmetal_v1_state_map21_v1.json`.

Documentation archive: `artifacts/analog_asic/documentation_history/project_docs_before_auxmetal_packet_map_20261013T063506Z.zip`.


## Integrated trained beta and shared auxiliary reference - 2026-10-13

GF180 integrated original-channel beta and physical shared-reference qualification. The detail_stem channel3 v4 SC parent passes DRC/LVS/GDS readback in0.04925mm2; actual386.4um2 auxiliary metal plates give measured beta0.88298 versus trained0.88189. Nominal21cases across0.75-2.55V have <=1.89mV combined beta/packet error with external calibrated reference. Two original-float heldout replays reproduce baseline hashes and change1.60/1.83% pixels with IoU+0.00175/+0.00123 for this channel only. Native three-resistor/MIM-decoupled reference v2 also passes physical checks; one extracted reference drives21 extracted parents with1us stagger and10ns beta edges, <=3.54mV candidate error. Inter-macro wiring remains bench-only. Next physically route reference and compute together, qualify actual weight/VCM producers and learned-beta channel coverage, then shared-service/full-chip integration. Full-model accuracy and5ms population service remain unqualified. Evidence and rejected attempts: `artifacts/analog_asic/results/gf180_sc_packet_beta_reference_stage_v1.json`. Archive: `artifacts/analog_asic/documentation_history/project_docs_before_sc_beta_reference_20261013T071254Z.zip`.


## Layout-first delivery order - 2026-10-13

Full-chip research layout completion first, then per-module simulation, per explicit user direction2026-10-13. Carry current measured imperfections forward. Start from V13 full-population numeric-state access assembly and existing physical module library; physically implement and connect the25-actor event graph, actor/event boundaries, parameter delivery and phase/address controls. Fix only missing connections, shorts/opens, absent required functions or faults preventing operation. Defer calibration refinements, behavior optimization and repeated accuracy screens until the full layout is assembled. Analog state and original epoch58 float parameters remain the architecture. Full layout and population5ms/accuracy validation are incomplete; do not claim placement/capacity alone completes functional layout. Archive: `artifacts/analog_asic/documentation_history/project_docs_before_layout_first_20261013T072922Z.zip`.


## Routed event graph and scalar actor boundary - 2026-10-13

The full 25-actor/53-edge categorical graph now has actual routed GDS/ODB/DEF/SPEF/LEF and an extracted 3,087-terminal physical contract. Macro size 1,730.68 x 1,730.68 um (2.995 mm2); final detailed-route violations 0. The original default 5.5V timing report retains 1,833 max-slew violations. Reanalysis of unchanged ODB/SPEF with the existing GF180 typical 25C/3.3V standard-cell library gives setup slack +2.43 ns and hold slack +0.77 ns at 20 ns. This is nominal macro STA, not full-chip or PVT closure.

The existing shared analog lane produces sequential scalar decisions, so its output cannot be treated as 128 simultaneous comparators. A new scalar result packet adapter accepts a settled sampled comparator decision plus canonical channel/y/x address and tag, suppresses non-spikes, and emits full-bin completion after the last spike handshake. Sample-valid and last-result are service-controller inputs; last-result must cover the entire actor population. RTL cases pass for sparse/silent/single-neuron bins, backpressure, final-spike ordering, tag wrap and fail-closed tag/order faults. Its routed macro is 251.315 x 251.315 um (0.06316 mm2), 119 terminals, detailed-route violations 0 and default final max-slew count 0. Nominal 3.3V setup/hold slacks +9.49/+0.82 ns at 20 ns.

Evidence: assembly/full25_event_graph_layout_v1/physical_macro.json; assembly/scalar_result_packet_layout_v1/physical_macro.json; results/scalar_result_packet_v1/simulation.json. Their timing_3v3_v1 and timing_3v3_v2 subfolders respectively retain nominal STA. Scalar timing attempt1 failed only because openroad was not on PATH; the failed log is preserved and attempt2 uses the installed executable. Neither macro has a new Magic independent DRC result. Neither is yet physically bound into V13. Full-chip functional layout, parameter/control producers, loaded analog interfaces, model accuracy and 5ms service remain incomplete. No calibration/behavior refinement was performed.


## Existing binding reconciliation and connected packet fabric - 2026-10-13

Earlier binding work is present and retained: gf180_one_neuron_page_link_v1 and gf180_neuron_page_scatter_link_v1 both have actual GDS, zero full-style Magic DRC and extracted SPIKE-to-page lane0 connectivity. Rechecked 10 and9 source/artifact hashes and the actual hierarchical SPICE link; both pass. V13 numeric-state read/restore/writeback bindings remain the physical base. These are completed partial bindings, not absent work. The earlier statement that binding was still needed refers to remaining full25 graph/parameter/control connections, not rebuilding the existing one-neuron demonstration or storage access. Evidence: assembly/full25_packet_fabric_v1/prior_binding_reconciliation_v1.json.

The next parent physically joins one existing graph macro with25 scalar-result macros, reusing their GDS/LEF and regenerated 3.3V timing abstracts. Synthesized structure independently confirms all25 adapter packet buses/handshakes/tags (1475 bit connections) and result/control slices. All numeric state/weights remain analog. The parent exposes sampled comparator results and graph actor-input ports; native actor conductors and parameter/phase/address producers still need binding.

The first hierarchical parent stopped with GPL-0305 numerical divergence in global placement, before routing. Original logs, status and failed ODB remain preserved. A bounded repair variant packet_fabric_repair1 lowers movable-cell density0.30 to0.08 and disables timing/routability-driven placement inflation; the26 macros, placements and RTL connections are unchanged. Live handle ess-gf180-full25-packet-fabric-repair1. This is a new all25 packet-fabric composition, not a rerun of the successful earlier one-neuron binding. Full-chip completion remains false.


## All25 actual spike outputs and packet-parent supply repair - 2026-10-13

New full-state GDS: assembly/full25_spike_breakouts_v15/eventspikeseg140k_spike_breakouts_v15.gds, top ESS140K_SPIKE_BREAKOUTS_V15,55,230,028bytes. Each actual compute__C_SPIKE (or existing OWN_SPIKE for stem) now has an M5 escape to a SPIKE_RESULT pad20um outside its enclosing top-level membrane/adaptation wrapper. Conservative contact proof rejects any touched M5 component other than the existing source component. Independent full-parent readback passes all25, including the enclosing-parent metal. It verifies326unchanged sourcecells bytewise and66cloned actor/ancestorcells, preserving all existing state geometry and array multiplicities. V14 internal-pad intermediate preserved. These are real analog output conductors, still not joined to the graph. New escapes have no spacingDRC/RC/loading acceptance yet.

Connected packet fabric repair1 passed detailed signal routing (finalDRT0; one antenna net/pin remains) but final_report failed PSM-0069 on VDD. At least result_14,result_19,result_24 and graph_macro VDD pins are disconnected; VSS has not yet passed independently. Source GF180 default PDN script contains only a standard-cell grid and no macro supply connection grid. Final routed5_route.odb,DEF/SPEF and logs preserved; no finalGDS/LEF acceptance. No job remains live. Next is PG connection repair using the existing routed database, then final extraction/GDS export and external SPIKE-to-fabric routes; parameter/phase/address bindings still required.

Two bounded direct add_sroute_connect attempts preserved as supply_repair_v1/repair.tcl and repair2.tcl. First rejected float pitch arguments; the installed API expects integer database units. Second aborted inside OpenROAD SRoute::addSrouteInst when invoked with the existing same-domain grid (no power ring); it produced no repairedODB. Do not repeat this command blindly or rerun the13minute signal route. Repair the lateral Metal5 macro supply-pin connection to adjacent same-net Metal4 grid with explicit geometry/contact checks, or add a suitable macroPG strategy. V15 existing SPIKE escape checks remain independent of this supply issue.


## Connected25-output graph assembly V16 - 2026-10-13

Packet fabric supply repair now completes:163M5rail joins/one-cut via connections, no existing signal-wire edits (92,853shape fingerprint/readback), bothVDD/VSS power-grid checks pass. Corrected newVia4cut0.28to0.26um withgenerated-via metadata;163newcut checks against87,248existingPGVia4cuts find0conflicts. Nominal4.5ohm via resistance comes from the local open_pdks gf180mcuD.tech contact4500milliohm entries. The installed load_design hardcodes platform/setRC.tcl and bypassesRC_FILE; supported PRE_FINAL_REPORT_TCL now applies the native nominal cut-layer resistance after loading. Prior zero-resistance/Makefile-precedence/engine-interruption failures retained. Finalreport and power calculation complete at3.3V/25C. StreamedGDS296,398,522bytes;LEF3,012terminals;26macros;4,500x3,500um(15.75mm2,packetfabric only). Finalsetup slack-0.270113ns at20ns,hold+3.49325ns,Fmax49.3337MHz,max-slew count0. Carry this small50MHzsetup miss; no timing signoff claim. Prior signalDRT0 and oneantenna net/pin retained; no full-style DRC afterPGpatch.

V16 streams the unchanged V15full-state analog library and the unchanged completed packet-fabric library into one actualGDS, then routes25actualSPIKE_RESULTconductors to matching result_spike_i inputs. Outside-macro ManhattanM4/M5tracks andM3/M4pin approaches add829rectangles. Independent binaryGDSreadback verifies both childlibraries byte-identical, rootreferences/placements,25distinct source/destination components,0opens/aliases/floatingnewmetal and0incrementalM3/M4/M5inter-net spacing conflicts. Source54,630,400state identities and native geometry inherited unchanged; full chip native inventory not recounted anew. GDS351,683,212bytes,topESS140K_SPIKE_GRAPH_V16. This retains the spacious atlas, not a compact die. LongglobalwireRC/loading and full-styleDRC remain unqualified.

Required remaining bindings: shared supplies/clock/reset, settled sample-valid, per-neuron canonical address/bin-tag and entire-population last-result, graph actor-input to analog synapse/weight service, trained analog parameter delivery and phase/address producers. These are still essential functions. No QAT/digital-state fallback or calibration campaign was introduced. FullfunctionalASIC, original-float accuracy and5ms population service are incomplete. Evidence: assembly/full25_spike_graph_v16/delivery_stage_v1.json and gds_incremental_connectivity_v1.json; assembly/full25_packet_fabric_v1/physical_macro.json and final_boundary_contract_v1.json. No live job remains.


## Decision/address producer V2 and confirmed service bound - 2026-10-13

New categorical decision scan requests one native neuron service, requires a freshlow/high settled-done, holds its canonical channel/y/x address and result-valid through packet backpressure, and waits until the scalar adapter drains the entire-population completion. It generates membrane/local64/two-bank/local1024/forest selection and auxiliaryforest addresses; numerical state and weights remain analog. Start requires completed accumulation and required populationRMS/threshold phases; native service-ready/done/hold and physicalbindings remain open.

Physical mapping audit found11low-resolution actors have excludedlocalbanks0..8,10..19:bank9is the firstforestbank,bank19is localpage. The initial contiguousbankV1smoke is preserved and is not used for layout. V2uses an explicit380-bit categorical address table from frozen physicalexceptions, including local-page slot order. Its bounded adapter-linked simulation covers5440valid neuronresults with partialedge tiles, allfourserviceclasses, noncontiguous bankrank, auxiliaryaddress, canonical ordering, freshacknowledgment, backpressure, finalspike/completion, silentbin andreset. Independentgeneratedparameter audit checks all490240membranebanks, rank/inverse and exactvalidedge counts for30976000membranes across25originalfloat actors.

A concrete5ms architectural gap is confirmed: current one-serial-service-peractor cannot meet real-time5ms even if analog work were instantaneous. REQUEST,WAIT_SERVICE,PUBLISH require at least3clockcycles perneuron. At the controller25ns(40MHz)constraint the largest4,505,600-neuron actor needs at least0.33792s; at least68independent service lanes would be needed for thatactor before actualanalog service, storage contention, outputtraffic orgraph latency. This is a minimum, not the selected lane count. Addresslogic remains reusable; fullpopulationserial service must not be accepted for5ms. Next architecture work must partition state-access trees and replicate analogservice/results according to loaded native timing and traffic, while continuing requiredlayout/control/parameter bindings. No fullmodelSPICE or QAT fallback.

The25actual-shape controller top is running a bounded30minute nominal3.3VGF180physical flow: ess-gf180-full25-decision-control-v2. It reuses the proven PRE_FINAL_REPORT nominalvia-resistance hook. V16connected-output layout stays the current assembledGDS. Evidence: results/decision_scan_v2/simulation.json; assembly/full25_decision_control_v2/status.json, all_actor_address_map_v1.json, serial_service_lower_bound_v1.json. Controller layout/physicalbinding, fullfunctionalASIC, accuracy and5ms remain incomplete.


## 2026-10-13 — Fixed-kernel ingress and confirmed real-time parallelism

- User explicitly retained5ms real-time execution. Slower execution is not an accepted replacement.
- Generated all25 actor ingress services from original epoch58 float convolution/input shapes;143728 PLIF synaptic addresses, plus96separate head weights. Preserve event multiplicity; each group completion requires all connected output channels' signed analog charge.
- First ingress physical attempt exhausted4GB during Yosys arithmetic mapping. Preserved failed status/log. V2 uses bounded fixed-kernel categorical arithmetic and omits redundant per-output address arithmetic. Ingress protocol passes; all25 actual configurations pass150000 clock comparisons against prior valid-address behavior, including padding/stride/groups/backpressure. First comparison incorrectly compared coordinates when valid was false; retained failure and corrected protocol-qualified comparison in scatter_fixed_kernel_v2b.
- Physical ingress V2 running: ess-gf180-full25-actor-ingress-v2; assembly/full25_actor_ingress_v2/status.json. Native analog weight read/injection remains unbound.
- Decision-control V2 first attempt timed out after30min; saved5_1_grt.odb and prior status/log retained. Resumed routing/final export in ess-gf180-full25-decision-control-resume-v3 with repeated post-route antenna repair disabled; carry remaining antenna findings. Final timing/layout acceptance awaits terminal reports.
- Reused two existing verified epoch58 float activity records; no new full-model simulation.11actors exceed ideal single40MHz packet capacity;19 exceed ideal single group issue capacity. final_fuse.standard needs >=35packet paths, >=309group issue paths, >=68three-cycle decision services before analog delay/contention/DAG overhead. Bounds are necessary minima under optimistic40MHz, not chosen hardware parallelism or timing closure.
- Next architecture must partition shared storage roots, provide independent native services and parallel weight/event dispatch, then preserve completion barriers and result ordering. Serial macro completion does not establish a5ms ASIC. Latest assembled GDS remains V16; functional full layout, loaded module service, original-float accuracy and5ms are incomplete.

Evidence: artifacts/analog_asic/results/actor_ingress_v2/simulation.json; results/scatter_fixed_kernel_v2b/simulation.json; assembly/full25_actor_ingress_v2/status.json; assembly/full25_actor_ingress_v2/measured_parallel_service_requirements_v1.json; assembly/full25_decision_control_v2/status.json (all relative to artifacts/analog_asic except where shown).


## 2026-10-13 — Independent physical storage roots V4

Built `artifacts/analog_asic/assembly/parallel_storage_roots_v4/parallel_storage_roots_v4.gds` (27,307,772bytes), topGF180_PARALLEL_STORAGE_ROOTS_V4. Standalone candidate exposes54,105existing native1024pages independently, preserving every original page cell/position and54,600,000forest state identities. Remaining30,400local identities remain in existing actor modules. Shared ancestor selector circuits remain as unreferenced library definitions; no numerical state or native page geometry was altered. DATA/RECOV/write/read/address buses are now independent perpage in this candidate, ready for separate native services; global supply/control/compute/weight bindings are still absent.

Independent actual GDS readback passes54,105references, byte-identical native library, zero leaf bounding-box overlaps and every865,605canonical bank mapping with zero page/row/column identity aliases. Every page valid-state count includes edge padding and excluded local banks. Earlier V3 geometry is retained: its per-page active-count metadata incorrectly treated padding as contiguous and is superseded by V4. Evidence: `artifacts/analog_asic/assembly/parallel_storage_roots_v4/physical_partition.json`, `root_instance_map.json`, `independent_readback_v1.json`.

This is a physical partition building block for the confirmed5ms architecture. It does not prove enough native compute/injection bandwidth or loaded parallel service, and has not replaced V16. Latest connected full assembly remains V16. The two categorical physical jobs remain governed by their actual status/containers; do not repeat already completed analog neuron/page/scatter bindings.


## 2026-10-13 — All25 ingress physical macro completed

Container ess-gf180-full25-actor-ingress-v2 exited0; source hashes verified and final physical views collected in `artifacts/analog_asic/assembly/full25_actor_ingress_v2/physical_macro.json`. Real GDS/LEF/ODB/DEF/SPEF/netlist and nominal Liberty available. GF1803.3V/25C:1570.795x1570.795um (2.4674mm2),4804pins,40MHz setup slack+2.77583ns/hold+0.747967ns; nominal Fmax44.9961MHz. Detailed-route DRC0, antenna nets/pins0.495slew violations retained as measured imperfections. This is categorical addressing for25real convolution configurations, not analog weight storage/read/injection or real-time full-chip proof. Protocol and150000allactor valid-address comparisons pass. Confirmed5ms architecture still requires independent native parallel services and sufficient parallel event/weight bandwidth. Decision-control resume remains live; latest full connected assembly V16 and standalone parallel-storage V4 are preserved.


## 2026-10-13 — Decision V2 physical completion; vital V3 clock repair

Decision V2 completed its real GDS/LEF/ODB/DEF/SPEF/netlist/Liberty after bounded resume:1853.365um square,4279pins,DRC0,21antenna nets/22pins,380slew violations. Nominal3.3V/25C setup slack-28.6103ns at25ns (Fmax18.6531MHz),hold+0.928857ns. Physical completion is not40MHz timing closure. Preserve `artifacts/analog_asic/assembly/full25_decision_control_v2/physical_macro.json`; do not use the failed clock for a5ms claim.

V3 removes per-result coordinate multiplication by incrementing canonical bank/row/channel base counters. It uses the two actual frozen local-bank patterns directly instead of a19-comparator/addition chain. Numerical state/weights stay analog; actor identities and address protocol unchanged. Bounded protocol simulation passes5440results;3600RTL seeded boundary cases cover all25actual dimensions,8-column/8-row carries,partial last rows,channel rollover andfinal result. Seeded tests are not whole-population runtime. Evidence: `results/decision_scan_v3/simulation.json`, `results/decision_bank_carry_v3/simulation.json` under artifacts/analog_asic.

Started bounded GF1803.3V/25C V3 physical job `ess-gf180-full25-decision-control-v3`, ID5cde8d430fda8e67e932b319618cca6de7053452c84efcc6f02ab6cfd927d0a8,4GB/2CPU/1800s. Provenance: `artifacts/analog_asic/assembly/full25_decision_control_v3/status.json`. Post-route antenna refinement is disabled from launch; findings carried. This is a vital required-clock repair, not a calibration campaign. Serial services still require architectural replication/dispatch and independent analog roots to meet confirmed5ms; timing closure of V3 alone will not suffice. Latest connected full assembly remains V16, independent storage candidate V4, completed ingress V2.


## 2026-10-13 — Parallel native service pair and physical access interlock

Decision-control V3 completed with40MHz setup+8.57772ns/hold+0.726315ns,nominal Fmax60.8929MHz,routedDRC0;981slew violations and23antenna nets/pins retained. Vital coordinate-multiply timing failure fixed; no5ms population proof.

Built `assembly/parallel_page_service_pair_v1/parallel_page_service_pair_v1.gds` (9,635,056bytes): two independent existing V8 page/feedback-reader/level-shift/restore/analogcompute/signedinjector/eight-column-writeback services. Each has1024resident slots and192working/legacylocal slots; the latter are not additional model identities. Removed only two old categorical-controller references/private labels per reusable service, exposing phase ports without conflicting drivers. Independent binary GDS readback verifies unchanged native cells, all1665parent route elements, placements, two distinct nonoverlapping page/compute service instances. No new fullpage RC/transient/global wiring qualification or selection of54105compute copies.

Added categorical page access interlock. V1 layout preserved; V2 adds necessary physical zero-state initialization: load EXTERNAL_INIT_DATA tied to COMPUTE_REFERENCE into compute and all eight analog holders, then selected-row commit. No ideal numeric state/DATA source or digital numerical fallback. Read/restore, fresh low/high compute completion, isolated column capture, all-eight-only row write, read-only working-copy discard, safe address changes and sticky fault/reset gates pass bounded RTL tests using two-clock fixture durations. Actual model beta/event/RMS/threshold/reset phases remain external and must follow original float bin ordering.

Two-lane V2 interlock completed GF1803.3V/25C physical GDS/LEF/ODB/DEF/SPEF/netlist/Liberty:427.995um square,144pins,40MHz setup+14.9232ns/hold+0.803807ns,nominal Fmax99.2374MHz. Conservative unqualified analog access defaults are20.25us read/restore and10.15us capture before compute phases; a1024state serial sweep exceeds5ms. This is a connectivity/interlock building block, not a selected real-time schedule. Faster native loaded timing and/or more independently accessed services remains required. Parallel packet/weight delivery bounds are unchanged. Controller-to-native pin escape/binding, initialization reference tie and disabled legacy access-command ties are next.

Evidence under artifacts/analog_asic: `assembly/full25_decision_control_v3/physical_macro.json`; `assembly/parallel_page_service_pair_v1/physical_pair.json` and `independent_readback_v1.json`; `results/page_access_control_v2/simulation.json`; `assembly/page_access_pair_control_v2/physical_macro.json`. Latest full connected assembly remains V16; independent storage-root candidate V4 remains separate. No live jobs at this stage; inspect actual Docker identity/status before restarting any flow.


## 2026-10-13 — Connected native two-page access module completed

Real GDS: `artifacts/analog_asic/assembly/controlled_page_service_pair_v3/controlled_page_service_pair_v3.gds` (14,793,492bytes), topGF180_CONTROLLED_PAGE_SERVICE_PAIR_V3. Two unchanged native1024page/feedback-reader/restore/analogcompute/signedinjector/eight-column-writeback services now physically connect to the completed two-lane access interlock V2.84real controller paths,31disabled low controls/two high controls perlane,shared VDD/VSS and EXTERNAL_INIT_DATA tied to COMPUTE_REFERENCE for zero initialization. Source analog and standard-cell child libraries preserved.

79native control/reference/supply pin escapes pass complete native metal readback. Failed0.6um universal-guard attempt retained; selected compiled GF180D tech requires thin-wire M3/M4 .28um/M5 .46um spacing, and the successful escape attempt follows these rules. First top route plan conflicted with top escape elbows and is retained; V3 global tracks are above all escape elbows. Initial readback attempts rejected unsupported reflected standard-cell rows and PATH records. Reader V3 now explicitly handles orthogonal reflection/rotation and PATH end styles0/2/4, with bounded synthetic format checks, and rejects unsupported round paths. MIM Via4 behavior is preserved and checked separately from ordinary M4/M5 vias.

Actual complete native+standardcell GDS metal readback passes all84controller bindings and intended supply/zero-reference/legacy ties:0foreign/unknown native contacts,0inter-net aliases,0opens,0floating added rectangles across2139newconductor rectangles. Evidence: `assembly/controlled_page_service_pair_v3/independent_readback_v3.json`; `assembly/page_service_control_breakouts_v2/independent_readback_v1.json`; `results/service_metal_graph_v3/checks.json` under artifacts/analog_asic. Digital interlock V2 has40MHz setup+14.9232ns/hold+0.803807ns,DRC0/antenna0/slew0. Native page geometry is unchanged; this is not a new full-style parent DRC/device-extraction or loaded analog transient pass.

Broad stage: reusable parallel storage/access/control module now connected. Original-float continuous weight delivery,actual model phase/completion producers,loaded timing and full25actor integration remain. Conservative access defaults still exceed5ms per1024slot serial sweep; confirmed real-time5ms requires further qualified timing/parallel bandwidth. Latest full assembly stays V16; independent storage candidate V4 andthis module remain separate. No live physical jobs. Delivery inventory: `artifacts/analog_asic/assembly/controlled_page_service_pair_v3/delivery_stage_v1.json`.


## 2026-10-13 — Docker and duplicate build-output cleanup

Per user instruction, archived inspect/stdout/stderr/exit state/filesystem diffs for11stopped ess-* ASIC attempt containers,verified all result directories are host bind mounts,then removed the containers without force/volume deletion. Docker builder prune reported28.76GB cleared; cache/container counts now0. Images and four named volumes preserved. Removed38unreferenced byte-identical intermediates from completed physical-macro folders,retaining canonical views,for2,053,462,323bytes. Protected hash-referenced6_1_fill.odb and all failed-run folders. Rehashed all8physical-macro artifact sets successfully after cleanup. Windows VHD file shrinkage was not claimed.

Categorical collector now accepts verified terminal archives for missing disposable handles andautomatically archives/removes terminal containers after success/failure collection. Existing status/source hashes remain unchanged. Simulation containers already use --rm. Evidence: `artifacts/analog_asic/operations/storage_cleanup_20261013/cleanup_summary.json`, `duplicate_output_plan.json`, `duplicate_output_cleanup.json`; container archives in `artifacts/analog_asic/operations/docker_container_archive`. ASIC task remains native parallel weight/phase integration following controlled_page_service_pair_v3.


## Active remaining task: consumption per element type — 2026-10-14

The user clarified that per-module simulation means power/energy consumption for one representative instance of each implemented model element: one PLIF core, one membrane storage cell, one signed synaptic injector, beta/threshold/reset, adaptation, inhibition, normalization and class readout, plus their shared access/bias/control circuits. The full article layout is already delivered. Characterize element types once with explicit nominal operating point, activity/load, operation duration, idle/hold power and energy per operation. Do not simulate every replicated instance or restart behavior/calibration/layout improvements as completion gates.

Keep one resident storage cell separate from the shared PLIF update core and shared bank/page reader. Never divide a whole shared module's supply energy by its state capacity and label that a measured single-cell value. Account for driver/reference/programming ports explicitly; VDD alone may exclude energy supplied through other ports. Reuse saved current traces and existing supply results first, then run only missing bounded small-module measurements. Evidence/status: `artifacts/analog_asic/results/module_consumption_v1/consumption_inventory.json`; per-element consumption is not yet complete.



## Representative per-element consumption delivered — 2026-10-14

The article layout and representative consumption characterization are complete under the user's clarified scope. `artifacts/analog_asic/results/module_consumption_v1/consumption_summary.json` covers all22 required element/module families, plus native capacitor, sampled decision, bias/normalization kernels and the three shared categorical macro estimates. One physical PLIF core, one3T+MIM resident cell, signed injector, adaptation, inhibition, normalization, readout, access and controls are distinguished. Each transient row states its window and supply energy/power; detailed reports retain input-port accounting. Core beta/decision/reset windows are measurements of the whole core during those phases, not standalone leaf powers.

Coverage combines newly completed native transients, reused complete rail-current traces, native RMS DC/settled samples and explicitly labeled routed-library digital power estimates. Shared1024-state reader power is partition/leaf characterization, not a completed full connected-page power simulation. Bias/reference/phase-generator overhead outside the measured boundary remains excluded unless stated. No measured full-chip power, calibrated behavior or5ms full-population deadline is claimed. Do not sum overlapping modules or replicate shared-core cost per logical membrane. Further circuit optimization is optional.



## Layout images delivered — 2026-10-14

`artifacts/analog_asic/assembly/full25_native_controls_v31/layout_images_v2/` contains300dpi PNG exports: full_layout_overview.png (3200x2700), plif_core_detail.png (2800x1050), and membrane_bank_detail.png (2800x1800). The overview renders actual finalV31 GDS spatial hierarchy and parent polygons, simplifying small repeated instance extents to avoid flattening millions of cells. Its physical scale describes the spacious research atlas, not compact die area. The PLIF view is matched by native geometry signature within the actual assembledGDS; the membrane bank view is from its qualified native component-sourceGDS, not an independently matched assembled-cell crop. Source/layout SHA matches the final independent readback; image source scopes and hashes are in render_manifest.json. All three renders visually inspected. Images do not establish fabrication signoff, compactness or circuit accuracy. Rendering used host Python/Pillow; no new Docker images or containers.


2026-10-14 SVG export delivered: full_layout_overview.svg, membrane_bank_detail.svg and plif_core_detail.svg are beside the PNGs in `artifacts/analog_asic/assembly/full25_native_controls_v31/layout_images_v2/`. True vector GDS paths/reusable hierarchy; no embedded raster images. The full-layout overview retains fixed hierarchy simplification and does not reveal omitted transistor geometry on zoom. Component source scopes match the PNG manifest. XML parsed and all three SVG previews visually inspected. Provenance/file hashes: svg_manifest.json. Sizes:16.55MB overview,0.36MB membrane bank,0.16MB PLIF.


## ASIC artifact reorganization — 2026-10-14

Canonical article package: `artifacts/analog_asic/` (start at index.html). Final GDS is `layout/EventSpikeSeg140k_GF180_Analog.gds`; PNG/SVG figures are together in images/; current consumption data is consumption/summary.json. Original manifests/source/results are preserved unchanged under evidence/, components/, model_reference/support locations. The current path locator is `artifacts/asic_artifact_index.json`.

Digital documentation-only snapshots are `artifacts/ASIC/final/` and `artifacts/ASIC_XL/final/`; neither claims a completed digital full-chip layout. Last exports, hierarchy inventory, completed block views and final reports are retained; digital jobs remain paused.

All superseded attempts and build environments moved to `bin/asic_cleanup_2026-10-14_20261014T145109Z/`, including related digital OpenROAD history. No files deleted. cleanup_plan.json inventories every original file; integrity_audit.json accounts for all64,814 originals and verifies SHA256 of all2,779 retained files. restore_artifacts.ps1 can restore original artifact trees; pre-cleanup docs and .gitignore are backed up in the same bin. User review of this bin is pending; do not delete it without explicit instruction. Historical report/script paths are original provenance; resolve with the locator or restore dependencies before replay. New experiments belong outside final/.
