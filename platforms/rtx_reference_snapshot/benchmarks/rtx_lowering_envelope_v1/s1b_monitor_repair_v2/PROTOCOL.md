# S1B completed-graph software cost contract

Run pr116-s1b-cost-v1 depends on PR116 commit2b5ed1552263907df3adfdff9b0121d115734a6c.
Use exactly its24exposed preregistered profile_coordinates snapshots,three
families,both phases,q1..4 and fixed layers. Full Q/K/V/mask,all heads/channels/
keys,strides,GQA,scale,precision,numerical21DLLs and GGML_CUDA_DISABLE_GRAPHS=1
remain unchanged. Actual visible keys differ from padded256;no unseen-input claim.
PQ,QB,QH_C are real graphs. QB is primary strong baseline;QH_C is the candidate.

## Costs A–H and measurement boundaries

Windows QPC provides integer ticks and process-local frequency. Record raw
timestamps and units;nonpositive frequency,reversed or zero completed intervals
stop. Equal very short subintervals are allowed. QPC reads are not subtracted to
invent an observer-free time. CPU synthetic tests are explicitly not GPU times.
[Microsoft QPC](https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps).

A: main-entry/admission and shared-core/CUDA initialization (including named
identity audits),plus exact graph metadata build. OS loader before main is not
separately inferred;complete native process lifetime is reported separately and
contains diagnostics/teardown,never labeled kernel latency.
B: graph-only allocator construction and actual device allocation. Unlike the
numerical context allocator,it allocates only ordinary dependency tensors,not
unexecuted diagnostic stages. This allocation change needs real CUDA qualification.
C: exact full snapshot source reads. The inputs are exposed replay snapshots;
natural decoder causal-mask/KV production is outside this operator microbenchmark.
D: full-strided CPU materialization/copy of all Q/K/V/mask bytes. No hidden CPU
QH-specific packing. Required query packing,mask views/materialization,CONT/REPEAT,
all arithmetic and output restoration remain graph dependencies charged each eval.
E: four actual H2D input uploads plus setup cudaDeviceSynchronize,once per host.
Input before/after qualification readbacks and audits are separately identified;
they are not paid graph windows or silently omitted from total process cost.
F: the complete ggml_backend_graph_compute call,including any backend-internal
synchronization. It is not asserted to be asynchronous submission or a kernel.
G: the immediately following cudaDeviceSynchronize return interval. Together
F+G form one completed graph window with no double counting. No file writes,
readback,hash,profiler or per-op synchronization inside this interval.
[CUDA synchronization](https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/asynchronous-execution.html).
H: full ordinary output readback after completion. GPU ordinary restoration is
already in F and never added again. Every warmup/measured output must be finite
and full-byte equal to the fixed PR116 reference;comparison/audit is outside H.

Report three explicit views: resident steady mean of8 F+G observations;resident
complete-call F+G+H mean;and first input-inclusive cold call as the sum of actual
C+D+E+excluded-warmup(F+G+H). The latter is a disjoint measured-phase sum,not a
continuous wall interval,not a fresh natural request and not repeated8times.
Report A/B separately and actual process lifetime alongside it. Initialization,
allocation,source materialization and uploads are not assumed free in deployment.
There is no additional graph to measure another favorable cost view.

One explicit warmup,then8clean evaluations,each checked outside its paid window.
Only ordinary readback is present;no QK/softmax/AV diagnosis. Same resident inputs
and allocator are reused,so this is a warm-cache operator replay. All actual
ordinary occurrences and input before/after bytes are retained,with per-occurrence
receipts even if content-addressed complete bytes deduplicate. Failures preserve
available output and partial timing evidence;missing crash data remain missing.

## Fair order and statistics

Three fixed rotated acquisition blocks,72fresh hosts each. Each context/layout
occupies each Latin position once;context/family order rotates. This balances
positions,not all six directed carryovers.18q1 public-path hosts lead each block.
All inputs/layouts remain even if slow or unqualified. No block or input adaptation.

Main ratio T_QB/T_QH_C;secondary T_PQ/T_QB. Ratios>1favor the denominator. Record
all8values,host mean/median/p95/max,three independent host points/CV/min/max per
context,three per-block paired differences/ratios,all regressions and full missingness.
Eight within-host measurements are technical repetitions,not8independent trials.
Aggregate equally by context and acquisition block;stratify family,phase and q.
q1 is a negative-control diagnostic;focus claims on q2..4. No bootstrap or
confidence interval from these3blocks. No pooled success-only aggregate.

Prospective practical threshold: geometric speed ratio>1.02 AND mean absolute
improvement>0.001ms;this is an engineering screen aligned with the prior2% rule,
not significance. The1us floor exceeds two ticks at frozen10MHz QPC. The floor
does not certify measurement accuracy. q1 deviations are reported as potential
measurement/environment anomalies,never selected away or called new acceleration.

## Admission, support, execution and trace are separate

A_STRICT_IDLE_V1 remains:one recorded pre-host query,util<=5%,temperature<=55C,
free>=512MiB,AC and exact GPU/driver/capacity/power scheme. No cooldown,requery,
retry,Graph-strategy switch or background probe. A checkpoint is not continuous
exclusivity. Full source/input/runtime/module/host/registry/shared-core/plugin41
IAT identities,all node support and actual node/input buffer-device ownership
are checked. Current72clean graph support/ordinary qualification NOT_ESTABLISHED.

New census queries828nodes,0compute,1native+1readiness+1controller+2helpers.
Clean216hosts use1944computes and2484node-support calls. Three600s/1800owned blocks,
census600s/1800owned;all currently registrable stages872process starts including
helpers,217readiness queries,2160explicit device synchronization calls. Native60s,
census240s,query10s;Jobactive2/native2GiB/ready256MiB/controller512MiB,32KiBpipes.
Internal CUDA/driver APIs are UNKNOWN. Stage wall includes hashing,controls,
monitoring and reconciliation. Byte accounting is append-only;full check every18
completions;5s durable finalizer reserve. Completed slots never fail because the
next cannot fit. Every failed/unstarted/unadmitted coordinate remains explicit.

PROFILE_UNAVAILABLE is based on declared filesystem/PATH inspection only: no
Nsight/CUPTI collector was invoked or loaded. Real kernel names,launch counts,
stream durations/overlap,TensorCore use and memory traffic remain UNKNOWN.
[CUPTI activities](https://docs.nvidia.com/cupti/) require an actual compatible
collector;CPU graph counts and inclusive host time are not substitutes. Independent
trace host code/count loop exists,but trace execution/collection is NOT_ADMITTED.
All72trace coordinates remain in the original plan. See proposed AMENDMENT.md.

CPU audit,archive,Git/gh transport,authentication,fresh restore and new-interpreter
recompute have separate900s registered wall/15300s conservative owned budget.
Ordinary jobs use controller+child+conhost<=3;transportJob<=16descendants plus
controller<=17,each pinned. No uncharged Git child family. Zip parts<=40MiB,
two archive sets and two raw sets;full Git archive object copy also reserved.
Exact budget/storage/API counts are in BUDGET.json. No truncation or deleting
failed evidence to fit. Future trace collector process budget remains unresolved.

Stop after CPU preparation/F0 authentication. First possible GPU authorization is
S1B_CENSUS_ONLY;then separately S1B_CLEAN_BLOCK_0_EXACT. Later blocks need own author
approval plus previous qualified receipt hash. No automatic progression. S1B cost
does not qualify a natural actor,KV/rollback,speculative k3,acceptance or hardware.
QB remains the current strong method;negative QH results are retained. No paper,
main,release,automation,B570,natural decoder,S2/S3,RTL/FPGA/PPA change.
