from prepare import *
if __name__=='__main__':
    inputs=read(OUT/'INPUTS.json');requests=[{'task_id':t,'formatted_prompt':formatted((ROOT/v['prompt']).read_text(encoding='utf-8'))} for t,v in inputs.items()]
    payload=''.join(json.dumps(q)+'\n' for q in requests).encode()
    with (OUT/'input-tokenizer.stderr.log').open('wb') as se:
        r=subprocess.run([str(OUT/'worker-bin/tokenizer.exe'),str(RUNTIME),str(ASSET/'models/gguf/Qwen3-8B-Q8_0.gguf')],input=payload,stdout=subprocess.PIPE,stderr=se,check=True)
    for line in r.stdout.splitlines():
        x=json.loads(line);assert x['vocab_only'] and x['forward_calls']==0 and len(x['prompt_ids'])+128<=4096
        d=ROOT/inputs[x['task_id']]['prompt'];p=d.with_name('prompt_ids.json')
        if p.exists():assert read(p)==x['prompt_ids']
        else:save(p,x['prompt_ids'])
        inputs[x['task_id']]['ids']=str(p.relative_to(ROOT)).replace('\\','/');inputs[x['task_id']]['ids_sha256']=sha(p)
    save(OUT/'INPUTS.json',inputs)
    save(DOC/'INPUT_CONTRACT.json',{'inputs':inputs,'tokenizer_sha256':sha(OUT/'worker-bin/tokenizer.exe'),'EOG':sorted(EOG),'context':4096,'cap':128,'forward_calls':0,'utc':utc()})
    print('static token IDs bound for49 prompts',flush=True)
