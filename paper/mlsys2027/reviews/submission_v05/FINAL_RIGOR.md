# Final independent rigor review — revised v0.5

Review basis: the current main manuscript, all main sections and separate appendix; comparator scope addendum and submission provenance record; original runtime preregistration, calibration freeze, qualification report, formal report and recovery analyzer; original historical M4/Windows comparator code; and the compact 358H runtime diagnostic. I did not read other review reports. No manuscript or frozen evidence was edited.

## Verdict

The revision resolves the strongest presentation-level validity objections. It now states what was known historically, what was frozen prospectively, which comparator each campaign actually used, and what the provenance repair establishes. I find no demonstrated data-integrity failure that invalidates the narrow M4 prospective result. The major surviving scientific objection is contribution strength: the proposed continuation rule has not demonstrated incremental utility over the existing fixed speculative path, while the cross-platform observations are configuration-specific diagnoses rather than a controlled explanatory or predictive model. Honest scope makes this a defensible empirical case-study paper; it does not itself make the runtime intervention effective or the lessons general.

## Prospective versus historical knowledge

The manuscript explicitly says historical M4 outcomes informed the study design, and defines prospective as policy freezing before reserved-prompt outcomes. This is appropriate. The original preregistration fixes the eligibility inventory, seeded split, nine candidates, target reference, selection rule, direct-ID qualification and formal estimator. The freeze records all nine candidate scores and selects E8_M000 by the declared rule. Thus prior platform knowledge does not by itself invalidate held-out evaluation. The supported claim is conditional generalization to the reserved prompts under the chosen design, not discovery without historical knowledge or generalization across sessions/hardware.

The inventory can establish documented non-exposure, not prove absence of every historical exposure. The current wording (“no recorded prior M4 exposure”) and provenance limits acknowledge that distinction. I found no evidence warranting an allegation of held-out tuning.

## Comparator correction

This is a substantive correction, not cosmetic terminology. The historical code actually re-tokenizes parsed text: `m4_humaneval_code_conditioned.py` calls `tokenize` on `completion_text` before comparing arrays; `windows_humaneval_llama_replication.py` does the same. This cannot certify the intended direct generated-ID contract. The main framework, outcome wording, headline table, figure caption and appendix now state this distinction. The HumanEval prompt-in-parser issue is disclosed in the appendix. The correction appropriately neither invents new failures nor infers an unobserved direct-ID success rate.

Retaining “primary” classification is defensible only as the historical campaign status, not as equivalent strength of correctness evidence. The revised definition makes this explicit. The strict-contract rhetoric must continue to be read with this qualification: historical text agreement supports a weaker output-equivalence statement. Prospective direct-ID success cannot repair those historical records retrospectively. This is a permanent limitation of the evidence, now disclosed rather than hidden.

## Metadata defect and frozen evidence

The defect is real: the qualification record's intended freeze digest is the build-manifest digest. The recovery analyzer checks that all affected markers match this specific erroneous digest, checks qualification/observation identities, compares freeze and qualification bytes against the recorded clean formal-start commit, and rechecks source/model/calibration/policy constraints and complete attempts. I independently retrieved the two Git blobs at `202109717754bc62f889d19b5fbb141bfc3cc529`; their SHA-256 hashes match the submission record (freeze `3c179a35…`, qualification `abe0ba15…`). This supports consistency of the recovery explanation.

These are Git-object and archived-byte checks, not independent attestation of real-world chronology. The provenance record says so. Retaining original markers and STOPPED state is correct; the manuscript does not pretend the original gate passed uninterrupted. I see no basis to call the repair a measurement mutation. This review did not rerun models or independently recompute every raw observation, so this is an audit of the recovery logic and reported byte consistency, not fresh experimental replication.

The compact 358H diagnostic provides a bounded record of same-prefix divergence and proposal playback; hashes of absent traces are not substitutes for those traces. The appendix accurately retains the lack of local raw-trace replay and absence of formal R2 performance. No persistence speedup is inferred. Preserving numerical arrays and historical artifact bytes while correcting their interpretation is the right treatment of a frozen record.

## Major surviving objection

The original preregistration asks about lower held-out latency regret. The held-out result establishes exact, profitable execution versus target-only, but fixed speculation has the better aggregate estimate (1.3469× versus Guard's 1.3114×). Fallback frequency and closeness to an offline oracle do not show that fallback decisions improved performance. The manuscript now admits this repeatedly, so this is not a current overclaim; it is an unresolved scientific outcome. The guard may largely inherit fixed speculation's benefit while adding an unhelpful decision mechanism. A one-platform prospective implementation demonstration therefore supplies limited additional evidence beyond the case studies.

The strongest fair reviewer objection is: what new actionable intervention or transferable prediction does this work establish beyond showing, in selected stacks, that known numerical and state-management constraints matter? The 358H timing establishes a replay-plus-proposal region, not replay-only causality or the benefit of persistent state. The M4 study does not isolate workload from session effects. Hardware, runtime and quantization co-vary. These limitations are now accurately stated, but collectively restrict the contribution.

A direct paired Guard-versus-Always estimate on the already frozen prompt medians would sharpen the negative/control result without new measurement; it would not manufacture a positive contribution. Demonstrating beneficial control, persistence, or portability would require new evidence and belongs outside this frozen submission. Acceptance can reasonably turn on whether the documented empirical failures and qualification boundaries are sufficiently informative on their own, not on a claimed control improvement.

## Final assessment

No additional major hidden-validity objection was established in this re-review. Comparator strength remains permanently uneven, provenance is recovered rather than pristine, and the intervention lacks demonstrated incremental value. The revised paper presents those facts candidly. The remaining serious objection is scientific payoff and external validity, not an unsupported accusation of leakage or fabricated correctness.
