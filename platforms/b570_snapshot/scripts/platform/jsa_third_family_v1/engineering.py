"""Fixed six-condition engineering. Confirmation questions are never loaded."""
from runtime import *

def jobs():
    inputs=read(PUB/'ENGINEERING_INPUTS.json');cs=read(DESIGN/'DESIGN.json')['conditions'];jobs=[]
    for family in ['Qwen','SmolLM2','Llama']:
        for rnd in range(2):
            for c in (cs if rnd==0 else list(reversed(cs))):
                jobs.append({'name':f'{family}-discovery-r{rnd}-{c["name"]}','family':family,'condition':c,'capture':False,'cases':inputs['families'][family]})
        for c in cs:
            for capture in [False,True]:
                jobs.append({'name':f'{family}-capture-{c["name"]}-{int(capture)}','family':family,'condition':c,'capture':capture,'cases':inputs['capture_probes'][family]})
        # Seven predeclared boundaries; only exposed synthetic input, no fixtures/search.
        for c in [cs[0],cs[3]]:
            cases=[{**inputs['capture_probes'][family][1],'id':'synthetic/cap-'+str(cap),'cap':cap} for cap in [1,2,3,4,31,32,128]]
            jobs.append({'name':f'{family}-boundaries-{c["name"]}','family':family,'condition':c,'capture':True,'cases':cases})
    assert sum(len(j['cases'])+1 for j in jobs)==624
    return jobs

def main():
    receipt=read(LOCAL/'F0A_REMOTE_RECEIPT.json');assert receipt['status']=='PASS'
    root=LOCAL/'runs/engineering';root.mkdir(parents=True,exist_ok=True)
    with (root/'SINGLE_WRITER.lock').open('x') as f:f.write(str(os.getpid()))
    inputs=read(PUB/'ENGINEERING_INPUTS.json');plan=read(PUB/'ENGINEERING_PLAN.json');assert plan['jobs']==jobs()
    save(root/'START.json',{'utc':now(),'freeze_commit':receipt['frozen_sha'],'planned_paid_requests':624})
    for j in plan['jobs']:
        print('ENGINEERING',j['name'],flush=True);d=root/j['name']
        try:
            assert host()['AC']==1,'AC required'
            with Resident(d,j['family'],j['condition'],'engineering',j['capture']) as s:
                s.complete(inputs['warmups'][j['family']],j['name']+'|warmup',True)
                for t in j['cases']:
                    try:s.complete(t,j['name']+'|'+t['id'])
                    except Exception as e:print('ENGINEERING REQUEST FAILED',t['id'],type(e).__name__,flush=True)
        except Exception as e:
            save(root/(j['name']+'-BLOCK_FAILURE.json'),{'status':'ENGINEERING_BLOCK_FAILURE','job':j['name'],'error':repr(e),'utc':now()});print('ENGINEERING BLOCK FAILURE',j['name'],repr(e),flush=True)
    save(root/'COMPLETE.json',{'utc':now(),'actual_paid_started':len(list(root.rglob('REQUEST_STARTED.json'))),'completed':len(list(root.rglob('COMPLETED.json'))),'lifetimes_seconds':sum(read(p)['seconds'] for p in root.rglob('LIFETIME.json'))})
    print('ENGINEERING FINISHED',flush=True)
if __name__=='__main__':main()
