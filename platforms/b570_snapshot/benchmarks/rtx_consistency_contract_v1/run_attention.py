"""Eight fixed-reference qualification trajectories, with all failures retained."""
import json,os,subprocess,time
from run import HERE,OLD,ASSET,read,save,sha,now,native_module

def main():
    contracts=read(HERE/'INPUT_CONTRACTS.json');m=native_module();results=[]
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=HERE,text=True).strip()
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip()
    for task in [15,25,18,31]:
        for condition in ['reference','attention_candidate']:
            d=HERE/f'runs/attention/HumanEval-{task}-{condition}'
            if d.exists():raise RuntimeError('Retained attempt exists; no automatic repeat')
            d.mkdir(parents=True)
            template='TARGET_REFERENCE' if condition=='reference' else 'RTX_BATCHED_K2'
            cmd=m.templates(m.paths(ASSET))[template]
            executable=OLD/'native-build/bin/llama-cli.exe' if condition=='reference' else HERE/'generated/build/bin/llama-cli.exe'
            cmd[0]=str(executable);cmd+=['--threads','24','--threads-batch','24']
            mapping={'{prompt}':contracts[str(task)]['prompt'],'{native_log}':str(d/'native.log'),'{transcript}':str(d/'transcript.txt')}
            cmd=[mapping.get(s,s) for s in cmd]
            env={k:os.environ[k] for k in ['SystemRoot','WINDIR','TEMP','TMP','PATH','COMSPEC','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE'] if k in os.environ}
            env.update(HS_NATIVE_CAPTURE=str(d/'trace.jsonl'),LLAMA_BATCH_DEBUG='1')
            if condition!='reference':env['HS_ATTENTION_SINGLE_QUERY']='1'
            start={'task':task,'condition':condition,'utc':now(),'source_commit':head,'command':cmd,'frontend_sha256':sha(executable)}
            save(d/'START.json',start);t=time.monotonic()
            try:
                with (d/'stdout.log').open('wb') as so,(d/'stderr.log').open('wb') as se:
                    p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=so,stderr=se,cwd=d,env=env)
                    save(d/'PROCESS.json',{'pid':p.pid,'started_utc':now()})
                    try:rc=p.wait(timeout=300)
                    except subprocess.TimeoutExpired:p.kill();p.wait();raise
                if rc:raise RuntimeError('Frontend exit '+str(rc))
                parsed=m.parse_capture(d/'native.log',template)
                r={**start,'ids':parsed['generated_ids'],'endpoint':parsed['termination'],'elapsed_seconds':time.monotonic()-t,'valid':True}
                if condition=='reference':
                    hist=read(OLD/f'formal/HumanEval-{task}-R-r1/result.json')
                    assert r['ids']==hist['ids'] and r['endpoint']==hist['endpoint']
                else:
                    ref=read(HERE/f'runs/attention/HumanEval-{task}-reference/RESULT.json')
                    r['reference_equal']=r['ids']==ref['ids'] and r['endpoint']==ref['endpoint']
                    r['first_difference']=next((i for i,(a,b) in enumerate(zip(r['ids'],ref['ids'])) if a!=b),None)
                    if r['first_difference'] is None and len(r['ids'])!=len(ref['ids']):r['first_difference']=min(len(r['ids']),len(ref['ids']))
                    trace=[json.loads(s) for s in (d/'trace.jsonl').read_text().splitlines()]
                    graphs=[g for x in trace if x['event']=='decode' for g in x['graphs']]
                    r['single_query_attention_nodes']=sum(g['name']=='hs_attn_single_query-0' for g in graphs)
                    r['batched_layer_norm_nodes']=sum(g['name']=='attn_norm-0' and g['ne'][1]==2 for g in graphs)
                    assert r['single_query_attention_nodes']>0 and r['batched_layer_norm_nodes']>0
                r['files']={p.relative_to(d).as_posix():sha(p) for p in d.rglob('*') if p.is_file()};save(d/'RESULT.json',r)
                results.append(r)
                print(json.dumps({k:r.get(k) for k in ['task','condition','reference_equal','first_difference','single_query_attention_nodes','batched_layer_norm_nodes','elapsed_seconds']}),flush=True)
            except Exception as e:
                save(d/'FAILURE.json',{**start,'error':repr(e)});raise
    save(HERE/'generated/analysis/ATTENTION_QUALIFICATION.json',{'complete_trajectories':8,
        'status':'PASS_EXPOSED_PROBE' if all(r.get('reference_equal',True) for r in results) else 'FAIL_REFERENCE_GATE',
        'candidate_matches':sum(r.get('reference_equal',False) for r in results),
        'results':results,'performance_measured':False})
if __name__=='__main__':main()
