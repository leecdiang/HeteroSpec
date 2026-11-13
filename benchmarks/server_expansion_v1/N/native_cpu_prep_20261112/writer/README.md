# CPU-only raw writer preparation

`raw_writer.py` is a tested byte transport, not a native capture adapter. It imports
no inference or GPU library. A tensor descriptor follows PR #226 `compareTensor`:
F16LE/F32LE, exact shape/axes, byte count, SHA-256, relative file path. Raw bytes,
not a digest, are written. Caller buffers are copied at `OwnedTensor` construction
and frozen before later mutations. Nonfinite bit patterns are rejected.

Capture root must be a trusted, pre-existing absolute directory. Each capture has
an exclusive fresh directory; tensor files and completion marker never overwrite
existing objects. Directory FDs and O_NOFOLLOW protect final names. Partial files
remain on I/O failure. A separate capture ID is required, not resume or retry into
an incomplete capture. COMPLETE.json is linked only after manifest bytes and file
fsync succeed, then directory fsync is attempted. A directory-fsync failure after
link means durability is uncertain and must be treated as a failed/uncertain
write, not a successful completed experiment. This implementation is POSIX-only.

Receipts intentionally use `hs.N1a.synthetic-capture.v1`, `SYNTHETIC` and
`native_qualified:false`. The unchanged native snapshot validator rejects them.
The supplied source/executable hashes are transport labels, not proof that that
binary generated the bytes. A real adapter must observe native tensor layout,
active coordinates, synchronization, caller ownership and operation events; map
those into full hs.N1a.raw-state.v1 snapshots; and bind its real executable and
writer identity. This implementation does NOT supply those guarantees or claim
261 native checks are implemented.

Tests:

```
python -m unittest -v
python -O -m unittest -v
python interop_test.py /path/to/pr226/plan/raw_compare.js
```

19 tests cover immutable owned copies and descriptor isolation, duplicate names,
whole capture overwrite, unsafe names, symlink roots/destinations, short writes,
zero write, partial failure and manifest failure, both float formats' nonfinite
values, wrong shapes, zero-sized reset tensors, completion, closed writers and constructor-fsync failure closing both directory FDs.
Interop uses two synthetic F16 values and unchanged PR #226 JS comparator, checks
4 bytes directly, and verifies the synthetic receipt is rejected as native.
All tests execute zero model forwards, GPU contexts and placement actions.
