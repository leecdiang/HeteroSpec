# Submission-level review and coordinated revision v0.5

## Source and delivery identity

- Source: PR #27, `paper/mlsys2027-runtime-integration-v0.4`, HEAD `b326ff7f20d9bac5afff6f53a6e9d9d8a7aaa7ae`.
- PR #27 was already merged at discovery. Its head had not changed from the handoff. Original base: `bbf0c555cc50242f85c086eac342c9deb5c2e945`.
- Main at discovery/recheck: `7b22e0e7cbb3915597109951b6a709c1a92e5627`; its tree equals source HEAD (`05664f24437f169680240c1c263df2b92c8e2066`).
- New branch: `paper/mlsys2027-submission-review-v0.5`, from the exact source HEAD; target `main`, not stacked. Source checkpoint untouched.
- Starting tracked source tree was clean. A hash-verified sparse audit checkout used authentic Git commit/tree/blob objects; absent unrelated paths were skip-worktree, not deletions. Internal reviews were then created as new files.
- Final HEAD: the commit containing this report, resolved by the Draft PR head and recorded verbatim in its delivery description. A commit cannot contain its own immutable hash; the PR provides that external receipt.

## Contribution and review method

The bounded contribution is measured evidence of how output qualification and the actual stateful interface constrain usable speculative execution, plus a prospective continuation-control test on one qualified path. It is not a new threshold algorithm, universal hardware model, or demonstrated incremental advantage of adding Guard.

The coordinator read the entire paper and supporting ledgers before edits. Nine independent review lenses were saved before synthesis: A systems, B experimental rigor, C statistics, D novelty/related work, E adversarial, F champion, G writing, H rendered visual communication, I artifact reproduction. A fresh-context writing supplement and independent comparator source audit were added. Reports are in `reviews/submission_v05/`; `META_REVIEW.md` records priority, evidence, action, risk, page impact, and rejected requests. Reviewers did not receive each other's reports before their independent initial judgments. Fresh A/B/E/G re-review agents assessed surviving objections rather than merely checking requested edits. An area-chair simulation follows their final reports. These are internal, nonanonymous records.

### Independent concerns and preserved disagreements

| Lens | Main concern / decision |
|---|---|
| A systems | Runtime is credible but a simple guard adds no demonstrated benefit; retain essential timer and fallback-state detail. |
| B rigor | Prospective does not mean historically uninformed; separate frozen held-out outcomes from prior platform knowledge and qualify provenance recovery. |
| C statistics | A CI spanning parity is not energy equivalence; fallback denominator is executions; oracle is descriptive, not a guarantee. |
| D novelty | Accounting/adaptation/heterogeneity already exist; TurboSpec can disable speculation and BanditSpec is relevant prior art. |
| E skeptical | Limited novelty, uncontrolled cases, no successful 358H remedy, and Always-Spec's higher estimate remain rejection grounds. |
| F champion | The specific measured counterexamples, controls, and retained negative evidence can support an empirical systems contribution. |
| G writing | Condense repeated history, connect qualification to continuation without inventing causal transfer, reduce internal workflow language. |
| H visual | Keep four hardware figures and runtime table; separate ratio directions; do not add a decorative policy figure. |
| I artifact | Archive is independently reproducible; clarify Git prerequisites and distinguish integrity from historical attestation. |

A's implementation-detail request and G's concision request are resolved selectively: timer boundary, state suffix removal, and rule stay in main; candidate grid/tie breaks stay in appendix. E's rejection case and F's champion case both remain visible, not averaged into consensus acceptance.

## Material scientific corrections

1. **Historical comparator scope (P0).** Source and independent audit show historical M4, RTX workload controls and B570 compare re-tokenized CLI text; some historical HumanEval paths retain prompt echo. These are not direct generated-ID certificates. Current prose, captions and wording-only table overlays make this explicit. No counts, raw records, classifications, or hidden mismatch counts were changed or inferred. The separate RTX numerical token/score capture and 358H direct-ID evidence retain their respective scopes. Prospective M4 qualification and formal comparisons remain direct generated-ID checks. See `evidence/SUBMISSION_COMPARATOR_SCOPE_V05.md` and `reviews/submission_v05/COMPARATOR_AUDIT.md`.
2. **Energy inference (P0 wording).** The historical package-energy interval includes parity; it does not establish equivalence/neutrality or improvement. Values and uncertainty remain unchanged.
3. Timer wording now matches code: sampler/speculator setup, initial prefill and initial speculative setup precede the timed region; generation-loop initialization and online decisions are charged.
4. Historical knowledge informed the M4 design. Prospective refers to the frozen policy evaluated on reserved prompts, subject to the recorded prior-exposure inventory.
5. Fallback is 55/180 executions (30.6%), not a fraction of beneficial choices. The oracle is the lower measured target-only/Always-Spec median; it is unavailable online and not a universal achievable-policy bound.

Protected results remain Guard 1.3114x [1.2487, 1.3787], Always-Spec 1.3469x [1.2867, 1.4088], Guard/oracle 1.0278x [1.0137, 1.0446], 180/180 direct-token exact per speculative formal path, energy NOT_CLAIMED. The 358H outcome remains `UB2_INTRINSICALLY_BLOCKED_IN_TESTED_STACK`; no formal R2 speedup exists.

## Manuscript changes

- Abstract: one boundary-led story; fewer historical numbers; direct prospective result, higher fixed-speculation estimate and no demonstrated incremental control advantage remain visible.
- Introduction: measured question and bounded empirical contribution; historical comparator qualification is explicit, without a four-platform architectural ranking.
- Sections 4–5: scope comparator language, correct energy inference, retain both M4 outcomes and stack-specific diagnoses.
- Section 6: two concise synthesis/transition paragraphs, replacing repeated result summaries.
- Section 7: qualification then continuation as complementary decisions in separate studies; historical knowledge, measured boundary, reference estimator, state handling, fallback denominator and oracle scope clarified. No causal claim that 358H experimentally caused M4 design.
- Related work: acknowledge TurboSpec's disable option; append one primary-source citation, BanditSpec (ICML 2025, PMLR 267). All prior bibliography bytes retained. MemSpec lead recorded but no unsupported detailed comparison added.
- Limitations: consolidate material comparator, campaign, runtime, concurrency, energy, provenance and stopped-intervention boundaries.
- Conclusion: conceptual consequence for systems measurement and qualified runtime decisions, without a metric dump or promised remedy.
- Appendix: nine-candidate grid, conditional bootstrap interpretation, historical comparator limits and oracle construction.

## Deliberately rejected or deferred

No extra Guard complexity, alternate k/backend/workload, timing rerun, post-hoc policy search, subgroup promotion, added deployment/risk-reduction claim, pooled cross-campaign estimator, or paired-comparison analysis introduced to find a more favorable story. No claim of persistent-state benefit without its counterfactual. No new runtime figure: grouped table is sufficient. No template geometry/font reductions or gratuitous final-column balancing. No indiscriminate bibliography expansion. No universal UB2 or hardware diagnosis. A standalone reused historical artwork could still be misunderstood without its revised caption; immutable artwork is retained and this presentation risk is documented.

## Figures, packaging and validation

Four original vector figure assets, data, native widths and style remain byte-identical. Captions qualify historical labels; Figure 4 loses only a repeated explanation. Runtime Table 3 separates baseline speedup from the descriptive hindsight ratio. Historical generated table files remain immutable; exact checked `_v05.tex` overlays change interpretation wording only.

Final build: **10 body pages + 1 references page; separate appendix 4 pages**. Internal hardware-only removal check: 9 body + 1 references, no stale runtime section or unresolved references. Official template geometry/style unchanged.

| Gate | Result |
|---|---|
| Historical numerical/source checks | PASS, 228; original validator unchanged |
| Runtime evidence/numerical checks | PASS, 117; 23 macros |
| M4 archive | PASS, all 62 payloads; independent full recomputation, selection, exactness and CI endpoints |
| Formal-start provenance | PASS, archive freeze and qualification bytes equal authentic pinned Git objects; metadata defect retained |
| Protected scientific assets | PASS, 260 protected-file checks; all 57 historical prose macros retained |
| Figure replay | PASS, original numerical replays, current style variants, schematic, widths, placements and appendix |
| LaTeX/PDF | PASS, both documents; citations resolved, 15 references, full author lists, fonts embedded, anonymous metadata/text/links, no overfull boxes |
| Added scope checks | PASS, 37 comparator/projection/provenance checks |
| Clean-room package | PASS, 36 manifest members; fresh ZIP extraction builds both PDFs, all per-page extracted text identical, no unresolved/overfull errors |
| Visual review | All 15 pages reviewed; see FINAL_VISUAL.md for page-level findings and grayscale checks |

Receipts are versioned `*_V05.json` under `evidence/`. The unchanged legacy historical asset generator is retained but not run against truncated Git history. Default assets now verify frozen projections; a wrapper executes the unchanged numerical validator and restores its immutable old receipt after saving fresh v0.5 results. Scope diff uses tree comparison plus HEAD/worktree comparison to avoid missing-blob rename reads in the sparse checkout; no scope check is removed. The complete source ZIP builds independently, while full artifact QA requires historical Git objects and evidence. The compact 358H record cannot replay unavailable local raw traces.

## Final style and re-review

No Humanizer skill was available in this environment; none is claimed. After a complete scientific/numerical/LaTeX gate, a manually inspected sentence-level pass applied narrow G/E suggestions (pronoun, decision grammar, comparator naming and descriptive oracle terminology). No numbers, uncertainty, causal strength, policy, citations or evidence classes changed. All validation gates were rerun afterward. `SUBMISSION_STYLE_V05.json` records the edits.

A/B/E/G final reports, `FINAL_REVIEW_DISPOSITION.md` and `MOCK_DECISION.md` preserve resolved issues and remaining rejection grounds. The recurring surviving objection is contribution significance: familiar principles plus valuable bounded measurements, without an incremental Guard benefit or successfully evaluated 358H remedy. Editorial work cannot supply missing evidence. Historical text-path evidence, uncontrolled campaigns, one prospective M4 configuration, finite prompts, unmeasured session uncertainty, compact-only 358H provenance and recovered freeze metadata remain limitations.

No new hardware or runtime timing was performed.
No closed experiment result was modified.
No post-hoc policy search was performed.

This revision is for author review in a new Draft PR. It is not a conference submission and is not automatically merged.
