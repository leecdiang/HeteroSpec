# Cloud-only draft result, no device execution

The candidate isolates draft physical ubatch1/2/4 while preserving draft output
reserve1 and every target constructor call/effective parameter. The exact frozen
#151 worker is the input, and the derivative rejects original study slots.
The original experiments, model files and numerical libraries are untouched.

Current checks:
- 9 source-stage tests, including CRLF byte-pin rejection and unchanged target
  request algorithm/target calls.
- Fresh unmodified source-kit candidate CPU llama library built successfully at
  j1 after a retained j2 OOM. This is PR171 source, not the #151 RTX binary.
- Two original synthetic models plus two separately derived norm1 stress models:
  75 cases and114 verification cycles each; zero compared target-vector mismatch,
  exact serialized committed sequence match, pending/endpoint/reset checks pass.
- UBSan applies to the test executable only. No whole-runtime sanitizer claim.
- Independent review rejected two test mutants after corrections: premature
  one-token termination and discarded committed KV. The latter is caught by
  serialized sequence bytes, not necessarily continuation logits.
- Original Q8 has no logit history sensitivity in the six reviewed probes. The
  stress models improve four generic probes, but do not cure the specific
  continuation blind spot. All earlier results and failures are retained.

What this does NOT establish:
- Windows worker compilation, physical CUDA execution or service speedup.
- Qualification of the #151 scoped ubatch4 target on new proposal trajectories.
- Production rollback, cache leases, all hidden padding/state or arbitrary model
  correctness. Target code unchanged is not such a proof.
- Fewer singleton DRAFT_SYNC/PROPOSE calls. Only context microbatch capacity changes.

This candidate is prepared as an independent draft for review. Execution would require a separately
reviewed/budgeted protocol and Windows build, then actual-model target forced-
prefix/full-vector/state/endpoint qualification before any performance claim.
Do not modify or reuse historical scientific bindings to run this candidate.
