"""Freeze and execute balanced F/E confirmation; never retries a paid slot."""
from common import *
from dvr import DVRServer
from run_s import host_sample

BASE=[{'name':'R','mask':0,'spec':False,'ub':1,'k':0},
      {'name':'N','mask':0,'spec':True,'ub':4,'k':3},
      {'name':'M3','mask':3,'spec':False,'ub':4,'k':0},
      {'name':'C3','mask':3,'spec':True,'ub':4,'k':3}]

def prepare(model):
    family=model=='SmolLM2';discovery=read(PUB/'F_DISCOVERY.json') if family else None
    conditions=[dict(c) for c in BASE];e=read(PUB/('E_ENGINEERING_'+model+'.json'))
    if e['status']=='PASS':conditions.append({'name':'E32','mask':0,'spec':False,'ub':32,'k':0})
    elif not family:
        save(PUB/'Qwen_CONFIRMATION_BLOCKED.json',{'status':'IMPLEMENTATION_BLOCKED','engineering':e,'formal_requests':0});return
    if family and discovery['optional_Csel'] is not None:
        m=discovery['optional_Csel'];conditions += [{'name':'Msel','mask':m&3,'spec':False,'ub':4,'k':0},{'name':'Csel','mask':m,'spec':True,'ub':4,'k':3}]
    tasks=read(PUB/('F_CONFIRMATION_INPUTS.json' if family else 'QWEN_CONFIRMATION_INPUTS.json'));blocks=[];ledger={};n=len(conditions)
    for rnd in range(n):
        order=conditions[rnd:]+conditions[:rnd]
        ordered=sorted(tasks,key=lambda t:hashlib.sha256((f'JSA_RTX_VALIDATION_V1|{model}|round|{rnd+1}|'+t['id']).encode()).hexdigest())
        for pos,c in enumerate(order,1):
            name=f'r{rnd+1}-p{pos}-{c["name"]}';slots=[name+'|'+t['id'] for t in ordered]
            blocks.append({'block':name,'round':rnd+1,'position':pos,'condition':c,'tasks':[t['id'] for t in ordered],'slots':slots})
            for s in slots:ledger[s]={'status':'PLANNED'}
    names=['common.py','dvr.py','formal.py','run_s.py','verify_confirmation.py']
    plan={'utc':now(),'model':model,'starting_head':head(),'design_head':'0e1949eaf1289f96e2ffaa83babb3b22c8c3e322','conditions':conditions,'rounds':n,'blocks':blocks,'formal_requests':24*n*n,'warmups':n*n,'input_file':'F_CONFIRMATION_INPUTS.json' if family else 'QWEN_CONFIRMATION_INPUTS.json','input_sha256':sha(PUB/('F_CONFIRMATION_INPUTS.json' if family else 'QWEN_CONFIRMATION_INPUTS.json')),'code_sha256':{name:sha(Path(__file__).parent/name) for name in names},'native_build_sha256':sha(PUB/'NATIVE_BUILD.json'),'model_choice_sha256':sha(PUB/'MODEL_CHOICE.json'),'discovery_sha256':sha(PUB/'F_DISCOVERY.json') if family else None,'E_engineering_sha256':sha(PUB/('E_ENGINEERING_'+model+'.json')),'timer':'full nonstreaming client HTTP submit/receive/JSON parse perf_counter; server predicted_ms descriptive only','statistic':'absolute time medians across rounds per task/condition;24 task GM;10000 paired task bootstrap PCG64 seed20261010,type7; descriptive','missing':'no formal retries, imputations or passing-subset ratios','host':'single GPU sequential resident blocks;AC required;host snapshot before every load; balanced orders; no extra S-style cooling for F/E','method':'LLM42_DVR_GGML_W32; same target shared weights, fastUB4 verifierUB32; mask0; padding32; no engineering fixtures or graph capture','source_timer_generation_comparison':None,'stop_budget':'planned matrix only;48h total formal GPU cap;7000 request global cap','shared_F_E_records':family,'qualification':'all slots complete, full arrays equal to every paid R and stable R; E stable-but-different=COMPLETE_CONTRACT_MISMATCH'}
    save(PUB/(model+'_F0.json'),plan);save(LOCAL/(model+'_SLOTS.json'),ledger)
    print(model,'FROZEN PLAN',plan['formal_requests'],flush=True)

def run(model):
    plan=read(PUB/(model+'_F0.json'));receipt=read(LOCAL/(model+'_REMOTE_RECEIPT.json'));assert receipt['remote_sha']==receipt['frozen_sha'] and receipt['manifest_sha256']==sha(PUB/(model+'_F0.json'))
    family=model=='SmolLM2';cfg=read(LOCAL/('F_MODEL_CONFIG.json' if family else 'CONFIG.json'));warm=cfg['warm'] if family else WARM;exe=LOCAL/'native/build/bin/llama-server.exe'
    assert sha(PUB/plan['input_file'])==plan['input_sha256'];build=read(PUB/'NATIVE_BUILD.json')
    for name,h in build['binaries'].items():assert sha(exe.parent/name)==h
    for m in cfg['models'].values():assert sha(m['path'])==m['sha256']
    root=LOCAL/'runs'/('confirmation_'+model);root.mkdir(parents=True,exist_ok=False);ledger=read(LOCAL/(model+'_SLOTS.json'));tasks={t['id']:t for t in read(PUB/plan['input_file'])};begun=time.monotonic()
    save(root/'START.json',{'utc':now(),'freeze':receipt,'actual_head':head()})
    for b in plan['blocks']:
        for name,h in plan['code_sha256'].items():assert sha(Path(__file__).parent/name)==h,'confirmation immutable code drift'
        assert sha(PUB/'NATIVE_BUILD.json')==plan['native_build_sha256']
        d=root/b['block'];print('CONFIRMATION',model,d.name,flush=True);sample=host_sample();save(d.with_name(d.name+'-HOST.json'),sample)
        if sample['AC']!=1 or time.monotonic()-begun>48*3600:
            for slot in b['slots']:ledger[slot].update(status='MISSING_HOST_OR_BUDGET',utc=now())
            save(LOCAL/(model+'_SLOTS.json'),ledger);continue
        try:
            server=DVRServer(d,cfg['models'],warm,False) if b['condition']['name']=='E32' else Server(d,b['condition'],False,cfg['models'],exe,warm)
            with server as s:
                for tid,slot in zip(b['tasks'],b['slots']):
                    assert ledger[slot]['status']=='PLANNED';ledger[slot].update(status='STARTED',utc=now());save(LOCAL/(model+'_SLOTS.json'),ledger)
                    try:
                        a=measure(s,tasks[tid],slot);a.update(round=b['round'],position=b['position'],model=model,execution_freeze_commit=receipt['frozen_sha']);p=d/(tid.replace('/','-')+'.json');save(p,a)
                        ledger[slot].update(status='COMPLETED',record=str(p.relative_to(LOCAL)),record_sha256=sha(p),utc=now())
                    except Exception as e:ledger[slot].update(status='FAILED_OPERATION',error=repr(e),utc=now());print('FAILED',slot,repr(e),flush=True)
                    save(LOCAL/(model+'_SLOTS.json'),ledger)
        except Exception as e:
            save(d.with_name(d.name+'-ERROR.json'),{'error':repr(e),'utc':now()})
            for slot in b['slots']:
                if ledger[slot]['status']=='PLANNED':ledger[slot].update(status='MISSING_BLOCK_FAILURE',error=repr(e),utc=now())
            save(LOCAL/(model+'_SLOTS.json'),ledger)
    save(root/'COMPLETE.json',{'utc':now(),'statuses':{k:sum(a['status']==k for a in ledger.values()) for k in set(a['status'] for a in ledger.values())},'seconds':time.monotonic()-begun})
    print('CONFIRMATION FINISHED',model,flush=True)

if __name__=='__main__':
    import sys
    {'prepare':prepare,'run':run}[sys.argv[1]](sys.argv[2])
