"""Freeze raw Qwen R2 roots, then vocab-only admission; no model forwards."""
from host_rtx import *
sys.path.insert(0,str(P190/'host-dependencies/packages'))
import confirmation_select as saved
from design import SEED,panel
from jinja2 import Environment
DEST=ROOT/'R2'

def main():
    DEST.mkdir(exist_ok=False);rows,pins=saved.source_rows();prior_selection=read(P190/'confirmation/SOURCE_SELECTION.json');blocked=set();exposure={}
    def visit(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in ('id','root','input_id','root_id','task_id','message_id') and isinstance(v,str):blocked.add(v)
                if k in ('text','description','raw_prompt','formatted_prompt','prompt') and isinstance(v,str):blocked.add(hashlib.sha256(v.strip().encode()).hexdigest())
                if k in ('text_sha256','content_sha256','raw_prompt_sha256','formatted_prompt_sha256') and isinstance(v,str):blocked.add(v)
                if k in ('keys','root_ids','excluded_roots','additional_authenticated_roots') and isinstance(v,list):blocked.update(y for y in v if isinstance(y,str))
                visit(v)
        elif isinstance(x,list):
            for v in x:visit(v)
    for p,h in prior_selection['exposure_pins'].items():
        assert sha(p)==h,('historical exposure file changed',p);exposure[p]=h;visit(read(p))
    for p in [P190/'confirmation/SOURCE_SELECTION.json',P190/'confirmation/PANELS.json',P190/'Qwen-EXPOSED-ROOTS.json',P190/'Smol-EXPOSED-ROOTS.json']:
        exposure[str(p)]=sha(p);visit(read(p))
    unique={};excluded=0
    for r in sorted(rows,key=lambda r:r['id']):
        if {r['id'],r['text_sha256'],r['raw_prompt_sha256']}&blocked:excluded+=1;continue
        unique.setdefault(r['text_sha256'],r)
    def rank(r):return hashlib.sha256(f"{SEED}|{r['id']}|{r['text_sha256']}".encode()).hexdigest()
    candidates=[]
    for domain in ('math','code'):candidates += sorted([r for r in unique.values() if r['domain']==domain],key=lambda r:(rank(r),r['id']))[:64]
    assert len(candidates)==128
    put(DEST/'SOURCE_SELECTION.json',dict(seed=SEED,source_pins=pins,exposure_pins=exposure,source_entries=len(rows),excluded_entries=excluded,unique_unexposed_roots=len(unique),candidates_per_domain=64,candidates=candidates,raw_roots_selected_before_token_admission=True,additional_conservative_exclusion='All PR190 reserved source candidates plus actual selected/exposed roots.',PR191_exposure_review=dict(commit='acc86d9cb07c2afa983f73e28a1048fb99c63e3a',result_blob='628ac27bfee1f25b0360a3ebfcfef8105da66f3b',result_url='https://github.com/leecdiang/HeteroSpec/blob/acc86d9cb07c2afa983f73e28a1048fb99c63e3a/benchmarks/b570_economics_v1/RESULTS.md',no_new_natural_panel=True,only_four_already_exposed_PR187_roots=True),model_forward_outputs=0))
    contract_path=saved.CONTRACT;contract=read(contract_path)['families']['Qwen'];template=Environment().from_string(contract['template']);assert hashlib.sha256(contract['template'].encode()).hexdigest()==contract['template_sha256']
    oldpanel=read('D:/hs-qb-confirmation-v02/PLAN.json')['panel']['Qwen'];items=[]
    for i,r in enumerate(oldpanel):
        rendered=template.render(messages=[dict(role='user',content=r['raw_prompt'])],add_generation_prompt=True,enable_thinking=False);assert rendered==r['formatted_prompt'];items.append(dict(id='roundtrip-'+str(i),formatted_prompt=rendered))
    for r in candidates:items.append(dict(r,formatted_prompt=template.render(messages=[dict(role='user',content=r['raw_prompt'])],add_generation_prompt=True,enable_thinking=False)))
    inp=DEST/'rendered.jsonl';out=DEST/'tokens.jsonl'
    with inp.open('x',encoding='utf8') as f:
        for r in items:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    tokenizer=P190/'confirmation/tokenizer-Qwen';binding=read(tokenizer/'BUILD.json');assert binding['vocab_only'] and sha(tokenizer/'bin/worker.exe')==binding['exe']
    assert sha(MODEL['Qwen']['target_model'])==MODEL['Qwen']['target_sha256']
    command(DEST,'native-vocab-tokenize',[str(tokenizer/'bin/worker.exe'),MODEL['Qwen']['target_model'],str(inp),str(out)])
    tokens={r['id']:r['prompt_ids'] for r in map(json.loads,out.read_text(encoding='utf8').splitlines())};assert all(tokens['roundtrip-'+str(i)]==r['prompt_ids'] for i,r in enumerate(oldpanel))
    minimal=[dict(root=r['id'],content_sha256=r['text_sha256'],domain=r['domain'],prompt_tokens=len(tokens[r['id']])) for r in candidates]
    selection=panel(minimal,[],[]);put(DEST/'ADMISSION.json',selection)
    chosen={r['root'] for r in selection['selected']}
    full=[dict(r,prompt_ids=tokens[r['id']],cap=128,family='Qwen') for r in candidates if r['id'] in chosen]
    # The selected ordinary limit must also satisfy the conservative existing
    # D4 transient verify allocation; never change offsets or truncate prompts.
    assert len(full)==16 and all(len(r['prompt_ids'])+132<=1024 for r in full),'Retain admission; actual D4 capacity requires a separately recorded pre-output repair'
    put(DEST/'INPUTS.json',dict(Qwen=selection['selected']));put(DEST/'NATIVE_INPUTS.json',dict(inputs=full,model_hash=MODEL['Qwen']['target_sha256'],contract_sha256=sha(contract_path),template_sha256=contract['template_sha256'],tokenizer=binding,native_roundtrips=len(oldpanel),model_forwards=0,no_padding_or_offset_selection=True))
    print('R2 independently selected/admitted16 Qwen roots; native vocab-only roundtrips passed', [len(r['prompt_ids']) for r in full],flush=True)

if __name__=='__main__':main()
