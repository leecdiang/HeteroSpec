# Integrate into the actual Linux successor, not the design-only ABI

Bind immutable source/build/module/model receipts from the executing PR196 successor.
Reuse its native contexts, transaction/state reader, supervisor and cost ledger.
This package supplies plans/parameters/offline inspectors; it does not ship an
already qualified six-lane runtime. No parallel replacement audit framework is needed.

The original PR196 example worker/runner hard-codes parts of Qwen/Smol, C1024, k3,
output reservation and a single UUID. New stage fields cannot simply be added to
JSON and assumed effective. Implement a **versioned native capability echo** that
reports actual model hashes/structure, context size, output capacity/mask, k,
draft physical width, target/draft placements, cut/projection recipes and observed
physical rows. Before timing, compare every requested field with the actual echo;
unknown/ignored fields must fail rather than silently execute old defaults.

Required adaptations by lane:
- M: four D4 combinations already have components; add two missing combinations to
  the common frontend. For k7, size requested-output storage to8, update transaction
  indexes, transient capacity and row ownership, retain reference UB1/reserve1.
  `verification_spec.hpp` tests only parameter relationships, not the transaction.
- D14: add an exact-hash model profile with real metadata and full GPU placement.
  Parameterize context/output allocation in both new deployment R and candidate.
  The C4096 reference is independently fixed; no claim of byte identity to C1024.
- Q4: inspect actual mixed tensor types and kernel selection; implement typed
  arithmetic recipes. Do not change a Q8 whitelist into a wildcard.
- N: add resident append/turn state handoff, materialize pending and template suffix
  exactly once, validate true token prefix and observed cache head. Reference follows
  the same declared sequential history, not a convenient cold whole-prefix replay.
- F: use archived Llama exact bytes, template/vocab and the frozen shared rules.
  Evaluate rule transfer before adding model-specific repairs. Generic source
  changes are allowed but become an explicitly extended version, not zero-change transfer.
- X: split model device/context parameters and bind two authorized UUIDs; do not
  remove single-GPU protection from PR196. Keep target intact on its original GPU,
  independent draft KV, and explicit token/control transport for greedy inference.

Qualification: original requested full target vectors, active committed KV and
logical frontier, producer, first/later rejection, rollback, pending/correction/bonus,
native EOG, cap1/cap128, tails/reset and clean/heavy correspondence. Observe actual
physical widths. Finite scope is recorded. No formal proof is inferred from replay.
Clean supported paths must retain valid graph reuse and exclude heavy state export/
reference replay. Diagnostic instrumentation costs and perturbation are separate.

Every result record consumed by the shared analyzer must include root, session, arm,
status, qualified, reference_id, target gpu_uuid, declared clock, evidence_path and
its SHA256. `qualified` must be backed by the native proof registry, not assigned
because a process returned zero. Session N records aggregate **complete episodes**,
including all turns and initial setup, so turns are not pseudo-independent samples.
Timing must include real execution/copies/synchronization/reset/required state work;
actual burst/startup/worker windows are separate inclusive clocks and are not added.

Do not edit historical GGUFs, sources, freezes or results. Never upload company
credentials, other users' process command lines, private datasets or unrestricted
host inventories. Public benchmark/model access follows its licenses and company rules.
