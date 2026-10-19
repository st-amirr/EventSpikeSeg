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

## GitHub README and checkpoint evidence - 2026-10-18

Refreshed README for https://github.com/st-amirr/EventSpikeSeg with the current GF180 analog/mixed-signal research scope. Read both local checkpoints with torch.load(weights_only=True), without evaluation: epoch80 validation mIoU = 0.27095654606819153; best mIoU = 0.27976271510124207 at epoch58. Best pixel accuracy = 0.6693825125694275. Tracked evidence: docs/checkpoint_metrics.json, including hashes, per-class metrics, and the 234-record zurich_city_02_a validation split. The selected best checkpoint remains the original float analog reference. The article already reports its 27.976% software mIoU. No hardware accuracy claim, training, simulation, commit, or push was added.

## Publication labels and layout region atlas - 2026-10-18

Removed internal integration revision labels and raw top-cell identifiers from the published narrative/captions; immutable source identifiers remain in technical manifests. Figure 4 now numbers all 25 actor regions. Supplementary Material S1 (`article/submission/Supplementary_layout_sections.pdf`, 8 pages) supplies separate GDS-derived KLayout views for every region. Source: `article/Layout_sections.tex`; images and provenance: `article/figures/layout_sections/`. Rendering uses eight hierarchy levels, all layers, and independent region scales; deeper cells use bounds. These are regional views, not a claim to resolve every transistor. GDS geometry is unchanged. Native bank/device views remain in the manuscript. The reusable `Blocks_figures` document now has 13 pages; the article remains 10 pages (overview p6, native views p7, transient p8).

Rechecked the Microelectronics Journal guide on 18 October 2026. It does not specify printed ORCID; removed ORCID footnotes and retained IDs as submission metadata. Checked abstract/highlight limits, references, editable sources, embedded PDF fonts, figure captions, supplementary citation, and raster region resolution (at least 1297 dpi at the displayed 94 mm height). Added explanatory-diagram AI assistance disclosure to captions. All three documents build without LaTeX warnings and were visually reviewed. Updated the source ZIP and separate artwork. Author declarations, complete affiliation/postal details, final author approval and public data deposit/citation (or a justified restriction) still require completion before submission. Docker render containers used --rm, no network, 4 GB memory and two CPUs; no render containers remain.

## Microelectronics Journal editorial review - 2026-10-18

Final delivery check (18 October 2026): rebuilt and visually reviewed the 10-page manuscript and 5-page reusable figures; corrected GDS-to-PDF coordinate precision. Editable source bundle and submission_manifest.json are in article/submission/. Abstract, highlight lengths and citation keys checked; no LaTeX warnings. Author declarations/data deposit remain pending.

The manuscript has been adapted to the publisher's live Guide for Authors (https://www.sciencedirect.com/journal/microelectronics-journal/publish/guide-for-authors), read on 18 October 2026. Original-paper format: `elsarticle`, numbered decimal sections, numeric citations in first-appearance order, abstract under 250 words, seven keywords, four highlights of at most 85 characters. Required data/funding/conflict/AI sections and an author-contribution field are included; unknown declarations remain visibly marked.

Reviewer changes: clarified simulation versus silicon evidence; defined PLIF symbols, MIM and graph terminology; stated the charge/capacitance relation without claiming calibrated weight transfer; reordered figure first mentions and bibliography; added DYNAPs/Braindrop circuit context; updated SpikingEDN, SLTNet and EvSegSNN publication references; preserved all model/training/history details. Architecture is an editable vector diagram; overview and waveform PDF exports preserve existing source geometry/data. Six separately named artwork PDFs and editable sources/captions are in `article/submission/`. Existing numerical results and GDS remain unchanged.

Author metadata supplied: Amir Mohammad Khadem Hosseini, am_khadem@alumni.iust.ac.ir, ORCID 0009-0001-8347-9410; Sattar Mirzakuchaki, m_kuchaki@iust.ac.ir, ORCID 0000-0003-0232-9267 (verified against the public ORCID record with verified iust.ac.ir domain). The user identifies as an MSc graduate; no current student appointment is asserted.

This is an author-requested editorial review, not independent journal peer review. Remaining scientific limitations are explicitly reported. Remaining submission items are documented in ACTIVE_TASKS and YAML; no claim of submission readiness until author declarations and data availability are complete.

## Article review and figure evidence - 2026-10-15

### Addressed in the manuscript

| Reviewer issue | Revision and evidence |
| --- | --- |
| Main architecture used an unwanted visual style; historical image had stale topology | Corrected original-style `140k_final.png` is Figure 1; native detail8, skip sum/concat, fusion40-to-16 and continuous16-to-6 are shown. Original asset and previous vector reference retained. |
| Full implementation overview missing from main article | Figure 4 uses the delivered V31 GDS-derived SVG hierarchy, with unchanged placement and fixed small-cell extents. Source GDS SHA256 remains `fb28eeb6bbc8901ad8594dcd4b5cc14450b7cae438bd5f239096c587f96d1d92`. |
| Layout colors weak on paper | Added white-background/darker `_publication.svg/.png` exports; SVG definition coordinates/paths/transforms are unchanged. Native KLayout renders use the shared publication palette; bank wiring retained. |
| Signed update/retention described only as scalar results | Figure 6 plots the saved 2,360-sample binary trace. It reproduces 0.531097 mV drift over 5 ms. Restore70-80us, beta85-85.5us, positive pulse97-102us, negative pulse110-113us; commit baseline230us. |
| Nominal conditions and evidence types unclear | Added typical GF180, 3.3 V, 27 C; external fixture and local capacitance boundaries. 74 rows: 59 per-instance transients, 6 reused transient supplies, 3 DC, 3 settled samples, 3 routed-library estimates. |
| Logical state total not decomposed | 30,976,000 membranes + 10,982,400 age + 10,982,400 amplitude + 1,689,600 class-current identities = 54,630,400. |
| Storage discussion used superseded capacitor geometry | Final 5x5um plate gives 774.4mm2 for membrane plates alone. 100.32x99.90um bank /64 =156.59325um2 per state; membrane-bank replication reference4850.632512mm2, excluding other state/peripherals. This is not measured final die area. |

### Interpretation and remaining author work

Native device and bank panels are direct KLayout GDS renders. The full view is a GDS-derived hierarchy rendering with fixed simplified extents, not a fully resolved mask plot at arbitrary zoom. Only one full-layout export was found in the current project; no cleaner earlier physical placement was substituted. The 1438.228445x2928.936410mm atlas envelope is a spacious database arrangement, not a reticle-sized die claim. The detailed 140k model/training/search material remains intact.

The reviewer pass is based on local source data; it is not an independent literature or silicon validation. The manuscript retains commit/coupling errors, the incomplete full1024-page transient, unqualified PVT/mismatch robustness, global timing/power, and hardware mIoU as evidence limits. Author affiliation, email, acknowledgments and funding details still need author input. No unsupported measurement or performance comparison was added.

Provenance: `article/figures/article_review_figure_manifest.json`, `architecture_image_provenance.json`, `gds_figure_manifest.json`, `gds_device_manifest.json`; saved review audit: `artifacts/article_work/reviewer_delivery.json`.

## Wire-hidden device views and full model figures — 2026-10-15

The user requested regeneration with invisible wiring in PLIF/injector panels and visible wiring in the native 64-state bank. KLayout now hides metal1–5 and via1–4 for panels (a)/(c), with enlarged device windows; bank panel (b) is unchanged. Source GDS files are not modified. Renderer: scripts/render_article_gds_devices.py; source hashes, windows and hidden layer pairs: article/figures/gds_device_manifest.json. These are device-layer illustrations, not complete connectivity views. Full current 140k architecture is restored to the main model section (page 3) as an editable vector TikZ diagram. Original 140k_v4.png is preserved in the appendix (page 8), explicitly identified as the earlier detail32/selector96/spike-count topology. Current model detail8/fusion40-to-16/continuous16-to-6 remains authoritative. Both appear in Blocks_figures.tex. Article: 8 pages; reusable figures: 5 pages; compiled and visually reviewed. No circuit changes or new simulations.

## Model detail preservation and section figures — 2026-10-15

Article presentation update only: detailed model topology/training/search history retained; native PLIF state/threshold, reset, decision and injector source/TG windows replace long-wire full views in panels (a)/(c). Cell geometry and all reported circuit measurements are unchanged. Provenance is article/figures/gds_section_manifest.json. The bank remains a full native 8x8 component view. Physical compaction/routing optimization is not claimed.

## Article layout delivered — user scope clarification2026-10-14

V31 is the completed full hierarchical research-layout deliverable under the user's instruction to avoid strict operational acceptance. See `artifacts/analog_asic/assembly/full25_native_controls_v31/article_layout_delivery_v1.json` and ACTIVE_TASKS. All original analog states and implemented modules are included; verified address/event/supply/reference wiring and explicit external research interfaces are documented. Native numerical errors, incomplete full1024-state transient and unproven global5ms timing are reported limitations, not blockers to this layout delivery. Module evidence covers18 completed nominal families plus the page-reader frontend partition. Connected signed-update/commit/5ms-hold evidence is in `results/selected_accumulation_retention_v2/simulation.json`. Further behavioral optimization is optional. Earlier strict flags below are historical; do not infer that the full GDS has not been exported.


## Article background: restored quantitative experiments

Restored from the [committed Markdown snapshot](documentation_history/article_markdown_HEAD_4fd2e5e93257_20261014T155300Z.zip), commit `4fd2e5e93257`, on 2026-10-14. Historical experiments below retain their original scope; the current delivery is specified by `article_final_implementation` in [project_spec.yaml](project_spec.yaml).

These are development experiments and analytical estimates, suitable for methods discussion or supplementary material. Final layout and representative consumption results remain those in `artifacts/analog_asic/`; these historical measurements must not be presented as final-chip PPA or hardware mIoU.

### Storage capacity and service arithmetic — 2026-10-08

For the earlier native 7 × 7 micrometre MIM candidate, one plate per 30,976,000 membranes gives `30,976,000 × 49 / 1,000,000 = 1,517.824 mm²` of plate area. Differential pairs double that plate-only estimate. It excludes 10,982,400 adaptation-enabled states, access devices, shared peripherals and routing. Repeating isolated cell bounding boxes gave 3,124.23936 mm²; that is not an optimized array-area minimum. Neither value is the area of the final 5 × 5 micrometre MIM implementation or the delivered atlas.

Servicing every membrane once per 5 ms would require 6.1952 billion state updates per second before additional event and graph work. The historical analysis also considered a hypothetical 300 mm² allocation: half for membrane plates allowed 4.84246 µm² per state, while one quarter for the then-current feedback plates allowed an optimistic 3.12659 µs serial service slot. The measured 25 µs encoding phase of that candidate already exceeded the slot before reset/event/restore overhead. These conditional calculations motivated sharing and topology exploration; they do not establish a final throughput result or an unavoidable service requirement for every alternative schedule.

Source: the corresponding historical section in the committed Markdown snapshot linked above.

### Original-float software sensitivity to state noise — 2026-10-08

The archived screen injected independent state noise into original-float full-frame, writeback-every-bin software replays. With 274.199 µV noise and actor-based voltage ranges, record 0 present-class IoU fell from 0.205726 to 0.04618–0.04864. Ideal per-channel ranges improved the noisy result to 0.11872–0.11984. Record 1 fell from 0.198918 to 0.05807–0.06123 under actor-based ranges.

These are selected-record software sensitivity experiments with optimistic per-record scaling, not validation-set mIoU, transistor sampled-noise measurements, or accuracy results for the final ASIC. They demonstrate why voltage range and analog error must be evaluated together; float32 training or a Q7.16 export alone cannot specify required analog precision. The old entry announcing a 100 µV follow-up run is not a completed result and is deliberately excluded here.

Source: `docs/ARCHITECTURE.md`, “Linear state-noise tolerance screen”, in the committed snapshot linked above; related detailed experiments are in the archived RESULTS file.

### Tracking-parking calibration and state dependence — 2026-10-09

One feedback bank with external PROGRAM calibration converged in three iterations to +312.750/−369.530 µV, against targets of +312.749915/−369.523326 µV. Reversing event order at zero state gave a maximum target error of 0.050674 µV. This did not remove the approximately 4.9 µV bias observed with a nonzero membrane state.

Four native nine-MIM feedback banks reduced measured state-dependent packet variation to at most 1.275 µV in the completed negative 20 ns and positive 10 ns cases, each compared with its matching zero-state control. Four-bank tests inherited the one-bank programming; reset target errors were approximately 4 µV. The 1.275 µV value is relative state dependence, not total weight error, sampled noise, all-weight precision or model accuracy. Systematic event error can accumulate.

The archived audit covered six completed/rejected cascaded-loop cases, seven completed isolated-source diagnostics and 29 integrated reports (22 complete and seven incomplete), plus three pre-simulation netlist rejections. These counts describe the diagnostic campaign, not the final 22-family consumption coverage.

Source: the corresponding historical section in the committed Markdown snapshot linked above.

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

# Evidence and current results





Updated 2026-10-13. This page owns decision-relevant numerical conclusions. Current jobs/next steps: [ACTIVE_TASKS](ACTIVE_TASKS.md). Exact earlier summaries are archived through [PROGRESS](PROGRESS.md); raw reports remain unchanged.





**Overall:** reusable module layouts and limited original-float replays exist. Complete PLIF, original-model accuracy acceptance, full-population 5 ms service and full-chip layout remain unaccepted.


## Extracted signed event plus state/update cell composition - 2026-10-13

The extracted routed `gf180_signed_weight_charge_parent_v2` and extracted routed `gf180_nf_state_update_aux_overlap` netlists were composed in SPICE with the injector STATE node wired to the native membrane MIM state. At the same 1.5V magnitude command, TT27 produced +22.62mV for positive (`SIGN=0V`, `PPROGRAM=2.7V`) and -21.10mV for negative (`SIGN=3.3V`, `NPROGRAM=0.45V`). Absolute event-step ratio is1.072. The negative branch must use a full 3.3V logic high: the earlier 1V setting left the positive path selected. After the auxiliary BETA phase, the state moved +8.75mV / +10.10mV, then drifted -7.81mV / -7.92mV through5ms. These tests show comparable signed event transfer and 5ms state hold in the composed extracted circuit, while the beta edge itself adds a noticeable offset.

This is still a SPICE composition of two extracted module netlists, not a combined physical parent layout. It uses fixed analog weight/current biases rather than the calibrated 490,240-bank scale table, and does not include float-derived weights, the full PLIF recurrence, PVT/noise/mismatch, or population throughput. Accuracy and full-chip layout remain open. Evidence: `artifacts/analog_asic/results/gf180_signed_charge_state_update_integrated_v1.json`; benches/scripts: `artifacts/analog_asic/benches/gf180_signed_charge_state_update_v7.spice`, `...v14.spice`, `scripts/simulate_gf180_integrated_signed_charge_state_update_v7.py`, `...v14.py`.

## Direct float-state-to-capacitor-voltage mapping and scale calibration - 2026-10-13

The direct mapping is the selected state representation and is already defined in `membrane_voltage_scale_manifest_v2.json`: each guarded local float interval maps linearly onto 0.75–2.55 V around 1.65 V using Vstored=1.65+0.9*state/range. One shared scale serves each (actor, channel, 8x8 tile) bank. This preserves the original float state variable by an affine conversion; the synaptic update, threshold, reset, inhibition, adaptation and readout must use the same scale. Voltage-endpoint mapping alone does not prove those circuits preserve the recurrence.

The generated v5 table covers 490,240 bank scales, a 12,151:1 ratio. Its 81-point extracted 5ms transient check measured max absolute current error 0.1505% and max held-state error 0.0433mV. A first-order v6 correction derived from that residual was independently checked at 81 points: max relative current error 0.00235%, mean 0.000411%, max held-state error 0.0702mV. These are nominal TT27 cell-level results, not full recurrence, PVT, noise or mismatch qualification.

Full-float software replay was run on all eight saved validation records. All baseline prediction hashes match the epoch58 checkpoint. Applying the measured v6 per-bank current residual as a per-update multiplier changes 28.96% of pixels on average (28.38–30.11%) and raises mean IoU from 0.19679 to 0.20906 (+0.01226). The perturbation replay is an intentionally limited sensitivity surrogate: it does not instantiate the capacitor dynamics or analog update path. Prediction changes remain large despite the small cell residual; interpret this as evidence of a highly sensitive thresholded recurrence and keep accuracy acceptance open. On record0, scaling the measured residual by another factor of0.001 (maximum injected current error about2.35e-8 relative) still changes28.54% of pixels and gives nearly the same mIoU. This indicates the software replay is extremely threshold-sensitive; it cannot serve as a direct estimate of analog accuracy. Evidence: `artifacts/analog_asic/results/gf180_membrane_scale_v23_replay_sensitivity_probe_v1.json`.

Evidence: `artifacts/analog_asic/results/gf180_membrane_scale_v23_bank_calibration_v5.json`, `...v5_validate81pt_batched.json`, `...v23_bank_calibration_v6.json`, `...v6_validate81pt_batched.json`, `...transfer_replay_summary_v3.json`. Scripts: `scripts/calibrate_gf180_membrane_scale_v23_bank_ranges_v6.py`, `scripts/simulate_gf180_membrane_scale_v23_bank_map_v6_validate81pt_batched.py`, `scripts/replay_gf180_membrane_scale_v23_transfer_error_v3.py`.





## GF180 membrane bank-scale hardware requirement - 2026-10-13





The measured-range manifest maps490,240 analog scales for30,976,000 membrane states (one shared scale per up-to-64-state bank). Required bank scale spans12,151:1, while the existing characterized pulse-duration command window spans60:1, so pulse width alone cannot directly implement the range map. The maximum sampled8.238mV storage round-trip error equals0.915% of a bank signed half-range; expressed in model units, its absolute value grows with that bank’s range.





The first candidate to screen is a bank-held analog log(scale) voltage feeding a shared weak-inversion scale-current generator and current-domain update multiplier. A cascaded switched-capacitor range/fine stage is the fallback if the low-end current or gain error fails. Both remain hypotheses pending an extracted minimum/median/maximum transfer test. This analysis does not qualify the scale storage, multiplier, complete recurrence, original-float accuracy, or5ms service.





Evidence: `artifacts/analog_asic/results/gf180_membrane_scale_hardware_requirements_v1.json`; range manifest: `artifacts/analog_asic/assembly/membrane_voltage_scale_manifest_v2.json`.





## GF180 membrane scale-control circuit screen - 2026-10-13





A routed GDS-qualified inverse OTA and its extracted resistor amplifier were driven from a native GF180 poly-resistor divider to convert a log-scale control voltage into a PFET scale current. The first high-impedance divider result is invalid for transfer accuracy because its output is loaded by the amplifier input. A lower-impedance divider plus90us per-level settling gives measured current ratios min/median203.964:1, median/max65.474:1, and min/max13,354.45:1 against targets186.652:1,65.102:1, and12,151.40:1, respectively; total ratio error is+9.90%. The early5us low-current sample is transient-contaminated and superseded.





This is a nominal transfer screen, not an implementation pass. The scale input remains ideal, the divider is not laid out as a macro, and estimated divider current is47-92uA per unique scale. With490,240 distinct scale coefficients this static divider is unsuitable for replication. The next implementation stores gate-control voltage on an analog MIM hold node, then checks retention and current transfer before connecting scale current to the signed-weight injector and membrane update. No original-float inference or5ms service is qualified.





Evidence: `artifacts/analog_asic/results/gf180_membrane_scale_inverter_screen_v3.json`; earlier diagnostic runs remain in `gf180_membrane_scale_inverter_screen_v1.json` and `gf180_membrane_scale_inverter_screen_v2.json`.





## GF180 held membrane bank-scale current cell - 2026-10-13





The extracted sampled-weight 9-MIM writer/current cell was reused to represent the membrane bank scale. It was programmed through the physical writer, released, and measured through a1us read/integration event. The normalized scale test points were8.23e-5,0.01536, and1.0. Zero-subtracted charge fractions were0.000110087,0.0141897, and1.0, giving errors+33.8%,-7.6%, and0%. The minimum and median are initial calibration misses; all are nominal TT27 results. The held gate was observed near9us after programming, so millisecond retention is not yet shown.





This reuses an existing physically extracted writer, 9-MIM gate store and current source instead of replicating a static resistor divider. It does not yet establish whether the cell can be replicated per490,240 banks or shared without missing event deadlines. The next required block is bank-scale multiplication with the signed accumulated synaptic contribution, followed by the native membrane update. No original-float inference, PVT/noise,5ms coefficient retention, full-population5ms service or full-chip acceptance.





Evidence: `artifacts/analog_asic/results/gf180_membrane_scale_held_current_cell_v1_src6ca87d3a5103.json`.





## GF180 original 25-actor categorical graph interconnect - 2026-10-13





`gf180_analog_full25_event_graph_interconnect_v1.sv` binds 25 external analog actor packet interfaces across 53 categorical edges from the original 43-node/54-edge graph. It instantiates 12 lossless two-way forks, 9 sorted binary OR merges, 3 nearest-neighbor event expanders, 2 channel-offset concat joins, and one multiplicity-preserving skip join. The head class-current/readout edge is intentionally exposed as an analog boundary; no digital numerical state or weights are introduced.





Yosys 0.67 `hierarchy -check; proc; check` passes with zero warnings; flattened `scc -expect 0` finds zero combinational loops. A Verilator 4.038 cycle-level smoke passes raw ingress fanout to both stems and one project3 event's four expanded coordinates through decoder2 concat to decoder2_fuse. This is a bounded interconnect check, not full actor-graph replay or physical layout. Icarus 11.0 stalls in delta scheduling when the full graph receives that upsample event; isolated expander and expander+join controls pass. Keep this as a simulator-specific limitation, not a functional acceptance claim. Actor compute binding, residual/skip/second concat dynamic replay, class-current analog path, full parent extraction, original-float accuracy and 5 ms service remain open.





Evidence: `artifacts/analog_asic/assembly/full25actor_event_graph_interconnect_v1.json`; RTL: `asic/analog/gf180_analog_full25_event_graph_interconnect_v1.sv`; cycle-level harness: `artifacts/analog_asic/benches/sim_gf180_full25_event_graph_v1.cpp`.





## GF180 128-channel depthwise event-address scatter - 2026-10-12





The categorical address engine now enumerates only output channels in the incoming convolution group. This reduces a 128-channel depthwise event from 1,152 candidate scans to its 9 kernel taps. Numerical weights remain analog and are not encoded or compared by this block. The grouped 4-input/4-output, groups=2 regression still passes; a new 128-channel depthwise regression passes its channel, address, coordinate, multiplicity, and bin-tag checks in nine cycles.





The 128-channel, 3x3 GF180 macro completed ORFS synthesis, CTS, routing and abstract generation. Detailed-route DRC ended at zero; flattened GDS drc(full) is zero; CTS/final setup and hold violation counts are zero. Routed cell area is 48,641 um2 and die outline is 351.275 x 351.275 um. Under the 100 ns control-clock constraint, reported Fmax is 36.7 MHz and estimated digital-view power is 2.26 mW. This is the event-address controller alone: actor weight-array connections, analog loading, producer/consumer wiring, full graph, original-float accuracy and complete 5 ms service are still unverified. Evidence: artifacts/analog_asic/results/gf180_analog_weight_event_scatter_depthwise128_v1.json.





## Locally decoded full-capacity assembly and completed imperfect bank access - 2026-10-11





`full25_locally_decoded_storage_v1/delivery_report_v2.html`:17.17MB native GDS now replaces866055raw bank equivalents with433015independently selected128state pairs and25decoded singles;25original compute-tile banks retained. Independent binary AREF/SREF coordinate readback proves all original bank identities bijective,all54,630,400active states and all25actor cells byte-identical. Global bank selection/shared readout/writeback/compute and graph endpoints remain unbound. Actual spacious local-decoder macro footprints sum34,801.03mm2; not a compact die or the1215mm2bare-plate estimate. Required addressing adds hardware; shared row/column architecture and dense periphery remain to optimize.





New pair_v4:770MOS128MIM,source/GDS native fullDRC0 and Netgen unique,real445.44x180.42um LEF,7310native substrate/coupling branches independently verified. Compaction100243.42->80366.28um2. One50us run completed after measured120s timeout at39.98us justified one180s unchanged replay. Opposite-bank change during write<=.437mV;final112untargeted-state shift.615mV;full-trace peak8.340mV during read-enable. Write error23.56mV fails original20mV combined probe. Requested1.2V.ic startup actually settles2.372..2.375V; native initialization,5ms parent retention,trained precision and full population service unvalidated. No refit or gate relaxation. Trace-review JSON supersedes ambiguous final-versus-peak wording. Catalog97:20module sets/76assemblies;99evidence rows/17function coverage rows.





## First actor integration routing repair - 2026-10-11





Latest candidate: `artifacts/analog_asic/assembly/full25_physical_candidate_v5/delivery_report.html`,13.40MB combined GDS. Actor detail_stem native parent DRC decreases1206->1->0. Independent extracted-parent/reference comparison passes all1191native primitives, exact dimensions, fixed ports and every graph edge; no missing/extra ports. v4 had real VDD/VSS/state/reference shorts despite only1DRC error; that candidate is rejected. Method review traced power escapes across MIM plates and redundant repainting of existing VSS vias. v5 routes compute power outside the right native boundary and reuses its existing M3 landing. Original qualified child geometry is unchanged. Only this actor parent is physically checked; no parent nominal simulation, whole-chip verification, all-bank service or full functional-layout claim. Evidence: `full25_physical_candidate_v5/verification/actor_00_v3/qualification_attempt.json` and `parent_exact_connectivity_attempt.json`.





## Whole-model physical integration candidate and simulation coverage - 2026-10-11





[Delivery report](../artifacts/analog_asic/assembly/full25_physical_candidate_v3/delivery_report.html) links one16.89MB combined GDS, its physical manifest, identity/bounds correction, local pin bindings and98rows of existing module evidence across17required functions. All54,630,400resident identities and147,567parameter targets/capacity values are included.25first-channel first8x8membrane banks are removed from the raw arrays and placed in native shared64state compute tiles; independent hierarchy traversal counts866,055raw banks plus25compute-tile banks, preserving866,080bank capacity instances. Native geometry is namespaced without polygon edits. Local event duration/sign gates connect to existing injectors; selected bin phases connect to beta/reset/sample and peer phases.54logical edges have2754physical categorical corridor wires ending at unbound interface pads. New parent routing verification is separate. This is a physical integration candidate, not a completed functional ASIC; remaining bank access, parameter distribution, global event operators/endpoints,128RMS combination, calibrated threshold/reset,fullcycle accuracy and5ms service remain incomplete. Sparse macro atlas footprint is not dense die area.





## Resident adaptation complete-C characterization - 2026-10-11





`gf180_resident_adaptation_expiry_v3_fullcap_nominal_src98bffbb7a8dd.json`:200us native nominal run complete with1730verified complete resident capacitor branches. Initialization now blocks advance, spike resets/enables, and second spike resumes advance; expiry-block gate remains false. At39/55/95/135us AGE=1.197166/1.207191/1.216783/1.219969V for illustrative1.22V expiry. INITrelease AGE changes1.35->1.257663V and AMPLITUDE1.2->1.093257V; spike-release amplitude1.5->1.487347V. Native previous hierarchy-on report is retained; do not relabel its sequence successful. No calibration or voltage bounds changed. Preserve this completed imperfect characterization and use it as baseline for producer/load integration. The categorical expiry decision and commanded age-step/hold coupling need a focused review; current trace alone does not prove premature gate cutoff or a repair.





## Full64 feature adaptation sum and shared clipped threshold - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_adaptation_sum64_threshold_v2_article_boundary.json) records gf180_adaptation_sum64_threshold_v2: 1563 native MOS, 256 resistors and 768 MIMs; full DRC0/LVS, GDS reimport and real LEF, 8343 nonnegative flat capacitance branches. Nominal simulation completed; `native_adaptation_sum_threshold_chain_observed=True`. Three native nominal cases completed: maxsum5.606mV,maxunclipped5.938mV,maxclippedthreshold4.936mV; local sum settles6.486us to recordedfinal after fullgroup ramp. Source/GDS fullDRC0/nativeNetgen pass. Fresh flatDRC incomplete, native flatNetgen not run; independent complete12122node bijection verifies every primitive/pin/edge. Perfeature resident producers and RMS/decision/reset/control consumers not connected; fullpopulation accuracy/service unaccepted. Spacedgrid footprint is not dense area.





Native full64feature adaptation SUM tree with 1563MOS,256R,768MIM and one final clipped-threshold operator. Sum-only8way internal stages; TOTAL=VCOM+sum all64feature deviations at one pixel,not mean and not subset. Native physical grid,complete flat substrate/coupling C with per-node verification; source/GDS physical checks and flat exact primitive connectivity,realLEF. Separate native50fF output load.80us three sequential nominal fixtures:zero,onepositive channel,all channels summing0.32V. Reference master193uA;1us analog source ramps and100ohm external source resistance. Center1.65,bounds1.55/1.95 illustrative,not trained voltage calibration. Actual model has adaptation widths64/128. Per-channel resident-product inputs externally held; producer connection,RMS,decision/subtractive-reset consumers,autonomous control,dense placement,model accuracy and full-population5ms service remain unfinished. Spaced characterization grid is not dense fullchip area. Local30mV bringup criterion only;typical27C/noise/mismatch off. Catalog revision95: 20 module artifact sets/75 characterization assemblies. Full goal remains incomplete.





## Full64 physical and verification milestone - 2026-10-11





`gf180_adaptation_sum64_threshold_v2` contains1563MOS256nativeR768MIM,2587primitive records. Source and GDS reimport fullDRC0/nativeNetgen pass. Fresh flattened geometry has an exact12122node mapping against independent qualified-child reference; all979nets uniquely proposed then every primitive/pin/edge checked. Complete hierarchy-off capacitor export has8343nonnegative branches with every native substrate-node cap verified. Real LEF exported. Fresh flatDRC incomplete, native flatNetgen not run. OriginalVF2/VF2++ timeout logs and failedv1geometry preserved. Nominal simulation is separate pending evidence; no fullchip/accuracy/5msclaim.





## native eight channel adaptation sum connected to shared threshold clip - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_adaptation_sum8_threshold_v1_article_boundary.json) records gf180_adaptation_sum8_threshold_v1: 219 native MOS, 32 resistors and 96 MIMs; full DRC0/LVS, GDS reimport and real LEF, 973 nonnegative flat capacitance branches. Nominal simulation completed; `native_adaptation_sum_threshold_chain_observed=True`. Actual seven-adder SUM tree and shared base/clipped-threshold parent219MOS32R96MIM;973complete flatC branches. Three35us nominal cases complete:zero/one/eight active product-voltage inputs;maxsum1.165mV,maxrawthreshold1.578mV,maxclippedthreshold0.741mV. Source/GDS nativeNetgen passes; failed flatNativeNetgen retained,exact fixed-port primitive graph proves flat after deeper color refinement. Exact verifier keeps every edge/model/dimension; shallow128? original12round timedout,new128round completes,no acceptance weakening. Actual model adaptation widths64/128;8input block is a reusable reduction stage,not fullwidth acceptance. Resident product producers,RMS,decision/reset consumers,trained voltage mapping,dense layout and5ms service remain open.





Native219MOS32R96MIM seven-adder physical8channel SUM tree directly connected to buffered base addition and actual threshold clip. Complete native flat substrate/coupling capacitance with per-node checks. Source/GDS native Netgen LVS and source/flat/GDS fullDRC0; exact fixed-port primitive graph qualifies flat view after recorded native flat Netgen failure,realLEF. Separate native50fF output load.35us three sequential nominal fixtures: zero,one positive channel,all8positive channels. TOTAL=VCOM+sum(P_i-VCOM),never mean; threshold=clip(BASE+TOTAL-VCOM). Common center1.65,bounds1.55/1.95,1us input transitions/100ohm external source resistance,25uA shared reference master. These are externally held per-channel product voltage fixtures at one pixel; resident product connection,all64/128feature groups,RMS,decision/reset consumers,trained voltage calibration,dense placement and scheduler remain unfinished. Shared tree can be reused across pixels with correct identity/control; characterization footprint not dense area. Local30mV bringup gate only,not original-float precision or5ms/fullchip acceptance. Typical27C/noise/mismatch off. Catalog revision94: 20 module artifact sets/74 characterization assemblies. Full goal remains incomplete.





## shared adaptive threshold buffered addition and clipping - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_shared_adaptive_threshold_v1_article_boundary.json) records gf180_shared_adaptive_threshold_v1: 51 native MOS, 4 resistors and 12 MIMs; full DRC0/LVS, GDS reimport and real LEF, 208 nonnegative flat capacitance branches. Nominal simulation completed; `native_adaptive_threshold_chain_observed=True`. Native buffered base+summed-adaptation-minus-center path passes all three lower/linear/upper loaded fixtures; maxaddition0.312mV,maxeffective0.151mV. Correct208branch native ground/coupling export and actual native Netgen source/flat/GDS matches,fullDRC0,realLEF. External TOTAL_PENALTY must be the feature-channel sum at the same pixel; channel reducer and decision/reset consumers remain to connect. Illustrative voltage bounds,not original-float accuracy or fullchip acceptance.





Native51MOS4R12MIM buffered BASE+TOTAL_PENALTY-VCOM addition followed by actual27MOS range clamp. Complete208branch flat substrate/coupling C with per-node verification; unchanged native devices,source/flat/GDS native Netgen LVS and full DRC0,real LEF. Separate native5x5MIM50fF output load. Three35us sequential nominal typical27C fixtures with1us input transitions and100ohm external source output resistance. VCOM1.65 and bounds1.55/1.95 are illustrative voltage fixtures,not trained unit mapping. Four native reference branches share4uA external master. TOTAL_PENALTY supplied as externally held summed penalty; channel sum/resident adaptation/RMS,decision/reset consumer connections and autonomous scheduler remain unfinished. Report actual addition/clipping error; local30mV bringup gate is not original-model precision. No full population5ms,dense array orfullchip acceptance. Catalog revision93: 20 module artifact sets/73 characterization assemblies. Full goal remains incomplete.





## Corrected-C beta module characterization complete - 2026-10-11





Three10us native-driver phase trials completed at1.8/1.65/1.5V initialization,with frozen auxiliary reference and complete3941branch substrate/coupling extraction. Trained-beta residuals:-20.763/-13.311/-5.829mV. Autozero held; these are beta-phase results,not corrected fullcycle or full-model acceptance. Measured offset/gain retained; no circuit fit. Close this bounded characterization package and continue connected RMS/adaptation/inhibition/control and dense layout. [Three-state report](../artifacts/analog_asic/results/gf180_tile_v3_fullcap_three_state_beta_summary_v1.json). No jobs running.





## joined tile beta phase complete native substrate caps and native control drivers - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_shared_analog_compute_tile_v3_article_boundary.json) records gf180_shared_analog_compute_tile_v3: 413 native MOS, 8 resistors and 172 MIMs; full DRC0/LVS, GDS reimport and real LEF, 3941 nonnegative flat capacitance branches. Nominal simulation completed; `beta_phase_simulation_completed=True`. One10us beta-only sequence completes with native control inverters and3941complete substrate/coupling branches. Frozen-reference beta residual-20.763mV at initial1.800121V; after recharge1.761628V. Autzero held; no corrected fullcycle/detection/reset/rowcommit claim. Exact primitive connectivity qualifies source/flat/GDS; native Netgen is not passing. Earlier hierarchical-PCAP cycles underloaded critical nodes. V3 characterization entry qualifies this phase only; full neuron precision,control-driver placement,dense layout and5ms service remain open.





10us phase-isolated native joined-tile beta characterization with corrected3941branch flat RC. All413MOS8R172MIM retained. Initial compute1.8V steady bias; only compute WRITE release,beta/aux phases run. All autozero gates remain high; no comparator autozero release,injection,threshold/reset/read/row-writeback assertion. Method review after ideal Gear/regularized/Trap and finite-driver whole-cycle attempts abort at autozero edge. Only changing WRITE/WRITEB,AUXRESET and BETA commands use two qualified native GF180 inverters each; steady phase inputs remain DC. Whole-cycle native-driver composition timed out120s near1.058ms; do not restart or extend that run. This10us probe reduces changing phases to the beta mechanism; no threshold/row-service claim. This isolates beta with actual joined loading and frozen reference; no numerical tolerance or cap edits. Typical27C/noise/mismatch off; no trained precision or5ms/fullchip acceptance. Catalog revision92: 20 module artifact sets/72 characterization assemblies. Full goal remains incomplete.





## Corrected native capacitance export and grounded tile shield - 2026-10-11





GF180 joined tile v3 keeps413MOS8R172MIM and passes source/flat/GDS full DRC0 plus exact primitive connectivity proofs; native Netgen is not claimed. Ground shield reduces STATE-to-buffer coupling291.53fF to25.84fF. Hierarchy-on export of the geometrically flat tile omitted185 substrate pairs and altered98 existing ground pairs. Native hierarchy-off/top-on export yields3941 nonnegative branches,593identical device tokens and per-node substrate agreement; C_STATE-to-VSS1.70294pF and C_AUX-to-VSS0.35526pF. Earlier hierarchical-PCAP joined cycles are underloaded diagnostics and cannot establish full extracted precision. Preserve them; no blanket invalidation of unreviewed child modules.





Corrected full-cycle trials remain incomplete. Ideal controls stop at switching corners; finite AZ driver crosses the first failure,all-phase resistive drivers reach beta1.0649ms,with partial read/restore error-5.163mV. Native two-inverter control drivers reuse a prior successful sequencer method but the full trial timed out120s; no restart/runtime/tolerance sweep. A10us beta-only native-driver probe is active. Native driver composition is not an integrated driver layout or autonomous scheduler. Catalog91 retains20module sets/71completed characterization entries and adds v3 as physical-qualified,in progress. Full analog functionality,dense layout,original-float accuracy and5ms service remain open. Evidence: `artifacts/analog_asic/results/gf180_shared_tile_v3_export_and_phase_review_v1.json`.





## Joined beta phase diagnosis - 2026-10-11





Existing native tile trace partition:state1.73998V before beta ->1.57287V after share/release ->1.53895V before recharge ->1.54536V after complete cycle; trained target1.72935V. Share/release-167.10mV,between-phase-33.93mV,recharge+6.41mV. The dominant discrepancy precedes auxiliary recharge; this temporal partition alone does not prove one causal mechanism. No new run,fit,tolerance relaxation or correction. Evidence:`artifacts/analog_asic/results/gf180_joined_tile_beta_phase_partition_v1.json`. Full trained accuracy remains unaccepted.





## first connected shared analog compute read write tile - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_shared_analog_compute_tile_v2_article_boundary.json) records gf180_shared_analog_compute_tile_v2: 413 native MOS, 8 resistors and 172 MIMs; full DRC0/LVS, GDS reimport and real LEF, 3756 nonnegative flat capacitance branches. Nominal simulation completed; `native_closed_loop_update_observed=True`. First actual413MOS8R172MIM joined tile closed-loop native trial completed;3756 flat routing-C branches. Read/restore/beta/positive injection/sample/spike/subtractive reset/capture/row7commit all exercised. Positive event+271.09mV,spike3.284V,reset-47.34mV,writeback-13.53mV vsheld DATA0.56other rows change0.1766mV;other7columns of selected row4.982mV. Trained-beta residual-183.99mV fails semantic accuracy despite local path-observed gate; do not transfer old calibration or accept fullPLIF/model/service. Source/flat/GDS fullDRC0 and exact complete primitive graph bijections prove connectivity; native Netgen failures retained and not labeled passing. One intentional D=S dummy extraction warning/junction-area uncertainty retained. Spaced18.63mm characterization width is not dense tile/full-chip area.





First1.21ms native closed-loop trial of actual physical413MOS8R172MIM shared64state tile. Analog init mux programs1.656875V autozero baseline then1.8V compute target; eight real analog output holders initialize bank, row7column0 reads through native mux/replica/up-shifter, actual compute WRITE restores state, one frozen-beta auxiliary cycle and5us positive injection precede sampled decision and gated subtractive reset. Compute output passes native isolation/down-shift into holder0; all8held outputs commit onlyrow7. Other holders retain initialized values. Exact source/flat/GDS primitive connectivity proofs and all native flat C retained. Existing frozen v6 auxiliary reference/reset duration reused without new fit, preserving errors from new loading. External categorical scheduler,analog programming/current/parameter references; typical27C/noise/mismatch off. One selected update only, not all64updates,adaptation/RMS/inhibition,trained-weight mapping,original model accuracy,5ms population service,dense tile or full chip. Native Netgen comparisons failed; exact complete graph bijections qualify connectivity, no false Netgen pass. Catalog revision90: 20 module artifact sets/71 characterization assemblies. Full goal remains incomplete.





## explicit storage compute analog voltage contract - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_storage_compute_level_bridge_v1_article_boundary.json) records gf180_storage_compute_level_bridge_v1: 24 native MOS, 8 resistors and 12 MIMs; full DRC0/LVS, GDS reimport and real LEF, 120 nonnegative flat capacitance branches. Nominal simulation completed; `native_storage_compute_translation_observed=True`. Actual24MOS8R12MIM joined analog interface passes3points with120flat routing-C branches:storage1.0/1.2/1.4V ->compute1.45/1.65/1.85V ->return1.0/1.2/1.4V. Maximum forward0.484mV,roundtrip0.656mV. Isolation buffer is necessary to separate passive-feedback DC load; direct-cascade high-point148mV failure retained. This identity roundtrip is a voltage-domain fixture; actual neuron must be inserted between up-shifter and isolation before compute acceptance.





Three40us actual24MOS8R12MIM storage-compute level bridge trials, fresh joined source/GDS DRC0/LVS/LEF and full flat routing C. Up subtractor shifts storage1.0..1.4V by+0.45V into compute1.45..1.85V; unity isolation buffer separates resistor DC loads; down subtractor returns by-0.45V. External SREF1.2,CREF1.65,3uA master for three native PF references, ideal INPUT data and100fF external RETURN load. No ideal internal arithmetic,buffer,ADC,QAT or numerical digital state. Typical27C/noise-off/mismatch disabled. Identity transfer qualifies voltage-domain interface; full tile must insert actual compute between up shifter output and isolation input, then qualify row holding/writeback and learned mappings. Not model precision,service or full-chip completion. Catalog revision89: 20 module artifact sets/70 characterization assemblies. Full goal remains incomplete.





## eight analog output row commit - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_row_staged_writeback_v1_article_boundary.json) records gf180_row_staged_writeback_v1: 289 native MOS, 0 resistors and 108 MIMs; full DRC0/LVS, GDS reimport and real LEF, 2566 nonnegative flat capacitance branches. Nominal simulation completed; `native_staged_row_commit_observed=True`. Actual289MOS108MIM row-writeback parent passes one180us native sequence with2566 flat routing-C branches. Eight serial captures feed eight real bank DATA columns; onlyrow7commits. Maximum held-output error21.35mV,final bank error37.18mV;56unselected cells change0.300mV total and0.03385mV acrosscommit. Preserve imperfections; no external force on internal analog holding outputs. Complete compute operation,5ms parent retention and model accuracy/service remain incomplete.





One180us actual physical289MOS108MIM staged-writeback parent. All64analog bank states initialized through actual8row controls and eight real buffered analog DATA outputs. One shared native isolation amplifier buffers external COMPUTE_OUT; eight native TG/MIM output holders capture serial1.0..1.35V values, COMPUTE_OUT then changes0V, only row7writes all8held outputs. Every native flat parent routing capacitor retained,source/GDS DRC0/LVS/LEF. No ideal internal holding voltage,ideal switches,ADC,QAT or numerical digital state. External master IO9uA for9PF references,NF1uA,VCM1.2V and categorical phases. Typical27C/noise-off/mismatch disabled. This tests complete row commit and preservation of56unselected cells; not compute operation,full5ms parent hold,calibrated model precision,service or full chip. Spacious characterization footprint not dense capacity area. Catalog revision88: 20 module artifact sets/69 characterization assemblies. Full goal remains incomplete.





## analog staged row commit output - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_analog_commit_hold_buffer_v2_article_boundary.json) records gf180_analog_commit_hold_buffer_v2: 10 native MOS, 0 resistors and 5 MIMs; full DRC0/LVS, GDS reimport and real LEF, 43 nonnegative flat capacitance branches. Nominal simulation completed; `native_analog_output_hold_observed=True`. Focused hold-capacitor ratio repair50fF->968fF passes nominal local bring-up:maximum release18.655mV versus163.025mV before,DATA-stress excursion15.373mV versus149.234mV before,5ms end drift0.363mV. All43 flat C branches retained. Eight-output physical bank, upstream compute isolation and actual bank-column writeback still to join; do not claim full accuracy or final dense area.





Three5.05ms extracted10MOS5MIM analog commit hold-buffer trials at1.0/1.2/1.4V. Actual source/GDS DRC0,LVS,LEF,new flat C branches. Only hold MIM increased50fF to968fF after diagnosed native routing coupling. Native TG releases5us; DATA changes0/3.3V duringhold to expose feedthrough. Real buffered OUT has100fF external representative load, not yet the actual bank column.1uA external reference into native PF diode. Typical27C/noise-off/mismatch disabled. This qualifies one holding output, not eight-output row commit, upstream compute isolation, learned-model precision,5ms whole-population service or full chip. Catalog revision87: 20 module artifact sets/68 characterization assemblies. Full goal remains incomplete.





## analog compute restore and staged commit - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_analog_commit_hold_buffer_v1_article_boundary.json) records gf180_analog_commit_hold_buffer_v1: 10 native MOS, 0 resistors and 5 MIMs; full DRC0/LVS, GDS reimport and real LEF, 43 nonnegative flat capacitance branches. Nominal simulation completed; `native_analog_output_hold_observed=False`. Native10MOS5MIM analog holding output physical/5ms test complete with gatefalse:release128-163mV,DATA feedthrough149mV. Retain failure. Diagnosed4.81232fF DATA/HELD and4.98052fF WRITE/HELD routing coupling vs50fF hold; one focused968fF capacitor revision in progress, unchanged buffer/control mechanism.





Three5.05ms extracted10MOS5MIM analog commit hold-buffer trials at1.0/1.2/1.4V. Actual source/GDS DRC0,LVS,LEF,43 flat C branches. Native TG releases5us; DATA changes0/3.3V duringhold to expose feedthrough. Real buffered OUT has100fF external representative load, not yet the actual bank column.1uA external reference into native PF diode. Typical27C/noise-off/mismatch disabled. This qualifies one holding output, not eight-output row commit, upstream compute isolation, learned-model precision,5ms whole-population service or full chip. Catalog revision86: 20 module artifact sets/67 characterization assemblies. Full goal remains incomplete.





## analog compute restore and staged commit - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_bank_read_compute_bridge_v1_article_boundary.json) records gf180_bank_read_compute_bridge_v1: 301 native MOS, 0 resistors and 110 MIMs; full DRC0/LVS, GDS reimport and real LEF, 3143 nonnegative flat capacitance branches. Nominal simulation completed; `native_three_compute_restores_observed=True`. Actual physical bank/read-to-compute write bridge complete;three restorations maximum7.856mV error after TGrelease. Beta/injection/threshold/reset idle; VCM1.2V diagnostic differs from v6 semantic calibration1.65V. No trained-calibration or row-writeback acceptance.





One180us actual301MOS110MIM physical bank/mux/reader/five-module compute restore bridge,3143 flat C branches,source/GDS DRC0/LVS/LEF. Three stored row/column values are read and transferred by native compute WRITE TG into compute STATE, then released. All beta/injection/decision/reset functions idle; this only qualifies analog restore interface under actual compute loading. Both storage/computeVCM fixed1.2V, external AUXREF/SENSE_REF1.2V diagnostic settings. Earlier v6 compute semantic calibration used1.65V; no transfer of that calibration, learned-beta/threshold accuracy or restored float representation claimed. Native external PF diode parking reference plus1uA current fixture. External phase/voltage references, typical27C/noise-off/mismatch disabled. No row writeback: all8row columns require separate analog staging/parallel lanes before bank row commit. No complete PLIF, original model precision,5ms service or fullchip claim. Catalog revision85: 20 module artifact sets/66 characterization assemblies. Full goal remains incomplete.





## shared64state analog bank reader - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_bank_mux_replica_read_v1_article_boundary.json) records gf180_bank_mux_replica_read_v1: 245 native MOS, 0 resistors and 69 MIMs; full DRC0/LVS, GDS reimport and real LEF, 2415 nonnegative flat capacitance branches. Nominal simulation completed; `native_bank_mux_three_site_recovery_observed=True`. One reader now physically serves8columns/64states via native mux;245MOS69MIM parent. Three row/column sites recover within21.56uV, final storage change0.923mV. Reader/mux transistor count44 versus96 for8copies of reader:54.17percent lower reader-periphery transistor count; this is not measured full-chip area saving. Cold versus warm read settling7.179us/1.081us; sharing ratio and5ms schedule remain provisional. See gf180_shared_reader_serial_budget_v2.json; v1 all-cold multiplication is a conservative scenario, not a necessary throughput bound.





One180us actual245MOS69MIM physical bank/mux/replica-reader. All64 analog states initialized; row0column0,row0column3,row7column7 sequentially recovered through same native TG column mux and same replica feedback reader. All2415 flat routing-C branches and actual physical interconnect retained; source/GDS DRC0,LVS and LEF. Bank native mirror supplies actual column sinks and replica sink bias. No ideal buffer,fitted inverse,ADC,QAT or digital membrane. External analog DATA,categorical row/one-hot column commands,READ_ENABLE and1uA NF/PF references. Typical27C/noise-off/mismatch disabled;3sites do not establish full precision,PVT/matching,5ms retention/global service,compute or full chip. Spaced fixture is not dense capacity geometry. Catalog revision84: 20 module artifact sets/65 characterization assemblies. Full goal remains incomplete.





## shared analog column read - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_column_mux8_v2_article_boundary.json) records gf180_column_mux8_v2: 32 native MOS, 0 resistors and 0 MIMs; full DRC0/LVS, GDS reimport and real LEF, 196 nonnegative flat capacitance branches. Nominal simulation completed; `native_eight_column_selection_observed=True`. Native32MOS eight-column TG mux/inverter layout and nominal eight-selection test complete; inputs0.1..0.45V,100fF fixture load,7us samples. This tests mux selection only; no claim of analog precision from near-zero noiseless DC error.





One64us native32MOS eight-column analog TG selection sequence. Physical source/GDS DRC0,LVS,LEF and196 flat interconnect C branches retained. Actual eight NF/PF TGs with native inverter complements. External one-hot controls use100ns break before make, ideal analog inputs0.10..0.45V and100fF external output load. Selected output sampled7us after each selection. No ideal switches, numeric conversion, ADC or QAT. Typical27C/noise-off/mismatch disabled; actual bank/reader loading and global service remain to connect. Catalog revision83: 20 module artifact sets/64 characterization assemblies. Full goal remains incomplete.





## shared analog column read - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_bank_replica_read_column_v3_article_boundary.json) records gf180_bank_replica_read_column_v3: 213 native MOS, 0 resistors and 69 MIMs; full DRC0/LVS, GDS reimport and real LEF, 2154 nonnegative flat capacitance branches. Nominal simulation completed; `native_bank_replica_two_row_recovery_observed=True`. Actual bank-connected column0 analog read recovery passes two sequential held rows:maximum20.79uV reconstruction error,0.951mV final storage disturbance. Reader enable is a separate categorical command to support arbitrary selected rows. Other seven columns remain raw.





One160us actual213MOS69MIM physical bank plus shared analog column0 replica reader. All64 analog states initialized through independent row controls; row0 and row7 recovered sequentially by same reader; actual2154 flat routing-C branches, full source/GDS DRC0/LVS and LEF. Replica sink shares bank NF mirror BIAS; existing bank actual read sinks remain. No fitted numerical inverse or ideal buffer. External analog DATA,1uA NF/PF references and categorical row/reader-enable commands. Rows serviced sequentially; other seven columns retain raw outputs. Typical27C/noise-off/mismatch disabled. Not5ms parent retention, full8column read support, global scheduling, model accuracy or chip completion. Catalog revision82: 20 module artifact sets/63 characterization assemblies. Full goal remains incomplete.





## native analog replica feedback read - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_replica_feedback_reader_v3_article_boundary.json) records gf180_replica_feedback_reader_v3: 12 native MOS, 0 resistors and 5 MIMs; full DRC0/LVS, GDS reimport and real LEF, 58 nonnegative flat capacitance branches. Nominal simulation completed; `native_replica_feedback_reconstruction_observed=True`. Actual12MOS5MIM reader physical and sampled3point simulation complete: maximum22.04uV reconstruction error against held physical state. Nominal mismatch-free only. Prior v1 MIM-via/left-fanout errors and v2 right-escape collision retained; v3 reserves separate right-hand escape region. This spaced reader characterization footprint is not a dense array-area estimate.





Three60us native sampled read trials using actual flat12MOS5MIM reader with58 interconnect C branches and real source/GDS DRC0/LVS/LEF. Source-qualified extracted3T memory, native diode NF reference and native NF read sink fixtures. Write releases5us; both actual and replica read select10..55us; reconstruct at50us. Numerical membrane stays analog. No fitted inverse, ideal readout buffer, integer DAC or QAT. Typical27C/noise-off/mismatch disabled; current refs and categorical control/data external. New reader parent physical qualification complete, but separately composed memory fixture wiring has no new physical layout. Shared bank loading, PVT/mismatch, connected compute/global service remain incomplete. Catalog revision81: 20 module artifact sets/62 characterization assemblies. Full goal remains incomplete.





## compact shared row control - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_shared_decoder_two_banks_v1_article_boundary.json) records gf180_shared_decoder_two_banks_v1: 568 native MOS, 0 resistors and 128 MIMs; full DRC0/LVS, GDS reimport and real LEF, 5339 nonnegative flat capacitance branches. Nominal simulation completed; `native_decoded_bank_sequence_observed=True`. One166MOS decoder shares row control across two201MOS banks,568MOS128MIM total. Layout58130.6976um2 versus77888.9952um2 for two independent decoded banks:25.37percent smaller.200us128-state access passes; write22.66mV and finalread3.72mV. Banks operate in lockstep, with independent analog columns but no bank inhibit. This does not select compute sharing or establish parent5ms retention.





One measured runtime extension120s->660s:initial run reached41.9246us during fourth-row write-command edge. Same circuit,stimuli,tolerances. Actual568MOS128MIM two-bank parent,one166MOS native decoder shared by two201MOS gain-cell banks with16native sinks and2diode masters. All5339 routing-C branches retained.200us native fixture initializes8rows in both banks with different analog values, overwritesrow7 with opposite column slopes, readsrow0and7 through common row selection. All128states and16readouts recorded. Both banks operate in lockstep; separate analog columns preserve identities. Independent bank inhibit is not implemented. This storage grouping does not select compute-lane allocation or prove5ms parent retention/global service. Native bank5ms/50ms retention is separate child evidence. External address/command/data/master-current/reference fixtures; typical27C/noise-off. No calibrated read, permanent weights, fullmodel precision or chip claim. Catalog revision80: 20 module artifact sets/61 characterization assemblies. Full goal remains incomplete.





## compact shared row control - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_compact_decoded_bank8x8_v1_article_boundary.json) records gf180_compact_decoded_bank8x8_v1: 367 native MOS, 0 resistors and 64 MIMs; full DRC0/LVS, GDS reimport and real LEF, 3305 nonnegative flat capacitance branches. Nominal simulation completed; `native_decoded_bank_sequence_observed=False`. Connected64-state5.4ms sequence completed; write22.22mV,5ms hold6.35mV, finalread1.74mV. Local20mV write gate fails; measured imperfection retained.





Actual367MOS64MIM parent,166MOS native direct3address+command decode joined to201MOS64MIM under-MIM3T bank with actual9MOS shared column-current mirror, all3305 nonnegative extracted routing branches. External three categorical address bits and separate write/read commands drive real decoded wordlines, not ideal row sources. Initialize all8rows through decoder, overwrite only row7, stress shared DATA at2ms/4ms, hold all64states over5ms and read rows0and7 via native source followers. Record every state and all8columns. External ideal address/command/data/reference/master-current fixtures; no numeric digital state, ideal output buffer or fitted restore. Typical27C/noise off. One measured runtime extension120s->300s:initial run reached5.18995ms of5.4ms before timeout at address transition; preserve device models/tolerances/stimuli. Compact decoder leaf placement and parent routing footprint are measured; not a minimum-area array or fullchip. One external1uA master current feeds native8column sinks. No beta/weight compute, read calibration, full-model accuracy, population timing or fullchip acceptance. Catalog revision79: 20 module artifact sets/60 characterization assemblies. Full goal remains incomplete.





## compact categorical row control leaf - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_dense_inverter_v1_article_boundary.json) records gf180_dense_inverter_v1: 2 native MOS, 0 resistors and 0 MIMs; full DRC0/LVS, GDS reimport and real LEF, 5 nonnegative flat capacitance branches. Nominal simulation completed; `native_categorical_logic_observed=True`. One native32us fixture covers16input combinations and100fF output loading for both compact logic leaves. Address/control only; no numerical-state digitization or fullchip qualification. Joined decoder/bank experiments remain in progress.





One32us native extracted typical27C/noise-off fixture:16 categorical combinations of3address inputs+command, native NAND4/output inverter plus address inverter;100fF external output load each. Source/GDS fullDRC0/uniqueLVS,all55routing-C branches retained. Boolean operation is control/address only; no analog-state digitization. Stable samples1.8us into2us intervals; no real bank, global service, PVT or chip acceptance. Catalog revision78: 20 module artifact sets/59 characterization assemblies. Full goal remains incomplete.





## compact categorical row control leaf - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_dense_and4_v1_article_boundary.json) records gf180_dense_and4_v1: 10 native MOS, 0 resistors and 0 MIMs; full DRC0/LVS, GDS reimport and real LEF, 50 nonnegative flat capacitance branches. Nominal simulation completed; `native_categorical_logic_observed=True`. One native32us fixture covers16input combinations and100fF output loading for both compact logic leaves. Address/control only; no numerical-state digitization or fullchip qualification. Joined decoder/bank experiments remain in progress.





One32us native extracted typical27C/noise-off fixture:16 categorical combinations of3address inputs+command, native NAND4/output inverter plus address inverter;100fF external output load each. Source/GDS fullDRC0/uniqueLVS,all55routing-C branches retained. Boolean operation is control/address only; no analog-state digitization. Stable samples1.8us into2us intervals; no real bank, global service, PVT or chip acceptance. Catalog revision77: 20 module artifact sets/58 characterization assemblies. Full goal remains incomplete.





## shared analog storage optimization - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_underplate_biased_bank8x8_v1_article_boundary.json) records gf180_underplate_biased_bank8x8_v1: 201 native MOS, 0 resistors and 64 MIMs; full DRC0/LVS, GDS reimport and real LEF, 2103 nonnegative flat capacitance branches. Nominal simulation completed; `native_shared_bank_sequence_observed=True`. Single-NFET write within1.0-1.4V,3.3V wordline; local read isolation retained. Actual shared row/column wiring and MIM overlap where present. Article prototype evidence; uncalibrated read offsets and external controls/references remain. Fullchip incomplete.





One actual201MOS/64MIM8x8 shared-row/shared-column bank with all native nonnegative routing-cap branches. All64 states initialized through native single-NFET write access; rows0-6 held while row7 is overwritten on shared DATA columns, then each state held at least5ms with DATA rail stress. Sequential native source-follower reads of rows0and7; six middle rows remain unselected. All64 analog states and8 read columns recorded; no ideal output buffer. External ideal references/wordlines/data and one gated1uA master-reference fixture driving actual9MOS shared column-current mirror. Typical27C/noise disabled. 100ns external write-wordline slew, matching the completed3T bank sequence. Transistors occupy lower layers under MIM. Source-follower offset uncalibrated. Native8column sinks and1diode master included. No decoder/write-driver geometry, trained beta, threshold/RMS, large-array loading, population service, accuracy or fullchip acceptance. Catalog revision75: 20 module artifact sets/57 characterization assemblies. Full goal remains incomplete.





## shared analog storage optimization - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_underplate_bank8x8_v3_article_boundary.json) records gf180_underplate_bank8x8_v3: 192 native MOS, 0 resistors and 64 MIMs; full DRC0/LVS, GDS reimport and real LEF, 2070 nonnegative flat capacitance branches. Nominal simulation completed; `native_shared_bank_sequence_observed=True`. Single-NFET write within1.0-1.4V,3.3V wordline; local read isolation retained. Actual shared row/column wiring and MIM overlap where present. Article prototype evidence; uncalibrated read offsets and external controls/references remain. Fullchip incomplete.





One actual192MOS/64MIM8x8 shared-row/shared-column bank with all2070 nonnegative routing-cap branches. All64 states initialized through native single-NFET write access; rows0-6 held while row7 is overwritten on shared DATA columns, then each state held at least5ms with DATA rail stress. Sequential native source-follower reads of rows0and7; six middle rows remain unselected. All64 analog states and8 read columns recorded; no ideal output buffer. External ideal references/wordlines/data and gated1uA column-current fixtures. Typical27C/noise disabled. 100ns external write-wordline slew, matching the completed3T bank sequence. Transistors occupy lower layers under MIM. Source-follower offset uncalibrated. No decoder/driver geometry, trained beta, threshold/RMS, large-array loading, population service, accuracy or fullchip acceptance. Catalog revision74: 20 module artifact sets/56 characterization assemblies. Full goal remains incomplete.





## shared analog storage optimization - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_shared_underplate_3t_v2_article_boundary.json) records gf180_shared_underplate_3t_v2: 3 native MOS, 0 resistors and 1 MIMs; full DRC0/LVS, GDS reimport and real LEF, 30 nonnegative flat capacitance branches. Nominal simulation completed; `native_compact_memory_write_hold_read_observed=True`. Single-NFET write within1.0-1.4V,3.3V wordline; local read isolation retained. Actual shared row/column wiring and MIM overlap where present. Article prototype evidence; uncalibrated read offsets and external controls/references remain. Fullchip incomplete.





Three independent actual under-MIM routed3T/50fF-MIM cell instances, all native nonnegative extracted routing branches per cell retained. Initial DC write through native NFET stores1.0/1.2/1.4V, then write gate turn off at1us. Unselected ideal DATA sources switch to0V at2ms and3.3V at4ms. Record a full5ms hold from1us to5.001ms before read selection. Native NF source-follower plus read-select drives a separately gated ideal1uA external column sink; selected read sampled5.1ms and release5.19ms. No ideal output buffer, state restore or numerical conversion. Ideal voltage/wordline/reference/column-current fixtures remain external; supply energy excludes their drivers. Typical27C/noise disabled, unchanged1e-6 tolerance. This cell has no trained beta/threshold/inhibition/adaptation logic; array bus loading, decoder, calibrated read offsets, noise/PVT and full-model5ms service remain unfinished. Three memory records do not prove full population behavior. Catalog revision73: 20 module artifact sets/55 characterization assemblies. Full goal remains incomplete.





## shared analog storage optimization - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_shared_memory_bank8x8_v2_article_boundary.json) records gf180_shared_memory_bank8x8_v2: 192 native MOS, 0 resistors and 64 MIMs; full DRC0/LVS, GDS reimport and real LEF, 2007 nonnegative flat capacitance branches. Nominal simulation completed; `native_shared_bank_sequence_observed=True`. Single-NFET write within1.0-1.4V,3.3V wordline; local read isolation retained. Actual shared row/column wiring and MIM overlap where present. Article prototype evidence; uncalibrated read offsets and external controls/references remain. Fullchip incomplete.





One actual192MOS/64MIM8x8 shared-row/shared-column bank with all2007 nonnegative routing-cap branches. All64 states initialized through native single-NFET write access; rows0-6 held while row7 is overwritten on shared DATA columns, then each state held at least5ms with DATA rail stress. Sequential native source-follower reads of rows0and7; six middle rows remain unselected. All64 analog states and8 read columns recorded; no ideal output buffer. External ideal references/wordlines/data and gated1uA column-current fixtures. Typical27C/noise disabled. Focused external wordline slew repair:100ns instead of10ns after original transient aborted at20us row7 release; no internal device/tolerance change. Source-follower offset uncalibrated. No decoder/driver geometry, trained beta, threshold/RMS, large-array loading, population service, accuracy or fullchip acceptance. Catalog revision72: 20 module artifact sets/54 characterization assemblies. Full goal remains incomplete.





## shared analog storage optimization - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_shared_analog_memory_3t_v2_article_boundary.json) records gf180_shared_analog_memory_3t_v2: 3 native MOS, 0 resistors and 1 MIMs; full DRC0/LVS, GDS reimport and real LEF, 31 nonnegative flat capacitance branches. Nominal simulation completed; `native_compact_memory_write_hold_read_observed=True`. Single-NFET write within1.0-1.4V,3.3V wordline; local read isolation retained. Actual shared row/column wiring and MIM overlap where present. Article prototype evidence; uncalibrated read offsets and external controls/references remain. Fullchip incomplete.





Three independent actual routed3T/50fF-MIM cell instances, all31 nonnegative extracted routing branches per cell retained. Initial DC write through native NFET stores1.0/1.2/1.4V, then write gate turn off at1us. Unselected ideal DATA sources switch to0V at2ms and3.3V at4ms. Record a full5ms hold from1us to5.001ms before read selection. Native NF source-follower plus read-select drives a separately gated ideal1uA external column sink; selected read sampled5.1ms and release5.19ms. No ideal output buffer, state restore or numerical conversion. Ideal voltage/wordline/reference/column-current fixtures remain external; supply energy excludes their drivers. Typical27C/noise disabled, unchanged1e-6 tolerance. This cell has no trained beta/threshold/inhibition/adaptation logic; array bus loading, decoder, calibrated read offsets, noise/PVT and full-model5ms service remain unfinished. Three memory records do not prove full population behavior. Catalog revision71: 20 module artifact sets/53 characterization assemblies. Full goal remains incomplete.





## Storage control and article evidence milestone - 2026-10-11





Connected decoded-bank simulation completes; nominal gate=False, maximum write error4.84mV, hold excursion23.82mV and read disturbance36.88mV. Compact cell and8x8 bank50ms nominal retention complete; maximum excursions9.07mV and11.67mV. Full64 connected RMS/frontend6us exploratory transient completes after one100ns external input-slew diagnostic; root settling error17.40mV and sampled adaptation amplitude1.19437/1.19759/1.19371V are retained, including nonmonotonic transient output. Native hierarchy capacitance differs from geometric-flat baseline; no flat equivalence or model accuracy acceptance. Catalog70:20 module sets/52 assemblies.





Evidence: `artifacts/analog_asic/assembly/article_module_catalog_v70.json`, `artifacts/analog_asic/results/gf180_parameter_and_retention_supplement_v1.json`, `artifacts/analog_asic/results/gf180_addressed_memory_bank8x8_v2_native_decoded_sequence_src45c652b55f16.json`.





## native addressed 8x8 analog memory bank - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_addressed_memory_bank8x8_v2_article_boundary.json) records gf180_addressed_memory_bank8x8_v2: 430 native MOS, 0 resistors and 64 MIMs; full DRC0/LVS, GDS reimport and real LEF, 5160 nonnegative flat capacitance branches. Nominal simulation completed; `native_decoded_bank_sequence_observed=False`. Actual174MOS3to8 categorical decoder joins256MOS64MIM bank,430MOS total; all8rows initialized, onlyrow7 overwritten,64states held5ms and rows0and7 read. Preserve measured errors; spacious6.4mm integration fixture is not selected dense area. No numerical digital state or full-chip claim.





One660s runtime extension after the120s run advanced28.1us through decoded initialization, same solver/circuit/stimuli. Actual430MOS64MIM parent,174MOS native3to8 address/read/write decoder joined to256MOS64MIM bank, all5160 nonnegative extracted routing branches. External three categorical address bits and separate write/read commands drive real decoded wordlines, not ideal row sources. Initialize all8rows through decoder, overwrite only row7, stress shared DATA at2ms/4ms, hold all64states over5ms and read rows0and7 via native source followers. Record every state and all8columns. External ideal address/command/data/reference/current fixtures; no numeric digital state, ideal output buffer or fitted restore. Typical27C/noise off. Spacious integration routing is not dense macro area. No beta/weight compute, read calibration, full-model accuracy, population timing or fullchip acceptance. Catalog revision69: 20 module artifact sets/52 characterization assemblies. Full goal remains incomplete.





## full64 native RMS clip strength exploratory assembly - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_full64_rms_frontend_v1_article_boundary.json) records gf180_full64_rms_frontend_v1: 2397 native MOS, 2866 resistors and 1056 MIMs; full DRC0/LVS, GDS reimport and real LEF, 90640 nonnegative native hierarchical capacitance branches; geometric flat export incomplete and independent flat-cap equivalence unaccepted. Nominal simulation completed; `native_connected_RMS_frontend_transient_observed=False`. Native6us three-level transient completed after one external10ns-to100ns input-slew diagnostic; full source/GDS/LEF complete. Retain17.40mV root DC tracking error, half/full ratio.530 versus ideal.707 and frontend settling error. Geometric flat RC incomplete; hierarchical capacitance model not equivalent to flat baseline. Nominal precision gate false; no repeated tuning.





One660s native runtime extension after the180s run reached1.99us of6us without a convergence abort. Measured543s linear estimate plus20percent margin; unchanged actual geometry, solver and three levels; one focused diagnostic slows only external candidate rises from10ns to100ns after an abort exactly at the first edge. Actual64 candidate-minus-penalty formatters and full64 energy/mean-root physically drive native high-common-mode buffer, offset conversion, clipping and strength product in one2397MOS2866R1056MIM parent with90640 nonnegative algebraically expanded native hierarchical capacitance branches. This is exploratory hierarchical PEX: independent full64 geometric-flat comparison is not equivalent within export rounding; geometric-flat extraction for this parent remains incomplete. No flat-PEX-equivalence claim. Three sequential levels in6us: all candidates1.2V, half2V, all2V; shared penalty1.2V,VBASE.9,VZERO1.2,VDD3.3,64uA master,typical27C. No ideal internal candidate-minus-penalty arithmetic, formatted gate drive or ROOT voltage source. Frozen independently calibrated ROOT_REF2.412488477821002V and STRENGTH1.4V remain external, with separate4uA PMOS/1uA NF frontend references. Candidate/penalty sources remain external ideal buffered fixtures. Compare samples1.5/3.5/5.5us against independent actual connected-source-hierarchy three-level DC report. Compositional exact source/GDS and electrical-expansion device graph qualification retained; failed historical Netgen matching logs are not treated as passing. No fitted correction, calibrated trained RMS/epsilon, noise/PVT, all-neuron5ms service or full-chip acceptance Catalog revision68: 20 module artifact sets/51 characterization assemblies. Full goal remains incomplete.





## Dense analog storage and assembly milestone - 2026-10-11





The compact4T/50fF cell, actual2x2 bank and actual8x8 bank complete native source/GDS fullDRC0, independent reference LVS, flat routing capacitance and real LEF. All64 states in the8x8 bank complete selective overwrite, stressed5ms hold and two-row read: maximum write error1.43mV, hold excursion10.64mV and selected-read disturbance4.89mV. Read offsets and external ideal drivers remain. Catalog67 has20 reusable modules/50 completed characterization assemblies. Full64 RMS/frontend source/GDS/LEF and three native DC points separately complete; flatRC/transient remain incomplete.





Evidence: `artifacts/analog_asic/assembly/article_module_catalog_v67.json`, `artifacts/analog_asic/assembly/full_capacity_storage_gds_v1/capacity_assembly.json`, `artifacts/analog_asic/results/gf180_full64_flat_and_storage_atlas_method_review_v1.json`.





## shared row column 8x8 analog memory bank - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_compact_memory_bank8x8_v1_article_boundary.json) records gf180_compact_memory_bank8x8_v1: 256 native MOS, 0 resistors and 64 MIMs; full DRC0/LVS, GDS reimport and real LEF, 2226 nonnegative flat capacitance branches. Nominal simulation completed; `native_shared_bank_sequence_observed=True`. Actual64state bank149.42x112.4um; all64 native states recorded, row7 overwrite with other seven rows held,5ms hold maximum10.64mV, write error below1.43mV, selected-read disturbance below4.89mV. Storage-only: external decoder/drivers and uncalibrated read offsets; no compute-sharing or chip qualification.





One actual256MOS/64MIM8x8 shared-row/shared-column bank with all2226 nonnegative routing-cap branches. All64 states initialized through real TGs; rows0-6 held while row7 is overwritten on shared DATA columns, then each state held at least5ms with DATA rail stress. Sequential native source-follower reads of rows0and7; six middle rows remain unselected. All64 analog states and8 read columns recorded; no ideal output buffer. External ideal references/wordlines/data and gated1uA column-current fixtures. Typical27C/noise disabled. Source-follower offset uncalibrated. No decoder/driver geometry, trained beta, threshold/RMS, large-array loading, population service, accuracy or fullchip acceptance. Catalog revision66: 20 module artifact sets/50 characterization assemblies. Full goal remains incomplete.





## shared row column 2x2 analog memory bank - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_compact_memory_bank2x2_v4_article_boundary.json) records gf180_compact_memory_bank2x2_v4: 16 native MOS, 0 resistors and 4 MIMs; full DRC0/LVS, GDS reimport and real LEF, 155 nonnegative flat capacitance branches. Nominal simulation completed; `native_shared_bank_sequence_observed=True`. Actual shared-row/column bank1300.588um2; selective overwrite retains other row, four5ms holds with maximum10.21mV disturbance, native readout monotonic and final read disturbance below4.65mV. Read offsets and external decoder/driver remain unqualified.





One actual16MOS/4MIM2x2 shared-row/shared-column bank with all155 nonnegative routing-cap branches. Both rows initialized via real TG; row0 held while row1 is overwritten on shared DATA columns, then each held at least5ms with DATA rail stress before sequential native source-follower reads. External ideal references/wordlines/data and gated1uA column-current fixtures. Typical27C/noise disabled. Source-follower offset uncalibrated. No decoder/driver geometry, trained beta, threshold/RMS, large-array loading, population service, accuracy or fullchip acceptance. Catalog revision65: 20 module artifact sets/49 characterization assemblies. Full goal remains incomplete.





## compact 4T 50fF analog memory - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_compact_analog_memory_4t_v4_article_boundary.json) records gf180_compact_analog_memory_4t_v4: 4 native MOS, 0 resistors and 1 MIMs; full DRC0/LVS, GDS reimport and real LEF, 38 nonnegative flat capacitance branches. Nominal simulation completed; `native_compact_memory_write_hold_read_observed=True`. Area138.03um2; three5ms holds under8.8mV disturbance; write-release5.3-7.1mV; monotonic native source-follower read with869-969mV offset requiring downstream calibration. Storage/access only, no trained beta, array loading or full-chip acceptance.





Three independent actual routed4T/50fF-MIM cell instances, all38 nonnegative extracted routing branches per cell retained. Initial DC write through native TG stores1.0/1.2/1.4V, then both write gates turn off at1us. Unselected ideal DATA sources switch to0V at2ms and3.3V at4ms. Record a full5ms hold from1us to5.001ms before read selection. Native NF source-follower plus read-select drives a separately gated ideal1uA external column sink; selected read sampled5.1ms and release5.19ms. No ideal output buffer, state restore or numerical conversion. Ideal voltage/wordline/reference/column-current fixtures remain external; supply energy excludes their drivers. Typical27C/noise disabled, unchanged1e-6 tolerance. This cell has no trained beta/threshold/inhibition/adaptation logic; array bus loading, decoder, calibrated read offsets, noise/PVT and full-model5ms service remain unfinished. Three memory records do not prove full population behavior. Catalog revision64: 20 module artifact sets/48 characterization assemblies. Full goal remains incomplete.





## Assembly priority and startup branch review - 2026-10-11





Full64 extracted ROOT reaches the observed10mV DC-error band after1.781us for half-active and1.682us for all-active, within the recorded2us windows. The1.5us gate remains false. These are finite fixture observations, not calibrated model accuracy or5ms service. Native joined controller/writer UIC startup also timed out, last logged0.721us of22us; preserve independent module simulations and defer further tuning. Full64-to-native-clip/strength assembly is now being built.





## full64 native candidate penalty energy root - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_formatted_energy64_v3_article_boundary.json) records gf180_formatted_energy64_v3: 2304 native MOS, 2816 resistors and 1024 MIMs; full DRC0/LVS, GDS reimport and real LEF, 86538 nonnegative flat capacitance branches. Nominal simulation completed; `native_full_channel_energy_transient_observed=False`. Completed bounded native fixture, with exact source/GDS/flat graph qualification and physical views. Measured precision limitations retained. Not full-chip layout, trained-model accuracy or full-population5ms acceptance.





One180s runtime extension justified by4.97215us of requested6us progress at120s; unchanged circuitry, solver, fixtures and gates. Actual64 candidate-minus-penalty native formatters and full64 energy/mean-root connected in one flat2304MOS2816R1024MIM parent with all nonnegative extracted routing-capacitance branches retained. Three sequential levels in6us: all candidates1.2V, half2V, all2V; shared penalty1.2V,VBASE.9,VZERO1.2,VDD3.3,64uA master,typical27C. No ideal internal candidate-minus-penalty arithmetic or formatted gate drive. Candidate/penalty sources remain external ideal buffered fixtures. Compare samples1.5/3.5/5.5us against independent frozen source-hierarchy DC report. Compositional exact source/GDS and flat-device graph qualification retained; failed historical Netgen matching logs are not treated as passing. No fitted correction, calibrated trained RMS/epsilon, noise/PVT, all-neuron5ms service or full-chip acceptance Catalog revision62: 20 module artifact sets/47 characterization assemblies. Full goal remains incomplete.





## Connected native recheck boundary - 2026-10-11





Full64 parent flat DRC and exact native connectivity pass with86538 nonnegative aggregate routing-capacitance branches. First6us transient reached4.97215us before120s timeout; one180s extension is justified by measured progress. Scheduled618MOS controller/writer source/GDS/exact flat graph and5607 routing branches plus53-port LEF complete. First connected transient aborts0.21us at ideal Vclock branch; one focused fixture repair reuses the proven native two-inverter clock driver. No solver tolerance or physical parent changes. Review: `artifacts/analog_asic/results/gf180_connected_native_recheck_review.json`. Pending results: `artifacts/analog_asic/results/gf180_two_native_rechecks_20261011.json`. Neither timeout nor aborted trace is counted as completed simulation. Full-chip layout, original-float accuracy and5ms service remain incomplete.





## pre reset RMS aware native bin phase control - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_bin_commit_controller_v2_article_boundary.json) records gf180_bin_commit_controller_v2: 374 native MOS, 0 resistors and 0 MIMs; full DRC0/LVS, GDS reimport and real LEF, 2146 nonnegative flat capacitance branches. Nominal simulation completed; `all_sequencing_pass=True`. One actual native14us wait/completion fixture passes all ten ordered phases and zero pulsed-control overlap. RMS capture releases8.724493us before reset starts10.222500us and adaptation write starts12.222347us. Full DRC/LVS/GDS, flat2146 branches and18-port LEF complete. Native clock1MHz is a characterization fixture; analog load/settling and dense full-population5ms remain unproven. Separate three-case handshake RTL is not substituted for this native result.





Actual374MOS native ten-stage bin-control sequencer, actual nonnegative flat routing capacitance. One native-driver case per300s bounded run after measured7.72673us progress in120s; one runtime extension, no physics/solver/gate changes: idle, waitACCUM untilCOMPLETE, or reset while waiting.1MHz fixture clock; exact unchanged solver. Ordered AGE,BETA,ACCUM,RMS_SETTLE,RMS_CAPTURE,DETECT,RESET_STATE,INHIBIT,ADAPT,DONE. RMS capture physically releases before reset/adaptation strobe; no connected analog functional/timing/settling claim. COMPLETE external matching-bin token, downstream analog modules not connected. Separate handshake RTL is not substituted for this native circuit. No native all-population5ms/model/full-chip acceptance. Catalog revision60: 20 module artifact sets/46 characterization assemblies. Full goal remains incomplete.





## Full64 source/GDS connectivity and native RMS phase control - 2026-10-11





Full64 formatted energy parent source and GDS pass full DRC0. Exact compositional graph comparison independently proves every subcircuit interface, connection and transistor/passive dimension; original failed full-flat Netgen matching remains recorded. Real71-port LEF exported. Flat extraction is still running in original container7f79ed9c3247; no transient/full-population result inferred.





Native374MOS ten-stage controller adds RMS_SETTLE and RMS_CAPTURE before DETECT/RESET/INHIBIT/ADAPT. Source/GDS DRC0/LVS, flat2146 nonnegative branches and real18-port LEF complete. Native wait/completion nominal simulation pending. Separate handshake RTL passes initialization/order, zero-event completion waiting and stale-high acknowledgement cases; Yosys generic72 cells/5 control flip-flops, no physical mapping claim. Evidence: `artifacts/analog_asic/results/gf180_analog_bin_sequencer_RTL_three_cases.json`. Catalog59 retains20 modules/45 completed assemblies plus these explicitly incomplete assemblies.





## Connected64-channel RMS and sampling repair - 2026-10-11





Actual64 native formatters plus64 energy/root receivers (2304MOS/2816R/1024MIM) complete three source-hierarchy DC cases. ROOT=2.429009/2.324764/2.254135V; supply6.180/6.235/6.290mW. Exact parent-net bijection and identical qualified child definitions prove source hierarchy connectivity independently of unresolved full-flat Netgen symmetry matching. Source DRC0 and GDS exist; GDS readback and flatRC qualification remain unfinished, so this is not added to the45 completed assemblies. Evidence: `artifacts/analog_asic/results/gf180_formatted_energy64_v3_native_hierarchy_dc_src06716ac6c5d8.json`.





Sampling revision3 adds four22um MIMs and passes physical source/GDS/flat3234-branch/LEF checks, but transient aborts at8.99us despite rc0. Preserve completed revision2 with159mV capture-release error; no further storage/solver sweep. Review: `artifacts/analog_asic/results/gf180_pre_reset_capture_storage_branch_review.json`. Full neuron accuracy,5ms population service and full-chip layout remain incomplete.





## shielded pre reset RMS capture resident write - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_sampled_rms_resident_write_v2_article_boundary.json) records gf180_sampled_rms_resident_write_v2: 236 native MOS, 98 resistors and 72 MIMs; full DRC0/LVS, GDS reimport and real LEF, 3232 nonnegative flat capacitance branches. Nominal simulation completed; `pre_reset_capture_write_sequence_observed=False`. All three60us native cases complete after one runtime extension justified by measured progress. Local routing avoids the prior1.4V excursion/abort; captured amplitude still shifts152-159mV at release, while held change during write is below2mV and write tracks buffered hold below0.9uV. Capture precision fails and is not accepted. Preserve result; review capture charge/storage ratio before further changes.





Native236MOS98R72MIM capture of RMS/strength amplitude before spike/reset with high-impedance held nodes confined to a local shielded island, One180s runtime extension based on prior120s progress to43.12us of60us; exact same physics/fixtures/gates/solver. Native unity buffer isolates captured amplitude from actual resident write TGs, native resident age/amplitude/expiry retained. Actual flat extraction, typical27C,60us three ordered fixtures. CAPTURE ends8/28/48us; ROOT deliberately changes9/29/49us; SPIKE writes10..15/30..35/50..55us. Sampling and write phases never overlap. First capture is physically active at DC operating point; no ideal held state, ADC, quantized state or measured-output correction. Frozen ROOT_REF2.412488477821002 and external10uA PMOS/1uA NF masters. ROOT is still external; no all-channel energy reduction connection or native autonomous phase schedule/full model/5ms/full-chip acceptance. Known amplitude gain, capture/write kick and init/expiry errors retained. Catalog revision57: 20 module artifact sets/45 characterization assemblies. Full goal remains incomplete.





## Full-width native reducer transients - 2026-10-11





Actual64-channel448MOS and128-channel896MOS reducers complete6us extracted native transients with three input fixtures. ROOT is settled to its independently frozen DC values at samples1.5us after level changes; native RMS half/full ratio remains0.59627 versus0.70711 ideal. Coverage/power arithmetic and exact15-actor width mapping are in `artifacts/analog_asic/results/gf180_actual_adaptation_reducer_width_coverage.json`; no full-model accuracy, calibrated all-vector RMS or population5ms acceptance. Pre-reset capture revision1 aborts8.99us; extracted AMP_CAPTURE-to-CAPTUREB coupling is500.33fF, supporting a focused local shielded routing repair. Revised parent is not yet simulated.





## actual128 channel native energy reduction - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_energy_mean_root128_v1_article_boundary.json) records gf180_energy_mean_root128_v1: 896 native MOS, 0 resistors and 0 MIMs; full DRC0/LVS, GDS reimport and real LEF, 14692 nonnegative flat capacitance branches. Nominal simulation completed; `native_full_channel_energy_transient_observed=True`. Actual896MOS128-kernel128-receiver layout; three DC points and6us native extracted transient complete. ROOT agrees with frozen DC values at1.5us after input changes in these ideal-input fixtures. Native RMS ratio0.59627 versus ideal0.70711 remains unaccepted. Continuous reducer supply power3.45-3.67mW; duty control, actual candidate formatting and full-population5ms remain incomplete.





Actual64/128-channel native energy kernel/current-sum and matched parallel diode mean/root receiver, flat native devices and extracted capacitance present. Six-us native transient with three sequential levels: all differential0, half channels plus/minus100mV, all channels plus/minus100mV, VBASE.9V,VDD3.3V,typical27C. External ideal gate-input fixtures common within each half; native candidate/penalty formatters and original-float scaling are not connected. Loaded native ROOT settling measured at1.5/3.5/5.5us against the independently frozen three-DC-case report; external gate inputs are ideal fixtures. This is not whole5ms population service or calibrated RMS/noise/epsilon. No fitted output correction. Full actual channel count/layout is present; no whole-model SPICE, model accuracy or full-chip acceptance. Catalog revision55: 20 module artifact sets/44 characterization assemblies. Full goal remains incomplete.





## actual64 channel native energy reduction DC - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_energy_mean_root64_v1_article_boundary.json) records gf180_energy_mean_root64_v1: 448 native MOS, 0 resistors and 0 MIMs; full DRC0/LVS, GDS reimport and real LEF, 3636 nonnegative flat capacitance branches. Nominal simulation completed; `native_full_channel_energy_reduction_observed=True`. Actual448MOS64-kernel64-receiver layout, three native DC operating points completed. Half/full zero-subtracted ratio0.59627 versus ideal0.70711; supply power1.73-1.84mW per continuously biased reducer in these fixtures. This is DC only: candidate formatting, transient settling, duty control and full-population service remain incomplete. Do not extrapolate spacious fixture footprint as final dense area.





Actual64/128-channel native energy kernel/current-sum and matched parallel diode mean/root receiver, flat native devices and extracted capacitance present. Three DC cases: all differential0, half channels plus/minus100mV, all channels plus/minus100mV, VBASE.9V,VDD3.3V,typical27C. External ideal gate-input fixtures common within each half; native candidate/penalty formatters and original-float scaling are not connected. DC establishes operating points, not loaded transient settling/5ms service or calibrated RMS/noise/epsilon. No fitted output correction. Full actual channel count/layout is present; no whole-model SPICE, model accuracy or full-chip acceptance. Catalog revision54: 20 module artifact sets/43 characterization assemblies. Full goal remains incomplete.





## representative four state shared bus tile - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_resident_state_tile4_v2_article_boundary.json) records gf180_resident_state_tile4_v2: 16 native MOS, 0 resistors and 4 MIMs; full DRC0/LVS, GDS reimport and real LEF, 148 nonnegative flat capacitance branches. Nominal simulation completed; `native_independent_state_tile_observed=True`. Four physical state identities; three selective writes are monotonic and one common beta phase moves state toward1.2V. Unwritten-state disturbance reaches17.26mV and apparent beta varies0.682/0.689/0.813 across the three nonzero levels, versus representative trained0.881893. These errors are retained;260.3x239.4um is integration geometry and must not be presented as final dense area. Full hierarchy/interconnect remain incomplete.





Native16MOS4MIM2x2 resident tile with actual extracted shared DATA/VCM/AUXRESET/BETA/AUXREF supplies, distinct permanent STATE/AUX nodes and individual WRITE/WRITEB. All four physically initialized1.2V through writers; three selective writes .9/1.5/2.1V while fourth holds; shared data rebiases1.2, auxiliary reset releases then one common beta phase. Ideal complementary clock/reference voltage fixtures; no ideal state correction or digital numerical state. Typical27C deterministic70us fixture, not5ms retention/noise/PVT or trained-beta acceptance. Original representative leaf auxiliary overlap retained; array routing changes capacitance, so previous beta calibration does not transfer. Footprint is representative integration geometry, not final optimized dense array or full-chip area. Catalog revision53: 20 module artifact sets/42 characterization assemblies. Full goal remains incomplete.





## connected native rms resident amplitude write - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_rms_resident_write_v1_article_boundary.json) records gf180_rms_resident_write_v1: 224 native MOS, 98 resistors and 66 MIMs; full DRC0/LVS, GDS reimport and real LEF, 3182 nonnegative flat capacitance branches. Nominal simulation completed; `native_rms_amplitude_write_observed=True`. Three60us native root/clip/strength-to-resident write cases complete with monotonic written amplitude and maximum on-write tracking error3.49nV in this deterministic bench. Write release shifts storage by approximately21.43mV; this measured error remains unaccepted. ROOT is an external interface fixture; full channel reduction and pre-reset sampling remain incomplete.





Native224MOS98R66MIM RMS root conversion/clip/strength output directly drives resident amplitude write TGs, with initialization/expiry/triangle/product retained. Actual flat extracted wiring, typical27C;60us three sequential ROOT fixtures (zero,mid,overrange), each followed by5us spike write and release. No ideal AMP_DATA driver, output correction or fitted subtraction. External ROOT remains an interface fixture; no all-channel energy reduction/feedback. Frozen ROOT_REF2.412488477821002 from independent high-common-mode buffer characterization, supplied1uA NF and drained9uA PMOS masters. ADC and quantized numerical state absent. Known native product gain/offset and write kick retained; no trained normalization, complete bin/RMS sample sequencing, model/population5ms/full-chip acceptance. Catalog revision52: 20 module artifact sets/41 characterization assemblies. Full goal remains incomplete.





## resident adaptation initialization expiry - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_resident_adaptation_expiry_v3_article_boundary.json) records gf180_resident_adaptation_expiry_v3: 131 native MOS, 48 resistors and 34 MIMs; full DRC0/LVS, GDS reimport and real LEF, 1681 nonnegative flat capacitance branches. Nominal simulation completed; `resident_expiry_initialization_sequence_observed=False`. 200us loaded sequence completes but fails: initial AGE falls1.35 to1.112V after INIT release, spuriously enabling advance; spike reset works, loaded age steps are too small to reach expiry in two advances. Preserve measured errors and carry this layout forward for integration; no precision sweep or functional acceptance.





Native131MOS48R34MIM resident adaptation, loaded analog expiry comparator and advance gate, two initialization TGs, actual extracted interconnect and native control inverters.200us nominal typical27C: physical INIT writes inactive AGE1.35 and zero amplitude1.2, initial advance must be blocked; spike writes AMP1.5 and resets AGE1.2, two advances approach/cross expiry1.22, later advance must be blocked, second spike resets and permits another advance. VPEAK1.21,VEXPIRE1.22 is a local analog fixture and not trained all-channel calibration. Five physical PMOS references with external5uA. Known write/age-step/product errors retained. No full-model accuracy, retention/noise/corners or full-population5ms/full-chip acceptance. Catalog revision51: 20 module artifact sets/40 characterization assemblies. Full goal remains incomplete.





## Global completion barrier composition - 2026-10-11





The folded2300MOS layout has source/GDS/flat DRC0 and LVS plus real LEF. Its extracted25-join connectivity covers all25 actors and queue drain exactly once, depth5; three logical protocol records pass using the separately characterized native sticky-join contract. This is logical composition evidence, not a completed full native transient or clock/RC timing result. Native120s timeout and switch-simulator initialization/crash failures remain preserved. See `artifacts/analog_asic/results/gf180_global_barrier_method_review.json`. Catalog revision50 retains20 reusable modules/39 nominal characterization assemblies; control composition is counted separately.





## native rms clip strength high common mode - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_rms_clip_strength_frontend_v2_article_boundary.json) records gf180_rms_clip_strength_frontend_v2: 93 native MOS, 50 resistors and 32 MIMs; full DRC0/LVS, GDS reimport and real LEF, 1402 nonnegative flat capacitance branches. Nominal simulation completed; `native_clip_strength_chain_observed=True`. Three fixtures complete with maximum clipping error6.993mV and monotonic settled amplitude. Frozen independent buffer calibration applied electrically through ROOT_REF; actual all-channel root loading, trained normalization and write connection remain incomplete. No further precision sweep.





Native93MOS50R32MIM NF-input high-common-mode compensated root buffer, native offset subtractor, analog clamp, clamp-output buffer and native analog strength multiplier, actual flat extracted wiring, typical27C. ROOT_REF is a frozen external analog-reference voltage: zero-energy root interpolated through the independent high-common-mode buffer characterization BEFORE connected simulation, with no fit to connected outputs; it is driven electrically into native subtractor, not applied to measured output in software. Three ideal buffered root-input fixtures: zero, measured mid and overrange; STRENGTH1.4V,VZERO/VMIN1.2V,VMAX1.8V,VBASE.9V,separate4uA PMOS and1uA supplied NF references for five physical diodes. Native product gain/offset retained. This is a post-root interface fixture, not a connected all-channel RMS: root source/loading, epsilon1e-8, exact trained normalization/strength mapping and resident write/init remain incomplete. No full adaptation/model/population5ms/full-chip acceptance. Catalog revision49: 20 module artifact sets/39 characterization assemblies. Full goal remains incomplete.





## connected root clip strength with recorded failure - 2026-10-11





[Assembly boundary](../artifacts/analog_asic/results/gf180_rms_clip_strength_frontend_v1_article_boundary.json) records gf180_rms_clip_strength_frontend_v1: 93 native MOS, 50 resistors and 32 MIMs; full DRC0/LVS, GDS reimport and real LEF, 1398 nonnegative flat capacitance branches. Nominal simulation completed; `native_clip_strength_chain_observed=False`. All three50us fixtures complete but functional gate fails: zero/mid clip errors119.5/79.3mV and mid output unsettled; high clip correct. PMOS-input root buffer operates above its characterized common-mode window around2.3-2.43V. Preserve failure; a suitable input-common-mode buffer is the focused repair candidate. Actual model epsilon/gain/strength/write remain unfinished. Full physical/MIM dimension checks pass; physical completeness is not functional acceptance.





Native93MOS50R32MIM compensated root gate-input buffer, native offset subtractor, analog clamp, clamp-output buffer and native analog strength multiplier, actual flat extracted wiring, typical27C. ROOT_REF is a frozen external analog-reference voltage from the preceding physical zero-energy fixture; it is driven electrically into native subtractor, not applied to measured output in software. Three ideal buffered root-input fixtures: zero, measured mid and overrange; STRENGTH1.4V,VZERO/VMIN1.2V,VMAX1.8V,VBASE.9V,5uA for five physical references. Native product gain/offset retained. This is a post-root interface fixture, not a connected all-channel RMS: root source/loading, epsilon1e-8, exact trained normalization/strength mapping and resident write/init remain incomplete. No full adaptation/model/population5ms/full-chip acceptance. Catalog revision48: 20 module artifact sets/38 characterization assemblies. Full goal remains incomplete.





## compensated native voltage subtractor - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_candidate_penalty_subtractor_v2_article_boundary.json) records gf180_candidate_penalty_subtractor_v2: 8 native MOS, 4 resistors and 4 MIMs; full DRC0/LVS, GDS reimport and real LEF, 55 nonnegative flat capacitance branches. Nominal simulation completed; `native_subtractor_10mv_gate_pass=True`. Original minimum capacitors retained with two added native22um compensation devices. Three fixtures pass; sampled maximum subtraction error0.1954mV. Exact MIM dimension-class source/flat/GDS comparison passes; original mixed-size warnings retained. Loaded root conversion/strength chain and trained gain remain separate connected evidence.





Native8MOS4R4MIM candidate-minus-penalty unity subtractor, actual extracted resistor/OTA/compensation/wiring, typical27C. Three external buffered-voltage fixtures atVCOM1.65V, external1uA reference. TargetADJUSTED=CANDIDATE-PENALTY+VCOM. No ideal arithmetic inside circuit. Standalone output; actual held-candidate isolation, shared-penalty calibration/fanout, RMS and threshold connections remain unfinished. Local10mV gate is bringup, not model precision/population5ms/full-chip acceptance. Catalog revision47: 20 module artifact sets/37 characterization assemblies. Full goal remains incomplete.





## native analog adaptation expiry advance gate - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_adaptation_expiry_gate_v1_article_boundary.json) records gf180_adaptation_expiry_gate_v1: 18 native MOS, 0 resistors and 0 MIMs; full DRC0/LVS, GDS reimport and real LEF, 73 nonnegative flat capacitance branches. Nominal simulation completed; `all_analog_expiry_gate_fixtures_pass=True`. Three active/expired/reset-age voltage fixtures pass with native comparison and complementary gated advance. Expired age may be held above2T for fixed inference duration because its triangle stays zero until spike reset; documented in adaptation_expiry_observable_state_contract_v1.json. Resident initialization/reset and continuous trained-duration voltage mapping remain to connect and characterize. AGE fixture is externally driven; this is not complete resident adaptation or dense-array acceptance.





Native18MOS analog AGE<VEXPIRE comparator and advance gate, actual extracted interconnect, typical27C,1uA physical reference. Three wide voltage fixtures: active1.4V, expired2.2V, new-spike reset fixture1.2V;VEXPIRE2.0V,1us advance command clock. Native gate blocks expired age advancement and resumes after age reset. AGE is externally driven for this interface fixture; connected resident initialization/spike/reset/continuous-duration mapping and near-boundary precision remain unqualified. Expired analog age held above2T has zero triangle until next spike, observationally equivalent for frozen inference duration; no digital numeric state or duration rounding. No full adaptation/model/population5ms/full-chip acceptance. Catalog revision46: 20 module artifact sets/36 characterization assemblies. Full goal remains incomplete.





## Connected readout three independent records - 2026-10-11





[Aggregate evidence](../artifacts/analog_asic/results/gf180_six_class_readout_v3_three_independent_records.json): same physical458MOS30MIM layout completes three independent50ms ten-bin records, expected native winners1/0/5, label capture and hold after EVALoff. References independent per record; native current fixtures rather than trained final synapses. Earlier three-bank common-reference timeout preserved; both reference isolation and output/initial timestep changed, so cause is not isolated. Reset offsets/cross-class coupling/score gain and exact ties remain unaccepted. Catalog revision45 retains20 modules/35 characterization assemblies; this supplement adds case coverage, not a new module or full-chip completion.





## connected analog record native winner label capture - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_six_class_readout_v3_article_boundary.json) records gf180_six_class_readout_v3: 458 native MOS, 0 resistors and 30 MIMs; full DRC0/LVS, GDS reimport and real LEF, 2492 nonnegative flat capacitance branches. Nominal simulation completed; `all_native_readout_capture_fixture_cases_pass=True`. One isolated bank with its own references completes50ms ten-bin analog record, native class1 winner, categorical capture and hold after selector disable. Three-bank common-reference benchmark timeout preserved; isolated output/initial timestep0.1us, maximum20us and solver tolerances unchanged. Only one fixture qualified here; other signs/rankings, near ties, reset offsets and cross-class coupling remain to be characterized. Original float numeric state remains analog. Exact MIM dimension-class LVS for source/flat/GDS passed.





One bank with its own master references; output/initial timestep0.1us avoids oversized initial allocation estimate, maximum timestep20us and solver tolerances unchanged. Native458MOS30MIM connected six-class analog bank, evaluation-controlled winner and categorical label capture; twelve additional physically routed22um MIMs compensate the six state buffers; all original storage retained. One isolated class1-dominant extracted fixture bank, selected after three-fixture activation failure method review, native reset drivers.1ms reset then50ms ten-event analog record, selector EVALoff during accumulation; enable at51ms, sample51.075..51.076ms, disable at51.1ms and observe held label through51.2ms. Native standby TG and separate6uA state/1uA selector references for one bank; no ideal bias switching/argmax/score drive. Earlier labels ignored until first valid record capture, which initializes static label bits; no numeric state quantization. Ideal signed-current fixtures remain instead of trained16-to6 injectors. Reset offsets/routing gain/coupling/near-exact ties, actual controller/valid protocol and dense full-frame/model/population5ms/full-chip acceptance unqualified Catalog revision44: 20 module artifact sets/35 characterization assemblies. Full goal remains incomplete.





## native candidate penalty energy frontend - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_formatted_two_channel_energy_v1_article_boundary.json) records gf180_formatted_two_channel_energy_v1: 72 native MOS, 88 resistors and 32 MIMs; full DRC0/LVS, GDS reimport and real LEF, 2336 nonnegative flat capacitance branches. Nominal simulation completed; `monotonic_native_formatted_energy_observed=True`. Native differential formatter replaces ideal input arithmetic for two-channel energy. Zero/one/opposite-sign cases settle and respond monotonically. Zero-subtracted one/two ratio0.59506 versus ideal0.70711 remains an RMS accuracy limitation, not a gate to more precision sweeps. Exact MIM dimension-class source/flat/GDS verification resolves original comparison ambiguity. Epsilon/clip/strength/all-channel reduction and full-chip assembly remain unfinished.





Native72MOS88R32MIM compensated candidate-minus-shared-penalty differential formatting into native two-channel energy-square/current-sum/root circuit, actual flat extracted parasitics, typical27C. Three sequential zero/one-active/two-opposite-sign fixtures. CANDIDATE_A/B1.2/2.0/.4V, PENALTY/VZERO1.2V, VBASE.9V, two physical reference diodes with external2uA. Native formatter produces plus/minus (candidate-penalty)/8; no ideal subtractor, gate formatter or sqrt inside cell. Four unused sum OTA branches remain to reuse qualified physical formatter; this is characterization geometry, not a dense optimized frontend. Root threshold offset/nonideal RMS gain, epsilon, clip, learned strength, actual all-channel count/loading and model/population5ms/full-chip acceptance remain unfinished. Catalog revision43: 20 module artifact sets/34 characterization assemblies. Full goal remains incomplete.





## Physical compensation verification supplement - 2026-10-10





[Independent verification audit](../artifacts/analog_asic/results/gf180_physical_compensation_verification_audit.json) checks formatter revision3, product revision4, buffer revision2 and resident revision4. Original Netgen connectivity comparisons report mixed-size parallel-capacitor property/symmetry warnings. Independent comparison copies classify each native MIM by exact parsed width/length; all source, flat and GDS comparisons pass connectivity and dimensions. No physical geometry, simulator model, device value or tolerance changed; all failed comparison attempts preserved. Rely on this supplemental evidence for capacitor-size matching rather than the original connectivity-only success text.





## physically compensated resident adaptation sequence - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_resident_adaptation_product_v4_article_boundary.json) records gf180_resident_adaptation_product_v4: 109 native MOS, 48 resistors and 34 MIMs; full DRC0/LVS, GDS reimport and real LEF, 1514 nonnegative flat capacitance branches. Nominal simulation completed; `resident_native_product_sequence_observed=True`. Complete200us sequence within120s bound; sampled triangle maxerror0.11796mV, buffer maxerror0.13806mV, penalty increases1.23567mV after two age advances. Write-release error-65.424mV and unequal age steps remain unaccepted. Mixed-size parallel MIM ambiguity in original Netgen logs is resolved by supplemental exact dimension-class LVS for source/flat/GDS: artifacts/analog_asic/verification/dimension_class_mim/gf180_resident_adaptation_product_v4/qualification.json. This is local sequence evidence; trained RMS/expiry/full-channel mapping and dense assembly remain incomplete.





Native109MOS48R34MIM resident age/amplitude to native buffered triangle and amplitude buffer to native formatter/product/linear receiver. Actual extracted interconnect, native phase drivers, typical27C. One bounded200us local sequence initialized by DC operating point with SPIKE asserted (resident storage physically written/reset); not a cold-start or5ms retention test. Release write, two age advances, amplitude data changes while write off, spike overwrite/reset, third advance. Raw TRIANGLE is now gate-isolated by a dedicated native unity buffer before resistive formatter load; physically compensated product and both interface buffers, fourteen additional22um native MIMs preserve original capacitors. No ideal AGE/AMPLITUDE/TRIANGLE/product/output clamp. External4uA shared bias for4native references, PP2.6/PCAS2.2/PARK/VZERO1.2,VPEAK1.6,VBASE.9,VCOM1.65V. Analog age voltage uncalibrated; actual model duration/RMS amplitude/expiry/all-channel mapping and dense placement unfinished. Known write-release and cross-coupling errors retained. No model accuracy, complete adaptation/population5ms/full-chip acceptance. Catalog revision42: 20 module artifact sets/33 characterization assemblies. Full goal remains incomplete.





## compensated gate input unity buffer - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_amplitude_buffer_v2_article_boundary.json) records gf180_amplitude_buffer_v2: 8 native MOS, 0 resistors and 4 MIMs; full DRC0/LVS, GDS reimport and real LEF, 24 nonnegative flat capacitance branches. Nominal simulation completed; `nominal_buffer_10mv_gate_pass=True`. Two extra native22um compensation MIMs preserve both original5um capacitors. Three unloaded voltage fixtures and return step pass; maximum sampled error20.876uV. Loaded connected resident/readout behavior remains to be measured; this is not model precision acceptance.





Extracted native8MOS4MIM amplitude unity buffer. Three ideal-source amplitude voltages1.2/1.5/1.8V and return step; external1uA reference, typical27C, actual parasitics. Unloaded output; actual resident storage and native resistive formatter load require connected measurement. Local10mV gate is bringup only, not model precision or full adaptation/population5ms/full-chip acceptance. Catalog revision41: 20 module artifact sets/32 characterization assemblies. Full goal remains incomplete.





## physically compensated native adaptation product - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_native_adaptation_product_v4_article_boundary.json) records gf180_native_adaptation_product_v4: 42 native MOS, 46 resistors and 20 MIMs; full DRC0/LVS, GDS reimport and real LEF, 1210 nonnegative flat capacitance branches. Nominal simulation completed; `positive_native_product_observed=True`. Same three fixtures now give high/mid increment ratio6.003956 versus ideal6, with sampled late0.5us changes below7e-15V; earlier ratio3.692 and oscillation retained in revision2. Added ten physical22um native MIMs retain all original capacitors. This qualifies this nominal product fixture only; resident adaptation, trained precision and full layout remain incomplete.





Native42MOS46R20MIM fully native voltage-format/current-product/linear-receiver chain, actual extracted wiring including ten additional physically routed22um native MIM compensation capacitors, typical27C. Three externally driven buffered amplitude/triangle fixtures; VZERO1.2,VBASE.9,VCOM1.65V and master1uA. No ideal gate arithmetic/product/receiver/output clamp inside circuit. Native formatter ratio1/8 scales each deviation; physical square-difference core drives feedback receiver. Resident storage and actual buffered age triangle not connected yet; trained amplitude/triangle normalization, all-channel reduction, noise/PVT and dense area remain unfinished. Raw offset and product nonlinearity retained. No full adaptation/model accuracy/population5ms/full-chip acceptance. Catalog revision40: 20 module artifact sets/31 characterization assemblies. Full goal remains incomplete.





## native evaluation controlled class winner - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_six_class_winner_eval_v1_article_boundary.json) records gf180_six_class_winner_eval_v1: 284 native MOS, 0 resistors and 0 MIMs; full DRC0/LVS, GDS reimport and real LEF, 1803 nonnegative flat capacitance branches. Nominal simulation completed; `native_eval_winner_cases_pass=True`. Native standby TG keeps selectorBIAS3.290895V with EVALoff; activeBIAS2.482967V with EVALon. Three separated-score winners1/0/5 pass. State buffers need independent bias. This addresses sequencing during accumulation; connected50ms native readout/capture and exact ties remain unqualified.





Native284MOS one-hot winner with native evaluation bias standby clamp, actual extracted wiring, typical27C. Three separated-score fixtures class1/0/5. EVALlow clampsBIAS toVDD through native TG while external1uA reference continues; EVALhigh releases clamp for active native comparator operation. Record scores remain externally buffered fixtures, not actual class-current bank. Native winner cases and standby/active bias measured. No exact/near tie, record capture, loaded bank/PVT/noise/model/population5ms/full-chip acceptance Catalog revision39: 20 module artifact sets/30 characterization assemblies. Full goal remains incomplete.





## native categorical label capture - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_class_label_capture_v1_article_boundary.json) records gf180_class_label_capture_v1: 114 native MOS, 0 resistors and 0 MIMs; full DRC0/LVS, GDS reimport and real LEF, 389 nonnegative flat capacitance branches. Nominal simulation completed; `native_label_capture_hold_pass=True`. Six categorical labels captured from native phase pair/sixDFFs: class1/0/5 capture and hold pass after input winners change. Known-zero initialization sample required; no asynchronous reset. Numerical SNN membrane/weights stay analog. Record-done controller and actual class-bank/winner/capture connection remain next; no full readout acceptance.





Native114MOS class-label capture, actual extracted phase generator and six static master/slave DFFs. Initialization sample of known-zero WIN vector, then capture labels1/0/5 on SAMPLE falling, input winner changes during closed-master hold. Categorical output bits only; numeric SNN state/weights remain analog.8us standalone fixture, external one-hot winner and sample commands. Native readout/bank loading and ten-bin record-done controller not connected; tie/model/PVT/population5ms/full-chip acceptance unfinished. Catalog revision38: 20 module artifact sets/29 characterization assemblies. Full goal remains incomplete.





## native six class one hot winner - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_six_class_winner_v1_article_boundary.json) records gf180_six_class_winner_v1: 280 native MOS, 0 resistors and 0 MIMs; full DRC0/LVS, GDS reimport and real LEF, 1715 nonnegative flat capacitance branches. Nominal simulation completed; `native_one_hot_winner_cases_pass=True`. Native outputs selectclasses1/0/5 in three separated-score fixtures, one winner near3.3V and all others near0V. No ideal argmax inside cell. Exact/near ties and lowest-index tie contract remain unqualified; outputs not captured yet. Next connect actual six-class analog accumulation bank and record-done capture; no model accuracy acceptance.





Native280MOS six-class one-hot analog-score winner selector, actual extracted comparators/complements/AND gates and wiring, typical27C. Three external buffered score fixtures with strict separated maxima atclasses1/0/5; external1uA master. Native WIN logic outputs, no ideal comparison/argmax inside circuit. Scores are illustrative voltages, not actual trained readout. Exact/near tie handling, lowest-index tie contract, native class-bank loading, record-done capture andPVT/noise/model precision/population5ms/full-chip acceptance unqualified. Categorical output logic does not quantize analog numerical state. Catalog revision37: 20 module artifact sets/28 characterization assemblies. Full goal remains incomplete.





## connected resident adaptation product with recorded failure - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_resident_adaptation_product_v2_article_boundary.json) records gf180_resident_adaptation_product_v2: 101 native MOS, 48 resistors and 18 MIMs; full DRC0/LVS, GDS reimport and real LEF, 1488 nonnegative flat capacitance branches. Nominal simulation completed; `resident_native_product_sequence_observed=False`. The unchanged200us sequence completed within expanded660s bound after initial120s timeout. Functional gate is FALSE: triangle tracking error261.187mV, amplitude buffer/storage error6.667mV; penalty decreases322.390mV after two advances and remains unsettled. Stored write-release error-64.862mV. Raw TG-selected triangle is resistively loaded by native formatter; isolate with a native unity buffer before further connected evaluation. Shared-bias coupling/loaded-loop stability also remain unresolved. Completed artifacts do not qualify complete adaptation.





Same200us sequence and solver as preserved120s run; bounded660s wall limit justified by first run advancing normally to42.1205us without singular-matrix failure. Native101MOS48R18MIM resident age/amplitude to native buffered triangle and amplitude buffer to native formatter/product/linear receiver. Actual extracted interconnect, native phase drivers, typical27C. One bounded200us local sequence initialized by DC operating point with SPIKE asserted (resident storage physically written/reset); not a cold-start or5ms retention test. Release write, two age advances, amplitude data changes while write off, spike overwrite/reset, third advance. No ideal AGE/AMPLITUDE/TRIANGLE/product/output clamp. External3uA shared bias for3native references, PP2.6/PCAS2.2/PARK/VZERO1.2,VPEAK1.6,VBASE.9,VCOM1.65V. Analog age voltage uncalibrated; actual model duration/RMS amplitude/expiry/all-channel mapping and dense placement unfinished. Known write-release and cross-coupling errors retained. No model accuracy, complete adaptation/population5ms/full-chip acceptance. Catalog revision36: 20 module artifact sets/27 characterization assemblies. Full goal remains incomplete.





## six independent analog class records - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_six_class_current_bank_v1_article_boundary.json) records gf180_six_class_current_bank_v1: 60 native MOS, 0 resistors and 18 MIMs; full DRC0/LVS, GDS reimport and real LEF, 205 nonnegative flat capacitance branches. Nominal simulation completed; `all_fixture_rankings_match=True`. Three50ms six-class fixtures give software diagnostic winners1/0/5 as expected. Native argmax is absent. Channel-dependent reset offsets around-186..-189mV, gain differences and cross-channel coupling remain; zero-current class4 moves18.900mV in mixed fixture. Strong-margin rankings do not establish calibrated class-score or trained accuracy. One-location characterization bank, not full-frame dense layout.





Native60MOS18MIM six-class analog accumulation bank at one output spatial location. Three fixture banks in one extracted simulation, native reset drivers and18uA master for18physical references.1ms reset then50ms record with ten signed10us current pulses5ms apart. Fixture patterns class1 dominant/all-negative/class5 dominant; currents are ideal projection fixtures, not actual trained16-to6 weights/injector. Actual class STATE/OUTPUT nodes unforced after reset. Software argmax of measured outputs is diagnostic only; no native winner circuit implemented. Characterization routes may create class-dependent capacitive loading/reset offsets. No calibrated class-score accuracy/dense full-frame layout/population5ms/full-chip acceptance. Catalog revision35: 20 module artifact sets/26 characterization assemblies. Full goal remains incomplete.





## signed ten bin class current integrator - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_class_current_integrator_v1_article_boundary.json) records gf180_class_current_integrator_v1: 10 native MOS, 0 resistors and 3 MIMs; full DRC0/LVS, GDS reimport and real LEF, 36 nonnegative flat capacitance branches. Nominal simulation completed; `signed_ten_bin_accumulation_observed=True`. Ten signed100pA10us fixtures spaced5ms accumulate over50ms: positive+94.902mV, negative-94.947mV, zero drift+147uV. Reset-release offset-202.537mV remains unaccepted; quiet final4.779ms drift11.5..17.0uV and read-buffer error13.5..16.7uV. Current sources are fixtures, not actual learned16-to6 projection. Next six-class assembly and native selection; no final readout accuracy acceptance.





Native10MOS3MIM per-class analog current integrator and gate-input read buffer; three independent positive/negative/zero fixtures in one extracted simulation. Native reset phase drivers, shared3uA master for3references, initial1ms physically asserted reset then50ms accumulation record. Ten signed100pA10us current pulses spaced5ms; ideal current fixtures stand in for final learned synaptic projections. STATE/OUTPUT native and unforced after reset; no per-bin threshold/leak or digital numeric state. Measures actual charge steps, record sum, quiet final hold and read-buffer error. Current fixtures are not actual trained weights. No six-class wiring/argmax, signed injector calibration, loaded full-model accuracy/population5ms/full-chip acceptance. Catalog revision34: 20 module artifact sets/25 characterization assemblies. Full goal remains incomplete.





## connected native effective threshold - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_effective_threshold_v1_article_boundary.json) records gf180_effective_threshold_v1: 35 native MOS, 4 resistors and 2 MIMs; full DRC0/LVS, GDS reimport and real LEF, 142 nonnegative flat capacitance branches. Nominal simulation completed; `native_effective_threshold_10mv_gate_pass=True`. Physically joined sum then lower/upper clamp completed. Maximum sampled output error0.252mV across below/inside/above fixtures. Illustrative voltage scaling only; actual held candidate/shared penalty, threshold decision/reset fanout and model accuracy remain unfinished.





Native35MOS4R2MIM connected effective-threshold adder plus native lower/upper comparator/TG clamp, actual extracted wiring, typical27C. Three external buffered base/penalty pairs covering below/inside/above bounds. Two native references driven by2uA master. Common1.2V,bounds1.26/1.7V illustrate V=1.2+.4*model_value and default model bounds.15/1.25; no trained hardware calibration claim. Native sum and clamp nodes, no ideal arithmetic. Actual shared-penalty source, parameter storage, decision/reset load, near-bound/PVT/noise/model accuracy/population5ms/full-chip acceptance unfinished. Catalog revision33: 20 module artifact sets/24 characterization assemblies. Full goal remains incomplete.





## native threshold plus penalty adder - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_threshold_penalty_adder_v1_article_boundary.json) records gf180_threshold_penalty_adder_v1: 8 native MOS, 4 resistors and 2 MIMs; full DRC0/LVS, GDS reimport and real LEF, 55 nonnegative flat capacitance branches. Nominal simulation completed; `native_threshold_adder_10mv_gate_pass=True`. Three native sum fixtures complete. Maximum sampled sum error0.578mV. Targets base-plus-shared-penalty with common voltage removed; trained parameter programming and mapping remain external.





Native8MOS4R2MIM threshold-plus-penalty adder; actual extracted wiring, typical27C. Three external buffered base/penalty pairs, common1.2V, reference1uA. Output targetBASE+PENALTY-VCOM. Native arithmetic, no ideal adder. Illustrative voltage mapping, not calibrated model values or parameter-storage programming. Connected clamp/load/model precision/population5ms/full-chip acceptance unfinished. Catalog revision32: 20 module artifact sets/23 characterization assemblies. Full goal remains incomplete.





## native lower upper range clamp - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_analog_range_clamp_v1_article_boundary.json) records gf180_analog_range_clamp_v1: 27 native MOS, 0 resistors and 0 MIMs; full DRC0/LVS, GDS reimport and real LEF, 88 nonnegative flat capacitance branches. Nominal simulation completed; `native_range_clamp_10mv_gate_pass=True`. Three below/inside/above fixtures pass at1.26/1.7V bounds; unloaded settled pass-through/clamp error is negligible in this ideal-source nominal fixture, not an analog precision claim. Near-bound switching and actual fanout remain uncharacterized.





Native27MOS comparator/TG range clamp, actual extracted wiring, typical27C. Three externally buffered input voltages1.22/1.6/1.92V, bounds1.26/1.7V,1uA reference. Output native; no ideal min/max. Illustrative mappingV=1.2+.4*model_value maps default threshold bounds.15/1.25 to1.26/1.7V, not calibrated trained hardware scaling. No near-bound/PVT/output load/model precision/population5ms/full-chip acceptance. Catalog revision31: 20 module artifact sets/22 characterization assemblies. Full goal remains incomplete.





## native candidate minus shared penalty - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_candidate_penalty_subtractor_v1_article_boundary.json) records gf180_candidate_penalty_subtractor_v1: 8 native MOS, 4 resistors and 2 MIMs; full DRC0/LVS, GDS reimport and real LEF, 55 nonnegative flat capacitance branches. Nominal simulation completed; `native_subtractor_10mv_gate_pass=True`. Three native subtraction fixtures complete; targetADJUSTED=CANDIDATE-PENALTY+VCOM. Maximum sampled error0.195mV at typical27C. Input sources remain external buffered fixtures; stored candidate isolation, normalized shared penalty, RMS differential formatting and learned threshold connection still required. No model precision acceptance.





Native8MOS4R2MIM candidate-minus-penalty unity subtractor, actual extracted resistor/OTA/compensation/wiring, typical27C. Three external buffered-voltage fixtures atVCOM1.65V, external1uA reference. TargetADJUSTED=CANDIDATE-PENALTY+VCOM. No ideal arithmetic inside circuit. Standalone output; actual held-candidate isolation, shared-penalty calibration/fanout, RMS and threshold connections remain unfinished. Local10mV gate is bringup, not model precision/population5ms/full-chip acceptance. Catalog revision30: 20 module artifact sets/21 characterization assemblies. Full goal remains incomplete.





## native formatted adaptation product chain - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_native_adaptation_product_v2_article_boundary.json) records gf180_native_adaptation_product_v2: 42 native MOS, 46 resistors and 10 MIMs; full DRC0/LVS, GDS reimport and real LEF, 1209 nonnegative flat capacitance branches. Nominal simulation completed; `positive_native_product_observed=True`. Fully native formatter/current-product/linear-receiver chain completed after guard repair. Zero/mid/high outputs1.648692/1.657135/1.679867V. High/mid increment ratio3.692 versus ideal6; high-point late0.5us output change9.651mV and bias perturbation0.716mV show unsettled loaded behavior. Positive response alone is not accurate product acceptance. Preserve dynamic error; continue connected resident/layout coverage before precision tuning.





Native42MOS46R10MIM fully native voltage-format/current-product/linear-receiver chain, actual extracted wiring, typical27C. Three externally driven buffered amplitude/triangle fixtures; VZERO1.2,VBASE.9,VCOM1.65V and master1uA. No ideal gate arithmetic/product/receiver/output clamp inside circuit. Native formatter ratio1/8 scales each deviation; physical square-difference core drives feedback receiver. Resident storage and actual buffered age triangle not connected yet; trained amplitude/triangle normalization, all-channel reduction, noise/PVT and dense area remain unfinished. Raw offset and product nonlinearity retained. No full adaptation/model accuracy/population5ms/full-chip acceptance. Catalog revision29: 20 module artifact sets/20 characterization assemblies. Full goal remains incomplete.





## grounded native product gate formatter - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_product_gate_formatter_v2_article_boundary.json) records gf180_product_gate_formatter_v2: 29 native MOS, 44 resistors and 8 MIMs; full DRC0/LVS, GDS reimport and real LEF, 1157 nonnegative flat capacitance branches. Nominal simulation completed; `native_formatter_10mv_gate_pass=True`. Ground-guard repair puts VSS track above all internal resistor buses. Original revision1 floating guards caused extracted singular-matrix warnings and parent timeout; retained diagnosis gf180_product_formatter_v1_floating_guard_diagnosis.json. No capacitors deleted. Maximum sampled gate error0.267mV after repair; revision1 middle-point residual settling removed. Prefer revision2 for connected assembly; still no trained precision or full adaptation acceptance.





Native29MOS44R8MIM four-OTA gate formatter, actual extracted native resistors/compensation/wiring, typical27C. Three external amplitude/triangle pairs(1.2,1.6),(1.4,1.4),(1.8,1.6)V atVZERO1.2,VBASE.9V, external1uA reference. Four gate outputs are actual native feedback nodes; no ideal voltage arithmetic inside circuit. Standalone output has extracted parasitics only; product gate capacitance and resident buffer/triangle drive require parent assembly. Local10mV gate is bringup, not calibrated model precision. No complete adaptation/model accuracy/population5ms/full-chip acceptance. Catalog revision28: 20 module artifact sets/19 characterization assemblies. Full goal remains incomplete.





## native scaled product gate formatter - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_product_gate_formatter_v1_article_boundary.json) records gf180_product_gate_formatter_v1: 29 native MOS, 44 resistors and 8 MIMs; full DRC0/LVS, GDS reimport and real LEF, 1879 nonnegative flat capacitance branches. Nominal simulation completed; `native_formatter_10mv_gate_pass=True`. Three input pairs and four native output gates complete; maximum sampled gate error0.646mV. Native44unit resistor ratios implement1/8 scaling, four OTA loops and8MIM compensate. No ideal arithmetic inside cell. Product-kernel gate load, stored amplitude/triangle drive, trained normalization and dense area remain separate; middle sample has residual settling error.





Native29MOS44R8MIM four-OTA gate formatter, actual extracted native resistors/compensation/wiring, typical27C. Three external amplitude/triangle pairs(1.2,1.6),(1.4,1.4),(1.8,1.6)V atVZERO1.2,VBASE.9V, external1uA reference. Four gate outputs are actual native feedback nodes; no ideal voltage arithmetic inside circuit. Standalone output has extracted parasitics only; product gate capacitance and resident buffer/triangle drive require parent assembly. Local10mV gate is bringup, not calibrated model precision. No complete adaptation/model accuracy/population5ms/full-chip acceptance. Catalog revision27: 20 module artifact sets/18 characterization assemblies. Full goal remains incomplete.





## loaded resident amplitude buffer - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_resident_amplitude_buffer_v1_article_boundary.json) records gf180_resident_amplitude_buffer_v1: 18 native MOS, 2 resistors and 4 MIMs; full DRC0/LVS, GDS reimport and real LEF, 125 nonnegative flat capacitance branches. Nominal simulation completed; `loaded_buffer_tracks_resident_amplitude_observed=True`. Actual storage drives buffer gates, output drives two native series123x1 resistors. Maximum sampled buffer/storage error0.2123mV; final quiet5ms storage drift13.0uV. Write-release storage error remains-84.686mV; advance/data transitions visibly perturb stored amplitude. The report field amplitude_initial_hold_drift_v spans an advance pulse and is not quiet leakage. storage_sequence_observed=true is only a loose sequence gate, not accurate amplitude-write acceptance. Next native scaled sum/difference formatter.





Native18MOS2R4MIM resident storage and gate-input unity amplitude buffer with two physical series123x1 high-poly resistors loading AMP_BUF toVRESET1.2V. Actual extracted wiring and native phase drivers. One sequence, fixed1ms startup, two age advances5ms apart, spike-driven reset/amplitude overwrite1.5 to1.8V, another advance and5ms hold. External1uA bias, PP2.6/PCAS2.2/PARK1.2V. Stored AMPLITUDE has no ideal drive after write opens; buffer output supplies native resistor load. Input-capacitance/write-release offset and loaded buffer tracking measured separately. Load is characterization fixture, not native product formatter. No RMS/strength amplitude generation, triangle normalization/product, full adaptation/model accuracy/population5ms/full-chip acceptance. Catalog revision26: 20 module artifact sets/17 characterization assemblies. Full goal remains incomplete.





## analog amplitude gate input buffer - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_amplitude_buffer_v1_article_boundary.json) records gf180_amplitude_buffer_v1: 8 native MOS, 0 resistors and 2 MIMs; full DRC0/LVS, GDS reimport and real LEF, 24 nonnegative flat capacitance branches. Nominal simulation completed; `nominal_buffer_10mv_gate_pass=True`. Unloaded1.2/1.5/1.8V nominal buffer maximum error20.88uV. Native gate input isolates DC resistive load from storage, but connected kickback and loading remain separate evidence.





Extracted native8MOS2MIM amplitude unity buffer. Three ideal-source amplitude voltages1.2/1.5/1.8V and return step; external1uA reference, typical27C, actual parasitics. Unloaded output; actual resident storage and native resistive formatter load require connected measurement. Local10mV gate is bringup only, not model precision or full adaptation/population5ms/full-chip acceptance. Catalog revision25: 20 module artifact sets/16 characterization assemblies. Full goal remains incomplete.





## native linear penalty voltage receiver - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_two_channel_penalty_receiver_v1_article_boundary.json) records gf180_two_channel_penalty_receiver_v1: 20 native MOS, 2 resistors and 2 MIMs; full DRC0/LVS, GDS reimport and real LEF, 87 nonnegative flat capacitance branches. Nominal simulation completed; `positive_additive_voltage_observed=True`. Native receiver removes ideal OUT clamp. Zero/one/two-active outputs1.647611/1.681529/1.715442V; zero-subtracted steps33.918/67.831mV, ratio1.999852. Raw zero offset-2.389mV and late settling11.85uV in two-active case retained. Native amplitude isolation, scaled sum/difference gate formatting and trained normalization remain next; no full adaptation acceptance.





Native20MOS2R2MIM product-current sum plus feedback voltage receiver, actual extracted interconnect, typical27C. Three zero/one/two-active fixtures with ideal external gate formatting only; VBASE=.9V,VZERO=1.65V, external1uA master references. Receiver output and kernel summing voltage are native circuit nodes, not forced. Two123x1 high-poly feedback resistors operate in parallel. Raw voltage offset, non-square-law and compliance retained. No resident-amplitude isolation/native gate formatter, calibrated trained penalty mapping or actual full-channel load. No complete adaptation/model accuracy/population5ms/full-chip acceptance. Catalog revision24: 20 module artifact sets/15 characterization assemblies. Full goal remains incomplete.





## two channel penalty current reduction - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_two_channel_penalty_sum_v1_article_boundary.json) records gf180_two_channel_penalty_sum_v1: 12 native MOS, 0 resistors and 0 MIMs; full DRC0/LVS, GDS reimport and real LEF, 42 nonnegative flat capacitance branches. Nominal simulation completed; `positive_additive_sum_observed=True`. Zero/one/two-active extracted fixtures completed. Increment currents0/535.964/1071.928nA, two-to-one ratio2.000000; raw zero summed offset-37.455nA. Summation is native metal; external voltage formatting and1.65V output compliance remain ideal. Need native linear current receiver, resident-amplitude buffer and actual channel-count mapping.





Native12MOS two-channel square-difference product-current sum, actual extracted interconnect, typical27C. Three zero/one/two-active fixtures. Each active channel x=y=.05V; VBASE=.9V, ideal external gate formatting and1.65V OUT compliance fixture. Reports raw summed current and zero-subtracted increments. Not a native linear voltage receiver, resident-buffered full adaptation circuit or actual model channel-count implementation. No model accuracy, full-population5ms or full-chip acceptance. Catalog revision23: 20 module artifact sets/14 characterization assemblies. Full goal remains incomplete.





## adaptation product current core - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_adaptation_product_kernel_v1_article_boundary.json) records gf180_adaptation_product_kernel_v1: 6 native MOS, 0 resistors and 0 MIMs; full DRC0/LVS, GDS reimport and real LEF, 18 nonnegative flat capacitance branches. Nominal simulation completed; `positive_monotonic_product_observed=True`. Three nominal products completed. Half/full zero-subtracted current ratio0.499804 versus ideal0.5; raw zero-amplitude offset-18.727nA. Ideal external voltage formatting and output compliance remain fixtures; native buffer/formatter and calibrated model mapping still required.





Extracted native6MOS product-current core, typical27C. Three (x,y) points (0,.05),(.025,.05),(.05,.05)V with VBASE=.9V. Ideal external sum/difference gate formatting and1.65V output-voltage fixture; source voltages are scaled analog deviations, not trained weights or stored amplitude mapping. No native formatter, resident amplitude buffering, channel penalty sum or complete adaptation yet. Mirror offset, non-square-law error and output compliance retained. No model precision/population5ms/full-chip acceptance. Catalog revision22: 20 module artifact sets/13 characterization assemblies. Full goal remains incomplete.





## connected resident age and triangle - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_resident_triangle_adaptation_v1_article_boundary.json) records gf180_resident_triangle_adaptation_v1: 51 native MOS, 2 resistors and 6 MIMs; full DRC0/LVS, GDS reimport and real LEF, 238 nonnegative flat capacitance branches. Nominal simulation completed; `buffered_triangle_tracks_resident_age_observed=True`. Triangle tracks actual resident age within0.118mV. Final5ms drift:AGE42.6uV,AMP14.8uV. Equal pulses give31.883/18.016/31.925mV age steps; amplitude write-release error106mV and storage_sequence_observed=false. First deck omitted resistor model and never simulated; corrected deck adds res_typical with unchanged circuit and solver.





Native51MOS2R6MIM connected resident/buffered-triangle parent, actual extracted interconnect and native phase drivers. No ideal AGE/AMPLITUDE/TRIANGLE drive after spike write/reset; external1uA master current andVPEAK1.6V. Buffer high-impedance gate is actual resident AGE load. One sequence, fixed1ms common startup, two isolated age advances5ms apart, spike-driven age reset/amplitude overwrite, then another advance and5ms hold. External PP2.6V,PCAS2.2V,PARK/VRESET1.2V, amplitude data1.5 then1.8V. Age voltage is uncalibrated; no RMS/strength generation, calibrated age-duration normalization, amplitude multiplication or penalty reduction, full-neuron accuracy or population5ms/full-chip acceptance. Catalog revision21: 20 module artifact sets/12 characterization assemblies. Full goal remains incomplete.





## buffered adaptation triangle - 2026-10-10





[Assembly boundary](../artifacts/analog_asic/results/gf180_buffered_adaptation_triangle_v1_article_boundary.json) records gf180_buffered_adaptation_triangle_v1: 41 native MOS, 2 resistors and 4 MIMs; full DRC0/LVS, GDS reimport and real LEF, 143 nonnegative flat capacitance branches. Nominal simulation completed; `nominal_triangle_10mv_gate_pass=True`. Three trajectories complete; max nominal output error0.594mV. Buffer removes direct resistor load; actual resident capacitor connection still pending.





Native41MOS2R4MIM buffered triangle shaper with flat extracted interconnect. Three trajectories rising/falling/inactive-expired, each with three age levels around fixedVPEAK1.6/VZERO1.2V and physicalPF20/2 reference driven1uA. No ideal reflection, comparator, min/max or analog switch inside circuit; age/reference fixtures ideal. Native unity input follower now removes direct resistor loading of AGE; actual connected resident capacitor still requires simulation. Normalized10mV output bringup gate is local, not trained precision. Actual resident-age source load, calibrated continuous duration and amplitude multiplication/channel reduction still absent. No full-model accuracy/PVT/noise/population5ms/full-chip acceptance. Catalog revision20: 20 module artifact sets/11 characterization assemblies. Full goal remains incomplete.





## analog_adaptation_triangle_shape local control milestone - 2026-10-10





[Module boundary](../artifacts/analog_asic/results/gf180_adaptation_triangle_v1_article_boundary.json) records gf180_adaptation_triangle_v1: 34 native MOS, full DRC0, source and GDS-reimport LVS, flat capacitive extraction and actual LEF. Nominal extracted cases pass: rising, falling, inactive_expired. Catalog revision19 now contains20 module artifact sets and10 characterization assemblies.





Native34MOS2R2MIM adaptation triangle shaper. Reflection=2VPEAK-AGE from real native unity feedback amplifier. Native comparators and TG mux select AGE before peak and REFLECT afterward, then clamp below VZERO. Normalized shape is (TRIANGLE-VZERO)/(VPEAK-VZERO), targeting model max(0,min(age/T,2-age/T)); no behavioral min/max/amplifier inside circuit. External age/peak/zero and master bias current; no trained duration calibration, actual loaded resident-age source, amplitude multiply or channel penalty reduction. Requires extracted rising/peak/falling/expired sequence. Nominal circuit does not establish trained model precision, PVT/noise, full-population5ms or full-chip acceptance; characterization geometry, not dense leaf Rising/falling/expired trajectories completed; maximum nominal output error0.237mV at VZERO1.2,VPEAK1.6. Input is externally driven: reflection resistors load AGE, requiring a native buffer before resident-capacitor connection. Learned duration/age mapping and amplitude multiplication remain unfinished. Characterization geometry; do not replicate as dense storage area. Full-chip layout, analog accuracy and population5ms service remain incomplete.





## analog_age_reflection_amplifier local control milestone - 2026-10-10





[Module boundary](../artifacts/analog_asic/results/gf180_age_reflection_amplifier_v4_article_boundary.json) records gf180_age_reflection_amplifier_v4: 8 native MOS, full DRC0, source and GDS-reimport LVS, flat capacitive extraction and actual LEF. Nominal extracted cases pass: low_age, peak_age, two_duration_age. Catalog revision18 now contains19 module artifact sets and10 characterization assemblies.





Native8MOS2R2MIM age-reflection amplifier: corrected7MOS PMOS-input OTA, two identical123x1 native high-poly resistors, two minimumMIM Miller capacitors and physical diode PF bias reference. Unity inverting feedback around VPEAK targets VREFLECT=2VPEAK-VAGE. External master reference current into BIAS, age/peak inputs and supply; no ideal amplifier or ideal resistor in physical circuit. Provides falling branch only; triangle branch selection/floor clamp, normalized duration, amplitude multiplication and model accuracy remain unfinished. Requires extracted static three-point and step-settling measurements. Characterization geometry, not dense per-neuron placement or original-float/population5ms/full-chip acceptance Three age voltages and return step completed; maximum reflection error0.719mV at nominal conditions. No loaded age source, complete triangle or model tolerance acceptance. Preservedv1 envelope failure,v2 legacy-reference-via failure,v3 missing-port reference failure; v4 uses independently corrected source/GDS-port-verified reference. Characterization geometry; do not replicate as dense storage area. Full-chip layout, analog accuracy and population5ms service remain incomplete.





## Native energy current sum and root receiver - 2026-10-10





[Two-channel boundary](../artifacts/analog_asic/results/gf180_two_channel_energy_root_article_boundary.json) records real14MOS parent, full DRC0/LVS and independent GDS reimport, actual LEF and26 nonnegative flat capacitance branches. Three nominal fixtures complete: receiver VSG0.871080/0.975737/1.046600V for zero/one/two active channels; the two-active inputs have opposite signs. ROOT is not voltage-clamped and no behavioral square/sqrt is inside the circuit. Response is monotonic; one/two zero-subtracted ratio0.596271 differs from ideal RMS0.707107. No RMS accuracy/range acceptance. Catalog revision17:18 reusable module sets and10 characterization assemblies.





Inhibition selection/charge actuator completed; analog age/amplitude storage completed with failed functional check (unequal age steps,134mV write-release error). Do not hide those errors. Next physical functions: candidate-minus-adaptation differential formatting, triangle shape and amplitude product, channel penalty reduction/threshold clamp, final class-current/readout interface, global control and dense/full layout.





## differential_energy_current_kernel local control milestone - 2026-10-10





[Module boundary](../artifacts/analog_asic/results/gf180_energy_square_kernel_v1_article_boundary.json) records gf180_energy_square_kernel_v1: 6 native MOS, full DRC0, source and GDS-reimport LVS, flat capacitive extraction and actual LEF. Nominal extracted cases pass: negative, zero, positive. Catalog revision16 now contains18 module artifact sets and9 characterization assemblies.





Native6MOS differential quadratic current kernel,noMIM. Two long-channel input NMOS branches share OUT; two matched baseline NMOS feed a diode PMOS/current-mirror branch to subtract common current physically. VINP/VINN must be equal and opposite deviations around VBASE, so sum-input incremental current can approximate a squared signed voltage. Differential formatting and candidate-minus-adaptation subtraction remain external. This kernel does not sum all channels, normalize channel count, take square root, apply trained1.5 energy clamp or multiply learned strengths. DC offset, current-mirror compliance, non-square-law behavior and dynamic loading require extracted measurement; no unsigned-energy, RMS/model/population5ms/full-chip acceptance Three signed-input points completed; equal positive incremental sink currents537.740nA at both +/-0.1V, zero-input offset-20.503nA. Quadratic linearity/range and complete RMS remain unaccepted. Characterization geometry; do not replicate as dense storage area. Full-chip layout, analog accuracy and population5ms service remain incomplete.





## analog_adaptation_age_amplitude_storage storage characterization milestone - 2026-10-10





[Module boundary](../artifacts/analog_asic/results/gf180_adaptation_resident_v2_article_boundary.json) records gf180_adaptation_resident_v2: 10 native MOS, full DRC0, source and GDS-reimport LVS, flat capacitive extraction and actual LEF. Nominal extracted sequence completed with failed functional check: advance_twice_reset_overwrite_advance. Catalog revision15 now contains17 module artifact sets and9 characterization assemblies.





Native10MOS2MIM per-neuron analog adaptation storage: continuously biased PMOS current steer advances AGE capacitor only during once-per-bin ADVANCE; SPIKE resets AGE toVRESET and samples external RMS-times-strength amplitude onto separate AMPLITUDE capacitor. Non-spiking amplitude retains. ADVANCE and SPIKE must not overlap; advance occurs before threshold and spike update afterward. AGE is analog voltage, not a quantized model value; its voltage/bin scale, duration normalization and triangle shaping remain unqualified. No computed RMS/product, inactive/expiry clamp or complete adaptation penalty/reduction yet. Analog parking/bias/phase/data references external. Spacious characterization geometry; requires extracted increment/reset/overwrite/hold measurements. No complete-model precision/population5ms/full-chip acceptance Measured steps24.681/12.228/24.744mV for equal age pulses; amplitude sample loses134mV after switch opening, with data/age coupling. Raw storage_sequence_observed=false. Preserve errors and refine later; nominal artifact completion does not accept linear age or amplitude accuracy. Characterization geometry; do not replicate as dense storage area. Full-chip layout, analog accuracy and population5ms service remain incomplete.





## peer_inhibition_actuator local control milestone - 2026-10-10





[Module boundary](../artifacts/analog_asic/results/gf180_peer_inhibition_v1_article_boundary.json) records gf180_peer_inhibition_v1: 20 native MOS, full DRC0, source and GDS-reimport LVS, flat capacitive extraction and actual LEF. Nominal extracted cases pass: no_trigger, peer, own_spiker. Catalog revision14 now contains16 module artifact sets and9 characterization assemblies.





Native20MOS peer-inhibition actuator,noMIM: own-spike complement and nativeAND select ANY_SPIKE AND NOT OWN_SPIKE; existing12MOS subtractive current steering applies decrement only during INHIBIT phase and selected non-spiking peer. Preserves simultaneous spikers by excluding each OWN_SPIKE, without winner-only arbitration. Analog PROGRAM/CASCODE/PARK external: this actuator does not compute retinotopic RMS, learned strength product, any-spike reduction, candidate snapshot or threshold decision. Requires extracted no-trigger/peer/own-spiker cases and state-charge measurement. No complete-model accuracy/population5ms/full-chip acceptance Extracted no-trigger/peer/own-spiker cases complete; peer decrement8.651mV, excluded state steps0.109uV, nominal hold drift8.7..8.8uV over5ms. Decrement amplitude still external; no RMS/strength multiplier acceptance. Characterization geometry; do not replicate as dense storage area. Full-chip layout, analog accuracy and population5ms service remain incomplete.





## shared_master_current_bias_distribution characterization milestone - 2026-10-10





[Module boundary](../artifacts/analog_asic/results/gf180_shared_bias_mirror_v1_article_boundary.json) records gf180_shared_bias_mirror_v1: 6 native MOS, full DRC0, source and GDS-reimport LVS, flat capacitive extraction and actual LEF. Nominal extracted direction/finite-output cases complete: master_current_1e-09_A, master_current_1e-08_A, master_current_1e-07_A. Catalog revision13 now contains15 module artifact sets and9 characterization assemblies.





Native shared6MOS master-current bias/mirror module,noMIM: diode PF0.5/1 with two identical PMOS replica branches; diode NF0.25/0.28 with two identical NMOS replicas. PBIAS/NBIAS accept external reference currents and distribute physical gate bias. Master current generation, target-voltage selection, startup source sequencing, fanout buffering and bias noise/PVT remain external or unqualified. This is a reusable distribution primitive, not a complete voltage/current reference or bandgap. Requires native extracted nominal compliance/ratio/startup checks. No original-float precision/population5ms/full-chip acceptance Three nominal cases completed. PMOS at100us gives1.018..1.037 times reference; short-channel NMOS gives2.217..3.317, so unity mirror accuracy is not accepted. Characterization geometry; do not replicate as dense storage area. Full-chip layout, analog accuracy and population5ms service remain incomplete.





## Connected bin completion and commit control - 2026-10-10





[Connected boundary](../artifacts/analog_asic/results/gf180_joined_bin_control_article_boundary.json) records real398MOS join/controller parent revision2, full DRC0/LVS and GDS reimport, actual LEF and2008 nonnegative flat capacitance branches. Two branch tokens drive the physical sticky join; no external COMPLETE source. Nominal waiting/phase-order/commit check passes and DETECT follows joined COMPLETE. Catalog revision12:14 reusable module sets and9 characterization assemblies. Revision1 failed at exported Metal5 pin islands; revision2 extends global routes to cover pins, preserving failed evidence.





Only one active semantic bin and external valid tokens; graph-wide barrier, queue draining and connected analog phase completion remain unfinished. Not complete PLIF, model accuracy or population5ms acceptance.





## two_branch_completion_join local control milestone - 2026-10-10





[Module boundary](../artifacts/analog_asic/results/gf180_bin_completion_join2_v1_article_boundary.json) records gf180_bin_completion_join2_v1: 92 native MOS, full DRC0, source and GDS-reimport LVS, flat capacitive extraction and actual LEF. Nominal extracted cases pass: A_then_B, B_then_A, clear_stale_arrival. Catalog revision11 now contains14 module artifact sets and8 characterization assemblies.





Native two-input sticky completion join92MOS,noMIM. One in-flight global semantic bin; CLEAR asserted across a capture and tokens low before release. Each upstream TOKEN must represent completion of all work and remain valid through capture; upstream branch must not emit next-bin tokens until global barrier clears this cell. Native control DFFs retain each arrival; COMPLETE masked during CLEAR and high only when both sampled arrivals retained. No encoded bin tags or overlapping bins, no analog state/weights. This local cell does not prove graph-wide flush/barrier timing, metastability safety or5ms population throughput. Requires new extracted arrival-order, duplicate and clear/stale-token simulations Characterization geometry; do not replicate as dense storage area. Full-chip layout, analog accuracy and population5ms service remain incomplete.





## bin_commit_control local control milestone - 2026-10-10





[Module boundary](../artifacts/analog_asic/results/gf180_bin_commit_controller_v1_article_boundary.json) records gf180_bin_commit_controller_v1: 306 native MOS, full DRC0, source and GDS-reimport LVS, flat capacitive extraction and actual LEF. Nominal extracted cases pass: idle, wait_then_complete, reset_while_waiting. Catalog revision10 now contains13 module artifact sets and8 characterization assemblies.





Native bin-control sequencer306MOS,noMIM: eight static control stages,18MOS interlock,26 native gates and two input complement inverters. AGE then BETA precede ACCUM; ACCUM holds until external matching-bin all-upstream COMPLETE. Then DETECT,RESET_STATE,INHIBIT,ADAPT,DONE advance. Strobes gated byPHIA, ACCUM held level. Synchronous reset clears every stage; BIN_START admitted only READY. COMPLETE validity/tag matching remains upstream responsibility; hardware bin/DAG join not implemented here. Controls only, not analog membrane/weights, adaptation/RMS/inhibition circuits. New extracted waiting/order/reset simulation required; no accuracy/population5ms/full-chip acceptance Characterization geometry; do not replicate as dense storage area. Full-chip layout, analog accuracy and population5ms service remain incomplete.





## Complete prebiased local request-to-charge results - 2026-10-10





[Prebiased event boundary](../artifacts/analog_asic/results/gf180_prebiased_autonomous_event_boundary.json) and [catalog revision9](../artifacts/analog_asic/assembly/article_module_catalog_v9.json) retain12 modules/8 characterization assemblies. Same230MOS4MIM physical parent; fixed1ms prebias,50kHz clock and common analog biases. Three complete small-positive/large-positive/large-negative events give pulse widths3.948/7.740/7.740us and state steps+96.910/+190.319/-4.069mV. All-case local usability check:True; it checks charge signs, positive magnitude ordering, one pulse and one of each sequencer strobe, pulse finishing beforeARM ends, READY low duringARM and high afterDONE. Raw completion margins and waveforms retained.





This resolves the short-startup ARM-clipping diagnosis only at these three nominal points. It does not establish float-weight calibration, mismatch/noise, repeat-event service, full-population5ms, bin completion or complete neuron behavior. Shared references/programming, bin/DAG commit, adaptation/inhibition/readout, dense/full layout and original-float accuracy still required.





## Joined event-path startup diagnosis - 2026-10-10





[Startup diagnosis](../artifacts/analog_asic/results/gf180_event_prebias_diagnosis.json): short-startup full event returns READY but small weight clips to10.010us ARM. Internal ramp remains about1.103V, below held magnitude. Ramp routing capacitance is unchanged versus qualified signed-injector parent (24.914fF); ramp source-node routing capacitance increases241.326 to337.936fF.





One timing-only change delays clock/reset/request by1ms with identical circuit, analog references and solver tolerances. Source node settles to3.021V and small-weight cutoff restores to3.948us with+96.910mV state change. This identifies a startup/prebias requirement; it does not isolate source capacitance as the sole cause of transfer changes. Diagnostic ends afterARM and cannot prove finalDONE/READY. Three complete prebiased signed cases are running sequentially,180s bound each. Original-float accuracy, population5ms and full-chip layout remain unaccepted.





## Autonomous local event-to-charge path - 2026-10-10





[Boundary audit](../artifacts/analog_asic/results/gf180_autonomous_event_charge_boundary.json) and [catalog revision8](../artifacts/analog_asic/assembly/article_module_catalog_v8.json):12 reusable module artifact sets and8 characterization assemblies. New native16MOS static control flip-flop passes zero/one/toggling capture and closed-slave hold. Native156MOS event sequencer includes four such control stages and interlocked clock phases. Three native-driver cases pass idle, one event with extra request while busy, and synchronous reset during event; no overlapping strobes. The earlier ideal-source run aborted at request fall1.8us; adding native input drivers completed with identical circuit/tolerances.





The physically joined230MOS4MIM sequencer/signed-injector assembly passes full DRC, physical flat LVS against frozen reference, independent GDS flat readback/LVS, LEF and1225-branch nonnegative extraction. Deep-hierarchy Netgen overflow and pre-repair sources are preserved. One native50kHz small-positive request-to-charge run gives pulse width10.010us and state step+246.272mV. Pulse spans the full10us ARM window, so this parent does not yet demonstrate weight-dependent cutoff. Internal ramp/held/cutoff diagnosis is running; larger/negative cases deferred until mechanism is understood. Each run uses one request and actual sequencer-generated SAMPLE/ARM/RECOVER/DONE; no externally prescribed WRITE/ARM timing. Two native MIM state loads initialize through reset TG; analog programming/bias/PARK references remain external.





This is local event sequencing only. Synchronous reset takes effect at capture; request while busy is not queued and upstream must obey valid/ready. Control bits do not replace analog membrane or weights. A five-cycle admission estimate gives50 events per5ms per engine at50kHz, not measured sustained throughput or full-population service. Bin/DAG completion, commit control, adaptation/inhibition/readout, references/programming, dense/full-chip layout and original-model accuracy remain incomplete. No goal completion claim.





## Native switch-phase support and analog handoff - 2026-10-10





[Boundary audit](../artifacts/analog_asic/results/gf180_native_phase_transfer_boundary.json) and [catalog revision7](../artifacts/analog_asic/assembly/article_module_catalog_v7.json) add an18MOS native nonoverlap phase module and26MOS/2MIM physical sampling/transfer characterization assembly. Ten reusable module artifact sets and seven characterization assemblies now have checked GDS/DRC/LVS/LEF/flat views and completed nominal simulations. Full-chip layout remains unfinished.





The interlock derives PHIA=CMD AND NOT PHIB and PHIB=NOT CMD AND NOT PHIA, sensing actual phase outputs through separate native inverters. Extracted48-branch module at1MHz,27C typical, loaded with1/4/16 native inverter inputs on each output has minimum handoff gaps1.512/1.795/2.910ns and no primary-phase simultaneous logic-high interval. Primary output transients range about-0.166 to3.316V; no PVT/reliability qualification is claimed. These are threshold-crossing measurements, not zero-conductance TG guarantees.





The physical assembly adds DATA-to-HOLD and HOLD-to-OUTPUT native TGs, two minimumMIM plates, and reset TG/inverter. Its81-branch flat extraction includes all intermodule wiring. Three DATA values1.4/1.65/1.9V produce final errors-201.961/-195.912/-182.619mV after six passive transfers. Output monotonic across DATA:True; primary phases remain nonoverlapping:True. Each transfer intentionally shares charge with the output plate, and switching offsets are retained. The near-zero reported sampling_error_v is measured while the sample TG is still ON; it proves tracking only, not released-hold accuracy. This benchmark is not an accepted unity-gain reader or model state-copy path.





Earlier placement/escape failures are preserved. Clearances must cover routing escape envelopes as well as child bounding boxes. MinimumMIM P/M/VSS uses the previously qualified pin-specific escape pattern; generic top-metal lifts can intersect cap geometry. No DRC rule was relaxed. External command/reset/data and supply remain; autonomous event/bin sequencing, shared references, adaptation/inhibition/readout and dense/full assembly are still required.





## Physically joined weighted signed-charge path - 2026-10-10





[Boundary audit](../artifacts/analog_asic/results/gf180_signed_weight_charge_boundary.json) and [catalog revision6](../artifacts/analog_asic/assembly/article_module_catalog_v6.json): nine reusable module artifact sets and six characterization assemblies have physical views and completed nominal simulations. This is module-level evidence; full layout remains unfinished.





Guarded duration parent revision1 passes layout checks and produces one pulse but weights collapse to0.938ï¿½0.941us. Revision2 removes added debug-node routing, shortens global nets and places the cutoff inverter beside the duration parent. Actual44MOS/4MIM parent extraction has250 nonnegative branches; three programmed magnitudes1.5/1.65/1.8V give1.936/3.647/5.365us with one pulse each. This is a combined routing change, not an isolated causal attribution.





Routed signed-charge parent revision2 contains70MOS/4MIM, native sign inverter/two AND gates and bipolar injector. DRC/LVS/GDS readback/LEF pass; flat view has542 nonnegative branches. Netgen crashed while expanding the deep original hierarchy; flat LVS against the frozen reference already uniquely matched to that hierarchy passes. Failed output preserved. Initial combined three-case simulation timed out near cutoff; three sequential bounded cases retain the same circuit, biases and tolerances. Three native cases small-positive/large-positive/large-negative produce state steps+83.810/+228.754/-4.594mV on two minimum MIM loads. Both signs are observed and larger positive weight delivers more net charge. Large positive/negative step magnitudes differ by about50x; this nominal path is not a calibrated signed float-weight transfer. Net charge includes switching transients and uses fixed source biases2.5/.45V.





External references, programming and phases remain. No calibrated float weight map, original-model accuracy, full-population5ms service, dense layout or full-chip acceptance is claimed. Preserve transfer errors and proceed to remaining support functions, dense tiles and full hierarchy; refine precision later.





## Analog weight-control support modules - 2026-10-10





[Weight-control boundary](../artifacts/analog_asic/results/gf180_analog_weight_control_boundary.json) and [catalog revision5](../artifacts/analog_asic/assembly/article_module_catalog_v5.json) add analog parameter hold (4MOS/2MIM), sampled magnitude-duration (19MOS/2MIM), native ramp (4MOS/1MIM), routed stored-bias injector (16MOS/2MIM) and routed native ramp-duration parent (23MOS/3MIM). A pulse-termination guard adds19MOS/1MIM. All have full DRC/LVS/GDS readback, LEF, nonnegative flat extraction and completed nominal simulations; simulation completion is separate from functional acceptance.





Physical stored-bias injection preserves both signs: +28.682/-2.581mV, idle0.560uV on two minimum MIM state plates for1.609us. Held source settings differ from programmed2.5/.45V: actual2.559/.372V before event; NF hold drifts about-2.37mV over5ms. These are bias-interface measurements, not calibrated original-float weights.





Magnitude-duration initial low case missed its pulse because writer release lowered the held magnitude below the1.4V ramp floor. One common floor change to1.2V produces5.912/9.854/13.810us for programmed1.5/1.65/1.8V. Replacing the ideal ramp with a native PF current-source/cascode/MIM ramp gives4.054/7.363/10.695us with three real comparator loads. Separate modules are schematic-connected in that benchmark.





The physically routed native ramp-duration simulation completes but produces16 pulse fragments per case near cutoff, so it is not accepted as a usable one-pulse event generator. A physical dynamic termination guard, connected through one native comparator-output inverter in the extracted fixture, stops the pulse on the first cutoff; three programmed levels give widths2.155/3.871/5.592 us with one rise/fall pair each. That earlier fixture used schematic guard wiring; the later physically joined result is recorded above. A200us ARM window characterizes the routed mechanism and is not a full-population service result. No ideal ramp forces the node. Bias/reference voltages and phase commands remain external; signed injector connection, original-float weight/time mapping, adaptation/inhibition/readout, dense/full hierarchy and5ms population service remain unfinished. These macro footprints are characterization geometry, not dense weight-memory area. Raw failures and source snapshots preserved.





## Connected five-module characterization layout ï¿½ 2026-10-10





[Physical assembly audit](../artifacts/analog_asic/results/gf180_five_module_parent_boundary.json): all five checked modules are connected by real parent metal in revision6.56MOS,41nativeMIM plus186.5um2 auxiliary overlap,35 real external ports. Full DRC0, unique LVS, GDS readback DRC0/unique LVS, LEF and flat extraction with726 nonnegative linear branches pass. Earlier route/pin failures are preserved. Characterization footprint2862.6x651.57um is not a dense resident-state leaf or a chip-area estimate.





Three-target nominal extracted simulation completes with frozen prior auxiliary reference/reset duration; no state correction. Near/high/low decisions0/1/0; trained-beta residuals -47.967/-169.542/-36.391mV, loaded near/high slope0.51467 (trained0.88189), high reset interval -2.185mV and5ms hold drift<10uV. The routing/load substantially changes transfer; stable hold and passed layout checks do not establish functional PLIF accuracy. Injection is parked during this assembled baseline. Comparator autozero/reference storage, biases and phases remain external; adaptation/inhibition/readout and autonomous float-weight timing are still missing. User directs continued module/full layout completion with limitations documented; defer precision sweeps.





## Further completed physical modules ï¿½ 2026-10-10





[Assembly catalog v3](../artifacts/analog_asic/assembly/article_module_catalog_v3.json) now records five module layouts and nominal extracted simulations. New tracking/autozero parking:13MOS39MIM,8 ports, full DRC/LVS/GDS/LEF and flat63 nonnegative capacitor branches. Targets1.45/1.67/2.0V track with offsets1.588/3.742/7.084mV; late drift<0.5uV. Bias/VCM references and phases remain external; this is not an autonomous reference generator.





Signed injection:12MOS,12 ports, full physical checks and flat112 nonnegative branches. Initial PF2.75V gave a wrong-sign positive event because switching dominated weak source current. Retain raw failure. A single bias change to PF2.5V restores positive/negative response: +162.505/-7.446mV for the same1.609us pulse on two minimumMIM plates; idle step0.017uV and hold drift<14.1uV. Magnitude asymmetry and short-pulse transfer remain unrefined; external pulse timing/reference is not an implemented float-weight converter.





Sampled decision hold v2:6MOS1MIM,7 ports, full physical checks and flat24 nonnegative branches; all three nominal high/low/mid-high cases hold their decisions5ms after input reverses. Complementary output for mid-high remains0.227V. Version1 passes hierarchical checks but fails flat MIM bottom-contact enclosure at a new route via; version2 enlarges its M4 landing. Both versions and failed evidence are preserved. No new whole-model accuracy/service claims; next physically join these modules before further precision refinement.





## Current organization evidence





### Combined state and threshold module





[Completed nominal review](../artifacts/analog_asic/results/gf180_combined_v6_documentation_review.json) checks all recorded input/artifact hashes for the fresh three-target native run. The [v6 physical parent](../artifacts/analog_asic/layout/gf180_loaded_state_threshold_shielded_v6/qualification.json) joins resized state/beta and shielded threshold detector: full DRC zero, unique LVS, GDS readback DRC zero/unique LVS and [15-port abstract](../artifacts/analog_asic/layout/gf180_loaded_state_threshold_shielded_v6/abstract_qualification.json) pass. Eleven MOS, one minimum MIM and 186.5 um2 auxiliary metal overlap; 188 x 96.7 um characterization footprint, not dense-leaf or chip area.





Tracking/sensing/reset loading had shifted beta to about 0.927. Resizing the auxiliary geometry and shielding the combined routing restore the original targeted coefficient without changing the model. One common reference 1.568208849 V and reset width 1.609384125 us are frozen from the preceding nominal donor. Fresh writer targets 1.4/1.67/2.0 V give endpoint slope **0.882463** versus trained **0.881893**, with trained-update residuals **-0.197/-0.352/+0.147 mV**. This is nominal, one channel, one update; calibration donor is not validation.





Low state remains unreset. Near/high states receive net **8.529/6.779 mV** reset versus requested **6.875 mV**. Active 5 ms hold drift is +0.032/-0.214/+0.015 mV across the three targets. Reset voltage dependence is the next engineering issue; do not claim uniform reset precision from the high-state result. Full reset/tracking/reference/autozero assembly remains schematic around extracted children, with external biases/clocks. Repeated full cycles, native mismatch/noise, adaptive reset, model accuracy, population service and full-chip layout remain unfinished. Earlier isolated/reference/routed-selector results below are historical baselines and do not qualify this changed assembly.








[Internal-node diagnosis](../artifacts/analog_asic/results/gf180_combined_reset_feedback_diagnosis.json) reproduces every previously saved waveform column bit exactly with unchanged circuit/calibration. Near-threshold detector output changes 2.947 to 1.688 V after reset; high-state output stays about 3.257 V. Selected extracted linear feedback branches predict about -1.4 mV state shift using diagnostic charge/step capacitance, versus -1.75 mV extra near-state reset. This supports a feedback hypothesis, not isolated causal proof; native intrinsic capacitance is omitted from that estimate. [Actual v6 coupling audit](../artifacts/analog_asic/results/gf180_combined_parent_v6_coupling_boundary.json) verifies all 84 aggregate layout capacitor branches are nonnegative. Buffered sensing using the existing native tracking output is the focused next candidate; changed loading/routing must be characterized again.





[Buffered-sensing method review](../artifacts/analog_asic/results/gf180_buffered_sensing_method_review.json): nominal six-arm native run completes, all recorded hashes checked. Reusing tracking park as comparator input with staggered autozero worsens near/high reset to 10.187/13.923 mV and near-state 5 ms hold drift to -4.318 mV; loaded slope 0.865911 versus trained 0.881893. This is a changed schematic parent/loading, not a matched physical-route causal isolation. Reject this arrangement; no calibration sweep. Retain direct v6 parent. Next focused candidate clamps detector output to its buffered latched decision after sampling and measures the engagement disturbance explicitly.





[Single-cycle postdecision-clamp audit](../artifacts/analog_asic/results/gf180_postdecision_clamp_single_cycle_boundary.json): direct v6 physical parent retained, one native quarterTG connects detector output to buffered latched decision after sampling. Prior reference/width unchanged. Fresh three-target nominal run completes with checked provenance. Near/high net reset 7.070/6.777 mV, active hold drift +24.8/+15.2 uV; low state unreset, +32.2 uV drift. Near clamp engagement adds +0.477 mV (high +0.019 mV). Including that kick, beta error and 5 ms hold, single-cycle residuals are within0.281 mV. Do not subtract the kick to claim precision. Added clamp layout, clamp release at following decisions and repeated-cycle behavior remain unqualified; actual three-cycle native check is now running.





[Actual5ms three-cycle audit](../artifacts/analog_asic/results/gf180_postdecision_clamp_three_cycles_boundary.json): nominal active arm gives spike/spike/no-spike, matching its independently evolved golden recurrence from measured initialization. Cumulative commit residuals -0.417/-0.979/-5.204mV; clamp release shifts state -1.097/-2.399mV before later beta phases. This identifies a remaining history error; do not equate matching three spikes with accuracy acceptance. User prioritizes layout/module-simulation completion now; preserve these numbers and defer further precision tuning.





[Integrated output-clamp module](../artifacts/analog_asic/layout/gf180_state_threshold_output_clamp_v2/qualification.json) passes full DRC/LVS/GDS readback and [18-port LEF abstract](../artifacts/analog_asic/layout/gf180_state_threshold_output_clamp_v2/abstract_qualification.json). Thirteen MOS, one native minimum MIM and auxiliary overlap;248x102.7um characterization footprint. Initial v1 DRC passed but LVS found an unconnected clamp supply and incorrect reference port ordering; failed files retained, repaired v2 qualifies. The first completed hierarchical-view run is retained but not used for transfer acceptance: capacitor corrections aggregate AUXREF-ground to -2.879fF. [Same-geometry flat extraction](../artifacts/analog_asic/layout/gf180_state_threshold_output_clamp_v2/flat_cap_qualification.json) passes full DRC/device LVS and has92 nonnegative linear capacitor branches. Its bounded native per-module simulation is running; no capacitor terms were discarded and no geometry was changed.





[Flat-extracted clamp-module simulation](../artifacts/analog_asic/results/gf180_flat_output_clamp_module_boundary.json) completes, all recorded provenance checked. Near/high net reset7.524/7.198mV, active5ms hold drift25.9/16.5uV, clamp engagement1.895/0.021mV. Loaded endpoint beta0.836933 versus trained0.881893; pre-reset residuals -6.761/-21.700mV. These are the new physical revision's measured results, not the earlier schematic transfer. Record them and continue layout/module completion per user direction; precision refinement deferred.





[Current-steering reset module](../artifacts/analog_asic/layout/gf180_reset_current_steering_v1/qualification.json) is now a checked physical12MOS parent: two nativeNF sink/cascode devices, event/park quarterTG paths and6MOS phase/spike selection. Eight real external ports,263x68.5um characterization footprint. Full DRC/LVS/GDS readback and [8-port LEF](../artifacts/analog_asic/layout/gf180_reset_current_steering_v1/abstract_qualification.json) pass. [Flat extraction](../artifacts/analog_asic/layout/gf180_reset_current_steering_v1/flat_cap_qualification.json) has66 nonnegative capacitor branches and flat LVS. Native per-module simulation with the checked clamp/state module is running; tracking/autozero/reference and decision circuitry are still external fixture interfaces.





[Reset physical-module review](../artifacts/analog_asic/results/gf180_reset_routed_module_boundary.json): unshielded routing couples RESET-to-SPIKE29.289fF and source-output-to-selection25.850fF. Its standalone fired state rises about313mV, and sampled-latch joint native simulation aborts at1042.5us;1ohm fixture regularization does not resolve it. Failed reports retained. One physical shielding revision widens global tracks and adds grounded M5/M4 guards; [shielded12MOS module](../artifacts/analog_asic/layout/gf180_reset_current_steering_shielded_v2/qualification.json) passes all physical/8-port abstract/flat checks. RESET-to-SPIKE coupling falls to3.410fF. Same standalone nominal fixture now gives near/high state steps **-9.058/-9.195mV**, nonspiking step -0.097uV and5ms drift <=9.424uV. Module operates in the required direction; precise magnitude and driven-to-sampled interface remain later integration/refinement work. Shielded sampled-interface check is running.





[Article module catalog](../artifacts/analog_asic/assembly/article_module_catalog_v1.json) now collects both completed layout/nominal-simulation artifact sets, real ports, views, sizes and original epoch58 checkpoint/executed-inventory identity for subsequent assembly. This is assembly input, not a full-chip completion claim. Dense storage geometry, tracking/reference/injection, inhibition/adaptation/readout and real tile/chip interconnect remain to assemble.





[Shielded two-module connection audit](../artifacts/analog_asic/results/gf180_shielded_two_module_connection_boundary.json): sampled-decision native fixture now completes using both checked flat-extracted physical modules. Near/high net reset12.655/11.395mV, subsequent5ms hold drift14.1/8.4uV; decisions remain latched high through reset. Loaded beta0.904310 versus trained0.881893; pre-reset residuals -1.812/+5.613mV. This resolves the prior sampled-interface numerical failure for this fixture. Routing/magnitude/beta errors remain documented; do not tune them further before completing remaining layout/modules. Parent-to-parent wiring and tracking/reference/bias/phase interfaces are still schematic. [Assembly catalog revision2](../artifacts/analog_asic/assembly/article_module_catalog_v2.json) includes the completed connection result. No live job remains.





### Resident subtractive reset integration





[Eleven-case reset audit](../artifacts/analog_asic/results/gf180_resident_reset_task_boundary.json) verifies seven completed native reports, selector geometry/abstract hashes and retained failed artifacts. Native tests now latch the spike before reset, so falling membrane cannot truncate its own reset pulse. Matched idle and zero-program controls are retained. Direct pulsing of an attached two-NF cascode sink removed6.07mV initially, but warmup/fresh-target testing produced2.44mV immediate reset and15.49mV subsequent5ms drift; reject that arrangement. The first current-steering version reduced the tail but connected a floating intermediate switch node during decision sampling, disturbing state by about42mV; preserve and reject that path.





Phase AND latched-spike selection removes that connection. With continuously settled current on tracking parking, a common pulse-width prediction frozen from the1.68V case gives6.713mV net reset at fresh1.72V target (requested6.875mV), then23.2uV5ms drift. Native decision-sample disturbance is about9nV in this nominal fixture. This is bounded component evidence, not model/precision acceptance.





[Six-MOS selector](../artifacts/analog_asic/layout/gf180_reset_select_and_fullroute/qualification.json) now passes full DRC/LVS and GDS readback; [six-port LEF](../artifacts/analog_asic/layout/gf180_reset_select_and_fullroute/abstract_qualification.json) checked. It is a118x27.4um characterization fixture, not a dense leaf. Including its real routing capacitance changes the1.72V net reset to6.212mV (0.663mV short), with23.2uV5ms drift;1.64V nonspiking control receives effectively no reset. Full analog assembly is still schematic. Nominal pulse width does not automatically transfer to a changed parent. Seed29 unchanged-circuit180s followup completes after the first120s run saved incomplete output: net reset7.239mV (0.364mV excess), subsequent5ms hold23.2uV. Nonspiking controls remain effectively unreset. Seed arms have different native device statistics; subtracting idle control is diagnostic, not a matched-device causal control.





Actual idle-arm two-target beta diagnostic is0.926884 nominal /0.925694 seed29 versus original trained0.881893; worst sampled pre-reset error against that coefficient3.716/3.689mV. Tracking OTA input capacitance changes the resident beta transfer; earlier trained-beta qualification cannot transfer. Resize against unchanged trained beta under this load before claiming a combined neuron. Bias/reference generation, adaptive reset, repeated updates, native noise, shared-state access and full-population power/service remain unfinished. Do not scale characterization fixture footprints into a chip-area claim. Combined physical beta/sensing/reset loading is the next gate. Some frozen run scopes retain an outdated earlier2.1V width-donor sentence; audit records the exact calibration graph: the fresh/routed checks use the1.68V tracking-selector donor and1.474995516us common width. No raw report was rewritten.





### Fresh range/error review





[Three-record sensitivity audit](../artifacts/analog_asic/results/gf180_range64_comparator_error_boundary.json): preselected records16/24/32; original checkpoint, QAT off, all25 actors. Zero-offset copied-equation controls exactly match original predictions. Mean of per-record IoUs (not pooled dataset IoU): original0.130134, idealK64 saturation0.138733, uniform +0.363mV comparator proxy0.133564, negative proxy0.134256. Individual cases all exceed their original-record IoU; roughly24-27%pixels change with the proxy. Same-sequence reset records are limited evidence; no accuracy acceptance.





[Native proposed-threshold audit](../artifacts/analog_asic/results/gf180_threshold_range64_boundary.json): the same shielded autozero assembly, now calibrated at1.656875V, produces rising-trip errors **+0.827/+1.336mV** nominal/seed29. Reference release shifts -81.7/-102.3uV; reference moves about3.96mV during the scan. Initial high output persists. This dynamic ramp error includes delay/reference movement, not pure static offset, a mismatch distribution or resident-state operation. It exceeds the earlier1.85V proxy; the replay below uses this larger magnitude. Qualified children still do not qualify the combined parent.





[Larger-error three-record audit](../artifacts/analog_asic/results/gf180_range64_actual_threshold_error_boundary.json): uniform +/-1.335663mV rising-trip proxy, same selected records16/24/32 and exact zero-error controls. Mean per-record IoU: original0.130134, idealK64 0.138733, positiveproxy0.136782, negativeproxy0.116072. Positive direction improves each record; negative direction degrades each. About28-31%pixels change. Both native samples have positive rising error; negative sign is a sensitivity stress, not a measured mismatch sample. No symmetric error tolerance or dataset-wide accuracy acceptance follows. Freeze this range sweep; keep candidate under review while integrating real loading/reset.





[Resident actual-threshold assembly](../artifacts/analog_asic/results/gf180_state_threshold_range64_loading_src194959a60597.json): nominal matched bare/loaded arms, startup calibration1.656875V, writer targets1.652/1.658/1.664V, then original targeted beta phases. Loaded state at sensing is1.647310/1.652779/1.658512V with low/low/high logic. Maximum loaded-minus-bare commit magnitude **2.379mV**; high arm settles another1.61mV between31.5 and41.5us. This is a schematic assembly of extracted children, not a physical combined parent, precision sweep, subtractive reset or accepted trained transfer. Characterize final combined commit/settling and reset-disabled controls next; no more isolated reference fitting.





### Threshold integration and representation challenge





[Nine-case native threshold audit](../artifacts/analog_asic/results/gf180_threshold_interface_boundary.json): compact seven-MOS NF-input core and shielded variant both pass full DRC/LVS/GDS/abstract checks. Direct detector DC trip offsets9.5/27.5mV (nominal/seed29); bias switching shifts resident state up to4.64mV. Direct uncorrected/gated-bias use is rejected.





Shielded native startup autozero uses nine real minimum MIM reference units, one compensation MIM, quarterTG feedback and opposite-phase minimumNF dummy. Dummy reduces nominal release shift about5mV to0.73uV (seed29 residual-16.6uV). Slow1mV/us rising-ramp trip errors are-0.363/+0.143mV. Fast-ramp lag, initial high output and UIC reference overshoot at50ps are preserved; startup/headroom, falling/hysteresis, noise and retention remain unqualified. Different topology seeds are not matched device-statistical causal controls.





Resident-state diagnostic uses startup writer calibration, then ordinary state retention/beta with comparator continuously biased. Clear low/mid/high decisions; late state stable after settling. Added comparator changes beta transfer by up to1.503mV versus bare control. This is a schematic assembly of extracted children, not a combined physical layout or proof of population power/service.





[Original threshold voltage inventory](../artifacts/analog_asic/results/gf180_float_threshold_voltage_inventory.json): existing +/-0.44V fixed tile representation maps unchanged float base thresholds to7.8uV..88mV; unweighted tile/channel median1.527mV. Targeted detail_stem channel3 is0.155..2.488mV. Thus1.85V characterization around1.65V reset does not establish operation at trained threshold levels.





[Two-record range sensitivity](../artifacts/analog_asic/results/gf180_threshold_relative_range_boundary.json): original float checkpoint/weights,QAT off; approximate symmetric post-reset state saturation at K times each base threshold:





| Representation | Record8 IoU | Record64 IoU |


| --- | ---: | ---: |


| Original float | 0.164842 | 0.134148 |


| K64 | 0.172971 | 0.143919 |


| K16 | 0.154716 | 0.117024 |


| K4 | 0.109592 | 0.078007 |





K64 changes12.42/13.08%pixels; it is a candidate, not trained-state equivalence or accepted accuracy. It would place base threshold6.875mV above reset for a0.44V half-range. These two records are exploratory for this choice; no hardware error/noise or physical saturation/conversion is included. StopK16/K4, assessK64 on fresh records with circuit error before selecting a new representation. Original model remains the reference.





### Actual trained coefficient and original-float replay





Parameterized physical generator `scripts/build_gf180_parametric_state_update.py` now supports bounded state/auxiliary MIM counts and legal auxiliary overlap height, with executed actor/channel provenance. The targeted `detail_stem` channel3 parent passes full physical/11-port abstract checks. Original trained beta is 0.881893; first corrected nominal/seed29 slopes are 0.881626/0.881362. [Primary trained-beta audit](../artifacts/analog_asic/results/gf180_trained_beta_detailstem_ch3_boundary.json) compares against the unchanged coefficient rather than a fitted check slope.





[Single-channel task audit](../artifacts/analog_asic/results/gf180_trained_beta_task_boundary.json): earlier nominal transfer changes7.60/7.10% pixels on records8/64, with IoU losses0.00495/0.00185. Matched range-only controls are unchanged/nearly unchanged. Record8 ideal diagnostic isolates switching offset/nonlinearity as the dominant cause; slope error alone changes0.0046% pixels and IoU by about-0.0000011. These diagnostic corrections are not hardware.





One frozen secant reference1.552681856V uses two earlier nominal transfers; the earlier check becomes calibration evidence. [Fresh independent1.15/1.7/2.15V native checks](../artifacts/analog_asic/results/gf180_trained_beta_detailstem_ch3_secant_boundary.json) give worst three-cycle residual against trained beta0.479/0.792mV, nominal/seed29. Original-model sensitivity using these curves:





| Case | Original IoU | Measured-transfer IoU | Changed pixels |


| --- | ---: | ---: | ---: |


| Record8 nominal | 0.164842 | 0.163827 | 1.49% |


| Record64 nominal | 0.134148 | 0.133144 | 1.22% |


| Record8 seed29 | 0.164842 | 0.163444 | 2.67% |





Baseline checkpoint/input/target/prediction hashes reproduce; QAT off. Only one channel changes, with ideal frozen tile representation and first-cycle three-point interpolation. New reference and sample locations both change relative to earlier curves, so this is not a strict matched-sample causal improvement claim. Two same-sequence reset heldouts/one mismatch seed do not qualify model-wide accuracy, noise/history/service or a complete neuron. No more isolated reference tuning before threshold/reset loading is integrated. Generator's pre-geometry variable-shadow failure is preserved separately; repaired v2 layout is qualified.





### Physical coarse/fine beta range





[Auxiliary overlap audit](../artifacts/analog_asic/results/gf180_aux_overlap_boundary.json): two real M4/M5 overlap geometries pass full DRC/LVS/GDS readback and 11-port abstract checks. Relative to the same baseline parent:





| Overlap area | Added AUX-AUXREF coupling | Added AUX-ground coupling | Nominal corrected slope | Worst three-cycle residual |


| --- | ---: | ---: | ---: | ---: |


| 8 um2 | 0.403 fF | 0.683 fF | 0.880383 | 1.546 mV |


| 100 um2 | 4.088 fF | 1.107 fF | 0.833240 | 1.311 mV |





Small-overlap seed29 residual is 1.790 mV against its frozen nominal measured slope. Five bounded cases audited; native clocks, references/data external. This resolves a physical sub-minimum-MIM tuning example, not exact trained-beta coverage. Routing adds significant ground capacitance; do not apply the 2 fF/um2 MIM density assumption to these metal-overlap geometries.





[Coarse range audit](../artifacts/analog_asic/results/gf180_coarse_beta_range_boundary.json): one-state/three-auxiliary MIM parent gives nominal corrected slope 0.272198; six-state/no-extra-auxiliary MIM parent gives 0.978105. Both pass full physical/abstract checks and independent-target complete-cycle comparisons (worst residual 0.108/0.590 mV respectively). These two endpoints bracket trained beta 0.322731-0.974767. This does not establish interpolation or implement all 1856 coefficients. Four bounded cases, nominal only, geometry-specific external references, accelerated 100 us period. Next: parameterized geometry for representative actual trained ratios and original-model tolerance replay; complete PLIF remains unfinished.





### Extracted physical-parent transfer





[Five-case primary-waveform audit](../artifacts/analog_asic/results/gf180_extracted_state_update_boundary.json): actual combined routing changes one/two-plate complete-cycle slopes to 0.893756/0.939738. Old schematic reference yields 23.41/12.72 mV three-cycle residual and is not transferable. A frozen reference predicted from nominal endpoints for each geometry (1.541315141/1.534068209 V) gives independent-target three-cycle residuals:





| Extracted parent | Worst residual against earlier measured slope |


| --- | ---: |


| One plate, nominal | 1.573 mV |


| One plate, seed29 | 1.842 mV |


| Two plates, nominal | 1.105 mV |





Both parents and 11-port LEF abstracts pass physical checks. [Two-plate qualification](../artifacts/analog_asic/layout/gf180_nf_state_update_twoplates/qualification.json) uses two actual parallel MIMs, 76 x 78.9 um characterization footprint. This is physical ratio evidence, not coverage of all learned betas. References differ by geometry; a single shared bank reference is not qualified. The five initial runs use three accelerated 100 us cycles. [Extracted-parent actual 5 ms audit](../artifacts/analog_asic/results/gf180_extracted_state_update_5ms_boundary.json) also completes nominal/seed29 one-plate cases: primary-waveform late three-cycle residual 1.628/1.898 mV against the frozen measured slope; intervening 4.9875 ms static hold drift at most 40.46 uV. References/data and native clock drivers remain external fixtures. Noise, dielectric retention, PVT/yield, full PLIF/model/service/chip acceptance remain open. The earlier 1,215 mm2 inventory fit remains conditional schematic evidence, not an updated physical-parent area estimate.





### Earlier complete-cycle correction and physical integration





Auxiliary recharge moves state after beta-switch release, so commit must include that phase. The [repeated-cycle audit](../artifacts/analog_asic/results/gf180_resident_beta_nf_repeated_boundary.json) supersedes earlier release-only calibration for repeated use. Freeze the common physical auxiliary reference at 1.458866651 V, then check independent targets without per-lane state correction.





[Independent complete-cycle audit](../artifacts/analog_asic/results/gf180_resident_beta_nf_complete_cycle_boundary.json): worst three-cycle residual against earlier frozen measured slopes is 0.458 mV (nominal one plate), 0.605 mV (seed29 one plate), 1.034 mV (nominal two plates). These slopes are not accepted learned beta coefficients.





[Actual 5 ms cadence audit](../artifacts/analog_asic/results/gf180_resident_beta_nf_5ms_cadence_boundary.json): three one-plate updates, nominal/seed29, give worst cumulative residual 0.486/0.659 mV; intervening 4.9875 ms static holds drift at most 41.94 uV. Schematic parent uses extracted children, external references/clocks and configured native leakage. Physical dielectric retention, sampled noise, PVT/yield, population service and model accuracy remain open.





[Complete-cycle ratio inventory](../artifacts/analog_asic/results/gf180_nf_complete_cycle_ratio_inventory.json): a two-slope effective fit allocates conditional bare plates of 1124.55 mm2 state + 90.08 mm2 extra auxiliary = **1214.63 mm2** at 2 fF/um2. **User accepts approximately 1,215 mm2 (2026-10-10).** This excludes adaptation, switches, references, routing and spacing. The fit includes switching effects; it is not measured physical capacitance. Some 6,252,400 states need extra auxiliary ratios below the minimum MIM unit, requiring a real geometry solution. No full inventory implementation follows from this estimate.





[New combined physical parent](../artifacts/analog_asic/layout/gf180_nf_state_update_localnodes/qualification.json): quarterTG writer, NF reset/select and one MIM; four MOS, 58 x 78.9 um representative fixture. Full DRC0, unique LVS, empty extraction feedback and GDS readback DRC0/unique LVS. [11-port LEF abstract](../artifacts/analog_asic/layout/gf180_nf_state_update_localnodes/abstract_qualification.json) also passes size, pin and obstruction checks. STATE/AUX are locally routed. This is a characterization layout, not a dense leaf or complete PLIF. Its extracted complete-cycle simulation is next; earlier schematic calibration/results cannot transfer.





Earlier sections below preserve the evidence that led here; release-only references are historical and exclude auxiliary recharge.





### Exact background-state sharing





[Original-float measurement](../artifacts/analog_asic/results/gf180_float_background_state_srca72d2e6557e5.json) completed a zero-input reference and records8/64. Checkpoint, inputs, targets and predictions reproduce baseline hashes; QAT off. Zero-input reference produces zero output spikes and zero nonzero membranes.





| Reset ten-bin record | Peak joint state exceptions | Conservative history allocations |


| --- | ---: | ---: |


| 8 | 25,537,017 (82.44%) | 28,353,680 (91.53%) |


| 64 | 26,415,261 (85.28%) | 29,275,816 (94.51%) |





Denominator is30,976,000 membranes. Bitwise equality includes membrane and enabled adaptation age/amplitude; no small-state truncation. Conservative allocation covers full presynaptic kernel footprints, expands across output channels and never clears within a record. All observed exceptions are inside its mask. One bitmap alone is3,872,000bytes; real mapping/reference/periphery costs are additional.





**Conclusion:** exact default sharing alone gives insufficient density relief in these examples. Two same-sequence reset records do not establish continuous-stream or worst-case coverage; no physical compact-state implementation is accepted.





### Learned beta and native local charge sharing





[Executed beta inventory](../artifacts/analog_asic/results/gf180_executed_float_beta_inventory.json):25 actors,1856 executed channel betas; range0.322731-0.974767. Neuron-weighted10th/50th/90th percentiles are0.840517/0.934807/0.951687. Of30,976,000 membranes,24,147,200 (77.95%) have beta>=0.9. These are unchanged ordinary float sigmoid parameters, not quantized coefficients.





Completed native primitive cases: [disabled control](../artifacts/analog_asic/results/gf180_resident_charge_share_beta_off_plates1_src493d42582d19.json), [one state plate](../artifacts/analog_asic/results/gf180_resident_charge_share_beta_on_plates1_src493d42582d19.json), [two state plates](../artifacts/analog_asic/results/gf180_resident_charge_share_beta_on_plates2_src493d42582d19.json).





| Native case | Endpoint held-to-after slope | Midpoint offset relative to slope around1.65V, mV |


| --- | ---: | ---: |


| off, 1 state plate(s) | 1.000000 | -0.250 |


| on, 1 state plate(s) | 0.756197 | +29.997 |


| on, 2 state plate(s) | 0.844581 | +19.587 |





Slope uses actual high/low held and after measurements; offset is `after_mid - 1.65 - slope*(held_mid - 1.65)`. These describe the observed transfer, not accepted learned beta or measured capacitance. Native PF auxiliary gate has D/S/body=VDD and gate=aux; extracted TGs connect it to the MIM state. Three target levels, nominal only,0.5us sharing, short hold, schematic parent. Disabled control still shifts about-0.250mV.





**Conclusion:** local charge sharing avoids the shared reader/restore in this primitive but its slopes and switching offsets do not cover the trained inventory. Diagnose phases and area before growing MIM storage. No complete-neuron, noise,5ms retention, layout, service or accuracy acceptance.





### Phase diagnosis and shorter physical switch routing





[Phase audit](../artifacts/analog_asic/results/gf180_resident_beta_phase_boundary.json) validates primary finite waveforms and agreement with all printed measurements in the three original cases. One-plate common endpoint-line offset is26.76mV during sharing and27.94mV after release; release adds state-dependent error and midpoint nonlinearity grows0.094 to2.053mV. A two-point lumped-capacitance fit is diagnostic extrapolation only, not physical sizing or beta acceptance.





[Shorttracks audit](../artifacts/analog_asic/results/gf180_resident_beta_shorttracks_boundary.json): a separate quarterTG retains identical native device connections/dimensions and body taps, with shorter vertical access and lower rails. Full DRC0, unique LVS, GDS readback and six-port LEF pass. Its bbox falls1565.6 to805.6um2 (48.5%); this is switch-fixture area, not complete neuron area.





Two completed nominal cases use the new routing in writer/reset/beta TGs; targets, clocks, membrane and auxiliary PF stay unchanged. Compare actual held-to-after transfer because writer release also changes. One-plate slope rises0.756202 to0.791663, but midpoint offset about that slope grows29.994 to33.616mV and endpoint-line midpoint nonlinearity2.053 to2.403mV. Disabled-state movement falls0.250 to0.189mV.





**Decision:** retain the reusable physical switch; routing reduction alone fails the local-update precision/coverage gate. Review auxiliary storage and switching cancellation before capacitor expansion. No parent-layout, native noise, mismatch,5ms retention, model or service acceptance.





### Terminal-only auxiliary storage and physical reference correction





[Six-case audit](../artifacts/analog_asic/results/gf180_resident_beta_reference_mismatch_boundary.json): removing the explicit auxiliary PF leaves actual reset/select terminal capacitance as the charge store. One/two state-plate slopes are0.841240/0.905591; common offsets remain. A frozen external auxiliary precharge1.452736165V, predicted only from one-plate endpoints, is then tested at independent1.05/1.65/2.25V targets.





| Corrected case | Maximum error against earlier frozen slope |


| --- | ---: |


| One plate, nominal | 2.171mV |


| Two plates, nominal | 1.628mV |


| One plate, configured native mismatch seed29 | 1.813mV |





These are transfer errors against measured primitive slopes, not the learned beta coefficients or model accuracy. No per-lane numerical state correction; parent remains schematic with external timing/reference. One seed is not distribution/yield coverage.





[5ms hold audit](../artifacts/analog_asic/results/gf180_resident_beta_5ms_hold_boundary.json): a completed nominal three-level waveform measures5008.5us of static-bus hold before the one-plate update. Worst native-model hold drift112.62uV; following update error against the frozen slope remains2.171mV. This does not validate MIM dielectric leakage, sampled noise, PVT/statistical retention, live-event disturbance or full-population service.





**Next gate:** learned-beta programmability without multiplying state MIM area, then repeated-update/noise and complete-neuron integration. The common reference correction supports this direction; no full primitive/model/service acceptance yet.





### Beta programming review: reject short pulses, develop settled NF-only selection





[Partial-sharing audit](../artifacts/analog_asic/results/gf180_resident_beta_partial_sharing_boundary.json) checks native gate traces and32 measures for each of three nominal command widths.0.1/0.2/0.5ns holds give slopes0.9861/0.8926/0.8405, but midpoint nonlinearities7.32/-8.83/-0.16mV. Gate filtering and measured excursions mean command duration is not an accepted linear beta programmer. Stop this sweep.





[Native NF-only baseline](../artifacts/analog_asic/results/gf180_resident_beta_nf_terminal_storage_boundary.json): separate grounded-bodyNF0.25um/L0.28um selection primitive passes full DRC0, unique LVS, GDS readback and four-port LEF,16x17.8um bbox. Its actual extracted device/ports are oneNF,A/B/EN/VSS; inherited descriptive scope text in its builder includes legacy TG wording and does not change the verified netlist. Writer stays quarterTG; reset and beta switches become NF-only. Fully settled0.5us pulses yield slopes0.920108/0.955227 with1/2state plates and lower auxiliary capacitance.





[Corrected six-case audit](../artifacts/analog_asic/results/gf180_resident_beta_nf_corrected_boundary.json): freeze auxiliary reference1.469574269V from one-plate endpoints before new1.05/1.65/2.25V checks:





| Settled NF candidate | Maximum error versus earlier frozen slope |


| --- | ---: |


| One plate, nominal | 0.313mV |


| Two plates, nominal | 0.430mV |


| One plate, native local mismatch seed29 | 0.262mV |





This supports developing settled NF selection; it does not prove learned-beta coverage. Parent is schematic, reference/clocks external, one cycle/three levels. No beta calibration is transferred from earlier TG phases; no per-lane or forced numerical state correction. Repeat-update, NF-specific5ms hold/noise, headroom/PVT/statistical coverage, programmable ratios, integrated layout and task/service acceptance remain open. Earlier TG5ms result does not qualify this changed interface.





### Conditional storage/access budget





[Shared-interface budget](../artifacts/analog_asic/results/gf180_charge_interface_service_budget.json) assumes one complete shared access per membrane per5ms bin:





| Access scenario | Actor-assigned lanes | Membrane+lane bare plates, mm2 (1/4 restore-AZ banks) |


| --- | ---: | ---: |


| 100us characterization cycle | 619,520 | 5191.58 / 6011.20 |


| 50us read+restore, overhead omitted | 309,760 | 2982.99 / 3392.80 |


| 10us hypothetical access | 61,964 | 1216.20 / 1298.18 |


| 1us hypothetical access | 6,208 | 818.66 / 826.88 |





One5x5um membrane plate each totals774.4mm2; one hypothetical plate per adaptation amplitude adds274.56mm2. Transistors, routing, spacing, references and real scheduling are omitted. These are conditional plate sums, not measured chip area or a universal analog limit. Local updates may invalidate the shared-access assumption.





[Event-delivery budget](../artifacts/analog_asic/results/gf180_parallel_area_service_budget.json): observed peak signed contributions/bin are1,419,337,815 and1,491,656,684. Conditional four-way groups every6us require460,660 actor lanes; hypothetical360-way groups require5135 but are unqualified. Per-destination packing, overhead and DAG service remain unproved.





## Preserved shared charge-interface candidate





[Sample-isolation audit](../artifacts/analog_asic/results/gf180_memory_charge_sample_boundary.json): matched always-on/isolate controls localize major backaction to later restore-bus actuation. Movement falls22.55-34.92mV to1.57-1.66mV, while sampling introduces4.60-4.77mV. Old calibration yields110.02mV three-cycle drift and is rejected.





One frozen common correction uses107full7um coupling MIMs plus a5x5um plate, nine feedback units and external1.329442295V reference. Different1.05/1.65/2.25V targets then give:





| Case | Worst access error | Worst three-cycle state drift |


| --- | ---: | ---: |


| Nominal | 1.209mV | 3.616mV |


| Native seed29 | 4.632mV | 13.878mV |





No per-lane tuning or forced numerical state correction. Holds are about40/49us, not5ms retention. Different targets/hierarchy prohibit a matched improvement claim over older unsampled mismatch results. Noise, yield, model acceptance, service and combined layout remain open.





[Autozero audit](../artifacts/analog_asic/results/gf180_charge_sample_autozero_boundary.json): instrument-only capture reproduces54 donor measures exactly. Restore-only four banks reduce release shift about3.6 to0.96mV with matching printed MOS parameters, but nominal gain becomes1.078975 using the old calibration. This identifies a mechanism; it does not qualify a four-bank reader.





## Physical evidence and previous branches





| Evidence | Conclusion and limit |


| --- | --- |


| [Minimum-MIM integrity](../artifacts/analog_asic/results/gf180_minimum_mim_routed_gds_integrity.json) | Separate repaired5um view passes DRC/LVS/GDS connectivity. Legacy P-port loss preserved; primitive qualification is not retention/noise acceptance |


| [Memory audit](../artifacts/analog_asic/results/gf180_dense_memory_module_boundary.json) | Write-bus isolation reduces about79 to1.49mV variation; guarded alternative rejected |


| Qualified local-diagnostic writer-memory parent | 18MOS, four poly resistors, two MIMs; DRC0/unique LVS/GDS/25-port LEF. Spacious945x311.67um fixture; parent bus variation1.23mV, initial bias5.13mV; not dense-array area |


| [Current-reader mismatch](../artifacts/analog_asic/results/gf180_asymmetric_readout_mismatch_boundary.json) | Nominal settling improves; seed29 high-state output saturates3.3V. Uncalibrated mismatch robustness rejected |


| [Mismatch partition](../artifacts/analog_asic/results/gf180_readout_mismatch_partition_boundary.json) | Ideal controls plus exact current copy still leave up to48.6mV error. Diagnostic ideal replacements are not hardware |


| [Tracking-parking audit](../artifacts/analog_asic/results/gf180_tracking_parking_boundary.json) | Isolates unwanted switching charge; native parking/autozero improves selected cases; six cascaded-OTA variants rejected for invalid operating points |


| [Injection audit](../artifacts/analog_asic/results/gf180_fourbank_bias_service_boundary.json) | Selected programming fit error0.009327uV near reset and state variation<=1.275uV/packet are different metrics. Two-source stagger reduces serial/overlap difference9.197 to1.302uV; larger fan-in unqualified |





Two similar four-source numerical failures are retained; partial measurements or returncode0 do not establish completion. Do not resume blind sweeps. Exact parent provenance, settings, earlier calibrations and failures are in raw reports and the pre-cleanup archive.





## Original-float task sensitivity





[Charge-transfer replay](../artifacts/analog_asic/results/gf180_charge_restore_task_boundary.json) uses an earlier unsampled nominal five-point interface transfer, once per post-reset/bin, with frozen ranges and no extrapolation:





| Replay | Record8 IoU | Record64 IoU |


| --- | ---: | ---: |


| Original float | 0.164842 | 0.134148 |


| Fixed ranges, zero transfer error | 0.164826 | 0.134165 |


| Earlier unsampled transfer | 0.171287 | 0.142952 |





Pixels change13.73%/14.95%. Higher IoU on two same-sequence heldouts does not establish acceptance. This replay excludes sampled-interface errors, native noise, mismatch, history and actual service.





[Dense-storage sensitivity](../artifacts/analog_asic/results/gf180_dense_storage_boundary.json): nominal50fF independent Gaussian storage proxy (287.818uV sigma at300K), fixed8x8 ranges, gives IoU0.155824/0.124664 versus0.164842/0.134148 baseline. This assumes noiseless conversion and other operations; it is neither native sampled noise nor a universal minimum error. Calibration records0-7 exclude heldouts8/64; no dataset-wide tolerance is inferred.





## Evidence use





Use these reports to resolve the next organization decision. New model replay and parent layout should follow selection of the relevant complete interface. Keep measured component results, schematic assemblies, software sensitivity and conditional system estimates distinct.








Shared storage optimization -2026-10-11: actual3T/50fF bank with transistors below MIM, shared row/column buses and9MOS column mirror. Bank core8517.056um2 vs16794.808um2 (-49.3%); with native bias10017.972um2 (-40.3% against old bank excluding bias). Source/GDS fullDRC0, independentLVS, realLEF and2103 nonnegative native cap branches.5ms and50ms64-state sequences complete; maxwrite17.31mV,hold6.88mV,finalreadchange2.67/2.35mV. Source-follower offset uncalibrated. Single-NFET write range1.0-1.4V; do not assume arbitrary analog voltage range. Full state-capacity atlasv2 projects8676.37mm2 storage plus native bias, excluding decoder/write drivers/global compute/wiring; fullchip incomplete. Local buffered reads remain to preserve independent analog charge. See `artifacts/analog_asic/results/gf180_shared_storage_area_milestone_v1.json`. Next:dense shared row/write circuitry, read calibration and connected compute tile.








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








## GF180 analog graph event fork - 2026-10-12





The lossless categorical `event_fork2` is wrapped as a reusable GF180 macro. Icarus simulation passes independent branch backpressure and packet/completion/bin-tag preservation (8 testbench cycles). ORFS detailed route converged to 0 violations; final setup/hold violation counts are 0 and Magic flattened-GDS full-style DRC is 0. LEF/Liberty abstract import passes (181 terminals, 223.625 x 223.625 um). Standard-cell area is 22,463.5 um2; digital-view power estimate is 1.943 mW at the stated 100 ns constraint. Evidence: `artifacts/analog_asic/results/gf180_analog_event_fork2_v1.json`. This qualifies one categorical operator macro only; the analog actors, global graph, original-float accuracy, full-population 5 ms service and full-chip layout remain incomplete.








## GF180 analog graph nearest-neighbor upsampler - 2026-10-12





The categorical `event_upsample2x` operator is wrapped as a reusable GF180 macro. Icarus simulation passes four-coordinate expansion, channel/tag preservation, and exactly one completion token per bin. ORFS detailed route converges from 49 to 2 to 0 violations; antenna violations are 0. Magic flattened-GDS full-style DRC is 0, and the 123-terminal LEF/Liberty abstract imports. Standard-cell area is 19,378.6 um2; die is 205.885 x 205.885 um; Fmax is 101.928 MHz under the 100 ns macro constraint; digital-view power estimate is 2.022 mW. Evidence: `artifacts/analog_asic/results/gf180_analog_event_upsample2x_v1.json`. This is a standalone categorical operator result; full DAG binding, analog actor integration, original-float accuracy, full-population 5 ms service and full-chip layout remain incomplete.








## GF180 analog graph two-input event join - 2026-10-12





The lossless categorical `event_join2` wrapper passes a 20-cycle simulation: both data streams forward with payload/tag intact, matching completion tags rendezvous once, and mismatched tags raise an error and fail closed. ORFS route violations converge 195 -> 4 -> 4 -> 0; antenna violations are 0. Flattened Magic full-style GDS DRC is 0; the 182-terminal LEF/Liberty abstract imports. Standard-cell area is 30,891.2 um2, die is 258.85 x 258.85 um, Fmax is 63.962 MHz under the 100 ns macro constraint, and digital-view power estimate is 1.909 mW. Evidence: `artifacts/analog_asic/results/gf180_analog_event_join2_v1.json`. This join preserves coincident multiplicity and does not implement residual deduplication. Full DAG and actor binding, analog loading, original-float accuracy, full-population 5 ms service and full-chip layout remain open.








## GF180 analog residual OR by sorted stream merge - 2026-10-12





Implemented a bounded-state residual merger that holds one event from each input, emits the lower canonical channel-major address, and emits equal addresses once. It has no event-count-sized SRAM and no `MAX_EVENTS` cap. Icarus simulation passes sorted union, duplicate collapse, matching-bin completion, unsorted-input detection and fail-closed tag/order errors. ORFS detailed route converges to zero violations after inserting one antenna diode; flattened Magic full-style GDS DRC is zero; reusable 184-terminal LEF/Liberty imports. Standard-cell area is 89,588.6 um2, die 481.146 x 481.146 um, Fmax 82.331 MHz at the 100 ns macro constraint and estimated digital-view power 9.548 mW. Evidence: `artifacts/analog_asic/results/gf180_analog_binary_event_merge_sorted2_v1.json`. Critical dependency: every producer must emit at most one spike per address and scan addresses in strict ascending channel-major order. Analog actor output serialization is not yet bound or verified; no graph throughput, original-float accuracy, full-population 5 ms or full-chip acceptance follows.








## GF180 analog graph channel offset - 2026-10-12





The registered categorical channel-offset macro passes mapping, backpressure, completion/tag preservation, and overflow fail-closed simulation. ORFS route violations converge 33 -> 1 -> 0; antenna violations are 0. Magic flattened-GDS full-style DRC is 0 and the 123-terminal LEF/Liberty abstract imports. Standard-cell area is 17,535.6 um2, die is 192.135 x 192.135 um, Fmax 72.795 MHz at 100 ns and estimated digital-view power 1.664 mW. Evidence: `artifacts/analog_asic/results/gf180_analog_event_channel_offset64_v1.json`. The macro covers the 64..127 concat leg; full joins and actor binding remain open.





## GF180 32-lane actor spike serializer and four-bank page - 2026-10-12





The selected routing-friendly architecture divides each 128-neuron comparator bitmap into four contiguous 32-lane banks. Each bank scans ascending addresses with a shift register; a three-node sorted merge tree restores the global channel-major stream and performs residual duplicate collapse. The four-bank page wrapper simulation passes sparse events across all banks, matching bin completion, partial final-page masking, and invalid lane-count fail-closed behavior.





The standalone serializer bank has routed GF180 GDS, LEF and Liberty views. Its macro is 681.09 x 681.09 um (0.464 mm2); standard-cell area is 146,807 um2, final utilization 32%, post-route Fmax 109.65 MHz under a 20 ns constraint, and worst slack 10.88 ns. A bank scans up to 32 lanes in 0.64 us at 50 MHz, before output backpressure. Magic full-style flattened-GDS DRC reports zero errors. OpenROAD's final DRT report has two adjacent-net Metal2 spacing entries at one location; this discrepancy is retained. The four-bank parent now has its own routed GDS/SPEF/LEF/Liberty, DRT0, Magic flat DRC0 and imported abstract. Its final ORFS report still shows 120 max-slew violations; analog comparator binding, whole-model throughput, 5 ms and float accuracy remain unqualified. Evidence: `artifacts/analog_asic/results/gf180_analog_spike_event_serializer32_v1.json`.





The 128-lane single-block priority encoder and two sequential 128-lane scanner candidates did not complete bounded detailed routing. Their source and timeout logs remain preserved; the 32-lane partition is the selected article implementation path.


## Routed GF180 four-bank 128-neuron spike page - 2026-10-12





Four 32-lane ascending scanners feed a three-node sorted merge tree. The integrated simulation passes sparse events across all four banks, completion/tag rendezvous, partial-page tail masking and invalid count fail-closed. The flattened parent is physically routed with 0 OpenROAD detailed-route violations, 0 antenna net/pin violations, and 0 Magic full-style flat-GDS DRC errors. ORFS generated GDS/SPEF/LEF/Liberty and the 249-terminal abstract imports. Macro size is 1107.91 x 1107.91 um, standard-cell area 391,094 um2, final utilization 32%, post-route Fmax 119.74 MHz under a 20 ns constraint, and worst slack 11.65 ns. The default-activity digital-view estimate is 0.356 W. ORFS also reports 120 max-slew violations; setup/hold violations are zero. This page macro is now a routed parent result; comparator-to-analog-actor connections, full 43-node graph layout, complete loaded analog simulation, whole-model accuracy and 5 ms service remain open. Evidence: `artifacts/analog_asic/results/gf180_analog_spike_event_page128_v1.json`.


## GF180 analog neuron to 128-neuron event page co-simulation - 2026-10-12





The existing extracted five-module neuron parent produced SPIKE outputs of 6.151 mV (near case), 3.294 V (high case), and 0.194 mV (low case) at the recorded sample. A 0.7 VDD (2.31 V) CMOS-high boundary classified only the high case. Those measured bits fed the routed 128-neuron page; Icarus emitted event address 4001 and preserved the completion tag. This is reproducible interface co-simulation, not an extracted analog-to-digital physical interconnect, 128-channel actor simulation, full graph, accuracy, or 5 ms result. Evidence: `artifacts/analog_asic/results/gf180_neuron_spike_to_page128_v1.json`.





The page V1 final report places all 120 max-slew violations on clock pins, with 3.20-3.22 ns slew against a 2.80 ns limit; placement, CTS, and global-route reports show zero. Its ORFS config sets `SKIP_CTS_REPAIR_TIMING=1`. A preserved V2 experiment enabled that repair, but OpenROAD crashed during CTS after `repair_timing` at placement parasitic estimation (`child killed: illegal instruction`); no V2 layout was produced. Keep the V1 route as the usable result and the clock-slew issue unresolved.








## GF180 one-neuron physical event-page link - 2026-10-12





Assembled the characterized five-module analog neuron GDS with the routed 128-lane event page. Added an M5/via4/M4 route from neuron `SPIKE` to page `spike_bitmap_i[0]`. The first flat full-style DRC found one M5 minimum-width violation at the inside corner of an L bend; filling the corner square removed it. Final flattened Magic full-style DRC: **0**. Magic hierarchical extraction completed and confirmed both child subcircuits map the endpoints to the same extracted net, `gf180_neuron_five_module_parent_v6_0/SPIKE`. Parent GDS is 34,306,724 bytes and extracted SPICE 2,174,045 bytes. This is one physical channel handoff, not a 128-neuron physical bank, full graph, model-accuracy result, or whole-system 5 ms acceptance. Evidence and source: `scripts/assemble_gf180_one_neuron_page_link_v1.py`, `artifacts/analog_asic/assembly/gf180_one_neuron_page_link_v1/qualification.json`.








## GF180 analog neuron to pointwise weight-selector path - 2026-10-12





Replaced the expensive 26-bit flat-address division decoder after its merged physical route accumulated thousands of detailed-route violations. The selected interface now treats a page as the 128 channel bits at one spatial pixel; channel comes directly from the sorted bitmap lane and one 13-bit pixel index is decoded into x/y. The integrated page/decoder/pointwise-scatter top routed to final GF180 GDS, LEF, Liberty and SPEF; final detailed-route violations 0, antenna violations 0, setup/hold clean, mapped area 271,156 ÂµmÂ² (0.271 mmÂ²), die 1.82958 mm square (~3.35 mmÂ²). Flat full-style Magic DRC on the routed digital GDS: 0.





Composed the five-module analog neuron with that routed page/scatter macro. Physical M5/via4/M4/via3/M3 connection from neuron `SPIKE` to page `spike_bitmap_i[0]` passes flattened full-style Magic DRC0; hierarchical extraction confirms the endpoints share `gf180_neuron_five_module_parent_v6_0/SPIKE`. Mixed simulation using the measured 3.294347 V analog SPIKE sample (CMOS VIH 2.31 V) passes through channel 0 at pixel (21,10), yielding the expected pointwise selector tuple, multiplicity and tag. Parent GDS is ~22.85 MB. The selected analog weight value/read circuit and signed charge injection are not in this path; lanes 1â€“127, whole-model accuracy, full graph and 5 ms service remain open. Evidence: `scripts/assemble_gf180_neuron_page_scatter_link_v1.py`, `scripts/cosim_gf180_neuron_page_scatter_v1.py`, `artifacts/analog_asic/assembly/gf180_neuron_page_scatter_link_v1/qualification.json`, `artifacts/analog_asic/results/gf180_neuron_page_scatter_cosim_v1.json`.








## Signed weight delivery against the original-float inventory â€” 2026-10-13





The prior routed sequencer/injector used a 1.2V ramp reset while the float-derived storage range starts at1.0V. A bounded extracted-parent trial at1.1V therefore produced no event. Moving only the ramp reset reference to1.0V made the same1.1V magnitude produce one1.305us pulse, +31.828mV state step and3.7224fC charge. The1.0V zero case remained quiet: no pulse,8.716nV simulated state drift and3.42aC measured charge. At1.4V, the positive event produced one5.113us pulse, +125.616mV and14.6908fC; negative sign at the same voltage produced one5.113us pulse, -125.435mV and -14.6693fC. Full-scale sign-charge mismatch is0.147%; both sequencers emitted exactly one SAMPLE/ARM/RECOVER/DONE and returned READY.





The negative branch needed its shared NPROGRAM reference corrected from0.45V. At0.45V its1.8V event changed state by only-4.069mV; at0.8V it over-discharged to-1.559V. The bounded intermediate trials selected0.613V: at1.8V the positive/negative steps are+190.319/-189.570mV, a0.39% nominal mismatch. The1.4V matched-bias comparison under the new1.0V ramp reset is tighter. This is one nominal shared bias, not PVT, mismatch, loaded-population calibration or a per-channel correction.





The continuous candidate storage map is `MAG_DATA=1.0+0.4*abs(w)/max_abs(weight_tensor)` with the sign carried separately. The measured quarter-scale proxy at1.1V delivers25.34% of full-scale charge,1.35% above ideal linear scaling. The source archive contains26 weight tensors and143,824 original-float values; no values are quantized. Under per-tensor normalization,13.53% of magnitudes are below1% of tensor maximum. A linear full-scale fit estimates their pulse widths below51ns; the shortest region is not resolved by the current transient setup. This short-pulse region is the next analog accuracy challenge, not proof that those weights can already be delivered faithfully.





Physical weight-cell readout and selector are still disconnected from `MAG_DATA/SIGN`; the atlas remains capacity geometry. The candidate mapping has not been run through the original-float network, and full5ms service remains open. Evidence: `scripts/summarize_gf180_weight_delivery_float_mapping_v1.py`, `artifacts/analog_asic/results/gf180_weight_delivery_float_mapping_v1.json`, and the per-case extracted ngspice reports listed there.





## Low-end signed weight transfer â€” 2026-10-13





Tested the continuous per-tensor candidate `MAG_DATA=1.0+0.4*abs(w)/max_abs(weight_tensor)` on the same extracted GF180 sequencer/injector parent, with native phase generation, two physical MIM state loads, one positive event and fixed nominal TT27 biases. At normalized magnitudes5% and10% (1.02V and1.04V), the sequencer completed but produced no pulse; state movement was about8.7nV. At15% (1.06V), one0.541us pulse delivered1.521fC, only10.35% of full-scale charge rather than15%. At20% (1.08V), one0.901us pulse delivered2.559fC,17.42% of full-scale. Existing25% at1.1V gives25.34% and full-scale at1.4V gives14.691fC. The onset is bracketed between10% and15%; this is not a precise threshold fit.








## Physically extracted fixed-duration weight amplitude â€” 2026-10-13





The sampled-weight cell's native 9-MIM gate bank and writer, signed cascode current-source geometry, extracted charge-reader read TG and integrator, and phase inverter were composed for a single 1 us event. The current curve is smooth and monotonic from zero to full scale; inverse gate-voltage settings were refined against zero-subtracted charge. Nominal TT27 q0.1%, q1%, q5%, q10%, and full-scale results are0.0835%,0.9784%,4.9994%,9.8616%, and100% of full-scale charge, respectively. That is a 16.5% relative miss at q0.1%, 2.2% at q1%, less than0.02% at q5%, and1.4% at q10%; no small float point was erased in this sample.





Calibration used a transparent writer; separate v1/v2 screens sample and hold gate values on the actual MIM bank, but those held settings were from the initial calibration, not this final map. The measured charge differences are near atto-coulomb scale and are nominal simulator values, not evidence of a resolvable noise floor, device mismatch robustness or accurate model computation. Inter-macro routes, analog weight addressing, full-float network replay, 5 ms event service and chip acceptance remain open. The failed v3 switching screens are retained; using a transparent writer allowed this bounded calibration to complete without changing the extracted macro.





Evidence: `scripts/screen_gf180_physical_weight_amplitude_transfer_v1.py` through `scripts/screen_gf180_physical_weight_amplitude_transfer_v5.py` and `artifacts/analog_asic/results/gf180_physical_weight_amplitude_transfer_v5_src11e5a5445dc3.json`.





## Sample-held weight map and original-float low tail - 2026-10-13





The calibrated q0.1%, q1%, q5%, q10%, and full-scale gate settings were written through the actual GF180 nine-MIM sampled-weight macro. The writer was then released, the gate values remained near their programmed values at9us, and a fixed1us event was read into the extracted charge reader. Measured charge ratios are0.1291%,1.0329%,5.0704%,9.9413%, and100%; relative errors are+29.1%,+3.29%,+1.41%,-0.59%, and0%. This verifies the sample/hold path at these nominal points, not retention duration, noise, mismatch, PVT or analog address selection. Evidence: `artifacts/analog_asic/results/gf180_physical_weight_amplitude_transfer_v6_hold_srcbfe471246216.json`.





The epoch58 checkpoint was verified by SHA-256 and the historical parameter export was compared against the fresh export; arrays match exactly. Across143,824 nonzero weights in26 tensors, the minimum per-tensor-normalized magnitude is1.67785e-7 and the median is5.6864%. About2.002% of values are below0.1% of their tensor maximum. A lower-tail source screen at normalized magnitudes1e-4,1e-5,1e-6 and the actual minimum produced a measurable q1e-4 point at0.0119% of full-scale charge, while the smaller points printed the same charge as the zero case. The writer remained transparent, and the reported charge precision is coarse relative to the smallest differences. This is a simulator-resolution limitation in this diagnostic, not proof that the physical circuit has zero response or a basis for dropping the float weights. Evidence: `artifacts/analog_asic/results/gf180_physical_weight_amplitude_lowtail_v1_defaulttol_src560b1cb1ed2f.json` and the checkpoint/export verification in the accompanying run log.





Next, determine the inference sensitivity to the measured low-tail transfer and establish a useful analog sensitivity/noise floor. Retain every original float coefficient while evaluating continuous analog mappings. If the current source range is inadequate, investigate a wider analog current range or analog gain selection before connecting the addressed weight read to the whole network.





## Original-float low-tail inference sensitivity - 2026-10-13





Replayed four validation-listed440x640 records through all25 original-float actors and10 temporal updates from the verified epoch58 checkpoint. The q0.1 held-cell result is29.1% above its normalized target, so the sensitivity screen applied a continuous1.291 gain to actor weights whose effective post-ChannelAffine magnitude is below0.1% of their tensor maximum. This changes no signs, zeros no coefficient, and uses no quantized reference. Of143,728 actor weights,2,878 were perturbed. Mean-IoU deltas were-0.000567,+0.000607,-0.000124, and-0.000958; the average is-0.000261 and the average pixel-change fraction is9.59%. The error can move mean score either way across scenes and remains visible in class labels.





The perturbation extrapolates a single measured q0.1 point uniformly to all smaller coefficients, while the extracted source screen could not resolve q1e-5 and below. Four records are a small subset, not full validation accuracy, measured small-current behavior or analog acceptance. The v1 replay used raw-convolution normalization and is superseded by the corrected post-affine v2. Evidence: `scripts/replay_gf180_float_weight_lowtail_sensitivity_v2.py` and `artifacts/analog_asic/results/gf180_float_weight_lowtail_sensitivity_4record_summary_v1.json`.





## Settled low-current transfer screen - 2026-10-13





To separate event-edge feedthrough from source current, the extracted bench now averages current only from10.2us to10.8us within the1us read window and subtracts a matched zero-weight branch inside ngspice before printing. At normalized magnitude1e-4 (0.01% of tensor maximum), measured current is1.833e-16A, or0.01094% of full scale, close to the target. At1e-5,1e-6 and the actual minimum1.68e-7, the differences are -1.0e-17A,-3.45e-17A and-2.5e-17A, respectively; these are residuals rather than meaningful signal and are inconsistent with the positive weight transfer. Thus the current cell/readout/simulator composition does not resolve those lowest points at TT27. Evidence: `artifacts/analog_asic/results/gf180_physical_weight_amplitude_lowtail_v3_src2348b45e6cda.json`.





This is a deterministic simulation result with no statistical device mismatch or noise and does not establish the physical noise floor. It does show why setting raw float extrema as capacitor voltages is not sufficient by itself: the capacitor may accept the voltage, but the cell must convert the resulting value into a signed current above readout offset and noise. Keep all weights present and investigate a more sensitive analog current range or gain selection, then verify the effect over more full-float records.





## Signed low-current residual sensitivity - 2026-10-13





Applied a continuous signed offset equal to1.5e-5 of each actor tensor maximum to the557 post-ChannelAffine weights below normalized1e-4, in both directions, then replayed four validation-listed440x640 frames with all25 original-float actors and10 updates. Toward-zero offsets changed0.763% of pixels on average with mean-IoU deltas+0.001373,+0.000879,+0.001036,+0.001024 (average+0.001078). Away-from-zero offsets changed0.713% on average with deltas-0.001231,-0.000610,-0.000911,-0.000717 (average-0.000867). This bounds sensitivity to the deterministic nominal residual magnitude; it does not establish a physical offset sign/distribution, noise floor, measured transfer below1e-4, PVT behavior or network acceptance. The result supports mapping continuous float values over the capacitor's usable voltage span while improving current-path resolution; voltage-range fit alone cannot guarantee readable charge. Evidence: `scripts/replay_gf180_float_weight_lowtail_offset_sensitivity_v1.py`, four per-record JSON reports and `artifacts/analog_asic/results/gf180_float_weight_lowtail_offset_sensitivity_4record_summary_v1.json`.





## Refined low-tail inverse-current map and held-read boundary - 2026-10-13





The original settled low-tail screen used current absolute tolerance1e-16A, above the expected q1e-5 target (~1.68e-17A). A first extreme setting at1e-22A failed immediately; a moderate1e-19A setting converged for the transparent-writer source/reader bench. Sweeping the held-gate command in 1mV then0.1mV steps found a monotone zero-subtracted region near3.115-3.129V. In the calibrated-point screen, q1e-5 at3.1194V measured1.67e-17A (0.9964e-5 full scale) in one composition and1.84e-17A (1.098e-5) in a second; q1e-4 at3.079V measured1.811e-16A and1.833e-16A (about1.08-1.09e-4). Thus a continuous nonlinear inverse map plausibly covers q1e-5 nominally, with about10% composition spread.





The apparent q1e-6 and checkpoint-minimum points are not qualified: the0.1mV sweep crosses zero near3.1285V, but another extracted bench composition at3.12831V reported2e-18A against a2.81e-19A target. Tightening to1e-20A did not converge. Actual low-tail writer/held-MIM/readout benches also abort at the writer transition even with1e-16A tolerance, so these screens do not establish stored low-tail read accuracy. Only the prior q0.1%-to-full sample/hold points remain held-map evidence. Continue with physically matched offset/reference cancellation and a stable held read; retain every original float value. Evidence: `scripts/screen_gf180_physical_weight_amplitude_lowtail_v7_fine_gate_sweep.py`, `...v8_minimum_gate_sweep.py`, `...v9_calibrated_points.py`, `...v10_calibrated_tightertol.py`, and `scripts/screen_gf180_physical_weight_amplitude_transfer_v7_lowtail_hold.py` through `...v11_lowtail_hold_edgeshift.py`.





## Physical low-tail sample/hold read exposes baseline error - 2026-10-13





Shifted the existing physical writer ramp from100ns to1us. The extracted nine-MIM sampled-weight cell, writer, signed source and active charge reader now complete the transient for zero, q1e-5, q1e-4 and full scale. At9us, q1e-5 and q1e-4 held gates are3.11859V and3.07821V from commands3.1194V and3.079V, about0.8mV lower. Zero-subtracted settled 10.2-10.8us current fractions are4.386e-4 and6.331e-4 of full scale, versus targets1e-5 and1e-4; integrated read charges are4.471e-4 and6.472e-4, respectively. Full scale reads1.0. Thus transparent-writer calibration does not predict the held low-tail response. The low-tail read has a large residual/reference/feedthrough component; baseline cancellation and held-gate correction need physical measurement. The current result is nominal TT27, no mismatch/noise/PVT, no addressed array, model accuracy or5ms acceptance. Evidence: `scripts/screen_gf180_physical_weight_amplitude_transfer_v12_lowtail_hold_slowwrite.py`, corrected analyzer `scripts/screen_gf180_physical_weight_amplitude_transfer_v13_lowtail_hold_slowwrite_corrected.py`, and `scripts/screen_gf180_physical_weight_amplitude_transfer_v14_lowtail_hold_current.py`; the authoritative report is `artifacts/analog_asic/results/gf180_physical_weight_amplitude_transfer_v14_lowtail_hold_current_src9ace85408ed3.json`.








## Physically held weight-gate calibration - 2026-10-13





The prior held-cell low-tail screen used the transparent-writer inverse-map commands3.1194V and3.079V and measured q1e-5/q1e-4 about44x/6.3x high. v17 measured the held gate before/during/after READ and found only about0.01-0.02mV movement across the read event, ruling out meaningful read-edge gate disturbance. A coarse multibranch sweep v19 showed monotonic gate-to-current response but is only a map because its multi-branch composition differs from the four-case calibration.





The four-case v22 extracted run moved command gates to3.289V and3.236V; charge fractions were2.353e-5 and1.353e-4, respectively. One correction step produced v23 command gates3.294V and3.243V. The actual held gates measured3.29304V and3.24209V; zero-subtracted integrated charge fractions were1.1767e-5 and1.1767e-4, each about17.7% above target. Full-scale remained1.0. This is a usable nominal held-cell starting map, not acceptance. The result supports calibrating the actual float-to-capacitor voltage mapping from the physically held nonlinear transfer; it does not mean all float values should be linearly mapped across raw voltage limits. The checkpoint minimum1.68e-7 remains unqualified. v21 tightening solver abstol to1e-19A failed at the writer transition and is retained as an incomplete run.





Next use a matching independent held-cell composition to confirm transfer repeatability, then cover the original-float range continuously and evaluate a lower-current analog gain/range where required. Preserve every coefficient. No mismatch/noise/PVT, addressed-array, model replay or5ms acceptance was established here. Evidence scripts: `scripts/screen_gf180_physical_weight_amplitude_transfer_v17_hold_gate_during_read.py`, `scripts/screen_gf180_physical_weight_amplitude_transfer_v19_held_gate_map_sweep.py`, `scripts/screen_gf180_physical_weight_amplitude_transfer_v22_held_gate_transfer_recalibration.py`, and `scripts/screen_gf180_physical_weight_amplitude_transfer_v23_held_gate_transfer_recalibration.py`. Reports: `artifacts/analog_asic/results/gf180_physical_weight_amplitude_transfer_v17_hold_gate_during_read_src43c823780518.json`, `...v19_held_gate_map_sweep_srce8e9bce1faa4.json`, `...v22_held_gate_transfer_recalibration_srcaf2501b358a7.json`, and `...v23_held_gate_transfer_recalibration_srca9018ecd8428.json`.








## Independent held-cell low-tail repeatability - 2026-10-13





The v23 command gates were re-run in two independent three-branch extracted compositions (zero, target, full). Both simulations complete with the same1us write ramp and measured gate held at3.29304V for q1e-5 and3.24209V for q1e-4. The q1e-5 charge fraction is1.1789e-5 (1.179x target) and current fraction1.2320e-5. The q1e-4 charge fraction is1.2378e-4 (1.238x target) and current fraction1.1901e-4. Full-scale is unity in both. This confirms the v23 held-cell transfer is reproducible to within about5% relative at q1e-4 across these branch compositions and about0.2% at q1e-5. It remains a nominal TT27 transistor-level result; no mismatch/noise/PVT, minimum-weight point, addressed array, float inference or5ms acceptance.





Evidence: `artifacts/analog_asic/results/gf180_physical_weight_amplitude_transfer_v24_independent_q1e5_src073f25f38f06.json` and `artifacts/analog_asic/results/gf180_physical_weight_amplitude_transfer_v24_independent_q1e4_src75d4978d85ed.json`.








## Original-float membrane range mapping - 2026-10-13





The existing epoch58 calibration replay measures post-reset/inhibition state for all25 analog actors and all30,976,000 membrane identities on eight calibration records, then derives one analog representation range per8x8 spatial tile (490,240 ranges). Each uses25% headroom and a floor of four times that channel's base threshold. Across tiles, the absolute state-range estimate spans1.5719 to19,100.21 model units, with median102.33. A single global scale would waste most of the capacitor's usable voltage swing on many tiles or clip the largest-range tiles. The chosen direction is to map each tile's measured original-float range continuously onto its usable capacitor voltage span, with a local gain/reference and consistent scaling through beta, synaptic contribution, threshold, reset, inhibition, adaptation and readout. This is analog range normalization, not quantization or QAT.





The calibration is an existing software replay with baseline predictions unchanged; it does not show physical per-tile gain/reference distribution, capacitor voltage limits, noise, leakage, unseen-scene headroom or5ms service. Implement the local scale/reference path and verify the scaled recurrence against the original float model before claiming preserved accuracy. Evidence: `scripts/calibrate_gf180_float_state_tiles.py` and `artifacts/analog_asic/results/gf180_float_state_tile_calibration_dc685af8e3_srcc47640d01bc7.json`.








## Membrane float-range to physical bank manifest - 2026-10-13





Generated `artifacts/analog_asic/assembly/membrane_voltage_scale_manifest_v1.json` from the verified epoch58 eight-record range calibration and the permanent analog-state selector map. It binds each of490,240 channel-specific 8x8 spatial range values to its existing categorical bank address, covering all25 actors and30,976,000 membrane identities. Each scale applies to at most64 resident state capacitors. The mapping contract is `Vmem=VCM+(usable_signed_voltage_half_swing/Rtile)*state`; usable physical half-swing remains unset until the actual capacitor/read/restore path is characterized. No membrane identity, graph edge or numerical float was changed.





The separate native local-gain injection screen already has a calibrated fixed16x pulse-duration implementation for signed event increments, but it uses externally calibrated program references and is not connected to the per-bank range manifest. Next implement the shared bank scaling at the analog update interface and verify beta, weighted contribution, threshold, reset, adaptation and readout under one consistent scale. The manifest is a mapping artifact, not a physical range cell, full recurrence, accuracy or5ms acceptance. Source: `scripts/assemble_gf180_membrane_voltage_scale_manifest_v1.py`; inputs: `artifacts/analog_asic/results/gf180_float_state_tile_calibration_dc685af8e3_srcc47640d01bc7.json` and `artifacts/analog_asic/assembly/full25actor_permanent_analog_state_selectors_v1.json`. Existing gain-path evidence: `artifacts/analog_asic/results/gf180_local_gain_programming_calibration.json`.








## Measured membrane capacitor voltage span - 2026-10-13





The native extracted sampler/read/restore range screen uses a1.65V read common mode and tests stored differential state from-0.9V to+0.9V (absolute Vinput points0.75-2.55V). Across the seven overlapping lower/middle/upper points, maximum measured round-trip error is8.238mV. The banked continuous mapping is now explicitly `Vstored=1.65V+(0.9V/Rtile)*state`, where `Rtile` is the guarded calibrated absolute float range for that (actor,channel,8x8 tile). This directly assigns the original float state range to the measured nominal capacitor voltage span; it introduces no QAT or numerical state quantization.





Manifest: `artifacts/analog_asic/assembly/membrane_voltage_scale_manifest_v2.json`. Voltage evidence: `artifacts/analog_asic/results/gf180_restore_state_range_boundary.json`. The tested physical range is nominal extracted module characterization and does not establish per-bank scale programming, scale-dependent update accuracy, mismatch/noise/PVT, unseen-scene headroom, full-model accuracy or5ms service. The earlier v1 manifest intentionally left endpoints unset and is superseded by v2.








## Routed bank-scale candidate and 5 ms extracted transfer — 2026-10-13





Combined the physically qualified held 9-MIM writer/current cell with a long-channel PFET scale device in `gf180_membrane_scale_current_cell_v6`. The parent includes full routed interconnect, exposes the programmed weight/gate and scale-current terminals, and passes Magic full-style DRC (0), unique hierarchical LVS, extracted-capacitance generation, GDS export, and GDS-readback DRC/LVS. Parent bounding box is 780.3 x 414.2 um. The previous parent attempts are retained; LVS failure in v4/v5 came from omitting the via4 connection at the child metal5 pins.





The corrected ngspice47 TT27 transient uses the parent capacitance-extracted netlist, the extracted charge reader, and one 1 us read after a 5 ms gate hold. Zero-subtracted current fractions at normalized scales 8.23e-5, 0.01536, and 1.0 are 8.132e-5, 0.014920, and 1.0 (about -1.2%, -2.9%, and 0% relative to targets). Held-gate movement between 9 us and 5 ms is about 7.1-8.5 mV. The zero-scale baseline is measured and subtracted. This is deterministic nominal simulation, not mismatch/noise/PVT evidence; gate commands retain the prior nominal map and have not been recalibrated against the physically routed macro.





Evidence: `scripts/build_gf180_membrane_scale_current_cell_v6.py`, `artifacts/analog_asic/layout/gf180_membrane_scale_current_cell_v6/qualification.json`, `scripts/screen_gf180_membrane_scale_mim_gate_reader_v4.py`, and `artifacts/analog_asic/results/gf180_membrane_scale_mim_gate_reader_v4.json`. Scope excludes scale-weight multiplication, signed event aggregation, membrane update/restore, original-float accuracy replay, and full-population 5 ms service. The 780.3 x 414.2 um parent footprint is not yet shown feasible when replicated per bank; evaluate shared or smaller scale application before full replication.








## Compact one-MIM scale-cell layout probe — 2026-10-13





A smaller scale-hold cell was explored using one stored MIM bank, a routed transmission-gate writer and the qualified scale PFET. The initial version using `gf180_mim_7x7` is unsuitable for parent routing: its bottom-plate pin is on `mimcapcontact`, and the trial produced 16 full-style DRC errors plus shorted gate/reference pins. A second version using the previously qualified metal-access `gf180_mim_bank_7x7_n9` reduced the stack to a usable routed-pin basis, but its parent still produced 11 full-style DRC violations (via enclosure/minimum-area and child-device overlap issues). Neither compact macro passed LVS/readback or is usable for simulation. Preserve both attempts under `artifacts/analog_asic/layout/gf180_membrane_scale_compact_v1/` and `_v2/`, with build scripts `scripts/build_gf180_membrane_scale_compact_v1.py` and `_v2.py`.





The qualified v6 parent remains the only assembled scale macro result. Next fix the compact parent pin geometry and route clearances, then simulate the exact compact extracted cell before evaluating bank replication.






## Spatial sharing of membrane voltage scales - 2026-10-13



Merged adjacent original guarded 8x8 float ranges by their maximum and evaluated how the already measured 8.238mV state-storage roundtrip bound maps back into each original 8x8 range. This leaves the trained floats and weights untouched; it is a deterministic representation-range comparison, not QAT or inference simulation.



16x16 spatial banks reduce scale cells from 490,240 to 126,400 (3.88x). Weighted across actual membrane identities, the mapped roundtrip bound is median 0.969%, p95 1.803%, p99 8.823%, and maximum 714% of the original 8x8 range; 1.466% of states exceed 5% and 0.946% exceed 10%. 32x32 banks use 33,920 scales with 3.264% of states above 5%, 1.794% above 10%, and a 4,262% worst-case bound. 64x64 and 128x128 reduce scales further but worsen the tails. Keep 8x8 as the fidelity baseline until a coarsened-state original-float replay establishes actual segmentation effect.



Evidence: `scripts/analyze_gf180_membrane_scale_bank_coarsening_v2.py` and `artifacts/analog_asic/results/gf180_membrane_scale_bank_coarsening_v2.json`. This estimate treats the measured roundtrip bound as an absolute voltage-error scale and omits full temporal recurrence, error cancellation, saturation, noise, mismatch and unseen-scene behavior. It does not decide whether coarser banks preserve model accuracy.



## Eight-record membrane-scale coarsening stress replay - 2026-10-13

The original epoch58 float model was replayed on all eight calibration records. Every unperturbed prediction hash matched its existing calibration record. A deterministic error surrogate added the measured8.238mV capacitor roundtrip bound, mapped through each bank range, to the stored membrane after every PLIF update and clipped the result to bank rails. We compared 8x8 and16x16 bank ranges with alternating signs and also stressed16x16 with one-sided positive and negative bound errors. Original weights/equations were retained and QAT stayed disabled.

For16x16, mean mIoU change across the eight records was-0.0206 for alternating signs,-0.0354 for positive bound error, and-0.0495 for negative bound error. Mean pixel-change fractions were41.2%,44.2%,and45.9%, with7.68%,12.07%,and14.93% membrane clipping. The8x8 alternating-sign stress produced+0.0044 mean mIoU change,31.9% pixel changes and2.51% clipping. The unusually large, order-dependent response at both bank sizes shows this per-update full-bound surrogate is too conservative to stand in for a measured circuit error distribution; a positive mIoU in this scenario is not evidence of analog equivalence. It does show that16x16 cannot be adopted from range arithmetic alone. Retain8x8 pending a calibrated storage/update error model or exact extracted recurrence replay.

Evidence: `scripts/replay_gf180_membrane_scale_coarsening_v2.py`, `artifacts/analog_asic/results/gf180_membrane_scale_coarsening_replay_summary_v1.json`, and its eight per-record reports. This is software recurrence sensitivity analysis, not transistor simulation, measured error statistics, or model accuracy acceptance.


## Compact GF180 membrane scale parent v16 — 2026-10-13

The compact parent was rebuilt with wide child spacing after v4/v5 extracted nets merged. The v16 extracted netlist has the intended independent PROGRAM, WRITE, WRITEB, VCM, SCALE_OUT, VDD, VSS and SCALE_GATE nets. Magic full-style DRC reports zero errors; Netgen LVS matches uniquely; GDS readback has zero DRC errors and unique LVS. It contains one native 7um MIM bank (nine capacitors internally), one transmission-gate writer, and one long-channel PFET. The top-level bbox is 1271.5 x 100.1 um, approximately 0.1273 mm2. The width is dominated by spacing and global route tracks, so this validates connectivity and function but is not yet a dense reusable cell.

An extracted transient write/hold simulation at GF180 typical, 27C programmed 0.75V, 1.65V and 2.55V. At 5ms the stored values are 0.74959V, 1.65024V and 2.55109V respectively. The 19-point transfer sweep is monotonic over 0.75–2.55V, while PFET read current is strongly nonlinear: 1.55989uA at 0.75V, 404.827nA at 1.65V, and 1.42215nA at 2.55V. A calibrated inverse transfer is therefore required before mapping original-float bank values to current.

Evidence: `artifacts/analog_asic/layout/gf180_membrane_scale_compact_v16/qualification.json`, `artifacts/analog_asic/results/gf180_membrane_scale_compact_v16_hold5ms.json`, and `artifacts/analog_asic/results/gf180_membrane_scale_compact_v16_transfer19.json`. This is nominal single-cell simulation only; no measured mismatch/noise/PVT, full-float recurrence replay, signed weighted update, bank replication, or full-chip service acceptance is established.


## Compact scale parent v23 area reduction and extracted replay — 2026-10-13

The v23 parent keeps the proven TG/PFET spacing from v16 and shortens the global metal5 rails to the placed-cell bounds plus routing margin. Full-style DRC0, unique LVS and GDS readback DRC0/LVS unique remain clean. The extracted bbox is 270.5 x 100.1 um (0.02708 mm2), a 4.7x reduction from v16; full extracted connectivity is unchanged.

The 5ms write/hold simulation reproduced v16: programmed states at 0.75/1.65/2.55V finish at 0.74959/1.65024/2.55109V. The 19-point v23 transfer sweep is likewise monotonic, with read current from 1.55989uA at 0.75V to 1.42215nA at 2.55V. It remains strongly nonlinear and requires calibration against the actual original-float bank-value distributions.

Evidence: `artifacts/analog_asic/layout/gf180_membrane_scale_compact_v23/qualification.json`, `artifacts/analog_asic/results/gf180_membrane_scale_compact_v23_hold5ms.json`, and `artifacts/analog_asic/results/gf180_membrane_scale_compact_v23_transfer19.json`. This is still a nominal single-cell result, not recurrence, inference or full-chip acceptance.


## Nominal transfer-range coverage check — 2026-10-13

The compact v23 19-point extracted current sweep spans a nominal 1096.85:1 from 0.75V to 2.55V. Compared with the previously computed 202.52:1 pulse-window scale requirement, linear interpolation places the corresponding minimum-current point near 2.4485V (target 7.702nA), leaving about 0.1015V unused at the high-voltage end. This only establishes nominal range coverage between measured points; it does not establish linearity, noise-floor margin, matching, signed-current delivery, original-float recurrence accuracy or 5ms model service.

Evidence: `artifacts/analog_asic/results/gf180_membrane_scale_compact_v23_transfer_range_check_v1.json`; underlying sweep and requirement reports are referenced there.

## Routed signed update and membrane state parent v8 — 2026-10-13

The v7 composed GF180 parent passed full-style DRC, hierarchical LVS and GDS round-trip. v8 tightens top-level metal5 track pitch from50um to10um and moves the state/update child to a clear adjacent location. Full-style Magic DRC remains0, Netgen LVS remains unique, and GDS readback DRC/LVS both pass. Bbox is4550.6x1365.45um (6.21mm2), down57% from v7's14.44mm2; it remains a spacious characterization fixture because the signed injector child itself spans3725um.

Corrected the extracted transient ordering to apply beta to the prior state before the current event, matching the PLIF equation. At TT27, magnitude command1.5, PPROGRAM=2.7V, NPROGRAM=0.455V, and the extracted v8 parent: positive event step is+13.15mV; negative is-12.66mV (3.8% magnitude mismatch). Beta changes the centered initial state by-0.49mV before either event. Stored state drift from post-event through5ms is0.00mV positive and+0.01mV negative at report precision. The correct-order test avoids the earlier event-then-beta measurement, which was not model-faithful. v15 also used an incorrect DATA hookup; v21 failed at a sharp beta edge; all failures are retained as bench diagnostics.

Evidence: `artifacts/analog_asic/layout/gf180_signed_state_update_composed_v8/qualification.json`; `artifacts/analog_asic/results/gf180_signed_charge_state_update_v24.json` and `v25.json`; bench generators `scripts/simulate_gf180_integrated_signed_charge_state_update_v24.py` and `v25.py`. These are two nominal fixed-magnitude TT27 cases, not full transfer curves, calibrated original-float recurrence, PVT/noise/mismatch, 64-state bank service or full-chip acceptance. The v8 geometry is not dense macro area.

## Original-float storage endpoint check and signed-charge boundary — 2026-10-13

The current continuous state map uses Vstored=1.65V+0.9V*state/range, spanning0.75-2.55V for each local8x8 float interval. Re-ran the actual routed3T/50fF under-MIM storage cell at those endpoints and center with VCM=1.65V, 3.3V write wordline, extracted31 nonnegative capacitance branches per cell, 5ms hold, then selected read and release. Write-release errors are-4.57/-6.12/-5.51mV; maximum held excursions2.90/6.59/13.47mV; read-release state changes-4.03/-2.01/+0.21mV. The three-point storage transfer is monotonic. The prior1.0-1.4V screen was limited coverage, not a demonstrated hard range. The selected storage cell therefore supports testing the full mapped span at nominal TT27. Source-follower offsets are large and uncalibrated (about0.797/1.023/1.213V); read mapping remains to calibrate. This is a one-cell screen with ideal external wordline/data/reference/current drivers, not full-bank or model acceptance.

The center-calibrated pulse injector is not range independent: at a post-beta low state, the nominal negative event moves+44.65mV; at a post-beta high state, nominal positive moves-54.18mV. Raising NPROGRAM to0.60V restores a negative step but produces-360mV; lowering PPROGRAM to2.60V produces+41.76mV. The routed v8 parent remains electrically qualified and its centered +/-13mV tests pass, but this does not establish signed updates over0.75-2.55V.

Switched-cap packet diagnostics are still inconclusive. Early versions had a top-plate common-mode mismatch and large state disturbance. In the later extracted TG/MIM sequence, both packet plates track STATE through beta, the bottom is then connected to an ideal state-matched driver and stepped, and the top stays connected through the step. The bottom-source integral is-0.544fC over a26mV step; the state node is unchanged to 6-digit report precision during the packet. Opening the top TG then shifts STATE by-40.37mV; a zero-step control gives-39.995mV. The packet signal is therefore buried by the switch edge and not yet shown to update membrane state. Do not treat the earlier nominal endpoint deltas as acceptance. Next establish a non-disturbing state-tracked packet sample or a state-independent current injector, then bind it to the qualified shared bank and replay the original-float recurrence.

Evidence: `scripts/simulate_gf180_shared_analog_memory_3t_v2_range5ms_v2.py`, report `artifacts/analog_asic/results/gf180_shared_analog_memory_3t_v2_three_native_5ms_srce94a1c303383.json`; endpoint pulse reports `gf180_signed_charge_state_update_v27.json`, `v28.json`, `v29.json`, `v30.json`, `v31.json`, `v32.json`; switched-cap reports `gf180_sc_membrane_packet_lo_p_r3_9fccb3e4cb.json`, `gf180_sc_membrane_packet_hi_n_r3_9fccb3e4cb.json`, `gf180_sc_membrane_packet_lo_p_r4_9fccb3e4cb.json`. Failed/incorrect packet and pulse benches remain preserved and are not acceptance evidence.

## Switched-cap packet loading probe — 2026-10-13

The PDK model gives the 5x5um MIM packet about49.75fF area capacitance plus4.77fF perimeter capacitance (about54.5fF total);0.51842fF in the extracted netlist is a parasitic term, not the MIM value. A shortened transient measured before and after the bottom-plate edge and before top-switch release. At the low endpoint setup, a26mV bottom step produces+9.631mV while connected, then the top TG release produces-40.371mV; a135mV bottom step produces+50.003mV while connected, then-41.932mV on release, leaving a net+8.072mV. The 5ms result for the latter is0.378mV above its post-release value. At the center setup, no packet step gives-31.000mV net;80mV gives-2.400mV and110mV gives+8.330mV. At the high endpoint setup, the no-step release kick is-20.000mV; a60mV step gives+22.100mV connected movement and+1.450mV net, while140mV gives+51.570mV connected movement and+30.050mV net. Sparse interpolation puts local zero-update packet steps near112.3mV low,86.7mV center and55.9mV high. The trend is roughly affine in the three sampled states and supports a state-conditioned offset map as the next candidate for signed updates. It remains a hypothesis: data are sparse, one-polarity, nominal TT27 samples. The prior3.03fC integral spans the switch release and is not a packet-only measurement. A no-beta-pulse case retains a roughly-40.6mV release kick, so the beta pulse is not its cause. The TG output contributes6.02807fF to VSS. The packet transfers successfully while connected; the remaining problem is state-dependent top-switch release error and its calibration/cancellation.

Next characterize the complete packet step-to-net-state transfer densely across stored state, polarity, pulse order and representative weights; then fit a state-dependent zero-update correction and replay it against the original-float PLIF update. Keep feedthrough cancellation as a parallel option if the required offset accuracy is too tight. These are nominal TT27 schematic compositions using extracted child netlists and ideal external packet/common-mode drivers; they are not a routed full cell, PVT/noise result, model replay, or5ms service acceptance except for the one low-state 135mV point.

Evidence: `artifacts/analog_asic/results/gf180_sc_packet_signed_transfer_curve_v1.json`, `artifacts/analog_asic/benches/gf180_sc_membrane_packet_lo_p_fastedge_v1.spice`, `artifacts/analog_asic/results/gf180_sc_membrane_packet_lo_p_fastedge_v1.log`, `artifacts/analog_asic/benches/gf180_sc_membrane_packet_lo_p_compkick5ms_v1.spice`, `artifacts/analog_asic/results/gf180_sc_membrane_packet_lo_p_compkick5ms_v1.log`, and the exploratory switched-cap benches/reports cited above.

## Packet precharge handoff correction — 2026-10-13

The same low-state bench showed a second error before the event: after beta, STATE is0.837547V; opening the sample TG drops it to0.802955V, then connecting the bottom driver at0.837545V raises it only to0.814432V. The combined handoff leaves a-23.113mV pre-event error. Turning on the bottom driver before opening the sample TG does not remove this error. Raising the driver baseline by62mV, from0.837545V to0.899545V, makes the post-handoff state0.837400V, within0.15mV of the post-beta value. Under that baseline, a110mV packet step leaves-0.725mV net after top-TG release; a135mV step leaves+8.179mV and changes by+0.348mV over the remaining nominal5ms. This is an encouraging single-state compensation screen, not a qualified design: only the low endpoint was exercised, the drivers are ideal, the baseline/packet mappings are not physically implemented, and negative/full-float updates, mismatch, PVT, noise, layout and model replay remain open.

Evidence: `artifacts/analog_asic/results/gf180_sc_packet_handoff_compensation_v1.json` and its hashed benches/logs.

## Signed packet update and 5ms hold at three state levels — 2026-10-13

Applied the fitted baseline and per-state zero-update offset at low, center and high storage levels. One positive event at each level yields+8.179mV,+7.380mV,+7.660mV; one negative event yields-8.560mV,-8.350mV,-8.080mV. Positive 5ms post-release drift is+0.348mV,+0.070mV,+0.010mV; negative drift is+0.367mV,+0.070mV,+0.020mV. The compensated sample/drive handoff remains within0.27mV of the post-beta state at all three tested points. This is the first nominal extracted-cell demonstration of both signed packet updates over the mapped voltage span with a 5ms hold on all six cases. The amplitudes and baselines are hand-chosen from sparse calibration, and their voltage-generation circuit is idealized. No checkpoint-derived weight transfer, accumulated multi-event sequence, dense range coverage, mismatch/PVT/noise, model inference, physical parent layout or full-chip service has passed.

Evidence: `artifacts/analog_asic/results/gf180_sc_packet_signed_state_compensation_v1.json` and its hashed benches/logs.

## Full-frame original-float range diagnostic — 2026-10-13

Ran the original epoch58 float checkpoint on one full 440x640 training frame, all ten5ms updates and all25 PLIF actors, recording both pre-threshold candidates and post-reset states. The existing per-8x8 range map came from eight other calibration records and can under-cover this frame: sizing each bank to include its largest candidate and the existing four-times-threshold floor requires a median0.91x expansion, p90 1.44x, p99 22.3x, p99.9 205x and max605x. About5.82% of banks need over2x,1.58% over10x and0.409% over100x. The widened-range estimate drives the smallest analog threshold to16uV, while the median threshold remains5.68mV. This shows that simply widening every affected bank risks losing usable threshold margin; the 8x8 scale allocation needs refinement or a precision-preserving range strategy before full-float packet mapping can be accepted.

This is exact original-float software on one complete real frame, not QAT or analog inference. The analog voltage mapping is applied as a range diagnostic only. The data do not establish whole-dataset state bounds, acceptable hardware noise/mismatch, or model accuracy. Evidence: `artifacts/analog_asic/results/gf180_train_record_state_range_diagnostic_v1.json` and the unchanged checkpoint/model/calibration hashes recorded there.

## Stored-state versus candidate range follow-up — 2026-10-13

The capacitor stores the post-reset membrane, so the range diagnostic was split into post-reset storage state and pre-threshold candidate. The rare expansion remains in the stored state; the candidate does not explain it away. Eight contiguous full 440x640 training frames from `zurich_city_00_a` were run through all ten updates of the epoch58 original-float model. Across frames,1.90-2.11% of state sites require over2x the existing validation-derived per-site range,0.697-0.770% over10x, and0.099-0.117% over100x. The p99 expansion is5.16-6.09x, p99.9 is100.69-107.23x, and full expansion lowers the minimum threshold to15.55-16.10uV. All frames are contiguous within one sequence; these measurements do not establish independent-scene coverage, hardware accuracy or a viable noise floor.

Reports: `artifacts/analog_asic/results/gf180_train_record_state_range_diagnostic_v3_record0_store_vs_candidate.json` through `...record7_store_vs_candidate.json`. Source: `scripts/diagnose_gf180_train_record_state_range_v3_store_vs_candidate.py`.

## Existing capacitor range saturation replay — 2026-10-13

Ran the original epoch58 float model on eight full 440x640 contiguous training frames from `zurich_city_00_a`, with QAT disabled. Clamping the pre-threshold candidate to the existing per-8x8 capacitor range changed1.41-1.62% of prediction pixels and produced mean present-class mIoU delta-0.000364 (worst-0.000902). Clamping only post-reset stored state changed1.12-1.40% of pixels and produced mean delta-0.000349 (worst-0.000449). Labeled pixel accuracy changed by-0.000843 and-0.000790 on average, respectively. About1.6% of state values clipped. This supports keeping the existing range without widening it everywhere, as a provisional article-prototype choice. The limiter is idealized, sequence coverage is one scene, and no extracted packet/clamp interaction is included.

Report: `artifacts/analog_asic/results/gf180_train_record_voltage_range_saturation_v1_summary.json`, with eight hashed frame reports. Source: `scripts/replay_gf180_train_record_voltage_range_saturation_v1.py`.

## Always-connected state rail clamp screen — 2026-10-13

Simulated diode-connected GF180 NMOS/PMOS clamps continuously attached to a native5x5um MIM membrane node, with 4.77fF parasitic and TT27 models. Under a roughly±0.44fC packet at the voltage-window endpoints, the unclamped state holds the expected-rail update sign for5ms. With clamps attached, the low negative update recovers across its starting value to0.7573V, while the high positive update recovers down to2.5475V. This reverses the requested update polarity at the range edges. The topology is rejected; a phase-gated clamp has not been simulated.

Report: `artifacts/analog_asic/results/gf180_state_diode_clamp_screen_v1.json`; source benches and ngspice logs are hash-listed there.

## Phase-gated switched rail limiter — 2026-10-13

Composed the native5x5um MIM state with an extracted quarter-size transmission gate to connect the state node to a compensated shared rail for8.8us after an out-of-range update. At TT27, a low-rail negative packet moved0.750003V to0.743320V before the limiter and0.750017V after5ms. A high-rail positive packet moved2.550000V to2.556680V before the limiter and2.550010V after5ms. The two inward cases bypassed the limiter and held+7.499mV/-7.500mV over5ms; midpoint held at1.650000V. References0.7496V/2.5472V compensate nominal opening kick. This is a module-level nominal transient with ideal phase commands, not a physical range detector, routed combined parent, PVT/noise/mismatch or full model test.

Report: `artifacts/analog_asic/results/gf180_state_phase_gated_clamp_screen_v8.json`; hashed source bench and simulator log are recorded in the report.

## Float-state voltage mapping and extracted limiter-parent screen — 2026-10-13

The membrane encoding is already a direct affine mapping of the original signed float state into the safe capacitor span: `Vcap = 1.65 V + 0.9 V * state / R_tile`. The unresolved choice is the per-tile float interval `R_tile`. Existing calibration intervals are finite and can miss rare states in later frames; saturation remains a provisional article-prototype choice because widening all intervals sharply reduces the smallest analog threshold. The eight-frame full-float clipping replay measured mean mIoU change-0.000364 on one contiguous sequence, not dataset-wide analog accuracy.

Built `gf180_signed_state_update_limiter_v10`, placing and routing the extracted signed injector/state-update parent with low and high rail TGs on the shared STATE node. Magic DRC=0, unique LVS, GDS round-trip DRC=0 and unique LVS. The pin-exposed test parent measures6.53x1.91mm and is not the compact reusable macro. Combined extracted TT27 transient screens use an ideal0.44fC current pulse and externally timed limiter gates. After calibrating rail references separately, the low endpoint holds0.750000V and the high endpoint2.550000V at5ms (six-digit simulator output). Reports: `artifacts/analog_asic/results/gf180_signed_state_update_limiter_v10_combined_extracted_screen.json`; layout qualification: `artifacts/analog_asic/layout/gf180_signed_state_update_limiter_v10/qualification.json`.

Limitations and next action: the physical range comparator, packet-to-charge map, PVT/noise/mismatch, inward updates in this combined parent, full PLIF recurrence, and complete chip remain unqualified. Under the ideal pulse source, the attached parent changes STATE by only about0.29mV; diagnose its loading and compact STATE routing before connecting the checkpoint-derived analog weight map. External limiter phases do not establish autonomous range detection or bin service.


## Routed switched-capacitor signed membrane packet — 2026-10-13

The physical integration parent `gf180_sc_state_packet_compact_v12` combines the native state cell, one 5x5um MIM packet, and three quarter-size transmission gates for packet parking, sampling, and weight drive. Its bbox is 527x93.45um (0.04925mm2). Magic full DRC=0, unique LVS, GDS roundtrip DRC=0 and unique LVS. Single-source control pins are exposed directly at their child terminals; only shared state/packet/supply nets use parent routing. This cut control-to-state extracted coupling from about12.7fF in the first compact-bus parent to0.15fF. The earlier v7 parent’s long blanket buses produced170mV sample-edge disturbance and up to262mV release error, despite a clean physical check; those results identify parent-route parasitics, not packet behavior.

With center state, ideal external phases, baseline1.697545V, and packet steps94mV positive /45mV negative, extracted TT27 transient gives+8.01mV/-8.10mV after packet release. The subsequent5ms drift is+0.04mV in both cases. This is a layout-specific nominal result. The previous sparse endpoint settings do not transfer: low-state handoff is+13.875mV and events net+18.356mV/+2.862mV; high-state handoff is-11.970mV and events net+7.810mV/-6.730mV. Endpoint hold drift is at most0.191mV. Thus the center map works on this routed parent, but beta dynamics, sample/drive baseline, and signed packet amplitudes still require per-range calibration. The endpoint run uses a staggered switch/source release after an initial simultaneous-edge run reached an ngspice timestep failure; the staggered transient completes.

Smaller routing experiments v12/v13 retain DRC/LVS/GDS readback but have not replaced v12 as the characterized candidate. Attempts to move the MIM near the drive switch (v14-v16) retain DRC/spacing failures and are debug-only. No full-float weight mapper, autonomous sequencer, range detector, original-checkpoint recurrence replay, PVT/noise/mismatch sweep, 25-actor service, or full-chip layout is qualified.

Evidence: `artifacts/analog_asic/layout/gf180_sc_state_packet_compact_v12/qualification.json`; center run `artifacts/analog_asic/results/gf180_sc_state_packet_compact_v12_center_recalibrated_5ms_v2.json`; endpoint run `artifacts/analog_asic/results/gf180_sc_state_packet_compact_v12_endpoints_staggered_5ms_v2.json`; extracted capacitance `artifacts/analog_asic/layout/gf180_sc_state_packet_compact_v12/gf180_sc_state_packet_compact_v12_cap.spice`. Earlier failed and superseded outputs remain preserved.


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

Reused connected64-state tile VDD trace: [{"window": "initialization_restore_and_signed_update", "start_s": 0.0, "end_s": 0.00023, "duration_s": 0.00023, "VDD_supply_energy_j": 8.597910612571494e-08, "mean_VDD_power_w": 0.0003738222005465867}, {"window": "five_ms_hold", "start_s": 0.00023, "end_s": 0.00523, "duration_s": 0.005, "VDD_supply_energy_j": 1.790225511877614e-06, "mean_VDD_power_w": 0.0003580451023755228}]. This includes external native command buffers sharing VDD and excludes independent analog/command ports. These are whole-fixture rail measurements, not a one-PLIF or one-membrane estimate. Older excludes_external_fixtures wording is corrected by direct bench inspection; source results remain preserved.


## Representative per-element consumption delivered — 2026-10-14

The article layout and representative consumption characterization are complete under the user's clarified scope. `artifacts/analog_asic/results/module_consumption_v1/consumption_summary.json` covers all22 required element/module families, plus native capacitor, sampled decision, bias/normalization kernels and the three shared categorical macro estimates. One physical PLIF core, one3T+MIM resident cell, signed injector, adaptation, inhibition, normalization, readout, access and controls are distinguished. Each transient row states its window and supply energy/power; detailed reports retain input-port accounting. Core beta/decision/reset windows are measurements of the whole core during those phases, not standalone leaf powers.

Coverage combines newly completed native transients, reused complete rail-current traces, native RMS DC/settled samples and explicitly labeled routed-library digital power estimates. Shared1024-state reader power is partition/leaf characterization, not a completed full connected-page power simulation. Bias/reference/phase-generator overhead outside the measured boundary remains excluded unless stated. No measured full-chip power, calibrated behavior or5ms full-population deadline is claimed. Do not sum overlapping modules or replicate shared-core cost per logical membrane. Further circuit optimization is optional.

### Representative consumption table

| Circuit / instance | Window | Mean VDD power (uW) | VDD energy (pJ) | Basis |
|---|---|---:|---:|---|
| single_resident_membrane_cell / Xcell | write | 0.000119681 | 0.000143617 | native transient, one physical instance |
| single_resident_membrane_cell / Xcell | read | 2.38202 | 3.33483 | native transient, one physical instance |
| single_resident_membrane_cell / Xcell | five_ms_hold | 1.61404e-07 | 0.000807018 | native transient, one physical instance |
| native_membrane_cap / Xbare | write | 0 | 0 | native transient, one physical instance |
| native_membrane_cap / Xbare | read | 0 | 0 | native transient, one physical instance |
| native_membrane_cap / Xbare | five_ms_hold | 0 | 0 | native transient, one physical instance |
| gf180_neuron_five_module_parent_v6 / Xparent_high | beta | 41.9078 | 125.724 | native transient, one physical instance |
| gf180_neuron_five_module_parent_v6 / Xparent_high | decision_and_reset | 42.6712 | 341.369 | native transient, one physical instance |
| gf180_neuron_five_module_parent_v6 / Xparent_high | one_initialized_update | 41.6034 | 1872.15 | native transient, one physical instance |
| gf180_neuron_five_module_parent_v6 / Xparent_high | five_ms_hold | 41.7109 | 208555 | native transient, one physical instance |
| gf180_signed_event_injection_v1 / Xinject_positive | pulse_and_recovery | 0.148447 | 0.890683 | native transient, one physical instance |
| gf180_signed_event_injection_v1 / Xinject_positive | five_ms_hold | 0.148638 | 743.191 | native transient, one physical instance |
| gf180_signed_event_injection_v1 / Xinject_negative | pulse_and_recovery | 0.148647 | 0.891883 | native transient, one physical instance |
| gf180_signed_event_injection_v1 / Xinject_negative | five_ms_hold | 0.148638 | 743.191 | native transient, one physical instance |
| gf180_signed_event_injection_v1 / Xinject_idle | pulse_and_recovery | 0.148638 | 0.89183 | native transient, one physical instance |
| gf180_signed_event_injection_v1 / Xinject_idle | five_ms_hold | 0.148638 | 743.191 | native transient, one physical instance |
| gf180_phase_inverter_fullroute / Xinv_10fF | four_truth_states | 3.48515 | 0.278812 | native transient, one physical instance |
| gf180_phase_inverter_fullroute / Xinv_10fF | settled_last_state | 1.1362e-05 | 1.02258e-07 | native transient, one physical instance |
| gf180_reset_select_and_fullroute / Xand_10fF | four_truth_states | 7.06079 | 0.564863 | native transient, one physical instance |
| gf180_reset_select_and_fullroute / Xand_10fF | settled_last_state | 3.49684e-05 | 3.14716e-07 | native transient, one physical instance |
| gf180_phase_inverter_fullroute / Xinv_100fF | four_truth_states | 15.8811 | 1.27049 | native transient, one physical instance |
| gf180_phase_inverter_fullroute / Xinv_100fF | settled_last_state | 1.1362e-05 | 1.02258e-07 | native transient, one physical instance |
| gf180_reset_select_and_fullroute / Xand_100fF | four_truth_states | 22.2846 | 1.78277 | native transient, one physical instance |
| gf180_reset_select_and_fullroute / Xand_100fF | settled_last_state | 0.0246917 | 0.000222225 | native transient, one physical instance |
| gf180_fixed_body_tg_quarter_shorttracks / Xfwd | two_level_transfers_and_release | -0.0522943 | -0.00522943 | native transient, one physical instance |
| gf180_fixed_body_tg_quarter_shorttracks / Xfwd | off_hold | 1.49226e-05 | 0.0746132 | native transient, one physical instance |
| gf180_fixed_body_tg_quarter_shorttracks / Xrev | two_level_transfers_and_release | -0.0525744 | -0.00525744 | native transient, one physical instance |
| gf180_fixed_body_tg_quarter_shorttracks / Xrev | off_hold | 1.48252e-05 | 0.0741259 | native transient, one physical instance |
| gf180_sampled_decision_hold_v2 / Xdecision_high | complete_trace | 0.000195156 | 1.18069 | native transient, one physical instance |
| gf180_sampled_decision_hold_v2 / Xdecision_low | complete_trace | 9.71259e-06 | 0.0587612 | native transient, one physical instance |
| gf180_guarded_weight_duration_parent_v2 / Xduration_small | armed_pulse_cycle | 12.7432 | 2574.13 | native transient, one physical instance |
| gf180_guarded_weight_duration_parent_v2 / Xduration_small | parked | 25.1031 | 753.093 | native transient, one physical instance |
| gf180_guarded_weight_duration_parent_v2 / Xduration_middle | armed_pulse_cycle | 12.9424 | 2614.37 | native transient, one physical instance |
| gf180_guarded_weight_duration_parent_v2 / Xduration_middle | parked | 25.1048 | 753.144 | native transient, one physical instance |
| gf180_guarded_weight_duration_parent_v2 / Xduration_large | armed_pulse_cycle | 13.1647 | 2659.27 | native transient, one physical instance |
| gf180_guarded_weight_duration_parent_v2 / Xduration_large | parked | 25.1052 | 753.157 | native transient, one physical instance |
| gf180_peer_inhibition_v1 / Xinhibit_no_trigger | complete_trace | 0.000218413 | 1.3214 | native transient, one physical instance |
| gf180_peer_inhibition_v1 / Xinhibit_no_trigger | five_ms_hold | 5.2121e-06 | 0.0260605 | native transient, one physical instance |
| gf180_peer_inhibition_v1 / Xinhibit_peer | complete_trace | 0.000310389 | 1.87785 | native transient, one physical instance |
| gf180_peer_inhibition_v1 / Xinhibit_peer | five_ms_hold | 7.00769e-06 | 0.0350385 | native transient, one physical instance |
| gf180_peer_inhibition_v1 / Xinhibit_own_spiker | complete_trace | 0.000219673 | 1.32902 | native transient, one physical instance |
| gf180_peer_inhibition_v1 / Xinhibit_own_spiker | five_ms_hold | 2.9711e-06 | 0.0148555 | native transient, one physical instance |
| gf180_candidate_penalty_subtractor_v2 / Xsubtract | input_sequence | 19.7207 | 591.622 | native transient, one physical instance |
| gf180_candidate_penalty_subtractor_v2 / Xsubtract | late_settled | 19.7731 | 39.5463 | native transient, one physical instance |
| gf180_resident_adaptation_expiry_v3 / Xresident | five_age_advances_two_spikes | 233.27 | 46654.1 | native transient, one physical instance |
| gf180_resident_adaptation_expiry_v3 / Xresident | late_settled | 215.733 | 2157.33 | native transient, one physical instance |
| gf180_adaptation_shared_state_io_v6 / Xio | restore_capture_sequence | 682.952 | 75124.7 | native transient, one physical instance |
| gf180_adaptation_shared_state_io_v6 / Xio | late_settled | 682.759 | 6827.59 | native transient, one physical instance |
| gf180_class_current_shared_io_v1 / Xio | restore_capture_sequence | 401.455 | 72262 | native transient, one physical instance |
| gf180_class_current_shared_io_v1 / Xio | late_settled | 401.322 | 4013.22 | native transient, one physical instance |
| gf180_six_class_readout_v3 / Xbank_all_negative | ten_accumulations_and_readout | 122.306 | 6.26205e+06 | native transient, one physical instance |
| gf180_six_class_readout_v3 / Xbank_all_negative | readout_evaluation | 330.599 | 33059.9 | native transient, one physical instance |
| gf180_six_class_readout_v3 / Xbank_all_negative | parked_after_readout | 121.776 | 9742.11 | native transient, one physical instance |
| gf180_event_phase_sequencer_v1 / Xseq_idle | one_request_cycle | 24.795 | 198.36 | native transient, one physical instance |
| gf180_event_phase_sequencer_v1 / Xseq_one_event_busy_request | one_request_cycle | 36.5864 | 292.691 | native transient, one physical instance |
| gf180_bin_commit_controller_v2 / Xseq_wait_then_complete | one_bin_phase_sequence | 81.0719 | 1135.01 | native transient, one physical instance |
| gf180_pmos_bias_reference_fullroute_v2 / Xreference | settled_bias | 3.3 | 13.2 | native transient, one physical instance |
| gf180_energy_square_kernel_v1 / Xkernel | three_input_levels | 26.8086 | 536.17 | native transient, one physical instance |
| gf180_energy_square_kernel_v1 / Xkernel | positive_plateau | 26.8082 | 80.4247 | native transient, one physical instance |
| gf180_bank_pair_shared_reader_v1 / one physical shared module/partition | existing_completed_nominal_trace | 23.9134 | 1673.94 | reused native transient supply current |
| gf180_adaptation_sum64_threshold_v2 / one physical shared module/partition | existing_completed_nominal_trace | 3798.54 | 303883 | reused native transient supply current |
| gf180_adaptation_sum128_threshold_v2 / one physical shared module/partition | existing_completed_nominal_trace | 7579.26 | 303171 | reused native transient supply current |
| gf180_underplate_biased_bank8x8_v1 / one physical shared module/partition | existing_completed_nominal_trace | 0.451833 | 2349.53 | reused native transient supply current |
| shared_reader_page1024_v1 / one physical shared module/partition | existing_completed_nominal_trace | 28.2194 | 1128.78 | reused native transient supply current |
| gf180_decoded_shared_compute_tile_v2 / one physical shared module/partition | existing_completed_nominal_trace | 334.905 | 77028.2 | reused native transient supply current |
| gf180_formatted_energy64_v3 / one64-channel formatted RMS module | zero | 6180.41 | — | native hierarchy DC supply power |
| gf180_formatted_energy64_v3 / one64-channel formatted RMS module | half | 6235.06 | — | native hierarchy DC supply power |
| gf180_formatted_energy64_v3 / one64-channel formatted RMS module | all | 6290.38 | — | native hierarchy DC supply power |
| gf180_energy_mean_root128_v1 / one128-channel unformatted RMS reducer | zero | 3453.13 | — | native transient settled supply sample |
| gf180_energy_mean_root128_v1 / one128-channel unformatted RMS reducer | half_active | 3563.07 | — | native transient settled supply sample |
| gf180_energy_mean_root128_v1 / one128-channel unformatted RMS reducer | all_active | 3674.35 | — | native transient settled supply sample |
| gf180_analog_full25_packet_fabric_v1 / one routed shared categorical macro | ORFS default activity estimate | 5258.46 | — | routed OpenROAD/OpenSTA library power estimate; not transistor transient |
| gf180_analog_full25_actor_ingress_v2 / one routed shared categorical macro | ORFS default activity estimate | 75950.2 | — | routed OpenROAD/OpenSTA library power estimate; not transistor transient |
| gf180_analog_full25_accumulation_dispatch_v1 / one routed shared categorical macro | ORFS default activity estimate | 216102 | — | routed OpenROAD/OpenSTA library power estimate; not transistor transient |

The membrane cell write/read total positive terminal imports are reported in the JSON in addition to VDD, which alone omits DATA/clock energy. Very small hold currents are numerical/model-dependent. Digital library estimates retain their original activity assumptions.


## Layout images delivered — 2026-10-14

`artifacts/analog_asic/assembly/full25_native_controls_v31/layout_images_v2/` contains300dpi PNG exports: full_layout_overview.png (3200x2700), plif_core_detail.png (2800x1050), and membrane_bank_detail.png (2800x1800). The overview renders actual finalV31 GDS spatial hierarchy and parent polygons, simplifying small repeated instance extents to avoid flattening millions of cells. Its physical scale describes the spacious research atlas, not compact die area. The PLIF view is matched by native geometry signature within the actual assembledGDS; the membrane bank view is from its qualified native component-sourceGDS, not an independently matched assembled-cell crop. Source/layout SHA matches the final independent readback; image source scopes and hashes are in render_manifest.json. All three renders visually inspected. Images do not establish fabrication signoff, compactness or circuit accuracy. Rendering used host Python/Pillow; no new Docker images or containers.


2026-10-14 SVG export delivered: full_layout_overview.svg, membrane_bank_detail.svg and plif_core_detail.svg are beside the PNGs in `artifacts/analog_asic/assembly/full25_native_controls_v31/layout_images_v2/`. True vector GDS paths/reusable hierarchy; no embedded raster images. The full-layout overview retains fixed hierarchy simplification and does not reveal omitted transistor geometry on zoom. Component source scopes match the PNG manifest. XML parsed and all three SVG previews visually inspected. Provenance/file hashes: svg_manifest.json. Sizes:16.55MB overview,0.36MB membrane bank,0.16MB PLIF.


## ASIC artifact reorganization — 2026-10-14

Canonical article package: `artifacts/analog_asic/` (start at index.html). Final GDS is `layout/EventSpikeSeg140k_GF180_Analog.gds`; PNG/SVG figures are together in images/; current consumption data is consumption/summary.json. Original manifests/source/results are preserved unchanged under evidence/, components/, model_reference/support locations. The current path locator is `artifacts/asic_artifact_index.json`.

Digital documentation-only snapshots are `artifacts/ASIC/final/` and `artifacts/ASIC_XL/final/`; neither claims a completed digital full-chip layout. Last exports, hierarchy inventory, completed block views and final reports are retained; digital jobs remain paused.

All superseded attempts and build environments moved to `bin/asic_cleanup_2026-10-14_20261014T145109Z/`, including related digital OpenROAD history. No files deleted. cleanup_plan.json inventories every original file; integrity_audit.json accounts for all64,814 originals and verifies SHA256 of all2,779 retained files. restore_artifacts.ps1 can restore original artifact trees; pre-cleanup docs and .gitignore are backed up in the same bin. User review of this bin is pending; do not delete it without explicit instruction. Historical report/script paths are original provenance; resolve with the locator or restore dependencies before replay. New experiments belong outside final/.
