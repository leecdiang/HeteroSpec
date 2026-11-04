# Target-reference replay evidence prototype

Publication note: see [PUBLICATION_SCOPE.md](PUBLICATION_SCOPE.md). This directory is an additive PR183 delivery; preserved review-era “no PR modified” statements describe the investigation before publication. No existing worker/runtime file is changed.

Read DESIGN.md first. This is a read-only #183 design review plus CPU-only offline planning/auditing code. No GPU, user-device, or new neural inference was run. No PR was modified. A passing artifact audit is **not** GPU qualification.

Python 3.10+ standard library only. Run from this directory. Output paths must be fresh.

```sh
python test_replay_audit.py
python -O test_replay_audit.py
python make_artificial_example.py --output /tmp/fresh-artificial-demo
python replay_audit.py --trace /tmp/fresh-artificial-demo/trace.json \
  --identity /tmp/fresh-artificial-demo/identity.json \
  --output /tmp/fresh-artificial-demo/plan.json
python replay_audit.py --trace /tmp/fresh-artificial-demo/trace.json \
  --identity /tmp/fresh-artificial-demo/identity.json \
  --evidence /tmp/fresh-artificial-demo/evidence.json \
  --bundle /tmp/fresh-artificial-demo --output /tmp/fresh-artificial-demo/report.json
python estimate_budget.py --prompt-tokens 512 --output-cap 128 --output /tmp/fresh-budget.json
python inspect_existing_journals.py --fixture-root /path/to/pinned/pr183/experiments/draft_ubatch_probe \
  --output /tmp/fresh-existing-journal-plan.json
```

The last command reads existing `evidence/{release-dense,release-q8,stress-dense,stress-q8}-attempts.jsonl` and matching receipts (or the original local native.stdout directory layout). It requires every published STARTED to match its COMPLETED result in order. They are not bundled as new results. Its explicitly incomplete identity makes such plans ineligible for an evidence match. The artificial demo is labeled CPU_SYNTHETIC_BYTE_FIXTURE_ONLY and uses token integers as fake KV, not actual model state.

Files:
- DESIGN.md: source-cited protocol, state/pending semantics, exact-reference boundaries, resource estimates, tiered evidence and failure gates.
- replay_audit.py: immutable-prefix plan + offline raw-byte/metadata consistency checks.
- test_replay_audit.py: artificial adversarial tests; no neural engine.
- make_artificial_example.py: regenerate labeled fake byte payloads and schema example.
- inspect_existing_journals.py / journal_plan_published.json: planning counts from frozen #183 CPU reports.
- estimate_budget.py / budget_v2.json: arithmetic scenarios, not timing or mandatory storage.
- VALIDATION.json / PACKAGE_HASHES.json: exact local test and source/artifact identities.

Status names are intentionally limited. `PLAN_ONLY_NOT_QUALIFICATION` is a plan. `RECORDED_EVIDENCE_MATCH` verifies only available byte evidence and internally consistent metadata. Its `gpu_qualification_established` remains false even with all fields supplied. A native bridge, producer/extractor attestation, reference lifecycle qualification, device/JIT binding and observer-effect checks are still required.

The current payload counter counts every successful logical payload read, including repeated references, job observations and frontier logits. It is neither unique retained disk bytes nor measured operating-system disk IO. Chunked native capture/content-addressed KV retention described in DESIGN.md is a future implementation, not claimed as already built.

Independent review is retained under independent/, including executable historical counterexamples clearly marked as superseded. Re-run the final independent checker with `python -O independent/check_audit.py --audit-dir . --output /tmp/fresh-independent.json`. It checks 408 artificial mixed-branch/recipe/EOG cases and 24 further malformed-evidence mutations. The package rerun matched the independent RESULT.json byte-for-byte. These are still synthetic offline evidence tests, not native replay or GPU tests.
