"""Same constrained prefill for both conditions; disabled native observation."""
import hashlib,inspect,json,os,subprocess,time,urllib.error,urllib.request
from pathlib import Path
from run import HERE,ASSET,read,save,sha,now,native_module

def clean_head():
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=HERE,text=True).strip()
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip()

def environment():
    env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','LLAMA_ARG_','LLAMA_BATCH_DEBUG','GGML_','CUDA_'))}
    env['HS_ATTENTION_QUERY_BATCH']='1'
    return env

def qualification():
    head=clean_head();contracts=read(HERE/'INPUT_CONTRACTS.json');m=native_module();results=[]
    source=inspect.getsource(m.parse_capture)
    line="    ub = 2 if condition in ('RTX_BATCHED_K2','H1_TARGET_UB2') else 1"
    assert source.count(line)==1
    namespace=vars(m).copy();exec(compile(source.replace(line,'    ub = 4'),'<native-parser-matched-UB4>','exec'),namespace)
    for task in [15,25,18,31]:
        for condition in ['target','query_batch_k3']:
            d=HERE/f'runs/matched-qualification/HumanEval-{task}-{condition}';d.mkdir(parents=True,exist_ok=False)
            label='TARGET_REFERENCE' if condition=='target' else 'RTX_BATCHED_K2'
            cmd=m.templates(m.paths(ASSET))[label];cmd[0]=str(HERE/'generated/build/bin/llama-cli.exe')
            cmd[cmd.index('--ubatch-size')+1]='4'
            if condition!='target':cmd[cmd.index('--spec-draft-n-max')+1]='3'
            cmd+=['--threads','24','--threads-batch','24']
            mapping={'{prompt}':contracts[str(task)]['prompt'],'{native_log}':str(d/'native.log'),'{transcript}':str(d/'transcript.txt')}
            cmd=[mapping.get(s,s) for s in cmd];env=environment()
            start={'task':task,'condition':condition,'source_commit':head,'command':cmd,'utc':now(),
                   'frontend_sha256':sha(cmd[0]),'capture_disabled':True,'attention_mode':'query_batch'}
            save(d/'START.json',start)
            try:
                with (d/'stdout.log').open('wb') as so,(d/'stderr.log').open('wb') as se:
                    p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=so,stderr=se,cwd=d,env=env,
                                       creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                    save(d/'PROCESS.json',{'pid':p.pid,'utc':now()})
                    try:rc=p.wait(timeout=300)
                    except subprocess.TimeoutExpired:p.kill();p.wait();raise
                if rc:raise RuntimeError('Native candidate exit '+str(rc))
                x=namespace['parse_capture'](d/'native.log',label)
                ref=read(HERE/f'runs/attention/HumanEval-{task}-reference/RESULT.json')
                r={**start,'ids':x['generated_ids'],'endpoint':x['termination'],'valid':True,
                   'reference_equal':x['generated_ids']==ref['ids'] and x['termination']==ref['endpoint']}
                r['files']={p.relative_to(d).as_posix():sha(p) for p in d.rglob('*') if p.is_file()}
                save(d/'RESULT.json',r);results.append(r)
                print(json.dumps({'task':task,'condition':condition,'reference_equal':r['reference_equal'],'ids':len(r['ids'])}),flush=True)
            except Exception as e:save(d/'FAILURE.json',{**start,'error':repr(e)});raise
    save(HERE/'generated/analysis/MATCHED_QUALIFICATION.json',{'status':'PASS_EXPOSED_PROBE' if all(r['reference_equal'] for r in results) else 'BLOCKED',
         'complete_trajectories':8,'results':results})

def cost():
    assert read(HERE/'generated/analysis/MATCHED_QUALIFICATION.json')['status']=='PASS_EXPOSED_PROBE'
    head=clean_head();out=HERE/'runs/cost-matched';out.mkdir(exist_ok=False)
    exe=HERE/'generated/build/bin/llama-server.exe';inputs=read(HERE/'COST_INPUTS.json');reps=4;conditions=['target','query_batch_k3']
    base=[str(exe),'--model',str(ASSET/'models/gguf/Qwen3-8B-Q8_0.gguf'),'--device','CUDA0','--n-gpu-layers','all',
          '--fit','off','--ctx-size','4096','--batch-size','2048','--ubatch-size','4','--flash-attn','off','--parallel','1',
          '--threads','24','--threads-batch','24','--cache-ram','0','--host','127.0.0.1','--port','18763',
          '--no-webui','--no-warmup','--no-cache-prompt']
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(route,body=None,timeout=120):
        req=urllib.request.Request('http://127.0.0.1:18763'+route,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with opener.open(req,timeout=timeout) as r:return json.load(r)
    def completion(prompt,cap):
        return request('/completion',{'prompt':prompt,'n_predict':cap,'temperature':0,'top_k':0,'top_p':1,'min_p':0,
                                     'seed':123,'cache_prompt':False,'return_tokens':True,'stream':False})
    save(out/'MANIFEST.json',{'source_commit':head,'runner_sha256':sha(Path(__file__)),'inputs_sha256':sha(HERE/'COST_INPUTS.json'),
         'server_sha256':sha(exe),'cuda_sha256':sha(HERE/'generated/build/bin/ggml-cuda.dll'),'base_command':base,
         'conditions':conditions,'repetitions':reps,'started_utc':now(),'measured_request_cap':152,'excluded_warmups':8,
         'capture_disabled':True,'observer_fast_bypass':True,'both_conditions_attention_mode':'query_batch'})
    records=[]
    for rep in range(reps):
        for condition in (conditions if rep%2==0 else list(reversed(conditions))):
            prefix=f'r{rep+1}_{condition}';cmd=base.copy();env=environment()
            if condition!='target':
                cmd+=['--spec-type','draft-simple','--model-draft',str(ASSET/'models/gguf/Qwen3-0.6B-Q8_0.gguf'),
                      '--spec-draft-device','CUDA0','--spec-draft-ngl','all','--spec-draft-n-max','3','--spec-draft-n-min','0',
                      '--spec-draft-threads','24','--spec-draft-threads-batch','24']
            save(out/(prefix+'_COMMAND.json'),{'command':cmd,'attention_mode':'query_batch','capture_disabled':True})
            print('START '+prefix,flush=True)
            with (out/(prefix+'.log')).open('wb') as log:
                p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                save(out/(prefix+'_PROCESS.json'),{'pid':p.pid,'utc':now()})
                try:
                    deadline=time.monotonic()+120
                    while True:
                        if p.poll() is not None:raise RuntimeError('Server exited '+str(p.returncode))
                        try:
                            if request('/health',timeout=2).get('status')=='ok':break
                        except (OSError,urllib.error.URLError):pass
                        if time.monotonic()>deadline:raise RuntimeError('Server readiness timeout')
                        time.sleep(.5)
                    warm='<|im_start|>user\nWrite Python code to add two integers.<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
                    save(out/(prefix+'_WARMUP.json'),completion(warm,32))
                    for task in inputs[rep:]+inputs[:rep]:
                        t=time.perf_counter();response=completion(task['formatted_prompt'],128);wall=1000*(time.perf_counter()-t)
                        ids=response['tokens'];assert ids and len(ids)==response['tokens_predicted'] and len(ids)<=128 and response['timings']['cache_n']==0
                        assert response['stop_type'] in ['eos','limit'];endpoint='EOS' if response['stop_type']=='eos' else 'limit'
                        equal=ids==task['original_reference_ids'] and endpoint==task['original_endpoint']
                        r={'task':task['id'],'condition':condition,'repetition':rep+1,'wall_ms':wall,'response':response,'endpoint':endpoint,
                           'original_reference_equal':equal,'source_commit':head,'formatted_prompt_sha256':hashlib.sha256(task['formatted_prompt'].encode()).hexdigest()}
                        save(out/f"{prefix}_{task['id'].replace('/','-')}.json",r);records.append(r)
                        print(f"DONE {prefix} {task['id']} equal={equal} wall={wall:.1f} gen={response['timings']['predicted_ms']:.1f}",flush=True)
                        if condition=='target' and not equal:raise RuntimeError('Matched target reference changed')
                finally:
                    if p.poll() is None:
                        p.terminate()
                        try:p.wait(timeout=10)
                        except subprocess.TimeoutExpired:p.kill();p.wait(timeout=10)
    save(out/'RECORDS.json',records);print('COMPLETE '+str(len(records)),flush=True)

if __name__=='__main__':
    import sys
    {'qualification':qualification,'cost':cost}[sys.argv[1]]()
