"""Execute the frozen E1/E2 panel once; retain all failed and unstarted slots."""
import argparse
import json
from pathlib import Path
import time
import traceback
import runner as r
from audit_raw import audit_worker


def logical_trace(worker):
    events=[json.loads(line) for line in (worker/'trace.jsonl').read_bytes().splitlines()]
    keys={'decode':['role','phase','tokens','positions','sequence_ids','logits_mask','caller_batch','before','after','returncode'],
          'draft_proposal':['ids','pending','n_past'],
          'sample':['role','phase','logits_index','selected_id','positions'],
          'verify_decision':['proposal_ids','logits_indices','sampled_ids'],
          'verify_result':['proposed_ids','accepted_plus_last','query_indices','replay','rollback_count'],
          'verify_rollback':['kept_position_next','actual_positions','accepted_ids'],
          'draft_reconciled':['positions','pending_id','next_target_position'],
          'committed_token':['id','origin','output_index','pending_id','target_positions']}
    return [{'event':event['event'],**{key:event[key] for key in keys[event['event']]}} for event in events if event.get('event') in keys]


def qualify_pair(records,worker,layers):
    r.require(len(records)==2 and r.signature(records[0])==r.signature(records[1]),'capture/count endpoint difference')
    counters=lambda record:{k:v for k,v in record['workload'].items() if k!='graphs_reused'}
    r.require(counters(records[0])==counters(records[1]),'capture/count state/workload difference')
    raw_audit=audit_worker(worker,layers)
    vectors,geometry=r.vectors(worker)
    r.require(vectors,'full decision vectors missing')
    r.require(set(layers)<={event['layer'] for event in geometry},'first/middle/last target-layer geometry missing')
    r.require(all(event['physical_key_extent']>=max(event['visible_keys']) for event in geometry),'visible keys exceed physical extent')
    r.require(all(event['Q']['ne'][2] % event['K']['ne'][2]==0 for event in geometry),'GQA geometry invalid')
    return {'vectors':vectors,'logical_trace':logical_trace(worker),
            'q_gt_one_verification':any(event['phase']=='continuation' and event['q_occupied']>1 for event in geometry),
            'geometry_records':len(geometry),'raw_audit':raw_audit}


def run_e1(config,root,native,state,ledger):
    outcomes={}
    for family in ['Qwen','SmolLM2','Llama']:
        family_out={'status':'NOT_RUN_CALIBRATION_FAILURE','inputs':[],'fast_qualified':False,'reference_outputs':{}}
        if family not in config['eligible_primary']:
            outcomes[family]=family_out;continue
        failed=False;fast_failed=False;witness=False
        for index,task in enumerate(config['panel'][family]):
            if failed:break
            pair_results={};records={};workers={};cell={'input_index':index,'task_id':task['id'],'arms':{}}
            arms=['R','PQ','QB']+(['NATIVE_FAST'] if family in config['eligible_fast'] and not fast_failed else [])
            for arm in arms:
                ident=f'{index:02d}_{arm}';r.save(root/'host'/f'E1_{family}_{ident}.json',r.host_gate(native,config))
                completed=[]
                try:
                    with r.worker(native,root,state,ledger,config,family,arm,'E1',ident) as active:
                        workers[arm]=active.d
                        for mode in ['heavy','counts']:completed.append(active.complete(task,f'E1/{family}/{index}/{arm}/{mode}',mode))
                    pair_results[arm]=qualify_pair(completed,active.d,config['layers'][family]);records[arm]=completed
                    cell['arms'][arm]={'status':'PAIR_QUALIFIED','worker':str(active.d),'records':completed,
                                       'geometry_records':pair_results[arm]['geometry_records']}
                except BaseException as error:
                    cell['arms'][arm]={'status':'QUALIFICATION_FAILURE','records':completed,'error':repr(error),'traceback':traceback.format_exc()}
                    if arm=='NATIVE_FAST':fast_failed=True
                    else:failed=True
                print('E1',family,index,arm,cell['arms'][arm]['status'],flush=True)
                if failed:break
            if not failed:
                reference=r.signature(records['R'][0]);family_out['reference_outputs'][task['id']]=reference
                failures=[]
                for arm in ['PQ','QB']:
                    if r.signature(records[arm][0])!=reference:failures.append(arm+' deployed reference mismatch')
                for key in ['vectors','logical_trace']:
                    if pair_results['PQ'][key]!=pair_results['QB'][key]:failures.append('PQ/QB matched-prefix '+key+' mismatch')
                witness |= pair_results['QB']['q_gt_one_verification']
                if 'NATIVE_FAST' in records and r.signature(records['NATIVE_FAST'][0])!=reference:fast_failed=True
                cell['primary_failures']=failures;failed=bool(failures)
            family_out['inputs'].append(cell);r.save(root/'E1_results'/f'{family}_{index:02d}.json',cell)
        family_out.update(status='REFERENCE_OBSERVER_OR_STATE_FAILURE' if failed else 'QUALIFIED' if witness else 'NO_Q_GT_ONE_WITNESS',
                          q_gt_one_verification_witness=witness,fast_qualified=family in config['eligible_fast'] and not fast_failed and not failed)
        outcomes[family]=family_out;r.save(root/'E1_results'/(family+'_SUMMARY.json'),family_out)
    r.save(root/'E1_SUMMARY.json',outcomes)


def schedule(config):
    rows=[];families=['Qwen','SmolLM2','Llama']
    for session in range(4):
        for family in families[session%3:]+families[:session%3]:
            for j in range(12):
                index=(j+session)%12;arms=['R','PQ_A','PQ_B','QB'];off=(session+index)%4;arms=arms[off:]+arms[:off]
                if family in config['eligible_fast']:arms.insert((session+index)%5,'NATIVE_FAST')
                for arm in arms:
                    for category in ['warmup','measured']:
                        rows.append({'slot':f'E2/{session}/{family}/{index}/{arm}/{category}','session':session,'family':family,'input_index':index,'arm':arm,'category':category})
    return rows


def run_e2(config,root,native,state,ledger):
    qualified=r.read(root/'E1_SUMMARY.json');rows=schedule(config);results=[];blocked=set()
    for first,second in zip(rows[::2],rows[1::2]):
        family=first['family'];arm=first['arm'];session=first['session'];index=first['input_index'];task=config['panel'][family][index]
        if family in blocked or qualified[family]['status']!='QUALIFIED':continue
        if arm=='NATIVE_FAST' and not qualified[family]['fast_qualified']:continue
        ident=f's{session}_{index:02d}_{arm}';r.save(root/'host'/f'E2_{family}_{ident}.json',r.host_gate(native,config))
        records=[]
        try:
            with r.worker(native,root,state,ledger,config,family,arm,'E2',ident) as active:
                for slot in [first,second]:
                    record=active.complete(task,slot['slot'],'counts',warmup=slot['category']=='warmup')
                    record.update({key:slot[key] for key in ['session','input_index','category']})
                    r.require(r.signature(record)==qualified[family]['reference_outputs'][task['id']],'timed request departed from E1 reference')
                    records.append(record)
            r.save(root/'E2_results'/(family+'_'+ident+'.json'),{'status':'COMPLETED','records':records,'cleanup_verified':True})
            results.extend(records)
        except BaseException as error:
            r.save(root/'E2_results'/(family+'_'+ident+'.json'),{'status':'FAILURE','records':records,'error':repr(error),'traceback':traceback.format_exc()})
            if arm!='NATIVE_FAST':blocked.add(family)
            else:qualified[family]['fast_qualified']=False
        print('E2',session,family,index,arm,len(records),flush=True)
    r.save(root/'TIMING_RECORDS.json',results)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True);parser.add_argument('--commit',required=True);parser.add_argument('--registration',required=True);parser.add_argument('--stage',choices=['E1','E2'],required=True);args=parser.parse_args()
    config=r.check_freeze(args.config,args.commit,args.registration);config['freeze_commit']=args.commit
    root,native,state=r.setup(config);ledger=r.Ledger(root,config['budget'])
    with (root/'EXECUTION.lock').open('x') as stream:stream.write(str(__import__('os').getpid()))
    try:
        if args.stage=='E1':run_e1(config,root,native,state,ledger)
        else:run_e2(config,root,native,state,ledger)
    finally:(root/'EXECUTION.lock').unlink()

if __name__=='__main__':main()
