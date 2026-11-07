"""CPU-only artificial records test completeness, raw suffix and reference gates."""
from analyse import *
def write(p,a):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(a,ensure_ascii=False),encoding='utf-8')
def main(tag=''):
    root=LOCAL/('cpu-check'+tag);root.mkdir(exist_ok=False);pub=root/'repository/benchmarks';local=root/'third-family';cs=[{'name':c} for c in ['R','N','M3','C3_K3','C3_K1','C3_K2']];families=['Qwen','SmolLM2','Llama']
    tasks=[{'id':f'fixture/{i}','domain':'MBPP' if i<12 else 'GSM8K','cap':128,'prompt_token_count':1} for i in range(24)]
    freeze='1'*40;blocks=[];paths={}
    for session in range(2):
        for family in families:
            for rnd in range(4):
                for c in cs:
                    name=f'{family}-{session}-{rnd}-{c["name"]}';slots=[name+'|'+t['id'] for t in tasks];blocks.append({'block':name,'session':session,'family':family,'round':rnd,'condition':c,'slots':slots})
                    for task,slot in zip(tasks,slots):
                        d=local/'runs/formal'/name/task['id'].replace('/','_');paths[(family,session,rnd,c['name'],task['id'])]=d
                        write(d/'REQUEST_STARTED.json',{'slot':slot,'warmup':False,'fixture_no_model_forward':True})
                        response={'tokens':[9],'tokens_predicted':1,'stop_type':'eos','truncated':False,'timings':{'cache_n':0,'prompt_n':1}}
                        if c['name']=='N':response['timings'].update(draft_n=7,draft_n_accepted=3)
                        a={'slot':slot,'task':task['id'],'family':family,'condition':c,'freeze_commit':freeze,'response':response,'tokens_digest':digest(response['tokens']),'input_sha256':digest(task),'wall_ms':{'R':4.,'N':1.5,'M3':2.,'C3_K3':1.,'C3_K1':1.1,'C3_K2':1.2}[c['name']],'utc':'2000-01-01T00:00:00+00:00','fixture_no_model_forward':True}
                        write(d/'RECORD.json',a);write(d/'COMPLETED.json',{'record_sha256':sha(d/'RECORD.json')})
    write(pub/'FORMAL_PLAN.json',{'blocks':blocks,'conditions':cs});write(pub/'CONFIRMATION_INPUTS.json',{'tasks':tasks,'families':{f:tasks for f in families}});write(pub/'MODEL_CONTRACT.json',{'families':{f:{'eog':[9]} for f in families}});write(local/'F0B_REMOTE_RECEIPT.json',{'frozen_sha':freeze})
    a=analyse(local,pub);assert a['completed']==3456 and all(q['qualified'] for f in a['families'].values() for q in f['qualification'].values())
    assert all(next(c['qualified_ratio'] for c in f['comparisons'] if c['comparison']=='M3/C3_K3')==2 for f in a['families'].values())
    assert all(f['native_distributions']['N']['native_proposed_draft_IDs']==192*7 and f['native_distributions']['N']['native_accepted_draft_IDs']==192*3 for f in a['families'].values())
    n=paths[('Llama',0,0,'N','fixture/0')];(n/'COMPLETED.json').unlink();b=analyse(local,pub)
    assert not b['families']['Llama']['qualification']['N']['qualified'] and next(c['qualified_ratio'] for c in b['families']['Llama']['comparisons'] if c['comparison']=='M3/C3_K3')==2
    c=paths[('Llama',0,0,'C3_K3','fixture/0')];r=read(c/'RECORD.json');r['response']['tokens']=[9,8];r['response']['tokens_predicted']=2;r['tokens_digest']=digest([9,8]);write(c/'RECORD.json',r);write(c/'COMPLETED.json',{'record_sha256':sha(c/'RECORD.json')});z=analyse(local,pub)
    assert not z['families']['Llama']['qualification']['C3_K3']['qualified'] and next(c['qualified_ratio'] for c in z['families']['Llama']['comparisons'] if c['comparison']=='M3/C3_K3') is None
    assert next(r['suffix_ids'] for r in z['native_case_diagnostics'] if r['slot']==read(c/'RECORD.json')['slot'])==[8]
    d=paths[('Qwen',0,0,'R','fixture/0')];r=read(d/'RECORD.json');r['response']['tokens']=[8,9];r['response']['tokens_predicted']=2;r['tokens_digest']=digest([8,9]);write(d/'RECORD.json',r);write(d/'COMPLETED.json',{'record_sha256':sha(d/'RECORD.json')});q=analyse(local,pub)
    assert not q['families']['Qwen']['stable_complete_R'] and all(c['qualified_ratio'] is None for c in q['families']['Qwen']['comparisons'])
    save(PUB/('CPU_ANALYSIS_TESTS'+tag+'.json'),{'status':'PASS','fixture_records':3456,'model_forwards':0,'artificial_records_not_experiments':True,'analysis_code_sha256':sha(Path(__file__).parent/'analyse.py'),'tests':['complete native-array matrix qualifies and matched ratio2','missing unrelated N does not erase complete M3/C3_K3','paid suffix after EOG prevents raw-array qualification and remains retained','unstable paid R nulls all family comparisons','native speculative counters read from response timings'],'fixture_root':str(root)})
    print('CPU ANALYSIS GATES PASS',flush=True)
if __name__=='__main__':
    import sys
    main(sys.argv[1] if len(sys.argv)>1 else '')
