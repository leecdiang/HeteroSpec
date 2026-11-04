# Independent protocol audit and targeted improvements

Date: 2026-11-04. Audited PR179 at `d694011de1065701b25840f30e25cc532c27f52d`.
These changes improve CPU protocol correctness and cache usability. They do not
establish new GPU numerical qualification, speedup, or paper acceptance odds.

## Reproduced failure: failed callback could leave CLEAN metadata

`execute_operator` tainted the live state before calling an operator, but a
callback could inadvertently write `live.clean=true` and then return false or
throw. Both paths left `clean=true`, violating the function's stated failure
invariant. A standalone compiled reproducer returned `success=0 clean=1` and
`exception clean=1`. The trusted-callback boundary does not make this desirable:
the interface already detects unexpected position/recipe mutations and should
conservatively retain taint on every noncommit exit.

A transaction scope guard now sets `clean=false` unless the function explicitly
commits success. Regression cases include operator false return, thrown failure,
and verifier false return after a write to clean metadata. No claim is made that
this protects against malicious in-process callers or uncontrolled concurrency.

## Proof assumptions must be executable obligations

Previously `structural_assumptions` required only a nonempty text description.
That text is useful documentation but cannot check data-dependent premises such
as finiteness, aliasing, or an execution-layout invariant. Qualification records
now require a trusted per-request predicate whenever assumptions are declared.
The predicate is evaluated on the current request; absent, false, or throwing
checks deny optimization. A stable qualification copy is retained during it.

The predicate is still a host trust boundary, not a proof checker. A host must
bind it to the actual operands/state for the declared assumptions; returning
true blindly is not evidence. Unconditional bit-semantics claims remain trusted
records, not independently verified theorems. Tests exercise missing predicates,
changing premise values between requests, and exceptions.

## Separate cache lookup identity from stored-state integrity

The original `ExactRecipeCache.get(key, expected_capsule)` requires expected KV
and logits bytes. That is useful for exact artifact lookup/integrity, but cannot
by itself implement a prefix cache that avoids producing those bytes first.
It is retained for compatibility and is not relabeled as a serving scheduler.

`CacheIdentity` and `PrefixCheckpointCache` add a separate lookup path based on
known deployment, exact producer recipe, tokens, positions, and pending metadata.
The caller does not supply KV/logits for lookup. The cache stores only previously
qualified immutable checkpoints, compares full identities after digest lookup,
and separately verifies stored-state integrity. If the same full identity yields
a different state, the identity is quarantined rather than choosing one result.
This deliberately reveals an incomplete recipe or noncanonical producer instead
of silently resolving it. Cross-recipe compatibility is still not inferred.

`StateOwner.restore_cached_checkpoint` performs identity/receipt admission,
imports the full capsule, and publishes the new clean state only after complete
readback. Failed import preserves the old recovery checkpoint and leaves the
context tainted. Tests include digest collisions, conflicting states, malformed
identities, corrupted integrity, wrong recipes, successful import, and partial
import followed by recovery.

This is single-owner Python protocol behavior. It has no eviction policy,
concurrent sharing, GPU resident page manager, or native Python adapter. Integrity
checking hashes the stored bytes and can be expensive. It is not a claim of
production hit rate or favorable serving cost.

## Unchanged hard limits

- CUDA enforcing mode still refuses a backend split; observations do not become
  certificates. CUDA collect mode changes capture/fusion policy and cannot be
  silently treated as the unmodified reference deployment.
- Actual GPU toolchain/binary qualification, source-to-machine semantics and
  full-reference replay are still needed before enabling optimization.
- The current native owner synchronizes and exports complete state before and
  after append, retains copies, and disables relevant graph reuse. These costs
  can dominate the old approximately 4% packing improvement; old performance
  results must not be attributed to this implementation.
- Full-state transaction tests establish restoration on a tiny CPU fixture,
  not Qwen GPU correctness, concurrent service safety, or a TPDS-level result.

## Follow-up review and executed validation

A second reviewer reproduced the analogous Python failure: a callback writing
CLEAN and then failing could leave clean metadata. `qualify`, `execute`, own
checkpoint restore and cached-checkpoint restore now use explicit commit guards,
leaving TAINTED on every unsuccessful exit. Regression tests include false
results, exceptions and partial imports after accidental metadata writes.

The audited revision passed 61 Python tests and 652 primary plus 72 independent C++ checks, including UBSan
and shared-library binding. A fresh staging/build of the complete authorized
source kit also passed 47 real tiny-Q8 CPU native transaction checks, 16 real CPU
tensor checks, 19 CPU CUDA-audit ABI fixture checks and eight upstream state cases.
These are distinct scopes, not thousands of independent numerical experiments.
CUDA compilation/execution, Windows and Qwen GPU qualification remain unrun.

Independent review reproduced the failure paths, reran the protocol suite and
ran the fresh native binaries. Its additional C++ and cache probes are now
committed as `test_independent_execution.cpp` and `test_independent_cache.py`.

## No append-atomicity assumption

This revision retains full-context restoration, not a delta undo log. Native
memory updates can occur before graph construction, K/V `SET_ROWS` may scatter
writes, and a later microbatch failure does not make the entire logical batch
atomic. A future low-overhead recovery path must account for the complete
logical-batch write set, allocator/shift/copy metadata and output/sampling state.
Suffix removal alone is not such a recovery protocol. None of the added cache
lookup or protocol tests proves a native incremental-rollback implementation.
