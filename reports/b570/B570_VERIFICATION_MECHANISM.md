# Arc B570 two-token verification mechanism

Date: 2026-09-12 (+08:00)  
Branch: `windows/b570-backend-control`  
Qualification commit: `385f3fc590e4b37d27d7ae6db9211aa7803c84ba`  
Status: **NOT RUN / STOP**

## Preregistered operation

The frozen plan defined `V2(n) = T_verify(2,n) / T_decode(1,n)` using the same llama-bench PP2/PP1 target-forward proxy as the Windows CUDA mechanism study: identical Qwen3-8B Q8_0 target, Flash Attention off, full target offload, and 20 repetitions per cell. The B570-specific differences were Vulkan0 instead of CUDA0, depth/context points 512 and 2048, batch 128, plus both the fast ubatch-2 route and serialized ubatch-1 control. Individual nanosecond samples, median, mean, sample standard deviation, CV, and ratio of medians were to be retained.

This proxy measures the marginal target-forward cost of evaluating two adjacent tokens instead of one. It is not end-to-end speculative-decoding speedup.

## Stop reason

No verification cell was launched. The unattended stage intentionally ran the correctness gate first, and the frozen correctness configuration aborted on `HumanEval/3` with `n_tokens_all <= cparams.n_batch`. Continuing into the timing microbenchmark after the formal gate's invalid configuration would have produced mechanism numbers detached from a completed correctness qualification.

## Result

- V2, context 512: **not available**
- V2, context 2048: **not available**
- Case classification: **none; prerequisites not met**
- Recommendation: **STOP; do not run frozen HumanEval30**

No HumanEval30 performance run, power/energy measurement, parameter search, backend comparison, or V2 timing cell was performed.
