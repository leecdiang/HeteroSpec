## Formal v2 census completed; numerical execution awaits separate authorization

The census-only author approval at reviewed05912d0 was executed with the frozen
controller, host and F0. All360 actual metadata graphs (72 contexts x5 layouts)
completed5418 backend node-support queries: MQ72/72, PQ72/72, QB72/72, QH_C72/72,
QH_D72/72. All5418 individual node queries returned support; no unsupported
coordinates, missing graphs or control/runtime failures. QH_C remains primary.

Actual census cost:1controller,1readiness query,1native support host and2pinned
conhost helpers =5owned starts. Controller wall24.707993300/600s; conservative
owned bound74.123979900/1800s (wall x3). Native0.550775200/240s, readiness
0.075663800/10s.0numerical hosts, graph-compute calls, model requests, warmups or
scientific retries. CUDA was loaded/initialized for this census; it was not zero
device activity. Internal driver queries/context allocations remain UNKNOWN.
Engineering lifetimes are not clean performance measurements.

Actual CUDA process core/registry/host module identities and all41plugin core-IAT
ownership checks passed. Initialization of the exact shared ggml-base.dll preceded
CUDA loading. Frozen source, host,21numerical DLLs, input/wire/plan, primaryQH_C
and originalGGML_CUDA_DISABLE_GRAPHS=1 remained unchanged. No implementation or
experimental design was changed in this execution.

F0 SHA256: `73ef7106240be73ab914e4c6a36064a0d1fd6d41ce5d9c38bf65f38e8331f080`

Actual census SHA256: `11d6cb5c18eb934e5d5c5e851d4bf90814088d0a52e45425666ca89ee7a4a878`

Actual decision SHA256: `3051209f293f755218c2488effc43f33f78cf92714e332afa558f9009ac71db6`

Actual data commit: `c96215d8856198ff99ab7228b31187d391a5a2fc`.
Existing seal_census.py sealed the raw bytes and authenticated the remote archive
and manifest at that commit, rechecking every member and reconstructing the exact
decision. One earlier CPU readback used a mistyped commit and returned404 before
receiving bytes; its failure receipt is retained. The corrected authenticated
readback used no new GPU process and did not rerun census.

Evidence: formal_numerical_v2/census_execution/RESULT.md, SUMMARY.json, complete
SUPPORT_COORDINATES.csv, actual author approval, PID/lifetime/Job/module receipts,
census_delivery/CENSUS_RAW.zip and MANIFEST.json, actual census_readback bytes and
AUTHENTICATED_CENSUS.json. The archive is64008B; old full archives were not copied.

The frozen decision's numerical_admitted=true is a technical condition, not
execution authorization. All720 new numerical slots remain unstarted. Actual
graph execution/placement/synchronization, GPU numerical correspondence and
repeatability, actor/end-to-end qualification and timing/profile/S2/S3 remain
unestablished and unauthorized. No speed, truth or universal-equivalence claim.

Old720 remains1failed/719unstarted/0completed; GPU14 remains14completed/0failed.
Their immutable archives were rechecked and neither contributes repetitions to
the new panel. Keep PR113 Draft. No main/PR104/110/B570/paper/release/automation
changes. Stop after census; await a separate human numerical approval bound to
the actual F0, census and decision hashes above.
