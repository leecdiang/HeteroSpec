# 358H draft threshold analysis

Formula: `speedup = T_b*C/(T_d(2)+V_2*T_b+T_x)`; T_x=0 favorable bound. Exactness: 18/18 PASS.

## CPU — overall BORDERLINE

- 512: BORDERLINE; central median 0.9037, CI95 [0.8897, 0.9555]; optimistic CI95 [1.3346, 1.4333]
- 2048: BORDERLINE; central median 0.8848, CI95 [0.8724, 1.0104]; optimistic CI95 [1.3086, 1.5155]
- 8192: BORDERLINE; central median 0.7559, CI95 [0.7456, 0.7861]; optimistic CI95 [1.1184, 1.1792]

## NPU — overall BORDERLINE

- 512: BORDERLINE; central median 0.9056, CI95 [0.8908, 0.9570]; optimistic CI95 [1.3362, 1.4355]
- 2048: BORDERLINE; central median 0.9038, CI95 [0.8899, 1.0159]; optimistic CI95 [1.3348, 1.5238]
- 8192: BORDERLINE; central median 0.8396, CI95 [0.8277, 0.8649]; optimistic CI95 [1.2415, 1.2973]

Phase 3 was not started.

