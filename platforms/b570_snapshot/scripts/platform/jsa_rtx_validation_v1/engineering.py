"""Finite family/method engineering using only exposed and synthetic inputs."""
from common import *
from dvr import DVRServer
from prepare_family import format_smol
def wait_s():
    while not (LOCAL/'runs/S_formal/COMPLETE.json').exists():time.sleep(20)
def bridge_new_core():
    root=LOCAL/'runs/new_core_bridge';root.mkdir(parents=True,exist_ok=False);exe=LOCAL/'native/build/bin/llama-server.exe';tasks=read(PUB/'BRIDGE_INPUTS.json')
    conditions=read(REPO/'docs/experiments/jsa_rtx_validation_20261010/DESIGN.json')['S']['conditions']
    for c in conditions:
        d=root/c['name']
        with Server(d,c,False,exe=exe) as s:
            for t in tasks:save(d/(t['id'].replace('/','-')+'.json'),measure(s,t,'new_core_bridge|'+c['name']+'|'+t['id']))
    save(root/'COMPLETE.json',{'requests':16,'warmups':4,'utc':now()})
def family_proof():
    cfg=read(LOCAL/'F_MODEL_CONFIG.json');tasks=read(PUB/'F_DISCOVERY_INPUTS.json')[:4];root=LOCAL/'runs/F_graph_proof';root.mkdir(parents=True,exist_ok=False)
    conditions=[{'name':'R','mask':0,'spec':False,'ub':1,'k':0},{'name':'N0','mask':0,'spec':True,'ub':4,'k':3},{'name':'C3','mask':3,'spec':True,'ub':4,'k':3},{'name':'C15','mask':15,'spec':True,'ub':4,'k':3}]
    for c in conditions:
        d=root/c['name']
        with Server(d,c,True,cfg['models'],cfg['exe'],cfg['warm']) as s:
            for t in tasks:save(d/(t['id'].replace('/','-')+'.json'),measure(s,t,'graph_proof|'+c['name']+'|'+t['id']))
    save(root/'COMPLETE.json',{'requests':16,'warmups':4,'utc':now()})
def family_discovery():
    cfg=read(LOCAL/'F_MODEL_CONFIG.json');tasks=read(PUB/'F_DISCOVERY_INPUTS.json');root=LOCAL/'runs/F_discovery';root.mkdir(parents=True,exist_ok=False)
    conditions=[{'name':'R','mask':0,'spec':False,'ub':1,'k':0}]+[{'name':'N'+str(m),'mask':m,'spec':True,'ub':4,'k':3} for m in range(16)]+[{'name':'M'+str(m),'mask':m,'spec':False,'ub':4,'k':0} for m in range(4)]
    save(root/'PLAN.json',{'conditions':conditions,'tasks':[t['id'] for t in tasks],'repetitions':2,'requests':504,'warmups':42,'utc':now(),'source_commit':head()})
    for rep in range(2):
        for c in (conditions if rep==0 else list(reversed(conditions))):
            d=root/f'r{rep+1}-{c["name"]}';print('F DISCOVERY',d.name,flush=True)
            with Server(d,c,False,cfg['models'],cfg['exe'],cfg['warm']) as s:
                for t in tasks:
                    a=measure(s,t,d.name+'|'+t['id']);a['repetition']=rep+1;save(d/(t['id'].replace('/','-')+'.json'),a)
    save(root/'COMPLETE.json',{'requests':504,'warmups':42,'utc':now()})
def dvr_engineering(model):
    is_family=model=='SmolLM2';cfg=read(LOCAL/'F_MODEL_CONFIG.json') if is_family else read(LOCAL/'CONFIG.json');models=cfg['models'];warm=cfg['warm'] if is_family else WARM;fmt=format_smol if is_family else lambda t:'<|im_start|>user\n'+t+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
    tasks=read(PUB/'F_DISCOVERY_INPUTS.json')[:4] if is_family else read(PUB/'BRIDGE_INPUTS.json');cases=[]
    for t in tasks:
        for rep in range(2):cases.append({'name':'probe-'+t['id'].replace('/','-')+f'-r{rep+1}','body':{'prompt':t['formatted_prompt'],'n_predict':128},'kind':'exposed_probe','task':t['id']})
    long=fmt('Write a Python function with fifty sequential variable assignments. Return only the code.')
    for cap in [1,2,31,32,33,64,128]:
        for rep in range(2):cases.append({'name':f'cap-{cap}-r{rep+1}','body':{'prompt':long,'n_predict':cap},'kind':'synthetic_cap'})
    for cap in [2,5,12]:
        for dummy in [32,33]:
            for rep in range(2):cases.append({'name':f'padding-cap{cap}-dummy{dummy}-r{rep+1}','body':{'prompt':long,'n_predict':cap,'fixture_padding_token':dummy,**({'fixture_save_state':True} if cap==2 and dummy==32 and rep==0 else {})},'kind':'synthetic_padding'})
    for index in [0,15,30]:
        for rep in range(2):cases.append({'name':f'rollback-{index}-r{rep+1}','body':{'prompt':long,'n_predict':64,'fixture_bad_proposal_at':index},'kind':'synthetic_rollback'})
    for rep in range(2):cases.append({'name':f'pending-eog-r{rep+1}','body':{'prompt':long,'n_predict':128,'fixture_pending_eog':True},'kind':'synthetic_pending_eog'})
    for index in [0,15,30]:
        for rep in range(2):cases.append({'name':f'verified-eog-{index}-r{rep+1}','body':{'prompt':long,'n_predict':128,'fixture_verified_eog_at':index},'kind':'synthetic_verified_eog_decision'})
    root=LOCAL/'runs'/('E_engineering_'+model);root.mkdir(parents=True,exist_ok=False);save(root/'PLAN.json',{'cases':cases,'requests':len(cases),'warmups':1,'source_commit':head(),'utc':now()})
    with DVRServer(root/'server',models,warm,True) as s:
        for c in cases:
            body={**c['body'],'temperature':0,'seed':123,'cache_prompt':False,'return_tokens':True,'stream':False}
            print('E ENGINEERING',model,c['name'],flush=True);started=time.perf_counter();r=s.request('/completion',body);wall=1000*(time.perf_counter()-started)
            save(root/(c['name']+'.json'),{'case':c,'body':body,'response':r,'wall_ms':wall,'utc':now(),'source_commit':head()})
    save(root/'COMPLETE.json',{'requests':len(cases),'warmups':1,'utc':now()})
if __name__=='__main__':
    import sys
    mode=sys.argv[1];wait_s()
    {'bridge':bridge_new_core,'family_proof':family_proof,'discovery':family_discovery}.get(mode,lambda:dvr_engineering(mode))()
