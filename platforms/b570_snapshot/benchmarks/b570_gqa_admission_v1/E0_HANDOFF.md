# E0 recovery and E2 exit

Pinned review/design: PR130 `7a209727f151f375c28653605f58252b6da77953`.
Scientific parents: PR128 `cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9`, PR129 `c541241ad62213a8d31006e539e4ce0623793040`.

| Item | State | Evidence / consequence |
|---|---|---|
| Old request R versus new clean q1 reference | INCOMPATIBLE qualification scope | No old qualification inherited |
| PR129 model identity | KNOWN | Qwen3-8B Q8_0 SHA256 `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6` |
| PR129 request | KNOWN | Exposed HumanEval/42,124 prompt IDs,16 output cap,greedy,ubatch1; actual q1/key256 |
| Natural q>1 values/state/endpoint | MISSING | New operator data remain synthetic |
| Natural QK K descriptor | KNOWN | F16 ne[128,256,8,1], nb[2,2048,256,2097152] |
| Natural Q descriptor | KNOWN for q1; DERIVED for q>1 | F32 ne[128,q,32,1], nb[4,16384,512,16384*q] |
| Natural AV V descriptor | KNOWN | F16 ne[256,128,8,1], nb[2,2048,262144,2097152] |
| KV format/capacity | KNOWN | F16/capacity1024; physical256 is distinct from capacity |
| Mask state | DERIVED | Synthetic causal masks, no natural speculative transaction claim |
| Head map | KNOWN from graph contract | h -> floor(h/4); QB query dimension3 |
| Graph mode | KNOWN | Direct fresh graph compute/synchronize, no CUDA replay or model graph cache |
| Old PR128 support | INCOMPATIBLE | Equal heads and contiguous A do not cover natural GQA strides |
| Candidate E2 support | Observed for executed descriptors | Not a general admission certificate |
| Candidate E2 numerical qualification | FAILED | key512/q2 first AV mismatch; later q4 unexecuted |
| Phase/request costs | MISSING | No inference from PR129 combined profiler subtotal |
| Actor/CPU8 qualification | Unchanged | No actor or CPU8; CPU8 0/8, no F0 |
| Available remaining budget | KNOWN | 51.5894409 seconds, no reset |

## Next platform action

Do not run a model request with this candidate. Retain the failed patch for review only.
CPU-only next work can check whether existing nc AV dispatch can process each lifted query using equal-batch views and the same arithmetic kernel. Preserve shared V, no REPEAT, offsets and output order; source review must establish correct lifetimes/synchronization and no changed q1 branch. Do not claim this is already implemented or equivalent.

A new experiment, if selected, must first freeze a distinct candidate and reference contract, reuse the complete six-coordinate test without dropping key512, and carry forward248.4105591s. A single process with20s execution plus15s cleanup/capture admission reserve fits the current51.5894409s; that is a proposal, not a new budget or executed slot. First failure stops again.

Only after a full GQA pass should a separately frozen natural speculative request bridge be considered. Its required draft/target/accept/reconcile/cache/endpoint controls and actual process budget are currently unresolved; the remaining balance is not evidence that the full request matrix fits.

PR130's research decision remains SOFTWARE_FIRST/HOLD. This negative E2 evidence strengthens the distinction between reachable backend paths and reference-preserving mappings; it provides no new accelerator, request speedup or physical bottleneck result.
