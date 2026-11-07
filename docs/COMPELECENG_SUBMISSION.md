## Model forward simulation added — 2026-11-07 (current)

The article now reports the completed detailed per-pulse SPICE-calibrated behavioral forward pass: one 440×640 record, ten bins, all 25 actors, 24.2625% mIoU versus 26.2210% for its matching PyTorch reference. This is not the full 234-record validation score or direct transistor-level network inference. External encoding/decoding remains ideal; assumed storage noise is 1 mV RMS. Calibration has a 3 mV tested-history working tolerance, counted extrapolations and failed stricter source checks. A separate 5 fF bank has passing retained DRC/LVS/readback evidence; the original whole-model GDS is unchanged.

Supplementary Material S3 is included under Model_Forward_Simulation/ in article/supplementary.zip. Canonical result: artifacts/analog_asic/evidence/forward_simulation/result.json. Matching baseline: artifacts/ASIC/reports/forward_simulation/. Older statements that 5 fF is analytical-only or no network behavioral simulation exists are superseded by this entry.

# Computers & Electrical Engineering submission audit - 2026-11-03

Source: user-supplied 19-page saved ScienceDirect Guide for Authors, visually read because PDF text encoding is broken. Relevant guide pages: 2, 4-5, 8-14. These findings supersede earlier inaccessible-guide and anonymization notes.

## Review and files

- Single-anonymized review (p. 2). Author names need not be hidden; the guide says all authors must be listed in the manuscript (p. 4). `article/article.pdf` and `.tex` now match the author-bearing master `article.pdf` and `.tex`; earlier author-separated copies are preserved in artifacts/article_work/guide_audit. Repository links remain.
- Upload article.pdf as Manuscript, title_page.pdf as Title page with author details, cover_letter.pdf as Cover letter. The live portal explicitly requests PDF for initial LaTeX submissions and sources at revision. Guide p. 8 requires editable sources upon submission or revision; Article.zip retains those sources.
- Highlights are REQUIRED, not optional (p. 9): upload highlights.txt separately. Existing five bullets satisfy 3-5 bullets and <=85 characters including spaces.
- Abstract <=250 words and 1-7 keywords (p. 9); existing abstract and six keywords satisfy these limits.
- Graphical abstract encouraged, not required (p. 9).
- Supply layout AND simulation supplements at initial submission, with captions (pp. 11-12). Supplementary.zip contains separate files, not a combined layout PDF.
- The six-page limit on p. 2 applies to technical communications, not a stated limit on original research articles.
- No printed-ORCID requirement found in the title-page section.

## Remaining mandatory requirement

Research data: Option C requires repository deposition and citation/link, or a factual explanation if sharing is impossible (p. 12). Public deposition of generated evidence is not established. The source GitHub repository and DSEC input-data links do not establish a generated-data deposit. Final author approval and exclusive submission must also be confirmed by the authors.

Biographies, separate photographs, full institutional postal address, caption disclosures and separate current artwork have now been prepared and checked.

## Guide/portal differences

- Declaration tool/Word upload: guide p. 4 requests completion and Word output even for no interests; live portal explicitly permits a no-interest checkbox instead. The supplied checkbox meets that portal alternative. Complete the publisher tool as well if the portal later requests its document; do not represent a locally generated statement as tool output.
- Acknowledgements: guide p. 13 says put actual acknowledgements in the end matter, not title page; portal requests them on title page. Current title page says None, and no acknowledgements were supplied, so no substantive acknowledgement is misplaced.
- Source format: retain editable LaTeX package, while following the live portal's PDF-only initial manuscript instruction.

Prepared files are not certified fully compliant until the outstanding items above are resolved. No submission or upload performed. Scientific results, layout and simulations are unchanged.

## Completed preparation - 2026-11-03

Biographies: article/author_biographies.docx (67 and 63 words), rendered through installed Word and visually checked. Photographs supplied by author: article/author_khadem_hosseini.jpg and article/author_mirzakuchaki.png (updated higher-resolution source). Title page and manuscript use the published institutional postal address. All six current figure PDFs regenerated from current manuscript bodies; main and supplementary layout caption disclosures added. Article.zip rebuilt. Main manuscript is 27 pages.

Upload article.pdf, title_page.pdf, cover_letter.pdf, highlights.txt, author_biographies.docx, the two separate portraits, and the layout/simulation supplements. Supply individual Figure_1.pdf through Figure_6.pdf as artwork when requested. Keep Article.zip for editable source submission/revision per portal instructions.

Outstanding: public deposition of generated research data. GitHub tree did not establish artifact deposition. supplementary.zip is prepared locally; repository destination/licensing and actual upload remain pending. Do not invent a DOI or state that deposition is complete. Author final review, co-author approval and exclusive-submission confirmation also remain.

## Mandatory-only scope - current instruction

Prepare only journal/portal requirements. No graphical abstract, optional co-submission, extra biography PDF or optional publication package is requested. The guide's Vitae section requests editable biographies (<=100 words each) and separate photographs; retain author_biographies.docx and both portraits. A separate biography file is a packaging choice for fulfilling the editable-biography requirement, not a separately mandated layout. Upload it under Biography if that category exists; do not create additional versions.

Required initial upload set: article.pdf; title_page.pdf; cover_letter.pdf; highlights.txt; editable biographies and separate portraits; current figure artwork; referenced layout/simulation supplements. Use the portal's no-interest confirmation alternative. Keep editable LaTeX sources for the revision stage as directed by the portal.

Duplicate biography TXT and optional deposit metadata moved recoverably to bin/optional_submission_files_20261103. Public data deposition remains a mandatory unresolved requirement; this move does not waive it.

## Reverted unnecessary packaging

The duplicate manuscript.tex/manuscript.pdf pair was archived recoverably in bin/unnecessary_submission_duplicates_20261103. Use article.pdf for the Manuscript upload and article.tex as its sole editable master. The earlier author-removal change is already reverted because review is single-anonymized. Required separate title page, cover letter, highlights, editable biographies, photographs, artwork and referenced supplements remain. No optional graphical abstract or co-submission was added. Scientific content and required disclosures were retained.
