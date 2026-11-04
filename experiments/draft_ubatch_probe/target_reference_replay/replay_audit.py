#!/usr/bin/env python3
"""Offline replay-plan/evidence audit prototype. No inference, GPU, or network.
A successful audit is not an attestation of the producer, extractor, or GPU.
"""
import argparse, hashlib, json, math, struct, re
from pathlib import Path

class EvidenceError(ValueError): pass

def need(ok, msg):
    if not ok: raise EvidenceError(msg)
def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def query_id(prefix, identity, prompt_length):
    return digest({'reference_deployment':identity['reference_deployment_sha256'],
                   'target_model':identity['target_model_sha256'],
                   'tokenizer':identity['tokenizer_sha256'],
                   'positions':list(range(len(prefix))), 'tokens':prefix,
                   'n_ctx':identity['n_ctx'],'reference_recipe':identity['reference_recipe'],'prompt_boundary':prompt_length})
def reference_widths(prefix_length, prompt_length, identity):
    recipe=identity['reference_recipe']
    if recipe=='tokenwise_all':return [1]*prefix_length
    need(recipe=='historical_prefill_then_scalar','unknown reference producer recipe')
    need(prefix_length>=prompt_length>0,'invalid reference prompt boundary')
    return [prompt_length]+[1]*(prefix_length-prompt_length)

def reference_metadata(tokens, prompt_length, identity):
    widths=reference_widths(len(tokens),prompt_length,identity)
    return {'mode':'forced_prefix','fresh_context':True,'start_empty':True,
      'decoded_tokens':tokens,'positions':list(range(len(tokens))),'sequence_id':0,
      'caller_widths':widths,'physical_ubatches':[1]*len(tokens),
      'logits_masks':[[False]*(w-1)+[True] for w in widths]}

def candidate_metadata(tokens, base, row, call_id, identity):
    ub=identity['candidate_target_ubatch'];n=len(tokens)
    return {'call_id':call_id,'tokens':tokens,'positions':list(range(base,base+n)),
      'sequence_ids':[0]*n,'caller_width':n,'physical_ubatches':[min(ub,n-i) for i in range(0,n,ub)],
      'logits_mask':([False]*(n-1)+[True]) if call_id=='prefill' else [True]*n,
      'captured_batch_row':row,'captured_output_index':0 if call_id=='prefill' else row}

def same_metadata(record, expected, label):
    for field,value in expected.items():
        need(field in record and digest(record[field])==digest(value) and type(record[field]) is type(value),label+': '+field)

def valid_ids(ids, identity):
    need(isinstance(ids,list) and all(type(x) is int and 0<=x<identity['vocab'] for x in ids),'invalid token IDs')
def stopped(output, case, eog):
    return len(output)==case['cap'] or output[-1] in eog or (case.get('stop_after_output_index',0)>0 and len(output)==case['stop_after_output_index'])

def make_plan(case, prompt, identity):
    for field in ('reference_deployment_sha256','candidate_deployment_sha256','target_model_sha256','tokenizer_sha256'):
        need(isinstance(identity[field],str) and re.fullmatch('[0-9a-f]{64}',identity[field]),'invalid identity digest: '+field)
    need(type(identity['vocab']) is int and identity['vocab']>0,'invalid vocabulary size')
    need(type(identity['n_ctx']) is int and identity['n_ctx']>0,'invalid context size')
    need(type(identity['candidate_target_ubatch']) is int and identity['candidate_target_ubatch'] in (1,4),'unsupported candidate target ubatch')
    need(identity['candidate_prefill_recipe']=='whole_prompt_last_only','unsupported candidate prefill producer')
    need(type(case['cap']) is int and case['cap']>0,'invalid integer output cap')
    need(type(case.get('stop_after_output_index',0)) is int and case.get('stop_after_output_index',0)>=0,'invalid synthetic stop index')
    need(type(case['cycles']) is list,'invalid cycles inventory')
    need(type(case.get('forced_reject_index',-1)) is int and -1<=case.get('forced_reject_index',-1)<=3,'invalid forced rejection probe index')
    valid_ids(prompt,identity);valid_ids(case['ids'],identity)
    need(prompt and case['ids'] and case['cap']>0,'empty prompt/output or bad cap')
    need(type(case.get('target_ubatch')) is int and case['target_ubatch']==identity['candidate_target_ubatch'],'source target ubatch differs')
    need(case['target_ubatch']==1 or case.get('capture_schema')=='native-target-v1','unsupported source schema')
    reference_widths(len(prompt),len(prompt),identity)
    eog=identity['eog_ids']; valid_ids(eog,identity)
    if case.get('stop_after_output_index',0):need(case.get('stop_is_synthetic_eog_predicate') is True,'unbound synthetic stop')
    q={};uses=[];commits=[]
    def use(prefix, name, producer):
        need(len(prefix)<=identity['n_ctx'],'context capacity exceeded')
        k=query_id(prefix,identity,len(prompt))
        q.setdefault(k,{'query_id':k,'tokens':prefix.copy(),'positions':list(range(len(prefix))),'capture_uses':[],'state_required':False})
        q[k]['capture_uses'].append(name);uses.append({'use_id':name,'query_id':k,'producer':producer})
        return k
    def commit(prefix, output, done, name, frontier_use):
        n=len(prefix)-len(prompt)
        need(0<=n<=len(output) and len(output)-n<=1,'invalid materialized frontier')
        need(prefix==prompt+output[:n],'state history differs from independent emitted frontier')
        left=output[n:]
        need(done or len(left)==1,'nonterminal commit must retain one pending token')
        k=query_id(prefix,identity,len(prompt));need(k in q,'state prefix lacks target query')
        q[k]['state_required']=True
        commits.append({'commit_id':name,'query_id':k,'tokens':prefix.copy(),'positions':list(range(len(prefix))),
          'next_position':len(prefix),'sequence_id':0,'unmaterialized_output':left.copy(),
          'pending_for_next_loop':None if done else left[0],'done':done,
          'frontier_logits_use':frontier_use})
    initial=case['ids'][0];output=[initial];history=prompt.copy();pending=initial;done=stopped(output,case,eog)
    use(history,'initial',candidate_metadata(prompt,0,len(prompt)-1,'prefill',identity));commit(history,output,done,'initial','initial')
    for i,c in enumerate(case['cycles']):
        need(not done,'cycle after terminal condition')
        for field in ('base','accepted','keep'):
            need(type(c[field]) is int,'noninteger cycle field: '+field)
        need(c.get('pending') is None or type(c['pending']) is int,'invalid cycle pending type')
        if 'seed' in c:need(type(c['seed']) is int,'invalid cycle seed type')
        base=len(history);need(c['base']==base,'wrong cycle base')
        if 'seed' in c:need(c['seed']==pending,'wrong actual seed')
        prop=c['proposals'];dec=c['decisions'];valid_ids(prop,identity);valid_ids(dec,identity)
        need(len(prop)==3 and len(dec)==4,'missing proposal or verification row')
        verify=[pending]+prop
        for j in range(4):use(history+verify[:j+1],f'cycle-{i}-row-{j}',candidate_metadata(verify,base,j,f'verify-{i}',identity))
        accepted=0;last=None
        for j in range(3):
            if done:break
            if dec[j]==prop[j]: accepted+=1;token=prop[j];last='accepted'
            else:token=dec[j];pending=token;last='correction'
            output.append(token);done=stopped(output,case,eog)
            if last=='correction':break
        if accepted==3 and not done:
            pending=dec[3];output.append(pending);done=stopped(output,case,eog);last='bonus'
        history+=verify[:1+accepted]
        need(c['accepted']==accepted and c['last']==last and c['keep']==len(history),'recorded transaction differs')
        need(c.get('pending')==(None if done else pending),'next-loop pending differs')
        commit(history,output,done,f'cycle-{i}',f'cycle-{i}-row-{accepted}')
    need(done,'incomplete request')
    need(output==case['ids'],'endpoint differs from independently replayed transaction')
    need(len(output)<=case['cap'] and not any(t in eog for t in output[:-1]),'invalid stop history')
    need(bool(case['cycles'])==(len(output)>1),'vacuous cycle coverage')
    leaves=[x for x in q.values() if not any(len(y['tokens'])>len(x['tokens']) and y['tokens'][:len(x['tokens'])]==x['tokens'] for y in q.values())]
    jobs=[];assigned=set()
    for x in leaves:
        available=[y['query_id'] for y in q.values() if x['tokens'][:len(y['tokens'])]==y['tokens']]
        owned=[k for k in available if k not in assigned];assigned.update(owned)
        jobs.append({'job_id':x['query_id'],'tokens':x['tokens'],'query_ids':owned,'available_query_ids':available})
    need(assigned==set(q),'internal reference capture assignment incomplete')
    return {'fresh_replay_jobs':jobs,'schema':'hs-target-replay-plan-v1','status':'PLAN_ONLY_NOT_QUALIFICATION',
      'identity':identity,'prompt_ids':prompt,'case':case,'queries':list(q.values()),'uses':uses,'commits':commits,
      'expected_output':output,'proposal_mode':'native_draft' if case.get('forced_reject_index',-1)<0 else 'forced_protocol_probe',
      'warning':'Derived plan. Current PR183 journals lack raw vectors, per-commit KV and native deployment attestation; a plan is not numerical evidence.'}

def blob(root, ref, expected_size):
    need(set(ref)>= {'path','sha256','bytes'},'incomplete blob reference')
    p=(root/ref['path']).resolve();need(p.is_relative_to(root.resolve()),'payload path escapes bundle')
    need(p.is_file(),'INCOMPLETE: missing payload')
    b=p.read_bytes();need(len(b)==ref['bytes']==expected_size,'payload byte length mismatch')
    need(hashlib.sha256(b).hexdigest()==ref['sha256'],'payload digest mismatch')
    return b

def vector(root, ref, vocab):
    b=blob(root,ref,4*vocab);v=struct.unpack('<'+'f'*vocab,b)
    need(all(math.isfinite(x) for x in v),'nonfinite target vector')
    return b,v

def argmax(v):return max(range(len(v)),key=v.__getitem__)

def audit(plan, evidence, root, trusted_identity):
    need(trusted_identity.get('binding_complete') is True,'UNPROVEN: incomplete deployment binding')
    need(type(trusted_identity['kv_bytes_per_token']) is int and trusted_identity['kv_bytes_per_token']>0,'UNPROVEN: zero or invalid KV size contract')
    # Reconstruct rather than trusting a user-editable precomputed plan.
    actual=make_plan(plan['case'],plan['prompt_ids'],trusted_identity)
    need(digest(plan)==digest(actual),'plan/identity differs from independent reconstruction')
    need(evidence['candidate_identity']==trusted_identity['candidate_deployment_sha256'],'candidate identity mismatch')
    need(evidence['reference_identity']==trusted_identity['reference_deployment_sha256'],'reference identity mismatch')
    need(evidence['state_format']==trusted_identity['state_format'],'UNPROVEN: incompatible state format')
    nv=trusted_identity['vocab'];read_bytes=0;read_calls=0
    def read_blob(ref, size):
        nonlocal read_bytes,read_calls
        b=blob(root,ref,size);read_bytes+=len(b);read_calls+=1;return b
    def read_vector(ref):
        b=read_blob(ref,4*nv);v=struct.unpack('<'+'f'*nv,b)
        need(all(math.isfinite(x) for x in v),'nonfinite target vector');return b,v
    uses={x['use_id']:x for x in plan['uses']};qs={x['query_id']:x for x in plan['queries']}
    need(set(evidence['candidate_rows'])==set(uses),'missing/extra candidate rows, including unexamined rows')
    need(set(evidence['reference_queries'])==set(qs),'incomplete/extra forced-prefix query inventory')
    need(set(evidence['reference_jobs'])=={j['job_id'] for j in plan['fresh_replay_jobs']},'incomplete/extra fresh-R job inventory')
    for job in plan['fresh_replay_jobs']:
        observed=evidence['reference_jobs'][job['job_id']]
        same_metadata(observed,{'start_empty':True,'status':'COMPLETED','tokens':job['tokens']},'fresh-R maximal path incomplete or polluted')
        same_metadata(observed['execution'],reference_metadata(job['tokens'],len(plan['prompt_ids']),trusted_identity),'fresh-R job execution metadata differs')
        need(set(job['query_ids'])<=set(observed['observations'])<=set(job['available_query_ids']),'missing required or invalid intermediate R prefix observation')
        for qid,obs in observed['observations'].items():
            canonical=evidence['reference_queries'][qid]
            same_metadata(obs,reference_metadata(qs[qid]['tokens'],len(plan['prompt_ids']),trusted_identity),'fresh-R observation metadata differs')
            ob,_=read_vector(obs['logits']);cb,_=read_vector(canonical['logits'])
            need(ob==cb,'duplicate fresh-R prefix observations disagree')
            if qs[qid]['state_required']:
                n=len(qs[qid]['tokens'])*trusted_identity['kv_bytes_per_token']
                need(read_blob(obs['kv'],n)==read_blob(canonical['kv'],n),'duplicate fresh-R KV observations disagree')
    need(set(evidence['candidate_commits'])=={x['commit_id'] for x in plan['commits']},'missing/extra committed snapshots')
    row_vectors={};reference_vectors={}
    for key,q in qs.items():
        r=evidence['reference_queries'][key]
        same_metadata(r,reference_metadata(q['tokens'],len(plan['prompt_ids']),trusted_identity),'reference execution metadata differs')
        need(r['mode']=='forced_prefix' and r['fresh_context'] is True and r['start_empty'] is True,'reference not a fresh forced-prefix replay')
        need(r['decoded_tokens']==q['tokens'] and r['positions']==q['positions'] and r['sequence_id']==0,'wrong forced reference prefix/positions')
        need(r['caller_widths']==reference_widths(len(q['tokens']),len(plan['prompt_ids']),trusted_identity),'reference producer recipe differs')
        need(r['physical_ubatches']==[1]*len(q['tokens']),'reference physical ubatch is not scalar')
        rb,rv=read_vector(r['logits']);reference_vectors[key]=rb
        for name in q['capture_uses']:
            c=evidence['candidate_rows'][name];need(c['query_id']==key,'candidate wrong row/prefix identity')
            same_metadata(c['producer'],uses[name]['producer'],'candidate producer metadata differs')
            cb,cv=read_vector(c['logits'])
            need(cb==rb,'full target vector bytes differ at '+name)
            row_vectors[name]=rb  # Equality checked; retain one raw reference, not Python floats.
            if name=='initial':want=plan['expected_output'][0]
            else:
                _,i,_,j=name.split('-');want=plan['case']['cycles'][int(i)]['decisions'][int(j)]
            need(argmax(cv)==want,'recorded decision disagrees with actual vector')
    for commit in plan['commits']:
        c=evidence['candidate_commits'][commit['commit_id']]
        for field in ('query_id','positions','next_position','sequence_id','unmaterialized_output','pending_for_next_loop','done','frontier_logits_use'):
            same_metadata(c,{field:commit[field]},'committed semantic metadata mismatch')
        r=evidence['reference_queries'][commit['query_id']]
        count=len(commit['tokens'])*trusted_identity['kv_bytes_per_token']
        cb=read_blob(c['kv'],count);rb=read_blob(r['kv'],count)
        need(cb==rb,'committed active KV bytes differ at '+commit['commit_id'])
        # The retained logits MUST come from row accepted, not the discarded final row.
        fb,_=read_vector(c['frontier_logits'])
        need(fb==row_vectors[commit['frontier_logits_use']],'wrong saved frontier logits')
    free=evidence['free_scalar_run']
    need(free['mode']=='autonomous_scalar' and free['forced_tokens_used'] is False and free['fresh_context'] is True,'free-run oracle was teacher-forced')
    need(free['prompt_ids']==plan['prompt_ids'] and free['cap']==plan['case']['cap'],'free-run prompt/cap differs')
    consumed=plan['prompt_ids']+plan['expected_output'][:-1]
    need(free['start_empty'] is True and free['sequence_id']==0,'free-run initial/sequence state differs')
    need(free['decoded_tokens']==consumed and free['positions']==list(range(len(consumed))),'free-run materialized execution differs')
    need(free['logits_masks']==reference_metadata(consumed,len(plan['prompt_ids']),trusted_identity)['logits_masks'],'free-run output mask differs')
    need(free['caller_widths']==reference_widths(len(consumed),len(plan['prompt_ids']),trusted_identity),'free-run producer recipe differs')
    need(free['physical_ubatches']==[1]*len(consumed),'free-run physical ubatch is not scalar')
    expected_prefixes=[plan['prompt_ids']+plan['expected_output'][:i] for i in range(len(plan['expected_output']))]
    need(free['prefixes']==expected_prefixes,'free-run prefixes differ')
    need(free['eog_flags']==[t in trusted_identity['eog_ids'] for t in free['output']],'native EOG classification differs')
    need(free['output']==plan['expected_output'],'free greedy endpoint differs')
    stop_contract={'cap':plan['case']['cap'],'eog_ids':trusted_identity['eog_ids'],'synthetic_stop_after':plan['case'].get('stop_after_output_index',0)}
    need(free['stop_contract']==stop_contract,'free-run stop contract differs')
    reason='EOG' if free['output'][-1] in trusted_identity['eog_ids'] else ('CAP' if len(free['output'])==plan['case']['cap'] else 'SYNTHETIC_STOP')
    need(free['stop_reason']==reason,'free-run stop reason differs')
    need(len(free['logits'])==len(free['output']),'free-run vector count differs')
    for prefix,row,token in zip(expected_prefixes,free['logits'],free['output']):
        b,v=read_vector(row);need(argmax(v)==token,'free-run output not its own greedy decision')
        key=query_id(prefix,trusted_identity,len(plan['prompt_ids']));need(key in reference_vectors,'free prefix missing forced reference coverage')
        need(b==reference_vectors[key],'free and forced scalar R vectors differ at same prefix')
    same_metadata(free,{'mode':'autonomous_scalar','forced_tokens_used':False,'fresh_context':True,
      'start_empty':True,'sequence_id':0,'prompt_ids':plan['prompt_ids'],'cap':plan['case']['cap'],
      'decoded_tokens':consumed,'positions':list(range(len(consumed))),
      'caller_widths':reference_widths(len(consumed),len(plan['prompt_ids']),trusted_identity),
      'physical_ubatches':[1]*len(consumed),'logits_masks':reference_metadata(consumed,len(plan['prompt_ids']),trusted_identity)['logits_masks'],
      'prefixes':expected_prefixes,'output':plan['expected_output'],
      'eog_flags':[t in trusted_identity['eog_ids'] for t in plan['expected_output']],
      'stop_contract':stop_contract,'stop_reason':reason},'free-run typed metadata differs')
    return {'status':'RECORDED_EVIDENCE_MATCH','target_vector_uses':len(uses),'unique_forced_prefix_queries':len(qs),
      'committed_snapshots':len(plan['commits']),'payload_bytes_read':read_bytes,'payload_read_calls':read_calls,
      'payload_counting_scope':'Logical successful payload reads, including repeated references and frontier/job evidence; not unique storage bytes or measured OS disk IO.',
      'gpu_qualification_established':False,'scope':trusted_identity['scope'],
      'limits':'Offline bytes/coverage/semantic consistency only. Producer truth, source/binary/device/JIT binding, canonical KV extractor correctness, observation effects and hidden backend state remain external qualification gates.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',type=Path,required=True);p.add_argument('--identity',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--evidence',type=Path);p.add_argument('--bundle',type=Path)
    a=p.parse_args();t=json.loads(a.trace.read_text());identity=json.loads(a.identity.read_text());plan=make_plan(t['case'],t['prompt_ids'],identity)
    if a.evidence:
        need(a.bundle is not None,'--bundle required');result=audit(plan,json.loads(a.evidence.read_text()),a.bundle,identity)
    else:result=plan
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
if __name__=='__main__':main()
