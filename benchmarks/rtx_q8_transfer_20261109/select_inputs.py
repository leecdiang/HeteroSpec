"""Prospective selection from the unchanged authorized pools; vocabulary only."""
from pathlib import Path
import ast, collections, hashlib, json, subprocess, sys, time
from admission import HERE, ROOT, sha, put

def visit(x, blocked):
    if isinstance(x,dict):
        for k,v in x.items():
            if k in ('id','root','input_id','root_id','task_id','message_id') and isinstance(v,str): blocked.add(v)
            if k in ('text','description','raw_prompt','formatted_prompt','prompt') and isinstance(v,str): blocked.add(hashlib.sha256(v.strip().encode()).hexdigest())
            if k in ('text_sha256','content_sha256','raw_prompt_sha256','formatted_prompt_sha256') and isinstance(v,str): blocked.add(v)
            if k in ('keys','root_ids','roots','excluded_roots','additional_authenticated_roots') and isinstance(v,list): blocked.update(y for y in v if isinstance(y,str))
            visit(v,blocked)
    elif isinstance(x,list):
        for y in x: visit(y,blocked)

def main():
    start=time.monotonic();out=ROOT/'cohort';out.mkdir(exist_ok=False)
    sys.path.insert(0,'D:/rtx188/host-dependencies/packages')
    import pyarrow.parquet as pq
    from jinja2 import Environment
    script=HERE.parents[2]/'phase188/benchmarks/rtx_phase_plan_v1/confirmation_select.py'
    tree=ast.parse(script.read_bytes());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='source_rows')
    env=dict(Path=Path,sha=sha,json=json,hashlib=hashlib,pq=pq)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(script),'exec'),env)
    rows,pins=env['source_rows']();blocked=set();exposures={}
    prior=Path('D:/rtx192-review-v2/R2/SOURCE_SELECTION.json')
    saved=json.loads(prior.read_bytes())
    for p,h in saved['exposure_pins'].items():
        p=Path(p);assert sha(p)==h,('prior exposure changed',p)
        exposures[str(p)]=h;visit(json.loads(p.read_bytes()),blocked)
    for p in [prior,Path('D:/rtx192-review-v2/R2/NATIVE_INPUTS.json'),Path('D:/rtx188/Qwen-EXPOSED-ROOTS.json')]:
        exposures[str(p)]=sha(p);visit(json.loads(p.read_bytes()),blocked)
    # All original M1/M2 formal roots came from the immutable PR195 R2 pool.
    # Exclude the entire 128-root prospectively reserved PR195 source pool too.
    unique={}
    for r in sorted(rows,key=lambda r:r['id']):
        if {r['id'],r['text_sha256'],r['raw_prompt_sha256']}&blocked:continue
        unique.setdefault(r['text_sha256'],r)
    ordered=sorted(unique.values(),key=lambda r:(r['domain'],hashlib.sha256(('20261109|'+r['domain']+'|'+r['id']).encode()).hexdigest(),r['id']))
    contract_path=Path('D:/hs144-e5c03228-9eb9-4198-8f14-a7d279d08afa/MODEL_CONTRACT.json')
    contract=json.loads(contract_path.read_bytes())['families']['Qwen']
    assert hashlib.sha256(contract['template'].encode()).hexdigest()==contract['template_sha256']
    template=Environment().from_string(contract['template'])
    render=lambda r:template.render(messages=[dict(role='user',content=r['raw_prompt'])],add_generation_prompt=True,enable_thinking=False)
    original=json.loads(Path('D:/hs-qb-confirmation-v02/PLAN.json').read_bytes())['panel']['Qwen']
    tokenizer=Path('D:/rtx188/confirmation/tokenizer-Qwen');build=json.loads((tokenizer/'BUILD.json').read_bytes())
    assert build['vocab_only'] and sha(tokenizer/'bin/worker.exe')==build['exe']
    for n,h in build['modules'].items():assert sha(tokenizer/'bin'/n)==h
    inp=out/'rendered.jsonl';output=out/'tokens.jsonl'
    with inp.open('x',encoding='utf8') as f:
        for i,r in enumerate(original):
            assert render(r)==r['formatted_prompt']
            f.write(json.dumps(dict(id='roundtrip-'+str(i),formatted_prompt=render(r)),ensure_ascii=False)+'\n')
        for r in ordered:f.write(json.dumps(dict(id=r['id'],formatted_prompt=render(r)),ensure_ascii=False)+'\n')
    put(out/'SOURCE_SELECTION_BEFORE_TOKENIZATION.json',dict(seed=20261109,rule='SHA256(20261109|domain|task_id); first eight/domain with prompt tokens <=192; no padding or output criteria',
        source_pins=pins,exposure_pins=exposures,source_reader_sha256=sha(script),source_entries=len(rows),unique_eligible_before_length=len(ordered),
        ranked_ids=[r['id'] for r in ordered],tokenizer_executable_sha256=build['exe'],model_forwards=0))
    argv=[str(tokenizer/'bin/worker.exe'),'D:/HeteroSpec-PC/models/gguf/Qwen3-8B-Q8_0.gguf',str(inp),str(output)]
    began=time.monotonic()
    with (out/'tokenizer.stdout.log').open('xb') as stdout,(out/'tokenizer.stderr.log').open('xb') as stderr:
        r=subprocess.run(argv,stdout=stdout,stderr=stderr,timeout=900)
    put(out/'TOKENIZER_COST.json',dict(argv=argv,code=r.returncode,wall_seconds=time.monotonic()-began,model_forward_requests=0,vocabulary_only=True))
    r.check_returncode()
    tokens={r['id']:r['prompt_ids'] for r in map(json.loads,output.read_text(encoding='utf8').splitlines())}
    assert all(tokens['roundtrip-'+str(i)]==r['prompt_ids'] for i,r in enumerate(original))
    selected=[];counts={}
    for domain in ('code','math'):
        eligible=[r for r in ordered if r['domain']==domain and 1<=len(tokens[r['id']])<=192]
        counts[domain]=dict(source_candidates=sum(r['domain']==domain for r in ordered),eligible_prompt_le192=len(eligible))
        for r in eligible[:8]:selected.append(dict(r,formatted_prompt=render(r),formatted_prompt_sha256=hashlib.sha256(render(r).encode()).hexdigest(),prompt_ids=tokens[r['id']],cap=96,family='Qwen'))
    put(out/'COHORT_ADMISSION.json',dict(status='COHORT_PROVISIONAL_EXPOSURE_AUDIT_REQUIRED' if len(selected)==16 else 'INSUFFICIENT_ELIGIBLE_ROOTS',
        counts=counts,selected=selected,source_selection_sha256=sha(out/'SOURCE_SELECTION_BEFORE_TOKENIZATION.json'),
        template_sha256=contract['template_sha256'],contract_sha256=sha(contract_path),tokenizer=build,
        roundtrips=len(original),no_model_forwards=True,total_wall_seconds=time.monotonic()-start,
        remaining_gate='Verify explicit archived PR209 roots and PR62 exposure identities before final freeze; no formal outputs authorized by this provisional selection'))
    print(json.dumps(dict(counts=counts,selected_ids=[r['id'] for r in selected],token_lengths=[len(r['prompt_ids']) for r in selected],model_forwards=0)))

if __name__=='__main__':main()
