# Decisions grounded in the review and fixed repository evidence

The user's supplied review is the research basis. The following fixed resources
were checked during design; distinct references and timing windows are NOT pooled.

| Source | What it supports | Consequence here |
|---|---|---|
| [PR64](https://github.com/leecdiang/HeteroSpec/pull/64), `68421206452c22caef19c9fb34452cb04a3f99b3` | In-place phase binding already exists; own 15-task complete-request comparison was slower than R | Reuse `code/implement_C.py` and `candidate-front/phase.h`; no novelty for being resident |
| [PR82](https://github.com/leecdiang/HeteroSpec/pull/82), `7e82fa0b8fc2c9d56e04512c47a0986171534b25` | Smol endpoint-qualified resident result still cost about1.83x R; raw suffix differs | Do not inherit current cap/EOG/full-state qualification from the old endpoint result |
| [PR132](https://github.com/leecdiang/HeteroSpec/pull/132), `7e98e288b4137c998604a0809c7e956474967de1` | Fixed six-coordinate AV/GQA panel preserves per-output arithmetic via strides/dispatch | Reuse mechanism, not its synthetic result as trained-model qualification |
| [PR165](https://github.com/leecdiang/HeteroSpec/pull/165), `5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f` | Qwen precision/prefix repair and a qualified target-only control | The optimized ordinary path, not just slow R, must be a comparator |
| [PR169](https://github.com/leecdiang/HeteroSpec/pull/169), `8ca17478c292275b3515a91b51d0e791a8fae256` | Local/WB tradeoffs depend on width/alignment; d64 Smol p021 extension | Do not assume local is fastest; transfer shape rules, not model-name patches |
| [PR175](https://github.com/leecdiang/HeteroSpec/pull/175), `cd5f542a851d192e21187bc00566de0f685e2383` | Natural-prefix AUTO did not establish a gain | No new fitted AUTO or favorable-offset panel |
| [PR187](https://github.com/leecdiang/HeteroSpec/pull/187), `b01040d3b303abfc31c5ce2dbcb100cac7490b27` | Smol T contract and six-arm clean results; Qwen capacity failure | Preserve historical results; Smol primary, independently referenced Qwen transfer only if admitted |
| [PR188](https://github.com/leecdiang/HeteroSpec/pull/188), `de96c18ced307b480f360d4d88a85792fc71fd6c` | Source-based transition workload and RTX plan | Read for shared interface ideas; do not modify running RTX or call calculated bytes measured traffic |

Reviewed online source: PR63 `66594b349955e66146702325559c26019ea16485`,
`benchmarks/b570_closeout_overnight_v1/code/src/observer.h`, `native.cpp`,
`target.cpp`; subsequent PR187 `smol_producer.py`, `smol_qualify.py`,
`smol_campaign.py`, `smol_timing.py`, `smol_bulk.hpp` describe their derivatives.

The online move still exports three full states, imports one, creates a context
and compares states even with tracing off. The bulk reader is an offline observer.
This is a source fact, not an attribution of the entire measured slowdown.
`generation_ms` starts before move and is not pure decoder time.

PR64's private setter changes n_ubatch, synchronizes and re-reserves the scheduler.
Its frontend ALSO changed output reservation and prompt handling. Only reuse the
required mechanism; do not transplant the old reserve512 or declare it harmless.

The supplied review's one-input phase numbers are diagnostic examples, not a
population cost decomposition. Source-derived MiB/GiB estimates are logical byte
volumes, not measured PCIe traffic, bandwidth or time. No new paper claim follows
from this plan or its helper tests.
