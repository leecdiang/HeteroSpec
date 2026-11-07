"""Post-matrix reporting and bounded exploratory analysis; no model execution."""
import collections, re, shutil
from common import *
import verify

def selected_dir(t,c,r=1):
    chosen=load(OUT/'SELECTED_ATTEMPTS.json')[f'formal/{t}/{c}/{r}'];return (ROOT/chosen['record']).parent/chosen['attempt']
def decision(d,ordinal):
    events=[json.loads(l) for l in (d/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    samples=[e for e in events if e['event']=='sample' and e['role']=='target']
    if ordinal is None or ordinal>=len(samples):return None
    sample=samples[ordinal];before=[e for e in events if e['event']=='decode' and e['role']=='target' and e['sequence']<sample['sequence']]
    return {'sample':sample,'preceding_live_decode':before[-1] if before else None,'alignment':'same generated decision ordinal and complete committed prefix; speculative lookahead KV/positions may differ, so not an equal-full-live-state comparison'}
def main():
    report=OUT/'formal-verify';summary=load(report/'SUMMARY.json');assert summary['status']=='PASS' and summary['formal']==171
    arrays=load(report/'ARRAYS.json');by={(r['task'],r['condition'],r['rep']):r for r in arrays['records']};comparisons=load(report/'COMPARISONS.json');witness=load(report/'WITNESSES.json')
    # Freeze described outcome-dependent selection, used only after full completion.
    priority={}
    for d in comparisons:
        if d['pair']=='U2/N1' and not d['joint_equal']:priority[d['task']]=min(priority.get(d['task'],128),d['first_divergence'] if d['first_divergence'] is not None else min(d['left_length'],d['right_length']))
    for t in load(DOC/'COHORT.json')['tasks']:
        for c in ['N0','N1','U2']:
            for r in [2,3]:
                diff=verify.difference(by[t,c,1],by[t,c,r])
                if not diff['joint_equal']:priority[t]=min(priority.get(t,128),diff['first_divergence'] if diff['first_divergence'] is not None else min(diff['left_length'],diff['right_length']))
    selected=sorted(priority,key=lambda t:(priority[t],int(t.split('/')[1])))[:4]
    for t in ['HumanEval/15','HumanEval/25','HumanEval/18','HumanEval/31']:
        if len(selected)<4 and t not in selected:selected.append(t)
    save(DOC/'DIAGNOSTIC_SELECTION.json',{'tasks':selected,'exploratory':True,'rule':load(DOC/'PROTOCOL.json')['diagnostic_selection'],'priority':priority,'additional_generations':0,'reason':'all formal N paths already retain the available detailed capture; repeating the same three conditions would add no richer U2 state','cap':12})
    details={};graphs={};tails={}
    for key,w in witness.items():
        for phase,row in w.get('graphs',{}).items():
            c=key.split('/')[3];dest=graphs.setdefault(c+'/'+phase,{f:set() for f in row})
            for field,values in row.items():dest[field].update(values)
        if w.get('post_endpoint_sample_tail'):tails[key]=w['post_endpoint_sample_tail']
    for t in selected:
        comparisons_t={name:verify.difference(by[t,a,1],by[t,b,1]) for name,(a,b) in {'U2/N1':('U2','N1'),'U2/N0':('U2','N0'),'N0/N1':('N0','N1')}.items()}
        n0,n1=selected_dir(t,'N0'),selected_dir(t,'N1');idx=comparisons_t['N0/N1']['first_divergence']
        state={c:{'source_before':sha(d/'trace.jsonl.source_before.kv'),'pending_logits':sha(d/'trace.jsonl.pending_logits.f32'),'transfer':next(json.loads(l) for l in (d/'trace.jsonl').read_text(encoding='utf-8').splitlines() if json.loads(l)['event']=='transfer')} for c,d in [('N0',n0),('N1',n1)]}
        u2text=(selected_dir(t,'U2')/'native.log').read_bytes().replace(b'\r\n',b'\n').decode('latin-1');start=re.search(r'new prompt,.*task.n_tokens = (\d+)',u2text);tail=u2text[start.end():];first=re.search(r'slot process_toke:.*n_gen = 1,',tail)
        dump=lambda text:list(map(int,re.findall(r'ubatch_print:\s+n_tokens\s*=\s*(\d+)',text)))
        u2group={'prefill_logged_batch_dump_lengths':dump(tail[:first.start()]),'continuation_logged_batch_dump_lengths':sorted(set(dump(tail[first.end():]))),'limitation':'logger dumps include caller and split batches; these are not callback-observed occupied graph tensor dimensions'}
        details[t]={'comparisons':comparisons_t,'first_pending_state':state,'first_pending_source_bytes_equal':state['N0']['source_before']==state['N1']['source_before'],'first_pending_logits_bytes_equal':state['N0']['pending_logits']==state['N1']['pending_logits'],'N0_first_divergent_decision':decision(n0,idx),'N1_first_divergent_decision':decision(n1,idx),'U2_batch_dump_observations':u2group,'U2_state':'KV/logits/sampler/occupied-graph callbacks unavailable on released ordinary CLI; raw prompt/caller/commit logs retained','recorded_formal_attempts':{c:load(OUT/'SELECTED_ATTEMPTS.json')[f'formal/{t}/{c}/1'] for c in ['N0','N1','U2']}}
    save(DOC/'DIAGNOSTIC_FACTS.json',{'selected':details,'new_U2_N1_mismatches':priority,'graph_summary':{k:{f:sorted(v) for f,v in row.items()} for k,row in graphs.items()},'raw_post_endpoint_sample_tails':tails,'additional_generations':0,'unavailable':'full committed-prefix live KV/logits at first later divergent sample; U2 internal state; opaque sampler serialization; independent absolute clock'})
    for src,name in [('SUMMARY.json','RESULTS.json'),('ARRAYS.json','FORMAL_ARRAYS.json'),('COMPARISONS.json','COMPARISONS.json'),('RETROSPECTIVE_LEAD.json','RETROSPECTIVE_LEAD.json'),('TASK_COMPARISONS.csv','TASK_COMPARISONS.csv')]:shutil.copyfile(report/src,DOC/name)
    shutil.copyfile(OUT/'SELECTED_ATTEMPTS.json',DOC/'SELECTED_ATTEMPTS.json');shutil.copyfile(OUT/'ATTEMPT_LEDGER.jsonl',DOC/'ATTEMPT_LEDGER.jsonl')
    comp=summary['comparisons'];st=summary['stability'];changed=[r['task'] for r in summary['task_table'] if r['N0_N1_changed']]
    cases=''
    old=load(DOC/'HISTORICAL_BINDINGS.json')
    histref={}
    for row in load(ROOT/'benchmarks/rtx_trajectory_cost_v4/A_trajectory/RESERVED_PREDICTIONS.json')['rows']:
        histref[row['task_id'],row['repetition']]={'ids':row['conditions']['A_REFERENCE_UB1']['generated_ids'],'endpoint':row['conditions']['A_REFERENCE_UB1']['termination']}
    for t in ['HumanEval/15','HumanEval/25','HumanEval/18']+sorted(set(priority)-{'HumanEval/15','HumanEval/25','HumanEval/18'}):
        d=verify.difference(by[t,'N0',1],by[t,'N1',1]);refs={c:verify.difference(by[t,c,1],histref[t,1])['joint_equal'] for c in ['N0','N1','U2']}
        cases+=f"| {t} | {len(by[t,'N0',1]['ids'])} | {len(by[t,'N1',1]['ids'])} | {len(by[t,'U2',1]['ids'])} | {d['first_divergence']} | {d['left_id']}→{d['right_id']} | {refs} |\n"
    pairtable='\n'.join(f"| {p} | {v['array_equal']}/57 | {v['endpoint_equal']}/57 | {v['joint_equal']}/57 | {v['all_three_equal_tasks']}/19 |" for p,v in comp.items())
    report_text=f'''# RTX matched target-only bridge study

Status: **{summary['outcome']}**. All171/171 newly executed formal records passed
independent raw verification. Engineering12, diagnostic0, failed attempts0. No
historical/engineering/diagnostic observation enters the formal denominator.

Scientific parent: `{PIN}`, PR54; implementation freeze
`{load(DOC/'FREEZE_RECEIPT.json')['commit']}`. This new PR is stacked on the exact
PR54 head branch. Manuscript and all inherited evidence remain unchanged.

Machine: RTX5070Ti Laptop, UUID GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd,
12227MiB, driver616.92, Windows11 build26300, Python3.11.9. Target/draft hashes,
released b10839 runtime and prior native frontend hashes match pinned contracts.
Target37/37 and draft29/29 layers CUDA0; all native target/draft logged threadpools24.
U2 loads only target, ctx4096/batch2048/globalUB2, 24/24 numerical threads.
Separate supported draft generation/batch flags are24 on N paths. Qualification
reuses unchanged instrumentation and passes12 local checks, seven negative tests.

Retrospective motivation was independently recomputed from source-bound arrays:
old U2=N0 51/57, old U2=N1 57/57. The old U2 CLI selected12threads; current study
matches24/24 and preserves ordinary U2 initialization/prefill rather than forcing
native caller grouping or transplanting state. No outputs/proposal tapes are model
inputs. Balanced condition order was frozen before formal execution.

| Pair | Full arrays | Endpoints | Joint | All3 equal task units |
|---|---:|---:|---:|---:|
{pairtable}

Within-condition full-array/endpoint stability: N0 {st['N0']}/19, N1 {st['N1']}/19,
U2 {st['U2']}/19. Three observations per task, not57 independent tasks. The complete
per-task/per-repetition table gives lengths, zero-based first divergence, IDs,
endpoint equality and unequal-length positional difference counts. Endpoints mean
EOS/limit under inclusive-first-EOG/cap128; terminal IDs remain in full arrays.

N0/N1 changed task units: {changed}. The remaining{19-len(changed)} task units are
unchanged and must not inflate the method claim. Predicting N1=N0 yields
{comp['N0/N1']['joint_equal']}/57 ({comp['N0/N1']['all_three_equal_tasks']}/19 tasks).
U2's agreement on changed tasks is reported in COMPARISONS.json; this is a post-hoc
execution-simplification candidate on already exposed tasks, not a general predictor.

| Case | N0 length | N1 length | U2 length | N0/N1 first index | IDs | Equal old UB1 reference |
|---|---:|---:|---:|---:|---|---|
{cases}

Fresh-vs-pinned historical full-array/endpoint equality:
N0 {summary['historical_bridges']['N0']['joint_equal']}/57,
N1 {summary['historical_bridges']['N1']['joint_equal']}/57,
U2 {summary['historical_bridges']['U2']['joint_equal']}/57. U2 is a24-vs12thread
observational bridge, not a controlled thread-causality experiment. Current full
reference agreement (unchanged old UB1 definition):
N0 {summary['historical_reference_matches']['N0']}/57,
N1 {summary['historical_reference_matches']['N1']}/57,
U2 {summary['historical_reference_matches']['U2']}/57.
/15 recovery and /25 movement away from reference remain different scientific
outcomes; /18 is not restored by agreement between candidate paths.

**Interpretation and decision.** If all U2/N1 checks agree, ordinary target-only U2
is empirically sufficient on this finite matched cohort, weakening novelty of the
more complex RTX P/R predictor for this specific reproduction objective. Shared
deterministic greedy execution with the same numerical backend is a plausible
explanation; a general equivalence theorem or bitwise internal-state equality does
not follow. Stop pursuing57/57 agreement or a new method-paper claim from this route.
Only a concrete frozen construction rule tested on new tasks/configurations against
ordinary target-only and the no-op baseline, with a useful engineering decision,
could justify another separately authorized study. This study does not identify
such demonstrated utility. Preserve the failed reference-restoration objective.

DIAGNOSTICS.md distinguishes measured caller/graph/sample facts and unavailable
live state. No speed, energy, VRAM reduction, functional correctness, cross-platform
generality or uninstrumented deployment benefit is inferred. No manuscript edit,
merge, release, external review request or weights/runtime upload.

Independent verifier reads raw selected logs/traces and all bindings without
importing controller/capture helpers, reconstructs171 records and all comparisons,
checks repetition stability, source/input/config/endpoint/handoff integrity and
separation of namespaces, and reparses114 historical N logs. Hashes authenticate
supplied content consistency, not original hardware execution or absolute time.
Raw archive restoration/readback receipts are separate final Git objects and do
not claim to be inside the archive whose hash they report. See REPRODUCIBILITY.md,
VERIFICATION_REPORT.md and HANDOVER.md for exact coverage and resume paths.
'''
    (DOC/'STUDY_REPORT.md').write_text(report_text,encoding='utf-8',newline='\n')
    text='# Bounded exploratory diagnosis\n\n'
    text+=f"Selected using frozen rule: {selected}. All171 formal cells finished first.\nAdditional diagnostic generations:0/12; detailed formal N captures already contain\nthe available state/graph witnesses. U2 retains its released ordinary CLI.\n\n"
    for t,d in details.items():
        diff=d['comparisons']['N0/N1'];text+=f"## {t}\n\n"
        text+=f"N0/N1 first divergent generated decision: {diff['first_divergence']};\nIDs {diff['left_id']} / {diff['right_id']}; lengths {diff['left_length']} / {diff['right_length']};\nendpoints {diff['left_endpoint']} / {diff['right_endpoint']}. U2/N1 joint equality:\n{d['comparisons']['U2/N1']['joint_equal']}. First-pending source serialized bytes equal:\n{d['first_pending_source_bytes_equal']}; full pending-logit bytes equal:\n{d['first_pending_logits_bytes_equal']}. These comparisons concern the original live\nfirst-pending boundary, not a fresh prefill of a later prefix.\n\n"
        group=d['U2_batch_dump_observations'];text+=f"U2 prefill first logged full batch length:{group['prefill_logged_batch_dump_lengths'][0]};\nall prefill logged dump-length values:{sorted(set(group['prefill_logged_batch_dump_lengths']))};\npost-first-commit dump lengths:{group['continuation_logged_batch_dump_lengths']}.\nThe logs contain caller and split-batch dumps, not tensor callback dimensions.\nNo grouping was changed to match N0/N1. N callback caller/graph observations are\nretained independently in DIAGNOSTIC_FACTS.json.\n\n"
        if diff['first_divergence'] is not None:
            for c in ['N0','N1']:
                w=d[c+'_first_divergent_decision'];s=w['sample'];dec=w['preceding_live_decode']
                text+=f"{c}: selected{ s['selected_id']}, logits-index{s['logits_index']},\ntop1{s['top1']}={s['top1_score']}, top2{s['top2']}={s['top2_score']};\npreceding target caller length{dec['caller_batch']}, UB{dec['ub_capacity']},\npositions{dec['positions']}, logits-mask{dec['logits_mask']}.\n\n"
            text+='Equal committed output prefixes align the sampled decision ordinal. The\npreceding speculative lookahead positions/occupied graphs may differ; these are\nobserved live caller states, not proof of equal complete committed-prefix KV.\n\n'
        else:text+='All committed arrays agree at this case; no divergent decision exists to diagnose.\n\n'
    text+='''## Supported explanation and remaining alternatives

The N0/N1 intervention demonstrably changes target continuation capacity/occupied
graph shape and preserves the initial captured state and first pending token.
Native target callers still carry actual live draft proposals; U2 is ordinary
target-only continuation. Same output IDs do not prove identical KV/logits/kernel
execution. F16-KV shared backend/greedy sampling, occupied graph shapes, caller
grouping and possible accumulated numerical differences remain explanations.
A correlated score/graph difference at the first output divergence is not unique
causal identification. No large new state instrumentation was introduced.

Unavailable: original live U2 KV/logits/sampler/graph metadata; full serialized KV
at the later first divergent N decision; opaque sampler bytes. Existing traces
provide actual pending IDs, positions/masks, proposals, selected target scores,
rollback endpoints and initial source/destination state. DIAGNOSTIC_FACTS.json
retains full selected sample/decode fields and all N graph summaries. U2 caller
dumps and all raw traces remain in the evidence archive. Raw samples/verification
decisions beyond an endpoint, if any, are exported separately and never compared
as committed output. No diagnostic observation replaces a formal result.
'''
    (DOC/'DIAGNOSTICS.md').write_text(text,encoding='utf-8',newline='\n')
    print(json.dumps({'outcome':summary['outcome'],'selected':selected,'formal':171,'diagnostic_generations':0,'changed':changed,'raw_sample_tails':len(tails)}),flush=True)
if __name__=='__main__':main()
