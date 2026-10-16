# S1A Bridge v2 Numerical — complete240-cell qualified panel

Independent run pr114-s1a-bridge-v2,authorized against PR116 Census commit
afa9293981eea328457eeead2ae5026e8c8e7b26. No census rerun,no scientific retry.

## Actual scope and qualifications

240native starts,240qualified,0failed,0unstarted;240graph calls/returns and240
successful completion synchronization receipts. Qwen80/80,SmolLM280/80,Llama80/80.
Every family x prefill/continuation x q1..4 cell has10/10qualified slots (5layouts x2
fresh processes),with the original fixed layer selector and24complete exposed
PR104 contexts. Original72-context panel is not declared complete. Old PR113474/720,
PR114zero-start failure and GPU14 repeats remain separate history,not pooled here.

First60q1 public controls passed before anyq>1start.120/120independent layout
repeat pairs are bitwise identical across QK,softmax,AV andordinary. Process
independence uses PID+kernel creation time,not PID alone. MQ own-path,original
PQ/QB historical byte controls,complete sizes/logical order/finite values and all
input/module/graph/buffer/device/completion controls passed independent frozen CPU
analysis. No infrastructure or numerical control failure. No input/kernel/DLL/
precision/candidate/tolerance/environment modification.

## Full480 comparisons; no universal MQ equality requirement

Each of QH_C/PQ,QH_C/QB,QH_D/PQ,QH_C/QH_D,PQ/QB,QH_D/QB has48/48valid
context/repeat comparisons with all four stages bitwise equal:24contexts x2repeats,
not48independent inputs. Thus the288non-MQ comparisons are bitwise equal.
All sixq1 contexts have the common MQ path as well (48MQ/candidate comparisons).

For each MQ/PQ,MQ/QB,MQ/QH_C,MQ/QH_D relation:12q1 comparisons are equal and36
q>1comparisons have first divergence QK. Across allfour relations:144finite valid
q>1differences,covering18contexts x2repeats x4candidates. Total480pairs consist of
336all-stage bitwise equal and144differing. No withheld comparison.

Global maxima for MQ versus each identical candidate group:

| Stage | Maximum absolute difference | Maximum ULP distance |
|---|---:|---:|
| QK | 0.078582763671875 | 2017357824 |
| softmax | 0.0009172558784484863 | 96633 |
| AV | 0.0062923431396484375 | 1922026752 |
| ordinary | 0.0062923431396484375 | 1922026752 |

These are actual finite differences,not described as negligible. Full per-context,
family,layer,phase,q,layout,repeat,stage bitwise/error/ULP/first-divergence locations
are retained in PAIRWISE_STAGES.csv and the unchanged analyzer output. No claim that
matching candidates are closer to mathematical truth,or use the same kernel or
reduction tree. Ordinary error follows the retained AV output restoration.

## CUDA evidence and costs

Each actual host has41pinned plugin core imports (9840entries total),shared core/
registry/host checks,complete graph structure and actual CUDA buffer/device binding,
full Q/K/V/mask reads before/after,all four output byte strings,graph return and
post-compute synchronization.3612actual numerical-node support queries completed.
No Numerical CUDA host is replaced by a CPU fixture. Recorded pre-host identity:
RTX5070TiLaptop,driver616.92,AC1,balanced scheme381b4222-f694-41f0-9685-ff5bb260df2e.
All240readiness queries showutil0%,temperature41..49C,free12227MiB. These are
pre-host checkpoints,not continuous exclusivity,residency or peak GPU-memory data.

Actual Numerical launches961:controller1,native240,readiness240,conhost480. Stage
wall463.297923300s<=1800,conservative owned1389.893771100s<=5400.
Controller sampled private commit peak41410560B,
native Job peak511725568B,readiness Job
peak24006656B. Child pipe output75840B;
raw root109760651B. Source/input hashing,actual readbacks,
controls and34.186842sfull byte-reconciliation work are inside stage wall.
This instrumented execution is not clean timing or software acceleration evidence.
No model request,warmup,extra probe,profiler,actor or subsequent stage.

## Raw archive and CPU-only closure

Frozen offline.py --action analyze completed:COMPLETE_QUALIFIED_PANEL. Raw package
created by unchanged evidence.py contains9951members,all actual inputs,
stage bytes,individual readback/process/module/placement/lifecycle/control records,
complete input/referenceCAS and frozen source/host/F0/independent analyzer.
Archive bytes32281862;SHA25600b1cdae95e88cda64aee67f16cc1646267e2c8f02b71a466bd953cac02de229.
Original analysis SHA256:5084cfe0a98d433ddabcf19ee1d6994d605654a4df45ad4b67efee4ec64c772e.
Raw manifest is closure/RAW_MANIFEST.json. No full old experiment archive was recopied.

Authenticated remote archive readback,fresh restore and new-interpreter reanalysis
are PENDING here and must actually succeed before final delivery closure. CPU-only
delivery retains its independent900s wall/2700owned cap and includes prior Census
CPU spending without reset. No GPU process remains;no new GPU task is available
in the offline workflow. All input/kernel/runtime/source-role hashes remain fixed.

F0 SHA256:3da19af573ac4c93e73c4b4d9831f0da94fb2460247471395e4498862a7aada0
Census SHA256:85c9dcd2747491183047b05937abdd29a47cfa9c6675261e94947b0b665a128b
Decision SHA256:3b621d5686044a0ea7bcef9f2a7861c22d234bf0d27c0910c4849f0c807129a6

## Limits and next authorization boundary

Qualified exposed24-context software numerical scope only:6q1 and18q>1contexts,
not unseen prompts,full72coverage,universal equivalence,actor/KV/rollback/endpoint
qualification,cost reduction,TensorCore utilization or higher speculative acceptance.
QB remains the strong software baseline;SOFTWARE_FIRST/HOLD hardware status and
paper claims unchanged. Matching outputs do not establish same kernel/reduction.

After actual fresh closure,this independent complete panel satisfies the accepted
limited24-context numerical prerequisite to PREPARE/REVIEW same24 S1B. It does not
authorize216clean hosts,72trace hosts,profiling,actor,natural decoder,S2/S3 or RTL.
PR116 stays Draft. Main,paper,release,B570,PR113/114/104/110 and automation untouched.
Stop after CPU delivery;no further GPU work.
