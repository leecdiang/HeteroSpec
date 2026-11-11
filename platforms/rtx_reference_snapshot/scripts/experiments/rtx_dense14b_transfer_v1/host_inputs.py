"""Host-only prospective input recovery; never executes a model."""
import sys, json, hashlib, urllib.request, subprocess, re
from pathlib import Path
ROOT=Path('D:/rtx155/preparation')
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def fetch():
    ROOT.mkdir(parents=True,exist_ok=True)
    for name,rev in [('codeparrot/apps','21e74ddf8de1a21436da12e3e653065c5213e9d1'),('EleutherAI/hendrycks_math','21a5633873b6a120296cce3e2df9d5550074f4a3')]:
        meta=json.load(urllib.request.urlopen('https://huggingface.co/api/datasets/'+name+'/revision/'+rev))
        save(ROOT/(name.split('/')[-1]+'_source.json'),meta)
        if name=='codeparrot/apps':
            p=ROOT/'apps-first1000.jsonl'
            if not p.exists():
                with urllib.request.urlopen('https://huggingface.co/datasets/'+name+'/resolve/'+rev+'/test.jsonl',timeout=120) as response, p.open('xb') as out:
                    for i,line in enumerate(response):
                        if i==1000:break
                        out.write(line)
            print(p,flush=True)
        else:
            for item in meta['siblings']:
                n=item['rfilename']
                if not n.endswith('.parquet') or '/test-' not in n:continue
                p=ROOT/'math'/n
                if not p.exists():
                    p.parent.mkdir(parents=True,exist_ok=True)
                    with urllib.request.urlopen('https://huggingface.co/datasets/'+name+'/resolve/'+rev+'/'+n,timeout=120) as r:p.write_bytes(r.read())
                print(p,flush=True)
def tokenize():
    sys.path.insert(0,'D:/rtx155/pydeps')
    from tokenizers import Tokenizer
    from jinja2 import Environment
    import pyarrow.parquet as pq
    from common import prompt_hash
    tokpath=Path('D:/HeteroSpec-PC/models/qwen3-14b/tokenizer.json')
    tok=Tokenizer.from_file(str(tokpath))
    contract=json.loads(Path('D:/hs144-e5c03228-9eb9-4198-8f14-a7d279d08afa/MODEL_CONTRACT.json').read_bytes())['families']['Qwen']
    template=contract['template'];assert sha(template.encode())==contract['template_sha256']
    tmpl=Environment().from_string(template)
    def render(text):return tmpl.render(messages=[{'role':'user','content':text}],add_generation_prompt=True,enable_thinking=False)
    old=json.loads(Path('D:/hs-qb-confirmation-v02/PLAN.json').read_bytes())['panel']['Qwen']
    # Four already-exposed inputs, two per domain in historical order; no 14B outputs.
    pil=[]
    receipt={'tokenizer_sha256':sha(tokpath.read_bytes()),'template_sha256':sha(template.encode()),'enable_thinking':False,'add_special_tokens':True,'tokenizer_version':__import__('tokenizers').__version__,'command':'host_inputs.py tokenize','historical_roundtrip_checks':[]}
    for x in old:
        text=render(x['raw_prompt']);ids=tok.encode(text,add_special_tokens=True).ids
        assert text==x['formatted_prompt'] and ids==x['prompt_ids'],x['id']
        receipt['historical_roundtrip_checks'].append(x['id'])
    save(ROOT/'TOKENIZATION.json',receipt);rh=sha((ROOT/'TOKENIZATION.json').read_bytes())
    chosen=[x for x in old if x['domain']=='MBPP'][:2]+[x for x in old if x['domain']!='MBPP'][:2]
    for x in chosen:
        pil.append(dict(x,domain='code' if x['domain']=='MBPP' else 'math',source_revision='PR144/'+sha(Path('D:/hs-qb-confirmation-v02/PLAN.json').read_bytes()),text_sha256=sha(x['description'].strip().encode()),prompt_ids_sha256=prompt_hash(x['prompt_ids']),tokenization_receipt_sha256=rh))
    save(ROOT/'calibration.json',{'inputs':pil})
    rows=[]
    with (ROOT/'apps-first1000.jsonl').open(encoding='utf-8') as f:
        for i,line in enumerate(f):
            x=json.loads(line);rows.append(('code','APPS/test/'+str(x.get('problem_id',i)),x['question'],'21e74ddf8de1a21436da12e3e653065c5213e9d1'))
    for p in sorted((ROOT/'math').rglob('*.parquet')):
        for i,x in enumerate(pq.read_table(p).to_pylist()):rows.append(('math','MATH/'+p.parent.name+'/test/'+str(i),x['problem'],'21a5633873b6a120296cce3e2df9d5550074f4a3'))
    candidates=[];counts={}
    for domain,ident,text,rev in rows:
        prefix=('Complete the following Python programming task. Return only the completed Python code, without Markdown fences.' if domain=='code' else 'Solve the following mathematics problem. Give your reasoning and final answer.')
        raw=prefix+'\n\n'+text;rendered=render(raw);ids=tok.encode(rendered,add_special_tokens=True).ids
        n=len(ids);band='short' if 128<=n<=384 else 'long' if 512<=n<=768 else None
        if band is None:continue
        counts[domain+'/'+band]=counts.get(domain+'/'+band,0)+1
        candidates.append(dict(id=ident,domain=domain,stratum=band,source_revision=rev,description=text,raw_prompt=raw,formatted_prompt=rendered,prompt_ids=ids,prompt_ids_sha256=prompt_hash(ids),text_sha256=sha(text.strip().encode()),tokenization_receipt_sha256=rh,cap=128))
    save(ROOT/'candidates.json',{'inputs':candidates});save(ROOT/'ELIGIBLE_COUNTS.json',counts);print(counts)

def exposure(repo):
    from common import prompt_hash
    ids=set();texts=set();tokens=set();inventory=[];errors=[]
    def walk(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in ('id','input_id','task_id') and isinstance(v,str):ids.add(v)
                if k in ('description','question','problem','raw_prompt','prompt','formatted_prompt','text') and isinstance(v,str):texts.add(sha(v.strip().encode()))
                if k in ('text_sha256','prompt_text_sha256') and isinstance(v,str):texts.add(v)
                if k in ('prompt_ids_sha256','input_ids_sha256') and isinstance(v,str):tokens.add(v)
                if k in ('prompt_ids','input_ids','token_ids') and isinstance(v,list) and v and all(type(n)is int for n in v):tokens.add(prompt_hash(v))
                walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    def ingest(b,label):
        try:
            if label.endswith('.jsonl'):
                for line in b.splitlines():
                    if line.strip():walk(json.loads(line))
            else:walk(json.loads(b))
            inventory.append({'source':label,'bytes':len(b),'sha256':sha(b)})
        except Exception as e:errors.append({'source':label,'error':str(e)})
    refs=subprocess.check_output(['git','for-each-ref','--format=%(objectname)','refs/heads','refs/remotes','refs/tags'],cwd=repo,text=True).splitlines()
    objects={}
    pattern=re.compile(r'(input|panel|exposure|calibration|plan|contract|manifest)',re.I)
    for ref in sorted(set(refs)):
        for line in subprocess.check_output(['git','ls-tree','-r',ref],cwd=repo,text=True).splitlines():
            meta,path=line.split('\t',1)
            if path.endswith(('.json','.jsonl')) and pattern.search(Path(path).name) and not re.search(r'RAW_FILE|SOURCE_FILE|ARTIFACT_MANIFEST|FILE_MANIFEST',Path(path).name,re.I):objects.setdefault(meta.split()[2],ref+':'+path)
    save(ROOT/'EXPOSURE_GIT_INVENTORY.json',{'refs':sorted(set(refs)),'objects':objects})
    for i,(oid,label) in enumerate(objects.items()):
        ingest(subprocess.check_output(['git','cat-file','blob',oid],cwd=repo),label)
        if i%100==0:print('git exposure',i,len(objects),flush=True)
    roots=[p for p in Path('D:/').iterdir() if p.is_dir() and p.name.lower().startswith(('hs','heterospec','rtx151'))]+[Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/repo/work'),Path('C:/Users/ASUS/Documents/Codex/2026-10-10/kan/work')]
    files=subprocess.check_output(['rg','--files','--hidden','--no-ignore',*[str(p) for p in roots],'-g','*.json','-g','*.jsonl'],text=True,encoding='utf-8',stderr=subprocess.DEVNULL).splitlines()
    for name in files:
        p=Path(name)
        if 'rtx155' in name or not pattern.search(p.name):continue
        if any(x in name for x in ('.venv','site-packages','node_modules','/models/','\\models\\')):continue
        if re.search(r'RAW_FILE|SOURCE_FILE|ARTIFACT_MANIFEST|FILE_MANIFEST',p.name,re.I):continue
        if p.stat().st_size>32*1024**2:continue
        ingest(p.read_bytes(),str(p))
    ingest((ROOT/'calibration.json').read_bytes(),'calibration.json')
    result={'coverage_review_complete':not errors,'input_ids':sorted(ids),'text_sha256':sorted(texts),'prompt_ids_sha256':sorted(tokens),'inventory_sources':inventory,'errors':errors,'scope':'All available Git branch/tag head input/plan/manifest blobs, retained D drive and local work input manifests; raw file inventories and model caches excluded.'}
    save(ROOT/'exposure.json',result);print('exposure',len(ids),len(texts),len(tokens),'errors',len(errors),flush=True)

def review_exposure(repo):
    original=ROOT/'exposure.before_placeholder_review.json'
    if not original.exists():original.write_bytes((ROOT/'exposure.json').read_bytes())
    result=json.loads(original.read_bytes());resolved=[]
    for e in result['errors']:
        label=e['source']
        b=Path(label).read_bytes() if label.startswith('D:') else subprocess.check_output(['git','show',label],cwd=repo)
        fixture=('cpu_tests' in label and b.strip() in (b'CPU_FIXTURE_NO_GPU_AUTHORITY',b'CPU_FIXTURE_NOT_GPU_AUTHORIZED'))
        empty=(label.endswith('benchmarks/jsa_b570_validation_v1/remote/EXPOSURE_AUDIT.json') and b==b'\n')
        assert fixture or empty,(label,b[:100])
        resolved.append(dict(e,sha256=sha(b),bytes=len(b),content=b.decode(),resolution='Explicit non-GPU CPU fixture' if fixture else 'Empty remote placeholder; contains no inputs; other source manifests remain inventoried'))
    result.update(coverage_review_complete=True,errors=[],reviewed_placeholders=resolved)
    save(ROOT/'exposure.json',result)

if __name__=='__main__':
    if len(sys.argv)==1:fetch()
    elif sys.argv[1]=='tokenize':tokenize()
    elif sys.argv[1]=='exposure':exposure(Path.cwd())
    elif sys.argv[1]=='review-exposure':review_exposure(Path.cwd())
