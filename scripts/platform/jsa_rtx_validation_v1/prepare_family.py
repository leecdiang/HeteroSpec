"""Resolve model choice and complete zero-forward input/vocabulary contracts."""
from common import *
from gguf import Reader
TEMPLATE="{% for message in messages %}{% if loop.first and messages[0]['role'] != 'system' %}{{ '<|im_start|>system\nYou are a helpful AI assistant named SmolLM, trained by Hugging Face<|im_end|>\n' }}{% endif %}{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n'}}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}"
def format_smol(text):return '<|im_start|>system\nYou are a helpful AI assistant named SmolLM, trained by Hugging Face<|im_end|>\n<|im_start|>user\n'+text+'<|im_end|>\n<|im_start|>assistant\n'
def main():
    assert read(PUB/'EXPOSURE_AUDIT.json')['status']=='PASS'
    cfg=read(LOCAL/'CONFIG.json');models={r:read(LOCAL/'models'/f'{r}_DOWNLOAD.json') for r in ['target','draft']};meta={};vocabs={};input_records={}
    official={r:read(LOCAL/'models'/f'{r}-tokenizer.json') for r in models}
    assert all(official['target'][k]==official['draft'][k] for k in ['model','added_tokens','normalizer','pre_tokenizer','post_processor','decoder'])
    discovery=read(PUB/'BRIDGE_INPUTS.json')+read(PUB/'S_INPUTS.json')[:8];confirmation=read(PUB/'CONFIRMATION_INPUTS.json')
    tasks=[{**{k:v for k,v in t.items() if k not in ['prompt_ids','prompt_token_count','formatted_prompt','formatted_prompt_sha256']},'formatted_prompt':format_smol(t['raw_prompt'])} for t in discovery+confirmation]
    warm={'id':'synthetic/warmup','raw_prompt':'Write Python code to add two integers.','formatted_prompt':format_smol('Write Python code to add two integers.'),'cap':32}
    for role,m in models.items():
        assert sha(m['path'])==m['sha256'];g,tensors=Reader(m['path']).metadata();meta[role]=g
        assert g['general.architecture']=='llama' and g['general.file_type']==7
        tc=read(LOCAL/'models'/f'{role}-tokenizer_config.json');assert tc['chat_template']==TEMPLATE
        request=''.join(json.dumps({'task_id':t['id'],'formatted_prompt':t['formatted_prompt']})+'\n' for t in tasks+[warm]).encode()
        cmd=[str(LOCAL/'native/vocabulary.exe'),str(Path(cfg['asset'])/'tools/llama-b10839'),m['path']]
        r=subprocess.run(cmd,input=request,capture_output=True,timeout=120,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        (LOCAL/'models'/f'{role}-vocabulary.stdout.jsonl').write_bytes(r.stdout);(LOCAL/'models'/f'{role}-vocabulary.stderr.log').write_bytes(r.stderr);assert r.returncode==0
        rows=[json.loads(line) for line in r.stdout.splitlines()];v=rows[0];vocabs[role]=v;input_records[role]={r['task_id']:r['prompt_ids'] for r in rows[1:]}
        assert v['vocab_only'] and v['forward_calls']==0 and v['context_creations']==0
        ordered={i:s for s,i in official[role]['model']['vocab'].items()};ordered.update({a['id']:a['content'] for a in official[role]['added_tokens']})
        assert len(ordered)==len(v['tokens'])==49152 and all(t['text']==ordered[t['id']] for t in v['tokens'])
        assert [t['text'] for t in v['tokens']]==g['tokenizer.ggml.tokens'];assert v['eos']==2 and v['bos']==1
        save(LOCAL/'models'/f'{role}-GGUF_METADATA.json',{'metadata':g,'tensors':tensors})
    assert vocabs['target']==vocabs['draft'];assert input_records['target']==input_records['draft']
    kv_bytes=sum(2*2*4096*meta[r]['llama.block_count']*meta[r]['llama.attention.head_count_kv']*(meta[r]['llama.embedding_length']//meta[r]['llama.attention.head_count']) for r in models)
    estimate=sum(m['bytes'] for m in models.values())+kv_bytes+512*1024**2+2*1024**3;assert estimate<12227*1024**2
    for t in tasks+[warm]:
        t['prompt_ids']=input_records['target'][t['id']];t['prompt_token_count']=len(t['prompt_ids']);t['formatted_prompt_sha256']=hashlib.sha256(t['formatted_prompt'].encode()).hexdigest();assert len(t['prompt_ids'])+128+32<4096
    save(PUB/'F_DISCOVERY_INPUTS.json',tasks[:12]);save(PUB/'F_CONFIRMATION_INPUTS.json',tasks[12:]);save(PUB/'F_WARMUP.json',warm)
    # Qwen confirmation uses its own frozen template and actual zero-forward tokenization.
    qwen=[]
    for t in confirmation:
        qwen.append({**t,'formatted_prompt':'<|im_start|>user\n'+t['raw_prompt']+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'})
    request=''.join(json.dumps({'task_id':t['id'],'formatted_prompt':t['formatted_prompt']})+'\n' for t in qwen).encode()
    r=subprocess.run([str(LOCAL/'native/vocabulary.exe'),str(Path(cfg['asset'])/'tools/llama-b10839'),cfg['models']['target']['path']],input=request,capture_output=True,timeout=120,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));assert r.returncode==0
    (LOCAL/'models/Qwen-vocabulary.stdout.jsonl').write_bytes(r.stdout);rows=[json.loads(line) for line in r.stdout.splitlines()];qv=rows[0];qid={a['task_id']:a['prompt_ids'] for a in rows[1:]}
    for t in qwen:t['prompt_ids']=qid[t['id']];t['prompt_token_count']=len(t['prompt_ids']);t['formatted_prompt_sha256']=hashlib.sha256(t['formatted_prompt'].encode()).hexdigest()
    save(PUB/'QWEN_CONFIRMATION_INPUTS.json',qwen)
    choice={'status':'STATIC_QUALIFIED_NO_FORWARD','selected_pair':'SmolLM2-1.7B-Instruct / SmolLM2-135M-Instruct Q8_0','choice_reason':'Llama official assets unavailable (HTTP401); no licensed local Llama GGUF located; predetermined Smol fallback','llama_access':read(LOCAL/'models/LLAMA_ACCESS.json'),'models':models,'architecture':'llama','actual_vocabulary_equal':True,'all_token_count':49152,'vocabulary_digest':digest(vocabs['target']),'full_official_token_mapping_equal':True,'official_tokenizer_components_equal':True,'eog':vocabs['target']['eog'],'bos':vocabs['target']['bos'],'eos':vocabs['target']['eos'],'add_bos':vocabs['target']['add_bos'],'add_eos':vocabs['target']['add_eos'],'suppress':vocabs['target']['suppress'],'estimated_full_offload_bytes_including_2GiB_display_and_512MiB_graphs':estimate,'Qwen_eog':qv['eog'],'official_compatibility':'full vocab and BOS/EOS flags checked as a stronger static gate; unchanged native common_speculative_are_compatible still executes during actual draft startup','graph_patch':'separate guarded Llama dense attention graph branch; no override of Qwen architecture assertion','confirmation_inputs_sha256':sha(PUB/'CONFIRMATION_INPUTS.json'),'official_metadata':{r:{n:sha(LOCAL/'models'/f'{r}-{n}') for n in ['config.json','tokenizer.json','tokenizer_config.json']} for r in models},'second_family_forwards':0,'conversion_lineage_limit':'public publisher conversion revision/hash bound; original official weight revision lineage unverified; not a newly converted official checkpoint'}
    save(PUB/'MODEL_CHOICE.json',choice);save(LOCAL/'F_MODEL_CONFIG.json',{'models':models,'eog':choice['eog'],'warm':warm['formatted_prompt'],'exe':str(LOCAL/'native/build/bin/llama-server.exe')})
    print(json.dumps({'model_choice':'SmolLM2','vocab_equal':True,'vocab_size':49152,'eog':choice['eog'],'estimated_VRAM_bytes':estimate,'confirmed_inputs':len(confirmation),'forward_calls':0}),flush=True)
if __name__=='__main__':main()
