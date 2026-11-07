# RTX repair-scope transfer: registered design and CPU tools

**2026-10-29 host update:** the new worker and both source cohorts are built,
resident resource admission passed, and both families passed their 98-request
numerical qualification (196 total). SmolLM2 required a CPU-only correction for
an already observed tensor-name alias; the original refusal and unchanged raw
data hashes are preserved in [AUDIT_METADATA_CORRECTION.md](AUDIT_METADATA_CORRECTION.md).
See [HOST_EXECUTION.md](HOST_EXECUTION.md) and `host_execution/` for current host
evidence. The text below records the original design-only submission; its
`NOT_RUN`/extension statements do not describe subsequent execution receipts.
Three-date performance collection and the separate Llama stream remain pending.

**Status: design/work package only. No new native requests, no new performance results, no compiled or qualified worker.** Stack this PR on `windows/rtx-native-delivery-20261026` at `9149b6f5f5a4dcde1b6124c654dc0ba1241ca509` (PR149).

This study asks whether the net value of drafting changes between global serialization and attention-local repair on the **fixed, already exposed PR144 transfer panel**, and whether its direction persists on three actual dates. Qwen3 and SmolLM2 form the factorial study. A separate, bounded Llama diagnostic retains the known failure and two controls; it does not need to produce a fix.

## What this PR implements

The standard-library-only `scripts/experiments/rtx_scope_transfer_v1/study.py` extracts the exact pinned native prompt IDs and model identities, constructs deterministic seven-arm paired schedules, checks the design, audits a documented future host record envelope, and computes date-weighted contrasts only for complete qualified cohorts. It also reconstructs the already recorded Llama endpoint counterexample. The auditor never imports a worker, compiles, downloads, launches a subprocess or runs a model.

The new ArmSpec worker, multi-family source routing, resident GS/R contexts, expanded observer, and host adapter/runner are **not implemented or native-qualified here**. The existing bridge cannot consume the new schedule unchanged. `HOST_HANDOFF.md` identifies the exact source changes and admission steps. These omissions are execution gates, not commands that secretly fall back to an old experiment.

## Files

| File | Role |
|---|---|
| `PROTOCOL.md`, `PLAN.json` | Scientific design, estimands, budgets and stopping rules |
| `PANEL.json`, `MODEL_PINS.json`, `SOURCE_PINS.json` | Exact IDs, original source/member hashes and family identity routing |
| `SLOTS.jsonl` | 196 qualification, 1008 measurements and 84 explicit warmups |
| `DIAGNOSTIC_SLOTS.jsonl` | Llama A1=18 and A2=36, separate from performance |
| `RECORD_SCHEMA.md` | New normalized host contract; not an existing bridge format |
| `EXECUTION_IDENTITY_TEMPLATE.json` | Incomplete template; null fields must be bound before execution |
| `REFERENCE_REQUIREMENTS.json` | Historical R references still to retrieve; never replaced by new R |
| `A0_KNOWN_COUNTEREXAMPLE.json` | CPU reconstruction of the historical endpoint summary, with raw-data limits |
| `CPU_VALIDATION.json` | Synthetic CPU checks; not experiment data or native qualification |

## Implemented commands

Run from the repository root with Python 3.11+. These commands do not execute a model:

```bash
python -B scripts/experiments/rtx_scope_transfer_v1/study.py check-plan
python -B scripts/experiments/rtx_scope_transfer_v1/test_cpu.py
```

To re-extract from an existing, hash-verified PR144 checkout, pass its actual files. No download or native tokenization occurs:

```bash
python -B scripts/experiments/rtx_scope_transfer_v1/study.py prepare --manifest /path/to/PR144/INPUT_MANIFEST.json --model-contract /path/to/PR144/results/MODEL_CONTRACT.json
python -B scripts/experiments/rtx_scope_transfer_v1/study.py inspect-known-counterexample --source /path/to/PR144/results/COUNTEREXAMPLES.json --out /path/to/a0_endpoint_check.json
```

After the **new host worker/adapter has been implemented, compiled and qualified**, its retained bundle can be checked without a GPU:

```bash
python -B scripts/experiments/rtx_scope_transfer_v1/study.py audit --bundle /path/to/retained_bundle --out /path/to/AUDIT.json
python -B scripts/experiments/rtx_scope_transfer_v1/study.py analyze --bundle /path/to/retained_bundle --out /path/to/ANALYSIS.json
```

Missing identity, reference, receipt or raw files produce explicit ineligibility and `qualified_performance: null`. Missing/failed arms are never filled or dropped to obtain a more favorable panel. A failed family's scientific result remains visible; another family can qualify only when its complete panel and all shared host/cleanup gates hold.

## Interpretive boundary

The panel is exposed, one host is studied, and domain/length are confounded in PR144. Three **Asia/Shanghai local dates** with two independent model-load sessions per date are three date units, not six or 1008 independent date observations. The date-level t interval is a weak sensitivity analysis. Llama A2 changes recipes inside fixed layouts and does not perform clean-receiver state transfer. Success, counterexample, runtime dependence and unresolved localization are all valid study outcomes.
