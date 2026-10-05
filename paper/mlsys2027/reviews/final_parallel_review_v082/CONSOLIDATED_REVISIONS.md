# Consolidated Revision Opportunities

## Provenance and interpretation

This artifact-only synthesis uses **only** `manuscript-v0.8.2.pdf`, `appendix-v0.8.2.pdf`, and `REVIEWER_1_SYSTEMS.md`, `REVIEWER_2_NOVELTY.md`, `REVIEWER_3_RIGOR.md`, `REVIEWER_4_ADVERSARIAL.md`, `REVIEWER_5_WRITING.md`, and `REVIEWER_6_CHAMPION.md`. Reviewer IDs below are R1–R6 in that order. Counts denote reviewers who independently raised the underlying modification opportunity, including a stated weakness where the localized repair is evident; shared assignment prompts or reviewer roles are not counted as evidence of consensus. A singleton is labeled explicitly. Page numbers are printed PDF pages. P0 means acceptance blocker, P1 important, P2 useful, and P3 polish. **No item is assigned P0:** these are improvements to an already reported, bounded result, and the reviewers disagree on its acceptance threshold. Scientific risk rates the chance that the *edit or added experiment* changes interpretation, not the importance of the concern.

## Evidence, validity, and scope

### CR-01 — Inspectable B570 precommitment and sequence-validation record

- **Severity:** P1 important. **Reviewers:** 5/6 — R1, R3, R4, R5, R6. **Kind:** validity/evidence; independently shared.
- **Affected PDF:** manuscript §5.2, p. 5; appendix §J, p. 6 (and provenance description §A, p. 1).
- **Exact problem:** The PDFs state the 72/72 complete-ID prediction, pre-live commitment, independent checks, and four divergence examples, but do not expose the actual commitment digest, ordering identifiers, or a per-reserved-prompt binding of predicted and observed arrays. A PDF-only reader cannot independently audit all 72 matches or the pre-outcome freeze.
- **Why it matters:** The predictive endpoint carries the main distinctive contribution; aggregate counts and an asserted archive chronology are weaker inspectable evidence than a compact commitment ledger.
- **Localized fix:** Add the actual digest and serialization/endpoint definition, freeze and first-live ordering markers, and a 24-prompt manifest with three-run sequence lengths and prediction/outcome digests, reference-equality flags, and first divergence where applicable. Point to complete arrays if accessible in a review artifact; keep the four informative divergence examples in the PDF. Do not imply that a printed digest alone independently timestamps a freeze.
- **Scientific risk of edit:** MEDIUM — exposing a reproducible manifest may uncover identity or endpoint inconsistencies and requires careful validation.
- **CONFLICT (presentation extent):** R1/R3/R6 favor all-prompt hashes or full trace access; R4 asks for a smaller in-PDF digest/ordering ledger and one complete divergent example without requiring all 72 arrays in print; R5 allows a compact table or machine-readable supplement if page limits constrain it. These agree on inspectability but differ on how much belongs in the PDF.

### CR-02 — Explicit comparison against a simpler B570 predictor

- **Severity:** P1 important. **Reviewers:** 2/6 — R2, R5. **Kind:** significance/mechanism comparison; independently shared.
- **Affected PDF:** manuscript §5.2, p. 5; appendix §J, p. 6.
- **Exact problem:** The reserved-set result lacks an aligned row comparing default/reference target-only output with the micro-batch-one predictor against the same live serialized sequences. The reported 60/72 reference equality and 72/72 predictor equality imply the comparison but leave its incremental value implicit; an alternative target-only partition is not tested.
- **Why it matters:** A visible competing predictor clarifies why target-partition control predicts the 12 divergent repetition pairs, and whether the claim exceeds same-path replay.
- **Localized fix:** Print a reserved-set comparison table with 24 prompt and 72 run units, `UB128 reference → live` (60/72) and `UB1 target-only → live` (72/72), identify the four prompts/12 pairs where predictions differ, and label this an implied comparison of already observed outputs. If testing another partition, freeze it prospectively and report it separately; do not present an unrun H2 branch as a negative control.
- **Scientific risk of edit:** MEDIUM — the existing comparison is arithmetic, while a new partition experiment could alter mechanistic interpretation.

### CR-03 — Transfer beyond the B570 configuration

- **Severity:** P1 important. **Reviewers:** 6/6 — R1, R2, R3, R4, R5, R6. **Kind:** significance/scope; independently shared, with different acceptance judgments.
- **Affected PDF:** manuscript §§5.2, 9, pp. 5, 10; appendix §J, p. 6.
- **Exact problem:** The frozen prediction uses one B570/Vulkan build, model pair, greedy `k=2`, target partition, HumanEval family, and 24 reserved prompts. No second backend/model family or independent partition intervention tests transfer.
- **Why it matters:** Predictive sufficiency is strong for the tested stack but cannot establish a portable partition rule or broad systems generality.
- **Localized fix:** If feasible, prospectively repeat the same precommitted prediction protocol on a second backend, model pair, or non-code workload, including a possible failed transfer. In the current text, tie the 72/72 result and practical advice to the named tested configuration and list transfer as open work.
- **Scientific risk of edit:** HIGH for a new study (a negative result may narrow the thesis); LOW for scoping prose.
- **CONFLICT (priority/acceptance bar):** R4 considers the untested transfer a possible reason to reject the broad contribution; R1/R2/R3/R5/R6 identify the narrowness but describe second-system testing as optional or compatible with a bounded current claim. This is a significance disagreement, not a dispute about the 72/72 observation.

### CR-04 — Predictive sufficiency versus unique numerical cause

- **Severity:** P1 important. **Reviewers:** 6/6 — R1, R2, R3, R4, R5, R6. **Kind:** validity/scope of mechanism language; independently shared.
- **Affected PDF:** abstract and introduction p. 1; manuscript §5.2 p. 5, Figure 3 p. 7, conclusion/§9 p. 10; appendix §J p. 6.
- **Exact problem:** Phrases such as “target-partition isolation” can be read as identification of a unique kernel, numerical operation, or causal root, although target-only `nubatch=1` is a sufficient predictor and H2 was not run after H1 passed.
- **Why it matters:** Different execution paths could generate the same trajectory. The evidence does not isolate a unique cause or prove a rule for RTX or other backends.
- **Localized fix:** At each headline occurrence state “target-only greedy decoding with target micro-batch one reproduces the serialized trajectory on this tested B570 stack/workload.” Define the UB128 reference and no-live-draft control at first use; add a sentence that observationally equivalent partitions and numerical mechanisms remain possible. Preserve the distinction from the separately qualified RTX path.
- **Scientific risk of edit:** LOW — it calibrates language to the measured endpoint.

### CR-05 — Historical text comparator versus strict generated IDs

- **Severity:** P1 important. **Reviewers:** 6/6 — R1, R2, R3, R4, R5, R6. **Kind:** validity/presentation; independently shared.
- **Affected PDF:** introduction p. 1; manuscript §§2.1, 4 and Tables 1–2, pp. 2, 4; appendix Table A4 p. 4 and Table A5 p. 6.
- **Exact problem:** Historical M4/RTX/B570 timing counts use parsed, re-tokenized CLI text, while fresh RTX/B570 qualification and prospective M4 runtime use direct generated IDs. “Qualified,” “exact,” and “matching pairs” in standalone table cells can be read as uniform direct-ID equality despite explanatory captions.
- **Why it matters:** The old speedups cannot be retrospectively certified under the paper's strict ID contract, and the three B570 figures (historical 60/90 text, fresh serialized 78/90 IDs, reserved 60/72 reference equality) have different endpoints.
- **Localized fix:** Add a comparator column/badge to Table 2 and replace bare “Qualified; exact” in appendix A4 with “text-path agreement” and counts. Put a short endpoint key or roadmap before Table 2/near §§4–5 distinguishing historical timing, fresh direct-ID gates, and reserved ID prediction. Label the three B570 denominators explicitly; keep the qualification-only A5 study apart from timing claims.
- **Scientific risk of edit:** LOW — relabeling preserves the data and limits overreading.

### CR-06 — Fresh latency for the strictly qualified RTX serialized path

- **Severity:** P2 useful. **Reviewers:** 1/6 — R1 only. **Kind:** validity/significance of cross-study linkage; single-reviewer idea.
- **Affected PDF:** manuscript §§4.2, 5.1, pp. 4–5 and Figure 3B p. 7; appendix §I/Table A5 pp. 5–6.
- **Exact problem:** The new 90/90 direct-ID RTX serialized gate has no matched fresh latency endpoint; historical serialized latency came from another host/driver context and weaker comparator.
- **Why it matters:** Readers cannot price strict qualification from the same execution campaign.
- **Localized fix:** If matched latency was recorded under the frozen fresh path, report it with its timing boundary and estimator; otherwise say beside Figure 3B that this study measures qualification only. Do not splice the historical latency into the new gate.
- **Scientific risk of edit:** MEDIUM — a new performance study has changed session conditions and needs a valid matched baseline; a disclosure-only note is LOW.

### CR-07 — Statistical units and conditional uncertainty

- **Severity:** P2 useful. **Reviewers:** 3/6 — R3, R5, R6. **Kind:** validity/interpretation; independently shared.
- **Affected PDF:** manuscript §§3.2, 5.2, 7.3 and §9, pp. 3, 5, 8–10; appendix §§H–J, pp. 5–6.
- **Exact problem:** Three repetitions on 24 B570 prompts yield 72 deterministic sequence checks, not 72 independent tasks or a population failure-rate estimate; M4 prompt-bootstrap intervals condition on sampled prompts, selected policy, and session, without covering all runtime or recalibration variation.
- **Why it matters:** Replication supports a finite-set strict endpoint and stability, but could be mistaken for a larger diversity sample or broader uncertainty bound.
- **Localized fix:** State together “24 prompts, four reference-divergent prompts, 72 repeat-stable executions, 12 divergent pairs,” and add one sentence that repeats do not triple task diversity. Put a concise conditional-CI note near the Guard result and preserve its post-study status.
- **Scientific risk of edit:** LOW — interpretation of existing estimands.

### CR-08 — B570 exposure audit inspectability

- **Severity:** P2 useful. **Reviewers:** 2/6 — R3, R5. **Kind:** validity/provenance; independently shared.
- **Affected PDF:** manuscript §3.1 p. 3; appendix §J p. 6.
- **Exact problem:** The 31/164 exclusions, selection rule, and “no known exposure” boundary are described, but the audited exclusion inventory is not exposed in the PDFs; unknown records cannot be excluded.
- **Why it matters:** Reservation independence rests on a recorded-exposure audit and should be inspectable without implying universal absence of prior execution.
- **Localized fix:** Add a compact inventory or supplement pointer listing excluded task IDs and the audit criterion/version; retain “no known exposure in audited records.” Place the hash-selection rule and 24 reserved IDs beside the chronology in CR-01.
- **Scientific risk of edit:** MEDIUM — inventory reconciliation could reveal an exposure classification error.

## Significance and comparative interpretation

### CR-09 — Foreground the predictive contribution and case-study scope

- **Severity:** P1 important. **Reviewers:** 6/6 — R1, R2, R3, R4, R5, R6. **Kind:** significance/framing; independently shared.
- **Affected PDF:** title, abstract, introduction and contribution list p. 1; conclusion/§9 p. 10.
- **Exact problem:** “Consumer systems” and a dense four-platform opening can suggest a matched hardware benchmark or broadly portable method. The strongest new result is the prospective B570 complete-trajectory prediction, while campaign software, quantization, comparator, and sessions differ.
- **Why it matters:** The first-page promise sets the acceptance test and can overstate generality despite later caveats.
- **Localized fix:** Lead the abstract and first-page contributions with the frozen B570 prediction and its tested-stack scope, then summarize fresh direct-ID gates and the separate 358H cost case. Call the four systems independently frozen, configuration-specific case studies; place the old text-comparator warning next to legacy speedups. Preserve the negative Guard/fixed result even if moving numerical detail to §7.
- **Scientific risk of edit:** LOW — narrative ordering and explicit scope, provided no endpoint changes.

### CR-10 — Differentiate close prior art at the actual novelty boundary

- **Severity:** P1 important. **Reviewers:** 4/6 — R2, R3, R4, R5. **Kind:** significance/novelty; independently shared.
- **Affected PDF:** introduction p. 1 and related work §8 pp. 9–10.
- **Exact problem:** Correctness gating, batch-shape-dependent greedy outputs, cost/commit accounting, heterogeneous placement, and adaptive control are already credited to prior work; a broad qualification-and-cost prescription by itself can sound like rediscovery.
- **Why it matters:** The paper's incremental systems advance is the precommitted complete serialized-output prediction on a held-out B570 set, with separate direct-ID qualification and realized interface measurement.
- **Localized fix:** Add a concise comparison paragraph or grid against the closest cited consumer/correctness and cost studies, with columns for comparator, prospective reserved trajectory prediction, and integrated cost boundary. State the present distinct endpoint without claiming first discovery of numerical path dependence or a novel cost identity; an early one-sentence signpost can point to §8.
- **Scientific risk of edit:** MEDIUM — priority claims require exact characterization of cited work; the synthesis here uses only the PDFs' descriptions.

### CR-11 — M4 Guard's adverse fixed-policy comparison

- **Severity:** P1 important. **Reviewers:** 6/6 — R1, R2, R3, R4, R5, R6. **Kind:** significance/comparison; independently shared concern, with explicit edits from R3–R6.
- **Affected PDF:** abstract p. 1; manuscript §7/Table 3 pp. 7–9; appendix §H p. 5.
- **Exact problem:** Guard is 1.3114× faster than target-only but Always-Spec is 1.3469×, and the post-study paired Guard/Always-Spec latency ratio is 1.0271 [1.0130, 1.0436]. Guard's target-only gain does not show incremental policy benefit; the failed 358H intervention likewise supplies no new qualified performance gain.
- **Why it matters:** A profitable exact policy is a feasibility endpoint, not evidence that its control decision improves deployment against a fixed policy or advanced serving controllers.
- **Localized fix:** In §7's opening, Table 3, abstract/conclusion summaries, keep both target-relative gains and the adverse paired comparison adjacent. Label ratio direction, post-study secondary status, prompt/session-conditioned CI, offline oracle as hindsight, and lack of transfer/serving-controller comparison. Do not promote fallback frequency to decision quality.
- **Scientific risk of edit:** LOW — the numerical contrast is already reported; the edit changes emphasis.

### CR-12 — 358H measured interface versus hypothesized persistence gain

- **Severity:** P1 important. **Reviewers:** 4/6 — R1, R2, R3, R4. **Kind:** validity/significance; independently shared concern. R5 separately requests a figure label (CR-18).
- **Affected PDF:** manuscript §§5.3, 7.1, 9 pp. 6–8, 10; Figure 4 p. 8; appendix §D p. 1.
- **Exact problem:** The synchronous NPU timed region combines full-prefix replay/reconstruction and proposal. The isolated throughput comparison uses a different boundary, and the later persistence/widened-target candidate stopped on qualification before formal timing. Replay-only cost and recovery from a better interface are unmeasured.
- **Why it matters:** A measured expensive interface does not establish intrinsic NPU inability or the causal speed benefit of a persistent-state design.
- **Localized fix:** Consistently call the region “full-prefix replay/reconstruction plus proposal”; state that its components are inseparable and the intervention has no qualified speed endpoint. A new claim about recovered time requires a separately qualified, matched intervention and complete loop timing, not subtraction of incompatible measurements.
- **Scientific risk of edit:** LOW for wording; HIGH for a new intervention that may fail the gate or change the cost conclusion.

### CR-13 — Practitioner iteration cost illustration

- **Severity:** P3 polish. **Reviewers:** 1/6 — R1 only. **Kind:** significance/practical use; single-reviewer idea.
- **Affected PDF:** manuscript §6 pp. 6–7.
- **Exact problem:** The proposed qualification → partition probe → realized-cost sequence gives no concrete indication of its evaluation cost.
- **Why it matters:** A bounded time/iteration illustration would make the procedure easier to operationalize without claiming universal efficiency.
- **Localized fix:** Add one short, configuration-specific worked tally of the actual gate and target-only probe runs or wall-clock evaluation budget if recorded; label excluded setup and avoid extrapolating to production.
- **Scientific risk of edit:** MEDIUM — an unmeasured time budget should not be invented; a run-count illustration is LOW.

## Figures, tables, and reading path

### CR-14 — Show the B570 discovery-to-prediction sequence directly

- **Severity:** P2 useful. **Reviewers:** 3/6 — R2, R4, R5. **Kind:** significance/clarity; independently shared.
- **Affected PDF:** manuscript §§3.1, 5.2 pp. 3, 5; conceptual Figure 2 p. 6; appendix §J p. 6.
- **Exact problem:** The central novelty is procedural and outcome-predictive, but the main visual space is occupied by a generic evaluation pipeline; chronology and informative divergent cases remain mostly prose/appendix.
- **Why it matters:** A reader should see how exposed discovery (36/36), frozen H1 and 72 arrays, then live reserved comparison (72/72, including 12 divergent pairs) differ from post hoc explanation.
- **Localized fix:** Add a compact timeline/table with the freeze boundary and one complete divergent reference/predicted/live token-sequence example, keyed to the CR-01 ledger. Do not imply the reserve was chosen after outcomes.
- **Scientific risk of edit:** LOW, provided the timeline follows recorded chronology.

### CR-15 — Figure 2 density and role

- **Severity:** P2 useful. **Reviewers:** 6/6 — R1, R2, R3, R4, R5, R6. **Kind:** clarity/space; independently shared.
- **Affected PDF:** manuscript Figure 2 and caption p. 6.
- **Exact problem:** Dense boxes and caption repeat §§2/6, and arrows may suggest a deterministic intervention chain between B570, 358H, and M4 even though these are independent cases.
- **Why it matters:** The organizing figure may consume space needed for the predictive evidence and blur the separation of diagnoses.
- **Localized fix:** Simplify text and caption, make the qualification versus cost boundaries explicit, and visually separate B570 prediction from 358H interface measurement. Keep the non-exhaustive, configuration-scoped caveat.
- **Scientific risk of edit:** LOW.
- **CONFLICT (placement):** R1/R3/R6 favor simplifying a useful main-text map; R4 regards it as the most expendable main figure; R5 suggests compression or appendix placement to free space; R2 suggests reallocating space to a B570 prediction diagram. Preserve both layout options for author choice.

### CR-16 — Figure 3 historical/prospective separation

- **Severity:** P2 useful. **Reviewers:** 6/6 — R1, R2, R3, R4, R5, R6. **Kind:** validity/clarity; independently shared.
- **Affected PDF:** manuscript Figure 3 pp. 7; appendix Table A3 p. 3 and Table A5 p. 6.
- **Exact problem:** Historical target-forward proxy cells in panel A sit beside fresh direct-ID qualification in panel B, inviting a same-run cost/correctness or hardware-frontier reading. Panel A's small context cells require appendix lookup.
- **Why it matters:** The panels use distinct contexts, sessions, and endpoints and cannot establish a cost/qualification tradeoff for one intervention.
- **Localized fix:** Put “historical proxy, different runs/contexts” and “fresh direct-ID gate, no latency endpoint” directly in the panels, strengthen the separating gutter or headers, and label panel A values/contexts where legible. Keep the caption's incompatibility statement and Table A3 lookup.
- **Scientific risk of edit:** LOW.

### CR-17 — Highlight gate status in Table 2 and Table A5

- **Severity:** P2 useful. **Reviewers:** 2/6 — R3, R4. **Kind:** validity/visual emphasis; independently shared observation, explicit shading proposal from R3.
- **Affected PDF:** manuscript Table 2 p. 4; appendix Table A5 p. 6.
- **Exact problem:** B570's precise 0.3087× diagnostic CI appears among admissible speedups; a skimmer may miss “Diag.” and infer a valid optimization result.
- **Why it matters:** An uncertainty interval cannot rescue a correctness-blocked path.
- **Localized fix:** Give blocked/diagnostic rows a visible status treatment or a small “blocked; timing diagnostic” label in the row, while retaining numerical measurements and the explicit A5 gate.
- **Scientific risk of edit:** LOW.

### CR-18 — Direct Figure 4 region and estimator labels

- **Severity:** P2 useful. **Reviewers:** 3/6 — R3, R4, R5. **Kind:** validity/clarity; independently shared.
- **Affected PDF:** manuscript Figure 4 p. 8 and §5.3 p. 6.
- **Exact problem:** The NPU colored share can be mistaken for replay alone, and arithmetic-mean stacked bars can be conflated with prompt-geometric-mean headline speedups; the caption has the necessary caveats but the panel bears little of them.
- **Why it matters:** This can turn one inseparable measured call into a quantified replay penalty or make mean bars appear to reconstruct the headline estimator.
- **Localized fix:** Label the bar itself “replay + proposal (inseparable)” and the totals “arithmetic mean”; retain a nearby note that 0.734×/0.352× use prompt geometric means and isolated throughput has a different boundary.
- **Scientific risk of edit:** LOW.

### CR-19 — Put detailed new direct-ID gate counts closer to Figure 3B

- **Severity:** P2 useful. **Reviewers:** 1/6 — R3 only. **Kind:** clarity; single-reviewer idea.
- **Affected PDF:** manuscript Figure 3B p. 7; appendix Table A5 p. 6.
- **Exact problem:** Main Figure 3B shows the qualification gate, but the compact path-by-path exact-prompt counts and comparator table reside in the appendix.
- **Why it matters:** The primary methodological separation could be understood faster without flipping to A5.
- **Localized fix:** Move or replicate A5's four-row gate table beside Figure 3B if space permits, or add exact-prompt counts to its direct labels; keep qualification-only status explicit.
- **Scientific risk of edit:** LOW.

### CR-20 — Table 1 scope note

- **Severity:** P2 useful. **Reviewers:** 3/6 — R3, R4, R5. **Kind:** scope/clarity; independently shared.
- **Affected PDF:** manuscript Table 1 p. 4.
- **Exact problem:** Its terse evidence-scope cells and hardware list can be skimmed as a matched hardware comparison, although software, quantization, contexts, and comparators co-vary.
- **Why it matters:** Device rankings are unsupported by the separate campaigns.
- **Localized fix:** Add a compact note stating “independently frozen case studies; not a matched hardware comparison” and the common greedy width/token cap where applicable, while flagging the distinct fresh-study contexts/comparators and 358H draft quantization.
- **Scientific risk of edit:** LOW.

### CR-21 — Appendix A4 redundancy and reuse of space

- **Severity:** P3 polish. **Reviewers:** 2/6 — R2, R5. **Kind:** clarity/space; independently shared.
- **Affected PDF:** appendix Table A4 p. 4 and §J p. 6.
- **Exact problem:** A4 substantially repeats manuscript Table 2 and Figure 2, while the prediction protocol/ledger needs more inspectable space.
- **Why it matters:** Appendix area can prioritize unique validation evidence once the comparator labels in CR-05 are repaired.
- **Localized fix:** Compress A4 to an evidence-class key with explicit comparators, or relocate the repeated rows, and spend saved space on CR-01/CR-14 material.
- **Scientific risk of edit:** LOW, if no distinct evidence-class information is lost.

### CR-22 — Figure 1 and Figure 4 caption length

- **Severity:** P3 polish. **Reviewers:** 1/6 — R5 only. **Kind:** writing; single-reviewer idea.
- **Affected PDF:** manuscript Figures 1 and 4, pp. 5, 8.
- **Exact problem:** Long captions carry estimator and boundary definitions already scattered across methods, reducing scanability.
- **Why it matters:** Essential qualifications are easier to find in a shared legend/nearby text and compact captions.
- **Localized fix:** Put repeated estimator/boundary definitions in a concise reader-facing methods key, then shorten these captions while preserving the noncausal M4 session caveat and Figure 4's inseparable call, mean-versus-GM, and excluded-prefill notes.
- **Scientific risk of edit:** LOW, provided caveats remain adjacent to figures.

## Suggested ordering

First repair the central prediction record and comparator labels (CR-01, CR-05), sharpen its scope and contribution (CR-03, CR-04, CR-09, CR-10), and make existing comparisons explicit (CR-02, CR-11, CR-12). Figure and appendix edits can then use the same precise endpoint vocabulary. New backend and state-persistence experiments would materially enlarge the paper, but the current PDF claims should remain bounded if they are not conducted.
