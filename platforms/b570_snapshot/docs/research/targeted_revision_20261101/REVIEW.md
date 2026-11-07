# Approved targeted manuscript revision — 2026-11-01

Author-approved follow-up to PR153, baseline `28a44f6d5755ff718e23609d73666f31b14a386c`. The current manuscript path stays `paper/scope_state_revision_20261101/`; no experimental files or prior paper directories are changed. No native model execution, PR merge, arXiv update or journal submission.

## Review and applied remedies

Eight lenses were applied by the same assistant: method/deployment contract, statistics, baseline economics, state/causal interpretation, closest work, mathematical/program consistency, typography and academic English. These are not eight independent agents, external peer reviews or an editor's decision.

1. **Offline versus online qualification.** Section 2.2 defines the finite experimental comparison set. Section 8's argmin is an empirical objective over already-qualified candidates, not a new-request router or online correctness guarantee. Reference generation precedes timing; per-campaign in-window checks are still charged. Future-request guarantees need an additional mechanism or adequate proof/generalization assumption.
2. **Scope versus layout.** Add the exact common-weight identity Gamma=(D_PQ/D_GS)(D_QB/D_PQ). Qwen factors are 1.344110 and 1.059343; Smol factors are 1.176962 and 0.999494. Smol's target-only and speculative QB/PQ costs fall by 6.579% and 6.532%, so lower local cost need not change the draft decision. These are post-hoc arithmetic descriptions, not new significance/equivalence tests or kernel-time attribution.
3. **Three baselines.** R defines preserved behavior, same-layout target-only defines draft opportunity cost, and PQ identifies the QB increment. Same-panel Smol C_QB/R=0.694295 but C_QB/M_QB=1.242426. No mixing with the earlier 1.007007 panel.
4. **Relational eligibility.** The two fixed-R B570 submatrices [[1,0],[1,1]] cannot be represented exactly by independent producer/consumer binary pass labels. Enumerate all16 assignments. This does not rule out relational modular verification. Preserve all48 cells,39 strict-R matches,16 local pairs and four jointly divergent local pairs; the latter is not a population failure rate. The intervention is complete KV plus initial logits in the validated clean receiver.
5. **Strong related work.** Add Vosti to the closest-work table with its canonical-KV engine invariant and selected relational kernel contracts. State that LLM-42 replaces decode KV with verified KV on successful acceptance as well as rollback. No common-contract external-system speed ranking is claimed.
6. **Mathematical wording.** A review found argmin described as a cost; it now correctly names a candidate with minimum observed cost. All96 original labels and13 original display-math environments remain. Original scientific reconstruction fields are unchanged.
7. **Figures and layout.** All12 reviewed figure sources remain byte-identical. Add two compact generated appendix tables and refine one figure caption. Shorten section8's long heading. Main article/references remain15 pages; supplement becomes17, total32. Do not shrink body type or remove counterexamples to force31 pages.
8. **Humanizer and anti-defensive prose.** After content revision,16 targeted English edits remove repeated staging and clarify agents/actions. Numeric multisets, math payloads and citation/label/input sequences are preserved in that prose pass. Relevant failures, scope limits and the AI-use declaration remain. No AI-detector/authorship claim.

## Validation performed

- 53 pre-existing CSV/JSON report inputs or derived inputs unchanged; references.bib and all12 figure sources unchanged.
- 1,680 report/source checks and86 analysis/regression tests pass (15 new tests). Separate original runtime contract suite:12 tests pass.
- Added reconstruction contains64 internal consistency checks; these are not independent experiments or a merit score.
- All32 final pages rendered/inspected; all fonts embedded; no blocking overflow, missing glyph or undefined citation/reference.
- Actual delivered source ZIP extracted into a new directory and built with all primary tests. PDF bytes match. A separate build with the entire anc directory removed also matches.
- PDF SHA256 `59f0da87153cbb00fc4aea2e1a39a9abf43e9aed7baade8e0d2f9b6dc2cd76ee`,420585 bytes.
- Full source diff, preservation inventory, exact language edits, full logs and all rendered pages are in the author QA ZIP, not in the publication source bundle.

The first external build command timed out; its logs are retained. A subsequent content build exposed a1.8984pt vertical overflow, removed by using compact pooled appendix tables. These are manuscript-build recoveries, not experimental retries. The final actual-ZIP/no-anc builds passed from fresh output directories.

## Workflow and verification sources

Humanizer3.1.0, blob `19fc634208e8cc6ae55d4ff287152583216fd244`; anti-defensive-writing-en, blob `87a163642daa5674a7fed82eb9112ae703ee0e73`; peer-review2.4 and ethical review guidance. Authorial assistance is not journal-assigned confidential external reviewing. Contribution-first structure was used without concealing material negative evidence.

Primary related-work text rechecked on2026-11-01:
- https://arxiv.org/html/2609.38981v1
- https://arxiv.org/html/2601.17768v2

Independent-account material access, second-machine native replay and full raw-logit authentication were not performed here. The author must arrange reviewer access and complete final scientific/personal-declaration approval. No acceptance-probability increase is inferred from editing or algebra alone.
