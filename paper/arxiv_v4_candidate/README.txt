HeteroSpec — source-reconciled v4, cross-reviewed refinement
===========================================================
Title: Phase-Scoped Query Layouts for Reference-Preserving Speculative Decoding
Author: Chengzhan Li
Review date: 2026-10-21

This package is the full v3-source-reconciled manuscript, not the obsolete
short PR138 reconstruction. The current PDF has 23 pages: 13 article/reference
pages and 10 supplementary pages, with 10 editable TikZ/PGFPlots figures.
All 25 original bibliography entries, six follow-up experiment references,
original figure data, report-level inputs and scientific failure records remain.
Selected original figure styling/labels were refined; no blanket claim of
byte-identical figure source is made for this second editorial round.

Build (Python 3.11+, pdfLaTeX, BibTeX, elsarticle, TikZ/PGFPlots):
    python -B scripts/build.py
Build using the included bibliography without BibTeX:
    python -B scripts/build.py --cached-bbl
Report-only checks, without LaTeX, network or inference:
    python -B anc/check.py
    cd anc
    python -B -m unittest test_release test_closure test_refinement -v
Regenerate follow-up figures and service tables:
    python -B scripts/generate_followup_figures.py
Descriptive review sensitivity and palette audit (not new inference):
    python -B scripts/review_audit.py

This refinement passed 484 reported-value/source checks and 31 regression/
mutation tests. Every final PDF page was rendered and inspected; no overfull
boxes, unresolved references/citations or missing glyphs remained. All fonts
are embedded. Review records describe the inspected artifact, not later edits.
The final source package is also rebuilt in a clean directory.

Scientific interpretation:
- Original CUDA k3 resident-request gains remain separate from new k1 service
  ratios: inputs, interfaces, runtime policies and cost windows differ.
- RTX QB/dual-PQ=0.989284 remains unresolved under 5.208% A/A imbalance.
  QB/R=0.582325 describes 41.8% lower service time, not a QB-specific speedup;
  dual-PQ/R already equals 0.588633. Figure 7 now displays both controls.
- B570 QB/dual-PQ=0.995144 and QB/R=2.619763 are a separate fixed panel.
  A draft-prefill follow-up is numerically qualified but lacks a complete
  timing result in the reviewed source. No optimized software ceiling follows.
- Full raw logits/runtime archives remain separately held. This package gives
  exact saved report data and CPU reconstruction, not independent native replay.

The earlier Humanizer 3.1.0 editing record remains under anc/review/.
The current round used four public K-Dense workflows: peer-review, scientific-
critical-thinking, scholar-evaluation and scientific-visualization. These are
four perspectives applied by one assistant, not four independent reviewers,
external certification or an editorial decision. Workflow versions, findings,
accepted/rejected remedies and journal-strategy uncertainty are recorded in
anc/review_round2/REVIEW.md. No proprietary manuscript was sent to an external
reviewing service. No new model execution, arXiv or journal submission occurred.

Current QA: anc/review_round2/QA_FINAL.json.
Historical first-round QA: anc/review/ (preserved, not the current certificate).
Source lineage: SOURCE_RECONCILIATION.md and CLAIM_EVIDENCE.md.
The author-supplied v3 ZIP is the editing baseline; its byte identity with the
arXiv-server source archive was not independently authenticated.
