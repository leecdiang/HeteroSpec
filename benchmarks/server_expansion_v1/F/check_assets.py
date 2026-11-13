"""Full-file identity, full native vocabulary/EOG and archived template checks.

This is zero-forward tokenizer preparation, not native numerical qualification.
"""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys, time
from historical_gguf import Reader

def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    for key in ('runtime','build','models','out','licenses'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();sys.dont_write_bytecode=True;sys.path.insert(0,str(a.runtime.resolve()));from common import need,read,save,sha
    need(not a.out.exists(),'Fresh zero-forward preparation epoch');a.out.mkdir(parents=True)
    here=Path(__file__).parent;spec=read(here/'models.json');history=read(here/'HISTORICAL_LLAMA.json');development=read(here/'HISTORICAL_DEVELOPMENT.json')['inputs']
    build=read(a.build/'BUILD.json');need(build['role']=='vocabulary_only_not_reference','No-forward tokenizer helper only')
    need(sha(build['executable'])==build['executable_sha256'],'Vocabulary helper changed')
    for path,h in read(a.build/'DEPENDENCIES.json')['files'].items():need(sha(path)==h,'Vocabulary compiler dependency changed: '+path)
    license_record=read(a.licenses/'SOURCE_AND_LICENSE.json');need(license_record['status']=='EXACT_PUBLIC_SOURCE_POINTERS_AND_LICENSE_SNAPSHOTS_CHECKED','Exact licensed source snapshots first')
    for row in license_record['licenses']:need(sha(a.licenses/'licenses'/row['name'])==row['sha256'],'License snapshot changed')
    vocab={};metadata={};roundtrip={};records=[]
    queries=''.join(json.dumps(dict(task_id=x['id'],prompt_ids=x['prompt_ids'],add_special=False),ensure_ascii=False)+'\n' for x in development)
    for role in ('target','draft'):
        s=spec[role];path=a.models/s['filename'];receipt=read(a.models/(role+'-VERIFIED.json'))
        need(receipt['verified'] and receipt['sha256']==s['sha256'] and receipt['bytes']==s['bytes'],'Complete acquisition receipt')
        need(path.stat().st_size==s['bytes'] and sha(path)==s['sha256'],'Actual complete model bytes/hash')
        meta,tensors=Reader(path).metadata();metadata[role]=meta
        save(a.out/(role+'-GGUF_METADATA.json'),dict(metadata=meta,tensors=tensors,weight_data_read=False,model_forwards=0))
        need(all(digest(meta[k])==h for k,h in history['tokenizer_metadata'][role].items()),'Historical tokenizer metadata differs: '+role)
        template=meta['tokenizer.chat_template'];expected=history['template_sha256' if role=='target' else 'draft_template_sha256']
        need(hashlib.sha256(template.encode()).hexdigest()==expected,'Actual historical chat template differs: '+role)
        env={k:v for k,v in os.environ.items() if k not in ('LD_PRELOAD',) and not k.startswith(('HS_','GGML_','HSC_','JSA_'))};env['CUDA_VISIBLE_DEVICES']=''
        began=time.monotonic()
        with (a.out/(role+'-vocabulary.stdout.jsonl')).open('xb') as out,(a.out/(role+'-vocabulary.stderr.log')).open('xb') as err:
            r=subprocess.run([build['executable'],str(path)],input=queries.encode(),stdout=out,stderr=err,env=env,timeout=300)
        need(r.returncode==0,'Native vocabulary-only utility failed: '+role)
        rows=[json.loads(x) for x in (a.out/(role+'-vocabulary.stdout.jsonl')).read_text().splitlines()];vocab[role]=rows[0]
        need(digest(rows[0])==history['vocabulary_sha256'],'Native vocabulary/EOG/flags differ from historical runtime: '+role)
        need(rows[0]['forward_calls']==0 and rows[0]['context_creations']==0,'No forward or context creation permitted')
        need([x['text'] for x in rows[0]['tokens']]==meta['tokenizer.ggml.tokens'],'Full native vocabulary versus GGUF tokens')
        roundtrip[role]={x['task_id']:x for x in rows[1:]}
        for x in development:need(roundtrip[role][x['id']]['prompt_ids']==x['prompt_ids'],'Archived native token roundtrip differs: '+x['id'])
        records.append(dict(role=role,bytes=s['bytes'],sha256=s['sha256'],template_sha256=expected,native_vocabulary_sha256=digest(rows[0]),
            full_native_tokens=len(rows[0]['tokens']),native_EOG=rows[0]['eog'],archived_roundtrips=len(development),
            helper_wall_s=time.monotonic()-began,helper_stdout_sha256=sha(a.out/(role+'-vocabulary.stdout.jsonl'))))
    need(vocab['target']==vocab['draft'],'Full native target/draft tokenizer/EOG/flag equality')
    for x in development:need(roundtrip['target'][x['id']]['native_detokenized_prompt']==roundtrip['draft'][x['id']]['native_detokenized_prompt'],'Pair prompt text roundtrip')
    save(a.out/'CHECKED.json',dict(status='EXACT_ASSETS_TOKENIZER_TEMPLATES_CHECKED_ZERO_FORWARD',passed=True,models=records,
        full_native_pair_vocabulary_equal=True,templates_verified_separately=True,target_template_render_once=True,
        target_draft_template_equality_required=False,model_forwards=0,context_creations=0,license_receipt_sha256=sha(a.licenses/'SOURCE_AND_LICENSE.json'),
        numerical_qualification='NOT_RUN',formal_performance='NOT_RUN',conversion_lineage='Exact original quantizer revision/bytes bound; original Meta checkpoint conversion process not independently certified'))
    print('LLAMA_EXACT_ASSETS_TOKENIZER_TEMPLATES_CHECKED',flush=True)

if __name__=='__main__':main()
