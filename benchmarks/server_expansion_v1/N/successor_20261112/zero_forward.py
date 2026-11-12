"""Full supplied-history census using the actual GGUF tokenizer and template.

No llama context, model forward, GPU admission or performance measurements.
The vocabulary-only helper is separately source/hash bound. All heads are
predictions; supplied assistant tokens are not reference-generated history.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from jinja2.sandbox import ImmutableSandboxedEnvironment
import jinja2
from corpus import build_corpus
from geometry import schedule


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()


def need(value,message):
    if not value:raise ValueError(message)


def write(path,x):
    with path.open('x')as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')


def run(a):
    if a.out.exists():raise ValueError('Fresh census output required; retain previous epochs')
    a.out.mkdir(parents=True);began=time.monotonic()
    spec=json.loads(a.spec.read_text())
    if spec['model_forward_authorized']or spec['GPU_authorized']:raise ValueError('This entry is zero forward only')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('Explicit empty CUDA visibility required')
    expected=spec['model'];need(a.model.stat().st_size==expected['bytes']and sha(a.model)==expected['sha256'],'Exact model bytes')
    need(sha(a.tokenizer)==spec['tokenizer_executable_sha256'],'Exact vocabulary executable')
    need(sha(a.template)==spec['chat_template_sha256'],'Exact GGUF chat template')
    need(sha(a.messages)==spec['messages_sha256'],'Complete normalized corpus bytes')
    need(jinja2.__version__==spec['renderer']['version'],'Pinned actual template renderer')
    raw=json.loads(a.messages.read_text());corpus=build_corpus(raw)
    write(a.out/'CORPUS.json',corpus)
    turns=corpus['user_turns'];nodes={x['message_id']:x for x in raw if isinstance(x,dict)and isinstance(x.get('message_id'),str)}
    env=ImmutableSandboxedEnvironment(trim_blocks=True,lstrip_blocks=True,autoescape=False)
    template=env.from_string(a.template.read_text())
    def render(messages):
        ms=[dict(m,tool_calls=[])for m in messages]
        return template.render(messages=ms,tools=None,add_generation_prompt=True,enable_thinking=False)
    queries=[];rendered={}
    for t in turns:
        if t['status']!='SUPPORTED':continue
        text=render(t['messages']);key='prompt:'+t['message_id'];rendered[key]=text
        queries.append(dict(task_id=key,formatted_prompt=text,add_special=False))
    for n in raw:
        if isinstance(n,dict)and n.get('role')=='assistant'and isinstance(n.get('text'),str)and n['text']:
            queries.append(dict(task_id='body:'+n['message_id'],formatted_prompt=n['text'],add_special=False))
    # Selection is source-only and fixed before any tokenizer geometry/result.
    root_paths={}
    for p in corpus['root_to_leaf_paths']:
        if p['status']=='SUPPORTED'and p['terminal_role']=='assistant'and len(p['user_message_ids'])>=2:
            root_paths.setdefault(p['root'],[]).append(p)
    chosen=sorted(root_paths,key=lambda r:hashlib.sha256(('N200-dev-v1:'+r).encode()).hexdigest())[:4]
    development=[]
    for r in chosen:
        p=min(root_paths[r],key=lambda p:p['leaf_message_id'])
        development.append(dict(root=r,leaf=p['leaf_message_id'],user_message_ids=p['user_message_ids'][:4],
            source_only_max_turns=4,selection='SHA256(N200-dev-v1:+root),lexicographic leaf; no tokenizer/offset/latency/acceptance selection'))
    write(a.out/'FOUR_DEVELOPMENT_SOURCE_INPUTS.json',development)
    with (a.out/'TOKENIZER_INPUT.jsonl').open('x')as f:
        for q in queries:f.write(json.dumps(q,ensure_ascii=False)+'\n')
    with (a.out/'TOKENIZER_INPUT.jsonl').open('rb')as si,(a.out/'TOKENIZER_OUTPUT.jsonl').open('xb')as so,(a.out/'TOKENIZER.stderr.log').open('xb')as se:
        result=subprocess.run([str(a.tokenizer),str(a.model)],stdin=si,stdout=so,stderr=se,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),timeout=1800)
    if result.returncode:raise RuntimeError('Vocabulary-only tokenizer failed; preserve logs')
    tokenized={};vocab=None
    with (a.out/'TOKENIZER_OUTPUT.jsonl').open()as f:
        for line in f:
            r=json.loads(line)
            need(r['vocab_only']is True and r['forward_calls']==0,'Vocabulary-only receipt')
            if r.get('event')=='vocabulary':vocab=r
            else:
                need(r['task_id']not in tokenized,'Unique tokenizer query');tokenized[r['task_id']]=r['prompt_ids']
    need(vocab and len(tokenized)==len(queries)and vocab['context_creations']==0,'Complete context-free vocabulary/tokenization output')
    for n in raw:
        if isinstance(n,dict)and n.get('role')=='assistant'and n.get('text')=='':tokenized['body:'+n['message_id']]=[]
    eos=spec['provided_history_eog_id'];need(eos in vocab['eog']and vocab['add_bos']is False,'Native EOG/BOS binding')
    rows=[]
    for t in turns:
        base=dict(message_id=t['message_id'],root=t.get('root'),turn=t.get('turn_index'),
            native_head=None,head_observed=False,head_source='token_geometry_prediction',
            history_origin='provided_conversation',not_dropped_from_denominator=True)
        if t['status']!='SUPPORTED':rows.append(dict(base,status='UNSUPPORTED_SOURCE',source_issues=t['issues']));continue
        pid='prompt:'+t['message_id'];ids=tokenized[pid];n=len(ids);chain=t['chain_to_node']
        initial=len(chain)==1;previous=[];reply=[];prefix=True;lcp=0;pending=None
        prior_long=False;provided_embedded_eog=False
        for node in chain[:-1]:
            if nodes[node]['role']=='assistant':
                body=tokenized['body:'+node]
                prior_long|=len(body)>128;provided_embedded_eog|=any(x in vocab['eog']for x in body)
        if not initial:
            assistant=chain[-2];previous_user=chain[-3]
            reply=tokenized['body:'+assistant]
            previous=tokenized['prompt:'+previous_user]+reply+[eos]
            prefix=n>=len(previous)and ids[:len(previous)]==previous
            for old,new in zip(previous,ids):
                if old!=new:break
                lcp+=1
            pending=previous[-1]
        h=0 if initial or not prefix else len(previous)-1
        append=n-h
        # A complete cap128 continuation needs127 additional materialized rows.
        capacity=n+127<=4096
        status='INITIAL_PREFILL'if initial else'PREFIX_REUSABLE_PREDICTION'if prefix else'COMMON_REBUILD_REQUIRED'
        g=schedule(h,append,32,256,4096)if capacity else None
        rows.append(dict(base,status=status if capacity else'UNSUPPORTED_CAPACITY',lifecycle_if_capacity_admitted=status,
            prompt_tokens=n,prompt_ids=ids,prompt_sha256=hashlib.sha256(canonical(ids)).hexdigest(),
            formatted_prompt_sha256=hashlib.sha256(rendered[pid].encode()).hexdigest(),
            prefix_reusable=prefix if not initial else None,token_prefix_lcp=lcp if not initial else None,
            previous_provided_chain_tokens=len(previous)if not initial else None,
            predicted_head_before_pending=len(previous)-1 if not initial else 0,
            predicted_pending_id=pending,pending_policy='Previous provided EOG is pending; reused append would include it once. Rebuild resets all methods before any mutation.',
            predicted_execution_head=h,predicted_append_rows=append,
            common_rebuild_rows=n if not initial and not prefix else 0,
            provided_history_has_response_over_cap128=prior_long,
            provided_history_has_embedded_eog=provided_embedded_eog,
            history_native_cap_compatibility='NOT_A_NATIVE_PRODUCER; supplied responses not truncated',
            capacity_admitted=capacity,capacity_required_worst_case=n+127,
            geometry=g,causal_native_or_performance_claim=False))
    write(a.out/'TURN_CENSUS.json',rows)
    rowmap={r['message_id']:r for r in rows};expanded=Counter()
    for p in corpus['root_to_leaf_paths']:
        if p['status']=='SUPPORTED':
            for m in p['user_message_ids']:expanded[rowmap[m]['status']]+=1
    admitted=[r for r in rows if r.get('geometry')]
    distinct=[r for r in admitted if r['geometry']['comparisons']['projection_partition_distinct']]
    noninitial=[r for r in rows if (r.get('turn')or 0)>0]
    report=dict(schema='heterospec.N.actual_tokenizer_provided_history_census.v1',status='ZERO_FORWARD_CENSUS_COMPLETE',
        model_forward_calls=0,GPU_requests=0,model_context_creations=0,
        source=spec['source'],model=expected,chat_template_sha256=spec['chat_template_sha256'],
        renderer=spec['renderer'],tokenizer_executable_sha256=spec['tokenizer_executable_sha256'],
        native_head_observations=0,history_origin='provided_conversation',
        message_count=len(raw),source_counts=corpus['counts'],unique_user_turns=len(rows),
        unique_turn_status_counts=dict(Counter(r['status']for r in rows)),path_expanded_turn_status_counts=dict(expanded),
        noninitial_unique_turns=len(noninitial),true_token_prefix_reusable_predictions=sum(r.get('prefix_reusable')is True for r in noninitial),
        canonical_prefix_mismatch_predictions=sum(r.get('prefix_reusable')is False for r in noninitial),
        history_contains_response_over_cap128_turns=sum(r.get('provided_history_has_response_over_cap128',False)for r in rows),
        capacity_unsupported_turns=sum(r['status']=='UNSUPPORTED_CAPACITY'for r in rows),
        admitted_geometry_turns=len(admitted),distinct_strong_rechunk_vs_LOCAL_projection_partitions=len(distinct),
        all_admitted_predicted_attention_work_equal=all(r['geometry']['comparisons']['predicted_padded_attention_work_equal']for r in admitted),
        unique_admitted_total_rows=sum(r['predicted_append_rows']for r in admitted),
        total_predicted_calls={k:sum(r['geometry'][k]['call_count']for r in admitted)for k in ('whole_fixed','whole_rechunk','local_outer','local_inner')},
        decision='NO_DISTINCT_CUT_OPPORTUNITY_UNDER_FROZEN_PROVIDED_HISTORY_CONTRACT_STOP_GPU_PANEL'if not distinct else'UNRESOLVED_STRUCTURAL_QUESTION_REQUIRES_NEW_GPU_ADMISSION',
        decision_limit='Geometry only; no timing/equivalence proof. Canonical full-template token-prefix contract and supplied history are fixed; other rendering policies/free sequential producer histories are different studies.',
        failure_and_exclusion_policy='Source/prefix/capacity/long-response limitations remain in denominators; no padding, offset, language,rank or latency selection.',
        caller_s=time.monotonic()-began)
    write(a.out/'CENSUS_REPORT.json',report);print(json.dumps(report))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('spec','messages','model','template','tokenizer','out'):p.add_argument('--'+name,type=Path,required=True)
    run(p.parse_args())
