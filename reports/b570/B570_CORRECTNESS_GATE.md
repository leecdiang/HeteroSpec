# Arc B570 correctness gate

Date: 2026-09-12 (+08:00)  
Branch: `windows/b570-backend-control`  
Qualification commit: `385f3fc590e4b37d27d7ae6db9211aa7803c84ba`  
Status: **INVALID / CONFIGURATION-BLOCKED**

## Frozen provenance

The B570 configuration and six prompt IDs were written to `work/b570/B570_FORMAL_CONFIG.json` before any formal B570 result. The selection was `HumanEval/106`, `HumanEval/129`, `HumanEval/3`, `HumanEval/10`, `HumanEval/19`, and `HumanEval/20`. The four additional IDs are the first four numerically ordered non-duplicate IDs in the pre-existing frozen HumanEval30 selection; no output, acceptance, or timing was used to select them.

The intended condition fixed llama.cpp b10839 / `0cae43063`, Qwen3-8B Q8_0 target, Qwen3-0.6B Q8_0 draft, `Vulkan0` Arc B570, full offload, greedy decoding, temperature 0, context 512, batch 128, ubatch 128, semantic output cap 128, and speculative `k=2`.

## Remote protocol evidence

The last attempt waited 120 seconds for manual disconnect and then 60 seconds for idle settling. Its preflight at 00:19 showed zero ToDesk activity on the B570 LUID and 9,009.5 MiB idle VRAM headroom. The unattended runner preserved timestamps, raw streams, and a failed marker. No result from an attempt with non-zero B570 ToDesk activity was accepted.

## Failure

The first scheduled pair (`HumanEval/19`, repetition 1) executed both processes, but the two b10839 applications did not produce a common output-cap boundary under the initial wrapper: the tokenized outputs were recorded as 127 and 129 tokens. That pair is not treated as evidence of a Vulkan numerical divergence because wrapper boundary handling is confounded.

The next scheduled run (`HumanEval/3`, repetition 1, speculative condition) aborted inside llama.cpp:

```text
GGML_ASSERT(n_tokens_all <= cparams.n_batch) failed
```

The frozen batch size of 128 is therefore not executable for every preregistered prompt. The run stopped after two recorded items and one aborted item; it did not complete the required 36 items. Parameters were not changed, GPU layers were not reduced, and the prompt set was not modified.

## Invalidated pilot classification

- `B570_FAST_PATH_CORRECTNESS = NOT DETERMINED`
- First-attempt classification: `INVALID / CONFIGURATION-BLOCKED`, not `FAIL`.
- Exact equality: not established; the frozen gate did not complete.
- Repetition stability: not established.
- Acceptance statistics: incomplete and non-reportable as a six-prompt gate.
- Minimum-reproduction candidate: the raw `HumanEval/19` pair is retained only as a wrapper-boundary diagnostic, not a proven backend mismatch.
- HumanEval30 recommendation: **STOP**.

Neither the batch assertion nor the CLI token-boundary ambiguity supports a Vulkan numerical-failure claim. The assertion occurred before a valid six-prompt gate could complete, while the 127/129 observation was confounded by inconsistent application framing and token-count semantics. The old attempt remains retained under `work/b570/formal-*` and is excluded from scientific correctness/performance inference.

Replacement preregistration v2 is frozen at `benchmarks/b570_backend_control/preregistration_v2.json`. It uses offline frozen-input capacity only to set `n_batch=512` and `n_ctx=1024`, and defines equality over normalized generated token IDs rather than raw CLI totals. No replacement formal execution has been run.
