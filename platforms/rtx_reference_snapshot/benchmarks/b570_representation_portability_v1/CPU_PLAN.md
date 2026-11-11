# Frozen CPU plan, revision 0

Parent/analysis: PR109 `039a24bf61374042e0dc9f3a3619ea40b218a5ad`.
Executed implementation: `bb803c94f23af0e5ab4e250c52f74e0b60621a66`.
PR108 design: `8d7b85d8aac6e546ca23e1f8a6ad353ea7ed2e02`.
F0 SHA256: `29cf422ef631edfa45ba55b56947926e1977070b8957dbc362e4e5581401d6e8`.
Remote PR108/109 queried 2026-10-15: heads equal the above pins; both open Draft.

No new model processes/requests, GPU forwards/operators, device/queue creation,
backend discovery, probes, warmups or retries. Only ggml-base and explicitly
loaded frozen ggml-cpu are admitted into the isolated CPU executable directory.
Record actual process modules at entry, after explicit load, and before/after
each fixture. Never load ggml/llama/Vulkan/CUDA DLLs. CPU threads=1.

Before any new fixture execution, commit this plan and fixtures.py. Development:
K=128,256 (24 geometries, 144 fixtures). Holdout: K=127,129,255,257 (48 geometries,
288 fixtures), executed only after a second rule/source lock commit. Preserve
first results, including crashes. At most two evidence-scoped implementation
revisions; compilation repairs are logged separately. No precision or tolerance
search. Maximum one working day; unresolved questions remain unresolved.

Geometry product: q={1,2}, K={127,128,129,255,256,257},
(Hq,Hkv)={(8,8),(8,1),(32,8)}, Dq=Dv=128,
Q storage={compact, model_permuted_offset}. Compact Q[D,q,H,1] strides
[4,512,512*q,512*q*H]. Model storage is base allocation 8+128*H*q
float32 elements, view offset 32 bytes, permutation of [D,H,q,1], with strides
[4,512*H,512,512*H*q]. K[D,K,Hkv,1] and V[K,D,Hkv,1] contiguous F16;
mask[K,32,1,1] contiguous F32. No all-masked query. Inputs are synthetic.

Masks: all valid; causal valid keys k < K-2+j (last keys padding);
sparse exactly one valid key (3+7*j)%K. Unused mask columns are -infinity.
Data: exact structured Q one-hot at (head+3*query)%128, K values
((key+head)%5-2)/8 constant over features, V ((feature+3*head+key)%9-4)/8;
and cancellation, coordinate hash seeded 0x570108 using unsigned32 mix in
fixtures.py, dyadic values /256 with signs. Storage conversion is performed
before independent FP64 math. Q F32, K/V F16, mask F32, scale 0.125.

The oracle uses logical arrays, scalar FP64 dot/softmax/AV and contiguous GQA
groups head//(Hq/Hkv). The address oracle independently inverts buffer coordinates
and compares actual graph view/shape/stride offsets, including all valid/padded
keys. It never uses floating labels. Numerics compare every actual QK, softmax,
AV, permute and final cont/concat element. Record absolute/relative/float32 ULP,
finiteness, exact count and error bins. No general tolerance-based PASS.
Structured QK must be exact; structured sparse single-key probabilities and
AV/final outputs must be exact. q1 constructs and executes the common original
nonflash graph; q2 invokes frozen PQ/QB helpers, alongside original MQ.

Four symbolic mutation negatives: query-offset reuse, modulo GQA mapping,
mask-column reuse, output query/head recombination. Rejection negatives:
nondivisible GQA, out-of-bounds Q view, mask stride, q>2. Pure CPU state model
checks role/phase/layout/ub/capacity identity and alternating q1/q2; it is not a
native binder test. Unknown state never authorizes switching midrequest.

Hypotheses kept separate: H1 semantic/lifetime mapping; H2 backend numerical
paths; H3 costs/materialization; H4 natural operand/state trajectories. Absence
of an H1 failure does not establish H2. Existing 49/48/1/31, 8110 callers,
cadence violation and 14 endpoint counterexamples remain NO-GO.
