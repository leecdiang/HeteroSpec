# PR128 independent review — 2026-10-20

## Decision

**Eligible to merge as a scoped experimental evidence archive.** No P0–P2 finding was identified that blocks that scope. This is not a general Vulkan/GQA admission certificate, a CPU8/F0 qualification, or permission to rerun the historical native launchers.

Reviewed repository: `leecdiang/HeteroSpec`.
Pinned head: `cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9`.
PR: https://github.com/leecdiang/HeteroSpec/pull/128

The current author request permits review and merge; prior Draft/no-merge wording remains useful historical context but should not be mistaken for an experimental result.

## Scope and source review

The complete GitHub PR file list and patch collection contain **56 added files, 17,751 additions, zero deletions**, exclusively beneath `benchmarks/b570_qb_batch_broadcast_v1/`. Existing active runtime files are not modified. Reviewed the three C++ harnesses, portable admission patch, CPU numerical-check scripts, balanced and transaction statistics, historical PowerShell launchers, packaging/closeout logic, frozen design and evidence summaries.

No AGENTS.md exists at the repository root, benchmarks/, or the new subtree and its balanced/transaction directories at the pinned head (GitHub returned 404 for each).

The portable patch admits only ordinary MUL_MAT satisfying:
- contiguous F16 A and F32 B;
- A fourth extent = 1, B fourth extent = 2 or 4;
- B second extent = 1;
- equal A/B third extents.

The candidate source snapshot from PR129 `SOURCE_SNAPSHOT.zip` exactly matches PR128's recorded candidate SHA256:
`c16de703ff610cb10d4f4b19b64a1f4bb2e36ad57047b1443b718725da939576`.

Reverse `git apply --check` succeeded; reversing the patch reconstructs the recorded baseline SHA256:
`04615c97998a76d2d0b15d2ebb93bf381eb3fb565492d7714d3fc9d1c333b98d`.

Source reasoning confirms that contiguous A bypasses the p021 and nc paths, whose restrictions would otherwise matter. The normal matrix-vector path derives r3 = ne13/ne03, carries broadcast3 through push constants, and retains existing noncontiguous B staging. Relevant candidate source locations: support predicate 18976–18986; dispatch selection 10242–10265; broadcast ratio 9743–9748; staging 9751–9787; dispatch constants 9927–9938. No shader was newly compiled: 147 frozen shader objects were reused. The narrow source finding should not be rewritten as “Vulkan generally supports QB”.

The unchanged query_head.h dependency was fetched at PR112 head `0c26448970fd89ad2b6639788479d90a57724bf9`; its exact SHA256 matches the frozen build manifest:
`2cf9dbc2efe7dcb6d9e4b122ed6b5040ca7d908ed6aacb1e569777ad5c340785`.
Its source is not included in PR128's new subtree; reproducing the build still requires this pinned dependency and the documented external Windows runtime/build inputs.

## Experimental validity and independent verification

The transaction harness:
- constructs permuted QB and compact QH_C views at transaction.cpp:128–142;
- checks support, original K/V objects, absence of REPEAT, and QB_A/B node metadata equality at 142–153;
- checks FP64 stages and cross-arm complete final bytes before timing at 159–179;
- times one continuous copy/transpose → Q upload/sync → graph/sync → full final readback/sync window at 181–201;
- checks every transaction's complete final bytes outside the timed window;
- balances all six arm permutations and preserves each sample at 213–240.

CPU-only verification performed here:
1. Downloaded and unpacked both compact NATIVE_EVIDENCE.zip files through the GitHub plugin.
2. Reran both unchanged analyze.py files successfully. Each differs from archived JSON in only two floating-point last-bit fields, maximum absolute difference **1.1102230246251565e-16**. All nine coordinate conclusions and each fixed panel remain UNRESOLVED.
3. Independently checked that all three transaction sessions contain exactly the expected 162 paired-block coordinates, 81 successful support/numerical/transaction slots, 15,633 returned graph computations, and normal cleanup.
4. Checked q1 graph metadata identity across all three arms for a representative key coordinate; the source also routes every q1 arm through the same original graph and memcpy path.
5. Verified all **17 downloaded compact entries** against the full transaction manifest.
6. Decompressed the **7,819-artifact manifest**, whose SHA256 exactly matches the recorded `59178c76ef8b0d3f67aa939bd032f267ac83f31958d128d5fb131709cbc22c51`.
7. Exact fetched transaction.cpp, preregistration, RUN_ALL.ps1, analyze.py, verify_raw.py and query_head.h bytes match their frozen build entries.
8. Checked all **243 complete-final witness hashes** agree across the archived resident and transaction CPU raw-check reports.

The full raw tensors (7,782 transaction raw files, 4,356,096,428 bytes) remain on the original Windows machine. Therefore the current independent review confirms compact metadata, statistical reconstruction, source identity and witness consistency; it does **not** independently re-execute all array numerical comparisons or externally authenticate every raw tensor.

No GPU/native/model/actor/RTL process was launched in this review.

## Numerical results

| Fixed equal-weight q2/q4 panel | Resident compact-Q graph | Common permuted-Q transaction |
|---|---:|---:|
| QB_A mean (us) | 125.4962243 | 187.0133539 |
| QB_B mean (us) | 125.2727675 | 187.8193210 |
| QH_C mean (us) | 124.3567901 | 185.8982922 |
| QH_C minus dual-QB (us) | -1.0277058 | -1.5180453 |
| Adjusted difference interval (us) | [-2.1765299, +0.0669518] | [-4.1677178, +0.9156414] |
| QH_C/dual-QB geometric ratio | 0.9918966861 | 0.9922438237 |
| Adjusted ratio interval | [0.9841056292, 1.0003563305] | [0.9799075402, 1.0046911898] |
| A/A practical-screen threshold (us) | 3.4447222 | 17.2838889 |
| Decision | UNRESOLVED | UNRESOLVED |

There are only three process clusters on one device/date, with three fixed synthetic input sets. The 43,740 transaction calls are technical repeats, not independent workloads. Transaction session mean differences are +0.0980, -2.5218 and -2.1304 us, so one session reverses direction. The conservative A/A screen and intervals correctly support retaining QB, not an equivalence claim or a declaration of universally optimal mapping.

Resident and transaction windows change both layout and cost scope. Their absolute means must not be subtracted to infer isolated transfer/packing cost.

## Budget and archival boundary

PR128 transaction parent charges are 9.8485258, 8.0238481 and 8.0635999 seconds. All three process receipts show observed exit 0, complete capture, no requested deadline kill and normal backend cleanup. New charge is 25.9359738 seconds; prior 27.8414773 seconds is preserved, yielding **53.7774511 / 300 seconds** at this historical head. PR129 subsequently advances the ledger, so any future executor must use the latest cumulative charge rather than this snapshot.

These are historical one-shot launchers with absolute Windows paths and frozen starting balances, not reusable CPU8 supervisory infrastructure. RUN_ALL.ps1 refuses an existing ledger, and RESULT.md explicitly prohibits restarting historical accounting. No old UUID, budget, CPU8 matrix or F0 was modified by this PR.

## Paper implications

The new evidence weakens a proposed hardware justification based solely on “the backend cannot accept QB” or “compact query-to-head must be faster”. A small admission repair enables the tested equal-head mapping; balanced software comparisons reveal no practical QH_C gain in either studied window. This is useful for a systems paper because it distinguishes backend admission, numerical qualification and charged implementation cost.

It does not settle:
- real model GQA and q2/q4 execution;
- natural Q production, ongoing KV updates, or full request critical path;
- physical GPU bandwidth, occupancy, submission or arithmetic bottlenecks;
- hardware PPA or end-to-end accelerator benefit.

Retain SOFTWARE_FIRST/HOLD. Use PR129 to decide whether the studied region matters on a real request, then require qualified natural q2/q4 geometry and an observable practical residual before an architecture prototype.

## Sources

- https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/transaction_v1/RESULT.md
- https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/transaction_v1/ANALYSIS.json
- https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/transaction_v1/PAPER_INTEGRATION.md
- https://github.com/leecdiang/HeteroSpec/blob/cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9/benchmarks/b570_qb_batch_broadcast_v1/qb-batch-broadcast-portable.patch
