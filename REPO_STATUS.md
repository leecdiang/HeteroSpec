# Repository status

Status as of 2026-09-18 on the 358H closeout branch. The 358H scientific campaign is complete; merge remains gated on final branch reconciliation and review.

## Completed and merged

- Windows 275HX + RTX 5070 Ti platform closure, including the 60Q pilot, root-cause controls, 14B capacity/crossover work, component power study, matched HumanEval replication, exact-verification microbenchmark, CUDA divergence diagnosis, and paper-critical raw provenance.
- MacBook Air M4 platform closure, including portability/correctness gates, the 12Q decision study, mechanism controls, the frozen 24Q representative confirmation, and the preregistered 30-prompt HumanEval code-conditioned study.
- Arc B570 Vulkan backend-control closure, including environment and board-power qualification, formal correctness failure, full HumanEval30 post-gate diagnostics, the single serialized fallback validation, clean verification measurements, board-energy data, and paper-critical provenance.
- Publication-sized M4 HumanEval archive: 30 frozen prompts, authoritative run record, authoritative raw power trace, manifest/checksums, processed summaries, reports, and figures.
- Publication-sized Windows raw archives for the HumanEval replication, exact-verification mechanism, and CUDA divergence diagnosis, each with manifests and SHA-256 integrity metadata.
- Publication-sized B570 archives for the formal correctness gate, diagnostic extension, and exact-fallback validation. B570 paper-critical files are stored with Git text conversion disabled and the committed Git blobs were audited against manifest size/SHA256 entries.
- Repository-wide documentation consolidation, including the unified verification-amortization framework and the cross-platform correctness-constrained mechanism interpretation.
- Cross-platform conclusion: acceptance alone does not determine profitability; cheap verification counts only when the cheap execution path also satisfies the token-exactness gate.

The authoritative M4 evidence map is `reports/m4/M4_EXPERIMENT_INDEX.md`. The Windows closure is `reports/5070ti/FINAL_5070TI_PLATFORM_REPORT.md`. The B570 closure is `reports/b570/B570_PLATFORM_CLOSEOUT.md`. Paper-critical raw archives are under `artifacts/` and governed by `docs/data_policy.md`.

## Completed on the 358H closeout branch

- Core Ultra X7 358H Phase 0–3: frozen canonical/reconstructed draft provenance, explicit CPU/GPU/NPU qualification, isolated CPU/NPU draft characterization, predictive break-even gate, and formal HumanEval30 end-to-end validation.
- Phase-3 result: CPU draft 0.734x [0.693, 0.771] and NPU draft 0.352x [0.333, 0.369], with 90/90 token-exact pairs per path and 0/30 prompts faster.
- A byte-complete compressed evidence artifact preserves all 34 original manifest entries. The earlier approximately-80-KiB text transfers are non-authoritative previews; see `reports/358h/358H_REPOSITORY_CLOSEOUT_AUDIT.md`.

## Pending or deliberately incomplete

- The M4 HumanEval preregistration's **corrected synthetic ceiling** has no completion artifact matching its frozen design (conditional probabilities 0.6/0.7/0.8/0.9/0.95/1.0 mapped to `p,p^2`, five repetitions, 128 output tokens, seed 20260911). The tracked earlier synthetic crossover is a different exploratory diagnostic and does not satisfy this item. This is a preregistration deviation/status gap, not a completed result; no new M4 experiment is authorized by the current closeout.
- HumanEval generated code was not functionally executed; “exact” means paired greedy token-ID equality.

## 358H closeout status

The preregistered sequence completed without post-result parameter search. CPU and NPU used the same frozen OpenVINO draft semantics; the target was explicitly bound to Vulkan0. The scientific execution is closed as correctness-admissible and not profitable. Formal-start host-state and interactive-monitoring disclosures are in `reports/358h/358H_FORMAL_EXECUTION_AMENDMENT.md`; repository transport recovery is in `reports/358h/358H_REPOSITORY_CLOSEOUT_AUDIT.md`.

## Data boundaries

Model weights, downloaded benchmark datasets, caches, virtual environments, credentials, machine profiles, build products, and most bulk/local runs remain excluded. Explicit paper-critical raw archives are retained for M4 HumanEval, Windows HumanEval/verification/divergence, and B570 backend-control evidence. Redundant server logs and smoke runs remain excluded when they contain no evidence beyond the archived authoritative payloads. Historical local paths in data records are provenance, not portable commands.

## Remaining before public release

- Choose and install a real license; `LICENSE_PLACEHOLDER.md` is not a release license.
- Finalize authors and identifiers in `CITATION.cff`.
- Decide whether local-path provenance fields need redaction or documented acceptance for the public archive.
- Run the security, large-file, link, and generated-artifact checks again on the exact release candidate.
- Add paper/arXiv, DOI, and archival-release metadata only when they exist.

## Remote and branch policy

Private GitHub repository: `https://github.com/leecdiang/HeteroSpec`. Completed 275HX/RTX, M4, and B570 platform results are merged to `main`. The completed 358H result remains on its dedicated closeout branch pending reconciliation with `main` and final review. Any follow-up optimization study must use a new preregistration rather than extending the closed campaign.
