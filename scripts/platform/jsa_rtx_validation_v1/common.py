"""Online transport and evidence writes; never loads output references."""
import hashlib,json,os,subprocess,time,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
REPO=Path(__file__).resolve().parents[3]
PUB=REPO/'benchmarks/jsa_rtx_validation_v1'
LOCAL=Path(os.environ.get('JSA_LOCAL_ROOT',str(REPO.parent/'jsa')))
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp')
    q.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n');q.replace(p)
def now():return datetime.now(timezone.utc).isoformat()
def head():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
def clean_env(mask=0,capture=None):
    e={k:v for k,v in os.environ.items() if not k.startswith(('HS_','LLAMA_ARG_','LLAMA_BATCH_DEBUG','GGML_','CUDA_'))}
    e['HS_SCOPE_MASK']=str(mask)
    if capture:e['HS_NATIVE_CAPTURE']=str(capture)
    return e
WARM='<|im_start|>user\nWrite Python code to add two integers.<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
class Server:
    def __init__(self,d,condition,capture=False,model_pair=None,exe=None,warm=WARM):
        self.d=Path(d);self.c=condition;self.capture=capture;self.cfg=read(LOCAL/'CONFIG.json');self.port=self.cfg['port'];self.warm=warm
        self.exe=Path(exe or Path(self.cfg['runtime_S'])/'llama-server.exe');m=model_pair or self.cfg['models']
        self.command=[str(self.exe),'--model',m['target']['path'],'--device','CUDA0','--n-gpu-layers','all','--fit','off','--ctx-size','4096','--batch-size','2048','--ubatch-size',str(condition['ub']),'--flash-attn','off','--parallel','1','--threads','24','--threads-batch','24','--cache-ram','0','--host','127.0.0.1','--port',str(self.port),'--no-webui','--no-warmup','--no-cache-prompt']
        if condition['spec']:self.command+=['--spec-type','draft-simple','--model-draft',m['draft']['path'],'--spec-draft-device','CUDA0','--spec-draft-ngl','all','--spec-draft-n-max',str(condition['k']),'--spec-draft-n-min','0','--spec-draft-threads','24','--spec-draft-threads-batch','24']
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(self,route,body=None,timeout=180):
        q=urllib.request.Request('http://127.0.0.1:'+str(self.port)+route,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with self.opener.open(q,timeout=timeout) as r:return json.load(r)
    def complete(self,prompt,cap):
        return self.request('/completion',{'prompt':prompt,'n_predict':cap,'temperature':0,'top_k':0,'top_p':1,'min_p':0,'seed':123,'cache_prompt':False,'return_tokens':True,'stream':False})
    def __enter__(self):
        self.d.mkdir(parents=True,exist_ok=False);save(self.d/'COMMAND.json',{'command':self.command,'condition':self.c,'exe_sha256':sha(self.exe),'capture':self.capture,'utc':now()})
        self.log=(self.d/'server.log').open('wb');self.start=time.perf_counter()
        self.p=subprocess.Popen(self.command,stdout=self.log,stderr=subprocess.STDOUT,env=clean_env(self.c['mask'],self.d/'trace.jsonl' if self.capture else None),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        save(self.d/'PROCESS.json',{'pid':self.p.pid,'utc':now()})
        try:
            deadline=time.monotonic()+180
            while True:
                if self.p.poll() is not None:raise RuntimeError('server exited '+str(self.p.returncode))
                try:
                    if self.request('/health',timeout=2).get('status')=='ok':break
                except (OSError,urllib.error.URLError):pass
                if time.monotonic()>deadline:raise TimeoutError('server readiness')
                time.sleep(.5)
            save(self.d/'WARMUP.json',{'response':self.complete(self.warm,32),'utc':now()});return self
        except BaseException:self.__exit__(None,None,None);raise
    def __exit__(self,*args):
        if self.p.poll() is None:
            self.p.terminate()
            try:self.p.wait(timeout=10)
            except subprocess.TimeoutExpired:self.p.kill();self.p.wait(timeout=10)
        self.log.close();save(self.d/'LIFETIME.json',{'seconds':time.perf_counter()-self.start,'utc':now()})
def measure(s,task,slot):
    # The full HTTP construction, response receive and JSON parsing are paid.
    started=time.perf_counter();r=s.complete(task['formatted_prompt'],task['cap']);wall=(time.perf_counter()-started)*1000
    return {'slot':slot,'utc':now(),'source_commit':head(),'task':task['id'],'condition':s.c,'wall_ms':wall,'response':r,'tokens_digest':digest(r.get('tokens')),'formatted_prompt_sha256':hashlib.sha256(task['formatted_prompt'].encode()).hexdigest()}
