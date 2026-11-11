# Formal v2 census: backend support queries passed

Only the actual census-only approval was used, at reviewed05912d0. The frozen
controller ended successfully; no implementation, F0, plan or execution flags
were changed. QH_C remains the primary candidate and QH_D the fixed control.

| Layout | Supported graphs | Supported node queries |
|---|---:|---:|
| MQ | 72/72 | 576/576 |
| PQ | 72/72 | 2196/2196 |
| QB | 72/72 | 900/900 |
| QH_C | 72/72 | 846/846 |
| QH_D | 72/72 | 900/900 |

All360 planned graphs and5418 node support queries are present. Unsupported graph
coordinates: none. Unsupported nodes: none. The complete360-coordinate report is
SUPPORT_COORDINATES.csv. All graph identities/parameters match CPU_GRAPH_EXPECTED.
The frozen decision gives numerical_admitted=true as a technical condition only;
there is no numerical execution authorization and all720 v2 slots are unstarted.

Actual processes: controller30148; native support host31800;
readiness query31772; pinned conhost helpers
8236,3400. Total5 owned starts,0 failures.
Native host0.550775200s; readiness
0.075663800s. Controller wall
24.707993300/600s, conservative owned bound
74.123979900/1800s (whole wall x3).
Controller sampled peak private commit54874112B;
native peak process/job commit194646016/195895296B;
readiness peak process/job commit22482944/23719936B.
Census metadata/logs1956399B; raw root including the complete
immutable reference CAS255320739B; sealed census archive
64008B/22members. No budget was reset or borrowed.
Requested50ms observations do not certify a continuous sampling cadence.

The actual CUDA-loaded process passed core/registry/host identities and all41
plugin core-IAT ownership checks. One process-level initialization of the exact
ggml-base.dll completed before CUDA loading.21 numerical DLLs and frozen source
identities remain unchanged. This census loaded/initialized CUDA and constructed
metadata graphs; it is not zero device activity. Explicit graph-compute calls,
graph-tensor allocations, numerical hosts, model requests and warmups are0.
Internal CUDA/context allocations and driver query counts are UNKNOWN. Actual
graph tensor placement, successful execution/synchronization, QK/softmax/AV/output
values and numerical/repeatability controls remain unobserved for formal v2.
No clean timing, speed, actor, S1 profile, S2 or S3 qualification is established.

Old720 remains1 started-failed/719 unstarted/0 completed; GPU14 remains14 started/
14 completed/0 failed. Their original archive hashes were rechecked and no records
were reused. The census contains no numerical outputs to fill any old/new slot.

F0 SHA256: `73ef7106240be73ab914e4c6a36064a0d1fd6d41ce5d9c38bf65f38e8331f080`

Census SHA256: `11d6cb5c18eb934e5d5c5e851d4bf90814088d0a52e45425666ca89ee7a4a878`

Decision SHA256: `3051209f293f755218c2488effc43f33f78cf92714e332afa558f9009ac71db6`

Archive SHA256: `9fb397606c1b22edce100775e285a65be5a0a301e60e8d2bdc82092aa533b77e`

The existing seal_census.py sealed these bytes. Commit/push and authenticated
remote byte reconstruction are recorded separately in AUTHENTICATED_CENSUS.json
after delivery. Stop here: a later human approval must bind these actual F0,
census and decision hashes before the numerical entry can be used.
