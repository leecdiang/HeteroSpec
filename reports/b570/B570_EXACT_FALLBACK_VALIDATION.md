# B570 Exact Fallback Validation

Status: **CORRECTNESS FAIL / DIAGNOSTIC PERFORMANCE ONLY**

## Frozen candidate

The unique serialized fallback changes only speculative `n_ubatch` from 128 to 1. Models, hashes, Vulkan0 placement, full target/draft offload, greedy decode, seed, k=2, context, batch, and output contract remained frozen.

## Correctness

- Exact pairs: 60/90
- Stable exact prompts: 20/30
- Global performance admissible: FALSE

## Verification mechanism

- V2_exact(512): 1.9827
- V2_exact(2048): 1.9917

V2 is a PP2/PP1 target-forward mechanism proxy, not end-to-end speedup.

## End-to-end timing

- Prompt-level geometric-mean speedup (baseline/fallback): 0.3087
- Prompt-level median speedup: 0.3248
- 95% prompt bootstrap CI: [0.2926903625835106, 0.3246036952205638]
- Prompts faster: 0/30
- Exact-subset speedup: 0.3026

## Board energy

- Energy-efficiency ratio (baseline/fallback board J per token): 0.3023
- 95% prompt-bootstrap CI: [0.28455311861341115, 0.3201604335732349]
- Baseline mean/median board J/token: 5.6020 / 5.5929
- Fallback mean/median board J/token: 18.8499 / 17.3867
- Exact-subset efficiency ratio: 0.2954

The boundary is Arc B570 adapter board power only; CPU package, wall, and whole-system energy are excluded.

## Platform decision

This exhausts the single preregistered exact fallback candidate. No additional parameter or backend search is authorized; the B570 backend-control campaign is **CLOSED**.
