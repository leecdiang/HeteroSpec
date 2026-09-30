# Consolidated Revision Opportunities

Artifact-only editorial synthesis of `manuscript-v0.8.3.pdf`, `appendix-v0.8.3.pdf`, and `REVIEWER_1_SYSTEMS.md` through `REVIEWER_6_CHAMPION.md`. Reviewer counts below count **independent reviewers who requested the particular modification**, not mentions of a limitation in the broader review. R1–R6 identify those six reports in order. P0 means an acceptance-blocking error in the submitted claim; P1 an important revision; P2 a useful strengthening; P3 polish. No P0 is established by these artifacts. Scientific-risk-of-edit estimates the risk of changing the scientific inference, rather than the effort to typeset the change.

## Central prediction and evidence

### CR-01 — Make the effective B570 sample visible at the claim

- **Severity / dimension:** P1 / presentation and significance calibration.
- **Independent requests:** **6** — R1, R2, R3, R4, R5, R6.
- **Where:** Manuscript abstract (p. 1), §5.2 (p. 6), conclusion (p. 10); Appendix §J and Tables A6–A7 (pp. 6–8).
- **Problem:** The prespecified 72/72 execution endpoint is correct, but three repetitions are repeat-stable for each of 24 prompts. Only four prompts, or 12 repetitions, diverge from the UB128 reference; 20 prompts match that reference. The appendix discloses the granularity, while the headline can imply 72 distinct, discriminating trajectories.
- **Why it matters:** The four divergent prompts are the strongest test that UB1 is predicting the serialized path instead of merely echoing the reference; repetitions establish stability rather than 72 independent prompt successes.
- **Localized fix:** Immediately after each prominent 72/72 claim, add “24 repeat-stable reserved prompts × three runs; four reference-divergent prompts (12 runs), 20 reference-equal prompts.” Put a compact UB128/live **60/72** versus frozen UB1/live **72/72** comparison and one of the four first-divergence examples beside §5.2, retaining the full ledger in Appendix Table A7. State that all 24 ledger outputs reach 128 IDs if interpreting “complete” there.
- **Scientific risk of edit:** **LOW**, provided 72/72 remains the frozen execution-level endpoint and 24 is described as distinct prompts, not an after-the-fact replacement endpoint.

### CR-02 — Make the full-array commitment auditable, or precisely state the PDF-only limit

- **Severity / dimension:** P1 / validity and evidence access.
- **Independent requests:** **5** — R1, R2, R3, R5, R6. R4 separately identifies the same PDF-only limitation but does not request an artifact addition.
- **Where:** Manuscript §3.1 (p. 3) and §5.2 (p. 6); Appendix §J, especially the commitment record and Table A7 (pp. 6–8).
- **Problem:** The PDFs provide a file digest, recorded relative chronology, short per-prompt hashes, equality counts, and four divergence examples. They do not expose all predicted and live ID arrays or an independently inspectable dated freeze record. A SHA-256 digest establishes content identity given the file, not the time at which it existed. The reported 91.37-second interval is recorded chronology, not a consequence of the hash.
- **Why it matters:** A reader cannot independently recompute 72 complete-sequence matches or authenticate their pre-live freeze using these two PDFs alone. This is a verification limit, not evidence of an incorrect result or an absent underlying archive.
- **Localized fix:** If anonymous supplemental access is feasible, give a reviewer-accessible locator and a short checking recipe for the 72 predicted arrays, 72 live arrays, full hashes, and timestamped freeze/live events; identify which records can be independently checked. Otherwise state plainly in §J and the main-text provenance sentence that the submission lets readers inspect the summary ledger and reported chronology only. Preserve the existing digest, chronology, and double-blind constraints without calling the digest temporal proof.
- **Scientific risk of edit:** **MEDIUM**: an artifact or audit procedure must preserve the actual pre-live record and anonymity; a text-only disclosure is low risk but cannot supply the missing independent check.

### CR-03 — Bound “target-partition sufficiency” to prediction on the tested path

- **Severity / dimension:** P1 / validity and scope.
- **Independent requests:** **4** — R1, R2, R3, R4. R5 asks for a more direct prior-work distinction, addressed in CR-11; R6 praises the existing bounded language rather than requesting this edit.
- **Where:** Manuscript abstract/Introduction (p. 1), §5.2 (p. 6), §9–Conclusion (p. 10).
- **Problem:** The body already disclaims a unique kernel or universal micro-batch rule. Detached headline uses of “sufficiency” or “mechanism” can still be heard as a causal localization. The target-only UB1 harness predicts the live serial trajectory; it does not toggle only the target micro-batch inside the live speculative loop with its execution history held fixed.
- **Why it matters:** Predictive reproduction on one B570 Vulkan configuration does not isolate the responsible numerical operation, prove a live-loop intervention effect, or transfer to RTX/other backends.
- **Localized fix:** Place “predictive/observational sufficiency on the tested B570 stack and capped endpoint” beside the first headline and conclusion uses. In §5.2 add one sentence describing the missing live-loop, history-controlled intervention and keep the present non-unique-cause caveat. Lead the first-page contribution with the frozen prediction while calling RTX/B570 qualification and 358H cost distinct supporting cases; say no cross-backend predictor transfer was tested.
- **Scientific risk of edit:** **LOW** for clarification; **HIGH** if the replacement prose instead implies causal isolation or transfer.

### CR-04 — Clarify the “complete sequence” endpoint near the headline

- **Severity / dimension:** P2 / validity and presentation.
- **Independent requests:** **2** — R1, R5.
- **Where:** Manuscript abstract/first use of “complete” (p. 1), §5.2 (p. 6); Appendix §J and Table A7 caption (pp. 7–8).
- **Problem:** “Complete” is defined in the methods and appendix as all committed generated IDs up to the first 128 IDs or earlier inclusive EOG, excluding prompt IDs and uncommitted proposals. The headline alone does not carry that cap; the reserved ledger shows every output has length 128.
- **Why it matters:** Readers may mistake capped generated-output equality for unbounded completion equality or whole-request identity.
- **Localized fix:** At first headline use, write “complete generated-ID sequences within the 128-ID/EOG endpoint.” In Table A7's caption note that all 24 reserved outputs reached the cap. Do not suggest an EOG case occurred in this ledger.
- **Scientific risk of edit:** **LOW**.

### CR-05 — Test transfer on an independent backend/model, if a broader mechanism claim is sought — **CONFLICT**

- **Severity / dimension:** P2 / significance and external scope; a new experiment, not a repair to the present within-stack result.
- **Independent requests:** **3** — R1, R2, R3 explicitly propose another backend/model prediction study. R4 says a comparable success would materially change its weak-reject assessment; R5 says it might strengthen its weak accept; R6 says it would strengthen confidence but is not needed for acceptance. These are distinct judgments, not six requests for an experiment.
- **Where:** Manuscript §9 (p. 10); a new, separately labeled study would need its own methods/results and appendix evidence.
- **Problem:** H1 is prospectively validated on one B570 model/runtime/backend, greedy setting, and HumanEval slice. No transfer or prevalence estimate follows from it.
- **Why it matters:** Reviewers disagree about whether a bounded prediction plus qualification/cost discipline has enough significance without a second independent success. The existing local claim remains valid as stated in all six reviewers' assessments.
- **Localized fix / opposing routes:** **Experimental route:** freeze the same full-sequence prediction criterion, independent reserved set, and reference-divergent comparison on a genuinely different backend or model; report failure as well as success and keep settings distinct. **Text-only route:** retain the tested-stack claim and foreground the untested transfer in §9 and the abstract. R1/R2 and R4 assign greater decision value to transfer; R6 explicitly accepts the bounded evidence, with R3/R5 intermediate. Do not convert an optional future experiment into an alleged current acceptance blocker.
- **Scientific risk of edit:** **HIGH** for new experimental comparability, freeze integrity, and interpretation; **LOW** for the bounded text route.

### CR-06 — Separate predictive proxy from a causal partition intervention — **CONFLICT**

- **Severity / dimension:** P2 / validity and mechanism discrimination.
- **Independent requests:** **2** — R2, R3. R3 proposes a same-prefix/logit or live-partition intervention; R2 asks for clearer H1/H2 discrimination and notes the absence of a reserved competing predictor. Other reviewers generally regard the existing predictive sufficiency as a bounded contribution without requiring that experiment.
- **Where:** Manuscript §5.2 and §9 (pp. 6, 10); Appendix §J's H1/H2 tree (p. 6).
- **Problem:** H1 was selected after 36/36 exposed discovery matches, and H2 was not run because H1 passed. The reserved comparison shows UB1 prediction, not a controlled switch of only live speculative target partition on identical committed prefixes/history.
- **Why it matters:** The current test supports path-level predictive sufficiency but does not uniquely localize why the paths diverge or establish that a live UB1 intervention would restore the reference trajectory.
- **Localized fix / opposing routes:** **Text-only:** explain why H1 could have failed on reserved trajectories, what H2 would have tested if H1 failed, and explicitly say H2 is unrun; name a same-prefix intervention as future discrimination. **Experimental:** on the four divergent prompts compare UB1/UB128 target logits and IDs at identical committed prefixes, or change only the live target partition with history controlled; prerecord the new endpoint and report it separately from 72/72. Do not imply the proposed experiment was already performed. This is a strengthening request, while the bounded-prediction reading remains supported by the other reports.
- **Scientific risk of edit:** **LOW** for accurate H1/H2 text; **HIGH** for intervention design and any stronger causal inference.

## Evidence boundaries and supporting cases

### CR-07 — Prevent pairing historical cost with fresh qualification

- **Severity / dimension:** P1 / validity and presentation.
- **Independent requests:** **4** — R1, R4, R5, R6.
- **Where:** Manuscript Table 1 (p. 3), Table 2/Figure 2 vicinity (p. 5), §5.1/Figure 3 (pp. 5–6); Appendix Table A5 (p. 6).
- **Problem:** Table 2 mixes historical text-path ratios and 358H direct-ID rows, and its historical B570 **60/90** resembles the fresh B570 fast **60/90** despite distinct comparators and runs. Figure 3A proxies and Figure 3B direct-ID gates sit side by side, but there is no matched fresh latency endpoint; fresh and historical settings differ in runtime/front end, context, reference, and sometimes driver.
- **Why it matters:** A visual or screenshot-level reading can accidentally certify old speedups with new ID gates or infer an exactness/cost tradeoff from unmatched runs, although the captions already deny it.
- **Localized fix:** Visually group Table 2's historical text-path rows apart from the 358H direct-ID rows; add a one-line Table 1/§5.1 fresh-study configuration note and an adjacent statement under Table 2/Figure 3 that the RTX/B570 direct-ID counts have **no matched fresh latency** and do not qualify historical timings. Label the two B570 60/90 populations by comparator and campaign whenever adjacent.
- **Scientific risk of edit:** **LOW** for labeling. A cross-run tradeoff estimate would be **HIGH** risk and is not supported.

### CR-08 — Measure matched latency on a freshly qualified path, if the paper seeks a cost/qualification tradeoff — **CONFLICT**

- **Severity / dimension:** P2 / significance; new experiment.
- **Independent requests:** **1** — R3 explicitly proposes a freshly matched latency rerun. R5 identifies the absent paired latency as a limitation, while R1/R6 seek clearer disclosure and R4 treats it as a scope limit rather than demanding a run.
- **Where:** Manuscript §5.1/Figure 3 (pp. 5–6), §9 (p. 10); Appendix §I (pp. 5–6).
- **Problem:** Fresh RTX serialization qualifies at 90/90, but those prospectively frozen direct-ID runs do not have a matching speed endpoint. Historical timing cannot be attached to them.
- **Why it matters:** The paper cannot quantify the speed cost of a *freshly qualified* RTX path from the displayed data.
- **Localized fix / opposing routes:** **Experimental:** measure paired post-prefill latency on the same frozen configuration and direct-ID-qualified path, with comparator and gate aligned, as a separate study. **Text-only:** preserve the explicit absence and avoid any synthesized tradeoff; CR-07 supplies the near-table warning. The reviewers differ in how much a new positive performance endpoint matters to significance, not on the fact that it is unmeasured.
- **Scientific risk of edit:** **HIGH** for new study/protocol comparability; **LOW** for disclosure.

### CR-09 — Keep 358H replay and proposal inseparable

- **Severity / dimension:** P2 / validity and presentation.
- **Independent requests:** **3** — R1, R4, R6.
- **Where:** Manuscript §5.3/Figure 4 (p. 7), §7.1 (p. 8), conclusion (p. 10).
- **Problem:** The NPU's 58.35% region is one synchronous OpenVINO **full-prefix reconstruction plus proposal** call. It is not a measured replay-only component. The CPU's 87.34% is complete target-side work. The attempted persistent-state intervention stopped at qualification.
- **Why it matters:** Calling 58.35% “replay overhead” or subtracting it as recoverable savings would claim an unmeasured persistence benefit. The current caption/body mostly handle this; the short conclusion could be read alone.
- **Localized fix:** Use “combined reconstruction/replay plus proposal (inseparable)” in the prominent Figure 4 label and concise conclusion; retain the measured CPU target-side label and one sentence that replay-only cost and persistence savings remain unknown. An isolated, qualified state-persistent comparison would be a new study, not a reinterpretation of Figure 4.
- **Scientific risk of edit:** **LOW** for exact labels; **HIGH** for an unsupported savings estimate.

### CR-10 — Present M4 Guard against the fixed speculative comparator

- **Severity / dimension:** P2 / significance and presentation.
- **Independent requests:** **4** — R2, R3, R5, R6.
- **Where:** Manuscript §7 opening (p. 8), §7.3/Table 3 (p. 9), conclusion (p. 10).
- **Problem:** Guard beats target-only (Target/Guard 1.3114×), but fixed Always-Spec is faster; post-study paired Guard/Always-Spec latency is 1.0271 [1.0130, 1.0436], where values above one mean Guard slower. The table caption explains this, but isolated positive speedup wording could suggest incremental control benefit.
- **Why it matters:** The qualified held-out test is useful negative evidence, not a demonstrated new optimization over the relevant fixed policy.
- **Localized fix:** Pair any summary of 1.3114× with the fixed comparator and negative paired result; keep “post-study paired secondary” in Table 3's row/heading and state latency direction there. Introduce §7 as a test of qualification/runtime decisions with one stopped intervention and one negative incremental comparison. Retain the offline oracle as hindsight, not a deployable policy.
- **Scientific risk of edit:** **LOW**.

## Organization and explanation

### CR-11 — Explain why the B570 prediction differs from prior batch-shape observations

- **Severity / dimension:** P2 / novelty framing and presentation.
- **Independent requests:** **2** — R2, R5.
- **Where:** Manuscript §5.2 (p. 6), Related Work §8 (p. 9), first-page contribution paragraph (p. 1).
- **Problem:** Existing target batch-shape sensitivity is acknowledged. The paper's distinctive evidence is the precommitted full-trajectory prediction, especially four reference-divergent reserved prompts; the current related-work passage could make that contrast more direct. H1's selection on exposed discovery and its possible failure on reserved data also deserve a plain explanation.
- **Why it matters:** The novelty should rest on the prospective test and its specific falsifier, not on discovering numerical path dependence or proposing a new decoder/control rule.
- **Localized fix:** Add two or three sentences linking prior observations to this protocol: H1 selected at discovery 36/36, frozen complete ID arrays before live reserved outcomes, all-or-nothing 72/72, and 12/12 divergent executions across four prompts. Say H2 would have been considered only upon H1 discovery failure and was not run. Avoid claiming a reserved competing-predictor test.
- **Scientific risk of edit:** **LOW**, as long as prior work is characterized only to the extent already described in the PDFs.

### CR-12 — Give central evidence the space occupied by the generic workflow figure

- **Severity / dimension:** P2 / presentation.
- **Independent requests:** **6** — R1, R2, R3, R4, R5, R6.
- **Where:** Manuscript Figure 2 and §5.2 (pp. 5–6); Appendix Tables A6–A7 (pp. 7–8).
- **Problem:** Figure 2 restates the evaluation sequence while the strongest prediction requires cross-reading §5.2 and appendix ledgers. Its arrows may look like a causal chain across independently frozen systems despite the caption's caveat.
- **Why it matters:** Main-text area can make the four informative divergences and discovery → freeze → reserved validation easier to understand at first pass.
- **Localized fix:** Shrink, move, or replace Figure 2 with a compact B570 timeline/comparison or one first-divergence example, and use the freed space for CR-01's same-set 60/72 versus 72/72 contrast. Preserve the distinction between the separate systems and the B570 within-study sequence. Reviewers vary on whether to remove, move, or replace the figure; no specific layout has unanimous support.
- **Scientific risk of edit:** **LOW**.

### CR-13 — Add the M4 session caveat at Figure 1

- **Severity / dimension:** P3 / presentation and scope.
- **Independent requests:** **1** — R6.
- **Where:** Manuscript Figure 1 (p. 4).
- **Problem:** The representative and HumanEval M4 campaigns share hardware but differ in session conditions as well as workload. The caption/body say this, yet the plotted contrast may be quoted without the caveat.
- **Why it matters:** A reader might assign the 0.842× versus 1.387× difference to workload alone.
- **Localized fix:** Put “separate sessions; not workload-only attribution” beside the visual or early in its caption.
- **Scientific risk of edit:** **LOW**.

### CR-14 — Expand compact labels and improve appendix/plot scanability

- **Severity / dimension:** P3 / presentation.
- **Independent requests:** **1** — R5.
- **Where:** Manuscript Table 2 (p. 5), Figure 3A (p. 6); Appendix Table A4 (p. 4).
- **Problem:** “Second.” and “Diag.” take decoding; Figure 3A's shape key lives chiefly in the caption; Table A4 repeats evidence inventory in sparsely used appendix space.
- **Why it matters:** These are small first-pass reading costs in an already dense evidence hierarchy.
- **Localized fix:** Expand the two Table 2 class abbreviations, add a small in-figure shape key if legible, and compress Table A4 only if its provenance distinctions remain available.
- **Scientific risk of edit:** **LOW**.

## Decision boundary across reports

The reports do **not** agree on acceptance or the need for more experiments: R1/R3/R5 weak accept, R2/R4 weak reject, and R6 accept. R2/R4 weigh the one-backend, four-divergent-prompt scope against top-tier significance; R6 accepts a bounded measurement contribution; R1/R3/R5 fall between. All six treat the 72/72 as a reported, falsifiable within-path result and distinguish absent independent PDF audit access from evidence of failure. The text-only revisions above can calibrate the claim and improve audit disclosure. CR-05, CR-06, and CR-08 preserve separate new-experiment routes and their opposing judgments; this consolidation does not decide the venue's significance threshold for the reviewers.
