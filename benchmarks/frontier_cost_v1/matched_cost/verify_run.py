"""Re-read saved blobs and independently check every reported equality and work total."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path,PurePosixPath


def verify(directory):
    directory=Path(directory);run=json.loads((directory/'RUN.json').read_text())
    result_path=directory/'native/RESULT.json';data=result_path.read_bytes();result=json.loads(data)
    if hashlib.sha256(data).hexdigest()!=run['result']['sha256']:raise ValueError('result binding differs')
    job=json.loads((directory/'JOB.json').read_text());inputs={c['name']:c for c in job['cases']}
    cache={};pairs=0;total={'contexts':0,'native_calls':0,'target_rows':0}

    def payload(record):
        rel=PurePosixPath(record['path'])
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('unsafe blob path')
        key=record['path']
        if key not in cache:
            data=(directory/'native'/Path(*rel.parts)).read_bytes()
            if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']:raise ValueError('blob digest mismatch')
            cache[key]=data
        return cache[key]

    fields={'initial_state':'initial_state','full_operation_vectors':'operation_vectors','final_state':'final_state',
            'full_continuation_vector':'continuation_vector','continuation_state':'continuation_state'}

    def check(reference,candidate):
        nonlocal pairs
        actual={}
        for name,blob in fields.items():
            actual[name]=payload(reference['captures'][blob])==payload(candidate['captures'][blob]);pairs+=1
        for name in ('initial_geometry','final_geometry','continuation_geometry'):actual[name]=reference[name]==candidate[name]
        if candidate['comparison']!=actual or candidate['qualified']!=all(actual.values()):raise ValueError('recorded equality is false')
        return all(actual.values())

    def work(case_name,q,record,warm=False):
        p=len(inputs[case_name]['history']);schedule=record['schedule']
        if sum(schedule)!=q or any(type(x)!=int or not 1<=x<=8 for x in schedule):raise ValueError('invalid schedule')
        calls=(p+31)//32+len(schedule)+1;rows=p+q+1
        if warm:calls+=(p+31)//32+len(schedule);rows+=p+q
        total['contexts']+=1;total['native_calls']+=calls;total['target_rows']+=rows
        if record['work']['outer_calls']!=len(schedule) or record['work']['target_rows']!=q:raise ValueError('outer operation accounting')
        histogram={}
        for value in schedule:histogram[str(value)]=histogram.get(str(value),0)+1
        if record['work']['physical_widths']!=histogram:raise ValueError('actual physical widths differ from promised schedule')
        for value in record['captures'].values():payload(value)

    references={};failed=False
    for cell in result['qualification']:
        key=(cell['case'],cell['q']);reference=cell['reference'];references[key]=reference
        work(*key,reference)
        for candidate in cell['candidates']:
            good=check(reference,candidate);failed|=not good;work(*key,candidate)
        if (cell['status']=='PASS')!=all(a['qualified'] for a in cell['candidates']):raise ValueError('cell status mismatch')
    if failed and result['measurements']:raise ValueError('timing ran after failed qualification')
    for m in result['measurements']:
        key=(m['case'],m['q']);check(references[key],m)
        if not math.isfinite(m['operation_seconds']) or m['operation_seconds']<=0:raise ValueError('invalid recorded duration')
        work(*key,m,warm=m['mode']=='one_shape_warmup_then_reset')
    expected={'contexts':result['work']['contexts'],'native_calls':result['work']['attempted_native_calls'],'target_rows':result['work']['attempted_target_rows']}
    if total!=expected:raise ValueError('independent work totals differ')
    if result['native_modules_before']!=result['native_modules_after']:raise ValueError('loaded module identities changed')
    bound={Path(k).name:v['sha256'] for k,v in run['libraries_before'].items()}
    if any(bound.get(k)!=v['sha256'] for k,v in result['native_modules_before'].items()):raise ValueError('actual module not bound by run')
    if sum(len(b) for b in cache.values())!=result['raw_bytes']:raise ValueError('unaccounted raw blob bytes')
    return {'status':'PASS_RECORDED_RESULT_AND_RAW_REPLAY','native_result_status':result['status'],
            'comparison_blob_pairs':pairs,'unique_verified_blobs':len(cache),'verified_raw_bytes':result['raw_bytes'],
            'independent_work':total,'measurement_records':len(result['measurements']),
            'GPU_qualification':'NOT_RUN' if result['backend']=='cpu' else 'LOCAL_DIAGNOSTIC_ONLY',
            'historical_GPU_reference_qualification':'NOT_ESTABLISHED','performance_claim':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);a=p.parse_args()
    print(json.dumps(verify(a.directory),indent=2))
