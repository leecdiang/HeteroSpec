"""Prospectively registered vocabulary-only census of the approved natural source."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('original_census', ROOT.parent/'audit_pool.py')
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)


def main():
    plan = old.read(ROOT/'PREP_REGISTRATION.json')
    out = Path(plan['output'])
    out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    old.save(out/'PLAN.json', plan)
    for name, pin in plan['files'].items():
        if old.sha(pin['path']) != pin['sha256']:
            raise ValueError('identity drift: '+name)
    contract = old.read(plan['files']['model_contract']['path'])['families']
    source = old.read(plan['files']['projected_descriptions']['path'])
    tasks = [{'id':'CodeContests/valid/'+str(i), 'domain':'CODE',
              'snapshot':plan['dataset_snapshot'], 'original_name':row['name'],
              'original_source':row['source'], 'description':row['description'],
              'raw_prompt':plan['code_prefix']+row['description']} for i,row in enumerate(source)]
    old.save(out/'NATURAL_TASKS.json',tasks)
    spec = importlib.util.spec_from_file_location('native_metadata',plan['files']['metadata_reader']['path'])
    gguf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gguf)
    summary, rows, receipts = {}, [], []
    for family, c in contract.items():
        metadata, _ = gguf.Reader(c['models']['target']['path']).metadata()
        if metadata['tokenizer.chat_template'] != c['template']:
            raise ValueError('template drift')
        queries = [{'task_id':t['id'], 'formatted_prompt':old.render(c,t['raw_prompt'],metadata['tokenizer.ggml.tokens']),
                    'add_special':c['added_special_for_template']} for t in tasks]
        old.save(out/(family+'-QUERIES.json'),{'vocab_only':True,'forward_calls':0,'queries':queries})
        payload = ''.join(json.dumps(q,ensure_ascii=False)+'\n' for q in queries).encode()
        outputs = []
        for role in ('target','draft'):
            if time.perf_counter()-start > plan['owned_seconds']-plan['cleanup_seconds']:
                raise ValueError('static census time budget exhausted')
            slot = family+'-'+role
            command = [plan['files']['helper']['path'],plan['dll_directory'],c['models'][role]['path']]
            old.save(out/(slot+'-START.json'),{'command':command,'model_contexts':0,'model_requests':0})
            tick = time.perf_counter()
            process = subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                       creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:
                stdout, stderr = process.communicate(payload,timeout=plan['per_process_timeout_seconds'])
            except subprocess.TimeoutExpired:
                process.kill();stdout,stderr=process.communicate(timeout=plan['cleanup_seconds'])
                (out/(slot+'.stdout.jsonl')).write_bytes(stdout);(out/(slot+'.stderr.log')).write_bytes(stderr)
                old.save(out/(slot+'-EXIT.json'),{'exit_code':process.returncode,'timed_out':True})
                raise
            (out/(slot+'.stdout.jsonl')).write_bytes(stdout);(out/(slot+'.stderr.log')).write_bytes(stderr)
            receipt={'slot':slot,'pid':process.pid,'exit_code':process.returncode,'seconds':time.perf_counter()-tick,
                     'stdout_sha256':old.digest(stdout),'stderr_sha256':old.digest(stderr),'exit_verified':process.poll() is not None}
            old.save(out/(slot+'-EXIT.json'),receipt);receipts.append(receipt)
            if process.returncode:raise ValueError('vocabulary process failed')
            records=[json.loads(line) for line in stdout.splitlines()]
            v=records[0]
            if v['forward_calls'] or v['context_creations'] or old.digest(json.dumps(v,ensure_ascii=False,separators=(',',':')).encode())!=c['vocabulary_sha256']:
                raise ValueError('native vocabulary contract differs')
            outputs.append(records[1:])
        if outputs[0]!=outputs[1] or len(outputs[0])!=len(tasks):raise ValueError('target/draft difference')
        name='Qwen3' if family=='Qwen' else family
        for task,query,record in zip(tasks,queries,outputs[0]):
            if task['id']!=record['task_id'] or record['forward_calls']:raise ValueError('native task mismatch')
            ids=record['prompt_ids']
            rows.append({**task,'family':name,'prompt_ids':ids,'prompt_tokens':len(ids),
                         'formatted_prompt':query['formatted_prompt'],
                         'text_sha256':old.digest(' '.join(task['description'].split()).encode()),
                         'token_ids_sha256':old.digest(json.dumps(ids,separators=(',',':')).encode())})
        family_rows=[r for r in rows if r['family']==name]
        summary[name]={f'{lo}-{hi}':sum(lo<=r['prompt_tokens']<=hi for r in family_rows) for lo,hi in [(64,192),(256,448),(640,832)]}
        print(name,summary[name],flush=True)
    old.save(out/'NATIVE_INPUTS.json',rows)
    old.save(out/'CENSUS.json',{'status':'SOURCE_INVENTORY_ONLY_NOT_SELECTED','families':summary,
             'model_requests':0,'model_contexts':0,'vocabulary_only_processes':6,'process_receipts':receipts,
             'owned_seconds':time.perf_counter()-start})
    old.save(out/'RAW_MANIFEST.json',[{'name':p.name,'sha256':old.sha(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file()])


if __name__=='__main__':main()
