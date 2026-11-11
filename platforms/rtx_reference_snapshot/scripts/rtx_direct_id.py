#!/usr/bin/env python3
"""Prospectively frozen RTX direct-ID replication; standard library only."""
import argparse
import gzip
import hashlib
import json
import os
import platform
import random
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / 'benchmarks/rtx_direct_id_v1'
START = '483c4cbd6cd72ae1cdcdbba4534a62fc1786f885'
LLAMA = '0cae43063cf15170e91a2ff4d034da0ecef4a1b2'
TASKS = [f'HumanEval/{i}' for i in [3,10,19,20,28,32,44,47,48,50,54,57,62,64,68,70,89,90,101,104,105,106,107,111,119,123,126,128,129,162]]
SANITY = [f'HumanEval/{i}' for i in [3,10,19,20,106,129]]
CONDITIONS = ['TARGET_REFERENCE', 'RTX_BATCHED_K2', 'RTX_SERIALIZED_K2']
SEED = 2026092801
EXPECTED = {'target':'408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6', 'draft':'9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031', 'dataset':'b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef'}
PROMPT = 'Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n{humaneval_prompt}'
EVENT = re.compile(r'^\d+\.\d{2}\.\d{3}\.\d{3} D slot process_toke: id\s+(\d+) \| task (\d+) \| n_gen = (\d+), n_remaining = (-?\d+), next token:\s+(-?\d+) ', re.M)

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def array_sha(ids):
    return hashlib.sha256(json.dumps(ids,separators=(',',':')).encode('ascii')).hexdigest()

def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
    tmp.replace(path)

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

def environment():
    return {'captured_utc':now(),'os':platform.platform(),'python':sys.version,'python_executable':sys.executable,
            'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,memory.total,pci.bus_id','--format=csv,noheader'],text=True).strip(),
            'nvidia_smi':subprocess.check_output(['nvidia-smi'],text=True),
            'runtime_override_variables':{k:v for k,v in os.environ.items() if k.startswith(('LLAMA_','GGML_','CUDA_'))}}

def paths(asset_root):
    return {'target':str(asset_root/'models/gguf/Qwen3-8B-Q8_0.gguf'),'draft':str(asset_root/'models/gguf/Qwen3-0.6B-Q8_0.gguf'),
            'dataset':str(asset_root/'datasets/humaneval/HumanEval.jsonl.gz'),'binary_dir':str(asset_root/'tools/llama-b10839')}

def identities(asset_paths):
    result = {k:{'path':asset_paths[k],'sha256':sha(asset_paths[k])} for k in EXPECTED}
    for k in EXPECTED:
        if result[k]['sha256'] != EXPECTED[k]:
            raise RuntimeError(f'{k} hash differs')
    binary_dir = Path(asset_paths['binary_dir'])
    result['binaries'] = {p.name:sha(p) for p in sorted(binary_dir.iterdir()) if p.suffix.lower() in ('.exe','.dll')}
    result['binary_dir'] = str(binary_dir)
    result['version'] = subprocess.check_output([str(binary_dir/'llama-cli.exe'),'--version'],stderr=subprocess.STDOUT,text=True).strip()
    if 'build 10839, commit 0cae43063' not in result['version']:
        raise RuntimeError('wrong runtime version')
    return result

def templates(asset_paths):
    base = [str(Path(asset_paths['binary_dir'])/'llama-cli.exe'),'--model',asset_paths['target'],'--device','CUDA0','--n-gpu-layers','all','--fit','off',
            '--ctx-size','4096','--flash-attn','off','--ubatch-size','1','--file','{prompt}','--n-predict','128','--temp','0','--top-k','0','--top-p','1','--min-p','0',
            '--seed','123','--single-turn','--simple-io','--no-display-prompt','--no-warmup','--cache-ram','0','--chat-template-kwargs','{"enable_thinking":false}',
            '--log-verbosity','5','--perf','--log-file','{native_log}','--output-file','{transcript}']
    out = {}
    for condition in CONDITIONS:
        cmd = base.copy()
        if condition != 'TARGET_REFERENCE':
            cmd += ['--spec-type','draft-simple','--model-draft',asset_paths['draft'],'--spec-draft-device','CUDA0','--spec-draft-ngl','all','--spec-draft-n-max','2','--spec-draft-n-min','0']
        cmd[cmd.index('--ubatch-size')+1] = '2' if condition == 'RTX_BATCHED_K2' else '1'
        out[condition] = cmd
    return out

def schedule():
    rng = random.Random(SEED)
    blocks = []
    for task in TASKS:
        for rep in range(1,4):
            order = CONDITIONS.copy()
            rng.shuffle(order)
            blocks.append({'task_id':task,'repetition':rep,'order':order})
    return blocks

def parse_capture(native, condition):
    text = native.read_text(encoding='utf-8')
    events = list(EVENT.finditer(text))
    if not events:
        raise ValueError('no direct runtime commit events')
    if {m.group(1) for m in events} != {'0'} or len({m.group(2) for m in events}) != 1:
        raise ValueError('multiple slots/requests')
    if [int(m.group(3)) for m in events] != list(range(1,len(events)+1)):
        raise ValueError('missing, duplicate, or out-of-order generated commit index')
    if len(events) > 128 or any(int(m.group(4)) != 128-int(m.group(3)) for m in events):
        raise ValueError('output budget differs')
    ids = [int(m.group(5)) for m in events]
    if any(x < 0 for x in ids):
        raise ValueError('negative token ID')
    perf = re.findall(r'slot print_timing: id\s+0 \| task \d+ \|\s+eval time\s*=\s*[\d.]+ ms /\s*(\d+) tokens',text)
    if perf != [str(len(ids))]:
        raise ValueError('commit count differs from runtime generated count')
    stops = re.findall(r'slot process_toke: id\s+0 \| task \d+ \| stopped by (EOS|limit)',text)
    if len(stops) != 1 or (stops[0] == 'limit' and len(ids) != 128):
        raise ValueError('unsupported/missing termination status')
    offload = re.findall(r'load_tensors: offloaded (\d+)/(\d+) layers to GPU',text)
    expected_layers = [('37','37')] if condition == 'TARGET_REFERENCE' else [('37','37'),('29','29')]
    if offload != expected_layers:
        raise ValueError(f'target/draft full offload differs: {offload}')
    placements = re.findall(r'llama_prepare_model_devices: using device ([^\n]+)',text)
    if len(placements) != len(expected_layers) or any(not p.startswith('CUDA0 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)') for p in placements):
        raise ValueError(f'actual device differs: {placements}')
    ubatches = list(map(int,re.findall(r'llama_context: n_ubatch\s*=\s*(\d+)',text)))
    ub = 2 if condition == 'RTX_BATCHED_K2' else 1
    if not ubatches or ubatches[0] != ub:
        raise ValueError(f'target ubatch differs: {ubatches}')
    cached = re.findall(r'cached n_tokens = (\d+), memory_seq_rm \[0, end\)',text)
    if cached != ['0']:
        raise ValueError('request did not begin with fresh KV state')
    # Read raw decoded pieces only for auxiliary output integrity, never for ID comparison.
    pieces = []
    for event in events:
        tail = text[event.end():]
        piece = re.match(r"'(.*?)'\n(?=\d+\.\d{2}\.\d{3}\.\d{3} [A-Z] |\Z)",tail,re.S)
        if not piece:
            raise ValueError('decoded piece log is truncated')
        pieces.append(piece.group(1))
    return {'generated_ids':ids,'token_array_sha256':array_sha(ids),'output_length':len(ids),'termination':stops[0],
            'capture_indices':[int(m.group(3)) for m in events],'runtime_generated_count':int(perf[0]),
            'placement':{'requested_target':'CUDA0','requested_draft':None if condition=='TARGET_REFERENCE' else 'CUDA0',
                         'actual_devices':placements,'offload_layers':offload,'target_full_offload':True,
                         'draft_full_offload':None if condition=='TARGET_REFERENCE' else True,'context_ubatches':ubatches,'fresh_cached_tokens':0},
            'auxiliary_decoded_text':''.join(pieces)}

def execute(task, rep, condition, prompt, command_templates, out, identity, original=False):
    run_id = f'{task.replace("/","-")}-r{rep}-{condition}'+('-original' if original else '')
    run_dir = out/'runs'/run_id
    run_dir.mkdir(parents=True,exist_ok=False)
    prompt_path = run_dir/'prompt.txt'
    prompt_path.write_text(prompt,encoding='utf-8',newline='\n')
    replacements = {'{prompt}':str(prompt_path),'{native_log}':str(run_dir/'native.log'),'{transcript}':str(run_dir/'transcript.txt')}
    cmd = [replacements.get(a,a) for a in command_templates[condition]]
    if original:
        cmd[cmd.index('--log-verbosity')+1] = '4'
        i = cmd.index('--log-file')
        del cmd[i:i+2]
    record = {'run_id':run_id,'task_id':task,'repetition':rep,'condition':condition,'command':cmd,'started_utc':now(),
              'source_head':git('rev-parse','HEAD'),'llama_commit':LLAMA,'identity':identity,
              'stdout_path':f'runs/{run_id}/stdout.txt','stderr_path':f'runs/{run_id}/stderr.txt','native_log_path':f'runs/{run_id}/native.log',
              'prompt_path':f'runs/{run_id}/prompt.txt','transcript_path':f'runs/{run_id}/transcript.txt','prompt_sha256':sha(prompt_path),'status':'STARTED'}
    save(run_dir/'record.json',record)
    with (run_dir/'stdout.txt').open('wb') as stdout, (run_dir/'stderr.txt').open('wb') as stderr:
        try:
            p = subprocess.run(cmd,stdout=stdout,stderr=stderr,stdin=subprocess.DEVNULL,timeout=300)
            record['process_returncode'] = p.returncode
            if p.returncode:
                raise RuntimeError(f'process returncode {p.returncode}')
            if not original:
                record.update(parse_capture(run_dir/'native.log',condition))
                transcript = (run_dir/'transcript.txt').read_text(encoding='utf-8')
                content = record['auxiliary_decoded_text']
                # CLI file writer appends one newline when needed, then a second newline.
                # The pinned --file loader removes exactly one terminal LF.
                cli_prompt = prompt[:-1] if prompt.endswith('\n') else prompt
                expected_transcript = 'User:\n'+cli_prompt+'\n\nAssistant:\n'+content+('' if content.endswith('\n') else '\n')+'\n'
                if transcript != expected_transcript:
                    raise ValueError('committed decoded pieces differ from CLI transcript')
                record['auxiliary_transcript_integrity'] = True
                save(run_dir/'generated_ids.json',record['generated_ids'])
            record['status'] = 'VALID'
        except Exception as exc:
            record['status'] = 'OPERATIONAL_FAILURE'
            record['error'] = str(exc)
    record['ended_utc'] = now()
    record['files_sha256'] = {p.name:sha(p) for p in sorted(run_dir.iterdir()) if p.is_file() and p.name!='record.json'}
    save(run_dir/'record.json',record)
    return record

def dataset(asset_paths):
    with gzip.open(asset_paths['dataset'],'rt',encoding='utf-8') as f:
        tasks = {x['task_id']:x for x in map(json.loads,f)}
    return {task:PROMPT.replace('{humaneval_prompt}',tasks[task]['prompt']) for task in TASKS}

def r0(asset_root, out):
    ap = paths(asset_root)
    identity = identities(ap)
    env = environment()
    if env['runtime_override_variables']:
        raise RuntimeError('runtime override variables require review before R0')
    prompts, commands = dataset(ap), templates(ap)
    result = {'status':'STARTED','started_utc':now(),'formal':False,'sanity_tasks':SANITY,'identity':identity,'environment':env,'runs':[],'comparisons':[]}
    save(out/'r0.json',result)
    for task in SANITY:
        for condition in CONDITIONS:
            captured = execute(task,1,condition,prompts[task],commands,out,identity)
            result['runs'].append(captured)
            save(out/'r0.json',result)
            print(f'R0 capture {captured["run_id"]}: {captured["status"]}',flush=True)
            if captured['status'] != 'VALID':
                raise RuntimeError(captured.get('error'))
            original = execute(task,1,condition,prompts[task],commands,out,identity,original=True)
            result['runs'].append(original)
            a = out/captured['transcript_path']
            b = out/original['transcript_path']
            same = original['status']=='VALID' and a.read_bytes()==b.read_bytes()
            result['comparisons'].append({'task_id':task,'condition':condition,'original_vs_logged_transcript_bytes_exact':same})
            save(out/'r0.json',result)
            print(f'R0 original {original["run_id"]}: transcript exact={same}',flush=True)
            if not same:
                raise RuntimeError('logging changed emitted output or original execution failed')
    # Fresh processes already reset every request; replay the first task after all other sanity tasks.
    for condition in CONDITIONS:
        repeated = execute(SANITY[0],2,condition,prompts[SANITY[0]],commands,out,identity)
        first = next(r for r in result['runs'] if r['task_id']==SANITY[0] and r['condition']==condition and 'generated_ids' in r)
        same = repeated['status']=='VALID' and repeated['generated_ids']==first['generated_ids']
        result['runs'].append(repeated)
        result['comparisons'].append({'task_id':SANITY[0],'condition':condition,'reset_replay_direct_ids_exact':same})
        save(out/'r0.json',result)
        if not same:
            raise RuntimeError('R0 reset integrity failed')
    if not any(r.get('termination')=='limit' for r in result['runs']):
        raise RuntimeError('R0 did not exercise cap')
    result['status']='PASS'
    result['ended_utc']=now()
    save(out/'r0.json',result)
    print('R0 PASS: 39 executions; no formal data',flush=True)

def freeze(asset_root, r0_dir):
    result=json.loads((r0_dir/'r0.json').read_text())
    if result['status']!='PASS':
        raise RuntimeError('R0 has not passed')
    if git('status','--porcelain'):
        raise RuntimeError('commit all source and preregistration before freeze')
    if git('branch','--show-current')!='experiment/rtx-direct-id-qualification-v1':
        raise RuntimeError('wrong branch')
    ap=paths(asset_root)
    identity=identities(ap)
    if identity!=result['identity']:
        raise RuntimeError('R0 identities changed')
    protocol=json.loads((STUDY/'protocol_v1.json').read_text())
    if protocol['command_templates']!=templates(ap) or protocol['schedule']!=schedule():
        raise RuntimeError('protocol commands or schedule changed')
    selected=['scripts/rtx_direct_id.py','scripts/verify_rtx_direct_id.py','benchmarks/rtx_direct_id_v1/PREREGISTRATION.md','benchmarks/rtx_direct_id_v1/protocol_v1.json','benchmarks/rtx_direct_id_v1/instrumentation.patch','benchmarks/rtx_direct_id_v1/build_manifest.json','benchmarks/rtx_direct_id_v1/R0_REVIEW.md','benchmarks/rtx_direct_id_v1/NATIVE_CAPTURE_CONTRACT.md']
    manifest={'schema':'heterospec.rtx_direct_id.freeze.v1','created_utc':now(),'starting_main':START,'source_head':git('rev-parse','HEAD'),
              'source_tree':git('rev-parse','HEAD^{tree}'),'branch':git('branch','--show-current'),'llama_commit':LLAMA,
              'source_files_sha256':{p:sha(ROOT/p) for p in selected},'identity':identity,'environment':environment(),
              'command_templates':templates(ap),'schedule':schedule(),'r0_summary_sha256':sha(r0_dir/'r0.json'),'protocol_version':1}
    save(STUDY/'runtime_freeze_manifest.json',manifest)
    print('Freeze saved. Commit this manifest before formal execution.',flush=True)

def run(out):
    manifest=json.loads((STUDY/'runtime_freeze_manifest.json').read_text())
    protocol=json.loads((STUDY/'protocol_v1.json').read_text())
    if out.exists():
        raise RuntimeError('formal destination must not exist; no overwrite/resume/rerun')
    if git('status','--porcelain') or git('branch','--show-current')!=manifest['branch']:
        raise RuntimeError('dirty source or different branch')
    freeze_commit=git('rev-parse','HEAD')
    parents=git('rev-list','--parents','-n','1','HEAD').split()[1:]
    if parents!=[manifest['source_head']]:
        raise RuntimeError('formal HEAD must be the single manifest-only commit atop frozen source')
    changed=git('diff-tree','--no-commit-id','--name-only','-r','HEAD').splitlines()
    if changed!=['benchmarks/rtx_direct_id_v1/runtime_freeze_manifest.json']:
        raise RuntimeError('freeze commit changes other source')
    for path, expected in manifest['source_files_sha256'].items():
        if sha(ROOT/path)!=expected:
            raise RuntimeError(f'frozen source changed: {path}')
    ap={k:manifest['identity'][k]['path'] for k in EXPECTED}
    ap['binary_dir']=manifest['identity']['binary_dir']
    if identities(ap)!=manifest['identity']:
        raise RuntimeError('frozen assets changed')
    env=environment()
    if env['gpu']!=manifest['environment']['gpu'] or env['os']!=manifest['environment']['os'] or env['python']!=manifest['environment']['python'] or env['runtime_override_variables']!=manifest['environment']['runtime_override_variables']:
        raise RuntimeError('frozen environment changed')
    out.mkdir(parents=True)
    import shutil
    for filename in ['PREREGISTRATION.md','protocol_v1.json','runtime_freeze_manifest.json','instrumentation.patch','build_manifest.json','R0_REVIEW.md','NATIVE_CAPTURE_CONTRACT.md']:
        shutil.copyfile(STUDY/filename,out/filename)
    shutil.copyfile(ROOT/'scripts/verify_rtx_direct_id.py',out/'verify_rtx_direct_id.py')
    shutil.copyfile(ROOT/'scripts/rtx_direct_id.py',out/'rtx_direct_id.py')
    save(out/'environment.json',env)
    prompts=dataset(ap)
    record={'schema':'heterospec.rtx_direct_id.formal.v1','status':'STARTED','started_utc':now(),'freeze_commit':freeze_commit,
            'frozen_source_head':manifest['source_head'],'freeze_manifest_sha256':sha(STUDY/'runtime_freeze_manifest.json'),
            'protocol_sha256':sha(STUDY/'protocol_v1.json'),'schedule':protocol['schedule'],'runs':[]}
    save(out/'formal_records.json',record)
    for block in protocol['schedule']:
        for condition in block['order']:
            if git('rev-parse','HEAD')!=freeze_commit or git('branch','--show-current')!=manifest['branch'] or git('status','--porcelain'):
                record['status']='INVALIDATED_SOURCE_CHANGED'
                save(out/'formal_records.json',record)
                raise RuntimeError('source changed during formal execution')
            item=execute(block['task_id'],block['repetition'],condition,prompts[block['task_id']],manifest['command_templates'],out,manifest['identity'])
            record['runs'].append(item)
            save(out/'formal_records.json',record)
            print(f'[{len(record["runs"])}/270] {item["run_id"]}: {item["status"]}, length={item.get("output_length")}',flush=True)
            if item['status']!='VALID':
                record['status']='INCOMPLETE_OPERATIONAL_FAILURE'
                record['ended_utc']=now()
                save(out/'formal_records.json',record)
                raise RuntimeError('operational failure retained; no selective rerun')
    final_env=environment()
    if identities(ap)!=manifest['identity'] or any(final_env[f]!=manifest['environment'][f] for f in ('gpu','os','python','runtime_override_variables')):
        record['status']='INVALIDATED_ASSET_OR_ENVIRONMENT_CHANGED'
        record['ended_utc']=now()
        save(out/'formal_records.json',record)
        raise RuntimeError('frozen assets or environment changed during formal execution')
    save(out/'environment_after.json',final_env)
    record['post_execution_asset_rehash']='PASS'
    record['status']='COMPLETE'
    record['ended_utc']=now()
    save(out/'formal_records.json',record)
    print('Formal execution complete: 270 executions',flush=True)

def analyze(out):
    data=json.loads((out/'formal_records.json').read_text())
    if data['status']!='COMPLETE' or len(data['runs'])!=270:
        raise RuntimeError('cannot classify incomplete formal attempt')
    keyed={(r['task_id'],r['repetition'],r['condition']):r for r in data['runs']}
    if len(keyed)!=270:
        raise RuntimeError('duplicate record')
    result={'schema':'heterospec.rtx_direct_id.analysis.v1','primary_endpoint':'direct committed/generated token-ID sequence equality','formal_executions':270,'conditions':{}}
    for condition in CONDITIONS[1:]:
        comparisons=[]
        for task in TASKS:
            for rep in range(1,4):
                a=keyed[(task,rep,CONDITIONS[0])]['generated_ids']
                b=keyed[(task,rep,condition)]['generated_ids']
                index=next((i for i in range(max(len(a),len(b))) if i>=len(a) or i>=len(b) or a[i]!=b[i]),None)
                comparisons.append({'task_id':task,'repetition':rep,'exact':a==b,'first_divergent_generated_index':index,
                                    'reference_token':a[index] if index is not None and index<len(a) else None,
                                    'candidate_token':b[index] if index is not None and index<len(b) else None,
                                    'reference_length':len(a),'candidate_length':len(b)})
        count=sum(x['exact'] for x in comparisons)
        wholly=[t for t in TASKS if all(x['exact'] for x in comparisons if x['task_id']==t)]
        stability={}
        for task in TASKS:
            hashes=[keyed[(task,r,condition)]['token_array_sha256'] for r in range(1,4)]
            stability[task]=len(set(hashes))==1
        result['conditions'][condition]={'exact_pairs':count,'total_pairs':90,'wholly_exact_prompts':len(wholly),'total_prompts':30,
                                         'qualification':'QUALIFIED' if count==90 else 'BLOCKED','mismatch_prompts':[t for t in TASKS if t not in wholly],
                                         'repeat_stable_prompts':sum(stability.values()),'repeat_stability':stability,'comparisons':comparisons}
    result['reference_repeat_stability']={t:len({keyed[(t,r,CONDITIONS[0])]['token_array_sha256'] for r in range(1,4)})==1 for t in TASKS}
    save(out/'FORMAL_ANALYSIS.json',result)
    print(json.dumps({c:{k:v for k,v in r.items() if k in ['exact_pairs','wholly_exact_prompts','qualification','mismatch_prompts']} for c,r in result['conditions'].items()},indent=2))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['r0','freeze','run','analyze'])
    parser.add_argument('--asset-root',type=Path,default=Path('D:/HeteroSpec-PC'))
    parser.add_argument('--output',type=Path)
    parser.add_argument('--r0',type=Path)
    args=parser.parse_args()
    if args.stage=='r0':r0(args.asset_root,args.output)
    elif args.stage=='freeze':freeze(args.asset_root,args.r0)
    elif args.stage=='run':run(args.output)
    else:analyze(args.output)

if __name__=='__main__':
    main()
