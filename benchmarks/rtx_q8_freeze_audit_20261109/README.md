# PR213 freeze audit (offline only)

Read [AUDIT.md](AUDIT.md) for the Chinese judgment, original pinned evidence links, exact timeline, recomputed coverage, unverified scope and optional minimal follow-up. Audit base: `ba5b4c8e01d50d4bfaab1ac3908f798347be063a`; design: `ad9fb6846dd979c3a76d3c415c74fa9f86565f7d`.

No GPU/native worker/tokenizer was executed. The independent readers use Python/std-lib/NumPy and read existing raw files. Source pool reconstruction additionally reads the existing pinned PyArrow sources. They do not import the old gate validators or executors. The optional supplement is an explicitly NOT RUN JSON draft, not a runner or authorization.

For another offline replay, use a fresh audit output directory: `put()` intentionally rejects existing proof files. Run `core.py`, `recheck_numeric.py`, `recheck_design.py`, `recheck_coverage.py`, `supplement_plan.py`, `recheck_runtime.py`, then `write_report.py`. Existing experiment paths are hard-bound in `core.py`; inspection does not reset or amend their ledger. All numerical comparison remains full-byte SHA256 equality; only independently reordered statistical sums use a1e-12 consistency threshold.

`NUMERIC_RECHECK.json` records the actual6232 full-vector and1224 active-KV comparisons, not legacy success flags. `RAW_FILES_READ.json` lists all8102 original binary paths/hashes read in that pass. The other proofs cover original source/input hashes, exact first Git appearances and local times, independently reconstructed cohort, full1024/128 panel accounting/bootstrap, live reader repair, runtime identities and the uncaptured joint state scope. Original capture bytes stay in the PR213 runtime and complete archive; no model weights are copied.
