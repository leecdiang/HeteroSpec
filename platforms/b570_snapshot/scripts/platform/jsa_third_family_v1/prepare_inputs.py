"""No-forward full vocabulary, target templates and prospective common panel."""
from preflight import *
from gguf import Reader
from jinja2.sandbox import SandboxedEnvironment
import jinja2

SALT='heterospec-jsa-third-family-20261011-v1'
def fail(s):raise ValueError(s)
def render(meta,raw):
    template=meta.get('tokenizer.chat_template');assert isinstance(template,str) and template.strip()
    env=SandboxedEnvironment(trim_blocks=True,lstrip_blocks=True)
    env.globals['raise_exception']=fail
    # Keep the model template's own historical date fallback; no current date injection.
    tokens=meta['tokenizer.ggml.tokens']
    return env.from_string(template).render(messages=[{'role':'user','content':raw}],add_generation_prompt=True,bos_token=tokens[meta['tokenizer.ggml.bos_token_id']],eos_token=tokens[meta['tokenizer.ggml.eos_token_id']],**({'enable_thinking':False} if meta['general.architecture']=='qwen3' else {}))

def main():
    audit=read(PUB/'EXPOSURE_AUDIT.json');assert audit['status']=='PASS'
    pool=read(LOCAL/'AVAILABLE_CANDIDATES.json')['eligible_pool']
    old=read(OLD/'benchmarks/jsa_rtx_validation_v1/F_DISCOVERY_INPUTS.json')
    assert len(old)==12 and [r['id'] for r in old[:4]]==['HumanEval/15','HumanEval/25','HumanEval/18','HumanEval/31']
    engineering=[{'id':r['id'],'raw_prompt':r['raw_prompt'],'cap':128} for r in old]
    synthetic=[{'id':'synthetic/warmup','raw_prompt':'Write Python code to add two integers.','cap':32},{'id':'synthetic/capture','raw_prompt':'Write a Python function with fifty sequential variable assignments. Return only the code.','cap':128}]
    tasks=pool+engineering+synthetic;assert len({t['id'] for t in tasks})==len(tasks)
    all_inputs={};contracts={};bad={};root=LOCAL/'static-native/full';root.mkdir(parents=True,exist_ok=False)
    for family,pair in models().items():
        metadata={};vocab={};native={}
        for role,m in pair.items():
            assert sha(m['path'])==m['sha256'] and Path(m['path']).stat().st_size==m['bytes']
            metadata[role],tensors=Reader(m['path']).metadata()
            save(root/f'{family}-{role}-GGUF_METADATA.json',{'metadata':metadata[role],'tensors':tensors,'vocab_only':True,'forward_calls':0})
        target=metadata['target'];texts={t['id']:render(target,t['raw_prompt']) for t in tasks}
        bos=target['tokenizer.ggml.tokens'][target['tokenizer.ggml.bos_token_id']]
        precheck_cmd=[str(LOCAL/'native/vocabulary.exe'),'D:/HeteroSpec-PC/tools/llama-b10839',pair['target']['path']]
        precheck=subprocess.run(precheck_cmd,input=b'',capture_output=True,timeout=120,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        (root/f'{family}-vocabulary-precheck.stdout.jsonl').write_bytes(precheck.stdout)
        (root/f'{family}-vocabulary-precheck.stderr.log').write_bytes(precheck.stderr)
        assert precheck.returncode==0
        actual_flags=json.loads(precheck.stdout.splitlines()[0]);assert actual_flags['forward_calls']==0 and actual_flags['context_creations']==0
        # An explicit template BOS is already a token. Do not add a second BOS.
        add_special=not (actual_flags['add_bos'] and all(text.startswith(bos) for text in texts.values()))
        queries=[{'task_id':t['id'],'formatted_prompt':texts[t['id']],'add_special':add_special} for t in tasks]
        payload=''.join(json.dumps(q,ensure_ascii=False)+'\n' for q in queries).encode()
        save(root/f'{family}-STATIC_QUERIES.json',{'eligible_pool':queries[:len(pool)],'engineering':queries[len(pool):],'vocab_only':True,'forward_calls':0})
        for role,m in pair.items():
            cmd=[str(LOCAL/'native/vocabulary.exe'),'D:/HeteroSpec-PC/tools/llama-b10839',m['path']]
            p=subprocess.run(cmd,input=payload,capture_output=True,timeout=240,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            (root/f'{family}-{role}-vocabulary.stdout.jsonl').write_bytes(p.stdout)
            (root/f'{family}-{role}-vocabulary.stderr.log').write_bytes(p.stderr)
            assert p.returncode==0,(family,role,'native vocabulary helper failed',p.returncode)
            rows=[json.loads(line) for line in p.stdout.splitlines()];vocab[role]=rows[0];native[role]={r['task_id']:r for r in rows[1:]}
            v=vocab[role];g=metadata[role]
            assert v['vocab_only'] and v['forward_calls']==0 and v['context_creations']==0
            assert [t['text'] for t in v['tokens']]==g['tokenizer.ggml.tokens']
            assert all(t['id']==i for i,t in enumerate(v['tokens']))
            assert v['bos']==g['tokenizer.ggml.bos_token_id'] and v['eos']==g['tokenizer.ggml.eos_token_id']
            for name in ['bos','eos']:
                if 'tokenizer.ggml.add_'+name+'_token' in g:assert v['add_'+name]==g['tokenizer.ggml.add_'+name+'_token']
        assert vocab['target']==vocab['draft'],'runtime native vocab/EOG/flags mismatch'
        keys=['model','pre','tokens','token_type','merges','bos_token_id','eos_token_id','add_bos_token','add_eos_token']
        assert all(metadata['target'].get('tokenizer.ggml.'+k)==metadata['draft'].get('tokenizer.ggml.'+k) for k in keys)
        assert set(native['target'])==set(native['draft'])==set(texts)
        records=[]
        for t in tasks:
            n=native['target'][t['id']];other=native['draft'][t['id']]
            reasons=[]
            if n['prompt_ids']!=other['prompt_ids']:reasons.append('pair_prompt_ID_mismatch')
            if not texts[t['id']].strip() or not n['prompt_ids']:reasons.append('empty_formatted_input')
            if max(len(n['prompt_ids']),len(other['prompt_ids']))>768:reasons.append('prompt_ID_count_exceeds_768')
            if n['native_detokenized_prompt']!=texts[t['id']]:reasons.append('native_rendered_byte_roundtrip_mismatch')
            if reasons:bad.setdefault(t['id'],{})[family]=reasons
            records.append({**t,'formatted_prompt':texts[t['id']],'formatted_prompt_sha256':hashlib.sha256(texts[t['id']].encode()).hexdigest(),'raw_prompt_sha256':hashlib.sha256(t['raw_prompt'].encode()).hexdigest(),'prompt_ids':n['prompt_ids'],'prompt_token_count':len(n['prompt_ids']),'prompt_ids_sha256':digest(n['prompt_ids']),'add_special':add_special,'native_detokenized_prompt':n['native_detokenized_prompt'],'static_exclusions':reasons})
        all_inputs[family]={r['id']:r for r in records}
        contracts[family]={'models':pair,'vocabulary_sha256':digest(vocab['target']),'native_all_tokens_equal':True,'vocabulary_tokens':len(vocab['target']['tokens']),'eog':vocab['target']['eog'],'bos':vocab['target']['bos'],'eos':vocab['target']['eos'],'add_bos':vocab['target']['add_bos'],'add_eos':vocab['target']['add_eos'],'suppress':vocab['target']['suppress'],'template':target['tokenizer.chat_template'],'template_sha256':hashlib.sha256(target['tokenizer.chat_template'].encode()).hexdigest(),'draft_template_sha256':hashlib.sha256(metadata['draft']['tokenizer.chat_template'].encode()).hexdigest(),'pair_target_render_once':True,'target_and_draft_IDs_equal':all(native['target'][k]['prompt_ids']==native['draft'][k]['prompt_ids'] for k in texts),'added_special_for_template':add_special,'conversion_lineage':'published conversion bytes/revision bound; original official checkpoint lineage unverified','tokenizer_metadata':{role:{k:digest(v) for k,v in g.items() if k.startswith('tokenizer.')} for role,g in metadata.items()},'architecture_shapes':{role:{k:v for k,v in g.items() if any(k.endswith(s) for s in ['block_count','embedding_length','head_count','head_count_kv','key_length','value_length'])} for role,g in metadata.items()}}
        print('STATIC NATIVE',family,'vocab',contracts[family]['vocabulary_tokens'],'pair IDs checked',len(tasks),flush=True)
    eligible=[t for t in pool if t['id'] not in bad]
    selected=[]
    for domain in ['MBPP','GSM8K']:
        domain_pool=sorted((t for t in eligible if t['domain']==domain),key=lambda t:(t['selection_hash'],t['id']))
        assert len(domain_pool)>=12,'INPUT_POOL_BLOCKED'
        selected+=domain_pool[:12]
    assert not any(t['id'] in bad for t in engineering+synthetic),'old engineering/synthetic input violates static gate'
    save(PUB/'CONFIRMATION_INPUTS.json',{'study_id':'JSA_THIRD_FAMILY_V1','tasks':selected,'families':{f:[all_inputs[f][t['id']] for t in selected] for f in all_inputs},'forwards':0})
    save(PUB/'ENGINEERING_INPUTS.json',{'families':{f:[all_inputs[f][t['id']] for t in engineering] for f in all_inputs},'warmups':{f:all_inputs[f]['synthetic/warmup'] for f in all_inputs},'capture_probes':{f:[all_inputs[f][engineering[0]['id']],all_inputs[f]['synthetic/capture']] for f in all_inputs},'forwards':0,'original_source_sha256':sha(OLD/'benchmarks/jsa_rtx_validation_v1/F_DISCOVERY_INPUTS.json')})
    save(PUB/'MODEL_CONTRACT.json',{'families':contracts,'helper_sha256':sha(LOCAL/'native/vocabulary.exe'),'jinja2_version':jinja2.__version__,'native_runtime_DLL_sha256':sha('D:/HeteroSpec-PC/tools/llama-b10839/llama.dll'),'forwards':0})
    save(PUB/'STATIC_INPUT_SELECTION.json',{'status':'PASS','exposure_audit_sha256':sha(PUB/'EXPOSURE_AUDIT.json'),'selection_salt':SALT,'eligible_pool':[{'id':t['id'],'domain':t['domain'],'selection_hash':t['selection_hash'],'prompt_counts':{f:all_inputs[f][t['id']]['prompt_token_count'] for f in all_inputs},'exclusions':bad.get(t['id'],{})} for t in pool],'selected':[t['id'] for t in selected],'forwards':0,'static_native_files':{p.name:sha(p) for p in root.iterdir()},'unobservable_history':'other private hosts and pretraining corpora unavailable; held-out only within audited project evidence'})
    print('PANEL STATIC PASS',[t['id'] for t in selected],flush=True)
if __name__=='__main__':main()
