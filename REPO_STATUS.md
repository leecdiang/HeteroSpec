# Repository status

Status as of 2026-09-13, based on `main` after Arc B570 backend-control closure, archival repair, and README consolidation.

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

## Pending or deliberately incomplete

- **Core Ultra X7 358H measurements have not been run or reported.** The platform is reserved for predictive draft-cost threshold validation across CPU, Xe3-class iGPU, and NPU. The onboarding and execution guide is `docs/358H_RUNBOOK.md`; the draft preregistration template is `benchmarks/358h_threshold_validation/preregistration_v1.json`.
- The M4 HumanEval preregistration's **corrected synthetic ceiling** has no completion artifact matching its frozen design (conditional probabilities 0.6/0.7/0.8/0.9/0.95/1.0 mapped to `p,p^2`, five repetitions, 128 output tokens, seed 20260911). The tracked earlier synthetic crossover is a different exploratory diagnostic and does not satisfy this item. This is a preregistration deviation/status gap, not a completed result; no new M4 experiment is authorized by the current closeout.
- HumanEval generated code was not functionally executed; “exact” means paired greedy token-ID equality.

## 358H onboarding status

The repository now defines the intended 358H study at the protocol level but deliberately does **not** invent unqualified runtime commands. Before formal measurement, the experimenter must complete Phase 0 qualification and fill all `FILL_*` fields in `benchmarks/358h_threshold_validation/preregistration_v1.json`, then commit that frozen preregistration before collecting formal data.

The planned sequence is:

1. explicit CPU / iGPU / NPU qualification;
2. same-draft-model latency characterization;
3. predictive break-even GO / BORDERLINE / NO-GO classification;
4. end-to-end `k=2` validation only for plausible paths;
5. archival closeout without post-result parameter search.

## Data boundaries

Model weights, downloaded benchmark datasets, caches, virtual environments, credentials, machine profiles, build products, and most bulk/local runs remain excluded. Explicit paper-critical raw archives are retained for M4 HumanEval, Windows HumanEval/verification/divergence, and B570 backend-control evidence. Redundant server logs and smoke runs remain excluded when they contain no evidence beyond the archived authoritative payloads. Historical local paths in data records are provenance, not portable commands.

## Remaining before public release

- Choose and install a real license; `LICENSE_PLACEHOLDER.md` is not a release license.
- Finalize authors and identifiers in `CITATION.cff`.
- Decide whether local-path provenance fields need redaction or documented acceptance for the public archive.
- Run the security, large-file, link, and generated-artifact checks again on the exact release candidate.
- Add paper/arXiv, DOI, and archival-release metadata only when they exist.

## Remote and branch policy

Private GitHub repository: `https://github.com/leecdiang/HeteroSpec`. Completed 275HX/RTX, M4, and B570 platform results are merged to `main`. Future 358H work should use a dedicated branch, preserve preregistration-before-result ordering, and be reviewed before merging.
