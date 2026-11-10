"""CPU-only identities and durable, exclusive state writes."""
import hashlib
import json
import math
import os
import re
from pathlib import Path


def need(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    def reject(value):
        raise ValueError('Nonfinite JSON: ' + value)
    def unique(pairs):
        result={}
        for key,value in pairs:
            need(key not in result,'Duplicate JSON key: '+key)
            result[key]=value
        return result
    return json.loads(Path(path).read_text(), parse_constant=reject,object_pairs_hook=unique)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def write(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.tmp-' + str(os.getpid()))
    with tmp.open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def fresh(path, value):
    p = Path(path)
    need(not p.exists(), 'Preserve existing output: ' + str(p))
    write(p, value)


def safe_relative(name):
    need(isinstance(name, str), 'Archive path must be text')
    p = Path(name)
    need(bool(name) and name not in ('.', '..') and not p.is_absolute() and
         '..' not in p.parts and '\\' not in name and ':' not in name and
         name == p.as_posix() and not any(ord(c)<32 for c in name),
         'Unsafe archive path')
    return p


def digest_value(value):
    need(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'SHA-256 syntax')
    return value


def positive(value):
    need(isinstance(value, (int, float)) and not isinstance(value, bool)
         and math.isfinite(value) and value > 0, 'Invalid duration')
    return float(value)


def config_echo(job):
    need(job['arm'] in ('G', 'B', 'C'), 'Unknown backend')
    expected = dict(n_ctx=1024, n_ubatch=32, output_reserve=32,
                    kv='F16', flash_attention=False, cuda_graphs=False)
    for key, value in expected.items():
        need(type(job[key]) is type(value) and job[key] == value, 'Configuration: ' + key)
    return {**expected, 'arm': job['arm'], 'cuda_initialized': False,
            'scope': 'CPU_PARSE_ONLY_NOT_GPU_QUALIFICATION'}


def historical_receipt(value):
    if 'service_seconds' in value and 'capture' in value:
        return dict(schema='candidate', heavy=value['capture'],
                    service_s=positive(value['service_seconds']))
    if 'service_s' in value and 'heavy' in value:
        return dict(schema='scalar-reference', heavy=value['heavy'],
                    service_s=positive(value['service_s']))
    raise ValueError('Unknown receipt schema; no zero substitution')


def module_files(value):
    result = []
    for path, entry in value.items():
        if isinstance(entry, str):
            digest = entry
        else:
            need(isinstance(entry, dict) and 'sha256' in entry, 'Module schema')
            digest = entry['sha256']
        digest_value(digest)
        result.append((path, digest))
    return sorted(result)


def normalize(rows, phase):
    """Reject malformed/incomplete records before estimating anything."""
    need(phase in ('S2', 'S3', 'REPLICA'), 'Unknown analysis phase')
    output = sorted(rows, key=lambda x: (x['block'], x['slot'], x['arm'], x['ordinal']))
    seen = set()
    workers = {}
    for r in output:
        need(r['operation_id'] not in seen, 'Duplicate operation')
        seen.add(r['operation_id'])
        need(r['arm'] in ('G', 'B', 'C') and r['role'] in ('warm', 'measured'), 'Role/arm')
        for k in ('block', 'slot', 'ordinal', 'q', 'output_rows', 'start_ns', 'end_ns',
                  'fence_ns', 'owned_ready_ns'):
            need(type(r[k]) is int and r[k]>=0, 'Noninteger/negative field: '+k)
        for k in ('input_sha256', 'config_sha256', 'output_sha256'):
            digest_value(r[k])
        need(r['unit'] == 's', 'Explicit seconds required')
        positive(r['elapsed_s'])
        start, stop = r['start_ns'], r['end_ns']
        need(stop > start and all(start <= r[k] <= stop for k in ('fence_ns', 'owned_ready_ns')),
             'Fence/output outside host interval')
        need(abs((stop-start)/1e9-r['elapsed_s']) < 1e-8, 'Clock unit mismatch')
        need(r['q']>0 and r['output_rows'] == r['q'] and r['all_outputs_owned'] is True,
             'Incomplete/aliased output')
        need(r['callback_continues'] is True, 'Observer truncated graph')
        if phase == 'S2':
            need(r['q'] == (4 if r['slot'] in (0,2) else 32), 'Cell width')
        else:
            tokens=r['tokens']
            need(isinstance(tokens,list) and 1<=len(tokens)<=128 and
                 all(type(t) is int and 0<=t<151936 for t in tokens) and
                 r['generated_tokens']==len(tokens), 'Missing/invalid complete token sequence')
            need(r['stop_reason'] in ('eog','cap') and
                 (r['stop_reason']!='cap' or len(tokens)==128), 'Stop/cap semantics')
        workers.setdefault(r['worker_id'], []).append(r)
    expected = {'S2':36,'S3':144,'REPLICA':54}[phase]
    need(len(workers) == expected and len(rows) == 2 * expected, 'Incomplete panel')
    for pair in workers.values():
        pair.sort(key=lambda x: x['ordinal'])
        need([r['role'] for r in pair] == ['warm', 'measured'], 'Missing/extra warmup')
        need(pair[1]['ordinal'] == pair[0]['ordinal'] + 1, 'Warmup is not adjacent')
        for key in ('input_sha256', 'config_sha256', 'slot', 'block', 'arm', 'q'):
            need(pair[0][key] == pair[1][key], 'Warmup mismatch: ' + key)
        need(pair[0]['end_ns'] <= pair[1]['start_ns'], 'Warm overlaps measurement')
        if phase in ('S3','REPLICA'):
            need(pair[0]['tokens']==pair[1]['tokens'] and
                 pair[0]['stop_reason']==pair[1]['stop_reason'], 'Warm/measurement semantics differ')
    measured = [r for r in output if r['role'] == 'measured']
    keys = {(r['slot'], r['block'], r['arm']) for r in measured}
    need(len(keys) == expected, 'Duplicate cell/root/round')
    slots, blocks = {'S2':(range(4),range(3)),'S3':(range(12),range(4)),
                     'REPLICA':(range(6),range(3))}[phase]
    need(keys == {(s, b, a) for s in slots for b in blocks for a in ('G','B','C')},
         'Missing arm/round/root')
    for s in slots:
        group=[r for r in measured if r['slot']==s]
        need(len({r['input_sha256'] for r in group})==1, 'Cell/root input changed')
        if phase in ('S3','REPLICA'):
            need(len({tuple(r['tokens']) for r in group})==1, 'Three-arm generated sequence mismatch')
    # The machine-generated ordering is checked using actual host intervals,
    # not directory enumeration or an arm field supplied by the analysis caller.
    from importlib.util import spec_from_file_location, module_from_spec
    spec=spec_from_file_location('sb217_design',Path(__file__).parent.parent/'design_checks.py')
    module=module_from_spec(spec);spec.loader.exec_module(module)
    schedule=module.plan()[{'S2':'q32_diagnostic','S3':'q32_panel','REPLICA':'q32_replica'}[phase]]
    actual=sorted(workers.values(),key=lambda pair:min(r['start_ns']for r in pair))
    for position,(pair,want) in enumerate(zip(actual,schedule)):
        first=min(pair,key=lambda r:r['ordinal'])
        need((first['arm'],first['slot'],first['block'])==
             (want['arm'],want['slot'],want['round']), 'Registered worker order')
        if position:
            need(max(r['end_ns']for r in actual[position-1]) <= min(r['start_ns']for r in pair),
                 'Workers overlap on the assigned device')
    return output
