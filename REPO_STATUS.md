# Repository status

Status as of 2026-09-08, based on `main` at `1012d3f5` after repository consolidation and Windows paper-critical raw-provenance archival.

## Completed and merged

- Windows 275HX + RTX 5070 Ti platform closure, including the 60Q pilot, root-cause controls, 14B capacity/crossover work, component power study, matched HumanEval replication, exact-verification microbenchmark, CUDA divergence diagnosis, and paper-critical raw provenance.
- MacBook Air M4 platform closure, including portability/correctness gates, the 12Q decision study, mechanism controls, the frozen 24Q representative confirmation, and the preregistered 30-prompt HumanEval code-conditioned study.
- Publication-sized M4 HumanEval archive: 30 frozen prompts, authoritative run record, authoritative raw power trace, manifest/checksums, processed summaries, reports, and figures.
- Publication-sized Windows raw archives for the HumanEval replication, exact-verification mechanism, and CUDA divergence diagnosis, each with manifests and SHA-256 integrity metadata.
- Repository-wide documentation consolidation, including the unified verification-amortization framework and the cross-platform correctness-constrained mechanism interpretation.
- Cross-platform conclusion: acceptance alone does not determine profitability; cheap verification counts only when the cheap execution path also satisfies the token-exactness gate.

The authoritative M4 evidence map is `reports/m4/M4_EXPERIMENT_INDEX.md`. The Windows closure is `reports/5070ti/FINAL_5070TI_PLATFORM_REPORT.md`. Paper-critical raw archives are under `artifacts/` and governed by `docs/data_policy.md`.

## Pending or deliberately incomplete

- Core Ultra X7 358H measurements have not been run or reported.
- The M4 HumanEval preregistration's **corrected synthetic ceiling** has no completion artifact matching its frozen design (conditional probabilities 0.6/0.7/0.8/0.9/0.95/1.0 mapped to `p,p^2`, five repetitions, 128 output tokens, seed 20260911). The tracked earlier synthetic crossover is a different exploratory diagnostic and does not satisfy this item. This is a preregistration deviation/status gap, not a completed result; no new M4 experiment is authorized by the current closeout.
- HumanEval generated code was not functionally executed; “exact” means paired greedy token-ID equality.

## Data boundaries

Model weights, downloaded benchmark datasets, caches, virtual environments, credentials, machine profiles, build products, and most bulk/local runs remain excluded. Explicit paper-critical raw archives are retained for M4 HumanEval and for the Windows HumanEval replication, verification mechanism, and CUDA divergence diagnosis. Redundant server logs and smoke runs remain excluded when they contain no evidence beyond the archived authoritative payloads. Historical local paths in data records are provenance, not portable commands.

## Remaining before public release

- Choose and install a real license; `LICENSE_PLACEHOLDER.md` is not a release license.
- Finalize authors and identifiers in `CITATION.cff`.
- Decide whether local-path provenance fields need redaction or documented acceptance for the public archive.
- Run the security, large-file, link, and generated-artifact checks again on the exact release candidate.
- Add paper/arXiv, DOI, and archival-release metadata only when they exist.

## Remote and branch policy

Private GitHub repository: `https://github.com/leecdiang/HeteroSpec`. Completed platform results, repository consolidation, and the Windows raw-provenance archive are merged to `main`. Future platform work, including 358H, should use dedicated branches and be reviewed before merging.
