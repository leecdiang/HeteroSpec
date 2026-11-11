Phase-Scoped Query Layouts for Reference-Preserving Speculative Decoding
Chengzhan Li — approved targeted author revision, 2026-11-01

Editing baseline: PR153 head 28a44f6d5755ff718e23609d73666f31b14a386c,
exact manuscript subtree 9a0d1aa04e9da302ff05d1ce31d0224b97afcdb0.
RTX evidence: 29511ed91eb9f3d9773cfdda53e3554b0f4ad08b.
B570 evidence: 022babfabb3d1b6f4f2a2830dca04b2654d193f9.
All original measurements, estimators, failure dispositions and figure sources
remain unchanged. New material is post-hoc algebra and finite-matrix reasoning,
not additional experiments or a general correctness theorem.

Build article plus supplement (Python 3.11+, pdfLaTeX/BibTeX, elsarticle,
TikZ/PGFPlots and the packages listed in preamble.tex):
    python -B scripts/build.py
Or use the supplied matching bibliography:
    python -B scripts/build.py --cached-bbl

Offline reported-data and targeted checks:
    python -B anc/check.py
    python -B scripts/analyze_final_revision.py --check
    python -B scripts/analyze_targeted_revision.py --check
Full standard-library tests, from anc/:
    python -B -m unittest test_release test_closure test_refinement test_round3 test_major_revision test_native_followup test_final_revision test_visual_revision test_targeted_revision -v

Regenerate the added interpretation tables and compact JSON:
    python -B scripts/analyze_targeted_revision.py
The four input hashes are pinned; old records are not rewritten. RTX data are
reported session logs, not native raw request records. B570 CSVs preserve the
original exact Git blobs. This is separate from the source-host raw-logit audits.

Targeted content:
- Separate local repair (PQ/GS) from QB's layout increment (QB/PQ).
- Distinguish fixed-panel qualification and empirical cost comparison from an
  online reference guarantee; no online selection service is implemented here.
- Explain the two producer/consumer qualification counterexamples and preserve
  the complete eight-input denominator and the combined KV+initial-logit scope.
- Compare Vosti and LLM-42 at their actual guarantee levels.

The 12 existing figures retain the reviewed visual grammar and numerical data.
The complete article compiles without anc/ because TeX tables and figures live
outside it. The supplementary source contains reproducible reported data and
scientific history, not confidential internal review memos. Review/QA receipts
are supplied separately. REPRODUCTION_ACCESS.md lists native materials and the
remaining authentication/dependency requirements; independent account/host
replication has not been performed by this revision.

Humanizer 3.1.0 and anti-defensive-writing principles were applied after content
revision; numeric, math and reference preservation was checked during the prose
pass. Prior adverse evidence and the AI-use declaration remain. Author approval,
formal peer review and submission are distinct from local checks. No native run,
PR merge, arXiv update or journal submission is performed by this source package.
