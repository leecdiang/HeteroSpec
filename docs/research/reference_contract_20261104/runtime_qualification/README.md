# Runtime qualification: conditional design and CPU reproductions

This directory contains a reviewed design, not an enabled native fast path. It adds no runtime code. All executable examples here are Python CPU abstractions; they do not run llama.cpp, CUDA, a model, or user hardware. No throughput or acceptance-probability result is claimed.

## Read first

- [Chinese integration summary](INTEGRATION_SUMMARY_ZH_20261104.md).
- [Conditional design, source audit, theorem and test plan](RUNTIME_QUALIFICATION_AND_COMMITTED_STATE_20261104.md).
- [Independent adversarial review](independent/INDEPENDENT_REVIEW_20261104.md) and [portable reproductions](independent/README.md).

The central proposal is qualified pure projection batching plus per-query KV insertion and unchanged scalar attention, protected by owned zero-tail storage, complete execution planning, reader exclusion and atomic publication. Kernel equivalence, compiled write frames, native integration, asynchronous completion and actual speedup remain open obligations. The original unqualified production gate must remain closed.

## Reproduce the primary abstraction

Requires Python 3.10+ without `-O` (assertions are checks) and only its standard library. Run from the repository root:

```sh
D=docs/research/reference_contract_20261104/runtime_qualification
python "$D/check_transaction_model.py"
python -m py_compile "$D/check_transaction_model.py" "$D/verify_source_manifest.py"
```

Compare the JSON with [transaction_model_results.json](transaction_model_results.json): 54 successful schedule/full-state comparisons, 648 abort points, 648 guard rejections and five deliberately reproduced counterexamples.

The model imports pure projection equivalence. It assumes no observers during a transaction and immediate known completion. Its whole-array equality tests are ghost checks, not a proposed runtime scan. It does not implement or verify linearizability, CUDA arithmetic, the native scheduler, or universal attention equivalence.

## Reproduce the independent review

```sh
D=docs/research/reference_contract_20261104/runtime_qualification
python "$D/independent/review_transaction_adversarial.py"
python "$D/independent/review_schedule_premises.py"
(cd "$D" && sha256sum -c SHA256SUMS)
(cd "$D/independent" && sha256sum -c SHA256SUMS)
```

Compare the JSON with the two saved independent result files. The 500 special-value scalar masked-sum cases and 200 bounded-input padded-QK/softmax/PV cases are separate toy domains. Neither exercises real attention or establishes all-value equivalence. The review also checks 18 abort-then-continue cases, rejects current alias/manifest failures, and separately reproduces observer and unsafe-alias premise violations.

The independent scripts pin the model digest. [reviewed_artifacts.json](independent/reviewed_artifacts.json) identifies the reviewed design/model/source manifest, and the directory-level `SHA256SUMS` files bind the published artifacts. These hashes establish identity, not correctness.

## Verify the inspected source identity

Source code is not copied into this directory. The line references bind to [source_manifest.json](source_manifest.json), not arbitrary current upstream code. To check an already staged copy:

```sh
D=docs/research/reference_contract_20261104/runtime_qualification
export HETEROSPEC_NATIVE_SOURCE=/path/to/authorized/staged/source
python "$D/verify_source_manifest.py"
# Optionally verify the original archive too:
python "$D/verify_source_manifest.py" --source "$HETEROSPEC_NATIVE_SOURCE" \
  --source-kit /path/to/native-source-kit.zip
```

The verifier is read-only and checks 12 source files. A matching digest establishes identity, not semantic correctness.

The source-kit archive is recorded at [fixed repository revision aa7ff4e](https://github.com/leecdiang/HeteroSpec/blob/aa7ff4e64752be3de0d7974febbce453ae3a96c0/benchmarks/rtx_prefix_reuse_v1/execution/evidence/native-source-kit.zip), with SHA256 `b1926827029e0bb8e219861901f2ca3538b330a44f9c6093b5267157dbfcd1ac`. Its candidate tree was processed by the repository's reference-contract staging, CUDA audit staging, observer port and native hardening steps. The existing [native validation record](../NATIVE_VALIDATION.json) at packaging base `5e63429220ef43b33d15ea5f7dadc2383a3e7592` contains matching overlapping staged-file hashes and its CPU build/reproduction commands. Those earlier CPU native tests are separate evidence: they do not execute the new plan in this directory.

To reproduce that separate staging/CPU-validation workflow, consult `scripts/reference_contract/validate_native.py` at the recorded repository revision. It takes an authorized extracted candidate directory and creates a fresh work tree. It also builds/runs the older native CPU tests. This bundle does not automatically invoke it, download a source kit/model, or access a GPU.

## Scope and known blockers

- The reference includes an exact transition schedule. A deployment hash alone does not make chunk-dependent producers equivalent.
- Full prelaunch preparation must include backend-internal allocations, quantization, padding writes, CPU thread settings, callbacks, copies and PDL/capture dependencies.
- Old raw KV descriptors need read leases through device completion. Pointer publication alone does not isolate in-place padded storage.
- Failure recovery needs known bounded writes and known completion; fatal CUDA errors are not caught by ordinary C++ exceptions.
- A scalar fallback must preserve the owner invariant or invalidate fast-path eligibility.
- Strict append-only zero-tail reasoning does not automatically cover cache import, shift, deletion, layer aliases or speculative partial acceptance.
- The proposed schedule can lose against the strong backend four-column loop. Only equal-outcome native experiments can establish net benefit.
