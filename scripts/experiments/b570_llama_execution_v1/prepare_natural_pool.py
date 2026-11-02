"""Tokenize natural tasks with exact historical Llama template, zero forwards."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,sha,need,digest,utc,TARGET

def run(root,repo,out):
    root=Path(root);repo=Path(repo);out=Path(out).resolve();need(not out.exists(),'fresh tokenized pool');out.mkdir(parents=True)
    sys.path.insert(0,str(root/'pool-pydeps'))
    from jinja2 import Environment
    import pyarrow.parquet as pq
    contract=read(repo/'benchmarks/jsa_third_family_v1/MODEL_CONTRACT.json')['families']['Llama']
    template=contract['template'];need(hashlib.sha256(template.encode()).hexdigest()==contract['template_sha256']==read(root/'history-01/MODEL_IDENTITY.json')['template_sha256'],'historical template identity')
    renderer=Environment().from_string(template)
    def render(text):return renderer.render(messages=[{'role':'user','content':text}],add_generation_prompt=True,bos_token='<|begin_of_text|>')
    historical=read(root/'HISTORICAL_PROMPT_PLAN.json')['P2_panel']['Llama']
    controls=[]
    for x in historical:
        need(render(x['raw_prompt'])==x['formatted_prompt'],'exact original template rendering')
        controls.append({'id':'historical/'+x['id'],'formatted_prompt':x['formatted_prompt']})
    code=next(x['raw_prompt'].split('\n\n',1)[0] for x in historical if x['domain']=='MBPP')
    math=next(x['raw_prompt'].split('\n\n',1)[0] for x in historical if x['domain']=='GSM8K')
    sources=read(root/'natural-source-00/SOURCES.json');prompts=[]
    for f in sources['files']:
        need(sha(f['path'])==f['sha256'],'natural data drift')
        iscode=f['repo']=='deepmind/code_contests';domain='code' if iscode else 'math';column='description' if iscode else 'problem'
        for i,row in enumerate(pq.read_table(f['path'],columns=[column]).to_pylist()):
            text=row[column];ident=f'CodeContests/test/{i}' if iscode else f'MATH/{Path(f["repo_path"]).parent.name}/train/{i}'
            raw=(code if iscode else math)+'\n\n'+text
            prompts.append({'id':ident,'domain':domain,'description':text,'raw_prompt':raw,'formatted_prompt':render(raw),'source_revision':f['revision'],'source_url':f['url'],'source_entry_sha256':hashlib.sha256(text.encode()).hexdigest(),'text_sha256':hashlib.sha256(text.strip().encode()).hexdigest(),'cap':128})
    need(len({x['id'] for x in controls+prompts})==len(controls+prompts),'duplicate task IDs')
    inp=out/'TOKENIZER_INPUT.jsonl'
    with inp.open('x',encoding='utf-8') as file:
        for x in controls+prompts:file.write(json.dumps({'id':x['id'],'formatted_prompt':x['formatted_prompt']},ensure_ascii=False)+'\n')
    b=read(root/'tokenizer-build-00/BUILD.json');model=read(root/'host-01.json')['target'];need(sha(model)==TARGET,'exact model identity')
    write(out/'FILES.json',{'files':b['files']});result=out/'TOKENIZER_OUTPUT.jsonl'
    command=[sys.executable,'-B',b['supervisor'],'--manifest',str(out/'FILES.json'),'--receipt',str(out/'SUPERVISOR.json'),'--limit','1800','--minimum-free-bytes',str(20*1024**3),b['executable'],model,str(inp),str(result)]
    write(out/'COMMAND.json',{'argv':command,'purpose':'CPU vocabulary-only preparation; no contexts, weights, inference or selected panel','utc':utc()})
    subprocess.run(command,check=True,timeout=1980)
    native=read(str(result)+'.MODEL.json');need(native['template']==template and native['forward_calls']==0 and native['contexts_created']==0 and not native['add_special'] and native['parse_special'],'native tokenizer contract')
    tokens={x['id']:x['prompt_ids'] for x in map(json.loads,result.read_text(encoding='utf-8').splitlines())}
    need(set(tokens)=={x['id'] for x in controls+prompts},'complete tokenizer inventory')
    for x in historical:need(tokens['historical/'+x['id']]==x['prompt_ids'],'historical native-token roundtrip')
    binding={'target_sha256':TARGET,'template_sha256':contract['template_sha256'],'historical_plan_sha256':sha(root/'HISTORICAL_PROMPT_PLAN.json'),'historical_roundtrips':len(historical),'build_sha256':sha(root/'tokenizer-build-00/BUILD.json'),'supervisor_sha256':sha(out/'SUPERVISOR.json'),'source_manifest_sha256':sha(root/'natural-source-00/SOURCES.json'),'forward_calls':0,'contexts_created':0}
    selected=[];counts={}
    for x in prompts:
        ids=tokens[x['id']];n=len(ids);band='short' if 128<=n<=384 else 'long' if 512<=n<=768 else None
        if band is None:continue
        selected.append(dict(x,prompt_ids=ids,prompt_ids_sha256=digest(ids),prompt_tokens=n,stratum=band))
        key=x['domain']+'/'+band;counts[key]=counts.get(key,0)+1
    write(out/'POOL.json',{'inputs':selected,'tokenizer_binding':binding,'not_selected_panel':True});write(out/'COUNTS.json',counts);write(out/'TOKENIZATION_RECEIPT.json',binding)
    print(counts,flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser()
    for k in ('root','repo','out'):a.add_argument('--'+k,required=True)
    p=a.parse_args();run(p.root,p.repo,p.out)
