# Reviewer reproduction and author closeout

## Three independent checks

**Reported data:** run `python -B paper/arxiv_v4_candidate/anc/check.py`, then the standard-library tests listed in the paper README. These reproduce saved ratios, intervals, table identities and fail-closed claim guards. They require no network, model weights or GPU.

**Document:** run `python -B scripts/build.py --cached-bbl` from the manuscript directory. The present local reconstruction passed 511 report/source checks and 36 distinct tests, produced 23 pages and matched the previously reviewed PDF SHA256 `111010ab9fa0f69892228cc9a4ea4318890494d0b009d49ad69f5fea5834f3ca`. A different TeX installation can change PDF bytes without changing its content; inspect any rebuilt PDF. Tests do not replace page review.

**Native science:** follow the exact commit-pinned source/model/runtime manifests and raw-access descriptions in the supplement. Full raw vectors are not all in this Git repository. No report-only checker should be described as full raw replay. An independent human/native replication remains distinct from this maintenance pass.

## Baseline map

| Comparison | Meaning | Keep separate |
|---|---|---|
| PQ versus QB | Local representation increment under one reference | Not total drafting value |
| GS versus local repair | Scope of numerical constraint | Not QB-only novelty |
| Same-layout target-only versus draft | Net value of drafting | Not a hardware ranking |
| Native/fused fast path | Eligible comparator only after same-reference qualification | A faster divergent endpoint is not an admissible speedup |

## Nonexperimental submission preparation

The paper has a contribution-led abstract, an explicit repair–draft interaction, complete adverse/unknown outcomes, an AI-use statement, 31 references and a public-source-only upload ZIP. The integration kit has exact source entry points and CPU tests; it is not a newly validated general CUDA/Vulkan runtime.

Before JSA submission the author must confirm funding, competing interests, CRediT roles, final author details, data-sharing permissions and the target portal's required files. These personal declarations are intentionally not invented. A suggested cover-letter core is: "This work studies reference-preserving graph lowering for quantized inference. It isolates local representation cost from repair scope and draft profitability, and uses state and backend interventions to specify transfer obligations." Do not claim a new speculative acceptance algorithm, a 41.8% QB-specific speedup or a new accelerator.

Request one genuinely independent systems review of the nearest-work distinction, same-reference baselines, state-to-method connection and exact evidence access. The present assistant's self-check is not independent peer review.
