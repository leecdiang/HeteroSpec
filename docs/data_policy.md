# Data policy

## Tracked evidence

Git stores source code, portable configuration, frozen benchmark IDs and preregistrations, processed tables, reports, figures, and small provenance records. It also stores a bounded set of explicit paper-critical raw-data archives:

- `artifacts/m4_humaneval_code_conditioned/` — frozen 30-prompt HumanEval inputs, authoritative `results.json`, raw `telemetry.csv`, and a manifest with checksums and runtime metadata.
- `artifacts/windows_humaneval_replication/` — authoritative raw JSON for the exact `ubatch=1` HumanEval replication, the correctness-aborted `ubatch=2` attempt, and their supporting NVML telemetry.
- `artifacts/windows_verification_mechanism/` — the raw exact-verification microbenchmark used to derive the Windows verification-amortization ratios.
- `artifacts/windows_cuda_divergence/` — the raw minimum-reproduction and logit-capture payloads plus supporting telemetry for the stable CUDA divergence diagnosis.

These archives are intentional exceptions because they directly support paper-critical claims and are small enough to retain in the repository. Their manifests record file sizes, SHA-256 hashes, classifications, derived outputs, and deliberate exclusions. Derived files in `analysis/` and `reports/` must remain traceable to these archives or to other explicitly indexed historical evidence.

## Excluded material

Do not commit model weights, downloaded benchmark datasets, Hugging Face caches, virtual environments, credentials, private keys, general machine profiles, build products, or bulk machine-local run/log directories. Most historical raw telemetry and raw experiment runs remain local and ignored. Redundant server stdout/stderr, smoke runs, caches, model files, runtime binaries, and debug build products remain excluded unless they contain evidence that cannot be reconstructed from an authoritative archived payload.

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
