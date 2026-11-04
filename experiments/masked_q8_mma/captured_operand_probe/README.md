# Real captured operand probe, not a projection replay

## Conclusion

The fixed PR171 repository evidence is insufficient for a real Q8 projection CPU replay of the PR181 candidate. `operands.json.gz` is a descriptor/hash/route summary, not the operand bytes. The separately downloaded `operand-sample.json.gz` contains genuine full F32 inputs and selected old F32 outputs for two 8B operators, but no Q8_0 weights and no captured Q8_1 activation buffer. Missing bytes, not cloud memory, are the current blocker.

This directory performs CPU parsing, digest/bit comparisons of historical captures, and explicitly counterfactual host quantizer probes. It does **not** execute a projection, the PR181 CUDA candidate, any frozen runtime, a GPU, or an actual driver JIT. No runtime implementation or frozen experiment was changed, and no work was performed on the user's computer. No full model or multi-gigabyte raw archive was downloaded.

## Pinned provenance and integrity

- PR171 source/evidence commit: `371223b696bb805030c29f04e39eb17b57fb2ebb`.
- PR181 candidate inspected: `44625c8d53b8a7cc694d9c25a197858424d63197`.
- [Collector lines 29–34](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/collect.py#L29-L34) explicitly writes hashes into the summary and only input/live32/scalar32/packed32/native8 into the sample. The original host `weight.bin` is hashed but not copied into either file.
- [Summary](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/evidence/operands.json.gz): 17,925 compressed bytes, 120,576 decompressed bytes, SHA256 `bff60fbaac437421ad4ded651cc7b94d7ddaa1245fa279e7cb7fc8b40845aed5`, Git blob `07f27b38b4ac219c7665cabc6f76e22a1dd848ae`.
- [Actual sample](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/evidence/operand-sample.json.gz): 5,502,833 compressed bytes, 7,340,244 decompressed JSON bytes, SHA256 `d1a7686e44cc85eb074e01b6471c44a20e81a72c1fbff7ab001c72286486c2a8`, Git blob `9fcced0000546b1d377c47de2c7b0b7af040be02`.

Both compressed SHA256 and Git blob SHA1 identities are checked by `probe.py`; gzip CRC and strict base64 decoding are also checked. Ten decoded blobs total 5,505,024 bytes. Every blob has the descriptor-implied length and a SHA256 matching the corresponding fixed summary input/output/route digest. An independently written verifier also checks all 36 route digests for the two operators using actual sample prefixes. Matching archived hashes verifies internal provenance, not the truth of an independent new GPU run.

The GitHub text/blob route could not decode gzip and its >1MB contents route returned empty content. Those were not treated as bytes. A fresh authenticated connector-provided same-resource download link successfully fetched the actual 5.5MB sample; no access restriction was bypassed. No temporary download credentials are stored in this deliverable.

## Coverage, layout, and exact missing data

The summary covers 16 projections: eight operator/weight descriptors in each of 0.6B and 8B, with q=2,4,8,16,32 route summaries. Only two 8B operators have actual sampled data:

| Operator | K | M | N | Actual F32 input bytes | Missing Q8_0 weight bytes | Required canonical Q8_1 bytes for N32 |
|---|---:|---:|---:|---:|---:|---:|
| blk.0.attn_q.weight | 4096 | 4096 | 32 | 524,288 | 17,825,792 | 147,456 |
| blk.0.ffn_down.weight | 12288 | 4096 | 32 | 1,572,864 | 53,477,376 | 442,368 |

Each has 524,288-byte live32/scalar32/packed32 outputs and a 131,072-byte native8 output. F32 arrays are little-endian, column-major, contiguous: element `(column,row)` has index `column*M+row`. Weights have Q8_0 type 8, 32 values per 34-byte block, `[half d, int8 q[32]]`; the rows have stride `34*K/32`. Inputs/outputs have F32 type 0. Candidate Q8_1 has 36-byte blocks `[half d, half sum, int8 q[32]]`.

Missing weight SHA256 values are:

- attn_q: `822086ad0b394e3f032f5a95a0193df9a6f2f628f58cee4b2d2c44ba4bb26b5e`.
- ffn_down: `36b32988dd1e72b7b2f91e36fdf7b23e191b36c56a9c633c32c73fab67980ca5`.

The two weight payloads total 71,303,168 bytes (68 MiB). Canonical Q8_1 data would add 589,824 bytes (0.5625 MiB). Captured sample payloads are 5.25 MiB. If those missing payloads existed, a streaming CPU implementation could operate on these two cases without loading the whole 8B model; roughly 73.8125 MiB is the sum of these payloads before workspace/JSON overhead. This is not a measured memory profile. The summary's weights across all 16 descriptors total 1,048,240,128 bytes, but their hashes do not reconstruct any weight values.

Q8_0's dot helper uses Q8_1 `d` and quantized bytes, not its `sum` field. Thus exact `d`+q bytes would suffice for this projection even without the unused sum bytes. Neither is captured here. Known F32 inputs plus a high-level quantizer formula are not the same as known frozen quantized bytes.

## What the real historical bits show

| Comparison | attn_q bit mismatches / elements | ffn_down bit mismatches / elements |
|---|---:|---:|
| scalar32 vs packed32 | 0 / 131,072 | 0 / 131,072 |
| scalar32 vs live32 | 131,052 / 131,072 | 131,046 / 131,072 |
| scalar first8 vs native8 | 20,151 / 32,768 | 23,558 / 32,768 |

For scalar first8 vs native8, the maximum absolute differences are 5.960464477539063e-8 and 2.384185791015625e-7. For scalar32 vs live32 they are 9.196996688842773e-5 and 4.4727325439453125e-4. These are old captured route differences. `live32` is the old native32 result, not a route-independent definition of the scalar/four-column reference. The PR181 experiment targets the four-warp scalar/four-column arithmetic; historical native8 disagreements are not a new PR181 failure.

All 524,288 sampled F32 input elements are finite and contain no F32 subnormals. attn_q has 992 zeros, of which three are negative zero; ffn_down has no zero inputs. All sampled outputs are finite and non-subnormal. The local private reproduction output can include exact first-mismatch coordinates and bits; that detailed output is not republished here. Large maximum ULP distances near cancellation/sign changes are not a useful substitute for the bitwise contract, so absolute differences and mismatch counts are given together.

## Quantizer identity is a real unresolved boundary

The [frozen quantizer PTX](https://github.com/leecdiang/HeteroSpec/blob/44625c8d53b8a7cc694d9c25a197858424d63197/experiments/masked_q8_mma/frozen_reference_audit/ptx/quantize_q8_1.sm90.ptx#L137-L165) uses two `div.approx.ftz.f32` instructions: amax/127 and x/d, followed by round-away behavior and half conversion. [NVIDIA's division specification](https://docs.nvidia.com/cuda/parallel-thread-execution/#floating-point-instructions-div) describes approximation error bounds, not a CPU RN bit-pattern identity. The archived PTX is evidence about that embedded virtual instruction path, not evidence for the exact deployed driver-JIT instruction sequence.

The nominal probe deliberately substitutes host float32 RN divisions. It preserves the XOR16,8,4,2,1 sum tree, round-away integer conversion, and half RN storage, but its generated Q8_1 SHA256 is a **counterfactual**, never a frozen-buffer digest. The CPU process is checked for FE_TONEAREST. No generated nominal Q8_1 is fed to a projection and represented as actual captured activation data.

A concrete actual-input counterfactual demonstrates the boundary: keeping the same RN d but changing RN(x/d) to RN(x * RN(1/d)) changes 62 attn_q quantized bytes, and zero bytes in this ffn_down sample. A scalar standard-library implementation independently confirms the count. Neither expression is claimed to emulate GPU `div.approx`. Actual input/output values and reversible tensor fragments are not included in this report.

A separate deliberately hypothetical ±4-adjacent-FP32-step sweep around both division results finds 474 attn_q and 10 ffn_down potentially crossing integer-rounding boundaries; zero and seven blocks respectively cross half-scale rounding boundaries. These are sensitivity counts, not observed GPU disagreements, not a certified PTX uncertainty interval, and not proof that its endpoints occur on any GPU.

For nominal RN quantization, every stored half d is finite, positive and normal. d ranges are approximately [1.032046e-4,1.184702e-3] and [6.756895e-5,3.497991e-2]. The independently recomputed sum tree has no F32 subnormal/nonfinite intermediate, but the final half sum has three subnormals for attn_q and ten for ffn_down. That field is unused by the Q8_0 dot. Do not overstate this as “no half subnormals anywhere.” The missing weight scales mean the full finite-half projection domain is still unverified.

## Relevance to current PR181 and stopping point

The [candidate entrypoint](https://github.com/leecdiang/HeteroSpec/blob/44625c8d53b8a7cc694d9c25a197858424d63197/experiments/masked_q8_mma/kernels.cu#L162-L175) accepts **prequantized** Q8_0/Q8_1 data. Both sampled shapes satisfy its simple K/M/N divisibility bounds, but shape eligibility is not data admission or numerical validation. The current main source has explicit RN arithmetic; its [frozen-reference audit](https://github.com/leecdiang/HeteroSpec/blob/44625c8d53b8a7cc694d9c25a197858424d63197/experiments/masked_q8_mma/frozen_reference_audit/README.md) identifies scale-first multiply, FMA/FTZ and the exact reduction chain for the frozen target. A full CPU replay would require those semantics and exact actual weight/activation operands. It could still not establish GPU compiler/JIT identity, performance, dispatch admission or end-to-end acceptance.

Smallest sufficient future evidence: the two exact weight tensors with hashes above, captured Q8_1 d+q bytes for the corresponding old input columns, and the precise scalar/four-column target route/runtime identity. Until then, the honest deliverable is this bit/quantization-boundary probe, not a reconstructed real projection or strengthened GPU acceptance claim. Existing synthetic mapping proofs remain synthetic; this real-data analysis complements them without upgrading them.

## Validation and reproduction

All production input checks use explicit exceptions rather than Python assert statements. The main suite runs under normal Python, -O and -OO: 23 unit tests in each mode (69 executions), 15 end-to-end CLI tamper negatives, and three valid CLI runs whose output files are byte-identical. Header-only changes that remain valid gzip are rejected by the pinned compressed hash. A changed actual operand byte in a reserialized sample is also rejected by outer identity. Separate direct tests exercise decoded length/digest rejection. Invalid inputs return a failure status before writing a success result.

The independently written verifier additionally checks exact sample/blob/route sets, duplicate records, all 36 route-prefix digests and non-vacuous aggregate results. Its copied-fixture tamper tests exercise decoded payload changes and route/structure errors under normal Python and -O. Test receipts accompany this report. These tests verify validation behavior, not GPU arithmetic.

Requirements: Python 3, NumPy and Linux libm. The original authorized evidence files are intentionally **not included**. Obtain/read the two files already present at the pinned repository links above through an authorized route; there is no auto-download or credential handling in these scripts. Keep those input files outside the publication directory. Run:

```
python probe.py --input-dir /path/to/authorized/evidence --output reproduced/probe_results.json
python test_validation.py --input-dir /path/to/authorized/evidence
python independent-verification/verify.py --input-dir /path/to/authorized/evidence --output reproduced/independent.json
python independent-verification/verify_division_counterfactual.py --input-dir /path/to/authorized/evidence --output reproduced/division.json
python independent-verification/verify_xor_domain.py --input-dir /path/to/authorized/evidence --output reproduced/xor.json
python independent-verification/test_verify_tampering.py --input-dir /path/to/authorized/evidence
```

The generated detailed outputs may contain original sample coordinates/values. They are ignored by Git and should stay local unless separately authorized for sharing. No actual input/output blobs, model weights, prompts, or decoded tensor fragments are republished. `SUMMARY.json` contains aggregate findings; `SOURCE_MANIFEST.json` pins source/evidence identities and the files in this supplement.
