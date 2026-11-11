"""Freeze one short native EOG diagnostic; no model forward or timing sample."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys
from gguf_metadata import Reader

def main():
    p=argparse.ArgumentParser()
    for key in ('runtime','build','target','admission','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();sys.dont_write_bytecode=True;sys.path.insert(0,str(a.runtime.resolve()));from common import need,read,save,sha
    need(not a.out.exists(),'Fresh explicitly versioned EOG diagnostic');a.out.mkdir(parents=True)
    spec=read(Path(__file__).parent/'models.json')['target'];need(a.target.stat().st_size==spec['bytes'] and sha(a.target)==spec['sha256'],'Exact already-admitted14B bytes')
    build=read(a.build/'BUILD.json');need(build['role']=='vocabulary_only_not_reference' and sha(build['executable'])==build['executable_sha256'],'Pristine no-forward vocabulary utility')
    for path,h in read(a.build/'DEPENDENCIES.json')['files'].items():need(sha(path)==h,'Vocabulary dependency changed')
    meta,_=Reader(a.target).metadata();template_sha=hashlib.sha256(meta['tokenizer.chat_template'].encode()).hexdigest()
    admitted=read(a.admission/'native-01/native/result.json');need(template_sha==admitted['target_model']['chat_template_sha256'],'Admitted target template binding')
    # Explicit controlled ChatML/closed-thinking prefix, not a new natural root
    # and not a claim of executing an external Jinja implementation.
    prompt='<|im_start|>user\nReply with exactly one word: OK.<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
    query=dict(task_id='D14/termination-fixture-v1',formatted_prompt=prompt,add_special=False)
    env=dict(os.environ);env['CUDA_VISIBLE_DEVICES']='';env.pop('LD_PRELOAD',None)
    with (a.out/'vocabulary.stdout.jsonl').open('xb') as out,(a.out/'vocabulary.stderr.log').open('xb') as err:
        result=subprocess.run([build['executable'],str(a.target)],input=(json.dumps(query)+'\n').encode(),stdout=out,stderr=err,env=env,timeout=300)
    need(result.returncode==0,'No-forward diagnostic tokenization failed')
    rows=[json.loads(x) for x in (a.out/'vocabulary.stdout.jsonl').read_text().splitlines()];need(rows[0]['forward_calls']==0 and rows[0]['context_creations']==0,'Tokenization-only contract')
    tokens=rows[1]['prompt_ids'];need(rows[1]['native_detokenized_prompt']==prompt,'Exact native prompt roundtrip')
    fixture=dict(id=query['task_id'],family='Qwen14B',prompt_ids=tokens,prompt_tokens=len(tokens),cap=128,
        prompt_ids_sha256=hashlib.sha256(json.dumps(tokens,separators=(',',':')).encode()).hexdigest())
    save(a.out/'FIXTURE.json',dict(inputs=[fixture],formatted_prompt=prompt,formatted_prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        target_sha256=spec['sha256'],admitted_template_sha256=template_sha,native_helper_sha256=build['executable_sha256'],
        purpose='Termination semantic diagnostic because all four original14B development references reached CAP128; not a natural benchmark or formal timing root',
        selection='One fixed short instruction registered before its own reference/candidate outcomes; no literal answer forced by the controller',
        model_forwards=0,formal_samples_added=0))
    print('EOG_DIAGNOSTIC_FROZEN_NO_FORWARD',len(tokens),flush=True)

if __name__=='__main__':main()
