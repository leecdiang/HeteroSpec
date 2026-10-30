# Independent Llama diagnostics and incremental evidence delivery

The main cohort is unchanged: qualification196, date0 measurements336 and
warmups28; 560 main requests are retained without rerun. The registered formal
dates remain October30/31 and November1, with both first-session 20-hour gates.

The registered independent Llama stream is now **54/54 completed and audited**:
A1=18 and A2=36. A0 made zero native requests. See
[diagnostic/STATUS.json](diagnostic/STATUS.json),
[diagnostic/AUDIT.json](diagnostic/AUDIT.json), and the pre-execution binding in
[diagnostic/FREEZE.json](diagnostic/FREEZE.json).

The known failure reproduces in the new runtime: strict R matches historical R,
while C_PQ/C_QB differ on CodeContests/valid/108. Both registered controls match
historical R. Under both P1 and P4_NATIVE in A2, the scoped target-only M_PQ/C1
matches R while C_PQ/C_QB still differ on the known case. All observer pairs
match in endpoint/transactions/final KV, and all paired PQ/QB heavy decision
vector inventories and bytes match. These are bundled producer/consumer recipe
observations; no common state was transplanted and no consumer-only causal
effect or repair is claimed. The earliest operator divergence remains unresolved.

Read-only alignment of the retained decision vectors is recorded in
[diagnostic/DECISION_COORDINATES.json](diagnostic/DECISION_COORDINATES.json).
On the known case, A1's first unequal committed target vector is at zero-based
output index29, while the first unequal emitted token is at index81. This
alignment uses the same committed token prefix, not an asserted common numeric
KV state. Both controls' aligned A1 committed target vectors match R. The
historical first and next captured target decision vectors also match across
R/PQ/QB. These coordinates describe existing evidence and consume zero new
requests; they do not identify the earliest internal operator divergence.

All 5916 new full-vocabulary vectors are retained. Actual fresh-context teardown,
producer call counts, 32-layer geometry, finite vector argmax, transactions,
execution identity, timing bounds and process cleanup pass the independent
diagnostic auditor. No extra capture/replay, checkpoint/restore, repair
confirmation or retry was run; the main 182-request reserve remains untouched.
All diagnostic clocks are excluded from performance estimates.

The sidecar lives in `scripts/experiments/rtx_scope_sidecar_v1`, outside the main
freeze's source directory. The immutable main EXE, DLLs and source files are
reused read-only. The live diagnostic evidence root is
`D:\rtx151-llama-diagnostic-v2`. The earlier failed CPU-only preparation directory
is retained and contains no native request.

The archive tool seals completed bundles into independent copies, hashes every
member, packs bounded parts and verifies fresh remote downloads including every
ZIP member. Its final archive receipts are separate from diagnostic completion;
do not infer remote delivery merely from a local manifest or a successful upload.
Formal timing always has priority over diagnostics, CPU audits and archival IO.

Date1 must begin on October31, SmolLM2 then Qwen, and both families reload again
for session1. Date2 keeps the registered Qwen-first order on November1. The
frozen `study.py audit` and `study.py analyze` commands remain the analysis
interface; they refuse a complete study estimate before all six sessions per
family and all three dates are present. No day0 timing is used to select later
inputs, work, or claims.
