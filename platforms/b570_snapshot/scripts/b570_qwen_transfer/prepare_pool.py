"""Tokenize existing pinned natural source texts; select nothing before freeze."""
import collections, hashlib, json, subprocess
from pathlib import Path
from execute import ROOT, OLD, PANEL, read, write, sha
LLAMA=Path('I:/HeteroSpec/b570-llama-20261102')
WRAPPER='<|im_start|>user\n{raw}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
PREFIX={'math':'Solve the following math problem. Give a concise solution and the final answer.\n\n','code':'Complete the following Python programming task. Return only the completed Python code, without Markdown fences.\n\n'}
def digest(value):
    return hashlib.sha256(json.dumps(value,separators=(',',':'),sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def text_hash(s):return hashlib.sha256(s.strip().encode()).hexdigest()
def prepare():
    dest=ROOT/'pool-00';dest.mkdir()
    old=read(PANEL);source=LLAMA/'natural-pool-00/POOL.json';index=LLAMA/'EXPOSURE_AUDIT-00.json'
    assert sha(index)==read(LLAMA/'UNSEEN_PANEL-00.json.selection.json')['exposure_sha256']
    seen=set(read(index)['keys'])
    for line in (LLAMA/'research/EXPOSURE.jsonl').read_text(encoding='utf-8').splitlines():
        d=json.loads(line);seen.update((d['id'],d['prompt_ids_sha256'],d.get('text_sha256')))
    previous=read(LLAMA/'UNSEEN_PANEL-00.json')
    for d in previous:seen.update((d['id'],d['text_sha256'],d['prompt_ids_sha256'],text_hash(d['description'])))
    records=[]
    for d in read(source)['inputs']:
        raw=PREFIX[d['domain']]+d['description'];fmt=WRAPPER.format(raw=raw)
        if any(x in seen for x in (d['id'],text_hash(d['description']),text_hash(raw),text_hash(fmt))):continue
        records.append(dict(id=d['id'],text=d['description'],domain=d['domain'],raw_prompt=raw,formatted_prompt=fmt,source_revision=d['source_revision'],source_url=d['source_url'],cap=128))
    controls=[old[x] for x in ('MATH500/test/prealgebra/1865.json','MATH500/test/prealgebra/1804.json','GSM8K/train/1184')]
    with (dest/'texts.jsonl').open('x',encoding='utf-8') as f:
        for d in controls+records:f.write(json.dumps({'id':d['id'],'formatted_prompt':d['formatted_prompt']},ensure_ascii=False)+'\n')
    tok=LLAMA/'tokenizer-build-00/build/Release/operator_replay.exe'
    with (dest/'tokenizer.log').open('x') as f:subprocess.run([str(tok),read(ROOT/'MODEL_PINS.json')['files'][0]['path'],str(dest/'texts.jsonl'),str(dest/'tokens.jsonl')],stdout=f,stderr=subprocess.STDOUT,check=True)
    tokens={x['id']:x['prompt_ids'] for x in map(json.loads,(dest/'tokens.jsonl').read_text(encoding='utf-8').splitlines())}
    assert all(tokens[x['id']]==x['prompt_ids'] for x in controls)
    rows=[];counts=collections.Counter()
    for d in records:
        ids=tokens[d['id']];n=len(ids)
        if n<24 or n+130>=512 or digest(ids) in seen:continue
        d.update(prompt_ids=ids,prompt_ids_sha256=digest(ids),prompt_tokens=n,band='near' if 244<=n<=255 else 'ordinary')
        rows.append(d);counts[d['domain']+'/'+d['band']]+=1
    write(dest/'POOL.json',dict(rows=rows,not_selected=True,source_sha256=sha(source),exposure_sha256=sha(index),latest_exposure_sha256=sha(LLAMA/'research/EXPOSURE.jsonl'),retained_roundtrips=len(controls),tokenizer_sha256=sha(tok),counts=counts))
    print('POOL_ONLY',counts)
if __name__=='__main__':prepare()

