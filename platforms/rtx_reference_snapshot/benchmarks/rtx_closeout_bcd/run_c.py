"""Paid width/length matrix and instrumentation bridges, all failures retained."""
import json
from close_base import HERE,PHASE2,read,save,sha,head,now
from close_server import Server,measure
from gpu import capture as gpu_capture
from analyze_bcd import signature

def inspect_trace(path,mask,requests,ub,spec):
    dec=[json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if json.loads(s)['event']=='decode']
    starts=0;coverage={};widths={};seen=set()
    for x in dec:
        bit={'target':{'prefill':1,'continuation':2},'draft':{'prefill':4,'continuation':8}}[x['role']][x['phase']]
        active=bool(mask&bit);assert x['scope_mask']==mask and x['scope_active']==active and x['returncode']==0
        assert x['ub_capacity']==ub
        key=x['role']+'_'+x['phase'];seen.add(key)
        if x['role']=='target' and x['positions'][0]==0:assert x['phase']=='prefill';starts+=1
        norm=[g['ne'][1] for g in x['graphs'] if g['name']=='attn_norm-0'];nodes=[g for g in x['graphs'] if g['name']=='hs_attn_query_batch-0']
        assert norm and max(norm)<=ub
        multi=sum(n>1 for n in norm);assert len(nodes)==(multi if active else 0)
        assert all(g['ne'][1]==1 and 1<g['ne'][3]<=ub for g in nodes)
        widths.setdefault(key,[]).extend(norm)
        if multi:
            coverage.setdefault(key,{'multiquery_graphs':0,'constrained_graphs':0});coverage[key]['multiquery_graphs']+=multi;coverage[key]['constrained_graphs']+=len(nodes)
    assert starts==requests,(starts,requests)
    expected={'target_prefill','target_continuation'}|({'draft_prefill','draft_continuation'} if spec else set())
    assert seen==expected and max(widths['target_prefill'])==ub
    return {'status':'PASS','decode_calls':len(dec),'request_prefill_resets':starts,'roles_phases':sorted(seen),'actual_graph_width_ranges':{k:[min(v),max(v)] for k,v in widths.items()},'multiquery_coverage':coverage}

def main(stage):
    source=head();plan=read(HERE/'C_MANIFEST.json');assert plan['inputs_sha256']==sha(HERE/'C_INPUTS.json') and plan['protocol_sha256']==sha(HERE/'PROTOCOL.md')
    exe=HERE/'generated/c-build/bin/llama-server.exe';assert sha(exe)==plan['build_identity']['server_sha256']
    root=HERE/'runs'/stage;root.mkdir(parents=True,exist_ok=False);save(root/'MANIFEST.json',{'stage':stage,'source_commit':source,'plan_sha256':sha(HERE/'C_MANIFEST.json'),'utc':now()})
    inputs=read(HERE/'C_INPUTS.json');byid={t['id']:t for t in inputs};selected=plan['B_selection']['condition'];records=[];proofs=[]
    refs={r['task']:signature(r) for r in read(HERE/'runs/b/RECORDS.json') if r['condition']=='scalar_reference' and r['repetition']==1}
    sessions=[]
    if stage=='c_bridge':
        for c in [{'name':'matched_target','mask':3,'spec':False,'ub':4,'k':0},{**selected,'name':'selected_speculation'}]:
            sessions.append({'name':c['name'],'condition':c,'tasks':[t['id'] for t in read(HERE/'B_INPUTS.json')],'caps':[128],'repetition':1,'width_k':3,'width_ub':4})
        byid={t['id']:t for t in read(HERE/'B_INPUTS.json')}
    elif stage=='c_topology':
        byid={t['id']:t for t in read(PHASE2/'INPUTS.json')}
        for k,ub in plan['B_selection']['widths']:
            for c in [{'name':'matched_target','mask':3,'spec':False,'ub':ub,'k':0},{**selected,'name':'selected_speculation','ub':ub,'k':k}]:
                sessions.append({'name':f'k{k}-{c["name"]}','condition':c,'tasks':['HumanEval/18','HumanEval/31'],'caps':[128],'repetition':1,'width_k':k,'width_ub':ub})
    else:
        assert stage=='c' and read(HERE/'generated/C_ENGINEERING.json')['status']=='PASS'
        sessions=[{**s,'name':f'r{s["repetition"]}-k{s["width_k"]}-{s["condition"]["name"]}'} for s in plan['schedule']]
    for session in sessions:
        c=session['condition'];d=root/session['name'];print('START '+d.name,flush=True)
        with Server(d,c,capture=stage=='c_topology',exe=exe) as server:
            gpu_capture(d/'GPU_PRE.json')
            try:
                for cap in session['caps']:
                    for taskid in session['tasks']:
                        t=byid[taskid];r=measure(server,t,c['name'],session['repetition'],source,cap)
                        r.update({'width_k':session['width_k'],'width_ub':session['width_ub'],'cohort':t.get('cohort','bridge')})
                        p=d/f'cap{cap}-{taskid.replace("/","-")}.json';r['record_relative_path']=p.relative_to(HERE).as_posix()
                        if stage=='c_bridge':r['B_reference_equal']=signature(r)==refs[taskid]
                        save(p,r);records.append(r);print(f'DONE {d.name} cap{cap} {taskid}'+(f' equal={r["B_reference_equal"]}' if stage=='c_bridge' else ''),flush=True)
                        if stage=='c_bridge' and not r['B_reference_equal']:raise RuntimeError('Widened frontend UB4 bridge failed; preserved paid request')
            finally:gpu_capture(d/'GPU_POST.json')
        if stage=='c_topology':proofs.append({'session':session,'proof':inspect_trace(d/'trace.jsonl',c['mask'],3,c['ub'],c['spec'])})
    save(root/'RECORDS.json',records)
    if stage=='c_bridge':save(HERE/'generated/C_BRIDGE.json',{'status':'PASS','requests':len(records),'records_sha256':sha(root/'RECORDS.json')})
    if stage=='c_topology':
        assert read(HERE/'generated/C_BRIDGE.json')['status']=='PASS'
        save(HERE/'generated/C_ENGINEERING.json',{'status':'PASS','requests':len(records),'proofs':proofs,'records_sha256':sha(root/'RECORDS.json')})
    print(f'COMPLETE {stage} {len(records)}',flush=True)

if __name__=='__main__':
    import sys
    main(sys.argv[1])
