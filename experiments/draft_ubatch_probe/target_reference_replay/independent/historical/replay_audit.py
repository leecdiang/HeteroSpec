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

def valid_ids(ids, identity):
    need(isinstance(ids,list) and all(type(x) is int and 0<=x<identity['vocab'] for x in ids),'invalid token IDs')
def stopped(output, case, eog):
    return len(output)==case['cap'] or output[-1] in eog or (case.get('stop_after_output_index',0)>0 and len(output)==case['stop_after_output_index'])

def make_plan(case, prompt, identity):
    for field in ('reference_deployment_sha256','candidate_deployment_sha256','target_model_sha256','tokenizer_sha256'):
        need(isinstance(identity[field],str) and re.fullmatch('[0-9a-f]{64}',identity[field]),'invalid identity digest: '+field)
    valid_ids(prompt,identity);valid_ids(case['ids'],identity)
    need(prompt and case['ids'] and case['cap']>0,'empty prompt/output or bad cap')
    need(case.get('target_ubatch')==1 or case.get('capture_schema')=='native-target-v1','unsupported source schema')
    reference_widths(len(prompt),len(prompt),identity)
    eog=identity['eog_ids']; valid_ids(eog,identity)
    if case.get('stop_after_output_index',0):need(case.get('stop_is_synthetic_eog_predicate') is True,'unbound synthetic stop')
    q={};uses=[];commits=[]
    def use(prefix, name):
        need(len(prefix)<=identity['n_ctx'],'context capacity exceeded')
        k=query_id(prefix,identity,len(prompt))
        q.setdefault(k,{'query_id':k,'tokens':prefix.copy(),'positions':list(range(len(prefix))),'capture_uses':[],'state_required':False})
        q[k]['capture_uses'].append(name);uses.append({'use_id':name,'query_id':k})
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
    use(history,'initial');commit(history,output,done,'initial','initial')
    for i,c in enumerate(case['cycles']):
        need(not done,'cycle after terminal condition')
        base=len(history);need(c['base']==base,'wrong cycle base')
        if 'seed' in c:need(c['seed']==pending,'wrong actual seed')
        prop=c['proposals'];dec=c['decisions'];valid_ids(prop,identity);valid_ids(dec,identity)
        need(len(prop)==3 and len(dec)==4,'missing proposal or verification row')
        verify=[pending]+prop
        for j in range(4):use(history+verify[:j+1],f'cycle-{i}-row-{j}')
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
    jobs=[{'job_id':x['query_id'],'tokens':x['tokens'],'query_ids':[y['query_id'] for y in q.values() if x['tokens'][:len(y['tokens'])]==y['tokens']]} for x in leaves]
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
    need(plan==actual,'plan/identity differs from independent reconstruction')
    need(evidence['candidate_identity']==trusted_identity['candidate_deployment_sha256'],'candidate identity mismatch')
    need(evidence['reference_identity']==trusted_identity['reference_deployment_sha256'],'reference identity mismatch')
    need(evidence['state_format']==trusted_identity['state_format'],'UNPROVEN: incompatible state format')
    uses={x['use_id']:x for x in plan['uses']};qs={x['query_id']:x for x in plan['queries']}
    need(set(evidence['candidate_rows'])==set(uses),'missing/extra candidate rows, including unexamined rows')
    need(set(evidence['reference_queries'])==set(qs),'incomplete/extra forced-prefix query inventory')
    need(set(evidence['reference_jobs'])=={j['job_id'] for j in plan['fresh_replay_jobs']},'incomplete/extra fresh-R job inventory')
    for job in plan['fresh_replay_jobs']:
        observed=evidence['reference_jobs'][job['job_id']]
        need(observed['start_empty'] is True and observed['status']=='COMPLETED' and observed['tokens']==job['tokens'],'fresh-R maximal path incomplete or polluted')
        need(set(observed['observations'])==set(job['query_ids']),'missing/extra intermediate R prefix observation')
        for qid,obs in observed['observations'].items():
            canonical=evidence['reference_queries'][qid]
            ob,_=vector(root,obs['logits'],trusted_identity['vocab']);cb,_=vector(root,canonical['logits'],trusted_identity['vocab'])
            need(ob==cb,'duplicate fresh-R prefix observations disagree')
            if qs[qid]['state_required']:
                n=len(qs[qid]['tokens'])*trusted_identity['kv_bytes_per_token']
                need(blob(root,obs['kv'],n)==blob(root,canonical['kv'],n),'duplicate fresh-R KV observations disagree')
    need(set(evidence['candidate_commits'])=={x['commit_id'] for x in plan['commits']},'missing/extra committed snapshots')
    nv=trusted_identity['vocab']; read_bytes=0;row_vectors={};reference_vectors={}
    for key,q in qs.items():
        r=evidence['reference_queries'][key]
        need(r['mode']=='forced_prefix' and r['fresh_context'] is True and r['start_empty'] is True,'reference not a fresh forced-prefix replay')
        need(r['decoded_tokens']==q['tokens'] and r['positions']==q['positions'] and r['sequence_id']==0,'wrong forced reference prefix/positions')
        need(r['caller_widths']==reference_widths(len(q['tokens']),len(plan['prompt_ids']),trusted_identity),'reference producer recipe differs')
        need(r['physical_ubatches']==[1]*len(q['tokens']),'reference physical ubatch is not scalar')
        rb,rv=vector(root,r['logits'],nv);read_bytes+=len(rb);reference_vectors[key]=rb
        for name in q['capture_uses']:
            c=evidence['candidate_rows'][name];need(c['query_id']==key,'candidate wrong row/prefix identity')
            cb,cv=vector(root,c['logits'],nv);read_bytes+=len(cb)
            need(cb==rb,'full target vector bytes differ at '+name)
            row_vectors[name]=(cb,cv)
            if name=='initial':want=plan['expected_output'][0]
            else:
                _,i,_,j=name.split('-');want=plan['case']['cycles'][int(i)]['decisions'][int(j)]
            need(argmax(cv)==want,'recorded decision disagrees with actual vector')
    for commit in plan['commits']:
        c=evidence['candidate_commits'][commit['commit_id']]
        for field in ('query_id','positions','next_position','sequence_id','unmaterialized_output','pending_for_next_loop','done','frontier_logits_use'):
            need(c[field]==commit[field],'committed semantic metadata mismatch: '+field)
        r=evidence['reference_queries'][commit['query_id']]
        count=len(commit['tokens'])*trusted_identity['kv_bytes_per_token']
        cb=blob(root,c['kv'],count);rb=blob(root,r['kv'],count);read_bytes+=len(cb)+len(rb)
        need(cb==rb,'committed active KV bytes differ at '+commit['commit_id'])
        # The retained logits MUST come from row accepted, not the discarded final row.
        fb,_=vector(root,c['frontier_logits'],nv)
        need(fb==row_vectors[commit['frontier_logits_use']][0],'wrong saved frontier logits')
    free=evidence['free_scalar_run']
    need(free['mode']=='autonomous_scalar' and free['forced_tokens_used'] is False and free['fresh_context'] is True,'free-run oracle was teacher-forced')
    need(free['prompt_ids']==plan['prompt_ids'] and free['cap']==plan['case']['cap'],'free-run prompt/cap differs')
    consumed=plan['prompt_ids']+plan['expected_output'][:-1]
    need(free['start_empty'] is True and free['sequence_id']==0,'free-run initial/sequence state differs')
    need(free['decoded_tokens']==consumed and free['positions']==list(range(len(consumed))),'free-run materialized execution differs')
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
        b,v=vector(root,row,nv);read_bytes+=len(b);need(argmax(v)==token,'free-run output not its own greedy decision')
        key=query_id(prefix,trusted_identity,len(plan['prompt_ids']));need(key in reference_vectors,'free prefix missing forced reference coverage')
        need(b==reference_vectors[key],'free and forced scalar R vectors differ at same prefix')
    return {'status':'RECORDED_EVIDENCE_MATCH','target_vector_uses':len(uses),'unique_forced_prefix_queries':len(qs),
      'committed_snapshots':len(plan['commits']),'payload_bytes_read':read_bytes,
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
