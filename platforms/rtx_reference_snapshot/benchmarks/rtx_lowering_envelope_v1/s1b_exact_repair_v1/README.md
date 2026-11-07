# Exact-byte binding / archive delivery repair

CPU-only repair of PR118 reviewed commit
649ebaf44a3d21445ce1512f77dc0e707d297150. Historical source, F0,
authorization, raw, failed slots and accounting remain untouched.

The new registration is `pr116-s1b-exact-r1`, with independent execution root
`D:/hs116-s1b-cost-v1-exact-r1`. Native `run_id` remains
`pr116-s1b-cost-v1`: it is a compiled host namespace, preserved to keep both
native executables byte-identical. This is a new exact-F0 execution registration,
not permission to resume the historical root or its stopped authorization.

**authorization binds exact bytes consumed by the execution entry**.
The sole Census artifact is the original native CRLF file, SHA256
d8c79ed1b4fc748ec8ce22a201137ef6fc201de79052fa7c6c4f7711806e8256.
`exact_binding.admit` reads and hashes those bytes and returns the same bytes to
the consumer. JSON parsing happens only after exact byte admission for support
inspection; it never substitutes for byte admission. The LF seal remains an
unchanged historical artifact, not an execution authorization alias.

The native executable, arithmetic, graphs, DLLs, inputs, ordinary references,
precision, readiness, 72 Block0 coordinates, 1+8 loop and cost rules do not change.
The identical host and identical 72 graph descriptions permit reusing the
existing 72/828 clean Census; no Census is rerun. PR116's separate 120/1806
numerical Census is also unchanged. No new CUDA identity/output/timing
qualification is inferred from this CPU repair.

`publication.py` rebuilds all declared member hashes, explicitly force-stages
the archive/manifest, checks index and actual commit bytes, then independently
enumerates and hashes every remotely downloaded/restored member. VERIFIED may
only be written after actual remote authentication. Prior 404/ignore failure
records remain in the historical directory. CPU regression records, including
the intermediate missing-test-input failure, are retained in CPU_RECORDS.zip.

Only a future independently approved `--stage clean0` can be accepted. It must
bind the new F0, registration_id, exact native Census hash and Decision hash.
There is no Census, Block1/2 or trace CLI choice. The new root and ledger must
not exist before first admission. No author approval is created by this repair.

CPU repair/audit complete is distinct from GPU permission or numerical
qualification. Stop for independent Block0 author approval after final sealing.
