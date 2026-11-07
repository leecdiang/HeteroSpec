"""Full-output bridge plus actual role/phase graph coverage."""
import inspect,json,subprocess
from base import HERE,PHASE1,ASSET,read,save,sha,now,head,env,native_module
from server import Server,measure

def inspect_trace(path,mask,requests):
    trace=[json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]
    dec=[x for x in trace if x['event']=='decode'];coverage={};starts=0
    for x in dec:
        assert x['scope_mask']==mask and x['phase'] in ['prefill','continuation']
        bit={'target':{'prefill':1,'continuation':2},'draft':{'prefill':4,'continuation':8}}[x['role']][x['phase']]
        active=bool(mask&bit);assert x['scope_active']==active
        if x['role']=='target' and x['positions'][0]==0:
            assert x['phase']=='prefill';starts+=1
        # Multi-token graphs are visible from layer0 normalization, not caller capacity.
        multi=any(g['name']=='attn_norm-0' and g['ne'][1]>1 for g in x['graphs'])
        nodes=[g for g in x['graphs'] if g['name']=='hs_attn_query_batch-0' and g['ne'][1]==1 and g['ne'][3]>1]
        if multi:
            assert bool(nodes)==active,(mask,x['role'],x['phase'])
            coverage.setdefault(x['role']+'_'+x['phase'],{'calls':0,'constrained_calls':0})
            coverage[x['role']+'_'+x['phase']]['calls']+=1
            coverage[x['role']+'_'+x['phase']]['constrained_calls']+=bool(nodes)
    assert starts==requests and len(coverage)==4,('Scope coverage incomplete',starts,coverage)
    return {'decode_calls':len(dec),'request_prefill_resets':starts,'actual_multiquery_scope_coverage':coverage}

def main():
    source=head();m=native_module();src=inspect.getsource(m.parse_capture)
    a="    ub = 2 if condition in ('RTX_BATCHED_K2','H1_TARGET_UB2') else 1";assert src.count(a)==1
    namespace=vars(m).copy();exec(compile(src.replace(a,'    ub = 4'),'<scope-bridge-native-parser>','exec'),namespace)
    bindings=read(HERE/'SOURCE_BINDINGS.json');records=[]
    root=HERE/'runs/engineering';root.mkdir(parents=True,exist_ok=False)
    save(root/'MANIFEST.json',{'source_commit':source,'cli_cap':8,'resident_request_cap':8,'warmups':4,
                              'protocol_sha256':sha(HERE/'MASTER_PROTOCOL.md'),'build_identity':read(HERE/'generated/BUILD_IDENTITY.json')})
    for task in [15,25,18,31]:
        for kind in ['old','new']:
            d=root/f'HumanEval-{task}-{kind}';d.mkdir()
            exe=(PHASE1 if kind=='old' else HERE)/'generated/build/bin/llama-cli.exe'
            cmd=m.templates(m.paths(ASSET))['RTX_BATCHED_K2'];cmd[0]=str(exe)
            cmd[cmd.index('--ubatch-size')+1]='4';cmd[cmd.index('--spec-draft-n-max')+1]='3';cmd+=['--threads','24','--threads-batch','24']
            mapping={'{prompt}':bindings['native_contracts'][str(task)]['prompt'],'{native_log}':str(d/'native.log'),'{transcript}':str(d/'transcript.txt')}
            cmd=[mapping.get(t,t) for t in cmd];start={'task':task,'kind':kind,'source_commit':source,'command':cmd,'frontend_sha256':sha(exe),'utc':now()}
            save(d/'START.json',start)
            with (d/'stdout.log').open('wb') as so,(d/'stderr.log').open('wb') as se:
                p=subprocess.Popen(cmd,stdout=so,stderr=se,stdin=subprocess.DEVNULL,cwd=d,env=env(None if kind=='old' else 15,d/'trace.jsonl'),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                save(d/'PROCESS.json',{'pid':p.pid,'utc':now()})
                try:rc=p.wait(timeout=300)
                except subprocess.TimeoutExpired:p.kill();p.wait();raise
            assert rc==0
            x=namespace['parse_capture'](d/'native.log','RTX_BATCHED_K2')
            taskrec=next(t for t in read(HERE/'INPUTS.json') if t['id']==f'HumanEval/{task}')
            assert x['generated_ids']==taskrec['original_reference_ids'] and x['termination']==taskrec['original_endpoint']
            r={**start,'ids':x['generated_ids'],'endpoint':x['termination'],'valid':True,'original_reference_equal':True}
            if kind=='new':r['scope_trace']=inspect_trace(d/'trace.jsonl',15,1)
            r['files']={p.relative_to(d).as_posix():sha(p) for p in d.rglob('*') if p.is_file()};save(d/'RESULT.json',r);records.append(r)
            print(f'BRIDGE {task} {kind} equal=True',flush=True)
    task=next(t for t in read(HERE/'INPUTS.json') if t['id']=='HumanEval/31')
    selective=[]
    for mask in [3,12,5,10]:
        d=root/f'scope-{mask}'
        with Server(d,mask,capture=True) as s:
            rr=[]
            for rep in [1,2]:
                r=measure(s,task,f'mask{mask}',rep,source);save(d/f'REQUEST-{rep}.json',r);rr.append(r)
        assert rr[0]['response']['tokens']==rr[1]['response']['tokens'] and rr[0]['endpoint']==rr[1]['endpoint']
        proof=inspect_trace(d/'trace.jsonl',mask,3);selective.append({'mask':mask,'proof':proof,'original_reference_equal':[r['original_reference_equal'] for r in rr]})
        print(f'SCOPE {mask} actual_graph_coverage=PASS',flush=True)
    save(HERE/'generated/ENGINEERING_QUALIFICATION.json',{'status':'PASS','cli_complete_trajectories':8,'resident_requests':8,'excluded_warmups':4,
         'source_commit':source,'records':records,'selective_scope_checks':selective})

if __name__=='__main__':main()
