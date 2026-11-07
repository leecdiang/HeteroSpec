"""Single writer, unique immutable paid request records and resident HTTP timer."""
from preflight import *
import math

class Budget:
    def __init__(self,phase):
        self.phase=phase;self.cap=640 if phase=='engineering' else 3600;self.root=LOCAL/'runs'/phase;self.root.mkdir(parents=True,exist_ok=True)
        self.paid=len(list(self.root.rglob('REQUEST_STARTED.json')))
        self.life=sum(read(p)['seconds'] for p in self.root.rglob('LIFETIME.json'))
        if phase=='engineering':self.life+=sum(read(p)['lifetime_seconds'] for p in PUB.glob('ZERO_LOAD_*.json'))
    def check(self):
        paid,life=self.paid,self.life
        assert paid<self.cap,'paid request budget exhausted'
        assert life<(8 if self.phase=='engineering' else 24)*3600,'owned GPU process budget exhausted'
        return paid,life

class Resident:
    def __init__(self,d,family,c,phase,capture=False):
        self.d=Path(d);self.family=family;self.c=c;self.phase=phase;self.capture=capture;self.cmd=command(models()[family],c,verbose=capture);self.budget=Budget(phase)
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(self,route,body=None,timeout=240):
        data=None if body is None else json.dumps(body,ensure_ascii=False).encode()
        q=urllib.request.Request('http://127.0.0.1:18783'+route,data=data,headers={'Content-Type':'application/json'})
        with self.opener.open(q,timeout=timeout) as r:return json.load(r)
    def __enter__(self):
        _,life=self.budget.check();assert life<(8 if self.phase=='engineering' else 24)*3600-252,'insufficient owned GPU loading/cleanup budget'
        self.d.mkdir(parents=True,exist_ok=False)
        save(self.d/'COMMAND.json',{'command':self.cmd,'condition':self.c,'family':self.family,'capture':self.capture,'utc':now(),'binary_sha256':sha(self.cmd[0]),'phase':self.phase})
        self.log=(self.d/'server.log').open('wb');self.start=time.perf_counter()
        self.p=subprocess.Popen(self.cmd,stdout=self.log,stderr=subprocess.STDOUT,env=clean_env(self.c['mask'],self.d/'trace.jsonl' if self.capture else None),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        save(self.d/'PROCESS.json',{'pid':self.p.pid,'utc':now()})
        try:
            deadline=time.monotonic()+240
            while True:
                if self.p.poll() is not None:raise RuntimeError('resident server exited '+str(self.p.returncode))
                try:
                    if self.request('/health',timeout=2).get('status')=='ok':break
                except (OSError,urllib.error.URLError):pass
                if time.monotonic()>deadline:raise TimeoutError('resident readiness')
                time.sleep(.5)
            loaded=host();save(self.d/'LOADED_HOST.json',loaded)
            assert loaded['total_MiB']-loaded['used_MiB']>=512,'full resident free VRAM below512MiB'
            return self
        except BaseException:self.__exit__(None,None,None);raise
    def complete(self,task,slot,warmup=False):
        _,life=self.budget.check()
        assert life+time.perf_counter()-self.start<(8 if self.phase=='engineering' else 24)*3600-252,'owned GPU lifecycle cap including timeout/cleanup reserve'
        d=self.d/('requests/'+slot.replace('/','_').replace('|','--'));d.mkdir(parents=True,exist_ok=False)
        freeze=read(LOCAL/('F0A_REMOTE_RECEIPT.json' if self.phase=='engineering' else 'F0B_REMOTE_RECEIPT.json'))
        body={'prompt':task['prompt_ids'],'n_predict':task['cap'],'temperature':0,'top_k':0,'top_p':1,'min_p':0,'seed':123,'cache_prompt':False,'return_tokens':True,'stream':False}
        save(d/'REQUEST_STARTED.json',{'utc':now(),'slot':slot,'task':task['id'],'family':self.family,'condition':self.c,'phase':self.phase,'warmup':warmup,'body':body,'input_sha256':digest(task),'freeze_commit':freeze['frozen_sha']})
        self.budget.paid+=1
        try:
            trace=self.d/'trace.jsonl';offset=trace.stat().st_size if self.capture and trace.exists() else 0
            start=time.perf_counter();response=self.request('/completion',body);wall=1000*(time.perf_counter()-start)
            result={'slot':slot,'task':task['id'],'family':self.family,'condition':self.c,'phase':self.phase,'warmup':warmup,'utc':now(),'response':response,'wall_ms':wall,'tokens_digest':digest(response.get('tokens')),'input_sha256':digest(task),'formatted_prompt_sha256':task['formatted_prompt_sha256'],'freeze_commit':freeze['frozen_sha']}
            if self.capture:result['capture_range']={'file':str(trace.relative_to(LOCAL)),'start':offset,'end':trace.stat().st_size}
            save(d/'RECORD.json',result)
            save(d/'COMPLETED.json',{'status':'COMPLETED','record_sha256':sha(d/'RECORD.json'),'utc':now()})
            return result
        except Exception as e:
            save(d/'FAILED.json',{'status':'FAILED_OPERATION','utc':now(),'error':repr(e)})
            raise
    def __exit__(self,*args):
        if self.p.poll() is None:
            self.p.terminate()
            try:self.p.wait(timeout=10)
            except subprocess.TimeoutExpired:self.p.kill();self.p.wait(timeout=10)
        self.log.close();save(self.d/'LIFETIME.json',{'seconds':time.perf_counter()-self.start,'utc':now(),'phase':self.phase})

def cooldown(d):
    # Conditions fixed before looking at any outcome. No service is resident here.
    start=time.monotonic();time.sleep(120);samples=[];passed=False
    while time.monotonic()-start+21<=600:
        batch=[]
        for i in range(3):
            batch.append(host())
            if i<2:time.sleep(10)
        samples+=batch
        expected=read(PUB/'DISPLAY_CHANGE_ADMISSION.json')['samples'][0]
        policy=read(PUB/'HOST_POLICY.json')
        passed=all(s['AC']==1 and s['util']<=5 and s['temp']<=55 and s['gpu']==expected['gpu'] and s['driver']==expected['driver'] and s['total_MiB']==expected['total_MiB'] and s['power_scheme_guid'] is not None and s['power_scheme_guid']==policy['power_scheme_guid'] for s in batch) and max(s['temp'] for s in batch)-min(s['temp'] for s in batch)<=2
        if passed:break
        if time.monotonic()-start+20>600:break
    save(d,{'status':'PASS' if passed else 'MISSING_HOST_ADMISSION','utc':now(),'seconds':time.monotonic()-start,'samples':samples})
    return passed

def writer_test():
    root=LOCAL/'writer-test';root.mkdir(exist_ok=False)
    p=root/'complete-001.json';save(p,{'status':'COMPLETED'})
    # Hold a completed file open exactly as a monitor would. Next record has a new path.
    with p.open('rb') as reader:
        save(root/'complete-002.json',{'status':'COMPLETED'})
        assert json.load(reader)['status']=='COMPLETED'
    try:save(p,{'status':'REPLACED'})
    except FileExistsError:duplicate_refused=True
    else:raise AssertionError('immutable record overwritten')
    child=subprocess.run([str(Path(__import__('sys').executable)),'-c','import pathlib,sys; p=pathlib.Path(sys.argv[1]); p.write_text("partial"); raise SystemExit(17)',str(root/'crash.writing')],capture_output=True)
    assert child.returncode==17 and len(list(root.glob('*.json')))==2
    lock=root/'SINGLE_WRITER.lock';lock.write_text('owner',encoding='utf-8')
    try:lock.open('x')
    except FileExistsError:lock_refused=True
    else:raise AssertionError('second writer admitted')
    save(PUB/'WRITER_ENGINEERING.json',{'status':'PASS','unique_paths_while_reader_holds_prior_record':True,'duplicate_refused':duplicate_refused,'second_writer_refused':lock_refused,'crash_partial_not_completed':True,'atomic_publish':'fsync unique .writing then rename to previously nonexistent completed path; monitor ignores .writing','forwards':0})
if __name__=='__main__':writer_test()
