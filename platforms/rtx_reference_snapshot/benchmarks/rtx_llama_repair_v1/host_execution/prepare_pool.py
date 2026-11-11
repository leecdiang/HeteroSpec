"""Prepare natural prompts with the original Llama template and GGUF tokenizer."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--model',required=True)
    p.add_argument('--helper-build',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,'D:/rtx155/pydeps')
    from jinja2 import Environment
    import pyarrow.parquet as pq
    contract_path=Path('D:/hs-qb-confirmation-v02/MODEL_CONTRACT.json')
    contract=read(contract_path)['families']['Llama'];template=contract['template']
    assert sha(template.encode())==contract['template_sha256'] and contract['added_special_for_template'] is False
    history=read('D:/hs-qb-confirmation-v02/PLAN.json')['panel']['Llama']
    renderer=Environment().from_string(template)
    def render(text):return renderer.render(messages=[{'role':'user','content':text}],add_generation_prompt=True,bos_token='<|begin_of_text|>')
    controls=[]
    for item in history:
        assert item['add_special'] is False and render(item['raw_prompt'])==item['formatted_prompt']
        controls.append({'id':'historical/'+item['id'],'formatted_prompt':item['formatted_prompt']})
    code_prefix=next(x['raw_prompt'].split('\n\n',1)[0] for x in history if x['domain']=='MBPP')
    math_prefix=next(x['raw_prompt'].split('\n\n',1)[0] for x in history if x['domain']=='GSM8K')
    source=Path('D:/rtx155/preparation');rows=[];files={}
    apps=source/'apps-first1000.jsonl';files[str(apps)]=sha(apps.read_bytes())
    for i,line in enumerate(apps.read_text(encoding='utf-8').splitlines()):
        x=json.loads(line);rows.append(('APPS/test/'+str(x.get('problem_id',i)),'code',x['question'],'21e74ddf8de1a21436da12e3e653065c5213e9d1'))
    for path in sorted((source/'math').rglob('*.parquet')):
        files[str(path)]=sha(path.read_bytes())
        for i,x in enumerate(pq.read_table(path).to_pylist()):rows.append((f'MATH/{path.parent.name}/test/{i}','math',x['problem'],'21a5633873b6a120296cce3e2df9d5550074f4a3'))
    prompts=[]
    for ident,domain,text,revision in rows:
        raw=(code_prefix if domain=='code' else math_prefix)+'\n\n'+text
        prompts.append({'id':ident,'domain':domain,'description':text,'raw_prompt':raw,'formatted_prompt':render(raw),
                        'source_revision':revision,'source_entry_sha256':sha(text.encode()),'text_sha256':sha(text.strip().encode()),'cap':128})
    need_ids=[x['id'] for x in controls+prompts];assert len(set(need_ids))==len(need_ids)
    source_file=a.out/'TOKENIZER_INPUT.jsonl'
    with source_file.open('x',encoding='utf-8',newline='\n') as f:
        for x in controls+prompts:f.write(json.dumps({'id':x['id'],'formatted_prompt':x['formatted_prompt']},ensure_ascii=False)+'\n')
    build=read(a.helper_build);helper=Path(build['executable']);assert sha(helper.read_bytes())==build['executable_sha256']
    output=a.out/'TOKENIZER_OUTPUT.jsonl'
    with (a.out/'tokenizer.stderr.log').open('xb') as err,(a.out/'tokenizer.stdout.log').open('xb') as stdout:
        subprocess.run([str(helper),a.model,str(source_file),str(output)],stdout=stdout,stderr=err,check=True,timeout=1800)
    native=read(str(output)+'.MODEL.json');assert native['template']==template and native['forward_calls']==0 and native['add_special'] is False
    tokenized={r['id']:r['prompt_ids'] for r in map(json.loads,output.read_text().splitlines())}
    assert set(tokenized)==set(need_ids)
    for item in history:assert tokenized['historical/'+item['id']]==item['prompt_ids'],item['id']
    tokenizer_id=sha(json.dumps(contract['tokenizer_metadata']['target'],sort_keys=True,separators=(',',':')).encode())
    receipt={'status':'EXACT_ORIGINAL_TOKENIZER_ROUNDTRIP','historical_items':len(history),'historical_ids':[x['id'] for x in history],
             'template_sha256':contract['template_sha256'],'tokenizer_sha256':tokenizer_id,
             'tokenizer_identity_definition':'SHA256 of the pinned target tokenizer-metadata hash map',
             'helper_build_sha256':sha(a.helper_build.read_bytes()),'source_files':files,'model':a.model,
             'contract_sha256':sha(contract_path.read_bytes()),'add_special':False,'parse_special':True,'forward_calls':0}
    save(a.out/'TOKENIZATION_RECEIPT.json',receipt);rh=sha((a.out/'TOKENIZATION_RECEIPT.json').read_bytes())
    candidates=[];counts={}
    for item in prompts:
        ids=tokenized[item['id']];n=len(ids);band='short' if 128<=n<=384 else 'long' if 512<=n<=768 else None
        if band is None:continue
        candidates.append(dict(item,prompt_ids=ids,prompt_ids_sha256=sha(json.dumps(ids,separators=(',',':')).encode()),
                               prompt_tokens=n,stratum=band,tokenizer_sha256=tokenizer_id,tokenization_receipt_sha256=rh))
        key=item['domain']+'/'+band;counts[key]=counts.get(key,0)+1
    save(a.out/'POOL.json',candidates);save(a.out/'COUNTS.json',counts)
    print('TOKENIZED_POOL_NO_OUTPUTS',counts)


if __name__=='__main__':main()
