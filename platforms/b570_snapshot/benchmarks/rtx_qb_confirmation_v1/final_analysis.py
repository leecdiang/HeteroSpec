"""CPU-only reconstruction of complete E2/E1 evidence, including restored roots.

No native execution. Raw path strings are retained; archive path translation is
only an analysis view and never changes a scientific guard or record.
"""
import argparse
import collections
import csv
import json
import math
from pathlib import Path
import sys
import experiment as e
import export_e2_checkpoint as export
sys.path.insert(0,str(Path(__file__).parent/'e1_integration_v1'))
import run_e1 as diag
sys.path.insert(0,str(Path(__file__).parent/'analysis_helpers'))
import mechanism
import closeout

def csvfile(root,name,rows):
    if not rows:return
    with (root/name).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def e2_summary(root,original):
    frozen=e.read(root/'FREEZE.json');legacy=Path(e.read(root/'PLAN.json')['legacy'])
    for name in ('mechanism.py','closeout.py'):
        match=[item for item in frozen['files'] if Path(item['path'])==legacy/name]
        e.require(len(match)==1 and e.sha(Path(__file__).parent/'analysis_helpers'/name)==match[0]['sha256'],'independent workload helper identity differs')
    result=export.checkpoint_analysis(root,original)
    events=[e.read(p) for p in sorted((root/'ledger').glob('*.json'))]
    records=[e.read(p) for p in sorted((root/'runs').rglob('RECORD.json'))]
    measured={(r['followup_block']['session'],r['family'],r['condition'],r['task']):r for r in records if not r['warmup']}
    # Descriptive workload-contract comparison, not a newly optimized hypothesis.
    fields=('proposal_generated','proposal_verified','accepted_committed','first_mismatch_rejected','unexamined_after_mismatch',
            'terminal_discarded','initial_target_committed','bonus_committed','correction_committed','fallback_committed',
            'verify_cycles','rollback_calls','accepted_prefix_hist','cycle_progress_hist','verification_caller_width_hist',
            'attempted_positions','accepted_positions','draft_prefill_calls','draft_continuation_caller_calls',
            'target_prefill_calls','target_continuation_calls','target_verification_calls','target_replay_calls')
    economics=[]
    for (session,family,arm,task),left in measured.items():
        if arm!='C_PQ':continue
        right=measured[session,family,'C_QB',task]
        differs=[name for name in fields if left['workload'][name]!=right['workload'][name]]
        economics.append(dict(session=session,family=family,task=task,same_recorded_acceptance_and_logical_workload=not differs,
                              different_fields=';'.join(differs),scope='recorded counters/histograms; not full control-trace or kernel identity'))
    keys=('target_prefill_calls','target_continuation_calls','draft_prefill_calls','draft_continuation_caller_calls',
          'physical_micrograph_calls','physical_micrograph_rows','target_verification_calls','target_replay_calls')
    counters={k:sum(r.get('workload',{}).get(k,0) for r in records) for k in keys}
    counts=dict(native_workers=sum(x['kind']=='load' for x in events),native_requests=sum(x['kind']!='load' for x in events),
                completed_records=len(records),warmups=sum(r['warmup'] for r in records),
                references=sum(r['condition']=='R' and not r['warmup'] for r in records),
                comparisons=sum(r['condition']!='R' and not r['warmup'] for r in records),
                native_owned_seconds=math.fsum(e.read(p)['seconds'] for p in sorted((root/'runs').rglob('LIFETIME.json'))),
                failed_requests=len(list((root/'runs').rglob('FAILED.json'))),
                failed_blocks=sum(e.read(p)['status']!='COMPLETED' for p in (root/'blocks').glob('*.json')),
                invalid_contracts=sum(not r['contract_valid'] for r in records),
                workload_errors=sum(bool(r['workload_error']) for r in records),
                heavy_observer_flags=sum(any(r['observation'].values()) for r in records),
                output_mismatches=sum(len(c['mismatches']) for c in result['comparisons']),
                nonpositive_or_nonfinite_latency=sum(not math.isfinite(r['wall_ms']) or r['wall_ms']<=0 for r in records),
                observed_counters=counters,logical_model_caller_invocations=sum(counters[k] for k in keys[:4]),
                hardware_kernel_starts='UNKNOWN',latency_exclusions=0,
                latency_anomaly_rule='All raw latencies retained; original nonfinite/nonpositive validity only; no posthoc trimming',
                all_auxiliary_OS_process_starts='NOT_GLOBALLY_CAPTURED')
    return dict(analysis=result,counts=counts,economics=economics)

def e1_summary(root,original):
    plan=e.read(root/'PLAN.json');frozen=e.read(root/'FREEZE.json');readback=e.read(root/'AUTHENTICATED_READBACK.json')
    contract=e.read(root/'MODEL_CONTRACT.json')
    e.require(e.digest((root/'FREEZE.json').read_bytes())==readback['sha256'],'E1 authenticated freeze changed')
    e.require(readback['commit']=='fea46ef7ffa0f553b6aa5c9f1a26f6296f1cd1ca','unexpected E1 registration')
    events=[e.read(p) for p in sorted((root/'ledger').glob('*.json'))]
    e.require(len({x['slot'] for x in events})==len(events),'duplicate E1 started slot')
    build=e.read(root/'NATIVE_BUILD.json')
    for name,key in [('llama-server.exe','server_sha256'),('querylayout-replay.exe','replay_sha256')]:
        e.require(e.sha(root/'native/build/bin'/name)==build[key],'retained E1 native executable changed')
    all_records={}
    for path in sorted((root/'runs/e1').rglob('RECORD.json')):
        receipt=e.read(path.parent/'COMPLETED.json');e.require(e.sha(path)==receipt['record_sha256'],'E1 record receipt differs')
        row=e.read(path);e.require(row['slot'] not in all_records,'duplicate E1 record');all_records[row['slot']]=row
    contexts=[];numeric=[];full=[]
    for index,c in enumerate(plan['contexts']):
        path=root/'contexts'/f'{index:03d}.json'
        if not path.exists():
            contexts.append(dict(index=index,family=c['family'],layer=c['layer'],phase=c['phase'],q=c['q'],min_key=c['min_key'],
                                 task=c['task']['id'],status='UNSTARTED_OR_INCOMPLETE',capture_on_off_equal=None,key_extent=None,visible_mask_keys=None,
                                 own_path_QK=None,own_path_softmax=None,own_path_AV=None,repeatability_MQ=None,repeatability_PQ=None,repeatability_QB=None,
                                 operator_failures=0,error=None));continue
        raw=e.read(path);e.require(raw['index']==index and raw['context']==c,'E1 context matrix changed')
        result=raw['result'];records=raw['records'];folder=root/'runs/e1'/c['family']/c['id']
        if records:
            process=e.read(folder/'PROCESS.json');modules=e.read(folder/'MODULE_IDENTITY.json')
            e.require(e.read(folder/'COMMAND.json')['command'][0]==str(original/'native/build/bin/llama-server.exe'),'E1 executable command changed')
            e.require(modules['verified'] and modules['pid']==process['pid'],'actual native module/PID receipt failed')
            seen={Path(x['path']).name.lower():x['sha256'] for x in modules['modules']}
            pinned={name.lower():h for name,h in build['numerical_DLL_sha256'].items()}
            e.require(all(pinned.get(name)==h for name,h in seen.items()),'loaded numerical DLL identity differs')
            e.require({'ggml-base.dll','ggml-cuda.dll','cublas64_12.dll','cublaslt64_12.dll','cudart64_12.dll'}<=set(seen),'required actual modules absent')
        for i,r in enumerate(records):
            e.require(all_records[r['slot']]==r,'E1 summary/raw record differs')
            binding=e.read(folder/'REQUEST_BINDINGS'/f'{i:02d}.json')
            e.require(binding['selectors']==c['selectors'] and binding['selectors_verified_in_child_environment'],'lost E1 child selector')
            started=folder/'requests'/__import__('hashlib').sha256(r['slot'].encode()).hexdigest()[:24]/'REQUEST_STARTED.json'
            body=e.read(started)['body'];e.require(body==binding['body'] and json.loads(binding['wire_utf8'])==body,'actual request body differs')
            task=plan['warmups'][c['family']] if i==0 else c['task']
            e.require(body['prompt']==task['prompt_ids'] and body['n_predict']==task['cap'],'E1 input/cap changed')
            e.require(body['hs_closeout_mode']==('heavy' if i==1 else 'counts'),'E1 request mode changed')
            e.require(body['temperature']==0 and body['top_k']==0 and body['top_p']==1 and body['min_p']==0 and body['seed']==123 and body['cache_prompt']is False,'sampler/cache changed')
            out=r['output'];response=r['response'];model=contract['families'][c['family']];ids=out['ids']
            valid=(0<len(ids)<=task['cap'] and all(type(x)is int and 0<=x<model['vocabulary_tokens'] for x in ids)
                   and out['eog_flags']==[x in model['eog'] for x in ids] and not any(out['eog_flags'][:-1])
                   and out['length']==len(ids)==response['tokens_predicted'] and response['tokens']==ids and out['terminal_id']==ids[-1]
                   and out['stop_reason']==('EOG' if out['eog_flags'][-1] else 'CAP')
                   and (out['eog_flags'][-1] or len(ids)==task['cap']) and out['cached_tokens']==0 and out['truncated']is False
                   and response['timings']['prompt_n']==len(task['prompt_ids']))
            e.require(bool(valid)==r['contract_valid'],'independent output-contract reconstruction differs')
            obs=response['hs_closeout'];e.require(obs['scope_mask']==0 and obs['target_ub']==c['q'] and obs['context']==1024 and obs['effective_batch']==1024,'native observer geometry differs')
            heavy=i==1
            e.require(obs['adapter']=='hsc89-v1' and obs['mode']==body['hs_closeout_mode'] and obs['heavy_capture']==heavy
                      and obs['phase_timers']==heavy and obs['added_sync']==heavy and obs['etw']is False,'native observation mode differs')
            identity=closeout.digest(dict(native_source=build['source_inventory_sha256'],server=build['server_sha256'],DLLs=build['numerical_DLL_sha256'],
                                          models=model['models'],contract_sha256=e.sha(root/'MODEL_CONTRACT.json')))
            e.require(r['runtime_identity_verified'] and r['source_identity_sha256']==identity and r['actual_condition']==c['condition'],'actual native runtime/condition identity differs')
            work=r['workload'];error=None
            try:
                assert work['unsupported_replay']is False
                mechanism.workload_metrics(work,len(ids))
                assert work['draft_continuation_calls']==work['draft_continuation_rows']
            except (AssertionError,KeyError) as failure:error=repr(failure)
            e.require(bool(error)==bool(r['workload_error']),'independent workload-contract reconstruction differs')
        if len(records)==3:
            same=e.signature(records[1])==e.signature(records[2]);e.require(same==result['capture_on_off_full_equal'],'observer control changed')
        if 'numerical' in result:
            registry=e.read(root/'snapshot_registry'/f'{index:03d}.json')
            old=Path(registry['root']);e.require(old.is_relative_to(original),'snapshot outside original root')
            snap=root/old.relative_to(original)
            m=diag.admit_snapshot(snap,registry['registry'],c)
            recalculated=diag.numerical(snap,root/'operators'/f'{index:03d}')
            e.require(recalculated==result['numerical'],'E1 own-path/repeatability/numerical reconstruction differs')
            for pair in recalculated['pairs']:
                for stage,metrics in pair['stages'].items():
                    numeric.append(dict(index=index,family=c['family'],layer=c['layer'],phase=c['phase'],q=c['q'],
                                        key_extent=m['captured_key_extent'],pair=pair['pair'],stage=stage,
                                        qualification=recalculated['qualification']['qualification'],
                                        first_divergence_operator=pair['first_divergence_operator'],**metrics))
        g=result.get('geometry',{})
        qual=result.get('numerical',{}).get('qualification',{});own=qual.get('own_path',{});repeat=qual.get('repeatability',{})
        contexts.append(dict(index=index,family=c['family'],layer=c['layer'],phase=c['phase'],q=c['q'],min_key=c['min_key'],
                             task=c['task']['id'],status=raw['status'],capture_on_off_equal=result.get('capture_on_off_full_equal'),
                             key_extent=g.get('captured_key_extent'),visible_mask_keys=json.dumps(g.get('visible_mask_keys_per_query')),
                             own_path_QK=own.get('QK'),own_path_softmax=own.get('softmax'),own_path_AV=own.get('AV'),
                             repeatability_MQ=repeat.get('MQ'),repeatability_PQ=repeat.get('PQ'),repeatability_QB=repeat.get('QB'),
                             operator_failures=len(result.get('operator_failures',[])),error=result.get('error')))
        full.append(raw)
    counters=collections.Counter(r['status'] for r in contexts)
    records=list(all_records.values());workkeys=('target_prefill_calls','target_continuation_calls','draft_prefill_calls','draft_continuation_caller_calls','physical_micrograph_calls','physical_micrograph_rows')
    workload={k:sum(r.get('workload',{}).get(k,0) for r in records) for k in workkeys}
    native_seconds=math.fsum(e.read(p)['seconds'] for p in sorted((root/'runs/e1').rglob('LIFETIME.json')))
    operator_seconds=math.fsum(e.read(p)['seconds'] for p in sorted((root/'runs/operator').rglob('LIFETIME.json')))
    return dict(contexts=contexts,numerical=numeric,counts=dict(status='COMPLETED_MATRIX' if (root/'RUN_COMPLETE.json').exists() else 'STOPPED_OR_INCOMPLETE',
                coordinates=72,context_statuses=dict(counters),native_workers=sum(x['kind']=='load' for x in events),
                native_process_ID_receipts=len(list((root/'runs/e1').rglob('PROCESS.json'))),
                native_requests=sum(x['kind'] in ('warmup','request') for x in events),
                warmups=sum(r['warmup'] for r in records),operator_starts=sum(x['kind']=='operator' for x in events),
                failed_requests=len(list((root/'runs/e1').rglob('FAILED.json'))),
                operator_failures=sum(len(c['result'].get('operator_failures',[])) for c in full),
                native_worker_owned_seconds=native_seconds,operator_owned_seconds=operator_seconds,combined_native_owned_seconds=native_seconds+operator_seconds,
                logical_model_caller_invocations=sum(workload[k] for k in workkeys[:4]),observed_counters=workload,
                invalid_output_contracts=sum(not r['contract_valid'] for r in records),workload_errors=sum(bool(r['workload_error']) for r in records),
                compilation_command_seconds=sum(x['seconds'] for x in e.read(root/'NATIVE_BUILD.json')['attempts']),
                actual_native_CPU_selector_test_command_seconds=sum(x['seconds'] for x in e.read(root/'CPU-tests/RESULT.json')['attempts']),
                before_after_input_checks='Enforced before and after every replay by frozen code against retained immutable registry; no separate per-replay hash-dump files',
                hardware_kernel_starts='UNKNOWN',kernel_identity='UNKNOWN',reduction_tree='UNKNOWN'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--e2',type=Path,required=True);p.add_argument('--e1',type=Path,required=True)
    p.add_argument('--original-e2',type=Path,default=Path('D:/hs-qb-confirmation-v02'));p.add_argument('--original-e1',type=Path,default=Path('D:/hs104-e1-v1'))
    p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=False,parents=True)
    e2=e2_summary(a.e2,a.original_e2);e1=e1_summary(a.e1,a.original_e1)
    e.save(a.out/'E2_ANALYSIS.json',e2['analysis']);e.save(a.out/'E2_COUNTS.json',e2['counts']);e.save(a.out/'E1_ANALYSIS.json',e1)
    e.save(a.out/'COUNTS.json',dict(E2=e2['counts'],E1=e1['counts']))
    csvfile(a.out,'E1_CONTEXTS.csv',e1['contexts']);csvfile(a.out,'E1_NUMERICAL.csv',e1['numerical']);csvfile(a.out,'E2_ECONOMICS_COUNTERS.csv',e2['economics'])
    sessions=[];tasks=[]
    for c in e2['analysis']['comparisons']:
        sessions.extend(dict(family=c['family'],path=c['path'],**r) for r in c['session_log_contrasts'])
        tasks.extend(dict(family=c['family'],path=c['path'],**r) for r in c['task_ratios'])
    csvfile(a.out,'E2_SESSION_CONTRASTS.csv',sessions);csvfile(a.out,'E2_TASK_CONTRASTS.csv',tasks)
    groups=collections.defaultdict(list)
    for row in tasks:groups[row['family'],row['path'],row['task']].append(row)
    per_task=[]
    for (family,path,task),rows in sorted(groups.items()):
        e.require(len(rows)==6,'task does not have six retained session values')
        ratio=math.exp(math.fsum(r['log_latency_contrast'] for r in rows)/6)
        per_task.append(dict(family=family,path=path,task=task,six_session_geometric_ratio=ratio,
                             interpretation='regression' if ratio<1 else ('weak/no practical difference' if ratio<1.02 else 'practical improvement evidence'),
                             sessions_below_1=sum(r['speed_ratio']<1 for r in rows),
                             minimum_session_ratio=min(r['speed_ratio'] for r in rows),maximum_session_ratio=max(r['speed_ratio'] for r in rows),
                             inference='descriptive task contrast; no request bootstrap or task-level significance test'))
    csvfile(a.out,'E2_TASK_SUMMARY.csv',per_task)
    table=[]
    for session in range(6):
        start=e.read(a.e2/f'SESSION-{session}.json');end=e.read(a.e2/f'SESSION-{session}-COMPLETE.json')
        lives=[e.read(p)['seconds'] for p in (a.e2/'runs').rglob('LIFETIME.json') if f's{session}' in p.relative_to(a.e2).parts]
        table.append(dict(session=session,start_utc=start['utc'],complete_utc=end['utc'],wall_seconds=end['epoch']-start['epoch'],
                          native_workers=len(lives),native_requests=270,native_owned_seconds=math.fsum(lives)))
    csvfile(a.out,'E2_SESSION_TABLE.csv',table)
    print(json.dumps(dict(E2=e2['counts'],E1=e1['counts']),indent=2))
if __name__=='__main__':main()
