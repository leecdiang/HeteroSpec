# CPU-only N1a native-chain preparation (partial, not admitted)

Parent: PR226 `87ea17971642f65468678cee8477505b9956611a`. New files only. No old sources, snapshots, data, reference, STATE, ledger, paper or deployment were changed.

## What was implemented

* `lifecycle.hpp`: C++17 C4096 sequential q1 lifecycle logic against an explicit mock backend interface. Reconciles at `min(LCP, materialized head)`, invalidates frontier, replays fully cached final token, appends pending once, owns complete finite vocabulary outputs, greedy lowest-ID tie break, keeps final sample pending, clears cold oracle independently, and poisons uncertain mutation errors. Request-state gates prevent incomplete append from sampling. This is NOT the frozen native reference or a working llama adapter.
* `budget/`: CPU-only persistent per-request/total reservations, exclusive process lock, fixed manifest identity, failure consumption retained, deadline and uncertain-I/O lockout. Native entry always refuses. This is not native request/launch enforcement.
* `writer/`: immutable owned F16LE/F32LE byte copies, finite/shape checks, no-overwrite directories, commit-last manifests and partial-write preservation. Compatible numerical descriptors are accepted by the unchanged #226 byte comparator. Synthetic receipts are deliberately rejected by its native snapshot validator. No native state is fabricated.
* `source_gate.py`: full-file SHA gate for actual deployment files documented by #225. Missing or mismatched files remain blocked. Matching files alone never admit a deployment.

Run `bash run_cpu_tests.sh` on Linux with Python3, Node and g++17. Tests create only synthetic data and short-lived mock C++ objects, not model/backend contexts. Python `-O` and C++ `-DNDEBUG` reruns exercise identical validation. No native dynamic library is linked. No benchmark, numerical qualification or timing estimate results from these tests.

## Hard blocker: actual source-bound native linkage

The repository contains only excerpts of original Linux reference `reference.cpp`, whose full SHA is `111401574d53c534e3a39cac75785ae5ae5fa9a61b44fc7ada989a96305f4723`. The old C1024 source is not a C4096 sequential reference. We did not reconstruct unseen code from excerpts, reuse another deployment, or use the newer producer runtime as proof of reference arithmetic.

Required on A5000 before GPU consideration:

1. Obtain the complete original reference/backend build tree and dependency hashes, plus exact strong worker and native active-KV capture APIs. Run `source_gate.py` on an explicit local path map, preserve mismatches and freeze a C4096 descendant separately.
2. Bind the lifecycle operations to that pinned backend. Compile/link without invoking backend init, model load, context creation, placement or forward. Demonstrate actual-state writer coordinate/layout binding and complete ownership/checkpoint receipts. The current synthetic writer is not this adapter.
3. Connect the persistent budget to every actual context/request/decode/placement entry. Add process supervision, runtime accounting and independently verify the 261-operation/checkpoint coverage; no native runner is delivered here.
4. Collect target-host RAM/disk/VRAM availability, owned-task/lock status, exact model/source/binary identities and bounded capture storage. The cloud snapshot is not A5000 admission.
5. Return these CPU-preparation results for separate finite N1a approval. Do not start execution from a JSON flag, idle GPU, previous quota or this PR.

## Still excluded

N1a numerical qualification, N1b LOCAL/packed, N2 performance, GPU timings, any universal5% claim. The proposal76 requests/85,738 rows/10 placements and551,473,155,769 bytes/5h is still unapproved, not a granted budget. No user decision is silently converted into a new measurement authorization.
