"""Bounded full-scope repair confirmation, frozen before paid repair pilot."""
from close_base import HERE,PHASE2,read,save,sha,now,head
from close_server import Server,measure
from analyze_bcd import signature,correctness,summarize
from run_c import inspect_trace
from gpu import capture as gpu_capture
import c2

def prepare():
    pre=read(HERE/'C3_PREOUTPUT_PLAN.json');rows=read(HERE/'runs/c_boundary_trace/RECORDS.json');pilot=[r for r in rows if r['condition']=='all_scopes']
    if not pilot or not all(r['reference_equal'] for r in pilot):
        save(HERE/'generated/C3_SELECTION.json',{'status':'SKIPPED','reason':'The pre-existing full-scope recipe does not repair every frozen failed-pair pilot.','preoutput_plan_sha256':sha(HERE/'C3_PREOUTPUT_PLAN.json')});print('C3 skipped by paid repair gate.',flush=True);return
    pairs=read(HERE/'generated/C_RESULTS.json')['diagnostic_pairs'];k=min(p['k'] for p in pairs);ub=k+1
    assert k in [5,7] and all(p['k']==k for p in pairs)
    tasks=read(HERE/'B_INPUTS.json')+[next(t for t in read(PHASE2/'INPUTS.json') if t['id']==f'HumanEval/{i}') for i in [15,25,18,31]]
    save(HERE/'C3_INPUTS.json',tasks)
    modes=[{'name':'matched_target','mask':3,'spec':False,'ub':4,'k':0},{'name':'anchor_speculation','mask':3,'spec':True,'ub':4,'k':3},
           {'name':'wider_speculation','mask':15,'spec':True,'ub':ub,'k':k},{'name':'ordinary_wider','mask':0,'spec':True,'ub':ub,'k':k}]
    save(HERE/'C3_MANIFEST.json',{'utc':now(),'preoutput_plan_sha256':sha(HERE/'C3_PREOUTPUT_PLAN.json'),'pilot_records_sha256':sha(HERE/'runs/c_boundary_trace/RECORDS.json'),
      'selected_k':k,'selected_mask':15,'selection':'Lowest frozen failing width, pre-existing all-on recipe, only if all paid pilot failures repaired; no speed selection or new mask tuning.',
      'inputs_sha256':sha(HERE/'C3_INPUTS.json'),'conditions':modes,'tasks':[t['id'] for t in tasks],'repetitions':4,'cap':128,'measured_requests':448,'warmups':16,
      'server_sha256':read(HERE/'generated/C_BUILD_IDENTITY.json')['server_sha256'],'long_inputs_sha256':sha(HERE/'C_INPUTS.json'),'long_caps':[256,512],'long_requests':132,'long_warmups':6,
      'scope_probe':{'task':pairs[0]['task'],'caps':[128],'widths':[5,7],'masks':[3,7,11,15],'repetitions':2,'requests':16,'warmups':8,'capture':True,'interpretation':'Four masks conditional on target scopes, one exposed failure probe; not global 16-mask minimality.'}})
    save(HERE/'generated/C3_SELECTION.json',{'status':'RUN','selected_k':k,'selected_mask':15,'manifest_sha256':sha(HERE/'C3_MANIFEST.json')});print(f'C3 repair confirmation selected mask15/k{k}, no speed selection; freeze manifest.',flush=True)

def run():c2.run('c3')
def analyze():c2.analyze('c3')

def extra(stage):
    source=head();plan=read(HERE/'C3_MANIFEST.json');assert plan['preoutput_plan_sha256']==sha(HERE/'C3_PREOUTPUT_PLAN.json')
    inputs=read(HERE/'C_INPUTS.json');byid={t['id']:t for t in inputs};root=HERE/'runs'/stage;root.mkdir(parents=True,exist_ok=False);save(root/'MANIFEST.json',{'utc':now(),'source_commit':source,'plan_sha256':sha(HERE/'C3_MANIFEST.json')});sessions=[];records=[]
    if stage=='c3_long':
        for rep in [1,2]:
            modes=[{'name':'scalar_reference','mask':0,'spec':False,'ub':1,'k':0},{'name':'matched_target','mask':3,'spec':False,'ub':plan['selected_k']+1,'k':0},next(c for c in plan['conditions'] if c['name']=='wider_speculation')]
            modes=modes[rep-1:]+modes[:rep-1]
            for mode in modes:sessions.append({'name':f'r{rep}-{mode["name"]}','condition':mode,'tasks':[t['id'] for t in inputs[rep-1:]+inputs[:rep-1]],'caps':[256,512] if rep==1 else [512,256],'rep':rep})
    else:
        assert stage=='c3_scopes';s=plan['scope_probe']
        for k in s['widths']:
            for mask in s['masks']:sessions.append({'name':f'k{k}-mask{mask}','condition':{'name':f'mask{mask}','mask':mask,'spec':True,'ub':k+1,'k':k},'tasks':[s['task']],'caps':[128],'rep':None})
    for session in sessions:
        d=root/session['name'];c=session['condition'];print('START '+d.name,flush=True)
        with Server(d,c,capture=stage=='c3_scopes',exe=HERE/'generated/c-build/bin/llama-server.exe') as server:
            gpu_capture(d/'GPU_PRE.json')
            try:
                for rep in ([1,2] if stage=='c3_scopes' else [session['rep']]):
                    for cap in session['caps']:
                        for tid in session['tasks']:
                            r=measure(server,byid[tid],c['name'],rep,source,cap);r.update({'width_k':c['k'] if c['spec'] else plan['selected_k'],'width_ub':c['ub'],'cohort':byid[tid]['cohort']})
                            p=d/f'r{rep}-cap{cap}-{tid.replace("/","-")}.json';r['record_relative_path']=p.relative_to(HERE).as_posix();save(p,r);records.append(r);print(f'DONE {d.name} {tid} cap{cap} r{rep}',flush=True)
            finally:gpu_capture(d/'GPU_POST.json')
        if stage=='c3_scopes':save(d/'TOPOLOGY.json',inspect_trace(d/'trace.jsonl',c['mask'],3,c['ub'],True))
    save(root/'RECORDS.json',records);print(f'COMPLETE {stage} {len(records)}',flush=True)

def long():extra('c3_long')
def scopes():extra('c3_scopes')

def analyze_extra():
    rows=read(HERE/'runs/c3_long/RECORDS.json');assert len(rows)==132;inputs=read(HERE/'C_INPUTS.json');tasks=[t['id'] for t in inputs];results=[]
    for cap in [256,512]:
        rr=[r for r in rows if r['requested_cap']==cap];anchors={r['task']:signature(r) for r in read(HERE/'runs/c/RECORDS.json') if r['requested_cap']==cap and r['condition']=='scalar_reference' and r['width_k']==1 and r['repetition']==1}
        stable,q,details,refs=correctness(rr,tasks,['scalar_reference','matched_target','wider_speculation'],2,anchors)
        results.append({'cap':cap,'reference_stable':stable,'qualification':q,'details':details,'cost':summarize(rr,tasks,'wider_speculation','matched_target',q['matched_target'] and q['wider_speculation'])})
    scopes=read(HERE/'runs/c3_scopes/RECORDS.json');assert len(scopes)==16;probe=read(HERE/'C3_MANIFEST.json')['scope_probe']['task']
    ref=next(r for r in read(HERE/'runs/b/RECORDS.json') if r['task']==probe and r['condition']=='scalar_reference' and r['repetition']==1);scope_results=[]
    for k in [5,7]:
        for mask in [3,7,11,15]:
            rr=[r for r in scopes if r['k']==k and r['mask']==mask];assert len(rr)==2
            scope_results.append({'task':probe,'k':k,'mask':mask,'reference_equal':all(signature(r)==signature(ref) for r in rr),'repeat_stable':len({signature(r) for r in rr})==1,'matching_requests':sum(signature(r)==signature(ref) for r in rr)})
    save(HERE/'generated/C3_EXTRA_RESULTS.json',{'long_requests':132,'long_warmups':6,'long_configurations':results,'scope_requests':16,'scope_warmups':8,'scope_results':scope_results});print({'long_qualification':[r['qualification'] for r in results],'scope_results':scope_results},flush=True)

if __name__=='__main__':
    import sys
    globals()[sys.argv[1]]()
