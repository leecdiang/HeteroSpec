# Actual engineering qualification

All 360 fixed exposed-task runs and 40 observer/endpoint runs were captured and independently verified. Each required base gate passes 36/36: original UB1 vs fresh R-reference, H2 vs fresh R-only, and original vs timer for each of the three B conditions. The observer on/off check passes all 20 paired complete outputs. Twenty real endpoint runs cover inclusive EOG and exactly 128 committed IDs. Five constructed R branch cases and P widths 0/1/2 use exposed inputs and are not prediction samples. Fifteen deliberately corrupted copies are rejected independently.

Clock calls p99: 0.6 microseconds, below 10 microseconds and 1% of the shortest retained engineering interval. This bounds clock calls only; logging overhead is neither bounded nor subtracted. All IDs, proposal tapes, transport bytes, raw timers and device snapshots are in separate A/B author archives and derived anonymous capsules. Qualification is instrumented-path qualification, not unrestricted deployment or throughput measurement.

No reserved A forward, A live or B formal run has been executed. The 576 formal conditions are planned, not measured. Engineering candidates were not selected using their match rate. Detailed complete comparisons and first divergences appear in ENGINEERING_REPORT.json.
