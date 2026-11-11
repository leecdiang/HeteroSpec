# Full endpoint equivalence classes (IDs + EOG + length + terminal + stop)

Original NO-GO remains: 49 starts, 48 complete, 1 incomplete, 31 unstarted, 14 treatment counterexamples.
Classes include timing-channel/session repeats. Equality is limited to this CAP128 window.

| Input | Class | Members |
|---|---|---|
| GSM8K/test/1011 | 1 (6811235be2ee) | R:counts:s0, R:counts:s1, R_SHADOW:counts:s0, R_SHADOW:diagnostic:s0, C_B_PQ:counts:s0, C_R_PQ:counts:s0, M_B_QB:counts:s0, M_R_QB:counts:s0 |
| GSM8K/test/1011 | 2 (709d796f2e48) | C_B_MQ:counts:s0, C_B_QB:counts:s0, C_R_QB:counts:s0 |
| GSM8K/test/1011 | 3 (03ce399280b6) | C_R_MQ:counts:s0 |
| GSM8K/test/1248 | 1 (fbb26b8017b5) | R:counts:s0, R:counts:s1, R_SHADOW:counts:s0, R_SHADOW:diagnostic:s0, C_R_MQ:counts:s0, C_R_PQ:counts:s0, C_R_QB:counts:s0, M_R_QB:counts:s0 |
| GSM8K/test/1248 | 2 (03c676ac0598) | C_B_PQ:counts:s0, C_B_QB:counts:s0, M_B_QB:counts:s0, C_B_MQ:counts:s0 |
| GSM8K/test/1249 | 1 (484ce82c42db) | R:counts:s0, R:counts:s1, R_SHADOW:counts:s0, R_SHADOW:diagnostic:s0, M_B_QB:counts:s0, M_R_QB:counts:s0, C_B_MQ:counts:s0, C_B_PQ:counts:s0, C_B_QB:counts:s0, C_R_MQ:counts:s0, C_R_PQ:counts:s0, C_R_QB:counts:s0 |
| GSM8K/test/831 | 1 (ebc7d75cd843) | R:counts:s0, R:counts:s1, R_SHADOW:counts:s0, R_SHADOW:diagnostic:s0, M_R_QB:counts:s0, C_R_PQ:counts:s0 |
| GSM8K/test/831 | 2 (7874c1bcf5e7) | C_B_MQ:counts:s0, C_B_QB:counts:s0, C_R_MQ:counts:s0 |
| GSM8K/test/831 | 3 (df3266ee09b5) | C_B_PQ:counts:s0, C_R_QB:counts:s0, M_B_QB:counts:s0 |

| Pair | Full endpoints equal across four inputs |
|---|---|
| C_B_MQ / C_B_PQ | 1248, 1249 |
| C_B_PQ / C_B_QB | 1248, 1249 |
| C_B_MQ / C_B_QB | 1011, 1248, 1249, 831 |
| C_R_MQ / C_R_PQ | 1248, 1249 |
| C_R_PQ / C_R_QB | 1248, 1249 |
| C_R_MQ / C_R_QB | 1248, 1249 |
| M_B_QB / C_B_PQ | 1011, 1248, 1249, 831 |
| M_R_QB / C_R_PQ | 1011, 1248, 1249, 831 |
| M_R_QB / C_R_QB | 1248, 1249 |

M_R_QB q1 executes the common original path. C_R_PQ 4/4 does not confer full-P1, unseen-input or safety qualification.
No state snapshots: operand/KV identity and state distance remain unknown. No qualified speedup is calculated.
