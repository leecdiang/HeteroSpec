"""Outcome-free raw-root selection, then original native token admission."""
from develop import *
sys.path.insert(0,str(ROOT/'host-dependencies/packages'))
import pyarrow.parquet as pq
from jinja2 import Environment

DEST=ROOT/'confirmation'
SEED='rtx-phase-plan-v1-confirmation-20261106'
CONTRACT=Path('D:/hs144-e5c03228-9eb9-4198-8f14-a7d279d08afa/MODEL_CONTRACT.json')

def save(path,value):
    if path.exists():assert json.loads(path.read_bytes())==value
    else:put(path,value)

def source_rows():
    rows=[];pins={}
    def pin(p):pins[str(p)]=sha(p)
    def apps(p,split,first=0):
        pin(p)
        for i,line in enumerate(p.read_text(encoding='utf8').splitlines(),first):
            x=json.loads(line);rows.append(dict(id=f'APPS/{split}/'+str(x.get('problem_id',i)),domain='code',description=x['question'],source_revision='21e74ddf8de1a21436da12e3e653065c5213e9d1'))
    base=Path('D:/rtx155/preparation');apps(base/'apps-first1000.jsonl','test')
    more=Path('E:/rtx164/apps-new');j=json.loads((more/'SOURCE.json').read_bytes());pin(more/'SOURCE.json');assert sha(more/'rows.jsonl')==j['sha256'];apps(more/'rows.jsonl','test',j['first'])
    more=Path('E:/rtx164/apps-train');j=json.loads((more/'SOURCE.json').read_bytes());pin(more/'SOURCE.json');assert sha(more/'rows.jsonl')==j['sha256'];apps(more/'rows.jsonl','train')
    paths=list((base/'math').rglob('test-*.parquet'))
    more=Path('E:/rtx164/math-train');pin(more/'SOURCE.json')
    for item in json.loads((more/'SOURCE.json').read_bytes()):
        p=more/item['path'];assert sha(p)==item['sha256'];paths.append(p)
    for p in sorted(paths):
        pin(p);split='test' if p.name.startswith('test-') else 'train'
        for i,x in enumerate(pq.read_table(p).to_pylist()):rows.append(dict(id=f'MATH/{p.parent.name}/{split}/{i}',domain='math',description=x['problem'],source_revision='21a5633873b6a120296cce3e2df9d5550074f4a3'))
    for r in rows:
        prefix='Complete the following Python programming task. Return only the completed Python code, without Markdown fences.' if r['domain']=='code' else 'Solve the following mathematics problem. Give your reasoning and final answer.'
        r['raw_prompt']=prefix+'\n\n'+r['description'];r['text_sha256']=hashlib.sha256(r['description'].strip().encode()).hexdigest();r['raw_prompt_sha256']=hashlib.sha256(r['raw_prompt'].encode()).hexdigest()
    assert len({r['id'] for r in rows})==len(rows),'ambiguous raw source root identities'
    return rows,pins

def exposures():
    blocked=set();pins={}
    def visit(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in ('id','input_id','root_id','task_id','message_id') and isinstance(v,str):blocked.add(v)
                if k in ('text','description','raw_prompt','formatted_prompt','prompt') and isinstance(v,str):blocked.add(hashlib.sha256(v.strip().encode()).hexdigest())
                if k in ('text_sha256','raw_prompt_sha256','formatted_prompt_sha256') and isinstance(v,str):blocked.add(v)
                if k in ('keys','root_ids','excluded_roots','additional_authenticated_roots') and isinstance(v,list):blocked.update(y for y in v if isinstance(y,str))
                visit(v)
        elif isinstance(x,list):
            for v in x:visit(v)
    prior=Path('E:/rtx164/exposure-pr163/EXPOSURE_AUDIT-00.json');j=json.loads(prior.read_bytes());assert j['complete'];blocked.update(j['keys']);pins[str(prior)]=sha(prior)
    paths=[p for p in (HERE.parent).rglob('*.json') if any(word in p.name.lower() for word in ('panel','inputs','expos','exclusion','selected','selection','census')) and 'POOL' not in p.name and 'rtx_phase_plan_v1' not in p.parts]
    paths+=list((HERE/'prospective_exposure').glob('*.json'))
    paths += [OLD.parent/('admission-'+family+'-v4/PANEL.json') for family in ('Qwen','SmolLM2')]
    paths += [ROOT/(family+'-EXPOSED-ROOTS.json') for family in ('Qwen','Smol')]
    # Retain the earlier complete audits and every subsequently planned panel.
    for base in (Path('E:/rtx164'),Path('E:/rtx170'),Path('E:/rtx172'),Path('F:/rtx176'),Path('F:/rtx184/selection-v3')):
        paths += [p for p in base.rglob('*.json') if any(w in p.name.lower() for w in ('panel','selected','selection','exposure','exclusions','heldout','unseen')) and not any(s in p.parts for s in ('source','core','build','reproduce03'))]
    for p in sorted(set(paths)):
        if not p.exists():continue
        pins[str(p)]=sha(p);visit(json.loads(p.read_bytes()))
    return blocked,pins

def select_sources():
    DEST.mkdir(exist_ok=True);rows,pins=source_rows();blocked,epins=exposures();unique={};excluded=0
    for r in sorted(rows,key=lambda x:x['id']):
        if {r['id'],r['text_sha256'],r['raw_prompt_sha256']}&blocked:excluded+=1;continue
        unique.setdefault(r['text_sha256'],r)
    used=set();families={}
    for family in ('Qwen','Smol'):
        picked=[]
        for domain in ('math','code'):
            eligible=[r for r in unique.values() if r['domain']==domain and r['text_sha256'] not in used]
            ordered=sorted(eligible,key=lambda r:hashlib.sha256((SEED+'|'+family+'|'+domain+'|'+r['id']).encode()).hexdigest())
            assert len(ordered)>=32;picked+=ordered[:32]
        used.update(r['text_sha256'] for r in picked);families[family]=picked
    save(DEST/'SOURCE_SELECTION.json',dict(seed=SEED,raw_source_entries=len(rows),historically_excluded_entries=excluded,unique_unexposed_roots=len(unique),source_pins=pins,exposure_pins=epins,source_candidates_per_domain_and_family=32,selected_before_any_new_token_admission=True,admission_rule='First4 roots per domain in frozen hash order with1<=tokens and tokens+132<=1024; no alignment/opportunity/performance filtering.',candidate_families=families))
    print('Raw roots selected before token admission:',len(rows),'source entries;',len(unique),'unique unexposed roots',flush=True)

def tokenizer(family):
    out=DEST/('tokenizer-'+family)
    if (out/'BUILD.json').exists():return out
    out.mkdir(exist_ok=True);old=OLD if family=='Qwen' else META;binding=json.loads((old/'BUILD.json').read_bytes())
    source=Path('E:/rtx160/tokenizer01/build/vocab_only.cpp').read_text().replace('128256','151936' if family=='Qwen' else '49152').replace('original Llama vocabulary','original family vocabulary')
    (out/'tokenizer.cpp').write_text(source);(out/'bin').mkdir(exist_ok=True)
    for n,h in binding['numerical_modules'].items():
        src=ROOT/VERSIONS['R-'+family]/'bin'/n;assert sha(src)==h
        if not (out/'bin'/n).exists():os.link(src,out/'bin'/n)
        else:assert sha(out/'bin'/n)==h
    for r in binding['commands']:
        if r['label'] not in ('worker','link'):continue
        argv=[v.replace(str(old/'worker.cpp'),str(out/'tokenizer.cpp')).replace(str(old/'worker.obj'),str(out/'worker.obj')).replace(str(old/'bin/rtx-scope-transfer.exe'),str(out/'bin/worker.exe')) for v in r['argv']];command(out,r['label'],argv)
    put(out/'BUILD.json',dict(exe=sha(out/'bin/worker.exe'),source_sha256=sha(out/'tokenizer.cpp'),core_sha256=binding['core_sha256'],modules=binding['numerical_modules'],vocab_only=True,model_forwards=0))
    return out

def admit():
    selected=json.loads((DEST/'SOURCE_SELECTION.json').read_bytes());contract=json.loads(CONTRACT.read_bytes());result={}
    for family in ('Qwen','Smol'):
        key='Qwen' if family=='Qwen' else 'SmolLM2';c=contract['families'][key];assert hashlib.sha256(c['template'].encode()).hexdigest()==c['template_sha256']
        template=Environment().from_string(c['template']);items=[]
        old_panel=Path('D:/hs-qb-confirmation-v02/PLAN.json');historical=json.loads(old_panel.read_bytes())['panel'][key];roundtrips=[]
        for i,r in enumerate(historical):
            rendered=template.render(messages=[dict(role='user',content=r['raw_prompt'])],add_generation_prompt=True,enable_thinking=False)
            assert rendered==r['formatted_prompt'],'original producer template roundtrip differs'
            roundtrips.append(dict(id=f'roundtrip-{i}',formatted_prompt=rendered))
        for r in selected['candidate_families'][family]:
            rendered=template.render(messages=[dict(role='user',content=r['raw_prompt'])],add_generation_prompt=True,enable_thinking=False)
            items.append(dict(r,formatted_prompt=rendered))
        build=tokenizer(family);inp=DEST/(family+'-rendered.jsonl');output=DEST/(family+'-tokens.jsonl')
        if not inp.exists():
            with inp.open('x',encoding='utf8') as f:
                for r in roundtrips+items:f.write(json.dumps(r,ensure_ascii=False)+'\n')
        if not output.exists():command(DEST,'tokenize-'+family,[str(build/'bin/worker.exe'),MODELS[family]['target_model'],str(inp),str(output)])
        tokens={r['id']:r['prompt_ids'] for r in map(json.loads,output.read_text().splitlines())};accepted=[];denominators=[]
        assert all(tokens[f'roundtrip-{i}']==r['prompt_ids'] for i,r in enumerate(historical)),'actual original-GGUF tokenizer roundtrip differs'
        for domain in ('math','code'):
            examined=0;rejected=[];chosen=[]
            for r in [x for x in items if x['domain']==domain]:
                examined+=1;ids=tokens[r['id']]
                if not 1<=len(ids) or len(ids)+132>1024:rejected.append(dict(id=r['id'],tokens=len(ids)));continue
                chosen.append(dict(r,prompt_ids=ids,cap=128,family=family))
                if len(chosen)==4:break
            assert len(chosen)==4,'insufficient preselected source candidates; do not choose replacements after outputs'
            accepted+=chosen;denominators.append(dict(domain=domain,source_candidates=32,examined_in_frozen_order=examined,rejected_capacity=rejected,admitted=4))
        result[family]=accepted
        save(DEST/(family+'-PANEL.json'),dict(inputs=accepted,denominators=denominators,natural_unpadded=True,contract_sha256=sha(CONTRACT),template_sha256=c['template_sha256'],native_vocabulary_only_receipt=str(output)+'.MODEL.json',original_producer_roundtrip_inputs=12,original_producer_panel_sha256=sha(old_panel),new_model_forwards=0))
    save(DEST/'PANELS.json',result);print('Admitted8 new roots/family, without forward outputs',[(f,[len(r['prompt_ids']) for r in rs]) for f,rs in result.items()],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action');a=p.parse_args()
    if a.action=='select':select_sources()
    else:admit()
