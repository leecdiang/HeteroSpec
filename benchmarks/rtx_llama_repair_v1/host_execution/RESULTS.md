# RTX Llama causal-prefix repair

Execution is in progress. This record separates completed mechanism evidence from the confirmation and delivery gates, which are not yet complete.

The starting protocol is PR160 at `aff1d029966a20adebfad6b664a36f32ed04bf9c`, based on PR159 at `38b3d3d3929dc958e6a2a7e0bdc8abd61ff38ab1`. This is a separate results branch. The original R executable, model files, tokenizer, metadata4 source archive and numerical DLL cohort remain unchanged. Earlier PRs and their ledgers remain intact.

## Historical reconstruction and default baseline

`history.py` authenticated all 54 PR151 Llama diagnostic requests and all 5,916 complete 128,256-element F32 decision vectors. The request manifest digest is `2e52aee27acb551f3f3556a566ec5f83b123aa0d50a9c01da3666ac33a2fa4b9`. The default roles=0 build had no numerical extension and no Qwen normalization patch. It passed native capacity admission and completed the registered 36-request matrix.

All nine heavy R/C_PQ/C_QB cells across the original failure and two controls reproduced their historical endpoints and every saved vector. Thus the baseline reproduced the failure rather than replacing its reference. CPU test success was recorded separately and was not used as native validation.

For CodeContests/valid/108, the first output mismatch at output index 81 maps to actual cycle 21, row 2, base 815 and input position 817: old R selects token 16, whereas both baseline C arms select token 15. The earliest saved common-prefix vector difference is output index 29 at cycle 8, row 0, base 765. These mappings come from the actual recorded cycles, not division by the draft length.

## Mechanism evidence

At cycle 8 the four consumed positions are 765–768. Single-row consumption uses a physical KV extent of 768 for the first three rows and 1,024 for the fourth. A natural four-row verification uses 1,024 for every row. On exactly the same candidate KV and pending state, the baseline q1 and q4 consumers differ in complete vectors, while the q1 vectors match the old R vectors at this point. At cycle 21 the same-state consumers agree, including the wrong decision: the earlier state divergence has already propagated.

The q4 own-path replay matches natural execution. Both shadow orders, trace/no-trace controls, live-state invariance and unchanged natural outputs were checked. Captured layer-zero Q, visible K, visible V, visible QK and valid probability values agree bitwise, and the masked probability suffix is exactly zero.

Twenty-two standalone native CUDA operator executions include repeated own-path reconstructions and crossed-extent interventions. The operator experiment uses the first query of actual C_PQ execution at the captured checkpoint. Both consumers lower this attention operation per query, so the captured query width is one on both sides; their physical KV extents differ. Padding the q1-consumer probabilities with zeros and using the 1,024-wide V operand reproduces that query's q4-consumer V×probability output. Cropping the q4-consumer probabilities and V operand to the 768-wide scalar extent reproduces its q1-consumer output. Softmax crop/pad controls preserve the visible probability bits. This isolates physical reduction extent as the causal variable in this captured attention operation. C_QB transfer is validated by its separate same-state and natural matrix controls. The Llama cause is not attributed to Qwen RoPE.

Scheduler evidence places these operations on CUDA0. Source inspection is consistent with a reduction launch geometry change; an exact profiled kernel launch is not claimed.

## Structural intervention and retained failures

The repair groups maximal adjacent query rows that have equal scalar-equivalent physical KV prefix extent. Extents are computed from actual cache occupancy, slot head and native padding, rather than from a task, model name, answer, output index, layer or margin. The rule is guarded to dense contiguous single-stream append, ordered single-sequence causal non-flash attention. It crops Q/K/V/mask views for each group, materializes a shortened mask when necessary, concatenates the attention outputs, and includes the prefix extent vector in graph reuse checks. Other paths retain the original behavior.

The combined candidate retains PR159's separately established Q/K head-normalization offload policy for Qwen regressions. Llama 3 has no such head-normalization nodes; that policy is not asserted to explain this Llama failure.

The first operand observer rejected a legitimate scheduler mask copy; its failed unit and reservation remain. The observer was repaired by checking the exact scheduler-copy naming, operation, storage disjointness and source-bound scheduler behavior. The first structural candidate failed the native contiguous-mask assertion after 10 of its 36 reserved requests. Its source, build, partial raw and all 36 reserved credits remain. The successor explicitly materializes noncontiguous masks. A related build containing the known faulty mask policy was retained without native execution.

The repaired candidate completes all 36 development requests with original-reference and observer equality. All 18 heavy cells' committed decision vectors equal the corresponding original R vectors. Eight repaired same-state pairs across both arms, both orders and trace/no-trace have equal complete q1/q4 vectors and pass own-path controls. A fresh ablation process with the structural repair disabled restores both original failures, including their vectors and states.

## Gates still in progress

New Qwen 8B and 14B regressions pass all 144 and 192 requests respectively under the same structural source policy, fixed original assets and previously exposed inputs. The additional 24 and 32 successful immutable original-R requests preserve complete R vectors in both native and reference-prefill candidate R cells. These are development work charged to the same ledger, not unseen transfer evidence. Failed original-worker schema attempts remain charged and preserved.

The first freeze attempt found that the immutable PR151 input records lack a text-hash field. A host-only successor (epoch07, unchanged candidate EXE and numerical policy) binds and checks the complete historical ID/text/token union, and correctly routes original-R records through their original schema. The previously selected panel remains unchanged and had no model outputs before this correction. The prior host source and failed freeze receipt are retained; all 73 CPU tests pass without skips, and capacity admission and the 36-request development matrix are repeated before freezing the successor.

The intended confirmation remains the registered 24 unseen inputs, balanced over code/math and short/long strata, followed by 48 old-R references, 240 candidate qualification requests and six complete Williams timing sessions (864 measured requests plus 864 warmups). No formal input has yet been run. Any qualification failure exposes the entire panel and precludes timing a successful subset.

Final costs, independent recomputation, complete archival manifests, remote upload/download readback and the separate results PR remain pending. No speed or practical layout-gain claim is made here.
