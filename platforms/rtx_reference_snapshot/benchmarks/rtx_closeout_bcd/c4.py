"""Separate logical lookahead from the already-qualified numerical microbatch."""
from close_base import HERE,PHASE2,read,save,sha,head,now
from close_server import Server,measure
from analyze_bcd import signature
from run_c import inspect_trace
import c2,c3

def prepare_pilot():
    assert not (HERE/'runs/c4_pilot').exists()
    tasks=read(HERE/'B_INPUTS.json')+[next(t for t in read(PHASE2/'INPUTS.json') if t['id']==f'HumanEval/{i}') for i in [15,25,18,31]]
    save(HERE/'C4_INPUTS.json',tasks)
    save(HERE/'C4_PILOT_MANIFEST.json',{'utc':now(),'preoutput_plan_sha256':sha(HERE/'C4_PREOUTPUT_PLAN.json'),'inputs_sha256':sha(HERE/'C4_INPUTS.json'),
       'tasks':[t['id'] for t in tasks],'lookaheads':[3,5,7],'ub':4,'mask':3,'cap':128,'repetitions':2,'requests':168,'warmups':6,
       'capture':True,'schedule':'rep1 k3,k5,k7;rep2 k7,k5,k3; tasks rotate one position in second repetition',
       'server_sha256':read(HERE/'generated/C_BUILD_IDENTITY.json')['server_sha256'],'reference':'Paid B scalar references and immutable old probe R; never online inputs.'})
    print('Freeze C4 numerical-microbatch isolation pilot:168+6.',flush=True)

def pilot():
    source=head();plan=read(HERE/'C4_PILOT_MANIFEST.json');assert plan['preoutput_plan_sha256']==sha(HERE/'C4_PREOUTPUT_PLAN.json') and plan['inputs_sha256']==sha(HERE/'C4_INPUTS.json')
    exe=HERE/'generated/c-build/bin/llama-server.exe';assert sha(exe)==plan['server_sha256'];tasks=read(HERE/'C4_INPUTS.json');refs=c2.references('c4')
    root=HERE/'runs/c4_pilot';root.mkdir(parents=True,exist_ok=False);save(root/'MANIFEST.json',{'utc':now(),'source_commit':source,'plan_sha256':sha(HERE/'C4_PILOT_MANIFEST.json')});records=[];proofs=[]
    for rep in [1,2]:
        for k in ([3,5,7] if rep==1 else [7,5,3]):
            c={'name':f'k{k}_ub4','mask':3,'spec':True,'ub':4,'k':k};d=root/f'r{rep}-k{k}';print('START '+d.name,flush=True)
            with Server(d,c,capture=True,exe=exe) as s:
                for t in tasks[rep-1:]+tasks[:rep-1]:
                    r=measure(s,t,c['name'],rep,source,128);r['reference_equal']=signature(r)==refs[t['id']]
                    p=d/(t['id'].replace('/','-')+'.json');r['record_relative_path']=p.relative_to(HERE).as_posix();save(p,r);records.append(r)
                    print(f'DONE {d.name} {t["id"]} equal={r["reference_equal"]}',flush=True)
            proof=inspect_trace(d/'trace.jsonl',3,29,4,True)
            proof['actual_largest_target_caller_batch']=max(x['caller_batch'] for x in __import__('json').loads('['+','.join(d.joinpath('trace.jsonl').read_text().splitlines())+']') if x['event']=='decode' and x['role']=='target' and x['phase']=='continuation')
            proofs.append({'repetition':rep,'k':k,'proof':proof})
    save(root/'RECORDS.json',records);save(HERE/'generated/C4_PILOT_PROOFS.json',proofs);print('COMPLETE c4_pilot168',flush=True)

def select():
    rows=read(HERE/'runs/c4_pilot/RECORDS.json');assert len(rows)==168;tasks=read(HERE/'C4_INPUTS.json');refs=c2.references('c4');q={};details=[]
    for k in [3,5,7]:
        q[k]=True
        for t in tasks:
            rr=[r for r in rows if r['k']==k and r['task']==t['id']];assert len(rr)==2
            equal=all(signature(r)==refs[t['id']] for r in rr);q[k]=q[k] and equal
            details.append({'task':t['id'],'k':k,'full_equal':equal,'repeat_stable':len({signature(r) for r in rr})==1})
    eligible=[k for k in [5,7] if q[k] and q[3]]
    save(HERE/'generated/C4_PILOT_RESULTS.json',{'requests':168,'warmups':6,'qualification':q,'details':details,'proofs':read(HERE/'generated/C4_PILOT_PROOFS.json'),'records_sha256':sha(HERE/'runs/c4_pilot/RECORDS.json')})
    if not eligible:
        save(HERE/'generated/C4_SELECTION.json',{'status':'SKIPPED','reason':'No higher logical lookahead qualifies all28 pilot tasks at fixed UB4.','preoutput_plan_sha256':sha(HERE/'C4_PREOUTPUT_PLAN.json')});print('C4 higher confirmation skipped.',flush=True);return
    k=max(eligible);modes=[{'name':'matched_target','mask':3,'spec':False,'ub':4,'k':0},{'name':'anchor_speculation','mask':3,'spec':True,'ub':4,'k':3},
       {'name':'wider_speculation','mask':3,'spec':True,'ub':4,'k':k},{'name':'ordinary_wider','mask':0,'spec':True,'ub':4,'k':k}]
    save(HERE/'C4_MANIFEST.json',{'utc':now(),'preoutput_plan_sha256':sha(HERE/'C4_PREOUTPUT_PLAN.json'),'pilot_results_sha256':sha(HERE/'generated/C4_PILOT_RESULTS.json'),
       'selected_k':k,'selected_mask':3,'selection':'Highest full-reference qualifying higher lookahead at fixed numerical UB4; no speed selection.',
       'inputs_sha256':sha(HERE/'C4_INPUTS.json'),'conditions':modes,'tasks':[t['id'] for t in tasks],'repetitions':4,'cap':128,'measured_requests':448,'warmups':16,
       'server_sha256':read(HERE/'generated/C_BUILD_IDENTITY.json')['server_sha256'],'long_inputs_sha256':sha(HERE/'C_INPUTS.json'),'long_caps':[256,512],'long_requests':132,'long_warmups':6})
    save(HERE/'generated/C4_SELECTION.json',{'status':'RUN','selected_k':k,'manifest_sha256':sha(HERE/'C4_MANIFEST.json')});print({'pilot_qualification':q,'selected_k':k},flush=True)

def run():c2.run('c4')
def analyze():c2.analyze('c4')

def long():
    source=head();plan=read(HERE/'C4_MANIFEST.json');assert plan['long_inputs_sha256']==sha(HERE/'C_INPUTS.json')
    tasks=read(HERE/'C_INPUTS.json');root=HERE/'runs/c4_long';root.mkdir(parents=True,exist_ok=False);save(root/'MANIFEST.json',{'utc':now(),'source_commit':source,'plan_sha256':sha(HERE/'C4_MANIFEST.json')});records=[]
    from gpu import capture as gpu_capture
    for rep in [1,2]:
        cs=[{'name':'scalar_reference','mask':0,'spec':False,'ub':1,'k':0},{'name':'matched_target','mask':3,'spec':False,'ub':4,'k':0},next(c for c in plan['conditions'] if c['name']=='wider_speculation')];cs=cs[rep-1:]+cs[:rep-1]
        for c in cs:
            d=root/f'r{rep}-{c["name"]}';print('START '+d.name,flush=True)
            with Server(d,c,exe=HERE/'generated/c-build/bin/llama-server.exe') as s:
                gpu_capture(d/'GPU_PRE.json')
                try:
                    for cap in ([256,512] if rep==1 else [512,256]):
                        for t in tasks[rep-1:]+tasks[:rep-1]:
                            r=measure(s,t,c['name'],rep,source,cap);r.update({'width_k':plan['selected_k'],'width_ub':4,'cohort':t['cohort']})
                            p=d/f'cap{cap}-{t["id"].replace("/","-")}.json';r['record_relative_path']=p.relative_to(HERE).as_posix();save(p,r);records.append(r);print(f'DONE {d.name} cap{cap} {t["id"]}',flush=True)
                finally:gpu_capture(d/'GPU_POST.json')
    save(root/'RECORDS.json',records);print('COMPLETE c4_long132',flush=True)

def analyze_long():
    from analyze_bcd import correctness,summarize
    rows=read(HERE/'runs/c4_long/RECORDS.json');assert len(rows)==132;tasks=[t['id'] for t in read(HERE/'C_INPUTS.json')];results=[]
    for cap in [256,512]:
        rr=[r for r in rows if r['requested_cap']==cap];anchors={r['task']:signature(r) for r in read(HERE/'runs/c/RECORDS.json') if r['requested_cap']==cap and r['condition']=='scalar_reference' and r['width_k']==1 and r['repetition']==1}
        stable,q,details,refs=correctness(rr,tasks,['scalar_reference','matched_target','wider_speculation'],2,anchors)
        results.append({'cap':cap,'reference_stable':stable,'qualification':q,'details':details,'cost':summarize(rr,tasks,'wider_speculation','matched_target',q['matched_target'] and q['wider_speculation'])})
    save(HERE/'generated/C4_LONG_RESULTS.json',{'requests':132,'warmups':6,'configurations':results});print([x['qualification'] for x in results],flush=True)

if __name__=='__main__':
    import sys
    globals()[sys.argv[1]]()
