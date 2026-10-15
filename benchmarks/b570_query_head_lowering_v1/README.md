# Query/head lowering under a fixed reference

**NEW independent study; design and locally tested CPU prototypes, not completed B570 inference.**

**Host update:** [host/RESULT.md](host/RESULT.md) now records432 actual frozen-GGML
CPU fixtures /2592 graph computations, full PQ/QH vector relations, native-actor
offline compilation and retained integration failures. S1's exact executable,
16 inputs,161-slot plan and [F0](host/S1_F0.json) are ready for separate author
approval. No device support query, GPU/model execution or S2/S3 start occurred.

The research object is a class of reference-constrained attention representations, not a fix for four GSM8K answers. The candidate encodes `r=h*q+j` and changes Q from `[d,q,H,1]` to `[d,1,H*q,1]`, retaining the original K/V objects. It avoids the *specific fourth-axis mismatch* found in PR111; it does **not** yet establish full Vulkan admission, native placement, numerical equivalence or speed.

## Start here

1. [HOST_PROMPT.md](HOST_PROMPT.md): exact B570 agent work order and stop conditions.
2. [PROTOCOL.md](PROTOCOL.md): complete staged study, reference contracts, budgets, holdout and decision branches.
3. [DESIGN.md](DESIGN.md): index argument, compact/dense mask alternatives, cost obligations, strong baselines, architecture interface and prior art.
4. `native/query_head.h`: real GGML graph-builder prototype, six explicit representations; q1/MQ require the caller to execute the original chain. This header has only been compiled against a descriptor test double here.
5. `core.py`, `oracle.py`, `plan.py`, `evidence.py`, `ledger.py`: descriptors, independent scalar/address checks, immutable planned cells, capability-only selection, full-vector/full-panel calculations and attempt accounting.

```bash
# Python >=3.11, standard library only. No model/backend imports.
python -B -m unittest discover -s tests -p 'test_*.py' -v
python -B plan.py cpu --out /path/to/new/CPU_PLAN.json
python -B plan.py operator --out /path/to/new/OPERATOR_PLAN.json
python -B plan.py pilot --out /path/to/new/PILOT_PLAN.json
# After independent exposure review and select_panel():
python -B plan.py confirm --panel HOLDOUT_PANEL.json --out /path/to/new/CONFIRM_PLAN.json

# Descriptor-only C++ check; this is NOT a GGML computation or Vulkan build.
g++ -std=c++17 -Wall -Wextra -Werror -Itests/mock -Inative tests/test_graph.cpp -o /tmp/hs-qh-descriptors
/tmp/hs-qh-descriptors
```

## Progression

| Stage | Planned work | Hard ceiling | Start authority |
|---|---|---|---|
| S0 | Source/near-neighbor review, independent CPU semantics, isolated real-GGML build and raw adapter | 432 CPU fixtures /2592 CPU graph computes; 14,400 child seconds; 8 GiB RSS; 2 GiB output | CPU preparation now |
| S1 | One device-support census, then bounded fixed-input operator comparison | 161 operator-host attempts: 1 support-only +160 graph attempts; 3600 seconds; 2 GiB | Exact F0 + author approval |
| S2 | Natural old-reference bridge and four exposed sentinels | 64 requests /64 processes; 7200 seconds; 4 GiB; no warmup | Separate exact F0 approval after S1 |
| S3 | Frozen unseen-input confirmation | 24 texts ×7 arms ×3 sessions: 504 measured +504 charged warmups; 504 processes; 21,600 seconds; 6 GiB | Separate GO/F0 after S2 |

Ceilings are **not commitments to run everything**. Unsupported slots, failed attempts and all unstarted slots remain visible. S0 does not authorize a device query; S1 support-only initialization is explicitly charged, not a hidden probe. No retry/warmup exists outside the above list. Across S2+S3 the ceiling is 1072 model requests; the 161 operator-host attempts are separate. Old PR109/105 costs are preserved separately and do not provide controls or reusable budget.

## What would be a meaningful result?

A new representation must provide a useful same-reference alternative to strong PQ, not merely be faster than unsupported QB. Generalization must be shown on frozen new conditions, not by rewriting rules after errors. Positive operator results do not prove full-decoder preservation. A correct but more costly path may be an engineering result, not a new accelerated method. CPU geometry coverage is not a new natural-input cohort.

## Boundaries

Do not modify/resume PR108/109/111, RTX PR104/110, arXiv, models, numerical DLLs, sampler, shader arithmetic or old archives. No donor restore, special-token/head search, speculative-state surgery or live-KV switch to reference. This PR adds only a new directory on fixed main.

The host must still implement/adapt: **real GGML CPU harness, full supports_op census, actual operator placement audit, Vulkan execution, native actor integration, real wire/request mapping, independent raw reconstruction, role-specific monitoring and owned-process watchdog, exact execution F0**. None is silently replaced by a synthetic result or a template PASS.

This exploration is not another prerequisite for the current arXiv update. Its output can be `SOFTWARE_FIRST`, `BOUNDED_POSITIVE_METHOD_EVIDENCE`, `NO_GAIN_OVER_PQ`, or `HOLD/STOP_WITH_COUNTEREXAMPLE`. No gain, fixed q-domain failure or narrow task-specific effect is an acceptable stopping result.
