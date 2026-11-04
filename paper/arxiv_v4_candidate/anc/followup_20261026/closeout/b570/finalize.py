"""Preserve the fixed matrix and all costs after the first terminal outcome."""
from pathlib import Path
import csv, datetime, hashlib, json, shutil, time, zipfile
from prepare import ROOT, read, write, sha, item

def main():
    started=time.monotonic();reg=read(ROOT/'REGISTRATION.json')
    assert not (ROOT/'CLOSEOUT.json').exists(),'Do not overwrite closeout'
    receipts=[];native=[];completed={};cost=[]
    for step in range(9):
        mode='E0' if step==0 else ('E1' if step<5 else 'E2');i=0 if step==0 else (step-1)%4
        rp=ROOT/f'{mode}-{i}.PROCESS_RECEIPT.json'
        if not rp.exists():continue
        rc=read(rp);receipts.append(rc)
        path=ROOT/f'{mode}-{i}/result.json'
        if not path.exists():continue
        n=read(path);native.append(n)
        cost.append({'kind':'model_load','process':f'{mode}-{i}','slot':'','seconds':n.get('model_load_seconds')})
        cost.append({'kind':'worker_wall','process':f'{mode}-{i}','slot':'','seconds':rc.get('charged_seconds')})
        cost.append({'kind':'wrapper_total_including_preflight','process':f'{mode}-{i}','slot':'','seconds':rc.get('total_wrapper_seconds')})
        for x in n['requests']:
            completed[x['slot']]=dict(x,worker_status=rc['status'],native_status=n['status'])
            for key in ['service_seconds','request_seconds']:
                cost.append({'kind':key,'process':f'{mode}-{i}','slot':x['slot'],'seconds':x[key]})
            for model in ['target','draft']:
                for phase,seconds in x[f'{model}_decode_seconds'].items():
                    cost.append({'kind':f'{model}_{phase}','process':f'{mode}-{i}','slot':x['slot'],'seconds':seconds})
    slots=[]
    for slot in read(ROOT/'REGISTERED_SLOTS.json'):
        x=completed.get(slot['slot']);entry=dict(slot,status='NATIVE_RECORD_COMPLETE' if x else 'NOT_STARTED_OR_NO_COMPLETED_RECORD')
        if x:entry.update(endpoint=[x['length'],x['stop_reason']],service_seconds=x['service_seconds'],
                          worker_status=x['worker_status'],native_status=x['native_status'])
        slots.append(entry)
    write('SLOT_DISPOSITION.json',slots)
    with (ROOT/'ALL_COST_WINDOWS.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['kind','process','slot','seconds']);w.writeheader();w.writerows(cost)
    analysis=read(ROOT/'INDEPENDENT_ANALYSIS.json') if (ROOT/'INDEPENDENT_ANALYSIS.json').exists() else None
    failure=next((r for r in receipts if r['status']!='PROCESS_COMPLETED'),None)
    if analysis:
        outcome='PRACTICAL_FINITE_PANEL_BENEFIT' if analysis['practical_screen_pass'] else 'NO_ESTABLISHED_PRACTICAL_PANEL_BENEFIT'
    elif failure:outcome='STOPPED_FIRST_FAILURE'
    else:outcome='BLOCKED_INCOMPLETE_MATRIX'
    now=datetime.datetime.now(datetime.timezone.utc)
    elapsed=(now-datetime.datetime.fromisoformat(reg['owned_start_utc'])).total_seconds()
    worker_seconds=sum(x['charged_seconds'] for x in receipts)
    wrapper_seconds=sum(x['total_wrapper_seconds'] for x in receipts)
    write('CLOSEOUT.json',{'outcome':outcome,'study_uuid':reg['study_uuid'],
          'finished_utc':now.isoformat(),'native_workers_started':len(receipts),
          'completed_native_request_records':len(completed),'registered_request_ceiling':156,
          'complete_matrix':len(completed)==156,'worker_wall_seconds':worker_seconds,
          'wrapper_total_seconds':wrapper_seconds,'owned_wall_seconds_through_closeout':elapsed,
          'non_worker_owned_wall_including_preparation_compilation_audits_and_coordination':elapsed-worker_seconds,
          'cost_intervals_overlap_do_not_sum':True,'all_native_exits_observed':all(x['exit_observed'] for x in receipts),
          'all_native_cleanup_returned':all(x.get('normal_cleanup_returned') for x in receipts),
          'failure':failure,'analysis':analysis,'historical_times_pooled':False,
          'prior_receipt_backed_cumulative_seconds':3435.1001972,
          'additional_prior_unreceipted_worker_seconds':None,
          'historical_cost_total_exactly_known':False,'software_policy_branch_closed':True,
          'further_experiment_authorized':False})
    # Full raw archive remains local, with compact review data in Git.
    raw_paths=[];compact=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or 'build' in p.parts or '__pycache__' in p.parts:continue
        if p.suffix=='.f32':raw_paths.append(p)
        elif p.suffix in ['.json','.md','.py','.cpp','.inc','.ps1','.log','.patch','.txt']:
            compact.append(p)
    with zipfile.ZipFile(ROOT/'FULL_RAW_LOCAL.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for p in raw_paths:z.write(p,str(p.relative_to(ROOT)).replace('\\','/'))
    write('LOCAL_RAW_ARCHIVE.json',dict(item(ROOT/'FULL_RAW_LOCAL.zip'),vectors=len(raw_paths),
          availability='Local original bytes only; no external raw-data certification',
          original_reference_root='C:/hs/b570-formal-request-20261020',
          prior_history_archive=item(ROOT/'HISTORICAL_COMPACT.zip')))
    with zipfile.ZipFile(ROOT/'COMPACT_EVIDENCE.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in compact:z.write(p,str(p.relative_to(ROOT)).replace('\\','/'))
        z.write(ROOT/'LOCAL_RAW_ARCHIVE.json','LOCAL_RAW_ARCHIVE.json')
    write('COMPACT_MANIFEST.json',item(ROOT/'COMPACT_EVIDENCE.zip'))
    destination=Path(reg['worktree'])/reg['result_path']
    for p in ROOT.iterdir():
        if p.is_file() and p.name!='FULL_RAW_LOCAL.zip' and p.suffix in ['.json','.md','.py','.cpp','.inc','.patch','.csv','.zip','.log','.txt']:
            shutil.copy2(p,destination/p.name)
    write('PACKAGING_COST.json',{'cpu_parent_wall_seconds':time.monotonic()-started,
          'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'native_model_processes':0,'full_raw_bytes':(ROOT/'FULL_RAW_LOCAL.zip').stat().st_size})
    shutil.copy2(ROOT/'PACKAGING_COST.json',destination/'PACKAGING_COST.json')
    print(json.dumps(read(ROOT/'CLOSEOUT.json'),indent=2))

if __name__=='__main__':main()
