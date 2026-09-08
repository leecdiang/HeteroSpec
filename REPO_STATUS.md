# Repository status

Status as of 2026-09-08, based on `main` at `9d825b6` before repository consolidation.

## Completed and merged

- Windows 275HX + RTX 5070 Ti platform closure, including the 60Q pilot, root-cause controls, 14B capacity/crossover work, component power study, matched HumanEval replication, exact-verification microbenchmark, and CUDA divergence diagnosis.
- MacBook Air M4 platform closure, including portability/correctness gates, the 12Q decision study, mechanism controls, the frozen 24Q representative confirmation, and the preregistered 30-prompt HumanEval code-conditioned study.
- Publication-sized M4 HumanEval archive: 30 frozen prompts, authoritative run record, authoritative raw power trace, manifest/checksums, processed summaries, reports, and figures.
- Cross-platform conclusion: acceptance alone does not determine profitability; cheap verification counts only when the cheap execution path also satisfies the token-exactness gate.

The authoritative M4 evidence map is `reports/m4/M4_EXPERIMENT_INDEX.md`. The Windows closure is `reports/5070ti/FINAL_5070TI_PLATFORM_REPORT.md`.

## Pending or deliberately incomplete

- Core Ultra X7 358H measurements have not been run or reported.
- The M4 HumanEval preregistration's **corrected synthetic ceiling** has no completion artifact matching its frozen design (conditional probabilities 0.6/0.7/0.8/0.9/0.95/1.0 mapped to `p,p^2`, five repetitions, 128 output tokens, seed 20260911). The tracked earlier synthetic crossover is a different diagnostic and does not satisfy this item. This is a preregistration deviation/status gap, not a completed result; no new experiment is authorized by this consolidation.
- HumanEval generated code was not functionally executed; “exact” means paired greedy token-ID equality.

## Data boundaries

Model weights, downloaded benchmark datasets, caches, virtual environments, credentials, machine profiles, and most raw/local runs remain excluded. The tracked M4 HumanEval archive is an explicit exception because it is the authoritative, publication-sized evidence package. Historical local paths in data records are provenance, not portable commands.

## Remaining before public release

- Choose and install a real license; `LICENSE_PLACEHOLDER.md` is not a release license.
- Finalize authors and identifiers in `CITATION.cff`.
- Decide whether local-path provenance fields need redaction or documented acceptance for the public archive.
- Run the security, large-file, link, and generated-artifact checks again on the exact release candidate.
- Add paper/arXiv, DOI, and archival-release metadata only when they exist.

## Remote and branch policy

Private GitHub repository: `https://github.com/leecdiang/HeteroSpec`. Platform results were merged to `main`; consolidation work is performed on `repo/consolidation-2026-09` and must be reviewed through a pull request rather than merged automatically.
