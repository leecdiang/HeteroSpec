"""Bind paid-reference schedule and pure-vocabulary prompt identities."""
import hashlib,json,subprocess
from close_base import HERE,PHASE1,PHASE2,ASSET,OLDROOT,read,save,sha,now

CONDITIONS=[{'name':'scalar_reference','mask':0,'spec':False,'ub':1,'k':0},
            {'name':'matched_target','mask':3,'spec':False,'ub':4,'k':0},
            {'name':'target_scopes','mask':3,'spec':True,'ub':4,'k':3},
            {'name':'all_scopes','mask':15,'spec':True,'ub':4,'k':3}]

def main():
    assert read(HERE/'EXPOSURE_LEDGER.json')['status']=='PASS'
    assert not (HERE/'B_MANIFEST.json').exists()
    inputs=read(HERE/'B_INPUTS.json');exe=OLDROOT/'work/rtx-target-v1/worker-bin/tokenizer.exe'
    request=''.join(json.dumps({'task_id':r['id'],'formatted_prompt':r['formatted_prompt']})+'\n' for r in inputs).encode()
    with (HERE/'generated/B_TOKENIZER.stderr.log').open('wb') as se:
        r=subprocess.run([str(exe),str(ASSET/'tools/llama-b10839'),str(ASSET/'models/gguf/Qwen3-8B-Q8_0.gguf')],
                         input=request,stdout=subprocess.PIPE,stderr=se,check=True,timeout=120,
                         creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    (HERE/'generated/B_TOKENIZER.stdout.jsonl').write_bytes(r.stdout)
    replies={x['task_id']:x for x in map(json.loads,r.stdout.splitlines())};assert len(replies)==len(inputs)==24
    for t in inputs:
        q=replies[t['id']];assert q['vocab_only'] and q['forward_calls']==0 and len(q['prompt_ids'])+512<=4096
        t['prompt_ids']=q['prompt_ids'];t['prompt_token_count']=len(q['prompt_ids'])
    save(HERE/'B_INPUTS.json',inputs)
    build=read(PHASE2/'generated/BUILD_IDENTITY.json')
    assert sha(PHASE2/'generated/build/bin/llama-server.exe')==build['server_sha256']
    assert sha(PHASE2/'generated/build/bin/llama-cli.exe')==build['frontend_sha256']
    old=read(PHASE2/'generated/ASSET_CHECK_POST.json');assets={}
    for label,name in [('target','Qwen3-8B-Q8_0.gguf'),('draft','Qwen3-0.6B-Q8_0.gguf')]:
        p=ASSET/'models/gguf'/name;assets[label]={'sha256':sha(p),'bytes':p.stat().st_size};assert assets[label]==old[label]
    assets['runtime_dlls']={p.name:sha(p) for p in sorted((ASSET/'tools/llama-b10839').glob('*.dll'))};assert assets['runtime_dlls']==old['runtime_dlls']
    save(HERE/'SOURCE_BINDINGS.json',{'phase2_source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=PHASE2,text=True).strip(),
         'phase2_build':build,'phase2_archive_sha256':'cd57ec99359b35ce201cf7c1b19979a46e05af3d03740e3cc2a753d596ca2b3d',
         'phase2_inputs_sha256':sha(PHASE2/'INPUTS.json'),'phase1_source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=PHASE1,text=True).strip(),
         'assets_pre':assets,'tokenizer_sha256':sha(exe),'tokenizer_stdout_sha256':sha(HERE/'generated/B_TOKENIZER.stdout.jsonl'),
         'new_task_forward_calls_before_freeze':0})
    save(HERE/'B_MANIFEST.json',{'stage':'B','utc':now(),'protocol_sha256':sha(HERE/'PROTOCOL.md'),
         'inputs_sha256':sha(HERE/'B_INPUTS.json'),'exposure_ledger_sha256':sha(HERE/'EXPOSURE_LEDGER.json'),
         'conditions':CONDITIONS,'repetitions':4,'tasks':[r['id'] for r in inputs],'request_cap':384,'warmups':16,
         'bridge':{'original_tasks':[15,25,18,31],'conditions':CONDITIONS,'requests':16,'warmups':4},
         'source_bindings_sha256':sha(HERE/'SOURCE_BINDINGS.json'),'reference_policy':'Paid scalar reference per task/repetition; no reference is an online input.',
         'candidate_rule':'mask3 iff full B and matched target qualify; otherwise mask15 iff full B and matched target qualify; otherwise stop dependent formal stages.',
         'new_task_forward_calls_before_freeze':0})
    print(json.dumps({'tasks':len(inputs),'max_prompt_tokens':max(t['prompt_token_count'] for t in inputs),'forward_calls':0,'B_requests':384,'warmups':16}),flush=True)

if __name__=='__main__':main()
