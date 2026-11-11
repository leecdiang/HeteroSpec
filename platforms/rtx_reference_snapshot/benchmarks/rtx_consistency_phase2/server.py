"""Native resident requests, fixed scope per process, no answer inputs."""
import json,subprocess,time,urllib.request,urllib.error
from base import HERE,ASSET,env,read,save,sha,now

class Server:
    def __init__(self,directory,mask,spec=True,capture=False):
        self.d=directory;self.mask=mask;self.spec=spec;self.capture=capture
        self.exe=HERE/'generated/build/bin/llama-server.exe'
        self.command=[str(self.exe),'--model',str(ASSET/'models/gguf/Qwen3-8B-Q8_0.gguf'),'--device','CUDA0',
            '--n-gpu-layers','all','--fit','off','--ctx-size','4096','--batch-size','2048','--ubatch-size','4',
            '--flash-attn','off','--parallel','1','--threads','24','--threads-batch','24','--cache-ram','0',
            '--host','127.0.0.1','--port','18764','--no-webui','--no-warmup','--no-cache-prompt']
        if spec:self.command+=['--spec-type','draft-simple','--model-draft',str(ASSET/'models/gguf/Qwen3-0.6B-Q8_0.gguf'),
            '--spec-draft-device','CUDA0','--spec-draft-ngl','all','--spec-draft-n-max','3','--spec-draft-n-min','0',
            '--spec-draft-threads','24','--spec-draft-threads-batch','24']
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(self,route,body=None,timeout=120):
        q=urllib.request.Request('http://127.0.0.1:18764'+route,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with self.opener.open(q,timeout=timeout) as r:return json.load(r)
    def complete(self,prompt,cap):
        return self.request('/completion',{'prompt':prompt,'n_predict':cap,'temperature':0,'top_k':0,'top_p':1,'min_p':0,
                                          'seed':123,'cache_prompt':False,'return_tokens':True,'stream':False})
    def __enter__(self):
        self.d.mkdir(parents=True,exist_ok=False)
        save(self.d/'COMMAND.json',{'command':self.command,'mask':self.mask,'spec':self.spec,'capture':self.capture,
             'server_sha256':sha(self.exe),'utc':now()})
        self.log=(self.d/'server.log').open('wb')
        self.p=subprocess.Popen(self.command,stdout=self.log,stderr=subprocess.STDOUT,
                                env=env(self.mask,self.d/'trace.jsonl' if self.capture else None),
                                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        save(self.d/'PROCESS.json',{'pid':self.p.pid,'utc':now()})
        try:
            deadline=time.monotonic()+120
            while True:
                if self.p.poll() is not None:raise RuntimeError('Server exit '+str(self.p.returncode))
                try:
                    if self.request('/health',timeout=2).get('status')=='ok':break
                except (OSError,urllib.error.URLError):pass
                if time.monotonic()>deadline:raise RuntimeError('Readiness timeout')
                time.sleep(.5)
            warm='<|im_start|>user\nWrite Python code to add two integers.<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
            save(self.d/'WARMUP.json',self.complete(warm,32));return self
        except Exception:self.__exit__(None,None,None);raise
    def __exit__(self,*args):
        if self.p.poll() is None:
            self.p.terminate()
            try:self.p.wait(timeout=10)
            except subprocess.TimeoutExpired:self.p.kill();self.p.wait(timeout=10)
        self.log.close()

def measure(server,task,condition,repetition,source):
    started=time.perf_counter();r=server.complete(task['formatted_prompt'],task['cap']);wall=1000*(time.perf_counter()-started)
    ids=r['tokens'];assert ids and len(ids)==r['tokens_predicted'] and len(ids)<=task['cap'] and r['timings']['cache_n']==0
    assert r['prompt']==task['formatted_prompt'] and r['stop_type'] in ['eos','limit']
    endpoint='EOS' if r['stop_type']=='eos' else 'limit'
    assert len(ids)==task['cap'] or endpoint=='EOS'
    eog={128247,151643,151645,151662,151663,151664}
    assert not any(t in eog for t in ids[:-1]) and ((ids[-1] in eog)==(endpoint=='EOS'))
    equal=ids==task['original_reference_ids'] and endpoint==task['original_endpoint']
    return {'task':task['id'],'condition':condition,'mask':server.mask,'spec':server.spec,'repetition':repetition,
        'source_commit':source,'wall_ms':wall,'response':r,'endpoint':endpoint,'original_reference_equal':equal,
        'formatted_prompt_sha256':__import__('hashlib').sha256(task['formatted_prompt'].encode()).hexdigest()}
