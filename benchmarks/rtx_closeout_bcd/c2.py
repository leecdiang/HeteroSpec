"""Conditional, output-selected wider-width confirmation; never speed selection."""
from close_base import HERE,PHASE2,read,save,sha,now,head
from close_server import Server,measure
from analyze_bcd import signature,summarize
from gpu import capture as gpu_capture

def prepare():
    plan=read(HERE/'C2_PREOUTPUT_PLAN.json');results=read(HERE/'generated/C_RESULTS.json');eligible=[]
    for k in [5,7]:
        configs=[c for c in results['configurations'] if c['k']==k]
        if len(configs)==3 and all(c['reference_stable'] and c['qualification']['matched_target'] and c['qualification']['selected_speculation'] for c in configs):eligible.append(k)
    if not eligible:
        save(HERE/'generated/C2_SELECTION.json',{'status':'SKIPPED','reason':'No wider width qualifies both full cohorts at all three caps.','preoutput_plan_sha256':sha(HERE/'C2_PREOUTPUT_PLAN.json')});print('C2 skipped by output gate.',flush=True);return
    k=max(eligible);ub=k+1;mask=read(HERE/'generated/C_SELECTION.json')['condition']['mask']
    tasks=read(HERE/'B_INPUTS.json')+[next(t for t in read(PHASE2/'INPUTS.json') if t['id']==f'HumanEval/{i}') for i in plan['old_probes']]
    save(HERE/'C2_INPUTS.json',tasks)
    modes=[{'name':'matched_target','mask':3,'spec':False,'ub':4,'k':0},
           {'name':'anchor_speculation','mask':mask,'spec':True,'ub':4,'k':3},
           {'name':'wider_speculation','mask':mask,'spec':True,'ub':ub,'k':k},
           {'name':'ordinary_wider','mask':0,'spec':True,'ub':ub,'k':k}]
    save(HERE/'C2_MANIFEST.json',{'utc':now(),'preoutput_plan_sha256':sha(HERE/'C2_PREOUTPUT_PLAN.json'),'C_results_sha256':sha(HERE/'generated/C_RESULTS.json'),
         'eligible_widths':eligible,'selected_k':k,'selection':'Highest whole-panel qualifying width at all three caps, without inspecting costs.',
         'inputs_sha256':sha(HERE/'C2_INPUTS.json'),'conditions':modes,'tasks':[t['id'] for t in tasks],'repetitions':4,'cap':128,'measured_requests':448,'warmups':16,
         'server_sha256':read(HERE/'generated/C_BUILD_IDENTITY.json')['server_sha256'],'reference':'Already-paid independent repeat-stable B scalar reference and immutable old scalar references; never supplied online.'})
    save(HERE/'generated/C2_SELECTION.json',{'status':'RUN','selected_k':k,'manifest_sha256':sha(HERE/'C2_MANIFEST.json')});print(f'C2 selected k{k} by outputs only; freeze new manifest before running.',flush=True)

def references():
    refs={r['task']:signature(r) for r in read(HERE/'runs/b/RECORDS.json') if r['condition']=='scalar_reference' and r['repetition']==1}
    refs.update({t['id']:(tuple(t['original_reference_ids']),t['original_endpoint']) for t in read(HERE/'C2_INPUTS.json') if t['id'].startswith('HumanEval/')})
    return refs

def run():
    source=head();plan=read(HERE/'C2_MANIFEST.json');assert plan['inputs_sha256']==sha(HERE/'C2_INPUTS.json') and plan['preoutput_plan_sha256']==sha(HERE/'C2_PREOUTPUT_PLAN.json')
    exe=HERE/'generated/c-build/bin/llama-server.exe';assert sha(exe)==plan['server_sha256']
    root=HERE/'runs/c2';root.mkdir(parents=True,exist_ok=False);save(root/'MANIFEST.json',{'utc':now(),'source_commit':source,'plan_sha256':sha(HERE/'C2_MANIFEST.json')})
    tasks=read(HERE/'C2_INPUTS.json');refs=references();records=[]
    for rep in range(4):
        cs=plan['conditions'];cs=cs[rep:]+cs[:rep];ts=tasks[rep:]+tasks[:rep]
        for c in cs:
            d=root/f'r{rep+1}-{c["name"]}';print('START '+d.name,flush=True)
            with Server(d,c,exe=exe) as s:
                gpu_capture(d/'GPU_PRE.json')
                try:
                    for t in ts:
                        r=measure(s,t,c['name'],rep+1,source,128);r['reference_equal']=signature(r)==refs[t['id']]
                        p=d/(t['id'].replace('/','-')+'.json');r['record_relative_path']=p.relative_to(HERE).as_posix();save(p,r);records.append(r)
                        print(f'DONE {d.name} {t["id"]} equal={r["reference_equal"]}',flush=True)
                finally:gpu_capture(d/'GPU_POST.json')
    save(root/'RECORDS.json',records);print('COMPLETE c2 448',flush=True)

def analyze():
    rows=read(HERE/'runs/c2/RECORDS.json');plan=read(HERE/'C2_MANIFEST.json');assert len(rows)==448;refs=references();q={};details=[]
    for c in plan['conditions']:
        name=c['name'];q[name]=True
        for task in plan['tasks']:
            rs=[r for r in rows if r['task']==task and r['condition']==name];assert len(rs)==4 and {r['repetition'] for r in rs}=={1,2,3,4}
            equal=all(signature(r)==refs[task] for r in rs);q[name]=q[name] and equal
            details.append({'task':task,'condition':name,'full_equal':equal,'repeat_stable':len({signature(r) for r in rs})==1,'reference_match_requests':sum(signature(r)==refs[task] for r in rs)})
    costs=[summarize(rows,plan['tasks'],a,b,q[a] and q[b]) for a,b in [('wider_speculation','anchor_speculation'),('wider_speculation','matched_target'),('anchor_speculation','matched_target'),('wider_speculation','ordinary_wider')]]
    cohorts={}
    for label in ['MBPP','HumanEval']:
        ids=[t for t in plan['tasks'] if t.startswith(label+'/')];cq={c:all(d['full_equal'] for d in details if d['task'] in ids and d['condition']==c) for c in q}
        cohorts[label]={'qualification':cq,'costs':[summarize(rows,ids,a,b,cq[a] and cq[b]) for a,b in [('wider_speculation','anchor_speculation'),('wider_speculation','matched_target')]]}
    out={'stage':'C2','selected_k':plan['selected_k'],'requests':448,'warmups':16,'records_sha256':sha(HERE/'runs/c2/RECORDS.json'),'qualification':q,'details':details,'costs':costs,'cohorts':cohorts,
         'interpretation':'Conditional configuration confirmation after C; the sixteen B tasks outside the C primary cohort had no wider-width outputs used for selection. This is not a new unused-task claim.'}
    save(HERE/'generated/C2_RESULTS.json',out);print({'qualification':q,'costs':[(c['numerator'],c['denominator'],c['generation']['task_median_geomean_speedup'],c['wall']['task_median_geomean_speedup']) for c in costs]},flush=True)

if __name__=='__main__':
    import sys
    globals()[sys.argv[1]]()
