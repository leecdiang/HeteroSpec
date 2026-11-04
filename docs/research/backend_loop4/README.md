# Strong backend-loop baseline for the frozen runtime

This is an independent, reviewable addition. It does not replace the frozen
reference R, merge experiments, import a different runtime, or establish a
speedup. CUDA source is staged; CUDA compilation and GPU execution are NOT_RUN.

## Three controlled candidate arms, plus unchanged R

All three arms start from the same hash-pinned PR171 candidate source kit:

- `packed`: byte-for-byte unchanged candidate. Independent groups occupy tensor
  dimension 2, with the existing graph tail path.
- `graph_tiles`: disable only the packed projection branch. Retain the original
  <=4-column graph views, matmuls and concat. Attention, rotary/head placement,
  reference batching helpers and other arithmetic are unchanged.
- `backend_loop4`: one explicitly marked rank-2 Q8_0/F32 matmul for contiguous,
  singleton-channel/sample q5..32 projections. The CUDA backend verifies actual
  same-device buffers and that the old dispatcher would select MMVQ for every
  <=4-column tile. It uses the existing wide-input quantizer, then loops over the
  already-quantized activation with the original MMVQ type/column specialization
  dispatcher. The remaining <=4 columns use their original specialization.
  No new reduction kernel or transcendental implementation is introduced.

The original oracle/reference binary is a separate fourth arm and stays untouched.
Within the original active Q8_0/F32 q5..32 outer condition, unsupported
contiguity/weight-channel geometry retains graph tiling. Other cases (q1..4,
q>32, other dtypes, or inactive query-batching policy) retain the original
unmarked matmul path. Neither path counts as a backend-loop execution.

The backend-loop arm removes projection graph tiling/concat, not attention
partitioning or all graph scheduling. It is a stronger control than a sequence
of full backend calls that requantizes every tile. From source, quantization is
outside the new tile loop. This is an expected host-call structure, NOT a
measured number of CUDA launches or synchronization events. Obtain a GPU trace.

## Exact implementation boundary

The marker occupies the previously zero last int32 op-parameter slot for this
private MUL_MAT path. It does not change precision or Hadamard hint slots.
Generic backend device-support, execution and plan-creation boundaries, plus
the raw CPU compute entry (including legacy CPU plans), reject
marked nodes unless the actual device belongs to the instrumented CUDA registry.
This prevents CPU/Vulkan/other fallback from silently executing a wide matmul
and labeling it as backend-loop4. Ordinary unmarked operations remain unchanged.

The CUDA entry checks Q8_0/F32, contiguity, q bounds, dimensions, real residency,
warp32, padding behavior and per-tile selection through the frozen selector.
The loop calls the old specialization after adjusting the quantized-input byte
offset and output float offset. For singleton channel/sample dimensions, derived
strides equal the old small contiguous tile's strides. We bound int-addressed
activation/output spans and the weight block span, including 32 padded rows.
The fixed eight-entry plan uses no heap allocation.

Unsupported marked cases fail; there is no automatic fallback that could
silently change the evaluated method. Use a C++ transactional harness that
synchronizes prior GPU work and restores the complete checkpoint after failure.
The source's other assertions/device errors are not made universally recoverable
by this baseline. GPU graph capture, reuse, fusion and actual selected kernels
must still be observed; no correctness claim follows from unchanged names.

## Qualification and fair timing

First compare every candidate with the unchanged R on identical saved inputs,
model, hardware/driver, output-row mask and state history. Compare complete binary32
logit vectors, KV state and continuation vectors/tokens, including tails and
physical prefix boundaries. `compare.py` only reports finite capture equality;
it neither authenticates supplied provenance nor registers a production proof.
Missing/truncated data, wrong R pin, fallback or absent backend-loop execution
rejects qualification. Full-state byte equality is deliberately conservative.

The planned matrix includes q=1/4 controls and q=5/7/8/9/16/31/32, with prefixes
1/255/256/257/511. Expand it with actual model geometries, lengths, dtypes and
negative cases rather than extrapolating synthetic tests. R and all candidates
must use equally optimized host/service policies. Account for quantization,
kernel launches, graph construction/concat, capture/reuse, memory traffic,
synchronization, state verification/recovery and end-to-end request latency.
Disable diagnostic tracing during timing and preserve every failed qualification.

Crucially, quantizing a wide batch once is NOT assumed bitwise equivalent to
quantizing its tiles independently. The frozen quantizer may have launch/config
or layout-dependent effects. Matching <=4 MMVQ specializations does not prove
quantizer or full-model equivalence. Hardware full-vector replay is mandatory.

## Prior art / attribution

The public `amiller/llama_reproducible` patch at commit
`f0dafdbd9dba40bd0e596f74f3da5f592900fca4`, file
[`patches/0001-all-deterministic-parity.patch`](https://github.com/amiller/llama_reproducible/blob/f0dafdbd9dba40bd0e596f74f3da5f592900fca4/patches/0001-all-deterministic-parity.patch),
Git blob `6cf817ce743199c44e438dd8dbdb3d2f3e92bf99`, explicitly contains a
`DET_MAX_BATCH=4` loop over quantized-input/output offsets. That public prior art
motivates this baseline and invalidates novelty claims for the loop itself.
Our implementation is independently adapted to the frozen source's dispatcher,
annotations and safety bounds. We do NOT import its deterministic global mode,
CPU dot products, norm/softmax/rope/transcendental changes, or assume its stated
warp configuration holds for this different source/device. Those changes could
change R and would confound a reference-relative comparison.

## Reproduce

From the project root:

```sh
python scripts/reference_baselines/validate.py \
  --candidate /path/to/verified/native-source-kit/candidate \
  --work /tmp/fresh-loop4-work --output /tmp/loop4-validation.json
```

This stages all three arms, builds the backend-loop arm's actual CPU library,
runs geometry/negative tests, actual CPU wrong-backend rejection, source-generated
CPU simulations and finite-capture comparator fixtures. It does not download a
model, install CUDA, run a GPU, or claim CUDA source compiles. Every CPU simulation
is labeled separately from the native CPU library and from missing GPU evidence.

## How to interpret the outcome

- If graph tiling itself fails full-vector equality against R, stop: the reference
  boundary is not established, so a relative speedup cannot support that claim.
- If backend-loop4 fails but graph tiles pass, inspect wide-vs-tile quantized
  buffers and continuation state. Do not assume matching column specialization
  is sufficient, or silently broaden the reference definition.
- If packed beats graph tiles but not this backend-loop control, the gain may be
  removal of graph/concat/dispatch overhead already addressed by known batching
  techniques. That does not establish a new arithmetic method or TPDS-level gain.
- Only compare performance among actually qualified arms, including state and
  service costs. A reproducible packed advantage over this stronger control is
  useful evidence, not a guarantee of novelty or acceptance.
