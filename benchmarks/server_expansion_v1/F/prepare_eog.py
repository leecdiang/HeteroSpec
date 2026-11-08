"""Freeze one explicit termination fixture using the archived target scaffold.

Tokenization only. No reference/candidate model forward or performance sample.
"""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys

def main():
    p=argparse.ArgumentParser()
    for key in ('runtime','build','models','assets','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();sys.dont_write_bytecode=True;sys.path.insert(0,str(a.runtime.resolve()));from common import need,read,save,sha
    need(not a.out.exists(),'Fresh frozen EOG fixture');a.out.mkdir(parents=True)
    spec=read(Path(__file__).parent/'models.json');history=read(Path(__file__).parent/'HISTORICAL_LLAMA.json');checked=read(a.assets/'CHECKED.json')
    need(checked['passed'] and checked['full_native_pair_vocabulary_equal'],'Original complete native tokenizer binding first')
    source=a.assets/'target-vocabulary.stdout.jsonl'
    with source.open() as f:f.readline();scaffold=json.loads(f.readline())['native_detokenized_prompt']
    marker='<|start_header_id|>user<|end_header_id|>\n\n';need(scaffold.count(marker)==1,'One archived user turn')
    start=scaffold.index(marker)+len(marker);end=scaffold.index('<|eot_id|>',start)
    prompt=scaffold[:start]+'Reply with exactly one word: OK.'+scaffold[end:]
    build=read(a.build/'BUILD.json');need(build['role']=='vocabulary_only_not_reference' and sha(build['executable'])==build['executable_sha256'],'Unchanged pristine vocabulary utility')
    for path,h in read(a.build/'DEPENDENCIES.json')['files'].items():need(sha(path)==h,'Vocabulary dependency changed')
    env=dict(os.environ);env['CUDA_VISIBLE_DEVICES']='';env.pop('LD_PRELOAD',None);ids={}
    for role in ('target','draft'):
        model=a.models/spec[role]['filename'];need(model.stat().st_size==spec[role]['bytes'] and sha(model)==spec[role]['sha256'],'Exact original model file')
        query=dict(task_id='Llama/termination-fixture-v1',formatted_prompt=prompt,add_special=False)
        with (a.out/(role+'.stdout.jsonl')).open('xb') as out,(a.out/(role+'.stderr.log')).open('xb') as err:
            result=subprocess.run([build['executable'],str(model)],input=(json.dumps(query)+'\n').encode(),stdout=out,stderr=err,env=env,timeout=300)
        need(result.returncode==0,'Native no-forward fixture tokenizer')
        with (a.out/(role+'.stdout.jsonl')).open() as f:vocab=json.loads(f.readline());row=json.loads(f.readline())
        digest=hashlib.sha256(json.dumps(vocab,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        need(digest==history['vocabulary_sha256'] and vocab['forward_calls']==0 and vocab['context_creations']==0,'Full historical native vocabulary/zero-forward contract')
        need(row['native_detokenized_prompt']==prompt,'Exact fixture text roundtrip');ids[role]=row['prompt_ids']
    need(ids['target']==ids['draft'],'One target-rendered prompt, identical pair IDs')
    tokens=ids['target'];fixture=dict(id='Llama/termination-fixture-v1',family='Llama',prompt_ids=tokens,prompt_tokens=len(tokens),cap=128,
        prompt_ids_sha256=hashlib.sha256(json.dumps(tokens,separators=(',',':')).encode()).hexdigest())
    save(a.out/'FIXTURE.json',dict(inputs=[fixture],formatted_prompt=prompt,formatted_prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        archived_scaffold_receipt_sha256=sha(source),target_template_sha256=history['template_sha256'],draft_template_sha256=history['draft_template_sha256'],
        model_forwards=0,formal_samples_added=0,native_helper_sha256=build['executable_sha256'],
        policy='Preserve the already verified archived target template instance and replace only its single user content; no external template-engine claim or literal answer forced',
        purpose='All three original development references reached CAP128; one fixed genuine-native-EOG diagnostic before its own R/candidate outcomes'))
    print('LLAMA_EOG_FIXTURE_FROZEN_NO_FORWARD',len(tokens),flush=True)

if __name__=='__main__':main()
