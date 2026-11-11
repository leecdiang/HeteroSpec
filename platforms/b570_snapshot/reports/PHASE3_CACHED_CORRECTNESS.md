# Phase 3 Cached Speculative-Decoding Correctness Suite

## Result

**PASS — 48/48 cached heterogeneous speculative outputs exactly matched their independent cached RTX greedy references.**

The suite validates target KV-cache prefill, block verification, accepted-token commit, rejected-tail removal, RTX correction-token insertion, and all-accepted bonus-token insertion on native Windows.

## Configuration

- Draft: Qwen3-0.6B symmetric INT4 OpenVINO, explicitly bound to CPU
- Target: Qwen3-8B bitsandbytes NF4/BF16, explicitly bound to RTX 5070 Ti Laptop GPU
- Target attention: PyTorch SDPA explicitly forced to cuDNN
- Prompts: three fixed semantic prompt families
- Context lengths: 64 and 128 tokens
- Output: 32 tokens
- Candidate sizes: `k = 1, 2, 4, 8`
- Repetitions: 2 per prompt/context/k cell
- Total cases: 3 × 2 × 4 × 2 = 48
- `AUTO`/`MULTI` and runtime fallback: prohibited

## Aggregate observations

| k | Cases | Exact matches | Aggregate acceptance | Mean verification rounds | Mean prototype seconds | Mean cached RTX reference seconds |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 12 | 12 | 99.0% | 16.17 | 1.78 | 3.68 |
| 2 | 12 | 12 | 99.2% | 11.00 | 1.93 | 3.68 |
| 4 | 12 | 12 | 99.0% | 7.00 | 1.38 | 3.68 |
| 8 | 12 | 12 | 99.4% | 4.00 | 0.97 | 3.68 |

Peak CUDA allocation across the complete suite was 5.803 GiB. The machine remained stable and stayed far below the previously observed near-full-VRAM crash condition.

The prompts are deliberately simple and repetitive, so their very high acceptance rates are correctness-fixture behavior, not representative workload estimates. The timing columns are engineering observations only: this suite was not randomized, power-logged, or designed as a formal performance benchmark.

## Rejection-path validation

The main suite encountered seven real rejection rounds and still matched the target reference in all cases. After replacing a deprecated positive-length cache crop with the current negative-tail-removal API, an additional three-case regression was run at context 64, output 32, and k=8.

- Post-change exact matches: 3/3
- Real rejection rounds: 1
- Rejected block: 8 proposed, 7 accepted, mismatch at zero-based candidate index 7
- RTX correction token: 472

This confirms that the maintained implementation passes an actual cache rollback and correction path, not only all-accepted cases.

## Correctness boundary

The implementation is correct for deterministic greedy decoding under the tested shapes and runtime versions. It does not yet implement probabilistic speculative sampling. Sampling would require the full rejection-sampling correction distribution; simply comparing sampled tokens would be incorrect.

## Decision

The cached CPU-draft/RTX-target engine is ready for a broader workload qualification. Before formal speed or energy claims, the next suite must add less repetitive prompts, longer outputs, EOS-aware stopping, per-run NVML telemetry, warm-up/repetition controls, and a pure-target baseline executed through a comparably optimized cache path.

## Evidence

- Maintained implementation: `scripts\phase3_cached_speculative_suite.py`
- Full 48-case result: `logs\phase3-cached-suite-20260905.json`
- Post-change rejection regression: `logs\phase3-cached-negative-crop-rejection-20260905.json`
- Initial cached canary: `logs\phase3-cached-canary-20260905.json`
