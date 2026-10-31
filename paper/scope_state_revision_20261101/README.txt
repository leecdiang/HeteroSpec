Phase-Scoped Query Layouts for Reference-Preserving Speculative Decoding
Chengzhan Li — author-review revision, 2026-11-01

This manuscript starts from the latest PR145 P0 scientific text at
 a97f97925e55ce29d8ce06a208c58b8e52664ad4
and incorporates the completed RTX three-date and B570 producer-state studies:
 RTX: 29511ed91eb9f3d9773cfdda53e3554b0f4ad08b
 B570: 022babfabb3d1b6f4f2a2830dca04b2654d193f9
No native experiment, remote merge, arXiv update or journal submission was run here.

Build the complete article plus supplementary material:
    python -B scripts/build.py
Use --cached-bbl to build with the supplied, matching bibliography. Required:
Python 3.11+, pdfLaTeX, BibTeX, elsarticle, TikZ/PGFPlots and the packages in
preamble.tex. No shell escape or network call is needed for the document.

Verify reported data and generated material:
    python -B anc/check.py
    python -B scripts/analyze_final_revision.py --check
    cd anc
    python -B -m unittest test_release test_closure test_refinement test_round3 test_major_revision test_native_followup test_final_revision -v

To regenerate the final-study tables and two figures:
    python -B scripts/analyze_final_revision.py

The final study's RTX CSV is an explicit projection of twelve reported session
log vectors, not a raw-request table. Its date/pooled algebra is independently
reconstructed. B570's two CSVs match the complete fixed Git blobs byte for byte.
The original E2 CSV supplies 1,620 request rows, from which 216 local-arm quartets
are independently reconstructed. These checks are distinct from native endpoint,
full-logit and archive audits performed by the source hosts.

Larger P0 raw-response projections and native-delivery receipts are not duplicated
in this publication bundle. Their immutable access entries remain in
REPRODUCTION_ACCESS.md. The core P0 argument, original equations, adverse outcomes
and complete scientific tables are retained. Older ancillary history remains
historical and is not the current release status.

TeX input files are under sections/, supplement/, figures/ and tables/; no TeX
compilation dependency is inside anc/. main.tex and the supplied main.bbl compile
without anc/. That folder provides reported data, checks and scientific history.

This is an author-review manuscript. Current PDF hashes, tests and page-review
records accompany the separately delivered review package. Private critique,
reviewer-development notes and acceptance estimates are not publication files.

VISUAL REVIEW — 2026-11-01
Figure 2 now displays the three-date scope interaction in a separate panel;
Figure 6 pairs all 48 original reference cells with the two fixed-R cases.
The on-figure range is an observed date range, not a confidence interval.
The complete numerical reconstruction is unchanged. The generated DERIVED
summary omits duplicate source rows/check-name lists; those remain reproducible
from the supplied CSVs and checker. The static check receipt is compact; the
full run output is retained in the separate review archive.
Run the complete 71-test suite with scripts/build.py --cached-bbl, or add
`test_visual_revision` to the older explicit unittest command above.
Repository integration uses a new paper/scope_state_revision_20261101 directory
and preserves all older manuscript and experimental directories.
