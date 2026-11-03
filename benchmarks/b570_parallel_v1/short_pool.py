"""Supplement one unfilled code stratum with intact, pinned validation tasks."""
from natural import *
def prepare():
    sys.path.insert(0,str(L/'pool-pydeps'))
    import pyarrow.parquet as pq
    seen=exposure();tasks=[]
    rev='802411c3010cb00d1b05bad57ca77365a3c699d6'
    root=f'https://huggingface.co/datasets/deepmind/code_contests/resolve/{rev}/data/'
    url=root+'valid-00000-of-00001-5e672c5751f060d3.parquet'
    def load(name,url):
        f=POOL/name
        if not f.exists():f.write_bytes(urlopen(url,timeout=120).read())
        return f
    for i,x in enumerate(pq.read_table(load('code-contests-valid.parquet',url),columns=['description']).to_pylist()):
        tasks.append((f'CodeContests/valid/{i}',x['description'],rev,url))
    rev='4bb6404fdc6cacfda99d4ac4205087b89d32030c'
    url=f'https://huggingface.co/datasets/google-research-datasets/mbpp/resolve/{rev}/full/validation-00000-of-00001.parquet'
    for x in pq.read_table(load('mbpp-validation.parquet',url),columns=['task_id','text','test_list']).to_pylist():
        ident=f'MBPP/{x["task_id"]}'
        # MBPP's original assertion examples are part of the task specification.
        if ident in seen or digest(x['text']) in seen:continue
        tasks.append((ident,x['text']+'\n\n'+'\n'.join(x['test_list']),rev,url))
    rows=[]
    for ident,txt,rev,url in tasks:
        raw=PREFIX['code']+txt;fmt='<|im_start|>user\n'+raw+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
        if any(z in seen for z in (ident,digest(txt),digest(raw),digest(fmt))):continue
        rows.append(dict(id=ident,description=txt,formatted_prompt=fmt,text_sha256=digest(txt),domain='code',source_url=url,source_revision=rev))
    inp=POOL/'short-input.jsonl';out=POOL/'short-tokens.jsonl'
    inp.write_text(''.join(json.dumps({k:r[k] for k in ('id','formatted_prompt')})+'\n' for r in rows),encoding='utf-8')
    command([L/'tokenizer-build-00/build/Release/operator_replay.exe',MODELS['qwen'][0],inp,out],POOL/'short-tokenize.log')
    tokens={v['id']:v['prompt_ids'] for v in map(json.loads,out.read_text(encoding='utf-8').splitlines())}
    kept=read(POOL/'eligible-v2.json')
    for r in rows:
        ids=tokens[r['id']];n=len(ids)
        if 80<=n<=255 and hashval(ids) not in seen:kept.append(dict(r,tokens=n,band='short',prompt_ids=ids,prompt_ids_sha256=hashval(ids)))
    write(POOL/'eligible-v3.json',kept)
    print(collections.Counter((r['domain'],r['band']) for r in kept))
if __name__=='__main__':prepare()
