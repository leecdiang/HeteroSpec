"""Target-template-once native tokenization, zero contexts and zero forwards."""
from run_common import *
import importlib.util
from jinja2.sandbox import SandboxedEnvironment

def metadata(path):
    spec=importlib.util.spec_from_file_location('closeout_gguf',REPO/'scripts/platform/jsa_third_family_v1/gguf.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m.Reader(path).metadata()[0]
def render(meta,raw):
    env=SandboxedEnvironment(trim_blocks=True,lstrip_blocks=True)
    def fail(s):raise ValueError(s)
    env.globals['raise_exception']=fail;t=meta['tokenizer.ggml.tokens']
    return env.from_string(meta['tokenizer.chat_template']).render(messages=[dict(role='user',content=raw)],add_generation_prompt=True,bos_token=t[meta['tokenizer.ggml.bos_token_id']],eos_token=t[meta['tokenizer.ggml.eos_token_id']],**({'enable_thinking':False} if meta['general.architecture']=='qwen3' else {}))
def tokenize(tasks,stage,reuse=False):
    root=LOCAL/'static-native'/stage;root.mkdir(parents=True,exist_ok=reuse);result={};receipt={}
    oldcontracts=read(PUB/'MODEL_CONTRACT.json')['families']
    for family,pair in models().items():
        m=metadata(pair['target']['path']);texts={t['id']:render(m,t['raw_prompt']) for t in tasks}
        contract=oldcontracts[family];add_special=contract['added_special_for_template']
        queries=[dict(task_id=t['id'],formatted_prompt=texts[t['id']],add_special=add_special) for t in tasks]
        payload=''.join(json.dumps(q,ensure_ascii=False)+'\n' for q in queries).encode();native={};vocabs={}
        query_path=root/(family+'-QUERIES.json');query_document=dict(vocab_only=True,forward_calls=0,queries=queries)
        if query_path.exists():assert reuse and read(query_path)==query_document
        else:save(query_path,query_document)
        for role,a in pair.items():
            cmd=[str(LOCAL/'native/vocabulary.exe'),'D:/HeteroSpec-PC/tools/llama-b10839',a['path']]
            output=root/f'{family}-{role}.stdout.jsonl';error=root/f'{family}-{role}.stderr.log'
            if reuse and output.exists() and error.exists():stdout=output.read_bytes()
            else:
                p=subprocess.run(cmd,input=payload,capture_output=True,timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
                output.write_bytes(p.stdout);error.write_bytes(p.stderr);assert p.returncode==0;stdout=p.stdout
            lines=stdout.splitlines();v=json.loads(lines[0]);vocabs[role]=v
            assert v['forward_calls']==0 and v['context_creations']==0
            # #84 vocabulary digest uses insertion-order JSON, retained exactly.
            old_digest=hashlib.sha256(json.dumps(v,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
            assert old_digest==contract['vocabulary_sha256']
            native[role]={r['task_id']:r for r in map(json.loads,lines[1:])}
        assert vocabs['target']==vocabs['draft']
        ft=[]
        for t in tasks:
            n=native['target'][t['id']];o=native['draft'][t['id']]
            assert n['prompt_ids']==o['prompt_ids'] and n['native_detokenized_prompt']==o['native_detokenized_prompt']
            roundtrip=n['native_detokenized_prompt']==texts[t['id']]
            if stage=='exposed':assert roundtrip
            ft.append({**t,'formatted_prompt':texts[t['id']],'formatted_prompt_sha256':hashlib.sha256(texts[t['id']].encode()).hexdigest(),'prompt_ids':n['prompt_ids'],'prompt_token_count':len(n['prompt_ids']),'native_detokenized_prompt':n['native_detokenized_prompt'],'template_roundtrip_equal':roundtrip,'add_special':add_special})
        result[family]=ft;receipt[family]=dict(vocabulary_sha256=contract['vocabulary_sha256'],full_vocabulary_equal=True,inputs=len(ft),template_sha256=hashlib.sha256(m['tokenizer.chat_template'].encode()).hexdigest(),helper_sha256=sha(LOCAL/'native/vocabulary.exe'))
        assert receipt[family]['template_sha256']==contract['template_sha256']
        receipt[family]['detokenization_display_difference_ids']=[t['id'] for t in ft if not t['template_roundtrip_equal']]
    save(root/'RECEIPT.json',dict(families=receipt,forwards=0,files={p.name:sha(p) for p in root.iterdir()}))
    return result

def exposed():
    old=read(OLDPUB/'ENGINEERING_INPUTS.json');confirm=read(OLDPUB/'CONFIRMATION_INPUTS.json');d=read(DESIGN/'DESIGN.json')
    ids=d['mechanism']['calibration_task_ids'];first=d['families'][0]
    tasks=[dict(id=t['id'],raw_prompt=t['raw_prompt'],cap=128) for t in old['families'][first]]
    tasks += [dict(id=t['id'],raw_prompt=t['raw_prompt'],cap=128) for tid in ids for t in confirm['families'][first] if t['id']==tid]
    tasks += [dict(id=t['id'],raw_prompt=t['raw_prompt'],cap=128) for t in [old['warmups'][first],old['capture_probes'][first][-1]]]
    native=tokenize(tasks,'exposed');result=dict(families={},calibration={},warmups={},boundary={},forwards=0,source_head=BASE_HEAD)
    for f,rows in native.items():
        by={t['id']:t for t in rows};engids=[t['id'] for t in old['families'][f]]
        for t in old['families'][f]+confirm['families'][f]:
            if t['id'] in by:assert t['prompt_ids']==by[t['id']]['prompt_ids']
        result['families'][f]=[by[i] for i in engids];result['calibration'][f]=[by[i] for i in ids]
        result['warmups'][f]=by['synthetic/warmup'];probe=by['synthetic/capture']
        boundary=[{**probe,'id':'synthetic/cap'+str(cap),'cap':cap} for cap in [1,2,3,4,31,128]]
        long={**probe,'id':'synthetic/long768','prompt_ids':probe['prompt_ids']+[probe['prompt_ids'][10]]*(768-len(probe['prompt_ids'])),'prompt_token_count':768,'cap':128,'construction':'synthetic native IDs padded to768; qualification-only, no dataset task'}
        boundary += [long,{**by['synthetic/warmup'],'id':'synthetic/reset'}];result['boundary'][f]=boundary
    save(PUB/'ENGINEERING_INPUTS.json',result)
    status('EXPOSED_INPUTS_NATIVE_VERIFIED',forwards=0)

if __name__=='__main__': exposed()
