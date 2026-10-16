# Bridge census — complete support only

F0 SHA256: `c5f980b1a56673145fced02f38864eb8cbff4d793b285705fd66f88b6338c92a`
Census SHA256: `a72b1f5de3678b992e28be303ddedc50059d94974d83a7038d0bdc2dc63ee364`
Decision SHA256: `3b621d5686044a0ea7bcef9f2a7861c22d234bf0d27c0910c4849f0c807129a6`

120/120 actual graphs fully supported;1806/1806 node API queries completed and all returned true. No NOT_SUPPORTED coordinates. QH_C remains fixed primary;QH_D is unchanged contrast.

| Layout | Supported graphs | Node support queries |
|---|---:|---:|
| MQ | 24/24 | 192 |
| PQ | 24/24 | 732 |
| QB | 24/24 | 300 |
| QH_C | 24/24 | 282 |
| QH_D | 24/24 | 300 |

Actual process starts:1 controller,1 readiness,1 native support host,2 pinned conhost;total5. Controller PID2904;readiness PID28360;native PID25248.
Census wall17.087632s;conservative owned51.262897s within600/1800. Readiness0.105894s and native0.456331s within10/240. Native peak job commit165425152B;controller sampled peak28901376B. Raw root93919613B. These are engineering costs,not clean timing.

Actual shared core/registry/CUDA plugin paths,hashes,host IAT and41 CUDA-to-core imports passed the frozen controller and independent CPU sealer. All21 numerical DLLs,models/full input/reference/source/serializer identities passed the frozen pre-readiness hash gate. Full120 graph node geometry,parameters and edges match the frozen CPU registry. No CUDA tensor upload/readback or numerical correspondence is claimed by a metadata-only census.

Zero graph_compute,numeric hosts,model requests,warmups,profilers,extra probes or scientific retries. There was real authorized CUDA loading/initialization/support-query device activity. Census active lock is an immutable historical receipt;ENDED is COMPLETE and the owned jobs closed. Do not restart census.

CPU seal ran through frozen offline.py --action seal-census,using seal_census.py. Actual census+decision must now be committed and independently authenticated by offline.py --action census-readback before a separate author request. numerical_admitted=true is technical only. No BRIDGE_NUMERICAL_EXACT approval was generated;the240 numerical slots remain unstarted.

Old PR113 v2 remains474 qualified/246 unstarted;old failure/locks/missing receipts,old720(1 failure/719 unstarted/0complete)andGPU14(14complete/0failure)unchanged. PR113/104/110,B570,paper,main,releases,automations untouched. S1B,actor,S2/S3 and hardware remain unadmitted.
