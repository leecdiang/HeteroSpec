"""Validate a complete pinned PR221 run before exposing diagnostic macro costs.

This is an offline integrity boundary, not a certificate of clean resident
serving or historical R. No native library, model, or CUDA API is executed.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

SOURCE_SHA='4cc4c7114262bea71957e95478e963486a95cc416a0465d37bb897e971f838ec'
RUNNER_SHA='d10df8f66e5d2a31301445037b0bc8f3c5135e5086b29074e06cd38949299a8f'
LEGACY_CPU_RUNNER_SHA='2d365ee8f3ef6e7169b613ccce785e7bfafa4704e5cbfa5956f3e705c4ddf5b3'
MANIFEST_SHA='8d37214bb699565c535b52d3fd4439786f3e45c2d40a1aaff6db948c27366a1f'
TARGET_SHA='408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6'
MODES=('first_after_fresh_context','one_shape_warmup_then_reset')
CAPTURES=('initial_state','operation_vectors','final_state','continuation_vector','continuation_state')
GEOMETRIES=('initial_geometry','final_geometry','continuation_geometry')
COMPARISONS=('initial_state','initial_geometry','full_operation_vectors','final_state','final_geometry','full_continuation_vector','continuation_state','continuation_geometry')


class AdmissionError(ValueError):
    def __init__(self,code,detail=''):
        self.code=code
        super().__init__(code+(': '+detail if detail else ''))


def require(value,code,detail=''):
    if not value:raise AdmissionError(code,detail)


def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def read_json(path):
    def pairs(items):
        value={}
        for k,v in items:
            require(k not in value,'DUPLICATE_JSON_KEY',k);value[k]=v
        return value
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs)


def bound(path,record,role):
    require(Path(path).is_file(),'ASSET_ABSENT',role)
    require(type(record.get('bytes'))==int and Path(path).stat().st_size==record['bytes'] and digest(path)==record.get('sha256'),'BINDING_MISMATCH',role)


def schedules(q):
    plans=[]
    for width in (1,4,8):
        plan=(width,)*(q//width)+((q%width,) if q%width else ())
        if plan not in plans:plans.append(plan)
    return plans


def expected_panel(data):
    qs=data['q_values'];cases=data['cases']
    require(data['schema']=='heterospec.matched-local-inputs.v1' and data['repeats']==2,'INPUT_SCHEMA')
    require(qs==sorted(set(qs)) and qs and all(type(q)==int and 1<=q<=8 for q in qs),'INPUT_Q_SCOPE')
    require(1<=len(cases)<=2 and len({c['name'] for c in cases})==len(cases),'INPUT_CASE_SCOPE')
    stages={};contexts=0;qual=[];measure=[]
    def add(stage,calls,rows):
        r=stages.setdefault(stage,{'reserved_calls':0,'reserved_rows':0,'attempted_calls':0,'attempted_rows':0})
        for name in ('reserved_calls','attempted_calls'):r[name]+=calls
        for name in ('reserved_rows','attempted_rows'):r[name]+=rows
    def one(case,q,schedule,phase,warm):
        nonlocal contexts
        contexts+=1;p=len(case['history']);calls=(p+31)//32
        add(phase+'/prefill',calls,p);add(phase+'/operation',len(schedule),q);add(phase+'/continuation',1,1)
        if warm:add(phase+'/warmup',len(schedule),q);add(phase+'/reset_prefill',calls,p)
    for c in cases:
        require(1<=len(c['history'])<=512 and len(c['rows'])==8,'INPUT_TOKEN_SCOPE')
        require(all(type(t)==int and t>=0 for t in c['history']+c['rows']+[c['continuation']]),'INPUT_TOKEN_TYPE')
        for q in qs:
            qual.append((c['name'],q))
            for schedule in schedules(q):one(c,q,schedule,'qualification',False)
    for mode in MODES:
        for repeat in range(2):
            for c in cases:
                for q in qs:
                    order=schedules(q)
                    if repeat:order=order[::-1]
                    for schedule in order:
                        measure.append((c['name'],q,mode,repeat,schedule))
                        one(c,q,schedule,'measurement/'+mode,mode==MODES[1])
    calls=sum(r['attempted_calls'] for r in stages.values());rows=sum(r['attempted_rows'] for r in stages.values())
    work={'contexts':contexts,'reserved_native_calls':calls,'reserved_target_rows':rows,'attempted_native_calls':calls,'attempted_target_rows':rows,'by_stage':stages}
    return qual,measure,work


def validate_exact_run(directory,inputs,assets,expected_run_sha256):
    """Assets are explicit caller-supplied paths; receipt paths are never opened.

    The expected RUN hash must come from an external trusted publication/manifest.
    Rehashing the file under examination and supplying that hash is not trust.
    """
    directory=Path(directory)
    require(bool(re.fullmatch(r'[0-9a-f]{64}',expected_run_sha256)),'EXTERNAL_RUN_PIN_REQUIRED')
    require(digest(directory/'RUN.json')==expected_run_sha256,'RUN_PIN_MISMATCH')
    run=read_json(directory/'RUN.json')
    require(run.get('status')=='PASS' and run.get('returncode')==0 and run.get('native_status')=='PASS','RUN_NOT_SUCCESSFUL')
    bound(inputs,run['inputs'],'inputs');bound(directory/'JOB.json',run['job'],'JOB');bound(directory/'native/RESULT.json',run['result'],'RESULT')
    data=read_json(inputs);job=read_json(directory/'JOB.json');result=read_json(directory/'native/RESULT.json');plan=read_json(directory/'PLAN.json')
    for key in ('cases','q_values','repeats','threads'):require(job[key]==data[key],'JOB_INPUT_MISMATCH',key)
    require(run['plan']==plan,'PLAN_BINDING_MISMATCH')
    require(result.get('status')=='PASS' and result.get('timing_started') is True,'NATIVE_NOT_SUCCESSFUL')
    require(job['backend']==run['backend']==result['backend'],'BACKEND_MISMATCH')
    require(job['model']==run['model']['path'],'MODEL_PATH_BINDING')
    require(run['probe_source']['sha256']==SOURCE_SHA and run['source_manifest']['sha256']==MANIFEST_SHA,'UNSUPPORTED_SOURCE_SNAPSHOT')
    require(run['runner']['sha256'] in (RUNNER_SHA,LEGACY_CPU_RUNNER_SHA),'UNSUPPORTED_RUNNER_SNAPSHOT')
    require(run['checked_numerical_source_members']==3539,'SOURCE_MEMBERSHIP_COUNT')
    require(all(stage.get('returncode')==0 for stage in run['build_stages']) and len(run['build_stages'])==2,'BUILD_NOT_SUCCESSFUL')
    bindings={key:run[key] for key in ('runner','probe_source','model','source_manifest','binary')}
    bindings.update({'frontend/'+k:v for k,v in run['frontend_headers'].items()})
    before=run['libraries_before'];require(before==run['libraries_after'],'LIBRARIES_CHANGED')
    names={Path(k).name:v for k,v in before.items()}
    require(len(names)==len(before),'AMBIGUOUS_LIBRARY_NAMES')
    bindings.update({'library/'+k:v for k,v in names.items()})
    for role,record in bindings.items():
        require(role in assets,'ASSET_MAPPING_REQUIRED',role);bound(assets[role],record,role)
    require(job['expected_native_libraries']=={k:v['sha256'] for k,v in names.items()},'JOB_LIBRARY_BINDING')
    modules=result['native_modules_before'];require(modules==result['native_modules_after'],'ACTUAL_MODULES_CHANGED')
    required_prefixes=['libllama.so','libggml.so','libggml-base.so','libggml-cpu.so']
    if result['backend']=='cuda':required_prefixes.append('libggml-cuda.so')
    require(all(any(k.startswith(prefix) for k in modules) for prefix in required_prefixes),'INCOMPLETE_ACTUAL_MODULES')
    require(all(k in names and v=={'bytes':names[k]['bytes'],'sha256':names[k]['sha256']} for k,v in modules.items()),'UNBOUND_ACTUAL_MODULE')
    require(result['vocab']==job['expected_vocab']==data['model_binding']['expected_vocab'],'VOCAB_BINDING')
    qual_keys,measurement_keys,work=expected_panel(data)
    budget={'contexts':work['contexts'],'native_calls':work['attempted_native_calls'],'target_rows':work['attempted_target_rows']}
    require(job['budget']==plan['budget']==budget,'PLAN_BUDGET_MISMATCH')
    require(run['work']==result['work'],'RUN_WORK_BINDING')
    require(result['work']==work,'INCOMPLETE_OR_INCORRECT_WORK_LEDGER')
    require([(r['case'],r['q']) for r in result['qualification']]==qual_keys,'QUALIFICATION_PANEL_COVERAGE')
    actual_measurement_keys=[(r['case'],r['q'],r['mode'],r['repeat'],tuple(r['schedule'])) for r in result['measurements']]
    require(actual_measurement_keys==measurement_keys,'MEASUREMENT_PANEL_COVERAGE')
    cases={c['name']:c for c in data['cases']};blobs={};references={}
    def blob(record):
        h=record['sha256'];require(bool(re.fullmatch(r'[0-9a-f]{64}',h)) and record['path']=='blobs/'+h+'.bin','BLOB_PATH_BINDING')
        if h not in blobs:
            file=directory/'native'/record['path'];bound(file,record,'blob');blobs[h]=file.stat().st_size
        require(record['bytes']==blobs[h],'INCONSISTENT_BLOB_REFERENCE')
        return h
    def row(case,q,record,schedule,reference=None):
        require(tuple(record['schedule'])==schedule,'ACTION_SCHEDULE_MISMATCH')
        p=len(cases[case]['history']);histogram={str(k):v for k,v in Counter(schedule).items()}
        observed=record['work']
        require(observed['outer_calls']==len(schedule) and observed['target_rows']==q and observed['physical_calls']==len(schedule) and observed['physical_widths']==histogram,'PHYSICAL_ACTION_MISMATCH')
        require(all(type(observed[k])==int and observed[k]>=0 for k in ('graphs_built','graphs_reused')),'GRAPH_STATE_MISSING')
        require(set(record['captures'])==set(CAPTURES),'CAPTURE_COVERAGE')
        for capture in CAPTURES:blob(record['captures'][capture])
        require(record['captures']['operation_vectors']['bytes']==q*result['vocab']*4 and record['captures']['continuation_vector']['bytes']==result['vocab']*4,'FULL_VECTOR_SIZE')
        for key,next_position in zip(GEOMETRIES,(p,p+q,p+q+1)):
            g=record[key]
            require(g['dense_seq0'] is True and g['head_equals_next_by_native_guard'] is True and g['n_ubatch']==32 and g['n_ctx']==1024 and g['used']==g['occupied_end']==next_position,'STATE_GEOMETRY_MISMATCH')
        require(len(record['executions'])==len(schedule),'EXECUTION_COVERAGE')
        offset=0
        for execution,width in zip(record['executions'],schedule):
            require(execution['phase']=='VERIFY' and execution['width']==width and execution['position']==p+offset and execution['requested_rows']==list(range(width)) and execution['active_cells']==p+offset+width and len(execution['expected_extents'])==width,'EXECUTION_SCOPE_MISMATCH')
            offset+=width
        if reference is not None:
            require(record.get('qualified') is True and set(record['comparison'])==set(COMPARISONS) and all(v is True for v in record['comparison'].values()),'RECORDED_QUALIFICATION_FAILED')
            require(all(record['captures'][k]==reference['captures'][k] for k in CAPTURES) and all(record[k]==reference[k] for k in GEOMETRIES),'RAW_QUALIFICATION_FAILED')
    for cell in result['qualification']:
        key=(cell['case'],cell['q']);plans=schedules(cell['q'])
        require(cell['status']=='PASS' and len(cell['candidates'])==len(plans)-1,'CANDIDATE_PANEL_COVERAGE')
        reference=cell['reference'];row(*key,reference,plans[0]);references[key]=reference
        for candidate,schedule in zip(cell['candidates'],plans[1:]):row(*key,candidate,schedule,reference)
    for measurement in result['measurements']:
        key=(measurement['case'],measurement['q']);row(*key,measurement,tuple(measurement['schedule']),references[key])
        seconds=measurement['operation_seconds'];require(type(seconds) in (int,float) and math.isfinite(seconds) and seconds>0,'INVALID_TIMING')
    require(sum(blobs.values())==result['raw_bytes'] and len(blobs)==result['raw_unique_blobs'],'RAW_BLOB_ACCOUNTING')
    require({f.name for f in (directory/'native/blobs').iterdir() if f.is_file()}=={h+'.bin' for h in blobs},'UNACCOUNTED_BLOB_FILES')
    require(result['historical_GPU_reference_qualification']=='NOT_ESTABLISHED' and result['full_service_performance_claim'] is False,'REFERENCE_SCOPE_CHANGED')
    deployment={'model_sha256':run['model']['sha256'],'backend':run['backend'],'source_sha256':run['probe_source']['sha256'],
                'source_manifest_sha256':run['source_manifest']['sha256'],'frontend':{k:v['sha256'] for k,v in run['frontend_headers'].items()},
                'binary_sha256':run['binary']['sha256'],'actual_native_modules':modules,'GPU_preflight':run.get('GPU_preflight'),
                'context':{'n_ctx':1024,'n_batch':1024,'n_ubatch':32,'output_reserve':8,'KV_type':'F16','lowering':'LOCAL'}}
    return {'status':'EXACT_RUN_VALIDATED','run_sha256':expected_run_sha256,'input_sha256':run['inputs']['sha256'],
            'deployment':deployment,'deployment_sha256':canonical(deployment),'measurement_count':len(measurement_keys),
            'work':budget,'raw_bytes':result['raw_bytes'],'data':data,'run':run,'result':result}


def diagnostic_costs(validated):
    """Never promote capture-conditioned macro timings into online stage costs."""
    run=validated['run'];result=validated['result']
    out={k:validated[k] for k in ('run_sha256','input_sha256','deployment','deployment_sha256')}
    out.update(schema='heterospec.typed-macro-costs.v2',scope='CAPTURE_CONDITIONED_TARGET_OPERATION_ONLY',
               online_stage_cost_eligible=False,historical_R_qualified=False,full_service_performance_claim=False,
               timing_window=result['timing_window'],timing_condition=result['timing_state_condition'],macro_costs=[],stage_costs=[])
    if run['backend']!='cuda':out['status']='REJECTED_CPU_SMOKE_AS_DEPLOYMENT_COST';return out
    require(run['runner']['sha256']==RUNNER_SHA and run['model']['sha256']==TARGET_SHA,'UNSUPPORTED_CUDA_DEPLOYMENT')
    require(run.get('native_process',{}).get('timed_out') is False and run['native_process'].get('child_reaped') is True and run['native_process'].get('returncode')==0,'CUDA_PROCESS_RECEIPT')
    for key in ('git_before','git_after'):require(run[key]['status']=='CLEAN_COMMITTED_SUBTREE','CUDA_UNCOMMITTED_SOURCE')
    require(run['git_before']['subtree_tree_sha']==run['git_after']['subtree_tree_sha'],'CUDA_SOURCE_CHANGED')
    require(run.get('model_qualification',{}).get('status')=='ORIGINAL_PR213_TARGET_SHA_MATCHED','ORIGINAL_MODEL_BINDING_MISSING')
    gpu=run['GPU_preflight'];require(gpu['physical_index']>0 and gpu['physical_binding']['physical_index']==gpu['physical_index'] and gpu['visible_CUDA_device']['visible_device_count']==1,'PHYSICAL_GPU_BINDING_MISSING')
    cases={c['name']:c for c in validated['data']['cases']}
    for record in result['measurements']:
        case=cases[record['case']]
        out['macro_costs'].append({'history_sha256':canonical(case['history']),'candidate_rows_sha256':canonical(case['rows'][:record['q']]),
                                  'q':record['q'],'schedule':record['schedule'],'mode':record['mode'],'repeat':record['repeat'],
                                  'initial_state_sha256':record['captures']['initial_state']['sha256'],'initial_geometry':record['initial_geometry'],
                                  'operation_nanoseconds':record['operation_seconds']*1e9,'observed_work':record['work']})
    out['status']='VALIDATED_MACRO_DIAGNOSTIC_ONLY';return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--assets',type=Path,required=True,help='Explicit role -> local file mapping; files are read and hashed only')
    p.add_argument('--expected-run-sha256',required=True,help='External trusted publication pin; never copy a self-reported hash')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    require(not a.output.exists() and not a.output.is_symlink(),'FRESH_OUTPUT_REQUIRED')
    try:
        exact=validate_exact_run(a.run_dir,a.inputs,read_json(a.assets),a.expected_run_sha256)
        answer=diagnostic_costs(exact)
    except (AdmissionError,KeyError,ValueError,OSError) as error:
        answer={'schema':'heterospec.typed-macro-costs.v2','status':'REJECTED_COST_IMPORT','reason':str(error),
                'online_stage_cost_eligible':False,'macro_costs':[],'stage_costs':[]}
    with a.output.open('x') as f:json.dump(answer,f,indent=2);f.write('\n')
    print(json.dumps({'status':answer['status'],'macro_costs':len(answer['macro_costs']),'stage_costs':0}))


if __name__=='__main__':main()
