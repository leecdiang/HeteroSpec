# Design validation

CPU-only validation, 2026-10-18, Python unittest: 5 tests passed.
- Logical visibility is invariant across padded storage; padded positions hidden.
- Invalid/truncated and boolean extents rejected.
- 256 unique timed jobs; deterministic plan; default graph-call count 11,400.
- Every arm occupies every position once per four-block session, with all 12
  directed distinct-arm first-order transitions covered in that session.
- Duplicate control definitions match; physical intervention extents match design.

These checks do not qualify native tensor packing, CUDA replay, floating-point
identity, the timing adapter or hardware performance. Those gates are explicitly
assigned to the RTX platform. No GPU execution took place during design.
