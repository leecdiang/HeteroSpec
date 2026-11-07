# CPU audit correction: metadata4 query tensor names

The original CPU auditor rejected the completed SmolLM2 qualification unit with
`local geometry lacks family-specific target layers`. All 98 requests had
already passed the host's complete historical endpoint and transaction checks.
The original rejection is retained in
`host_execution/SmolLM2/QUALIFICATION-original-auditor.json`.

## Source and retained evidence

The pinned metadata4 `src/llama-graph.cpp`, lines 2646-2647, calls the graph
callback twice on the same `q` tensor:

```cpp
cb(q, "hs_attn_query_batch", il);
cb(q, "jsa_llama_query_batch", il);
```

`llama_context::graph_get_cb()` at `src/llama-context.cpp:2530` assigns the tensor
name with `ggml_format_name(cur, "%s-%d", name, il)`. The second call therefore
replaces the first name. The worker's direct-node observer filters `hs_`/`kq`
names, but it also retains actual metadata for every source of each observed
node. Thus the renamed query survives as the second operand of `kq-N`'s
`MUL_MAT`, without additional capture or any new GPU request.

For SmolLM2 input0, the retained M_QB record contains all 24 query layers in these
operands, with measured `ne=[64,1,32,4]`, `nb=[4,8192,256,8192]` and the RTX device
description. C_QB contains the same 24 layers across its observed verifier
calls. These are existing tensor observations, not dimensions copied from the
requested configuration. Full qualification re-audits every fixed input.

## Narrow correction and unchanged requirements

`study.py local_geometry()` now additionally reads the second source of an
observed `kq-N` `MUL_MAT` only when its actual name is
`jsa_llama_query_batch-N`, the family is SmolLM2, and the bound source variant and
archive hash are exactly the pinned metadata4 cohort. Direct `hs_` observations
remain supported. It neither renames nor edits retained records.

All original requirements remain: the exact 24-layer set, actual head/query
axes, positive strides, GPU placement, measured physical widths, complete
historical endpoints, every required vector, PQ/QB byte/state equality and
off/on sentinels. Tests reject the wrong family, archive, operator, layer and
operand position, and verify that incorrect dimensions are preserved for the
existing shape gate to reject.

No executable, model, numerical DLL, native source, request schedule, resource
limit, calendar date, raw record or vector changed. No GPU request was repeated
or added. `AUDIT_CORRECTION_BEFORE.json` and `AUDIT_CORRECTION_AFTER.json` bind
the identical request/attempt byte streams and record the auditor revision.
This is a CPU evidence-reading correction, not numerical repair or a new
qualification run. The initial rejection remains visible.

Before formal execution, the continuation's source binding must reference the
commit containing this correction, while retaining the original execution
freeze `011e484b0ec98be800cae4dbcf75e8d9cfdfcbb2`. Runtime identities and the
frozen execution identity bytes remain identical. Three-date performance and
the separate Llama diagnostic are still pending.
