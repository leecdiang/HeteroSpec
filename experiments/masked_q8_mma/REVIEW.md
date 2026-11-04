# Independent review record

Reviewed kernel SHA256: a8a465ac224ba8aa9613946edbe5cf7291a063f1a4c171f366a143aa82586bb9.

A separate reviewer inspected source, PTX and both architectures' SASS. No blocking indexing/synchronization defect was found in this limited prototype. The reviewer checked original r%2 writers for four/eight-row controls, unique output writers, warp-uniform missing-K handling, the CTA barrier before cross-warp reads, full-warp shuffle participation, Q8_0 two-byte and Q8_1 four-byte payload bounds/alignment, signed integer instructions and absence of local-memory load/store instructions. The reviewer independently assembled the compute89 PTX with ptxas and reproduced resources.

Review required changing initial byte-at-a-time loads to alignment-safe packed loads and adding the logical-lane M2N32/M4N16/M8N8 DP4A controls. The original same-layout DP control alone is not a fair proxy for optimized DP4A. An actual-device architecture guard was also added before launch.

All 24 variant/architecture compilations succeeded with zero reported spills. The reviewer identified the difference between ptxas user shared memory and sm120a cubin SHARED metadata (+1024 bytes); its cause is not asserted. Both are preserved.

The executable passed eight host argument-rejection checks and then returned77 because no usable CUDA driver/device exists here. No GPU numerical result, synchronization/memory sanitizer result, frozen-R equality, occupancy, timing or novelty was established. The review is not formal verification of the complete SASS dependency graph. The final v3 harness adds those eight negative calls but uses exactly the reviewed kernel bytes.
