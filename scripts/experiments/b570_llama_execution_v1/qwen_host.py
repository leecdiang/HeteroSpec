"""Bounded original-Qwen regression, sharing the Llama resource/exposure ledgers."""
from pathlib import Path
import argparse,os,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,sha,need,utc,canonical,digest
import budget

def run(build,repo,root,out,mode,index):
    b=read(build);repo=Path(repo).resolve();root=Path(root).resolve();out=Path(out).resolve()
    models=read(repo/'benchmarks/b570_native_reproduction_v1/MODEL_IDENTITY.json')
    for m in models:need(Path(m['path']).stat().st_size==m['bytes'] and sha(m['path'])==m['sha256'],'old Qwen model identity')
    panel=repo/'benchmarks/b570_native_reproduction_v1/INPUT_PANEL.json';inputs=read(panel)['inputs']
    need(mode in ('admit','qual') and 0<=index<4,'mode/index')
    need(not out.exists(),'fresh Qwen attempt');need(sha(b['supervisor'])==b['supervisor_sha256'],'supervisor drift')
    if mode=='qual':
        admission=read(out.parent/'admission/RECEIPT.json');need(admission['success'] and admission['build_sha256']==sha(build),'same build zero-forward admission')
    lock=Path('C:/hs/b570-llama-exclusive.lock');write(lock,{'pid':os.getpid(),'attempt':str(out),'utc':utc()});out.mkdir(parents=True)
    started=False;cleaned=False;success=False;actual=0;begin=time.monotonic()
    try:
        budget.reserve(root/'LEDGER.jsonl',str(out),3 if mode=='qual' else 0,0,1200);started=True
        write(out/'FILES.json',{'files':b['files']});write(out/'MODEL_IDENTITY.json',models)
        if mode=='qual':
            x=inputs[index]
            with (root/'EXPOSURE.jsonl').open('a',encoding='utf-8') as f:
                f.write(canonical({'id':x['id'],'prompt_ids_sha256':digest(x['prompt_ids']),'attempt':str(out),'stage':'old-Qwen-regression','utc':utc()}).decode()+'\n');f.flush();os.fsync(f.fileno())
        command=[sys.executable,'-B',b['supervisor'],'--manifest',str(out/'FILES.json'),'--receipt',str(out/'SUPERVISOR.json'),'--limit','1200','--minimum-free-bytes',str(20*1024**3),b['executable'],str(out/'native'),models[0]['path'],models[1]['path'],str(panel),mode,str(index),str(root)]
        write(out/'COMMAND.json',{'argv':command,'build_sha256':sha(build),'panel_sha256':sha(panel),'utc':utc()})
        p=subprocess.run(command,timeout=1380);s=read(out/'SUPERVISOR.json');n=read(out/'native/result.json')
        cleaned=s.get('job_accounting',{}).get('active_processes')==0;actual=len(n['requests'])
        need(cleaned and p.returncode==0 and n['normal_cleanup_returned'],'native/cleanup failure')
        need(n['status']==('RESOURCE_ADMITTED' if mode=='admit' else 'QUALIFICATION_PASS'),'Qwen native gate')
        loaded={Path(x['path']).name.lower():x['sha256'] for x in s['loaded_module_hashes']}
        for f in b['files']:
            name=Path(f['path']).name.lower()
            if name in loaded:need(loaded[name]==f['sha256'],'DLL drift')
        need(all(n in loaded for n in ('llama.dll','ggml-vulkan.dll','ggml-base.dll')),'runtime modules unobserved');success=True
    finally:
        if (out/'SUPERVISOR.json').exists():cleaned=read(out/'SUPERVISOR.json').get('job_accounting',{}).get('active_processes')==0
        if (out/'native/result.json').exists():actual=len(read(out/'native/result.json').get('requests',[]))
        seconds=time.monotonic()-begin
        write(out/'RECEIPT.json',{'success':success,'cleanup_verified':cleaned,'completed_model_requests':actual,'owned_seconds':seconds,'build_sha256':sha(build)})
        if started and cleaned:budget.append(root/'LEDGER.jsonl',{'event':'END','attempt':str(out),'completed_model_requests':actual,'operator_calls':0,'seconds':seconds,'success':success})
        if not started or cleaned:lock.unlink(missing_ok=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('build','repo','root','out'):p.add_argument('--'+n,required=True)
    p.add_argument('--mode',choices=['admit','qual'],required=True);p.add_argument('--index',type=int,default=0);a=p.parse_args();run(a.build,a.repo,a.root,a.out,a.mode,a.index)
