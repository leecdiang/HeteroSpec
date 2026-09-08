# Data policy

## Tracked evidence

Git stores source code, portable configuration, frozen benchmark IDs and preregistrations, processed tables, reports, figures, and small provenance records. It also stores one explicit authoritative raw-data exception: `artifacts/m4_humaneval_code_conditioned/`, containing the frozen 30 prompts, `results.json`, `telemetry.csv`, and a manifest with checksums and runtime metadata.

The exception is intentional: these files are required to audit the formal M4 HumanEval result and are small enough for the repository. Derived files in `analysis/` and `reports/m4/figures/` must remain traceable to that archive and the tracked summarizer.

## Excluded material

Do not commit model weights, downloaded benchmark datasets, Hugging Face caches, virtual environments, credentials, private keys, general machine profiles, build products, or machine-local run/log directories. Most historical raw telemetry and raw experiment runs remain local and ignored; reports must label when only processed evidence is available.

Absolute paths embedded in authoritative run records may be retained as provenance, but they are neither portable nor instructions. Review them for usernames or sensitive directory names before public release. Never copy secret values into audit reports.

## Measurement rules

- Never infer unavailable Intel power domains or sum overlapping domains as whole-system power.
- Keep Intel package and NVIDIA board energy separate unless a future measurement provides a validated non-overlapping whole-system boundary.
- Distinguish raw evidence, machine-readable summaries, and narrative interpretation.
- “Token-exact” means identical paired greedy token IDs; it does not imply HumanEval functional correctness.
- Failed correctness-gate timings are diagnostic only and cannot be promoted to admissible performance results.
- A preregistered item without a matching result artifact must be reported as incomplete or deviated, never reconstructed from a different diagnostic.

## Release process

Before publishing, verify dataset redistribution terms, model and runtime licenses, author metadata, local-path/privacy exposure, secrets, large files, generated-artifact provenance, and links. An absent public license means reuse rights have not yet been granted.

