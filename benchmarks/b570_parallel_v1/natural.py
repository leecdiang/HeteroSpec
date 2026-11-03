"""Zero-forward preparation, post-freeze blind selection and paired natural service."""
from host import *
import collections
import gzip
from datetime import datetime,timezone
from urllib.request import urlopen
L=Path('I:/HeteroSpec/b570-llama-20261102')
POOL=ROOT/'pool'
PREFIX={'math':'Solve the following math problem. Give a concise solution and the final answer.\n\n','code':'Complete the following Python programming task. Return only the completed Python code, without Markdown fences.\n\n'}
def digest(s):return hashlib.sha256(s.strip().encode()).hexdigest()
def exposure():
    old=L/'EXPOSURE_AUDIT-00.json'
    assert sha(old)==read(str(L/'UNSEEN_PANEL-00.json')+'.selection.json')['exposure_sha256']
    seen=set(read(old)['keys'])
    def absorb(r):
        for k in ('id','prompt_ids_sha256','text_sha256'):
            if k in r:seen.add(r[k])
        for k in ('text','description','formatted_prompt','raw_prompt'):
            if k in r:seen.add(digest(r[k]))
        if 'prompt_ids' in r:seen.add(hashval(r['prompt_ids']))
    for s in (L/'research/EXPOSURE.jsonl').read_text(encoding='utf-8').splitlines():absorb(json.loads(s))
    for r in read(L/'UNSEEN_PANEL-00.json'):absorb(r)
    for panel in (DATA,PR165/'UNSEEN.json'):
        for i,r in read(panel).items():absorb(dict(r,id=i))
    # The four source tasks used to build the independent geometry's teacher sequence.
    for r in sorted(read(PR165/'pool-00/POOL.json')['rows'],key=lambda v:hashval(['smol-heldout',v['id']]))[:4]:absorb(r)
    for family in ('qwen8b02','qwen14b02'):
        for f in (f'development/{family}_PANEL.json',f'evidence/{family}/PANEL.json'):
            src='benchmarks/reference_batching_transfer_20261103/rtx_execution/'+f
            name=POOL/(f.replace('/','_'))
            if not name.is_file():
                b=subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','show','abd36bea639bf814159ad68ab015bc983c5338b1:'+src],cwd=HERE)
                name.write_bytes(b)
            p=read(name)
            for r in p['inputs'] if isinstance(p,dict) else p:absorb(r)
    latest=POOL/'rtx-parallel-panel.json'
    if not latest.exists():
        latest.write_bytes(subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','show','9c79594f679ea4aad1956d8a385fdf6a7352d892:benchmarks/tpds_parallel/evidence/panel.json'],cwd=HERE))
    for r in read(latest):absorb(r)
    return seen
def supplement():
    seen=exposure()
    rev='b9453e8f1865df0a0057a1383767caa400acfbcf'
    url=f'https://raw.githubusercontent.com/openai/human-eval/{rev}/data/HumanEval.jsonl.gz'
    source=POOL/'HumanEval.jsonl.gz'
    if not source.is_file():source.write_bytes(urlopen(url,timeout=60).read())
    tasks=[json.loads(s) for s in gzip.decompress(source.read_bytes()).decode().splitlines()]
    assert len(tasks)==164
    rows=[]
    for task in tasks:
        ident=task['task_id'];txt=task['prompt'];raw=PREFIX['code']+txt
        fmt='<|im_start|>user\n'+raw+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
        if any(z in seen for z in (ident,digest(txt),digest(raw),digest(fmt))):continue
        rows.append(dict(id=ident,description=txt,formatted_prompt=fmt,text_sha256=digest(txt),domain='code',source_url=url,source_revision=rev))
    inp=POOL/'human-input.jsonl';out=POOL/'human-tokens.jsonl'
    if not out.is_file():
        inp.write_text(''.join(json.dumps({k:r[k] for k in ('id','formatted_prompt')})+'\n' for r in rows),encoding='utf-8')
        command([L/'tokenizer-build-00/build/Release/operator_replay.exe',MODELS['qwen'][0],inp,out],POOL/'human-tokenize.log')
    tokens={v['id']:v['prompt_ids'] for v in map(json.loads,out.read_text(encoding='utf-8').splitlines())}
    kept=[r for r in read(POOL/'eligible.json') if not any(z in seen for z in (r['id'],r['text_sha256'],r['prompt_ids_sha256']))]
    for r in rows:
        ids=tokens[r['id']];n=len(ids)
        if 80<=n<=255 and hashval(ids) not in seen:kept.append(dict(r,tokens=n,band='short',prompt_ids=ids,prompt_ids_sha256=hashval(ids)))
    write(POOL/'eligible-v2.json',kept)
    print(collections.Counter((r['domain'],r['band']) for r in kept))
def prepare():
    POOL.mkdir(exist_ok=True);seen=exposure();sys.path.insert(0,str(L/'pool-pydeps'))
    import pyarrow.parquet as pq
    records=[]
    for f in read(L/'natural-source-00/SOURCES.json')['files']:
        assert sha(f['path'])==f['sha256']
        code=f['repo']=='deepmind/code_contests';domain='code' if code else 'math'
        col='description' if code else 'problem'
        for i,v in enumerate(pq.read_table(f['path'],columns=[col]).to_pylist()):
            text=v[col];ident=f'CodeContests/test/{i}' if code else f'MATH/{Path(f["repo_path"]).parent.name}/train/{i}'
            raw=PREFIX[domain]+text;fmt='<|im_start|>user\n'+raw+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
            if any(z in seen for z in (ident,digest(text),digest(raw),digest(fmt))):continue
            records.append(dict(id=ident,domain=domain,description=text,formatted_prompt=fmt,text_sha256=digest(text),source_url=f['url'],source_revision=f['revision']))
    controls=[dict(d,id=i) for i,d in read(DATA).items() if i in ('MATH500/test/prealgebra/1865.json','MATH500/test/prealgebra/1804.json','GSM8K/train/1184')]
    inp=POOL/'input.jsonl';out=POOL/'tokens.jsonl'
    if not out.is_file():
        with inp.open('w',encoding='utf-8') as f:
            for r in controls+records:f.write(json.dumps({k:r[k] for k in ('id','formatted_prompt')},ensure_ascii=False)+'\n')
        command([L/'tokenizer-build-00/build/Release/operator_replay.exe',MODELS['qwen'][0],inp,out],POOL/'tokenize.log')
    tokens={v['id']:v['prompt_ids'] for v in map(json.loads,out.read_text(encoding='utf-8').splitlines())}
    assert len(controls)==3 and all(tokens[r['id']]==r['prompt_ids'] for r in controls)
    kept=[]
    for r in records:
        ids=tokens[r['id']];n=len(ids)
        if n<80 or n>800 or hashval(ids) in seen:continue
        kept.append(dict(r,prompt_ids=ids,prompt_ids_sha256=hashval(ids),tokens=n,band='short' if n<=255 else 'medium' if n<=511 else 'long'))
    write(POOL/'eligible.json',kept);print(collections.Counter((r['domain'],r['band']) for r in kept))
def select():
    assert (ROOT/'FREEZE.json').is_file()
    rows=read(POOL/'eligible-v3.json');panel=[];used=set()
    for domain in ('code','math'):
        for band in ('short','medium','long'):
            picked=[]
            for r in sorted((x for x in rows if (x['domain'],x['band'])==(domain,band)),key=lambda x:hashval(['b570-independent-parallel-v1',x['id']])):
                keys=(r['id'],r['text_sha256'],r['prompt_ids_sha256'])
                if used.intersection(keys):continue
                used.update(keys);picked.append(r)
                if len(picked)==2:break
            assert len(picked)==2;panel.extend(picked)
    evidence=[L/'EXPOSURE_AUDIT-00.json',L/'research/EXPOSURE.jsonl',L/'UNSEEN_PANEL-00.json',DATA,PR165/'UNSEEN.json',
              POOL/'rtx-parallel-panel.json',*sorted(POOL.glob('*_PANEL.json'))]
    write(ROOT/'NATURAL_PANEL.json',dict(selected_utc=datetime.now(timezone.utc).isoformat(),freeze=sha(ROOT/'FREEZE.json'),pool=sha(POOL/'eligible-v3.json'),exclusions=[dict(path=str(p),sha256=sha(p)) for p in evidence],rows=panel))
if __name__=='__main__':{'pool':prepare,'supplement':supplement,'select':select}[sys.argv[1]]()
