## Publication prose policy - 2026-10-19 (current)

The article omits internal project bookkeeping: YAML/Markdown files, local artifact paths, source-code filenames, manifests, checksums and delivery-report inventories. The former Figure and Evidence Reproducibility appendix is removed. Keep scientific methods, operating conditions, evidence boundaries, model/training detail, supplementary figure references and public data/code links in the publication. Technical provenance remains in repository documentation and manifests. Older descriptions below of that appendix are historical.

## Caption export and affiliation cleanup - 2026-10-19 (current)

All six main figure captions are embedded in article/article.tex; all 25 supplementary PDFs include their own captions, with editable caption text in article/supplementary_layout/manifest.json. The duplicate article/figure_captions.tex is recoverably archived under bin/article_affiliation_cleanup_20261019/. Do not regenerate a separate caption export unless the submission portal requests it.

The displayed affiliation is Iran University of Science and Technology, Tehran, Iran. Department and neighbourhood are omitted; city and country are retained. Full postal/contact details may still be requested during submission. Earlier references below to the caption export or longer affiliation are historical.

## Author declarations supplied - 2026-10-19 (current)

The corresponding author supplied the publication declarations: no specific grant, no competing interests, Amir Mohammad Khadem Hosseini responsible for the research/development/analysis/writing and Sattar Mirzakuchaki for supervision. CRediT roles are recorded in the manuscript and publication manifest. The optional acknowledgements section is removed. AI disclosure now covers OpenAI/Codex and Grok assistance for coding, feature combination and final model development, layout/routing/simulation workflows, and manuscript preparation, with author responsibility retained.

Data availability cites https://github.com/st-amirr/EventSpikeSeg and the official DSEC downloads at https://dsec.ifi.uzh.ch/dsec-datasets/download/ plus DSEC-Semantic label information at https://dsec.ifi.uzh.ch/dsec-semantic/. Only DSEC was used for the reported experiments. These links identify the code/documentation repository and external dataset; public release of locally ignored generated checkpoints/GDS/traces has not been verified. Remaining submission checks are postal affiliation/address confirmation, final co-author approval/review, publisher forms, artifact-release coverage and reviewer suggestions. Older pending-declaration notes below are historical.

## Current publication layout policy - 2026-10-19 (supersedes older entries below)

Previously visible interconnect retains its original appearance, including the native bank and full overview. Only routing absent from the earlier exported views is visually subdued. Native views retain all layers within their documented windows. Regional views retain existing hierarchy/spatial cutoffs; internal geometry of collapsed cells remains summarized, while thin routing above the extent cutoff is no longer discarded by width. The GDS and simulation results are unchanged.

The main manuscript is 10 pages. All 25 zoomable sections are separate one-page vector PDFs, with matching SVGs, in `article/supplementary_layout/` (Figures S1-S25). There is no active combined supplementary PDF. Upload individual files; each PDF includes its caption below the vector artwork. The reusable `article/figures/Blocks_figures.pdf` is 5 pages. Keep the full overview embedding rasterized for fast loading. Supplement placement is the author's preference, not a journal page-limit requirement. No separate submission directory is used.

Provenance: `article/figures/native_interconnect_manifest.json` and `article/supplementary_layout/vector_manifest.json`. Reusable rendering sources: `scripts/extract_article_region_vectors.py`, `scripts/extract_article_native_vectors.py`, and `scripts/write_article_layout_vectors.py`; geometry intermediates go under `artifacts/article_work/layout_vectors/`. Extract with KLayout's Python runtime, then write PDFs/SVGs with ReportLab. Historical superseded images remain recoverably archived: 61 assets in `article/figures/old/move_manifest.json`. Author declarations and data availability remain pending.

## Vector actor regions and unused-figure archive - 2026-10-19

All 25 Appendix B actor-region views now embed PDF vector drawings; matching SVG files are supplied in article/figures/layout_sections/. Each PDF and SVG was checked to contain no raster image objects. These are bounded GDS hierarchy/selected-mask views: small cells become extents, and sub-visible thin shapes are omitted. Per-region geometric cutoffs and primitive counts are recorded in layout_sections/vector_manifest.json; original GDS is unchanged. Vector zoom preserves represented edges, not omitted transistor detail. The global overview remains rasterized for fast loading. Documents remain 19 article pages and 13 reusable-figure pages. Both compile without warnings and changed pages were visually reviewed; full article render at 850 pixels took 6.503 seconds.

Moved 49 unused assets, including the former 25 region PNGs, into article/figures/old/ with original relative structure and verified SHA256 hashes. old/move_manifest.json maps every original path to its preserved file. Current manuscript/reusable sources, native device/bank images, required separate Figure_1--Figure_6 exports and active provenance remain in the main figures folder. Updated publication_manifest.json, README, YAML and live provenance paths. Historical path mentions below can be resolved with the archive map. No simulations, GDS changes, staging, commit or upload.

## Consolidated article with integrated layout appendix - 2026-10-19

Current publication files live directly in article/ and article/figures/. The journal guide was rechecked on 19 October 2026: no overall ten-page limit is specified, and supplementary material is encouraged rather than required. The earlier separate layout supplement was an organization choice, not a journal requirement. All 25 actor-region views are now inside article/article.pdf as Appendix B, Figures B.1-B.25. Article: 19 pages; reusable figures: 13 pages. The overview remains rasterized for fast PDF rendering, and vector/GDS originals are preserved. Both builds have no LaTeX warnings; appendix labels and page rendering were verified and visually reviewed.

There is no active article/submission/ folder or separate supplementary document. Highlights, captions and publication_manifest.json are directly in article/; Figure_1 through Figure_6 and component artwork are in article/figures/. The superseded upload package, standalone supplement wrapper/PDF and build intermediates are retained in bin/article_consolidation_20261019/. Original before-change snapshot is artifacts/article_work/article_consolidation_20261019/before_changes.zip. The README and current YAML pointers have been updated. Older dated folder/page-count policies below are historical. Author declarations and public data availability remain pending before submission. No circuit/layout changes, new simulations, staging, commit, or upload were performed.

## Faster overview PDF rendering - 2026-10-19

Replaced embedded hierarchical-vector overview in article/article.tex, Blocks_figures.tex and separate Figure_4 with raster PNG derivatives. Main overview: 2219 x 4400 pixels, 1016 dpi at 110 mm height. Reusable overview: 4286 x 8500 pixels, 1053 dpi at 205 mm height. Original indexed vector PDF/SVG and GDS are retained. Native device/bank views and all 25 regional views are unchanged. Provenance: article/figures/overview_raster_manifest.json. Main overview-page render benchmark at 1100 pixels: 26.620 s before, 0.435 s after. All 10 article pages rendered in 1.793 s and all 13 reusable-figure pages in 5.141 s at 850 pixels. These are local renderer timings, not an in-app viewer latency measurement. The PDFs remain 10/13 pages; article is 2,546,743 bytes and reusable figures 5,084,557 bytes. Changed pages visually checked; LaTeX builds have no warnings. Separate artwork, source ZIP and submission manifest refreshed. No circuit/layout or numerical-result changes.

## Canonical workspace relocation - 2026-10-18

Working source/manuscript destination: `C:/Users/stamir/My Drive (amir76kh@gmail.com)/ELEC/EventSpikeSeg`. Large artifacts remain at `C:/Users/stamir/Desktop/EventSpikeSeg/artifacts`; the destination uses a local `artifacts` directory junction and the existing `.env` artifact path. The junction is local filesystem configuration and is not part of GitHub content. Keep artifact hashes and historical provenance paths intact. Preserve the newer Git history already present in ELEC, and retain the original Desktop Git directories and any replaced destination files under ignored `bin/workspace_move_*/`. The move inventory and integrity report are retained both there and in the Desktop artifacts directory. No staging, commit or GitHub push is authorized by this move.

## Publication labels and layout region atlas - 2026-10-18

Removed internal integration revision labels and raw top-cell identifiers from the published narrative/captions; immutable source identifiers remain in technical manifests. Figure 4 now numbers all 25 actor regions. Supplementary Material S1 (`article/submission/Supplementary_layout_sections.pdf`, 8 pages) supplies separate GDS-derived KLayout views for every region. Source: `article/Layout_sections.tex`; images and provenance: `article/figures/layout_sections/`. Rendering uses eight hierarchy levels, all layers, and independent region scales; deeper cells use bounds. These are regional views, not a claim to resolve every transistor. GDS geometry is unchanged. Native bank/device views remain in the manuscript. The reusable `Blocks_figures` document now has 13 pages; the article remains 10 pages (overview p6, native views p7, transient p8).

Rechecked the Microelectronics Journal guide on 18 October 2026. It does not specify printed ORCID; removed ORCID footnotes and retained IDs as submission metadata. Checked abstract/highlight limits, references, editable sources, embedded PDF fonts, figure captions, supplementary citation, and raster region resolution (at least 1297 dpi at the displayed 94 mm height). Added explanatory-diagram AI assistance disclosure to captions. All three documents build without LaTeX warnings and were visually reviewed. Updated the source ZIP and separate artwork. Author declarations, complete affiliation/postal details, final author approval and public data deposit/citation (or a justified restriction) still require completion before submission. Docker render containers used --rm, no network, 4 GB memory and two CPUs; no render containers remain.

## Microelectronics Journal manuscript policy - 2026-10-18

The active journal target is **Microelectronics Journal**, article type **Original paper**. Use `article/article.tex` with Elsevier `elsarticle` (two-column LaTeX is permitted). The current Figure 1 is editable `article/figures/140k_mejo_vector.tikz`; preserve both older raster illustrations. Keep the full 140k model/training/history material. Describe consumption as simulation-derived and retain the actual error and characterization boundaries. `article/submission/` contains separate artwork, highlights, captions and a source bundle. The journal guide requires a public research-data deposit/citation or justified restriction; local project paths alone do not satisfy that requirement. Author declarations and final human approval remain pending. Older figure/format snapshots below are historical.

## Current article figure policy - 2026-10-15

Figure 1 now uses `article/figures/140k_final.png`, an edit of the original illustration with the final detail8/semantic32-64-128/fusion40-to-16/continuous16-to-6 graph. A/B markers distinguish skip sum and concat. The unmodified original and previous TikZ source are retained, but the historical duplicate is no longer published. Model artwork is illustrative; physical figures must remain derived from actual GDS. Higher-contrast SVG/PNG variants use `_publication`; KLayout panels use `scripts/article_gds_palette.py`. Keep native bank wiring visible and PLIF/injector interconnect hidden as requested. Current scope and review details are in RESULTS and project_spec; older page-number snapshots below are historical.

## ASIC source cleanup — 2026-10-15

`asic/` is retained hardware source/build input; final results remain in `artifacts/analog_asic/`. Archived 38 superseded/provisional/metadata files (171,273 bytes) to `bin/asic_source_cleanup_20261015T115233Z`; 185 original source/configuration files remain. Final GF180 control roots and retained digital tool/test dependencies are preserved; the older parallel scatter source stays because the pw128 wrapper uses it. All 223 original hashes were checked after the move; the README was then refreshed with its original in before_changes.zip. Bin includes inventory, restore script and audit; artifact resolver handles archived original paths. No tests/simulations, permanent deletion, staging or commit.

## Wire-hidden device views and full model figures — 2026-10-15

The user requested regeneration with invisible wiring in PLIF/injector panels and visible wiring in the native 64-state bank. KLayout now hides metal1–5 and via1–4 for panels (a)/(c), with enlarged device windows; bank panel (b) is unchanged. Source GDS files are not modified. Renderer: scripts/render_article_gds_devices.py; source hashes, windows and hidden layer pairs: article/figures/gds_device_manifest.json. These are device-layer illustrations, not complete connectivity views. Full current 140k architecture is restored to the main model section (page 3) as an editable vector TikZ diagram. Original 140k_v4.png is preserved in the appendix (page 8), explicitly identified as the earlier detail32/selector96/spike-count topology. Current model detail8/fusion40-to-16/continuous16-to-6 remains authoritative. Both appear in Blocks_figures.tex. Article: 8 pages; reusable figures: 5 pages; compiled and visually reviewed. No circuit changes or new simulations.

## Model detail preservation and section figures — 2026-10-15

Preserve the detailed 140k model sections when revising the ASIC-focused article. Current topology uses detail8, semantic32/64/128, native40-to-16 fusion and continuous16-to-6 readout; the older 140k_v4.png is historical and must not replace the current topology. Use scripts/render_article_gds_sections.py and article/figures/gds_section_manifest.json for local GDS windows in panels (a)/(c). Cropping does not establish physical compaction or routing optimization. Full-cell views remain retained.

## Canonical docs and article paths — 2026-10-15

Use main `docs/` as the single documentation source. Identical `artifacts/analog_asic/documentation/` copies were moved into the review bin; do not recreate them. The user relocated the analog package to `artifacts/analog_asic/` (no nested `final/`). The path locator supports old final-package paths. Current manuscript: `article/article.tex`; reusable figure source: `article/Blocks_figures.tex`. Actual GDS images and provenance: `article/figures/gds_figure_manifest.json`; regenerate with `scripts/render_article_gds_klayout.py` inside the existing KLayout environment. Script attempts/backups/caches are in `bin/scripts_cleanup_20261014T163508Z/`, with inventory and restore script. 201 original scripts were retained; the new KLayout renderer is an additional utility. No staging, commit or permanent deletion was performed.



## ASIC artifact reorganization — 2026-10-14

Canonical article package: `artifacts/analog_asic/` (start at index.html). Final GDS is `layout/EventSpikeSeg140k_GF180_Analog.gds`; PNG/SVG figures are together in images/; current consumption data is consumption/summary.json. Original manifests/source/results are preserved unchanged under evidence/, components/, model_reference/support locations. The current path locator is `artifacts/asic_artifact_index.json`.

Digital documentation-only snapshots are `artifacts/ASIC/final/` and `artifacts/ASIC_XL/final/`; neither claims a completed digital full-chip layout. Last exports, hierarchy inventory, completed block views and final reports are retained; digital jobs remain paused.

All superseded attempts and build environments moved to `bin/asic_cleanup_2026-10-14_20261014T145109Z/`, including related digital OpenROAD history. No files deleted. cleanup_plan.json inventories every original file; integrity_audit.json accounts for all64,814 originals and verifies SHA256 of all2,779 retained files. restore_artifacts.ps1 can restore original artifact trees; pre-cleanup docs and .gitignore are backed up in the same bin. User review of this bin is pending; do not delete it without explicit instruction. Historical report/script paths are original provenance; resolve with the locator or restore dependencies before replay. New experiments belong in a separate work directory, outside the delivered artifact directories.
## Representative per-element consumption delivered — 2026-10-14

The article layout and representative consumption characterization are complete under the user's clarified scope. `artifacts/analog_asic/results/module_consumption_v1/consumption_summary.json` covers all22 required element/module families, plus native capacitor, sampled decision, bias/normalization kernels and the three shared categorical macro estimates. One physical PLIF core, one3T+MIM resident cell, signed injector, adaptation, inhibition, normalization, readout, access and controls are distinguished. Each transient row states its window and supply energy/power; detailed reports retain input-port accounting. Core beta/decision/reset windows are measurements of the whole core during those phases, not standalone leaf powers.

Coverage combines newly completed native transients, reused complete rail-current traces, native RMS DC/settled samples and explicitly labeled routed-library digital power estimates. Shared1024-state reader power is partition/leaf characterization, not a completed full connected-page power simulation. Bias/reference/phase-generator overhead outside the measured boundary remains excluded unless stated. No measured full-chip power, calibrated behavior or5ms full-population deadline is claimed. Do not sum overlapping modules or replicate shared-core cost per logical membrane. Further circuit optimization is optional.

## Historical consumption task definition — 2026-10-14

The user clarified that per-module simulation means power/energy consumption for one representative instance of each implemented model element: one PLIF core, one membrane storage cell, one signed synaptic injector, beta/threshold/reset, adaptation, inhibition, normalization and class readout, plus their shared access/bias/control circuits. The full article layout is already delivered. Characterize element types once with explicit nominal operating point, activity/load, operation duration, idle/hold power and energy per operation. Do not simulate every replicated instance or restart behavior/calibration/layout improvements as completion gates.

Keep one resident storage cell separate from the shared PLIF update core and shared bank/page reader. Never divide a whole shared module's supply energy by its state capacity and label that a measured single-cell value. Account for driver/reference/programming ports explicitly; VDD alone may exclude energy supplied through other ports. Reuse saved current traces and existing supply results first, then run only missing bounded small-module measurements. Evidence/status: `artifacts/analog_asic/results/module_consumption_v1/consumption_inventory.json`; Representative consumption delivery is now recorded above; this paragraph preserves the task definition.

## Article layout delivered — user scope clarification2026-10-14

V31 is the completed full hierarchical research-layout deliverable under the user's instruction to avoid strict operational acceptance. See `artifacts/analog_asic/assembly/full25_native_controls_v31/article_layout_delivery_v1.json` and ACTIVE_TASKS. All original analog states and implemented modules are included; verified address/event/supply/reference wiring and explicit external research interfaces are documented. Native numerical errors, incomplete full1024-state transient and unproven global5ms timing are reported limitations, not blockers to this layout delivery. Module evidence covers18 completed nominal families plus the page-reader frontend partition. Connected signed-update/commit/5ms-hold evidence is in `results/selected_accumulation_retention_v2/simulation.json`. Further behavioral optimization is optional. Earlier strict flags below are historical; do not infer that the full GDS has not been exported.

## Control and class infrastructure — 2026-10-14

Latest qualified full-population GDS is V30 (`assembly/full25_class_infrastructure_v30/integration_readback_v1.json` under artifacts/analog_asic). All three categorical macro upper VDD/VSS grids are connected to existing rails; actual native M4/M5/VIA4 proofs cover all power-port rectangles. The class-current/readout wrapper has 118 verified boundary escapes and four verified supply/reference joins. V29 failed branch conflict is preserved; V30 moves the conflicting ground via. All source state geometry and existing graphs are preserved. Remaining work is native event/commit boundary controls, driven/observation terminal classification, retained module interfaces and connected per-module accumulation/retention/timing. No jobs live; full layout completion and 5 ms remain unproven. Earlier handoffs below are historical.

## Infrastructure progress — 2026-10-14

V26 is the latest incrementally readback-qualified full-population GDS. V24 added and verified 1,750 boundary terminals; V25 connected 100 analog supply endpoints; V26 connected 100 storage/compute-reference endpoints. Existing V23 address graph and all native state geometry are preserved. Evidence: `artifacts/analog_asic/assembly/full25_analog_references_v26/integration_readback_v1.json`. Remaining categorical/class-current infrastructure, operation interfaces and connected module simulations are listed in ACTIVE_TASKS. No global RC/IR/EM, full layout completion or 5 ms pass is claimed; no jobs are live. Prior handoffs below are historical.

## Current layout handoff — qualified address binding V23, 2026-10-13

Latest readback-qualified full-population GDS: `artifacts/analog_asic/assembly/full25_native_address_routes_v23/eventspikeseg140k_native_address_routes_v23.gds` (536,631,368 bytes), top `ESS140K_NATIVE_ADDRESS_ROUTES_V23`. All 947 controller address nets now physically reach all 1,622 native membrane address/select endpoints. Actual parent-metal graph and native dispatcher-edge checks pass: no opens, aliases, floating pieces, unlanded cuts, foreign/unknown native contacts or native-core intrusions within the checked scope. Complete V19 child geometry, all state identities, 25 spike paths and 3,050 control links are preserved. Combined evidence: `assembly/full25_native_address_routes_v23/independent_readback_v1.json` under `artifacts/analog_asic/`.

Next: finalize supply/reference and external analog contribution/phase interfaces, then connected per-module accumulation/retention/timing simulation coverage. Do not repeat address routing. Full layout completion and 5 ms accumulation are still unproven; no global-wire RC or whole-chip DRC/timing claim. No host or Docker jobs remain live. V20/V21/V22 failed plans are retained. Read the active scope clarification below: only supplied input-event delivery/accumulation has the 5 ms deadline; trained-weight transfer, output completion and hardware mIoU are excluded.

## Latest integration handoff — 2026-10-13

V19 is the latest readback-qualified full-population layout. The 25 spike routes, 1,475 fabric/ingress routes and 1,575 ingress/destination-controller routes are already done. Native 1,622 address/select escapes are also done. Continue with the 947 controller-to-native address nets using assembly/native_address_route_inputs_v1/routing_inputs.json. Do not repeat completed links. The destination ORFS job is completed, archived and removed; no jobs are live. Read ACTIVE_TASKS for scope, evidence and remaining global/analog requirements.

## Latest physical stage — 2026-10-13

V17 full-population GDS now integrates the routed fabric/ingress pair and retains all 25 spike routes, with independent incremental readback passes. Read ACTIVE_TASKS for evidence and scope. Next is destination-to-membrane addressing/control and global infrastructure; do not repeat spike-to-fabric or fabric-to-ingress binding. Trained-weight programming and output accuracy remain outside the completion gates.

## Active scope clarification — 2026-10-13

The user defines this deliverable as an article-suitable analog/mixed-signal implementation of the EventSpikeSeg140k architecture: full physical layout with membrane storage and event-to-membrane accumulation, followed by per-module simulations. The original epoch58 float model defines topology and state identities; QAT is unnecessary.

The 5 ms real-time requirement applies to delivery and accumulation of supplied input events onto their destination membranes. It does not require threshold/output generation, a full layer-to-layer inference pass, or final segmentation within 5 ms. For module timing, state exactly which input event workload and destinations were exercised; do not infer a full-model deadline pass from a small example. Later-layer workloads may be supplied externally for module characterization; this is not autonomous end-to-end inference.

Trained-weight loading, transfer, programming and exact checkpoint weight reproduction are outside the required completion gates. Retain the synaptic contribution/weight-control interfaces and existing physical synapse circuitry: an externally applied analog magnitude/sign is an explicit research interface, not a claim of loaded trained weights. Events must still have physical paths to selected membrane capacitors; removing weight transfer does not remove event fanout, charge injection or membrane access time.

A useful segmentation output, hardware mIoU, PyTorch-equivalent accuracy, calibration optimization and manufacture-ready signoff are not required. Preserve existing threshold/reset/adaptation/readout modules as architecture components and report their connectivity and simulation coverage, without requiring output completion for the accumulation deadline.

Completion requires a real hierarchical full-architecture GDS, inventory and connection/boundary manifest, and per-module simulation results including selected-event membrane accumulation/retention and measured timing. Explicit external interfaces are allowed. Opens/shorts in paths claimed connected remain vital defects. Never call an unconnected placement a functioning full ASIC or claim 5 ms compliance without corresponding evidence.

Next work: integrate the existing packet fabric and ingress/address macros with the membrane-access/injection architecture, expose analog contribution and phase controls, export the full architecture layout, then finish per-module simulations. Do not start trained-weight programming or output-accuracy campaigns. The old 68-decision-service lower bound is not an active completion gate. Existing packet/group lower bounds remain conditional on their supplied workload and assumed delivery architecture; they are not automatically waived or proven satisfied.

This scope supersedes conflicting older requirements below. Existing results and failures remain unchanged. No physical Docker jobs are live.

# Docker storage lifecycle — user instruction2026-10-13

Reuse existing images. Use --rm for bounded foreground simulation containers. For detached ORFS jobs, collect terminal results, archive inspect/logs/exit state with scripts/docker_attempt_lifecycle.py, then remove the stopped container without force or volume deletion. The categorical collector now does this automatically for success andfailure. Archived job evidence replaces container presence; never restart a completed job just because its disposable container was removed. Keep physical source/results and useful failed checkpoints. Remove only proven byte-identical,unreferenced intermediate copies while retaining canonical views; do not delete images,named data volumes or unique results as routine cleanup. No live job may be removed.

# User delivery priority - 2026-10-13

Complete the full layout first, then per-module simulation. Carry existing measured errors. Make only changes vital to connect or operate required blocks; defer behavior/calibration improvements. This user instruction supersedes precision-first stage ordering below. Original full-float analog architecture remains active.

# Current workflow override - 2026-10-10

Read docs/ACTIVE_TASKS.md first, then the relevant evidence only. docs/project_spec.yaml active_workflow is current; dated sections and digital/SKY130 policies below are historical and do not override it. Current prototype is GF180, original epoch58 float, analog state, article-suitable research scope. No QAT/digital membrane fallback or full-model SPICE. Use the experiment/documentation limits in ACTIVE_TASKS; routine work does not require rereading historical specs. Preserve artifacts. No subagents without user authorization.

# Preserved earlier instructions

# EventSpikeSeg Agent Instructions

## Analog synapse decision review — 2026-09-24

Use a signed charge-per-presynaptic-event interface on the active SKY130 prototype. Continue the existing pulse-duration injector as the first candidate; switched-capacitor charge injection is the conditional alternative, not a more inherently SNN-faithful implementation. Do not use pulse-density error feedback across semantic bins or future events. Weight determines a connection's contribution; it does not independently set presynaptic firing frequency. Internal subpulses are implementation phases, not extra network spikes, and must finish within the same update.

The primary analog reference is the best-validation full-float 140k seed-17 checkpoint from the 80-epoch run: `artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt`, epoch 58 / best epoch 58, `is_best=true`, SHA-256 `c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7`. The epoch-80 checkpoint is a comparison only (`is_best=false`). Verify metadata/hash before use. The analog path uses the checkpoint's ordinary float inference parameters; QAT, Q7.16 exports and quantized references are not needed and must not define analog precision or acceptance. Float32 storage does not require float32 analog accuracy.

At the update boundary, reproduce the model's signed weighted sum, learned beta, threshold/reset, inhibition and adaptation order. For this float PLIF, charge is `candidate = beta * previous_post_reset_state + summed_current`; apply beta once. Preserve the float path's subtractive reset, affine gain and any offsets, including when no presynaptic spike arrives. Hold uncommanded leak sufficiently small during accumulation and threshold only after all contributions arrive. Raw-event ingress may have multiplicity; do not reduce it to binary hidden-layer semantics.

The bin-based contract means finite pulse duration is not automatically less faithful than a capacitor packet: integrated signed charge and completion before the 5 ms boundary are decisive. Charge delivery, saturation, uncommanded droop and order effects must still be measured. Preserve all digital/XL artifacts and keep their campaigns stopped; no new Markdown files or full-model SPICE campaign.


## Full analog implementation delegation — 2026-09-23

The user authorizes the full analog/mixed-signal workflow, including design, debug, per-module simulation, physical macro generation, full assembly and ORFS execution once readiness passes. ASAP7 is not mandatory: evaluate another PDK where it is a better fit, and keep technology-specific comparisons clearly separated. `docs/ACTIVE_TASKS.md` is the authoritative staged task plan. Earlier Grok-test-only and blanket no-ORFS instructions are superseded. Keep digital/XL jobs paused and all artifacts preserved. Use existing docs and YAML only. Approximate research estimates are allowed with explicit evidence/coverage; full layout still requires real implemented macros and validated assembly.


## Active approach override — 2026-09-23

User authorized analog/mixed-signal 140k feasibility as the active approach. Follow docs/ARCHITECTURE.md and write outputs to artifacts/analog_asic. Digital-only/register-state rules below now describe the preserved digital fallback, not restrictions on this analog experiment. Analog approximations and scaled estimates are allowed with explicit limitations; distinguish ideal, schematic, extracted and full-chip evidence. Preserve all digital/XL artifacts and keep their jobs paused. Prior active work is in docs/PROGRESS.md.


## Mission

## Preserved digital fallback target policy — 2026-09-21

The epoch-80 target statement below is the preserved digital ASIC baseline. The active analog experiment uses the best-validation epoch-58 full-float checkpoint specified above and in `docs/ACTIVE_TASKS.md`; do not apply the digital QAT/quantization contracts below to analog design or acceptance.

All primary ASIC layout, block simulation, power, area, timing, and inventory work is based on **EventSpikeSeg140k v8, epoch 80, seed 17**: six classes, 440x640, 25 permanent PLIF actors, 54 graph edges, 30,976,000 resident PLIF identities, and 143,824 deployed synaptic weights. Primary exports/results live under `artifacts/ASIC/`; the latest accepted small gate-simulation results are in `artifacts/ASIC/primitive_characterization/`.

**EventSpikeSegXL is secondary/reference work.** Preserve useful accepted XL GDS/LEF/Liberty views, final routed ODB/DEF/netlist/SDC/SPEF files, checkpoint-specific constants, hierarchy catalogs/instance maps/preflight, and validation/power reports. Keep them under `artifacts/ASIC_XL/` and their existing named OpenROAD result directories. Retain the latest useful unfinished-run database and failure summaries; redundant intermediate databases and rebuildable simulation binaries need not be retained. Never relabel XL measurements or its 44-actor inventory as 140k results. Reuse an XL physical view for 140k only after proving matching RTL, constants, geometry, interfaces and constraints.

XL physical expansion remains paused behind 140k work. Preserve independent XL training and checkpoints. Neither model has a completed full-chip layout; existing routed blocks and structural hierarchy data must be labeled accordingly. Current work uses small per-block simulations and extracted-layout measurements; whole-model simulation remains retired. Historical entries below retain their original model and date and do not change this priority.


Build and validate `EventSpikeSeg140k` for six-class DSEC at `440x640` as the primary
custom digital-neuromorphic ASIC target. Keep the eleven-class `EventSpikeSegXL`
model and its useful physical implementation evidence for secondary work.
Training remains PyTorch + SpikingJelly; deployment is a custom ASIC described directly in
synthesizable SystemVerilog, with Icarus/cocotb and Yosys/OpenROAD as the open verification
and PPA path.

## Source-of-truth order

1. `project_spec.yaml`
2. `AGENTS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DECISIONS.md`
5. tests and executable code

For operational state and task handoff, read `docs/ACTIVE_TASKS.md` after the sources
above, then inspect `docs/PROGRESS.md` and the referenced machine-readable status files.
Update `docs/ACTIVE_TASKS.md` whenever a long-running process starts, completes, fails,
or changes the next valid stage. Do not infer active work from container names alone.

Python constructors/forward methods remain authoritative if older diagrams disagree.

## Canonical naming and frozen graph

- `EventSpikeSeg140k`: validated baseline ASIC target; 149,835 registered parameters for
  six-class, two-polarity DSEC.
- `EventSpikeSegXL`: second ASIC target; 979,179 registered parameters for eleven-class,
  two-polarity DSEC. Epoch 1 is a structural/constants bring-up checkpoint, not a final
  accuracy checkpoint; regenerate its constants from the selected trained/QAT checkpoint.
- Deployable 140k inference: 149,423 executed parameters, 143,824 synaptic weights,
  25 Conv/ChannelAffine/PLIF populations, and one temporal class-current readout.
- The 140k export omits dead `refine2`, training-only `aux_head`/`boundary_head`,
  surrogate gradients, and XL-only modules.
- XL deployable inference has 968,831 executed parameters, 959,824 convolution weights,
  44 PLIF populations, four learned attention thresholds, and one 24-to-11 current readout.
  Omit `aux_head`, `deep_aux_head`, and surrogate-gradient-only behavior.

## Exact inference semantics

A learned `SpikingStage` is `SpikingJelly Conv2d (synapses) -> optional ChannelAffine ->
ParametricLIF -> binary spikes`. Convolution kernels are synaptic weights; the output
feature-map elements are PLIF neurons. DW/PW blocks contain two distinct PLIF
populations and must not be collapsed.

Hardware deployment implements the frozen executed 140k inference graph only. Hidden
layers are binary-spiking; the final 1x1 synapse accumulates continuous signed class
current over the ten updates and does not allocate class PLIF state.

## PLIF digital ASIC mapping contract

Per output channel, `beta=sigmoid(beta_logit)` and threshold are learned. Spatial
neurons keep individual membrane state. Software charge is equivalent to
`candidate = beta * membrane + current` before dynamic threshold/reset effects.

ASIC values are fixed-point numerical SNN states, not physical volts/amps. Both targets use
weight, beta, threshold, membrane, accumulator, adaptation, rounding, saturation, and
overflow formats in the integer export contract. The baseline must preserve the learned
per-channel beta with a quantized coefficient. Shift-only/power-of-two leak is an
optional optimization only after bit-exact and semantic-accuracy revalidation.

## Logical resident-state accounting rule

Do not infer neuron-state capacity from parameter count. The 25-population 140k graph has
30,976,000 logical accumulator/membrane identities and 10,982,400 adaptation-enabled states at DSEC
`440x640`. Every logical PLIF owns one signed int32 Q15.16 combined accumulator/state element. During a
bin it contains the pre-leaked membrane plus accepted current; completion thresholds/resets it and
pre-applies beta for the next bin. Static weights use signed Q7.16 in 24 bits, membrane and
threshold use signed Q7.16 in 24 bits, and beta uses unsigned UQ1.23. Enabled adaptation stores a
6-bit integer-bin age and a 19-bit unsigned Q3.16 amplitude. This is 150.89 MiB-equivalent of
logical state, but it is
distributed register/latch state rather than an addressed byte store. There is no last-bin tag,
touched queue, SRAM fetch, or writeback. Full-chip PPA must measure this resident design.
The 44-population XL graph has 78,707,200 logical membranes and 15,910,400
adaptation-enabled states, totaling 347.66 MiB-equivalent under the same widths.

Each actor owns resident local state across its spatial/channel destinations and may
not lend that state or compute identity to another layer. It must never alias logical
membrane identities from different channels, positions, or layers. The combined element becomes
the pre-leaked state for the next bin at commit; combined accumulator/adaptation state survives
events and consecutive records until the
documented reset boundary.

## Digital neuromorphic ASIC deployment rule

The primary runtime is fully digital but must preserve neuromorphic/SNN execution:

- PLIF combined accumulator and adaptation state persist in local fixed-point elements;
- hidden binary spike pulse/vector bits gate compile-time fixed weights;
- convolution remains fixed local synaptic connectivity and skips unasserted inputs;
- elastic pulse/vector routing carries only emitted binary activity between stages;
- clock-enable/inactivity suppression should be used where safe;
- CPU/GPU dense inference is absent from the deployed learned feature path.

### Static actor execution rule

Instantiate one permanent actor for every executed PLIF population (25 for 140k, 44 for XL).
**Each actor tuple is only a topological export order, never a linear pipeline.** Each actor owns its convolution address generator,
accumulator lanes, PLIF/mechanism unit, output FIFO, and initialized local weight ROM.
Cross-layer compute sharing, layer reconfiguration, and partial reconfiguration are forbidden.
The interconnect is compile-time fixed: input/detail-semantic forks, residual binary-OR joins,
`x1`/`x2` skip fanout, decoder upsample/concat, multiplicity-preserving `project2+x1`, and
late semantic/detail concat. Common clock/reset and final readout may be shared infrastructure.
Every logical spatial PLIF owns one physical register/latch combined accumulator element; enabled
adaptation fields are local to that PLIF. This direct-state rule is intentional.

### Exact autonomous actor execution order

DSEC ASIC inference must match the trained fixed 5 ms time grid while streaming live input.
Raw rectified events enter sequentially in timestamp order and immediately cause only their
connected signed-weight additions; no dense tensor or complete 5 ms bin is loaded. Within
an epoch, actors run autonomously using ready/valid spike traffic. An ordered completion
token follows the final presynaptic event. Tokens follow the **same DAG as spikes**: fanout
nodes duplicate them to every branch, and residual/skip/concat joins may forward one
downstream token only after all required upstream tokens carry the same 24-bit bin tag.
Only then may the downstream actor know that every contribution for that bin has arrived.
This is logically asynchronous actor dataflow, but the current RTL is clocked and makes no
electrically clockless/QDI claim. Never threshold after each signed tap contribution.

For a 3x3 convolution, the nine tap connections gate their compile-time signed weights from
asserted presynaptic pulse bits into the canonical postsynaptic current element. A tap is a
synapse projection, not a separate PLIF and not a membrane copy. Stride is fixed connectivity,
not a dense sliding scan.

### Natural mappings

- Conv weights -> compile-time signed fixed-point constants/wires
- binary hidden spikes -> pulse/vector bits that gate weight additions
- PLIF beta -> quantized per-channel leak coefficient
- learned threshold -> quantized per-channel comparator threshold
- combined accumulator/compact adaptation -> register/latch-resident per-PLIF state
- ChannelAffine -> fold into quantized weight/scale
- concat -> channel-ID routing
- nearest upsample -> spike-address fan-out
- quarter skip concat -> channel-ID routing into one 1x1 fusion accumulator
- half skip sum -> preserve coincident event multiplicity rather than OR-dedup
- class current accumulation/argmax -> signed accumulators/comparator

### Mapping risks requiring explicit validation

- stem peer-membrane inhibition uses retinotopic cross-channel membrane energy;
- encoder/context triangular threshold adaptation uses age/amplitude and a dynamic threshold;
- final readout is 16->6 for 140k and 24->11 for XL, using signed current accumulation over all ten updates;
- XL attention is fully spiking: four eight-channel Q/K coincidence popcounts compare
  exported Q7.16 thresholds, gate V spikes, and feed a spiking 1x1 output actor plus residual OR;
- DSEC PLIF decay advances in fixed 5 ms steps, with 5 ms as the
  learned-beta reference interval;
- every resident PLIF receives exactly one learned-beta update at each 5 ms completion, so no
  microsecond timestamp or `last_bin_tag` is stored.

Do not silently replace these. If hardware cannot reproduce them, define an explicit
hardware-compatible approximation and revalidate/fine-tune accuracy.

## Input contracts

DDD17 uses the 50 ms statistic scheduler and is an approximation because raw tuples are
unavailable. DSEC uses exact raw rectified events and bypasses the moment scheduler. GPU
training accumulates events into fixed physical-time divisions; the ASIC ingress accepts the
camera stream directly and does not store those training divisions as input bins.

## Verification

For the ASIC target, preserve this staged golden comparison:

1. SpikingJelly floating-point trained model
2. exported bit-exact fixed-point integer reference
3. SystemVerilog unit/full RTL simulation with Icarus and cocotb
4. Yosys synthesis and technology mapping
5. OpenROAD placement/routing, parasitic extraction, timing, and representative-event VCD/SAIF power
6. later test-silicon measurement

Compare layer currents, membrane trajectories, adaptation, hidden spikes, signed class-current accumulators, semantic
accuracy, latency, and overflow/saturation behavior. ASAP7 is predictive research PPA,
not tapeout signoff. Full-chip PPA is invalid until the complete native resident graph—not a
reduced actor or superseded SRAM reference—is placed, routed, timed, and activity measured.

## Secondary XL physical estimation and artifact preservation

Keep XL checkpoint-specific exports below
`artifacts/ASIC_XL/checkpoint_exports/<checkpoint-purpose>/`; do not create new
top-level `artifacts/ASIC_XL_*` siblings. Preserve differing checkpoint constants
as separate exports rather than merging or deleting them.

The retained secondary XL physical hierarchy retains logical 8x8 grouping but uses 1x1
physical leaves for every actor because 8x8 and 4x4 exceeded 20 GiB during mapping
and 2x2 exceeded 20 GiB during detailed routing. Regenerate the catalog, instance
map, wrappers, macroized top, and preflight together after any partition change.

For early feasibility, characterize one routed, activity-measured physical instance
of each block class and write results below the target's
`primitive_characterization/` directory. Scale only with the exact physical-instance
inventory and report measured coverage and uncertainty. Do not run or reconstruct a
whole-model simulation for either target. Full-chip layout still requires all catalog
views and top-level placement, routing, extraction, timing, and physical checks.


## Autonomous 5 ms DSEC runtime rule

Live DSEC input retains 5 ms semantic epochs. Events and ordered completion tokens propagate through the complete permanent **25-PLIF DAG** without a global actor scheduler. The input stream forks to `detail_stem` and `stem`; `x1` and `x2` each fan out into deeper encoder and later decoder routes. Residual joins binary-OR/deduplicate coincident pulse bits, whereas the `project2+x1` decoder merge must preserve multiplicity. Every multi-input join waits for all same-bin completion tokens before forwarding completion. PLIF/adaptation state persists across epochs and predictions. Every resident PLIF applies one learned-beta step per completion; there is no touched-state tag. All contributions to a layer/bin accumulate before one threshold/reset commit.

Prediction cadence is configurable, with **10 bins = 50 ms = 20 Hz** as the starting point to match training. Measure cycles/bin after implementation. Define `U = C_bin/(f_clk*0.005)` and `H = 1/U`. Hard sustained real time requires `U<=1` / `H>=1`; the starting design target is `U<=0.8` / `H>=1.25`. At 100 MHz this means 500,000 hard cycles/bin and 400,000 target cycles/bin.

## Active autonomous RTL interfaces

`resident_convolution_synapses` implements fixed standard/grouped/depthwise connectivity in
PyTorch Conv2d weight order. `streaming_resident_channelized_plif_actor` connects bitmap pulse
traffic to ordinary or retinotopic resident populations. `resident_event_ingress_adapter`
preserves raw-event multiplicity for the two ingress actors. Resident vector offset, upsample,
union, edge, fork, and join primitives implement the fixed DAG, and
`resident_temporal_class_readout` holds signed class currents locally. Older scalar scatter,
banked, and SRAM actors are temporary equivalence references pending resident graph equivalence.

## Active fixed-step RTL interfaces

The resident baseline has no sparse-state entry, state address, or timestamp. Each PLIF consumes
its exported learned per-channel beta once per 5 ms completion. Do not reintroduce a fixed-record
25-layer controller: runtime is the autonomous static DAG with ordered completion-token
rendezvous. The parameterized final resident readout uses signed current accumulation across the configured
prediction window plus first-index-tie argmax; do not create output PLIFs or class-spike counting.
