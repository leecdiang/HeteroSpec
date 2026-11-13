# C1024 full-GPU admission and qualification progress

The exact15,698,533,728-byte Qwen3-14B Q8_0 target is fully downloaded/SHA256
verified, with the fixed0.6B draft. Actual zero-forward allocation places every
target/draft weight and every F16 K/V layer on the allocated A5000 at C1024.
Minimum sampled free memory is8,436,842,496 bytes (7.86GiB); maximum sampled
total-minus-free is17,320,378,368 bytes (16.13GiB). The latter includes reserved/
unavailable memory and is not NVML memory.used or a per-process high-water mark.
The entire admission supervisor invocation takes113.822s. This is allocation
evidence, not forward-workspace headroom, numerical qualification or speed.

A new independent14B R is subsequently frozen. All four true target-only M
paths pass all12 finite geometry cases, with exact original requested vectors
and active states. The first combined natural worker reaches the retained900s
timeout. Partial outputs are not admitted, and all reservations remain charged.
See ../CONTINUATION_02.md for the separately versioned natural requalification,
read-only R/geometry reuse, added EOG semantic diagnostic and formal quiet guard.

D14-PROGRESS.json binds the actual stage proofs, independent reference and failed
worker at its timestamp. D14_ADMISSION.json is the original earlier admission
receipt: its NOT_FROZEN R field describes that earlier stage, not the later R
freeze. Old receipts are preserved rather than rewritten to imply later checks.

Full native qualification and the384-measurement/48-primer formal panel have
not completed at this snapshot. The original16 exposed roots remain deployment
transfer inputs, not new blind samples. No performance inference is reported.
C4096, M2, manuscript edits, rentals and automatic merge remain NOT_RUN.
