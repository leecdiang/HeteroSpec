"""Six bounded HTTP requests, historical and clean-built R/PQ/QB, immutable raw receipts."""
import argparse,json,os,pathlib,subprocess,time,urllib.request,urllib.error
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from rtx_recover import sha,read,save
P=pathlib.Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=P);a=ap.parse_args();root=a.root.resolve();out=root/'request-smoke';out.mkdir(exist_ok=False)
    pair=read(root/'MODEL_CONTRACT.json')['families']['Qwen']['models'];task=next(t for t in read(root/'PANEL.json')['inputs'] if t['id']=='GSM8K/test/443')
    historical=read(root/'HISTORICAL_R_ENDPOINTS.json')['endpoints'][task['id']]
    save(out/'INPUT.json',task);(out/'prompt.txt').write_bytes(task['formatted_prompt'].encode())
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));rows=[];authority=None
    def http(route,body=None):
        q=urllib.request.Request('http://127.0.0.1:18746'+route,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with opener.open(q,timeout=120) as r:return json.load(r)
    for build in ('original/native','clean-build'):
        for arm in ('R','PQ','QB'):
            dest=out/(build.replace('/','-')+'-'+arm);dest.mkdir();exe=root/build/'bin/llama-server.exe'
            cmd=[str(exe),'--model',pair['target']['path'],'--device','CUDA0','--n-gpu-layers','all','--fit','off','--ctx-size','1024','--batch-size','2048','--ubatch-size','1' if arm=='R' else '4','--flash-attn','off','--parallel','1','--threads','24','--threads-batch','24','--cache-ram','0','--cache-type-k','f16','--cache-type-v','f16','--host','127.0.0.1','--port','18746','--no-webui','--no-warmup','--no-cache-prompt']
            if arm!='R':cmd+=['--spec-type','draft-simple','--model-draft',pair['draft']['path'],'--spec-draft-device','CUDA0','--spec-draft-ngl','all','--spec-draft-n-max','3','--spec-draft-n-min','0','--spec-draft-p-min','0','--spec-draft-threads','24','--spec-draft-threads-batch','24','--spec-draft-type-k','f16','--spec-draft-type-v','f16']
            env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','LLAMA_ARG_','GGML_','CUDA_'))};env.update(HS_SCOPE_MASK='0' if arm=='R' else '3',HS_Q95_LAYOUT='QB' if arm=='R' else arm,HS_NATIVE_CAPTURE=str(dest/'trace.jsonl'))
            body=dict(prompt=task['prompt_ids'],n_predict=128,temperature=0,top_k=0,top_p=1,min_p=0,seed=123,cache_prompt=False,return_tokens=True,stream=False,hs_closeout_mode='counts')
            save(dest/'START.json',dict(argv=cmd,environment={k:v for k,v in env.items() if k.startswith('HS_')},body=body,executable_sha256=sha(exe)))
            p=None;start=time.perf_counter();record={'status':'RUNNING','arm':arm,'build':build}
            try:
                with (dest/'server.log').open('wb') as log:
                    p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
                    deadline=time.monotonic()+120
                    while True:
                        if p.poll() is not None:raise RuntimeError('server exited')
                        try:
                            if http('/health').get('status')=='ok':break
                        except (OSError,urllib.error.URLError):pass
                        if time.monotonic()>deadline:raise TimeoutError('load deadline')
                        time.sleep(.25)
                    response=http('/completion',body);save(dest/'RESPONSE.json',response)
                    endpoint={k:response[k] for k in ('tokens','stop_type','tokens_predicted','truncated')}
                    if authority is None:authority=endpoint
                    if response['tokens']!=historical['ids'] or response['tokens_predicted']!=historical['length'] or response['stop_type']!='limit' or response['truncated'] or historical['stop_reason']!='CAP':raise RuntimeError('historical E2 endpoint mismatch')
                    record.update(status='PASS' if endpoint==authority else 'NUMERICAL_FAIL',endpoint=endpoint,modules=response.get('hs_closeout',{}).get('modules'),response_sha256=sha(dest/'RESPONSE.json'))
            except Exception as e:record.update(status='ERROR',error=repr(e))
            finally:
                if p is not None and p.poll() is None:
                    p.terminate()
                    try:p.wait(timeout=10)
                    except subprocess.TimeoutExpired:p.kill();p.wait(timeout=10)
                record.update(pid=p.pid if p else None,exit_code=p.returncode if p else None,owned_seconds=time.perf_counter()-start,cleanup=True)
                save(dest/'RECEIPT.json',record);rows.append(record);save(out/'RESULT.json',dict(status='PASS' if all(r['status']=='PASS' for r in rows) and len(rows)==6 else 'INCOMPLETE_OR_FAILED',rows=rows))
            print(build,arm,record['status'],flush=True)
if __name__=='__main__':main()
