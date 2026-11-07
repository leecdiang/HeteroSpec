# Final RIGOR review - submission v0.7

This is an independent model reviewer simulation, not external human peer review. I inspected the actual `manuscript/output/manuscript-v0.7.pdf` (10 body pages plus one references page), the five-page `appendix-v0.7.pdf`, relevant manuscript source, both canonical formal analyses and preregistrations, capture/instrumentation contracts, original runner/verifier code, historical comparator audit, qualification scope and integration audit, both DIRECT_ID_*OFFLINE_V07 records, DIRECT_ID_INTEGRATION_QA_V07, and RUNTIME_QA_V07. Main PDF SHA-256: `da3c5c9951774880f2cc562ee767417d761a8aefcd686ba8e49e2002d3fa0670`; appendix: `afa4ab81d346c5764be43a24e7a58b43c117e2cbc65c872cf79d1421e3b7b15f`. I visually inspected the submitted Figure 3 page. I read the v0.5 MOCK_DECISION only after forming this assessment; no other v0.7 review was consulted. All work was offline; no inference, search, or experiment occurred.

## Reproducibility and contract assessment

The new qualification evidence has a materially stronger observation boundary than the historical text comparator. RTX native committed-token events expose actual integer IDs; prompt tokens and rejected proposals are excluded. B570 instrumentation appends accepted/replacement output IDs and runtime EOG flags without changing sampling or stopping. Its endpoint is the first 128 committed IDs or inclusive earlier EOG. Raw overshoot is retained, so this is a frozen finite-output contract rather than equality of every token the frontend happened to emit.

I independently checked both content-addressed archive hashes and all listed payload hashes in memory: 2,756 RTX payloads and 993 B570 payloads. I reconstructed RTX arrays from native logs and B570 arrays from raw sidecars, checked 270 unique executions per study, and recomputed all 180 comparisons per study. RTX produces 75/90 batched matches and 90/90 serialized matches, with 25/30 and 30/30 wholly exact prompts. B570 produces 60/90 fast and 78/90 serialized matches, with 20/30 and 26/30 prompts. Both use exactly the 90/90 gate; neither discards a mismatch or promotes a passing subset. All candidate conditions are repeat-stable on all 30 tasks. B570 has 129 records with raw overshoot, at most two extra IDs; the selected arrays agree with the archived endpoint arrays. These checks substantiate the reported contract, not independent real-world replication or historical execution chronology.

Both studies share one frozen 30-task HumanEval cohort, three repetitions, greedy fixed k=2, and one Qwen3 Q8_0 model pair. Three repetitions do not create 90 independent population samples; deterministic endpoint counts appropriately receive no population-rate confidence intervals. Protocol commonality is useful but incomplete: RTX uses the native embedded-server CLI, context 4096, and reference micro-batch one; B570 uses completion/speculative frontends, context 1024, and reference micro-batch 128. Consequently the counts cannot causally rank hardware or isolate a common numerical mechanism. The manuscript states that boundary prominently.

## Integrity versus inferential scope

I found no demonstrated integrity failure invalidating the narrow endpoints. RTX's incomplete v1 transport attempt is preserved and contributes no completed-v2 pair; a fresh freeze and full restart address observational byte transport. Fresh driver 616.92 differs from historical 616.56, so even unchanged upstream source would not certify old timing. B570's scheduled launch failed before inference with zero formal executions; the first data-producing launch used the unchanged frozen runner. This deployment deviation warrants disclosure, which the supplement provides, rather than treating it as selective rerunning after unfavorable outcomes.

Portable archive checks validate included records and frozen identities. They do not independently rehash omitted weights or runtime binaries or attest host chronology. Historical Windows provenance remains weaker. The M4 freeze-hash metadata recovery preserves erroneous markers and the stopped pipeline, making it auditable without pretending the original automated gate passed uninterrupted. The 358H source reconstruction and compact diagnostic limitations remain explicit.

The main methodological limitations are inferential: short outputs, one cohort/model family, one request at a time, session-conditioned intervals, and no functional code execution. Historical timing remains text-comparator scoped. The historical CUDA margin capture is a separate same-commit diagnostic; it cannot explain B570 or establish the new runs' precise kernel cause. State replay and proposal share one timed region, and the 358H intervention never reaches formal performance evaluation. These are limits to significance and transportability, not evidence falsification.

## Explicit deltas from the v0.5 decision

**A - Historical comparator:** Prospectively improved, not retroactively repaired. New direct-ID RTX qualification supplies a tested strict-contract alternative; historical RTX/M4 timing and B570 45/90 and 60/90 text counts retain their weaker representation.

**B - Common replication:** Substantially improved through shared tasks, models, k, repetitions, complete schedules, and direct-ID endpoints. Different contexts, references, and frontends still prevent a controlled cross-platform comparison.

**C - Remedy:** RTX serialization remedies qualification on its frozen path. B570 remains blocked. Neither qualification study establishes a performance remedy; the unevaluated 358H persistence intervention remains unchanged.

**D - Guard utility:** The previously missing paired contrast is now available: Guard/Always latency 1.027076, CI [1.012956, 1.043559]. This post-study secondary comparison supports higher Guard latency on the frozen workload. It does not establish universal harm, risk reduction, or controller utility; prospectively profitable execution against target-only remains valid.

**E - Significance:** The strict path-qualification characterization is stronger and more reproducible. Transferable prediction, architectural causality, and incremental controller benefit remain absent. Acceptance must rest on concrete empirical counterexamples and careful accounting.

## Recommendation and repairs

**Weak Accept, 4/6** (1 strong reject, 2 reject, 3 weak reject, 4 weak accept, 5 accept, 6 strong accept). **Confidence 4/5** in narrow validity; moderate confidence in the conference significance judgment. The added direct-ID replications make the characterization defensible from a rigor perspective, while an overall rejection for limited scientific reach remains reasonable. No submission-blocking integrity or contract error was found.

One nonblocking reproducibility repair: appendix Section I should explicitly list B570 reference micro-batch 128 and candidate micro-batches 128/1, alongside the already explicit RTX settings. The repository protocol supplies them, but these values determine the reference-relative contract and deserve visibility in the submitted supplement.
