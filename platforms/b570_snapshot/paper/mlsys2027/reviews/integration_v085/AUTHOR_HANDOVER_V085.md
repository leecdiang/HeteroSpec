# Author handover — v0.8.5

The current build and separate evidence index are ready for author review.
Consult `evidence/FINAL_ARTIFACT_MANIFEST_V085.json` for exact file lengths,
SHA256, source dependency digest and content commit; `evidence/DELIVERY_V085.md`
records the subsequent delivery commit role and Draft PR. Relative paths here
are from `paper/mlsys2027/` unless a repository path is given explicitly.

Review `manuscript/output/manuscript-v0.8.5.pdf` (10 body + 2 references),
`appendix-v0.8.5.pdf` (10 pages), the anonymous evidence index, and the exact
Draft PR together. The source ZIP is an editable/rebuildable source artifact;
the evidence index supplies arrays, fork records and condition times. The
existing separate H2 capsule remains at repository path
`artifacts/rtx_independent_proposal_replay_v2/anonymous-a5919b59342ecc68bd5f57d3c2b192edf62933b2645924381c3765dd50beb369.tar.gz`,
SHA256 `a5919b59342ecc68bd5f57d3c2b192edf62933b2645924381c3765dd50beb369`.
Its original-to-derived hash/ordinal mapping is not original-time attestation.
The `hardware-only` PDF is an internal section-removal/reference proof only.

Use the current manuscript README's tested single build entry and `make check`.
The final source ZIP was independently extracted, manifest-checked, and built
with plain latexmk; all pages' text and page counts match. Delivered PDF bytes
are the checked fresh-build bytes. All 32 delivered document pages were
visually inspected (12 main, 10 appendix, 10 proof); details, PNG digests and
repair history are in `evidence/VISUAL_QA_V085.md`.

Current scientific/numerical checks, retained complete archive replays,
source ZIP rebuild, and PDF/font/reference/anonymity checks were rerun. Frozen
B570's original complete verifier fails on POSIX Windows-basename parsing;
the disclosed Path.name-only adapter passes without changing source/evidence
or scientific assertions. That original failure remains a separate result.
358H runtime raw traces are UNAVAILABLE; compact pinned diagnostics are not
raw replay. The prior v084 sequence ZIP is UNAVAILABLE in this checkout;
original 72 sealed arrays were kept and exported element-identically.
No unfinished document build or mandatory validation remains.

Scientific scope remains narrow: no uniquely localized operation, numerical
implementation independence, adversarial OS isolation, untested transfer,
qualified batched matched timing, uninstrumented deployment speed, functional
pass@k, persistence savings or runtime energy follows. New RTX cost is slower,
H2 reference qualification fails, B570 immediate decisions are unchanged,
M4 Guard is slower than fixed Always, and 358H runtime stopped at qualification.

Next: initiate a separate independent submission-level review using the exact
v0.8.5 PDFs, evidence index/capsule and Draft PR. Review outcomes are not
predicted here. Any publication or submission upload is a separate author
step; no automatic merge, tag, release, OpenReview submission or messaging
is part of this integration delivery.
