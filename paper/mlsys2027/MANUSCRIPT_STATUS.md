# v0.6 paired M4 Guard versus Always-Spec secondary analysis

Current review: `reviews/M4_GUARD_ALWAYS_SECONDARY_RESPONSE_V06.md`. Current
PDFs: `manuscript/output/manuscript-v0.6.pdf` and `manuscript/output/appendix-v0.6.pdf`.
This reviewer-requested post-study contrast uses only frozen raw observations:
Guard/Always-Spec = 1.0270760219826773, 95% prompt-bootstrap interval
[1.0129560055428655, 1.0435592653980876]. The interval lies above parity;
Guard had higher latency on this comparison. Prompt medians favor Guard on
24 prompts and Always-Spec on 36, with no ties. No new measurement or policy
change occurred. All v0.5 review qualifications remain in force.

## v0.6 validation and visual review

- Main paper: **10 body pages + 1 reference page**; separate appendix: **4 pages**.
- Hardware-only removal/reference check: **9 body pages + 1 reference page**.
- **228** historical numerical checks; **260** protected narrative/source/assets;
  **57** historical macros; **117** prior runtime checks preserved in order plus
  **19** new checks (**136** total), with **23** primary and **6** secondary macros.
- Full primary archive replay: all **62** payload hashes, frozen policy, direct-ID
  qualification/formal pairs, primary intervals and fallback reproduced.
- Independent secondary path: **638** checks, all 60 prompt medians and ratios,
  exact headline and finite-bootstrap endpoints, and descriptive counts.
- **7** hardware-free replay/rejection tests; **41** submission scope/projection
  checks. All **41** pre-existing runtime-tree files and all **40**
  pre-existing paper evidence files are byte-identical to the exact starting main.
- Main, appendix, and hardware-only builds passed. Official style unchanged;
  fonts embedded, PDFs anonymous, no unresolved citations/references or overfull
  boxes. The **37-file** source ZIP also compiled in a clean directory.
- Fresh visual review covered every main/appendix page and detailed full-page
  inspection of main pages 9–10 and appendix page 4: Table 3's separated contrast
  and direction, literal interpretation, limitations, formula and provenance
  note are readable and fit without clipping or overlap. No new figure.

Receipts: `evidence/M4_GUARD_ALWAYS_SECONDARY_QA_V06.json`,
`evidence/M4_GUARD_ALWAYS_SECONDARY_TEST_QA_V06.json`,
`evidence/M4_GUARD_ALWAYS_SECONDARY_VISUAL_QA_V06.json`, and the versioned
`NUMERICAL`, `RUNTIME`, `NARRATIVE`, `NARRATIVE_FIGURE`, `NARRATIVE_PDF`, and
`SUBMISSION` v0.6 receipts. Previous receipts and PDFs remain historical and
unchanged. The artifact comparison sharpens the existing negative/control
conclusion; no result-dependent analysis choice or new measurement occurred.

# v0.5 coordinated submission review

Current review: `SUBMISSION_REVIEW_V05.md`. Current PDFs: `manuscript/output/*-v0.5.pdf`. Independent reports and disposition: `reviews/submission_v05/`. Historical comparator claims are narrowed by `evidence/SUBMISSION_COMPARATOR_SCOPE_V05.md`; closed values and evidence classes remain unchanged. Runtime integration is complete; no new timing or policy search was performed.

The previous status below is retained as history.

---

# Manuscript v0.4 — measured runtime integration

Current status: **MEASURED HARDWARE + BOUNDED PROSPECTIVE RUNTIME STUDY; DRAFT FOR AUTHOR REVIEW** — 2026-09-25.

Base main: `bbf0c555cc50242f85c086eac342c9deb5c2e945`. Branch: `paper/mlsys2027-runtime-integration-v0.4`. The exact delivery HEAD is the Draft PR head; `RUNTIME_INTEGRATION_V04.md` records scope and QA.

Section 7 now connects qualification to realized-cost control: the tested 358H intervention is qualification-blocked with no R2 performance result, and the separately frozen M4 guard is exact and profitable against target-only. The Guard does not beat fixed speculation's aggregate point estimate. Runtime energy is not claimed. The metadata-recording defect and independent M4 provenance recovery remain disclosed. Hardware campaigns and figures remain unchanged.

Current artifacts are `manuscript/output/manuscript-v0.4.pdf` (10 body pages + 1 reference page), `manuscript/output/appendix-v0.4.pdf` (4 pages), and the current v0.4 collaboration ZIP. The old v0.3 ZIP/PDFs below are historical. Four main figures retain native sizes on pages 4–7; new Table 3 reports M4 runtime ratios, CIs and descriptive oracle regret. Title retained.

Canonical build/check passes: 228 original numerical checks, 260 protected-file checks, all 57 prior prose numeric macros, 117 runtime checks and 23 sourced runtime macros, five original figure replays, active asset/placement checks, embedded fonts, anonymous PDFs, full-author references, zero overfull boxes and unresolved citations/references. Hardware-only removal remains an internal reference test (9 body + 1 reference page), not the primary paper or a standalone hardware manuscript.

Humanizer was used after claims/citations were frozen. Eight style edits preserved numerical literals, TeX commands and citations; each scientific assertion was manually checked. A later layout-only page break separates hardware appendix tables from runtime notes. All final main and appendix pages were rendered and inspected, including the runtime table in 96-dpi grayscale. The final body page has a normal unused right column; the conclusion is complete in the left column. No geometry or font changes were used.

Remaining reviewer risks: modest controller novelty; one model/runtime and finite held-out workload; M4 session/thermal uncertainty; 358H compact diagnostic provenance without local raw-trace replay. Full v0.2 raw qualification outputs are not present locally; their disposition is supplied by the task closeout, with pinned transition/protocol/diagnostic corroboration. These limits are not resolved by the integration.

No new hardware/runtime timing was performed. No closed experiment result was modified. The PR is Draft and must not be automatically merged.

---

# Initial manuscript v0.3 — collaboration freeze

**INITIAL DRAFT FROZEN FOR OVERLEAF COLLABORATION** — 2026-09-22.

This v0.3 status is historical. The v0.2 record below is also historical and is superseded where it describes active figures, page counts, validator invocation, or unresolved integration decisions.

- Starting main: `9014e4b8a89031cfa26fc2c03180181bee124d86`. Fetched, checked out main, confirmed this exact HEAD and a clean working tree before creating the requested integration branch.
- Branch: `paper/mlsys2027-initial-draft-v0.3`.
- Integration branch HEAD at the artifact-freeze checkpoint: `8ea0be7ae0e18e733e12405b136f58460473dfba`. The follow-up documentation commit records this already-built artifact revision. Resolve the delivery HEAD with `git rev-parse paper/mlsys2027-initial-draft-v0.3`; the Draft PR head identifies the final documentation revision.
- Delivery target: Draft PR against `main`; no automatic merge.
- Hardware evidence: closed and unchanged. Cross-platform synthesis: retrospective; campaign primary outcomes were frozen independently. Later controls retain their bounded evidence classes.
- Runtime/software: full Section 7 retained, proposed and unmeasured, including requirements, persistent-state interface, qualified path selection, and evaluation questions. Future evaluation must be a new frozen study. No implementation or result is claimed.

## Current artifacts and displays

| Artifact | Pagination |
|---|---|
| `manuscript/output/manuscript-v0.3.pdf` | 10 body pages + 1 reference page |
| `manuscript/output/appendix-v0.3.pdf` | 3 separate pages |
| `manuscript/build/hardware-only/hardware-only.pdf` | 8 body pages + 1 reference page; verification build only |
| `manuscript/output/overleaf-initial-draft-v0.3.zip` | 35 required source/dependency files; clean local compilation verified |

| Main figure | Semantic label | Asset relative to `figures/` | Page / width |
|---|---|---|---|
| 1: M4 independent observed contrast | `fig:m4` | `style_v04/pdf/m4.pdf` | 4 / 3.25 in |
| 2: measured translation boundaries | `fig:translation` | `mechanism_v05/mechanism.pdf` | 5 / 6.75 in |
| 3: verification-path qualification | `fig:verification` | `style_v04/pdf/verification.pdf` | 6 / 6.75 in |
| 4: isolated versus realized 358H cost | `fig:state` | `style_v04/pdf/state.pdf` | 7 / 6.75 in |

All assets are unchanged from the specified main, including Candidate B after PR #24. Only the manuscript mechanism caption adopts “does not survive the tested stateful integration.” The source `mechanism_v05/caption.tex` is untouched.

Main tables remain platform scope (Table 1, p. 3) and headline outcomes (Table 2, p. 5). The old overview is inactive; the old verification table is removed from the main flow and reproduced in appendix A3, retaining its five rounded ranges and qualification labels plus all 11 underlying context cells. Historical sources remain in place.

| Appendix display | Contents | Page |
|---|---|---|
| A1 | Frozen statistical policies | 2 |
| A2 | Sensor boundaries and allowed energy interpretations | 2 |
| A3 | Verification context lookup and original rounded ranges | 3 |
| A4 | Eight-case regime inventory, including unchanged 358H P/M labels | 3 |

The inventory uses the unchanged v0.4 booktabs source instead of the old graphical inventory. No active `fig:overview`, `fig:regimes`, or main-paper `tab:mechanism` reference remains.

## Verification and visual review

The ordinary `make check` passes: **228/228 numerical checks**, all five independent historical figure replays, the three active quantitative style receipts, the final schematic hash, four actual native-width placements, all 11 lookup cells, and eight inventory cases. Narrative checks preserve 260 protected-file entries (including overlapping checks), all 57 prior prose numerical macros, the complete figure tree, and the scientific ledger. Raw/processed records, scientific closeouts, original numerical validator, official template and bibliography are unchanged.

Both delivery PDFs pass anonymity checks on text, metadata and links; all fonts, including nested figure resources, are embedded. All 13 references retain full author lists. There are no overfull boxes or undefined references/citations. The official style's harmless empty-anchor warning remains. QA records and hashes are under `evidence/`.

Every page of the final full manuscript (11) and appendix (3) was rendered and visually inspected at 1,500 pixels on the long edge, preserving publication geometry. Figure placement checks confirm the actual 3.25/6.75-inch sizes. The verification page was also inspected in grayscale at 96 dpi: open/filled status marks, shapes and labels remain distinguishable. Hardware-only pp. 7–9 were additionally inspected for the synthesis, related work, limitations, conclusion and references.

All figures and captions are readable and unclipped. Consecutive wide floats occupy pp. 5–7 within the relevant results/diagnosis sequence, without an unintended blank page or drift into an unrelated later section. M4 is a normal top-of-page float on the page where its results begin. The final body page leaves the right column unused before the separate reference page; appendix p. 3 uses normal vertically centered table-float spacing. These are retained initial-draft whitespace, not a reason to shrink artwork, alter the official template, or compress runtime.

## Overleaf handoff and freeze scope

**Ready to become the shared Overleaf initial draft: yes.** Upload the source ZIP as a new project, use pdfLaTeX / TeX Live 2025, and select `main.tex`; select `appendix.tex` for the separate supplement. The bundle has been compiled in an independent directory. Its page counts and every page's extracted text match the reviewed PDFs, and its selected figures, inventory body, and style files retain their original bytes. No Overleaf project, upload, invitation, or submission was performed.

**Coherent without future software results: yes.** The observed outcomes, two configuration-scoped diagnoses, and standalone hardware synthesis do not depend on the proposed intervention. The full runtime reservation remains in the collaboration version. The hardware-only build is a coherence check, not a scope reduction.

The freeze covers the hardware story, scientific boundaries, figure language and manuscript structure. It is not a final submission, a final title/abstract, or a completed runtime contribution. `NARRATIVE_INTEGRATION_V03.md` records the integration decisions and validation boundaries.

---

# Manuscript v0.2 — narrative and selected publication figures

Integration completed: 2026-09-21. For the subsequent internal review and conservative revision, see the follow-up at the end of this record. Integration branch: `paper/mlsys2027-narrative-v0.2`.

The narrative pass started from main `1a11361f8526ec361e20dd6878d6e67352fb7bbd` and was checkpointed at `249c31c986da180bfae2e3f5881c300ae220edfa`. Current main `575f7d3c2991bdf00915fa213a644cb9deeb0673`, including publication-figure source `6cf4924a796ce12ef9c52cb4ef0527cff0937702`, was then merged at `37d2f32dfe6fc180d1c0856f049ec2f10ca22ac8`. No narrative work was discarded. The two `NARRATIVE_*BASELINE.json` evidence records preserve those phases and their protected hashes. Use `git rev-parse HEAD` for the delivery revision.

## Narrative and deliverables

Working title, still provisional: **Speculative Decoding Across Consumer Systems: Gains, Failures, and Runtime Costs**.

The paper begins with variation in integrated gains across the tested consumer workloads and stacks, asks why favorable local indicators fail to translate reliably, then diagnoses correctness-path and state-interface failures. These are bounded measured mechanisms, not an exhaustive theory. M4's observed workload-conditioned contrast stands independently of those mechanisms.

- `manuscript/output/manuscript-v0.2.pdf`: **10 main-text pages + 1 reference page**.
- `manuscript/output/appendix-v0.2.pdf`: **3 separate appendix pages**.
- `manuscript/README.md`: reproducible build and review boundaries.
- `NARRATIVE_REFACTOR_V02.md`: material narrative changes, title alternatives, claim-placement crosswalk and causal-wording review.
- `NARRATIVE_FIGURE_INTEGRATION.md`: final asset selection, captions, placement, validation and layout decisions.

The official submission style and all its hashes remain unchanged. No margin, type-size, spacing, or geometry adjustment was made. Both review PDFs are anonymous. Title, abstract, and final paper conclusion remain provisional; the hardware conclusion is complete. Historical v0.1 completion details and PDFs remain unchanged.

## Section and page allocation

Ranges include floats and are not additive. The runtime section retains approximately 1.5 pages of text across pp. 8–9 within the reserved 1.5–2-page planning budget. The main body reaches the ten-page ceiling.

| Section | Current compiled location |
|---|---|
| 1. Introduction | pp. 1–2 |
| 2. Experimental question and measurement discipline | pp. 2–3 |
| 3. Experimental methodology and platforms | pp. 3–4 |
| 4. Gains do not translate uniformly | pp. 4–5 |
| 5. Why favorable local indicators fail | pp. 5–7 |
| 6. Hardware-study synthesis | p. 8 |
| 7. Runtime co-design from measured failure modes | pp. 8–9 |
| 8. Related work | pp. 9–10 |
| 9. Limitations | p. 10 |
| 10. Conclusion | p. 10 |
| References, excluded from main-page budget | p. 11 |
| Appendix, separate artifact | 3 pages |

## Figure and table status

| Final number | Selected asset | Role and placement | Width |
|---|---|---|---|
| Figure 1 | `figure1.pdf` | Empirical overview, main p. 2 | 6.75 in |
| Figure 2 | `figure3.pdf` | M4 observed contrast, main p. 4 | 3.25 in |
| Figure 3 | `figure2.pdf` | Correctness-path diagnosis, main p. 6 | 6.75 in |
| Figure 4 | `figure4.pdf` | Isolated versus realized stateful cost, main p. 7 | 6.75 in |
| Figure A1 | `figure5.pdf` | Evidence inventory, appendix p. 3 only | 6.75 in |

All five selected vector PDFs under `paper/mlsys2027/figures/pdf/` are byte-identical to integration main. No figure was regenerated. Native widths are preserved (the wide figures differ by only normal TeX unit rounding). All active references use semantic labels and resolve to the final order. No stale accounting-diagram reference remains. Its unchanged historical source is unused; equations and definitions remain in Section 2.

Normal LaTeX floats are used. The state figure is queued at the preceding paragraph boundary so it stays on the state-diagnosis page rather than drifting into the runtime section. Appendix A1 occupies a dedicated, vertically centered float page with spare space above and below. These layout choices preserve validated figure and caption readability without shrinking text or changing the template.

Three main tables cover platforms, headline outcomes, and verification mechanisms. Two appendix tables cover frozen statistical policies and sensor boundaries. All table values and captions, numeric macros, and historical plot-coordinate files are byte-identical to the narrative baseline. No energy ranking was added.

## Evidence and wording checks

- **228/228 existing numerical checks rerun after integration and passed**, using the unchanged validator. The numerical report is byte-identical to the baseline.
- All five figure-specific independent numerical checks pass, including frozen bootstrap conventions and source rows. `NARRATIVE_FIGURE_QA.json` records their scope and limitations; no experiment or raw token-array replay was performed.
- The frozen evidence ledger, machine-readable exact values, source provenance, datasets, estimators, correctness/evidence classes, preregistration status and closeout claims are unchanged.
- Additional narrative checks pass for **89 protected file entries**, every one of the **57 prior prose numeric macros**, and the change scope. Some files are counted by multiple checks; this is not a count of unique datasets.
- The selected figure tree remains unchanged relative to integration main. Its source lock includes one historical narrative document, `WRITING_STATUS.md`; that entry is checked against the locked main revision, while scientific source files are checked against actual working-tree bytes.
- The ledger's historical v0.1 location map is preserved. Its current crosswalk is in `NARRATIVE_REFACTOR_V02.md`.
- All 13 bibliography entries and complete author lists are unchanged. No new source or citation gap was introduced.
- Manual wording review retained shared-path M4 micro evidence, session uncertainty, bounded CUDA divergence, B570 diagnostic status, the distinction between context ranges and CIs, complete target-side costs, inseparable replay-plus-proposal, and the absence of a measured runtime intervention. “Integrated” remains post-prefill decode execution, not whole-request user latency. No universal or exhaustive explanation is claimed.

No unresolved factual or causal wording defect was identified. Remaining editorial decisions are the final title/abstract and the runtime decision; figure selection and integration are complete.

## Runtime reservation and hardware-only coherence

Section 7 visibly states **proposed design only; implementation and measured results pending**. Its requirements follow diagnosed failures: draft-state persistence and reconciliation, correctness-qualified verification, and an optional profitability guard whose overhead must be measured. No implementation, speed, energy, correctness, or ablation result was added.

`make hardware-only` removes Section 7 and produces **9 main pages + 1 reference page**, with no undefined references. The observation-to-diagnosis argument, independent hardware synthesis, related work, limitations and conclusion remain coherent. This local verification PDF is not a separate delivery artifact.

## Final PDF review

Both delivered PDFs compile successfully and match the checked build bytes. Automated checks confirm anonymous metadata/text/links, embedded Type 1 and Type 0 fonts (including nested figure resources), complete reference authors, page counts, and no overfull boxes or undefined references/citations. The RTX identity check accepts line wrapping before “Laptop” while requiring the full hardware identity. The official style's harmless empty-anchor warning remains.

All **11 main-PDF pages and 3 appendix pages** were rendered at 1,400 pixels on the long edge and visually inspected after final integration. Text, equations, tables, figure labels, captions, references and section transitions are legible and unclipped. All ten hardware-only pages were rendered at 1,100 pixels; pages 7–10 covering the state figure, hardware synthesis, related work, limitations, conclusion and references were inspected (earlier content matches the main PDF). Final artifact hashes are in `evidence/PDF_QA.json`.

This work opens one Draft PR. It does not rerun experiments, merge the PR, submit, upload to arXiv, or change repository visibility. Internal provenance files are not anonymous review artifacts.

## Independent internal review and conservative revision — 2026-09-21

The next pass reviewed PR #18 at exact HEAD `afda6a192f3e9359eb5f5d7d24d3313bf59ef2f3` using three independent experimental-rigor, systems-contribution and presentation reviewers. Their complete initial reviews, meta-review and revision disposition are in `reviews/INTERNAL_REVIEW_V02.md`; the review was committed before any manuscript edit. The follow-up branch is `codex/mlsys2027-review-v02` and its Draft PR targets the narrative branch, not main.

Unanimously supported prose corrections make the retrospective synthesis explicit, distinguish independently frozen primary outcomes and later bounded controls, align prominent latency wording with post-prefill decode, name separate M4 sessions in the abstract, soften isolated state-cost causality, and present accounting as a method. All numerical results, estimators, evidence classes, correctness statuses, tables, bibliography, scientific records and the selected figure tree remain unchanged. The overview's manuscript caption wrapper changes one timing phrase; the publication artwork is untouched.

The resulting main PDF remains 10 body pages plus 1 reference page, the unchanged appendix remains 3 pages, and removing runtime leaves 9 body pages plus references. The original 228 numerical checks, five figure checks, protected-source checks, numeric-macro coverage and anonymous PDF checks pass. The historical narrative path allowlist required one explicit in-memory exception for the new review file; no validator was edited, and unmodified `make check` still needs that path exception. The review report records the reproducible invocation and final hashes.

The prior integration pass's absence of identified wording defects is a historical assessment, superseded by this review's concrete corrections and remaining concerns. The paper still requires author decisions on incremental novelty, runtime submission scope, mechanism-table duplication, caveat consolidation and the final title. Conservative copyediting does not make it submission-ready.

All 11 revised main-PDF pages were visually inspected after the final build, split between the coordinating editor (pp. 1–6) and Reviewer C (pp. 7–11). The state figure, synthesis/runtime transition, conclusion and references remain correctly placed. Reviewer C additionally inspected the changed hardware-only ending; the byte-identical appendix retains its complete prior inspection.
