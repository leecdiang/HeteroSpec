"""CPU-only reconstruction from immutable raw requests, processes and slot charges."""
import argparse
import collections
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
FAMILIES=['Qwen','SmolLM2','Llama']
ARMS=['R','PQ_A','PQ_B','QB','NATIVE_FAST']
def read(path):return json.loads(path.read_bytes())
def save(path,obj):path.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def require(ok,message):
    if not ok:raise ValueError(message)
def geo(items):
    items=list(items);require(items and all(math.isfinite(x) and x>0 for x in items),'invalid ratio')
    return math.exp(sum(math.log(x) for x in items)/len(items))
def signature(record):return record['output']
def work(record):return {k:v for k,v in record['workload'].items() if k!='graphs_reused'}
def checksum(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main(config_path,out):
    config=read(config_path);root=Path(config['run_root']);out.mkdir(exist_ok=False)
    contract=read(root/'MODEL_CONTRACT.json');events=[read(p) for p in sorted((root/'ledger').glob('*.json'))]
    charges={e['slot']:e for e in events};require(len(charges)==len(events),'duplicate charged slot')
    records={};workers={};problems=[];life=[];raw_audits=[]
    from audit_raw import audit_worker
    from verify_complete_capture import check as check_requested_rows
    for worker in sorted((root/'runs').glob('*/*/*')):
        if not worker.is_dir():continue
        key='/'.join(worker.relative_to(root/'runs').parts);workers[key]=worker
        cleanup=read(worker/'CLEANUP.json') if (worker/'CLEANUP.json').exists() else {}
        clean=cleanup.get('exit_verified') is True and cleanup.get('watchdog_failure') is None
        if not clean:problems.append({'worker':key,'error':'missing or failed cleanup'})
        if (worker/'LIFETIME.json').exists():life.append({'worker':key,**read(worker/'LIFETIME.json')})
        else:problems.append({'worker':key,'error':'missing lifetime'})
        module=read(worker/'MODULE_IDENTITY.json') if (worker/'MODULE_IDENTITY.json').exists() else {}
        identity=module.get('verified') is True
        if identity:
            arm=worker.name.split('_')[-1]
            variant='metadata4' if worker.parent.name in ['SmolLM2','Llama'] and 'PQ' in worker.name else 'original'
            build=config['builds'][variant]
            if key.startswith('calibration/'):
                # Calibration v1 identities are preserved in its original registration.
                build=read(HERE/'F0A_CALIBRATION.json')['builds'][variant]
            require(module['executable']==[str(Path(build['server']).resolve())],'module executable receipt differs')
            require(all(build['numerical_DLL_sha256'].get(name)==value for name,value in module['modules'].items()),'loaded numerical DLL receipt differs')
        for path in worker.glob('requests/*/RECORD.json'):
            record=read(path);slot=record['slot'];require(slot in charges and slot not in records,'unpaid/duplicate request')
            started=read(path.parent/'REQUEST_STARTED.json');body=started['body'];response=record['response'];family=record['family']
            ids=response['tokens'];eog=set(contract['families'][family]['eog'])
            output={'ids':ids,'eog_flags':[v in eog for v in ids],'length':len(ids),'terminal_id':ids[-1] if ids else None,
                    'stop_reason':{'eos':'EOG','limit':'CAP'}.get(response['stop_type'],response['stop_type']),
                    'cached_tokens':response['timings']['cache_n'],'truncated':response['truncated']}
            require(output==record['output'],'raw endpoint normalization differs')
            require(len(ids)==response['tokens_predicted'] and 0<len(ids)<=128,'length/cap mismatch')
            require(output['stop_reason'] in ['EOG','CAP'] and not output['truncated'] and output['cached_tokens']==0,'stop/cache mismatch')
            require((output['stop_reason']=='CAP' and len(ids)==128) or (output['stop_reason']=='EOG' and ids[-1] in eog),'terminal semantics')
            require(response['timings']['prompt_n']==len(body['prompt']),'prompt length mismatch')
            require(body['n_predict']==128 and body['cache_prompt'] is False and body['seed']==123 and body['temperature']==0,'request recipe drift')
            require(record['seconds']==(record['request_end_ns']-record['request_start_ns'])/1e9 and record['seconds']>0,'timer reconstruction differs')
            obs=response['hs_closeout'];require(obs['workload']==record['workload'] or {**obs['workload'],'counter_semantics_sha256':record['workload']['counter_semantics_sha256']}==record['workload'],'counter payload differs')
            require(obs['adapter']=='hsc89-v1' and obs['context']==1024 and obs['effective_batch']==1024,'native runtime contract')
            require(obs['target_ub']==(1 if record['arm']=='R' else 4) and obs['scope_mask']==(0 if record['arm'] in ['R','NATIVE_FAST'] else 3),'native UB/mask contract')
            require(obs['mode']==record['mode'] and obs['heavy_capture']==(record['mode']=='heavy'),'capture flags')
            require(obs['added_sync']==(record['mode']=='heavy') and obs['etw'] is False,'timed observation contamination')
            if record['stage'] in ['E1','E2']:
                task=next(t for t in config['panel'][family] if t['id']==record['task_id'])
                require(body['prompt']==task['prompt_ids'],'sealed input differs')
            records[slot]={'record':record,'worker':key,'raw_path':str(path.relative_to(root)),'exit_ok':clean,'identity_ok':identity}
        if key.startswith(('calibration/','E1/')) and (worker/'capture/observer.jsonl').exists():
            try:raw_audits.append({'worker':key,**audit_worker(worker,config['layers'][worker.parent.name],recover_append_offsets=key.startswith('calibration/')),'requested_row_completeness':check_requested_rows(worker)})
            except Exception as error:raw_audits.append({'worker':key,'status':'FAILURE','error':repr(error)})
    e1=read(root/'E1_SUMMARY.json') if (root/'E1_SUMMARY.json').exists() else {}
    raw_index={a['worker']:a for a in raw_audits};independent_e1={}
    for family in FAMILIES:
        cells=[]
        for i in range(12):
            errors=[];pairs={}
            for arm in ['R','PQ','QB']:
                pair=[records.get(f'E1/{family}/{i}/{arm}/{mode}') for mode in ['heavy','counts']]
                if not all(pair):errors.append(arm+' pair incomplete');continue
                a,b=pair;pairs[arm]=a
                if signature(a['record'])!=signature(b['record']) or work(a['record'])!=work(b['record']):errors.append(arm+' capture/count differs')
                if not all(v['exit_ok'] and v['identity_ok'] for v in pair):errors.append(arm+' placement/cleanup')
                if raw_index.get(a['worker'],{}).get('status')!='PASS_RAW_OWNERSHIP_AND_GEOMETRY':errors.append(arm+' strict raw audit')
            if len(pairs)==3:
                if not (signature(pairs['R']['record'])==signature(pairs['PQ']['record'])==signature(pairs['QB']['record'])):errors.append('deployed reference counterexample')
                pw=workers[pairs['PQ']['worker']];qw=workers[pairs['QB']['worker']]
                if checksum(pw/'capture/logits.f32')!=checksum(qw/'capture/logits.f32'):errors.append('PQ/QB full decision vector bytes differ')
                def causal(path):
                    selected={'decode':('role','phase','tokens','positions','sequence_ids','logits_mask','caller_batch','before','after','returncode'),
                              'draft_proposal':('ids','pending','n_past'),'sample':('role','phase','logits_index','selected_id','positions'),
                              'verify_decision':('proposal_ids','logits_indices','sampled_ids'),'verify_result':('proposed_ids','accepted_plus_last','query_indices','replay','rollback_count'),
                              'verify_rollback':('kept_position_next','actual_positions','accepted_ids'),'draft_reconciled':('positions','pending_id','next_target_position'),
                              'committed_token':('id','origin','output_index','pending_id','target_positions')}
                    result=[]
                    for line in path.read_bytes().splitlines():
                        v=json.loads(line);event=v.get('event')
                        if event not in selected:continue
                        fields=selected[event]
                        if event=='sample' and v['role']=='draft':fields=('role','phase','logits_index','positions','top1','top2','top1_score','top2_score')
                        result.append((event,{k:v[k] for k in fields}))
                    return result
                if causal(pw/'trace.jsonl')!=causal(qw/'trace.jsonl'):errors.append('PQ/QB canonical causal trace differs')
            cells.append({'input_index':i,'errors':errors})
        witness=any(a.get('q_gt_one_verification') for key,a in raw_index.items() if key.startswith('E1/'+family+'/') and key.endswith('_QB'))
        independent_e1[family]={'complete_qualified':all(not c['errors'] for c in cells) and witness,'q_gt_one_verification_witness':witness,'cells':cells}
        if e1.get(family,{}).get('status')=='QUALIFIED':require(independent_e1[family]['complete_qualified'],'independent E1 reconstruction contradicts qualification')
        fast_complete=family in config['eligible_fast']
        for i in range(12):
            values=[records.get(f'E1/{family}/{i}/{arm}/{mode}') for arm,mode in [('R','heavy'),('NATIVE_FAST','heavy'),('NATIVE_FAST','counts')]]
            if not all(values):fast_complete=False;continue
            reference,heavy,counts=values
            fast_complete &= signature(reference['record'])==signature(heavy['record'])==signature(counts['record']) and work(heavy['record'])==work(counts['record'])
            fast_complete &= all(v['exit_ok'] and v['identity_ok'] for v in values) and raw_index.get(heavy['worker'],{}).get('status')=='PASS_RAW_OWNERSHIP_AND_GEOMETRY'
        independent_e1[family]['fast_complete_qualified']=bool(fast_complete)
        if e1.get(family,{}).get('fast_qualified'):require(fast_complete,'independent FAST E1 contradiction')
    expected=[]
    def add(slot,stage,family,**fields):
        charged=charges.get(slot);raw=records.get(slot)
        status='COMPLETED' if raw else 'STARTED_WITHOUT_COMPLETED_RECORD' if charged else 'NOT_RUN'
        reason=None
        if status=='NOT_RUN':
            if fields.get('arm')=='NATIVE_FAST' and family not in config['eligible_fast']:reason='FAST calibration ineligible; preserved counterexample'
            elif stage=='E2' and e1.get(family,{}).get('status')!='QUALIFIED':reason='Family E1 blocked primary timing'
            elif fields.get('arm')=='NATIVE_FAST' and stage=='E2' and not e1.get(family,{}).get('fast_qualified'):reason='FAST held-out transfer not fully qualified'
            else:reason='Stopped by frozen family/arm qualification or execution gate; no retry or replacement'
        reference_match=None
        if raw:
            if stage=='calibration':ref=config['calibration'][family][fields['input_index']]['reference_output']
            else:
                source=records.get(f'E1/{family}/{fields["input_index"]}/R/heavy');ref=source['record']['output'] if source else None
            reference_match=raw['record']['output']==ref if ref is not None else None
        expected.append({'slot':slot,'stage':stage,'family':family,'status':status,'endpoint_reference_match':reference_match,**fields,**({'raw_path':raw['raw_path']} if raw else {}),**({'not_run_reason':reason} if reason else {})})
    for family in FAMILIES:
        for i in range(2):
            for arm in ['R','PQ','QB','NATIVE_FAST']:
                for mode in ['heavy','counts']:add(f'CAL/{family}/{i}/{arm}/{mode}','calibration',family,input_index=i,arm=arm,category=mode)
        for i in range(12):
            for arm in ['R','PQ','QB','NATIVE_FAST']:
                for mode in ['heavy','counts']:add(f'E1/{family}/{i}/{arm}/{mode}','E1',family,input_index=i,arm=arm,category=mode)
        for s in range(4):
            for i in range(12):
                for arm in ARMS:
                    for category in ['warmup','measured']:add(f'E2/{s}/{family}/{i}/{arm}/{category}','E2',family,session=s,input_index=i,arm=arm,category=category)
    require(len(expected)==1776,'request ceiling enumeration')
    require(set(records)<=set(x['slot'] for x in expected),'foreign scientific slot')
    inputs=[];blocks=[];estimates={};worker_slots=[]
    def add_worker(slot):worker_slots.append({'slot':slot,'status':'STARTED' if slot in charges else 'NOT_RUN'})
    for family in FAMILIES:
        for i in range(2):
            for arm in ['R','PQ','QB','NATIVE_FAST']:add_worker(f'calibration/{family}/{i}_{arm}/LOAD')
        for i in range(12):
            for arm in ['R','PQ','QB','NATIVE_FAST']:add_worker(f'E1/{family}/{i:02d}_{arm}/LOAD')
        for s in range(4):
            for i in range(12):
                for arm in ARMS:add_worker(f'E2/{family}/s{s}_{i:02d}_{arm}/LOAD')
    require(len(worker_slots)==888,'worker ceiling enumeration')
    spec=importlib.util.spec_from_file_location('registered_estimator',HERE.parents[2]/'docs/experiments/rtx_jsa_closeout_v1/toolkit.py')
    toolkit=importlib.util.module_from_spec(spec);spec.loader.exec_module(toolkit)
    for family in FAMILIES:
        failures=[];normalized=[];family_blocks=[];valid_e1=independent_e1[family]['complete_qualified']
        for i in range(12):
            reference=records.get(f'E1/{family}/{i}/R/heavy')
            for s in range(4):
                arm_records={}
                for arm in ARMS[:4]:
                    for category in ['warmup','measured']:
                        slot=f'E2/{s}/{family}/{i}/{arm}/{category}';raw=records.get(slot)
                        if raw is None:failures.append(slot+' absent');continue
                        item=raw['record'];qualified=bool(valid_e1 and reference and signature(item)==signature(reference['record']) and raw['identity_ok'])
                        normalized.append({'family':'Qwen3' if family=='Qwen' else family,'session':s,'input_index':i,'arm':arm,'category':category,'seconds':item['seconds'],'qualified':qualified,'exit_ok':raw['exit_ok']})
                        if not qualified or not raw['exit_ok']:failures.append(slot+' qualification/cleanup')
                        if category=='measured':arm_records[arm]=item
                b={'family':family,'session':s,'input_index':i,'task_id':config['panel'][family][i]['id'],'stratum':config['panel'][family][i]['stratum'],
                   'block_status':'COMPLETE_CORE_BLOCK' if len(arm_records)==4 else 'NOT_RUN_OR_INCOMPLETE','completed_arms':len(arm_records),
                   **{a:arm_records[a]['seconds'] if a in arm_records else None for a in ARMS[:4]},
                   **{k:None for k in ['QB_over_dual_PQ','PQ_A_over_PQ_B','QB_over_R','dual_PQ_over_R']}}
                if len(arm_records)==4:
                    if not (work(arm_records['PQ_A'])==work(arm_records['PQ_B'])==work(arm_records['QB'])):failures.append(f'{s}/{i} speculative workload differs')
                    times={a:arm_records[a]['seconds'] for a in ARMS[:4]};mean=(times['PQ_A']+times['PQ_B'])/2
                    b.update({'QB_over_dual_PQ':times['QB']/mean,'PQ_A_over_PQ_B':times['PQ_A']/times['PQ_B'],'QB_over_R':times['QB']/times['R'],'dual_PQ_over_R':mean/times['R']})
                    family_blocks.append(b)
                blocks.append(b)
        if failures or not valid_e1:
            estimates[family]={'status':'NO_QUALIFIED_COMPLETE_COST_PANEL','E1_status':e1.get(family,{}).get('status','NOT_RUN'),'reasons':failures}
        else:
            estimate=toolkit.analyze('RTX','Qwen3' if family=='Qwen' else family,normalized)
            estimate['status']='SUPPORTED_FINITE_PANEL_GAIN' if estimate['practical_screen_pass'] else 'QUALIFIED_PRACTICAL_NEGATIVE'
            if 0<1-estimate['candidate_over_dual_control']<=estimate['aa_max_input']:estimate['status']='QUALIFIED_NOISE_LIMITED'
            estimate['stratum_ratios']={label:geo(b['QB_over_dual_PQ'] for b in family_blocks if b['stratum']==label) for label in ['short','medium','long']}
            estimates[family]=estimate
        for block in blocks:
            if block['family']==family:block['qualified_family_cost']=not failures and valid_e1
        for i,task in enumerate(config['panel'][family]):
            row={'family':family,'input_index':i,'task_id':task['id'],'stratum':task['stratum'],'prompt_tokens':task['prompt_token_count'],'E1_status':e1.get(family,{}).get('status','NOT_RUN'),'qualified_cost':not failures and valid_e1}
            if row['qualified_cost']:
                selected=[b for b in family_blocks if b['input_index']==i]
                row.update({key:geo(b[key] for b in selected) for key in ['QB_over_dual_PQ','PQ_A_over_PQ_B','QB_over_R','dual_PQ_over_R']})
                row['session_reversals']=sum(b['QB_over_dual_PQ']>=1 for b in selected)
            inputs.append(row)
        fast=[];fast_errors=[]
        if not independent_e1[family]['fast_complete_qualified']:fast_errors.append('FAST E1 or calibration not fully qualified')
        for s in range(4):
            for i in range(12):
                for category in ['warmup','measured']:
                    f=records.get(f'E2/{s}/{family}/{i}/NATIVE_FAST/{category}');q=records.get(f'E2/{s}/{family}/{i}/QB/{category}')
                    if not f or not q:fast_errors.append(f'{s}/{i}/{category} incomplete');continue
                    if not (f['exit_ok'] and f['identity_ok'] and signature(f['record'])==signature(q['record'])):fast_errors.append(f'{s}/{i}/{category} mismatch/cleanup')
                    if category=='measured':fast.append(q['record']['seconds']/f['record']['seconds'])
        estimates[family]['NATIVE_FAST']={'status':'QUALIFIED_COMPLETE_SECONDARY_PANEL','QB_over_NATIVE_FAST':geo(fast)} if not fast_errors and len(fast)==48 else {'status':'NO_QUALIFIED_COMPLETE_SECONDARY_COST','reasons':fast_errors}
    require(len(inputs)==36 and len(blocks)==144,'complete input/block enumeration')
    save(out/'ALL_888_WORKERS.json',worker_slots);save(out/'INDEPENDENT_E1.json',independent_e1)
    save(out/'ALL_1776_SLOTS.json',expected);save(out/'RAW_AUDITS.json',raw_audits)
    save(out/'PROCESS_LIFETIMES.json',life);save(out/'ESTIMATES.json',estimates);save(out/'INPUT_RESULTS.json',inputs);save(out/'BLOCK_RESULTS.json',blocks)
    for name,rows in [('INPUT_RESULTS.csv',inputs),('BLOCK_RESULTS.csv',blocks),('TIMING_RECORDS.csv',[{'slot':s,'seconds':v['record']['seconds'],'worker':v['worker'],'exit_ok':v['exit_ok'],'identity_ok':v['identity_ok']} for s,v in records.items() if v['record']['stage']=='E2'])]:
        with (out/name).open('x',encoding='utf-8',newline='') as stream:
            fields=list(dict.fromkeys(k for row in rows for k in row));writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    loads=[e for e in events if e['kind']=='load'];requests=[e for e in events if e['kind']!='load']
    require(set(e['slot'] for e in loads)<=set(x['slot'] for x in worker_slots),'foreign worker slot')
    summary={'status':'CPU_RAW_RECONSTRUCTION_COMPLETED','charged_workers':len(loads),'charged_requests':len(requests),'completed_requests':len(records),
             'slot_status_counts':dict(collections.Counter(x['status'] for x in expected)),'owned_worker_seconds':sum(x['seconds'] for x in life),
             'worker_ceiling':888,'request_ceiling':1776,'worker_problems':problems,'E1':{f:{k:v for k,v in e1.get(f,{}).items() if k not in ['inputs','reference_outputs']} for f in FAMILIES},
             'claims':estimates,'raw_capture_failures':[a for a in raw_audits if a['status']=='FAILURE'],'calibration_offset_metadata_failures_preserved':sum(a['status']=='APPEND_STREAM_RECOVERED_METADATA_FAILURE' for a in raw_audits)}
    require(len(loads)<=888 and len(requests)<=1776,'budget exceeded')
    save(out/'VERIFICATION.json',summary)
    with (out/'RAW_FILE_MANIFEST.jsonl').open('xb') as stream:
        for path in sorted(root.rglob('*')):
            if path.is_file():stream.write((json.dumps({'path':str(path.relative_to(root)),'bytes':path.stat().st_size,'sha256':checksum(path)})+'\n').encode())
    print(json.dumps({k:v for k,v in summary.items() if k not in ['claims','E1']},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.config,a.out)
