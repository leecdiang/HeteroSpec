"""CPU-only prospective input table. No roots are selected or model forwarded.

Answers/solutions are never loaded from parquet. The final exposure closure and
six-per-domain selection remain separate gates, before all new S3 model output.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unicodedata


def need(value,message):
    if not value:raise RuntimeError(message)


def read(path):return json.loads(Path(path).read_text())


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as f:
        for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
    return h.hexdigest()


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x')as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')


def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def main(root,work,out,admission):
    need(not out.exists(),'Fresh CPU input preparation');out.mkdir(parents=True);began=time.monotonic()
    c=read(admission);need(c['model']['sha256']=='efd971561896866f0e910cce52761ca77b1b138090c7f15fe284676d57d1f689','Exact32B target')
    sys.path.insert(0,str(work/'data-reader-01/isolated'));import pyarrow,pyarrow.parquet as pq
    need(pyarrow.__version__=='19.0.1','Fixed isolated parquet reader');pyarrow.set_cpu_count(2)
    from acquire_code import FILES,REVISION
    candidates=[];sources=[]
    for filename,length,expected in FILES:
        path=work/'codecontests'/Path(filename).name
        need(path.stat().st_size==length and sha(path)==expected,'Complete immutable code snapshot')
        split=Path(filename).name.split('-')[0]
        # Deliberately request ONLY problem input columns, never solution/test columns.
        rows=pq.read_table(path,columns=['name','description'],use_threads=False).to_pylist()
        sources.append(dict(domain='code',dataset='deepmind/code_contests',revision=REVISION,
                            shard=filename,bytes=length,sha256=expected,rows=len(rows),columns_read=['name','description']))
        for i,x in enumerate(rows):
            need(isinstance(x['description'],str)and x['description'].strip(),'Complete natural code statement')
            candidates.append(dict(id=f'CodeContests/{split}/{i}',domain='code',description=x['description'],
                 raw_prompt='Write Python code to solve the following programming problem.\n\n'+x['description'],
                 source_split=split,source_index=i,source_name=x['name'],source_revision=REVISION,
                 source_file=filename,source_sha256=expected,cap=128))
    oldpool=read(root/'f-confirmation-bundle-01/confirmation_v1/POOL.json')
    for x in oldpool['inputs']:
        if x['domain']=='math':
            candidates.append(dict(id=x['id'],domain='math',description=x['description'],raw_prompt=x['raw_prompt'],
                 source_split=x['source_split'],source_index=x['source_index'],source_revision=x['dataset_snapshot'],
                 source_sha256=x['source_snapshot_sha256'],cap=128))
    need(len({x['id']for x in candidates})==len(candidates),'Unique canonical problem IDs')
    save(out/'STATEMENT_UNIVERSE.json',dict(inputs=candidates,sources=sources,
         math_source=dict(path='F fixed50-statement math snapshot',sha256=sha(root/'f-confirmation-bundle-01/confirmation_v1/POOL.json')),
         roots_selected=False,answers_or_solutions_used=False,model_forwards=0))
    # Reuse the exact no-forward vocabulary helper linked to pristine R.
    folder=root/'f-vocabulary-build-03';build=read(folder/'BUILD.json');helper=build['executable']
    need(build['max_model_forwards']==0 and build['max_context_creations']==0 and sha(helper)==build['executable_sha256'],
         'Exact original CPU vocabulary-only helper')
    for p,d in read(folder/'DEPENDENCIES.json')['files'].items():need(sha(p)==d,'Vocabulary helper dependency changed')
    model=c['model']['path'];need(Path(model).stat().st_size==c['model']['bytes'],'Fixed target size')
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1');env.pop('HS_STRONG_GPU_ADMISSION_FILE',None)
    costs=[]
    def query(label,items):
        path=out/(label+'.stdout.jsonl');error=out/(label+'.stderr.log');start=time.monotonic()
        with path.open('xb')as stdout,error.open('xb')as stderr:
            result=subprocess.run([helper,model],input=''.join(json.dumps(x,ensure_ascii=False)+'\n'for x in items).encode(),
                 stdout=stdout,stderr=stderr,env=env,timeout=300)
        need(result.returncode==0,'CPU-only native vocabulary request failed')
        with path.open()as f:
            header=json.loads(f.readline());records=[json.loads(x)for x in f if x.strip()]
        need(header['vocab_only']is True and header['forward_calls']==header['context_creations']==0 and len(header['tokens'])==151936,
             'Complete native vocabulary/zero-forward header')
        need(len(records)==len(items)and all(x['forward_calls']==0 and x['vocab_only']is True for x in records),'Zero-forward query completeness')
        costs.append(dict(label=label,caller_s=time.monotonic()-start,stdout_sha256=sha(path),stderr_sha256=sha(error),
                          complete_vocabulary_sha256=digest(header)))
        return header,records
    historical=read(root/'run-01/inputs-01/Qwen-DEVELOPMENT.json')['inputs'][0]
    header,scaffold_rows=query('historical-scaffold',[dict(task_id='historical-scaffold',prompt_ids=historical['prompt_ids'],add_special=False)])
    need(scaffold_rows[0]['prompt_ids']==historical['prompt_ids'],'Existing Qwen token roundtrip changed')
    scaffold=scaffold_rows[0]['native_raw_piece_prompt'];marker='<|im_start|>user\n';end='<|im_end|>'
    need(scaffold.count(marker)==1 and scaffold.count('<|im_start|>assistant\n')==1,'Single original Qwen user/assistant scaffold')
    first=scaffold.index(marker)+len(marker);last=scaffold.index(end,first)
    need(last>first,'Original user body exists')
    suffix=scaffold[last:];prefix=scaffold[:first]
    # The exact existing assistant suffix is retained, including its original
    # thinking policy. No output length or EOG is used in this preparation.
    save(out/'SCAFFOLD.json',dict(prefix=prefix,suffix=suffix,original_prompt_sha256=digest(historical['prompt_ids']),
         source_helper_sha256=build['executable_sha256'],native_vocabulary_sha256=digest(header),
         existing_GGUF_template_metadata='Same exact32B GGUF; checked old template commitment ec8f439daaf5791f1da8686759109efa3f5ff5698cd407018a9f96a739c28fae',
         training_unseen_claim=False))
    items=[dict(task_id=x['id'],formatted_prompt=prefix+x['raw_prompt']+suffix,add_special=False)for x in candidates]
    repeated,records=query('prospective-whole-universe',items);need(header==repeated,'Native vocabulary/flags/EOG changed')
    by_id={x['task_id']:x for x in records};need(len(by_id)==len(items),'Unique native query identities')
    table=[]
    for x,item in zip(candidates,items):
        row=by_id[x['id']];ids=row['prompt_ids'];need(not row['add_special']and row['native_raw_piece_prompt']==item['formatted_prompt'],
             'No implicit special tokens or prompt truncation')
        text=' '.join(unicodedata.normalize('NFKC',x['description']).split())
        table.append(dict(x,prompt_ids=ids,prompt_tokens=len(ids),prompt_ids_sha256=digest(ids),
             formatted_prompt=item['formatted_prompt'],normalized_description_sha256=hashlib.sha256(text.encode()).hexdigest(),
             rank=hashlib.sha256(('heterospec-q32-strong-v1:'+x['id']).encode()).hexdigest(),
             length_eligible=1<=len(ids)<=192 and len(ids)+128<=1024))
    counts={domain:sum(x['domain']==domain and x['length_eligible']for x in table)for domain in ('code','math')}
    save(out/'TOKENIZED_UNIVERSE.json',dict(inputs=table,length_eligible_counts=counts,root_selection='NOT_DONE_REQUIRES_EXPOSURE_CLOSURE',
         model_forwards=0,context_creations=0,helper_costs=costs,caller_s=time.monotonic()-began,cap=128,
         no_truncation=True,no_generated_outputs_seen=True,scope='Input availability/eligibility only, not a numerical or performance result'))
    print(json.dumps(dict(status='ZERO_FORWARD_UNIVERSE_TOKENIZED_NOT_SELECTED',counts=counts,universe=len(table),caller_s=time.monotonic()-began)))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('root','work','out','admission'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();main(a.root,a.work,a.out,a.admission)
