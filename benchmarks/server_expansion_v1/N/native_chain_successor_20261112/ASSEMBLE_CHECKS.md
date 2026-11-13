# Future capture assembly: file-only, no native execution

assemble_checks.js exports inventory(CAPTURE_ROOT, proposal) and
assemble(CAPTURE_ROOT, proposal). Both are pure Node file readers. They do not
create or run a model, native worker, tokenizer, context, resource probe or GPU.
The caller supplies the dedicated common capture root and the unchanged #226
N1A_PROPOSAL_NOT_ADMITTED.json. Admission remains separate and false.

One common root contains writer capture subdirectories and hashed flat receipt
JSON files. WorkerCapture's stored tensor paths are relative to that root; nested
per-worker roots cannot silently be rewritten. Output files must be fresh and
outside the read-only capture root. No STATE, capture or failed data is removed.

The exact frozen261 graph derives252 state snapshots,72 owned-vector events,
27 reconcile,36 mutation and36 ownership binding receipts. Current worker source
also requires24 complete producer receipts: four natural two-turn sessions in
R/repeat-R/strong, with no invented cold-oracle producer. Eight worker contexts
must be distinct, consistent within each registered path/cohort and share one run.

Inventory rejects duplicate/unplanned evidence, symlinks/path escapes, poison or
uncertainty markers, malformed/duplicate JSON members and changing files. An open
or incompletely committed capture stays incomplete. SNAPSHOT/COMPLETE/pending
receipts and every actual raw tensor byte count/SHA are checked as transport only.
The identity/header phase, natural/control cap and model/template bindings are
checked without treating their digests as numerical evidence. Actual native source,
executable freeze and authorization are external gates.

Reconcile and ownership records bind exact source snapshots and lifecycle events.
Producer records bind actual prior generated IDs/stop/cap to the prior terminal,
the exact user, stored history and safe wire message. R/repeat/strong producer
receipt fields are compared separately; nonsemantic wire metadata such as creation
time and request ID is not compared. This does not rerun a parser or tokenizer.

Only a complete, unambiguous set constructs the261 comparison manifest. The code
then calls the unchanged frozen verifyProvidedRaw, which compares all required
vectors/active-KV bytes, retention, ownership and reset conditions. A PASS is named
COMPLETE_PROVIDED_RAW_REPLAY_PASS_NOT_NATIVE_CERTIFICATE. It cannot attest that
native receipts were truthful or authorize any experiment. Negative results remain
negative and no replacement/retry is launched.

With absent/empty real captures the output is NOT_RUN and comparison_manifest is
null. Partial data is CAPTURE_SET_INCOMPLETE; invalid or ambiguous evidence is
INVALID_CAPTURE_SET. No synthetic261 native-pass packet was made in preparation.
The ten CPU tests use explicitly invented partial filesystem fixtures only.

CLI:

    node assemble_checks.js --inventory CAPTURE_ROOT FROZEN_PROPOSAL.json FRESH_INVENTORY.json
    node assemble_checks.js CAPTURE_ROOT FROZEN_PROPOSAL.json FRESH_ASSEMBLY.json

Saved preparation evidence is in review/ASSEMBLER_CPU_RECEIPT.json and
review/ASSEMBLER_NOT_RUN_INVENTORY.json. The latter uses an explicitly unregistered
missing capture-root placeholder; it is not a discovered running job or fabricated
native dataset. Full actual writer-to261 replay remains NOT_RUN until a real,
separately authorized capture set exists.

