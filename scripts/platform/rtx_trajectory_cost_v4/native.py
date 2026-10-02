#!/usr/bin/env python3
"""Lossless native committed-ID transport, adapted additively from RTX v2; no timing inference."""
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

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'benchmarks/rtx_trajectory_cost_v4'
START = '483c4cbd6cd72ae1cdcdbba4534a62fc1786f885'
LLAMA = '0cae43063cf15170e91a2ff4d034da0ecef4a1b2'
TASKS = [f'HumanEval/{i}' for i in [3,10,19,20,28,32,44,47,48,50,54,57,62,64,68,70,89,90,101,104,105,106,107,111,119,123,126,128,129,162]]
SANITY = [f'HumanEval/{i}' for i in [3,10,19,20,106,129,50]]
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
    # The native log contains arbitrary token byte fragments, including rejected drafts.
    # Latin-1 preserves each byte; ID fields remain ASCII and need no text decoding.
    text = native.read_bytes().replace(b'\r\n', b'\n').decode('latin-1')
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
    # Native b10839 logs both conditions when its inclusive EOG is token 128.
    # Preserve both observations; canonical EOS takes precedence only for that
    # exact endpoint. Missing, duplicate or contradictory stops still fail.
    eog_ids = {128247,151643,151645,151662,151663,151664}
    terminal_eog = ids[-1] in eog_ids
    expected_stops = (['limit', 'EOS'] if terminal_eog else ['limit']) if len(ids) == 128 else ['EOS']
    if stops != expected_stops or (len(ids) < 128 and not terminal_eog) or any(t in eog_ids for t in ids[:-1]):
        raise ValueError('unsupported/missing termination status')
    termination = 'EOS' if terminal_eog else 'limit'
    offload = re.findall(r'load_tensors: offloaded (\d+)/(\d+) layers to GPU',text)
    expected_layers = [('37','37')] if condition in ('TARGET_REFERENCE','H1_TARGET_UB2') else [('37','37'),('29','29')]
    if offload != expected_layers:
        raise ValueError(f'target/draft full offload differs: {offload}')
    placements = re.findall(r'llama_prepare_model_devices: using device ([^\n]+)',text)
    if len(placements) != len(expected_layers) or any(not p.startswith('CUDA0 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)') for p in placements):
        raise ValueError(f'actual device differs: {placements}')
    ubatches = list(map(int,re.findall(r'llama_context: n_ubatch\s*=\s*(\d+)',text)))
    ub = 2 if condition in ('RTX_BATCHED_K2','H1_TARGET_UB2') else 1
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
    return {'generated_ids':ids,'token_array_sha256':array_sha(ids),'output_length':len(ids),'termination':termination,'native_stop_observations':stops,
            'capture_indices':[int(m.group(3)) for m in events],'runtime_generated_count':int(perf[0]),
            'placement':{'requested_target':'CUDA0','requested_draft':None if condition in ('TARGET_REFERENCE','H1_TARGET_UB2') else 'CUDA0',
                         'actual_devices':placements,'offload_layers':offload,'target_full_offload':True,
                         'draft_full_offload':None if condition in ('TARGET_REFERENCE','H1_TARGET_UB2') else True,'context_ubatches':ubatches,'fresh_cached_tokens':0},
            'auxiliary_decoded_bytes_hex':''.join(pieces).encode('latin-1').hex()}

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
                save(run_dir/'generated_ids.json',record['generated_ids'])
                transcript = (run_dir/'transcript.txt').read_bytes().replace(b'\r\n', b'\n')
                content = bytes.fromhex(record['auxiliary_decoded_bytes_hex'])
                # CLI file writer appends one newline when needed, then a second newline.
                # The pinned --file loader removes exactly one terminal LF.
                cli_prompt = prompt[:-1] if prompt.endswith('\n') else prompt
                expected_transcript = b'User:\n'+cli_prompt.encode('utf-8')+b'\n\nAssistant:\n'+content+(b'' if content.endswith(b'\n') else b'\n')+b'\n'
                if transcript != expected_transcript:
                    raise ValueError('committed decoded pieces differ from CLI transcript')
                record['auxiliary_transcript_integrity'] = True
            record['status'] = 'VALID'
        except Exception as exc:
            record['status'] = 'OPERATIONAL_FAILURE'
            record['error'] = str(exc)
    record['ended_utc'] = now()
    record['files_sha256'] = {p.name:sha(p) for p in sorted(run_dir.iterdir()) if p.is_file() and p.name!='record.json'}
    save(run_dir/'record.json',record)
    return record
