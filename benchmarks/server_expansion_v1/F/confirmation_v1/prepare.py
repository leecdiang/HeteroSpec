"""Zero-forward native cohort admission and prospective24-worker Llama plan."""
from pathlib import Path
import argparse, copy, datetime, gzip, hashlib, json, subprocess, sys, time, unicodedata

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('integration','runtime','work','builds','assets','vocabulary_build','materials'):
        parser.add_argument('--'+key.replace('_','-'),type=Path,required=True)
    a=parser.parse_args()
    for key,value in vars(a).items():setattr(a,key,value.resolve())
    sys.path.insert(0,str(a.integration));import integrate as d
    d.load(a.runtime);need,read,save,sha=d.need,d.read,d.save,d.sha
    started=time.monotonic();w=a.work;out=w/'inputs-formal-01';token_out=w/'preparation-formal-tokenizer-01'
    need(not out.exists() and not token_out.exists() and not (w/'panel-01').exists(),'Fresh prospective preparation; preserve every prior epoch')
    out.mkdir();token_out.mkdir()
    policy=read(a.materials/'POLICY.json');pool=read(a.materials/'POOL.json');review=read(a.materials/'EXPOSURE_REVIEW.json')
    need(review['complete'] and not review['unresolved_sources'] and not review['training_unseen_claim'],'Closed project-history exposure scope first')
    for name,h in policy['materials'].items():need(sha(a.materials/name)==h,'Prospective material changed: '+name)
    exclusion_bytes=gzip.decompress((a.materials/'EXCLUSION_UNIVERSE.sha256.txt.gz').read_bytes())
    need(hashlib.sha256(exclusion_bytes).hexdigest()==review['uncompressed_sha256'],'Exclusion decompression changed')
    exclusions=set(exclusion_bytes.decode('ascii').splitlines())
    need(len(exclusions)==review['hashed_exclusion_key_count'],'Exclusion count')
    q=w/'qualification-registry-04';summary=read(q/'NATIVE_CHECKS_COMPLETE.json')
    need(sha(q/'NATIVE_CHECKS_COMPLETE.json')==policy['qualification_summary_sha256'] and summary['passed'] and summary['all_six_arms'],'Actual finite native qualification first')
    need(sha(q/'REGISTRY.json')==policy['qualification_registry_sha256'],'Different qualified registry')
    for row in summary['proofs']:need(sha(row['path'])==row['sha256'] and read(row['path'])['passed'],'Actual native proof changed')
    need(read(q/'PROJECTION_DISPATCH.json')['passed'] and read(w/'capability-negatives-01/CHECKED.json')['passed'],'Actual dispatch and native negatives')
    for core,expected in policy['executables'].items():
        build=read(a.builds/core/'BUILD.json')
        need(build['executable_sha256']==expected and sha(build['executable'])==expected,'Qualified executable changed: '+core)
    cfg=read(w/'config-reference-frozen-01.json');rf=Path(cfg['reference_freeze'])
    need(sha(rf)==cfg['reference_freeze_sha256'] and read(rf)['status']=='REFERENCE_FROZEN','Original independent Llama R changed')
    need(read(rf)['build']['sha256']==sha(a.builds/'reference/BUILD.json'),'Different pristine R build')
    assets=read(a.assets/'CHECKED.json');need(assets['passed'] and assets['full_native_pair_vocabulary_equal'],'Verified original native assets first')
    scaffold_file=a.assets/'target-vocabulary.stdout.jsonl'
    need(sha(scaffold_file)==next(x['helper_stdout_sha256'] for x in assets['models'] if x['role']=='target'),'Archived target scaffold receipt changed')
    with scaffold_file.open() as stream:stream.readline();scaffold=json.loads(stream.readline())['native_detokenized_prompt']
    marker='<|start_header_id|>user<|end_header_id|>\n\n'
    need(scaffold.count(marker)==1 and scaffold.count('<|begin_of_text|>')==1,'Single verified archived user/BOS scaffold')
    first=scaffold.index(marker)+len(marker);last=scaffold.index('<|eot_id|>',first)
    history=read(a.integration/'HISTORICAL_LLAMA.json');models=read(w/'inputs-01/MODELS.json')[d.FAMILY]
    build=read(a.vocabulary_build/'BUILD.json')
    need(build['role']=='vocabulary_only_not_reference' and sha(build['executable'])==policy['vocabulary_executable_sha256']==build['executable_sha256'],'Exact existing no-forward vocabulary helper')
    for path,h in read(a.vocabulary_build/'DEPENDENCIES.json')['files'].items():need(sha(path)==h,'Vocabulary dependency changed')
    for role in ('target','draft'):
        path=Path(models[role+'_model']);pin=policy['models'][role]
        need(path.stat().st_size==pin['bytes'] and sha(path)==pin['sha256']==models[role+'_sha256'],'Exact model changed: '+role)
    save(out/'BEFORE_TOKENIZATION.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_sha256=sha(Path(__file__)),policy_sha256=sha(a.materials/'POLICY.json'),integration_sha256=sha(a.integration/'integrate.py'),
        qualification_sha256=sha(q/'NATIVE_CHECKS_COMPLETE.json'),registry_sha256=sha(q/'REGISTRY.json'),reference_freeze_sha256=sha(rf),
        vocabulary_build_sha256=sha(a.vocabulary_build/'BUILD.json'),scaffold_receipt_sha256=sha(scaffold_file),
        target_template_sha256=history['template_sha256'],draft_template_sha256=history['draft_template_sha256'],
        new_cohort_model_forwards=0,selection_does_not_use_outputs=True))
    for name in ('POOL.json','POLICY.json','EXPOSURE_REVIEW.json'):save(out/name,read(a.materials/name))
    def text_keys(text):
        normalized=' '.join(unicodedata.normalize('NFKC',text).split())
        return {hashlib.sha256(x.encode()).hexdigest() for x in (text,text.strip(),normalized)}
    admitted=[];decisions=[]
    need(len(pool['inputs'])==70 and len({x['id'] for x in pool['inputs']})==70,'Fixed70 statement pool')
    for x in pool['inputs']:
        rank=hashlib.sha256((str(policy['seed'])+'|'+x['id']).encode()).hexdigest()
        prompt=scaffold[:first]+x['raw_prompt']+scaffold[last:]
        keys={hashlib.sha256(x['id'].encode()).hexdigest()}|text_keys(x['description'])|text_keys(x['raw_prompt'])|text_keys(prompt)
        overlap=sorted(keys&exclusions)
        decision=dict(id=x['id'],domain=x['domain'],rank=rank,preexisting_hash_matches=overlap,formatted_prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest())
        decisions.append(decision)
        if not overlap:admitted.append(dict(x,rank=rank,formatted_prompt=prompt))
    save(out/'POOL_ADMISSION_BEFORE_TOKENIZATION.json',dict(decisions=decisions,model_forwards=0,cohort_selected=False))
    need(admitted,'No unexposed statements remain')
    queries=''.join(json.dumps(dict(task_id=x['id'],formatted_prompt=x['formatted_prompt'],add_special=False),ensure_ascii=False)+'\n' for x in admitted)
    native={};costs=[];env=d.host.environment('');env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    for role in ('target','draft'):
        began=time.monotonic();stdout=token_out/(role+'.stdout.jsonl');stderr=token_out/(role+'.stderr.log')
        with stdout.open('xb') as stream,stderr.open('xb') as errors:
            result=subprocess.run([build['executable'],models[role+'_model']],input=queries.encode(),stdout=stream,stderr=errors,env=env,timeout=300)
        costs.append(dict(role=role,returncode=result.returncode,wall_s=time.monotonic()-began,stdout_sha256=sha(stdout),stderr_sha256=sha(stderr)))
        need(result.returncode==0,'Native no-forward tokenizer failed: '+role)
        with stdout.open() as stream:
            vocab=json.loads(stream.readline());rows=[json.loads(line) for line in stream if line.strip()]
        need(digest(vocab)==history['vocabulary_sha256'] and vocab['forward_calls']==0 and vocab['context_creations']==0,'Exact full native vocabulary/flags/EOG and zero-forward contract')
        need(len(rows)==len(admitted) and len({x['task_id'] for x in rows})==len(rows),'Every submitted native tokenizer query')
        native[role]={x['task_id']:x for x in rows}
    tokens=[];seen_tokens=set();capacity=policy['n_ctx']-policy['cap']-policy['transient_token_headroom']
    for x in sorted(admitted,key=lambda x:(x['rank'],x['id'])):
        target=native['target'][x['id']];draft=native['draft'][x['id']]
        need(target['prompt_ids']==draft['prompt_ids'] and target['native_detokenized_prompt']==draft['native_detokenized_prompt']==x['formatted_prompt'],'Exact native pair roundtrip')
        need(not target['add_special'] and not draft['add_special'] and target['forward_calls']==draft['forward_calls']==0,'No implicit special tokens or model forwards')
        ids=target['prompt_ids'];need(ids and ids[0]==128000 and ids.count(128000)==1,'Exactly one native BOS')
        token_sha=digest(ids);reasons=[]
        if token_sha in exclusions:reasons.append('historical_native_prompt_hash')
        if not 0<len(ids)<=capacity:reasons.append('C1024_cap_and_transient_capacity')
        if token_sha in seen_tokens:reasons.append('duplicate_pool_native_prompt')
        seen_tokens.add(token_sha)
        tokens.append(dict(x,prompt_ids=ids,prompt_tokens=len(ids),prompt_ids_sha256=token_sha,admission_rejections=reasons))
    save(out/'TOKENIZED_POOL.json',dict(inputs=tokens,native_pair_equal=True,model_forwards=0,context_creations=0,helper_costs=costs,
        vocabulary_stdout_scope='Private full native vocabulary; digest and selected token IDs retained publicly, no full-vocabulary redistribution'))
    selected=[]
    for domain,count in policy['roots_per_domain'].items():
        choices=[x for x in tokens if x['domain']==domain and not x['admission_rejections']]
        need(len(choices)>=count,'Insufficient eligible '+domain+' statements; retain preparation epoch')
        selected+=choices[:count]
    need(len(selected)==12 and len({x['id'] for x in selected})==12,'Exactly12 unique selected roots')
    inputs=[]
    for x in selected:
        inputs.append(dict(id=x['id'],family=d.FAMILY,prompt_ids=x['prompt_ids'],prompt_tokens=x['prompt_tokens'],prompt_ids_sha256=x['prompt_ids_sha256'],
            cap=policy['cap'],domain=x['domain'],source_index=x['source_index'],dataset_snapshot=x['dataset_snapshot'],selection_hash=x['rank'],
            source_entry_sha256=digest({k:x[k] for k in ('id','description','dataset_snapshot','source_dataset','source_config','source_split','source_index')}),role='prospective_project_history_unseen'))
    primers=read(w/'inputs-01/Llama-DEVELOPMENT.json')['inputs'];primers=[primers[-1],primers[0]]
    need(not {x['id'] for x in inputs}&{x['id'] for x in primers} and len({x['id'] for x in inputs+primers})==14,'Distinct known primers and new formal roots')
    save(out/'COHORT.json',dict(inputs=inputs,statements=selected,training_unseen_claim=False,scope=policy['source_scope']))
    save(out/'PRIMERS.json',dict(inputs=primers,scope='Two historical exposed primers, not formal roots'))
    structures=read(w/'MODEL_STRUCTURES.json');study=read(a.integration/'study.json')
    need(study['seed']==policy['seed'],'Original F study seed')
    plan=d.shared.schedule(study,'transfer',[dict(root=x['id']) for x in inputs]);arms=list(d.ARMS)
    rows=[[arms[(i+s)%6] for i in (0,1,5,2,4,3)] for s in range(4)]
    old={x['worker_id']:x for x in plan['workers']};plan['workers']=[old[f'{study["id"]}-transfer-s{s}-{arm}'] for s,row in enumerate(rows) for arm in row]
    plan.update(order_design='Four Williams6 rows: four distinct positions/arm,20of30 unique directed within-session edges; not complete six-row balance',worker_order_rows=rows)
    dest=w/'panel-01';lookup={x['id']:x for x in inputs+primers}
    for worker in plan['workers']:
        core,cut,draft=d.ARMS[worker['arm']];keys=[x['id'] for x in primers]+worker['roots']
        worker.update(id=worker['worker_id'],core=core,primers=keys[:2],job=worker['worker_id']+'.json')
        job=dict(models,residency='matched' if draft else 'target_only',draft=draft,draft_width=4 if draft else 1,lowering=cut,profile=False,
            capability_request=d.capability(models,structures,core,cut,draft),inputs=[dict(name=f'request-{i:02d}',input=lookup[key],capture=False) for i,key in enumerate(keys)])
        if not draft:job.pop('draft_model');job.pop('draft_sha256')
        save(dest/worker['job'],job);worker['job_sha256']=sha(dest/worker['job'])
    reference={k:v for k,v in models.items() if not k.startswith('draft')}
    reference.update(residency='target_only',draft=False,capability_request=d.capability(models,structures,'reference','WHOLE_UB1'),
        inputs=[dict(name=f'reference-{i}',input=x,capture=False) for i,x in enumerate(primers+inputs)])
    save(dest/'REFERENCE-JOB.json',reference);save(dest/'PLAN.json',plan)
    save(dest/'PROSPECTIVE_ORDER.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(dest/'PLAN.json'),
        cohort_sha256=sha(out/'COHORT.json'),order_rows=rows,D4_relative_order_counts=dict(SIMPLE_before_LOCAL=2,LOCAL_before_SIMPLE=2),
        new_cohort_model_outputs_seen=0,new_cohort_candidate_outputs_seen=0,measurements=288,primers=48,between_session_edges_not_balanced=True))
    ledger=[json.loads(x) for x in (w/'ledger.jsonl').read_text().splitlines()];reserved=[x for x in ledger if x.get('event')=='RESERVE']
    need(not any(x.get('phase')=='confirmation' for x in reserved),'No prior attempted formal slots')
    future=[d.host.reservation(read(dest/x['job'])) for x in plan['workers']]+[d.host.reservation(reference)]
    requests=sum(x['requests'] for x in reserved)+sum(x[0] for x in future);rows_reserved=sum(x['rows'] for x in reserved)+sum(x[1] for x in future)
    need(requests<=policy['request_ceiling'] and rows_reserved<=policy['row_ceiling'],'Prospective complete study envelope')
    save(out/'PROSPECTIVE_COHORT_CHECKED.json',dict(status='PREPARED_ZERO_FORWARD_FORMAL_NOT_RUN',passed=True,model_forwards=0,context_creations=0,
        roots=12,measurements=288,primers=48,plan_sha256=sha(dest/'PLAN.json'),reference_job_sha256=sha(dest/'REFERENCE-JOB.json'),
        exposure_review_sha256=sha(out/'EXPOSURE_REVIEW.json'),exclusion_compressed_sha256=policy['materials']['EXCLUSION_UNIVERSE.sha256.txt.gz'],
        qualification_sha256=sha(q/'NATIVE_CHECKS_COMPLETE.json'),reference_freeze_sha256=sha(rf),policy_sha256=sha(out/'POLICY.json'),
        helper_costs=costs,preparation_inclusive_wall_s=time.monotonic()-started,charged_plus_future_requests=requests,charged_plus_future_reserved_rows=rows_reserved,
        no_numeric_rules_or_executables_changed=True,formal_performance='NOT_RUN',training_unseen_claim=False))
    print('F_PROSPECTIVE_NATIVE_COHORT_FROZEN_NO_FORWARD',flush=True)

if __name__=='__main__':main()
