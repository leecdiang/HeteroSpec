#!/usr/bin/env python3
"""Independent offline validation of the RTX direct-ID evidence directory/archive."""
import argparse
import hashlib
import itertools
import json
import random
import re
import tarfile
import tempfile
from collections import Counter
from pathlib import Path

TASKS = [f'HumanEval/{n}' for n in (3,10,19,20,28,32,44,47,48,50,54,57,62,64,68,70,89,90,101,104,105,106,107,111,119,123,126,128,129,162)]
CONDITIONS = ('TARGET_REFERENCE','RTX_BATCHED_K2','RTX_SERIALIZED_K2')
ASSETS = {'target':'408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6','draft':'9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031','dataset':'b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef'}

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while chunk:=f.read(1024*1024):h.update(chunk)
    return h.hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def require(value,message):
    if not value:raise ValueError(message)

def safe(root,path):
    candidate=(root/path).resolve()
    require(candidate.is_relative_to(root.resolve()),f'path escapes evidence directory: {path}')
    return candidate

def validate(root,asset_root=None):
    manifest_path=root/'SHA256_MANIFEST.json'
    archive_manifest_verified=False
    if manifest_path.exists():
        contents=read(manifest_path)['files']
        actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p!=manifest_path}
        require(actual==set(contents),'archive contains missing/unmanifested files')
        for name,expected in contents.items():
            require(digest(safe(root,name))==expected,f'archive SHA-256 differs: {name}')
        archive_manifest_verified=True
    protocol=read(root/'protocol_v2.json')
    freeze=read(root/'runtime_freeze_manifest.json')
    records=read(root/'formal_records.json')
    analysis=read(root/'FORMAL_ANALYSIS.json')
    require(records['status']=='COMPLETE','formal attempt is incomplete')
    require(protocol['protocol_version']==freeze['protocol_version']==2,'protocol version differs')
    require(records['freeze_manifest_sha256']==digest(root/'runtime_freeze_manifest.json'),'freeze identity differs')
    require(records['protocol_sha256']==digest(root/'protocol_v2.json'),'protocol identity differs')
    require(freeze['starting_main']=='483c4cbd6cd72ae1cdcdbba4534a62fc1786f885','starting main differs')
    require(freeze['llama_commit']=='0cae43063cf15170e91a2ff4d034da0ecef4a1b2','runtime source differs')
    require(records['frozen_source_head']==freeze['source_head'],'frozen source differs')
    require(protocol['task_ids']==TASKS and protocol['conditions']==list(CONDITIONS) and protocol['repetitions']==3,'workload differs')
    require(protocol['qualification_rule']=='90/90 exact generated-ID pairs -> QUALIFIED; otherwise BLOCKED','qualification rule differs')
    require(protocol['schedule_seed']==2026092801,'schedule seed differs')
    rng=random.Random(2026092801)
    expected_schedule=[]
    for task in TASKS:
        for repetition in range(1,4):
            order=list(CONDITIONS)
            rng.shuffle(order)
            expected_schedule.append({'task_id':task,'repetition':repetition,'order':order})
    require(expected_schedule==protocol['schedule']==freeze['schedule']==records['schedule'],'schedule differs')
    require(protocol['command_templates']==freeze['command_templates'],'frozen commands differ')
    for name,expected in ASSETS.items():
        require(freeze['identity'][name]['sha256']==expected,f'{name} identity differs')
    require(read(root/'build_manifest.json')['identity']==freeze['identity'],'build manifest differs')
    require(digest(root/'instrumentation.patch')==hashlib.sha256(b'').hexdigest(),'runtime patch must be empty')
    for path,expected in freeze['source_files_sha256'].items():
        local=root/Path(path).name
        require(local.exists() and digest(local)==expected,f'frozen source bytes differ: {path}')
    require(records['post_execution_asset_rehash']=='PASS','post-execution asset rehash missing')
    env=read(root/'environment.json')
    after=read(root/'environment_after.json')
    for field in ('gpu','os','python','runtime_override_variables'):
        require(env[field]==freeze['environment'][field],f'environment differs: {field}')
        require(after[field]==env[field],f'post-execution environment differs: {field}')
    expected_order=[(b['task_id'],b['repetition'],c) for b in expected_schedule for c in b['order']]
    runs=records['runs']
    require(len(runs)==270,'expected 270 executions')
    keys=[(r['task_id'],r['repetition'],r['condition']) for r in runs]
    require(keys==expected_order,'execution order/membership differs')
    require(all(v==1 for v in Counter(keys).values()),'duplicate execution')
    indexed={key:r for key,r in zip(keys,runs)}
    for r in runs:
        rid=r['run_id']
        require(r['status']=='VALID' and r['process_returncode']==0,f'failed execution: {rid}')
        require(r['source_head']==records['freeze_commit'] and r['llama_commit']==freeze['llama_commit'],f'source identity differs: {rid}')
        require(r['identity']==freeze['identity'],f'model/dataset/binary hashes differ: {rid}')
        run_dir=root/'runs'/rid
        require(read(run_dir/'record.json')==r,f'per-run record differs: {rid}')
        for name,expected in r['files_sha256'].items():
            require(digest(safe(run_dir,name))==expected,f'raw file hash differs: {rid}/{name}')
        require(digest(safe(root,r['prompt_path']))==r['prompt_sha256'],f'prompt hash differs: {rid}')
        replacements={'{prompt}':r['command'][r['command'].index('--file')+1],'{native_log}':r['command'][r['command'].index('--log-file')+1],'{transcript}':r['command'][r['command'].index('--output-file')+1]}
        require(r['command']==[replacements.get(a,a) for a in freeze['command_templates'][r['condition']]],f'command differs: {rid}')
        ids=read(run_dir/'generated_ids.json')
        require(ids==r['generated_ids'] and all(type(t) is int and t>=0 for t in ids),f'token array differs: {rid}')
        canonical=json.dumps(ids,separators=(',',':')).encode('ascii')
        require(hashlib.sha256(canonical).hexdigest()==r['token_array_sha256'],f'token hash differs: {rid}')
        require(0<len(ids)<=128 and len(ids)==r['output_length']==r['runtime_generated_count'],f'token length differs: {rid}')
        # Independently recover committed IDs from native runtime events, not emitted text.
        # Lossless byte-to-character view; never UTF-8-decode individual token pieces.
        log=(run_dir/'native.log').read_bytes().replace(b'\r\n',b'\n').decode('latin-1')
        commit_lines=[line for line in log.splitlines() if re.match(r'^\d+\.\d\d\.\d{3}\.\d{3} D slot process_toke: id\s+0 \| task \d+ \| n_gen = ',line)]
        recovered=[]
        for position,line in enumerate(commit_lines,1):
            fields=line.split(' | ',2)[2]
            generation=int(fields.split('n_gen = ',1)[1].split(',',1)[0])
            remaining=int(fields.split('n_remaining = ',1)[1].split(',',1)[0])
            token=int(fields.split('next token:',1)[1].split()[0])
            require(generation==position and remaining==128-position,f'commit ordering/budget differs: {rid}')
            recovered.append(token)
        require(recovered==ids,f'direct-ID sidecar differs from native commits: {rid}')
        stop_eos='| stopped by EOS\n' in log
        stop_cap='| stopped by limit, n_gen = 128, n_predict = 128\n' in log
        require(stop_eos!=stop_cap and r['termination']==('EOS' if stop_eos else 'limit'),f'termination differs: {rid}')
        require(stop_eos or len(ids)==128,f'cap differs: {rid}')
        layers=re.findall(r'load_tensors: offloaded (\d+)/(\d+) layers to GPU',log)
        expected_layers=[('37','37')] if r['condition']=='TARGET_REFERENCE' else [('37','37'),('29','29')]
        require(layers==expected_layers,f'full offload differs: {rid}')
        devices=re.findall(r'llama_prepare_model_devices: using device ([^\n]+)',log)
        require(len(devices)==len(layers) and all(d.startswith('CUDA0 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)') for d in devices),f'CUDA0 placement differs: {rid}')
        require(devices==r['placement']['actual_devices'] and [list(x) for x in layers]==r['placement']['offload_layers'],f'placement record differs: {rid}')
        ubatches=[int(n) for n in re.findall(r'llama_context: n_ubatch\s*=\s*(\d+)',log)]
        require(ubatches[0]==(2 if r['condition']=='RTX_BATCHED_K2' else 1) and ubatches==r['placement']['context_ubatches'],f'ubatch differs: {rid}')
        require(re.findall(r'cached n_tokens = (\d+), memory_seq_rm \[0, end\)',log)==['0'],f'reset differs: {rid}')
    results={}
    absent=object()
    for candidate in CONDITIONS[1:]:
        comparisons=[]
        exact_by_prompt={t:0 for t in TASKS}
        for task in TASKS:
            for rep in range(1,4):
                a=indexed[(task,rep,CONDITIONS[0])]['generated_ids']
                b=indexed[(task,rep,candidate)]['generated_ids']
                differences=[(i,left,right) for i,(left,right) in enumerate(itertools.zip_longest(a,b,fillvalue=absent)) if left!=right]
                if differences:
                    i,left,right=differences[0]
                    row={'task_id':task,'repetition':rep,'exact':False,'first_divergent_generated_index':i,'reference_token':None if left is absent else left,'candidate_token':None if right is absent else right,'reference_length':len(a),'candidate_length':len(b)}
                else:
                    exact_by_prompt[task]+=1
                    row={'task_id':task,'repetition':rep,'exact':True,'first_divergent_generated_index':None,'reference_token':None,'candidate_token':None,'reference_length':len(a),'candidate_length':len(b)}
                comparisons.append(row)
        n=sum(exact_by_prompt.values())
        wholly=sum(v==3 for v in exact_by_prompt.values())
        status='QUALIFIED' if n==90 else 'BLOCKED'
        published=analysis['conditions'][candidate]
        require(published['comparisons']==comparisons,f'first-divergence analysis differs: {candidate}')
        require(published['exact_pairs']==n and published['wholly_exact_prompts']==wholly and published['qualification']==status,f'classification differs: {candidate}')
        stable={t:len({tuple(indexed[(t,r,candidate)]['generated_ids']) for r in (1,2,3)})==1 for t in TASKS}
        require(published['repeat_stability']==stable and published['repeat_stable_prompts']==sum(stable.values()),f'repeat stability differs: {candidate}')
        require(published['mismatch_prompts']==[t for t,n in exact_by_prompt.items() if n!=3],f'mismatch prompts differ: {candidate}')
        results[candidate]={'exact_pairs':n,'wholly_exact_prompts':wholly,'qualification':status}
    reference_stable={t:len({tuple(indexed[(t,r,CONDITIONS[0])]['generated_ids']) for r in (1,2,3)})==1 for t in TASKS}
    require(analysis['reference_repeat_stability']==reference_stable,'reference repeat stability differs')
    external_verified=False
    if asset_root:
        rel={'target':'models/gguf/Qwen3-8B-Q8_0.gguf','draft':'models/gguf/Qwen3-0.6B-Q8_0.gguf','dataset':'datasets/humaneval/HumanEval.jsonl.gz'}
        for name,path in rel.items():
            require(digest(asset_root/path)==ASSETS[name],f'external {name} bytes differ')
        for name,expected in freeze['identity']['binaries'].items():
            require(digest(asset_root/'tools/llama-b10839'/name)==expected,f'external binary bytes differ: {name}')
        external_verified=True
    return {'status':'PASS','executions_verified':270,'pairs_independently_recomputed':180,'tasks':30,'repetitions':3,'conditions':results,
            'native_commit_logs_verified':True,'source_bytes_verified':True,'archive_manifest_verified':archive_manifest_verified,
            'external_asset_bytes_verified':external_verified,
            'hash_verification_scope':'Frozen model/dataset/binary identities agree across all records. Omitted external assets are rehashed only when --asset-root is supplied; no GPU is needed.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence',type=Path)
    parser.add_argument('--asset-root',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.evidence.is_file():
        with tempfile.TemporaryDirectory(prefix='rtx-direct-id-verify-') as temp:
            root=Path(temp)
            with tarfile.open(args.evidence,'r:gz') as archive:
                for member in archive.getmembers():
                    require(member.isfile() or member.isdir(),'archive has link or special file')
                    safe(root,member.name)
                archive.extractall(root,filter='data')
            result=validate(root,args.asset_root)
    else:
        result=validate(args.evidence,args.asset_root)
    encoded=json.dumps(result,indent=2)+'\n'
    if args.output:
        args.output.write_text(encoded,encoding='utf-8',newline='\n')
    print(encoded)

if __name__=='__main__':
    main()
