"""Native resident service cost, with original historical reference as a gate."""
import hashlib,json,os,subprocess,time,urllib.error,urllib.request
from pathlib import Path
from run import HERE,OLD,ORIGINAL,ASSET,read,save,sha,now

def prepare():
    old=read(OLD/'INPUTS.json');inputs=[]
    for tid,rec in old.items():
        if not tid.startswith('HumanEval/'):continue
        text=(ORIGINAL/rec['prompt']).read_text(encoding='utf-8')
        assert sha(ORIGINAL/rec['prompt'])==rec['prompt_sha256']
        text=text[:-1] if text.endswith('\n') else text
        formatted='<|im_start|>user\n'+text+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
        rr=[read(OLD/f"formal/{tid.replace('/','-')}-R-r{i}/result.json") for i in [1,2,3]]
        assert all(x['ids']==rr[0]['ids'] and x['endpoint']==rr[0]['endpoint'] for x in rr)
        inputs.append({'id':tid,'formatted_prompt':formatted,'cap':128,'original_reference_ids':rr[0]['ids'],
                       'original_endpoint':rr[0]['endpoint'],'prompt_sha256':rec['prompt_sha256'],
                       'original_reference_sources':[sha(OLD/f"formal/{tid.replace('/','-')}-R-r{i}/result.json") for i in [1,2,3]]})
    assert len(inputs)==19
    save(HERE/'COST_INPUTS.json',inputs)

def run():
    assert read(HERE/'generated/analysis/ATTENTION_QUALIFICATION.json')['status']=='PASS_EXPOSED_PROBE'
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=HERE,text=True).strip()
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip()
    out=HERE/'runs/cost-v2';out.mkdir(exist_ok=False)
    exe=HERE/'generated/build/bin/llama-server.exe';inputs=read(HERE/'COST_INPUTS.json')
    base=[str(exe),'--model',str(ASSET/'models/gguf/Qwen3-8B-Q8_0.gguf'),'--device','CUDA0','--n-gpu-layers','all',
          '--fit','off','--ctx-size','4096','--batch-size','2048','--flash-attn','off','--parallel','1','--threads','24',
          '--threads-batch','24','--cache-ram','0','--host','127.0.0.1','--port','18763','--no-webui','--no-warmup','--no-cache-prompt']
    env0={k:v for k,v in os.environ.items() if not k.startswith(('HS_','LLAMA_ARG_','LLAMA_BATCH_DEBUG','GGML_','CUDA_'))}
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(route,body=None,timeout=120):
        req=urllib.request.Request('http://127.0.0.1:18763'+route,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with opener.open(req,timeout=timeout) as r:return json.load(r)
    def completion(prompt,cap):
        return request('/completion',{'prompt':prompt,'n_predict':cap,'temperature':0,'top_k':0,'top_p':1,'min_p':0,
                                     'seed':123,'cache_prompt':False,'return_tokens':True,'stream':False})
    save(out/'MANIFEST.json',{'source_commit':head,'runner_sha256':sha(Path(__file__)),'inputs_sha256':sha(HERE/'COST_INPUTS.json'),
        'server_sha256':sha(exe),'cuda_sha256':sha(HERE/'generated/build/bin/ggml-cuda.dll'),
        'base_command':base,'started_utc':now(),'measured_request_cap':171,'excluded_warmups':9})
    records=[]
    for rep in range(3):
        order=['target','serialized','attention'];order=order[rep:]+order[:rep]
        for condition in order:
            prefix=f'r{rep+1}_{condition}';cmd=base+['--ubatch-size','2' if condition=='attention' else '1'];env=env0.copy()
            if condition!='target':cmd+=['--spec-type','draft-simple','--model-draft',str(ASSET/'models/gguf/Qwen3-0.6B-Q8_0.gguf'),
                '--spec-draft-device','CUDA0','--spec-draft-ngl','all','--spec-draft-n-max','2','--spec-draft-n-min','0',
                '--spec-draft-threads','24','--spec-draft-threads-batch','24']
            if condition=='attention':env['HS_ATTENTION_SINGLE_QUERY']='1'
            save(out/(prefix+'_COMMAND.json'),{'command':cmd,'attention_constraint':condition=='attention'})
            print('START '+prefix,flush=True)
            with (out/(prefix+'.log')).open('wb') as log:
                process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                save(out/(prefix+'_PROCESS.json'),{'pid':process.pid,'utc':now()})
                try:
                    deadline=time.monotonic()+120
                    while True:
                        if process.poll() is not None:raise RuntimeError('Server exited '+str(process.returncode))
                        try:
                            if request('/health',timeout=2).get('status')=='ok':break
                        except (OSError,urllib.error.URLError):pass
                        if time.monotonic()>deadline:raise RuntimeError('Server readiness timeout')
                        time.sleep(.5)
                    warm='<|im_start|>user\nWrite Python code to add two integers.<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
                    save(out/(prefix+'_WARMUP.json'),completion(warm,32))
                    tasks=inputs[rep:]+inputs[:rep]
                    for task in tasks:
                        t=time.perf_counter();response=completion(task['formatted_prompt'],task['cap']);wall=1000*(time.perf_counter()-t)
                        assert response.get('tokens') and response['timings']['cache_n']==0
                        ids=response['tokens'];assert len(ids)==response['tokens_predicted'] and len(ids)<=128
                        stop=response['stop_type'];assert stop in ['eos','limit']
                        endpoint='EOS' if stop=='eos' else 'limit'
                        equal=ids==task['original_reference_ids'] and endpoint==task['original_endpoint']
                        r={'task':task['id'],'condition':condition,'repetition':rep+1,'wall_ms':wall,'response':response,
                           'endpoint':endpoint,'original_reference_equal':equal,'source_commit':head,
                           'formatted_prompt_sha256':hashlib.sha256(task['formatted_prompt'].encode()).hexdigest()}
                        save(out/f"{prefix}_{task['id'].replace('/','-')}.json",r);records.append(r)
                        print(f"DONE {prefix} {task['id']} equal={equal} wall={wall:.1f} gen={response['timings']['predicted_ms']:.1f}",flush=True)
                        if condition=='target' and not equal:raise RuntimeError('Service reference differs from immutable original CLI R')
                finally:
                    if process.poll() is None:
                        process.terminate()
                        try:process.wait(timeout=10)
                        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)
    save(out/'RECORDS.json',records);print('COMPLETE '+str(len(records)),flush=True)

if __name__=='__main__':
    import sys
    {'prepare':prepare,'run':run}[sys.argv[1]]()
