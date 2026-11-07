"""Freeze all input hashes and vocab-only reserved token IDs. No model forward."""
import json,subprocess
from pathlib import Path
from prepare import ROOT,STUDY,save
from engine import BIN,TARGET,prompts,format_prompt,ah,digest,now
def main():
    src=ROOT/'work/pinned-source';worker=Path(__file__).with_name('tokenizer.cpp');exe=ROOT/'work/h2-bin/T.exe';zig='D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/ziglang/zig.exe'
    cmd=[zig,'c++','-std=c++17','-O2','-target','x86_64-windows-gnu','-I'+str(src/'include'),'-I'+str(src/'ggml/include'),'-I'+str(src/'vendor/nlohmann'),str(worker),'-o',str(exe)]
    with (ROOT/'work/tokenizer-build.log').open('wb') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError('tokenizer-only build failed')
    inputs=prompts();selected=json.loads((STUDY/'RESERVED_SET.json').read_text(encoding='utf-8'))['selected_task_ids'];command=[str(exe),str(BIN),str(TARGET)]
    q=''.join(json.dumps({'task_id':t,'formatted_prompt':format_prompt(inputs[t])})+'\n' for t in selected).encode('utf-8')
    r=subprocess.run(command,input=q,capture_output=True,timeout=300);(ROOT/'work/tokenizer-only.stdout.jsonl').write_bytes(r.stdout);(ROOT/'work/tokenizer-only.stderr.log').write_bytes(r.stderr)
    if r.returncode:raise RuntimeError('vocab-only tokenization failed')
    rows=[json.loads(line) for line in r.stdout.splitlines()];assert [v['task_id'] for v in rows]==selected and all(v['forward_calls']==0 and v['vocab_only'] for v in rows)
    save(STUDY/'INPUT_CONTRACT.json',{'utc':now(),'input_hashes':{t:digest(b.encode('utf-8')) for t,b in inputs.items()},'reserved_tokens':{v['task_id']:{'prompt_ids':v['prompt_ids'],'prompt_array_sha256':ah(v['prompt_ids']),'formatted_input_sha256':digest(format_prompt(inputs[v['task_id']]).encode('utf-8'))} for v in rows},'tokenizer_source_sha256':digest(worker.read_bytes()),'tokenizer_exe_sha256':digest(exe.read_bytes()),'build_command':cmd,'command':command,'model_forward_calls':0,'sampling_calls':0,'context_creations':0,'template':'Qwen3 no-tools native formatting with enable_thinking=false; one terminal LF removed by common CLI --file loader','status':'PASS'})
    print('24 reserved vocab-only input contracts PASS; forward=0')
if __name__=='__main__':main()
