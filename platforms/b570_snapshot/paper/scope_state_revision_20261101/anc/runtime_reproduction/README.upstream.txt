# Query-layout integration kit (CPU contract + source map)

This entry separates reusable address/phase/cache obligations from archived native implementations. `contract.py` is a standard-library, no-GPU model of the view contract; it is not a numerical attention implementation or a positive CUDA/Vulkan support certificate. `SOURCE_INDEX.json` pins the actual implementation evidence. The mirrored patches/header are byte-identical archival files, not a newly portable backend release.

Run from repository root:

```sh
python -B -m unittest discover -s src/query_layout -p 'test_*.py' -v
python -B src/query_layout/contract.py
```

Integration order: preserve native Q/mask strides and ownership; retain native GQA mapping; apply paired views only in the supported role/phase; include layout and state recipe in graph-cache identity; restore native output order; leave acceptance, correction/bonus, pending-token ownership and KV reconciliation intact. Qualify actual backend admission/placement and fixed-operand correspondence separately, followed by complete endpoint/state qualification. Only then measure full cost.

The RTX scope header is for the archived single-writer process. Its process-wide layout setter is not a concurrent multi-request API. The Vulkan patch is restricted to its exact d128/Hq32/Hkv8/key256-or512/q2-or4 descriptors and requires preceding source/admission changes from PR131. Apply no patch automatically. Recover the original source capsule/build manifest before using it; current upstream llama.cpp is not a compatible substitute by default.

This completes an identifiable and CPU-testable reuse interface. General runtime packaging, arbitrary shapes, fused attention and multi-sequence concurrency are not claimed or implemented by this kit.
