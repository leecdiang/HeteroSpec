"""Round-limited P/R orchestration. No native speculative frontend is a predictor."""
import gzip,hashlib,json,os,queue,subprocess,threading
from pathlib import Path
from datetime import datetime,timezone
from prepare import ROOT,STUDY,save
ASSET=Path('D:/HeteroSpec-PC')
BIN=ASSET/'tools/llama-b10839'
TARGET=ASSET/'models/gguf/Qwen3-8B-Q8_0.gguf'
DRAFT=ASSET/'models/gguf/Qwen3-0.6B-Q8_0.gguf'
def now():return datetime.now(timezone.utc).isoformat()
def ah(ids):return hashlib.sha256(json.dumps(ids,separators=(',',':')).encode('utf-8')).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(o):return json.dumps(o,separators=(',',':'),ensure_ascii=True).encode('utf-8')
def source_head():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
def prompts():
    with gzip.open(ASSET/'datasets/humaneval/HumanEval.jsonl.gz','rt',encoding='utf-8') as f:return {r['task_id']:'Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n'+r['prompt'] for r in map(json.loads,f)}
def format_prompt(text):
    # Exact no-tools Qwen3 template with enable_thinking=false; CLI --file removes one LF.
    if text.endswith('\n'):text=text[:-1]
    return '<|im_start|>user\n'+text+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
def strip_logits(o):
    if isinstance(o,dict):
        if 'logits_bytes_hex' in o:
            b=bytes.fromhex(o.pop('logits_bytes_hex'));o['logits_sha256']=digest(b);o['logits_bytes']=len(b)
        for v in o.values():strip_logits(v)
    elif isinstance(o,list):
        for v in o:strip_logits(v)
    return o
class Worker:
    def __init__(self,role,ub,out,log):
        self.role=role;self.log=log;self.counter=0;self.closed=False
        self.stderr=(out/(role+'-stderr.log')).open('wb')
        self.command=[str(ROOT/'work/h2-bin'/(role+'.exe')),str(BIN),str(DRAFT if role=='P' else TARGET),str(ub),role]
        self.proc=subprocess.Popen(self.command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.stderr,cwd=BIN)
        self.queue=queue.Queue()
        def read():
            try:
                for line in self.proc.stdout:self.queue.put(line)
            finally:self.queue.put(None)
        self.thread=threading.Thread(target=read,daemon=True);self.thread.start()
        self.ready=self.response();self.record('startup',{'command':self.command},self.ready)
    def response(self):
        line=self.queue.get(timeout=300)
        if line is None:raise RuntimeError(f'{self.role} worker exited {self.proc.poll()}')
        r=strip_logits(json.loads(line))
        if r.get('event')=='ERROR':raise RuntimeError(r['error'])
        return r
    def record(self,event,q,r):
        self.counter+=1;row={'utc':now(),'role':self.role,'pid':self.proc.pid,'event_sequence':self.counter,'event':event,'request':q,'response':r}
        self.log.write(canonical(row)+b'\n');self.log.flush();return row
    def call(self,q):
        self.proc.stdin.write(canonical(q)+b'\n');self.proc.stdin.flush();r=self.response();self.record(q['op'],q,r);return r
    def close(self):
        if self.closed:return
        self.closed=True
        if self.proc.poll() is None:
            self.call({'op':'close'});self.proc.stdin.close();self.proc.wait(timeout=30)
        self.stderr.close()
def native_command(prompt,native,transcript,live):
    cmd=[str(BIN/'llama-cli.exe'),'--model',str(TARGET),'--device','CUDA0','--n-gpu-layers','all','--fit','off','--ctx-size','4096','--flash-attn','off','--ubatch-size','2' if live else '1','--file',str(prompt),'--n-predict','128','--temp','0','--top-k','0','--top-p','1','--min-p','0','--seed','123','--single-turn','--simple-io','--no-display-prompt','--no-warmup','--cache-ram','0','--chat-template-kwargs','{"enable_thinking":false}','--log-verbosity','5','--perf','--log-file',str(native),'--output-file',str(transcript)]
    if live:cmd+=['--spec-type','draft-simple','--model-draft',str(DRAFT),'--spec-draft-device','CUDA0','--spec-draft-ngl','all','--spec-draft-n-max','2','--spec-draft-n-min','0']
    return cmd
def parse_native(p):
    import re
    b=p.read_bytes().replace(b'\r\n',b'\n');text=b.decode('latin-1')
    ev=re.findall(r'process_toke: id\s+0 \| task \d+ \| n_gen = (\d+), n_remaining = (-?\d+), next token:\s+(\d+)',text)
    if not ev or [int(x[0]) for x in ev]!=list(range(1,len(ev)+1)) or any(int(n)!=128-int(i) for i,n,_ in ev):raise RuntimeError('native commitment indices/budget invalid')
    ids=[int(x[2]) for x in ev];stops=re.findall(r'process_toke:.*stopped by (EOS|limit)',text)
    if len(stops)!=1 or len(ids)>128 or stops[0]=='limit' and len(ids)!=128:raise RuntimeError('native endpoint invalid')
    layers=re.findall(r'load_tensors: offloaded (\d+)/(\d+) layers to GPU',text);devices=re.findall(r'llama_prepare_model_devices: using device ([^\n]+)',text)
    if not layers or layers[0]!=('37','37') or any(not d.startswith('CUDA0 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)') for d in devices):raise RuntimeError('native placement invalid')
    return {'generated_ids':ids,'array_sha256':ah(ids),'termination':stops[0],'placement':{'devices':devices,'offload':layers},'native_sha256':digest(b)}
def execute(task,rep,condition,out,text=None,tape_path=None):
    if text is None:text=prompts()[task]
    out=Path(out)/f'{task.replace("/","-")}-r{rep}-{condition}';out.mkdir(parents=True,exist_ok=False)
    record={'task_id':task,'repetition':rep,'condition':condition,'run_id':out.name,'source_head':source_head(),'started_utc':now(),'status':'STARTED','input_sha256':digest(text.encode('utf-8'))}
    save(out/'record.json',record);(out/'prompt.txt').write_text(text,encoding='utf-8',newline='\n')
    workers=[]
    try:
        if condition in ['REFERENCE_UB1','RTX_BATCHED_K2']:
            cmd=native_command(out/'prompt.txt',out/'native.log',out/'transcript.txt',condition=='RTX_BATCHED_K2');record['command']=cmd
            with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:run=subprocess.run(cmd,stdout=stdout,stderr=stderr,stdin=subprocess.DEVNULL,timeout=300)
            record['exit_code']=run.returncode
            if run.returncode:raise RuntimeError('native process failed')
            record.update(parse_native(out/'native.log'))
        else:
            with (out/'events.jsonl').open('wb') as log:
                r=Worker('R',1 if condition=='R_REFERENCE_UB1' else 2,out,log);workers.append(r)
                ri=r.call({'op':'init','formatted_prompt':format_prompt(text)});ids=ri['committed_ids'].copy();record['prompt_ids']=ri['prompt_ids'];record['prompt_array_sha256']=ah(ri['prompt_ids'])
                pos=len(ri['prompt_ids']);terminal=ri['terminal'];round_index=0
                if condition=='R_REFERENCE_UB1':
                    while not terminal:
                        v=r.call({'op':'verify','round':round_index,'position':pos,'pending':ids[-1],'proposal_ids':[]})
                        ids+=v['committed_ids'];pos=v['next_position'];terminal=v['terminal'];round_index+=1
                elif condition=='H2_P_R':
                    p=Worker('P',2,out,log);workers.append(p);pi=p.call({'op':'init','formatted_prompt':format_prompt(text)})
                    if pi['prompt_ids']!=ri['prompt_ids']:raise RuntimeError('P/R prompt tokenization differs')
                    previous='0'*64
                    with (out/'tape.jsonl').open('xb') as tape:
                        while not terminal:
                            pp=p.call({'op':'propose','position':pos,'pending':ids[-1],'max_proposals':min(2,128-len(ids)-1)})
                            props=pp['proposal_ids'];tokens=[ids[-1]]+props
                            q={'op':'verify','round':round_index,'position':pos,'pending':ids[-1],'proposal_ids':props}
                            event={'run_id':out.name,'task_id':task,'repetition':rep,'round':round_index,'prefix_count':len(ids),'prefix_sha256':ah(ids),'request':q,'tokens':tokens,'positions':list(range(pos,pos+len(tokens))),'sequence_ids':[[0] for _ in tokens],'logits_mask':[1]*len(tokens),'previous_event_hash':previous,'P_response_sha256':digest(canonical(pp)),'sealed_utc':now(),'P_event_sequence':p.counter,'R_next_event_sequence':r.counter+1}
                            event['event_sha256']=digest(canonical(event));previous=event['event_sha256'];tape.write(canonical(event)+b'\n');tape.flush();os.fsync(tape.fileno())
                            # R is called only after durable append and digest of the current request.
                            v=r.call(q);p.call({'op':'update','position':pos,'verified_batch':tokens,'retain_count':v['retain_count']})
                            ids+=v['committed_ids'];pos=v['next_position'];terminal=v['terminal'];round_index+=1
                    record['tape_sha256']=digest((out/'tape.jsonl').read_bytes());record['P_round_calls']=round_index
                elif condition=='R_ONLY':
                    if tape_path is None:raise RuntimeError('sealed tape required')
                    previous='0'*64
                    # Future rows are not read until R has completed the current row.
                    with Path(tape_path).open('rb') as tape:
                        while not terminal:
                            line=tape.readline()
                            if not line:raise RuntimeError('tape truncated')
                            event=json.loads(line);h=event.pop('event_sha256')
                            if h!=digest(canonical(event)) or event['previous_event_hash']!=previous:raise RuntimeError('tape hash chain invalid')
                            previous=h
                            if event['task_id']!=task or event['repetition']!=rep or event['round']!=round_index or event['prefix_count']!=len(ids) or event['prefix_sha256']!=ah(ids):raise RuntimeError('tape task/past prefix invalid')
                            q=event['request']
                            if set(q)!={'op','round','position','pending','proposal_ids'} or q['position']!=pos or q['pending']!=ids[-1]:raise RuntimeError('tape request dependencies invalid')
                            v=r.call(q);ids+=v['committed_ids'];pos=v['next_position'];terminal=v['terminal'];round_index+=1
                        if tape.readline():raise RuntimeError('future tape suffix beyond endpoint')
                    record['replayed_tape_sha256']=digest(Path(tape_path).read_bytes())
                else:raise RuntimeError('unknown condition')
                for w in workers:w.close()
                record.update(generated_ids=ids,array_sha256=ah(ids),termination='limit' if len(ids)==128 else 'EOS',round_count=round_index)
        record['status']='VALID';save(out/'generated_ids.json',record['generated_ids'])
    except Exception as e:record.update(status='OPERATIONAL_FAILURE',error=repr(e))
    finally:
        for w in workers:
            try:w.close()
            except Exception:
                if w.proc.poll() is None:w.proc.kill();w.proc.wait()
    record['ended_utc']=now();record['files']={p.name:{'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in out.iterdir() if p.is_file() and p.name!='record.json'};save(out/'record.json',record)
    return record
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--task',default='HumanEval/3');p.add_argument('--condition',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--tape',type=Path);a=p.parse_args()
    result=execute(a.task,1,a.condition,a.out,tape_path=a.tape);print(json.dumps({k:v for k,v in result.items() if k not in ['files','prompt_ids','generated_ids']}));raise SystemExit(0 if result['status']=='VALID' else 1)
