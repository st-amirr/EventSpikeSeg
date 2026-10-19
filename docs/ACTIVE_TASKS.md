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

## Microelectronics Journal adaptation - 2026-10-18

Final delivery check (18 October 2026): rebuilt and visually reviewed the 10-page manuscript and 5-page reusable figures; corrected GDS-to-PDF coordinate precision. Editable source bundle and submission_manifest.json are in article/submission/. Abstract, highlight lengths and citation keys checked; no LaTeX warnings. Author declarations/data deposit remain pending.

Completed the requested journal adaptation and editorial reviewer pass: Elsevier template, <=250-word abstract, seven keywords, four highlights, ordered numbered references, six separate artwork files, vector architecture/overview/waveform figures, and declaration sections. All detailed 140k model content and numerical evidence are retained. Authors: Amir Mohammad Khadem Hosseini (corresponding; academic email and supplied ORCID) and Sattar Mirzakuchaki (email and ORCID). Both use the stated IUST Electrical Engineering affiliation; confirm the full postal address and work affiliation before submission.

Remaining author actions: funding/competing interests, contributor roles and co-author approval, optional acknowledgements, final review of AI disclosure, and public data repository/DOI or justified sharing restriction. These are submission requirements, not new circuit/layout tasks. No submission, new simulation or GDS modification was performed.

## Completed article figures and evidence review - 2026-10-15

- Corrected original-style architecture promoted to Figure 1; historical duplicate removed.
- Higher-contrast GDS-derived overview added to the main article; native device/bank figures regenerated without changing GDS.
- Saved signed-update/5-ms-hold waveforms plotted; nominal conditions, state breakdown, result-method counts and final-bank area calculation added.
- Detailed 140k topology/training/search history preserved. Article: 9 pages; reusable figure document: 5 pages.
- Author affiliation/contact and acknowledgments remain author-supplied. Unavailable mismatch, full-chip power/timing and hardware mIoU data remain explicit limitations; they are not fabricated or new layout-completion gates.

## ASIC source cleanup — 2026-10-15

`asic/` is retained hardware source/build input; final results remain in `artifacts/analog_asic/`. Archived 38 superseded/provisional/metadata files (171,273 bytes) to `bin/asic_source_cleanup_20261015T115233Z`; 185 original source/configuration files remain. Final GF180 control roots and retained digital tool/test dependencies are preserved; the older parallel scatter source stays because the pw128 wrapper uses it. All 223 original hashes were checked after the move; the README was then refreshed with its original in before_changes.zip. Bin includes inventory, restore script and audit; artifact resolver handles archived original paths. No tests/simulations, permanent deletion, staging or commit.

## Wire-hidden device views and full model figures — 2026-10-15

The user requested regeneration with invisible wiring in PLIF/injector panels and visible wiring in the native 64-state bank. KLayout now hides metal1–5 and via1–4 for panels (a)/(c), with enlarged device windows; bank panel (b) is unchanged. Source GDS files are not modified. Renderer: scripts/render_article_gds_devices.py; source hashes, windows and hidden layer pairs: article/figures/gds_device_manifest.json. These are device-layer illustrations, not complete connectivity views. Full current 140k architecture is restored to the main model section (page 3) as an editable vector TikZ diagram. Original 140k_v4.png is preserved in the appendix (page 8), explicitly identified as the earlier detail32/selector96/spike-count topology. Current model detail8/fusion40-to-16/continuous16-to-6 remains authoritative. Both appear in Blocks_figures.tex. Article: 8 pages; reusable figures: 5 pages; compiled and visually reviewed. No circuit changes or new simulations.

## Model detail preservation and section figures — 2026-10-15

The user requested preservation of the actual 140k model detail. The article now restores the architecture-search history, residual-block diagram, chronological training/loss schedule, XL/digital background, and adds a source-checked per-stage inventory (25 actors, 30,976,000 membranes). ASIC implementation remains the main focus. Panels (a) and (c) show original-coordinate GDS device sections instead of full sparse parent wiring; full views remain available. Article and reusable figure PDFs compile to 7 and 3 pages and were visually inspected. No physical rerouting or circuit simulation was performed.

# Active tasks

Updated2026-10-14. Article layout, representative consumption and PNG/SVG views are delivered.

## Current deliverables

- Analog article package: `artifacts/analog_asic/index.html`.
- Final hierarchical GDS: `artifacts/analog_asic/layout/EventSpikeSeg140k_GF180_Analog.gds` (537,103,416bytes; SHA256fb28eeb6bbc8901ad8594dcd4b5cc14450b7cae438bd5f239096c587f96d1d92).
- Figures: `artifacts/analog_asic/images/`, including the three true-vectorSVGs and PNGs.
- Consumption: `artifacts/analog_asic/consumption/summary.json`,22 required families/74 rows. Per-instance transients, reused rail traces, RMS DC samples and digital-library estimates are explicitly distinguished.
- Digital140k andXL documentation: `artifacts/ASIC/final/index.html` and `artifacts/ASIC_XL/final/index.html`. No digital full-chip completion claimed.

## Scope and limitations

Original epoch58 full-float analog topology and54,630,400 state identities including30,976,000 membranes remain preserved. External analog/control interfaces are documented. The full1024-state page lacks complete connected power/transient evidence; partition and leaf consumption are supplied. No compact die, calibrated accuracy, full-chip power, globalRC/IR/EM, manufacture or full-population5ms acceptance is claimed. Further circuit optimization is optional.

## Cleanup completed; user bin review pending

Review bin: `bin/asic_cleanup_2026-10-14_20261014T145109Z/`. All64,814 original files accounted for; retained originals are SHA256-verified. No deletions performed. Original evidence bytes/hashes are preserved; `artifacts/asic_artifact_index.json` maps old paths to retained or binned files. restore_artifacts.ps1 and the move inventory are in the bin. Do not delete the bin without explicit user instruction. Archive the seven docs before future edits. No new simulations or Docker images were started during cleanup.

## Documentation and article consolidation — 2026-10-15

Main `docs/` is the only canonical documentation directory. The user moved the analog package directly to `artifacts/analog_asic/`; the nested `final/` path is retired. Identical packaged docs are preserved in `bin/article_reorganization_20261014T203110Z`. Script cleanup retained 201 scripts and archived 2,074 attempt/backup/cache files in `bin/scripts_cleanup_20261014T163508Z`; all original hashes verified. Article and GDS figures are updated and compiled. `article/article.pdf` is the ASIC-focused manuscript; `article/Blocks_figures.tex` and `article/figures/Blocks_figures.pdf` contain reusable physical-layout figures. KLayout produced native bank/injector GDS views and a PLIF cell directly from the delivered full GDS. No new circuit simulation was needed.
