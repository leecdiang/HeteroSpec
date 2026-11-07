"""Render the actual finite findings and complete missingness; CPU only."""
import sys
from pathlib import Path
D=Path(__file__).resolve().parent;V=D.parent
sys.path.insert(0,str(V))
from common import load,sha
a=load(D/'RECONSTRUCTED.json');f=load(D/'SCIENTIFIC_FINDINGS.json');l=load(D/'LEDGER_AUDIT.json');m=load(V/'formal_delivery/MANIFEST.json')
cost=l['cost'];counts=l['counts']
family='\n'.join('| '+name+' | '+str(c.get('COMPLETED_QUALIFIED',0))+'/240 | '+str(c.get('NOT_STARTED_PROTOCOL_STOP',0))+' |' for name,c in l['families'].items())
ps='\n'.join('| '+r['left']+'/'+r['right']+' | '+str(r['qualified'])+'/144 | '+str(r['bitwise_equal'])+' | '+str(r['finite_different'])+' | '+str(r['withheld'])+' |' for r in f['pair_summaries'] if r['scope']=='all')
worst='\n'.join('| '+s+' | '+str(f['maxima'][s+'_max_error']['value'])+' | '+str(f['maxima'][s+'_max_ULP']['value'])+' |' for s in ('QK','softmax','AV','ordinary'))
first=f['first_observed_pair_difference']
text=f'''# Formal numerical v2: budget stop,474 qualified /720 planned

## Execution and provenance

Actual newly received author approval authorized only the exact frozen numerical
stage plus CPU closure. Reviewed `ba5719149c2ae5e8f0ac6d1f68a4bd5b248b5e4f`.
Sole frozen controllerPID22008 started2026-10-16 00:26:52 Asia/Shanghai and
exited70 at00:56:52. It reserved no next process after the1731.760s remaining-
lifetime gate, having completed474 slots. The watchdog then ended in-controller
CPU analysis at the1800s ceiling. No GPU/native/readiness/scientific retry followed.

| Family | Qualified native graphs | Not started |
|---|---:|---:|
{family}

474native starts,474graph starts,474successful returns,474device-wide completion
returns,474original online COMPLETED receipts and474frozen offline qualifications.
0native runtime failures,0numerical control failures,0nonfinite outputs,
0NOT_SUPPORTED,246NOT_STARTED_PROTOCOL_STOP. All180q1 public controls passed.
There are48contexts with any data,47complete five-layout/two-repeat contexts,
onepartial context and24contexts with no executions. Repeats are not independent
inputs. This is an INCOMPLETE panel, not720/720 or all-family numerical admission.

NUMERICAL_FAILED and NUMERICAL_WATCHDOG_STOP are preserved. NUMERICAL_ENDED and
the controller's ANALYSIS are genuinely absent; ACTIVE_CONTROLLER.lock remains
as abnormal-stop evidence, not a running job or invitation to restart. A frozen
controller bookkeeping detail wrote FAILED into directory473 after its graph
had already completed/qualified because current still referenced473 when the
next-start reserve failed. Both COMPLETED and FAILED are preserved. Raw graph,
return,sync and unchanged online/offline controls establish graph473's status;
the failure is the controller's next-start budget gate. No new auditor promotes
an unqualified return: every offline-qualified cell has its original COMPLETED.

{counts['native_processes']}native +{counts['readiness_processes']}readiness +1controller +
{counts['conhost_helpers']}pinned conhost helpers ={counts['owned_process_starts']}owned starts
(cap2881). Native support API calls{counts['support_API_queries']}/10836; prior
census5418 remains separate.474explicit nvidia-smi queries,474backend loads/init,
948explicit device-wide sync calls,4464backend and4464buffer-type device-identity
calls. Internal driver/kernel/enumeration counts remain UNKNOWN. Models,warmups,
extra smoke/probes and scientific retries0.

Wrapper observed wall{cost['wrapper_wall_seconds']:.6f}s; start receipt to watchdog
epoch{cost['start_receipt_to_watchdog_epoch_seconds']:.6f}s. The nominal1800/5400
ceiling was actively enforced, but observed termination has a scheduling/closure
lag: wrapper x3 conservative envelope{cost['wrapper_x3_conservative_owned_envelope_seconds']:.6f}s,
slightly above5400. Do not round this down or claim an exact hard upper bound.
With census, observed conservative envelope{cost['combined_observed_conservative_envelope_seconds']:.6f}s
<7200. No budget was extended/reissued. Controller peak private commit UNKNOWN
because watchdog bypassed its final receipt. Native peak process/job commit
{cost['native_peak_process_commit_bytes']}/{cost['native_peak_job_commit_bytes']}B;
ready peak{cost['readiness_peak_process_commit_bytes']}/{cost['readiness_peak_job_commit_bytes']}B.
Requested50ms observation is not a certified maximum sampling gap.

Direct native lifetime sum{cost['native_lifetimes_sum_seconds']:.6f}s,readiness
{cost['readiness_lifetimes_sum_seconds']:.6f}s; the remaining process-envelope
interval includes Python checks,hashing,CPU comparisons,watcher,I/O and lifecycle.
It is not an exclusive CPU causal share or a clean operator timing. This run
establishes no speed,Tensor Core,DRAM traffic or hardware bottleneck evidence.

## Complete numerical relationships and denominators

Each comparison has72contexts x2process repeats =144planned observations. All
5760stage rows,including missing comparisons,are in PAIRWISE_STAGE_RELATIONS.csv.
All72joint family/layer/phase/q coordinates and complete layout denominators
are in CONTEXT_RELATIONS.csv; STRATIFIED_RELATIONS.csv separately groups family,
layer band,phase andq. Full first-divergence/operator/index/input bindings are
retained in ALL_VALID_DIFFERENCES.json and the unchanged frozen reconstruction.

| Pair | Qualified /144planned | Bitwise all4stages | Finite different | Withheld |
|---|---:|---:|---:|---:|
{ps}

QH_C/PQ,QH_C/QB,QH_D/PQ,QH_C/QH_D andPQ/QB each match94/94qualified process
comparisons (47contexts). Split the evidence: q1common36/36 across18contexts;
q>1genuine lowering58/58 across29contexts.50/144comparisons remain withheld for
each of these pairs. QH_D/QB is also94/94. No QH-specific finite counterexample
was observed; lack of execution is not evidence of correspondence.

Compact joint range table: A=allfive layouts equalMQ in both fresh repeats;
B=PQ=QB=QH_C=QH_D bitwise,each differs fromMQ starting atQK,both repeats;
P=onlyMQ/PQ both repeats qualified,QB/QH_C/QH_Dunstarted;
U=allq>1layouts unstarted. Every row covers exactly the specified inherited layers
and phases,not newly selected inputs.

| Family | Layers | Phase | q1 | q2 | q3 | q4 |
|---|---|---|---|---|---|---|
| Qwen |0,18,35|prefill,continuation|A|B|B|B|
| SmolLM2 |0|prefill,continuation|A|B|B|B|
| SmolLM2 |12|prefill|A|B|B|B|
| SmolLM2 |12|continuation|A|B|B|P|
| SmolLM2 |23|prefill,continuation|A|U|U|U|
| Llama |0,16,31|prefill,continuation|A|U|U|U|

MQ own-path matches its frozen original at all96MQ executions. PQ/QB retain
their historical original stage bytes at allqualified PQ/QB executions. Every
qualified result has complete full-size Q/K/V/mask before/after equality,finite
QK/softmax/AV/ordinary,ordinary-from-own-AV consistency,actualgraph identity,
node CUDA support and nonhost buffer/device ownership,shared-core/registry/
41plugin IAT/module checks,call/sync records and independent process identity.
237/237same-layout fresh-process repeat pairs are bitwise identical in allstages.

The234finite MQ-versus-candidate process comparisons are valid differences,not
234independent inputs or failed model predictions. All first diverge atQK.
The earliest by frozen acquisition order is{first['descriptor']} {first['left']}/
{first['right']} repeat{first['repeat']},at stage{first['first_divergence_operator']},
first logical index{first['stages'][first['first_divergence_operator']]['first_logical_index']}.
Ordinary restoration adds no first divergence; the differences are already inAV.

| Stage | Maximum absolute difference across valid pairs | Maximum signed-rank ULP distance |
|---|---:|---:|
{worst}

MaximumQKabsolute error is SmolLM2layer12continuationq2 MQ/PQ;
maximumsoftmaxerror is SmolLM2layer12continuationq3;
maximumAV/ordinaryerror is Qwenlayer35continuationq3. Other equal non-MQ arms
can tie these maxima. All differences and their complete input identities remain.
Large ULP distances nearzero/sign changes are reported as-is,without tolerance
tuning or interpretation as mathematical truth,accuracy loss or endpoint failure.

## Recoverable raw evidence and independent audit

Existing package_formal.py sealed{len(m['members'])}members to RAW_FORMAL_V2.zip,
{m['bytes']}B (below100MiB ordinaryGit file cap; no sharding needed), SHA256
`{m['sha256']}`. MANIFEST.json binds every original raw slot,complete readback
CAS,stages,census/decision,module/process/lifetime record,stop receipt,residual
lock and appended actual authorization/provenance. No model weights,numerical
DLLs or private OS memory dumps are republished.

The first post-stop unchanged frozen analyzer reproduced474qualifications and
all1440planned pair relations in43.013s with0new GPU starts; it did not change
raw status or write a fictitious in-controller ANALYSIS. After actual push,the
authenticated remote ZIP+manifest,new-directory full member verification,and
CPU reanalysis must be recorded in AUTHENTICATED_FORMAL.json and FRESH_AUDIT.json.
Until those actual receipts exist,remote restoration is not claimed complete.

Old720 remains1failed/719unstarted/0completed; GPU14 remains14completed/0failed.
Their archive hashes,allfrozen source roles,theEXE,PLAN,F0 and21numerical DLLs
were rechecked unchanged. No results are mixed or backfilled.

## Research decision and boundaries

CaseC applies: formal panel stopped on budget,not a QH numerical counterexample.
QH is a real source-bound query/head representation with observed finite
PQ/QB-compatible stage bytes beyond q1,not a universal equivalence result or
identified kernel/reduction tree. It offers another software representation;
this run shows no new numerical capability beyond the already implementedPQ/QB.
No measured cost ranking says QH is stronger/faster thanQB. Preserve that baseline.
The software candidate remains worth bounded cost investigation after valid
coverage/admission,while hardware remainsSOFTWARE_FIRST/HOLD. There is no evidence
here for a missing hardware mechanism,Tensor Core gain,acceptance increase or
request economics. Same bits do not prove closer mathematical truth.

Current evidence supports exposed operator-input correspondence and same-path
repeatability only. Full-model reference,live actor/KV/rollback transaction,
new natural prompts,longer visible keys,full endpoints and inclusive request
cost remainUNKNOWN. Padded tensor extent256 does not mean256valid visiblekeys.

Next CPU preparation follows the actual budget-stop branch and is recorded in
NEXT_CPU_PREPARATION.json/NEXT_STAGE.md after remote/fresh closure. No S1B clean
timing,profile,actor,S2/S3 or new numerical run is authorized. No current F0/source/
analyzer/input/wire/layout/precision/configuration change,no automated retry and
no extra GPU/model/query start. Keep PR113 Draft,main/paper/PR104/110/B570/release/
automation untouched. A future GPU phase requires a new reviewed F0 and explicit
author confirmation; the old720v2 ledger is permanently stopped.
'''
with (D/'RESULT.md').open('x',encoding='utf-8',newline='\n') as out:out.write(text)
body=f'''## Formal v2: budget stop;474qualified /720planned

The exact authorized frozen numerical run completed474graphs with474valid returns,
syncs and original online/frozen offline qualifications;246slots never started.
0native/control failures,0nonfinite outputs,0retries. All180q1controls passed.
Qwen240/240,SmolLM2174/240,Llama60/240; full panel is INCOMPLETE.

Next-start lifetime reservation stopped starts at1731.760s;1800s watchdog then
interrupted in-controller CPU analysis. MissingENDED/ANALYSIS,residual lock and
last-directory COMPLETED/FAILED collision are preserved/explained. Actual wrapper
wall1800.302941s; conservative x3 envelope5400.908823s (slight observation/closure
lag above nominal5400,not rounded away). Including census5475.032803s<7200.
474native+474ready+1controller+948pinned conhost=1897owned starts.6578new support
queries; oldcensus5418separate. Zero models,warmups,extra probes or GPU retries.

QH_C/PQ,QH_C/QB,QH_D/PQ,QH_C/QH_D,PQ/QB each94/94qualified comparisons equal
inQK/softmax/AV/ordinary:18q1commoncontexts plus29q>1contexts,each2freshrepeats.
Each pair withholds50/144planned comparisons.237/237same-layout repeat pairs
match. MQ differs finitely from allobservedq>1candidates,first atQK; maximumabs
QK0.0547027587890625,softmax0.0009159445762634277,AV/ordinary0.010433197021484375.
No QH-specific finite difference; no universal/kernel/truth/endpoint/cost claim.

Full raw archive{m['bytes']}B/{len(m['members'])}members,SHA`{m['sha256']}`.
Complete slots,readbacks,stage bytes,modules/processes,actual approval,census and
stop evidence are bound in MANIFEST. RESULT.md,72-coordinateCSV,5760stage rows,
stratified tables,allvalidcounterexamples and independentCPU reconstruction are
under formal_numerical_v2/numerical_execution. Remote authentication/fresh restore
and finalCPU next-stage readiness receipts are committed separately after they
actually complete. No old data reused;old7201failed/719unstarted/0complete,
GPU1414complete/0failed unchanged. No newGPU or oldslot restart.

CaseC: CPU closure/minimal next-stage engineering preparation; SOFTWARE_FIRST/HOLD.
S1B/profile,actor,S2/S3 remain unadmitted. Keep Draft; no main/paper/PR104/110/B570/
release/automation changes.
'''
with (D/'PR_BODY.md').open('x',encoding='utf-8',newline='\n') as out:out.write(body)
print('Actual finite findings rendered with complete denominators and budget/receipt limitations.')
