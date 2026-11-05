"""Publish compact receipts and complete reserved/observed native costs."""
from build_host import *
from native_adapter import RUNS
import sqlite3,datetime,os
HERE=Path(__file__).resolve().parent;DEST=HERE/'host_evidence'
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2),encoding='utf8');os.replace(tmp,p)
def main():
    copies={}
    for p in ROOT.glob('*.json'):
        if p.name.startswith('EVIDENCE_DEDUP-'):continue
        copies['host/'+p.name]=p
    for p in Path('D:/rtx184-qualification').glob('*/QUALIFICATION.json'):copies['qualification/'+p.parent.name+'.json']=p
    for p in RUNS.glob('priming-v3-*/PRIMING_QUALIFICATION.json'):copies['priming/'+p.parent.name+'.json']=p
    for case in Path('D:/rtx184-qualification').glob('O-root*'):
        for p in case.glob('*QUALIFICATION.json'):copies['qualification/'+case.name+'/'+p.name]=p
        for p in case.glob('OLD_OBSERVER_BRIDGE.json'):copies['qualification/'+case.name+'/'+p.name]=p
    for p in (ROOT/'selection-v3').glob('*.json'):copies['selection/'+p.name]=p
    for root in (ROOT/'draft-v3',ROOT/'forced-v2',Path('D:/rtx184-operator')):
        for name in ('BUILD.json','CORE_BUILD.json','BUILD_CORE.json','RUNTIME_BUILD.json','RUNTIME_BINDING.json'):
            for p in root.rglob(name):copies['build/'+p.parent.name+'/'+name]=p
    for name,p in copies.items():write(DEST/name,json.loads(p.read_bytes()))
    db=sqlite3.connect(ROOT/'ledger.sqlite');db.row_factory=sqlite3.Row;attempts=[dict(r) for r in db.execute('select * from attempts order by started')];db.close()
    services=[];native=[]
    for attempt in attempts:
        base=RUNS/attempt['id']
        if not base.exists():base=ROOT/attempt['id']
        record=dict(attempt=attempt['id'],status=attempt['status'],reserved={k:attempt[k] for k in ('requests','token_rows','operators')})
        exit=base/'exit.json'
        if exit.exists():record['host_exit']=json.loads(exit.read_bytes())
        receipt=base/'session-result.json'
        if receipt.exists():
            result=json.loads(receipt.read_bytes());record['actual_work']=result['actual_work'];services += [dict(x,attempt=attempt['id']) for x in result['records']] if 'records' in result else []
        elif record.get('host_exit',{}).get('status')=='COMPLETE' and (base/'native/result.json').exists():
            result=json.loads((base/'native/result.json').read_bytes())
            if isinstance(result.get('requests'),list):
                actual=dict(requests=len(result['requests']),token_rows=0,operators=0)
                for item in result['requests']:
                    r=json.loads((base/'native'/item['record']).read_bytes());n=len(r['prompt_ids'])
                    actual['token_rows']+=n+(n+len(r['cycles'])*8 if r['draft_enabled'] else len(r['ids'])-1)
                    services.append(dict(attempt=attempt['id'],slot=item['slot_id'],arm=r.get('arm','R'),kind='qualification',service_s=r['service_seconds'],native_record=item['record'],cost_provenance='completed original bridge native journal'))
                assert all(actual[k]<=record['reserved'][k] for k in actual);record['actual_work']=actual
        for file in ('result.json','PROVISIONED.json'):
            p=base/'native'/file
            if p.exists():
                data=json.loads(p.read_bytes());record[file]={k:v for k,v in data.items() if ('seconds' in k or 'memory' in k or k in ('status','requests','token_rows','error')) and k!='requests'}
                if isinstance(data.get('requests'),list):record['completed_native_records']=len(data['requests'])
        if (base/'failure.json').exists():record['failure']=json.loads((base/'failure.json').read_bytes())
        # Original service repeats model/pool setup values on each slot. Count
        # each loaded process / block once, retaining each slot's service cost.
        slot_details=[]
        for p in (base/'native').glob('*/receipt.json'):
            r=json.loads(p.read_bytes())
            if 'service_seconds' not in r:continue
            detail=dict(path=str(p),slot=p.parent.name,seconds={k:v for k,v in r.items() if 'seconds' in k or k=='prefill_wall_s'})
            n=len(r['prompt_ids']);detail['decoded_token_rows']=n+(n+len(r['cycles'])*8 if r['draft_enabled'] else len(r['ids'])-1)
            slot_details.append(detail)
        if slot_details:
            record['slot_costs']=slot_details
            record['model_load_seconds_once']=slot_details[0]['seconds'].get('model_load_seconds')
            record['pool_setup_seconds_once']=slot_details[0]['seconds'].get('pool_setup_seconds')
            if 'actual_work' not in record:record['completed_slot_records_lower_bound']=len(slot_details)
        if (base/'input.json').exists():
            manifest=json.loads((base/'input.json').read_bytes())
            if 'replay' in manifest:
                cells=[]
                for p in base.glob('*/*.json'):
                    r=json.loads(p.read_bytes())
                    if isinstance(r,dict) and 'submit_s' in r:
                        cells.append(dict(path=str(p),executions=len(r['submit_s']),submit_s=r['submit_s'],sync_s=r['sync_s']))
                record['operator_cells']=cells;record['completed_operator_executions_lower_bound']=sum(x['executions'] for x in cells)
                if record.get('host_exit',{}).get('status')=='COMPLETE':record['actual_work']=dict(requests=0,token_rows=0,operators=record['completed_operator_executions_lower_bound'])
            elif record.get('host_exit',{}).get('status')=='COMPLETE':record['actual_work']=dict(record['reserved'])
            if (base/'load.json').exists():record['model_load']=json.loads((base/'load.json').read_bytes())
        if (base/'RECOVERED_COMPLETED_NATIVE.json').exists():
            record['recovery']=json.loads((base/'RECOVERED_COMPLETED_NATIVE.json').read_bytes())
            if record['recovery']['native_return_code']==0 and record.get('completed_operator_executions_lower_bound')==record['reserved']['operators']:
                record['actual_work']=dict(requests=0,token_rows=0,operators=record['reserved']['operators'])
        native.append(record)
    summary=dict(as_of_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),attempts=attempts,native=native,reserved_total={k:sum(x[k] for x in attempts) for k in ('requests','token_rows','operators')},host_process_seconds=sum(x.get('host_exit',{}).get('seconds',0) for x in native),service_seconds=sum(x['service_s'] for x in services),services=services,interpretation='Reservations never refunded. Service/model/provision components are nested within host process wall and must not be added to it. Running/failed attempts remain explicit; missing actual-work fields are not zeros.')
    summary['failed_attempt_completed_slot_service_seconds_lower_bound']=sum(s['seconds'].get('service_seconds',0) for r in native if r['status']!='COMPLETE' for s in r.get('slot_costs',[]))
    summary['known_complete_and_failed_slot_service_seconds_lower_bound']=summary['service_seconds']+summary['failed_attempt_completed_slot_service_seconds_lower_bound']
    summary['confirmed_work_lower_bound']={k:sum(r.get('actual_work',{}).get(k,0) for r in native) for k in ('requests','token_rows','operators')}
    summary['actual_work_unresolved_attempts']=[r['attempt'] for r in native if 'actual_work' not in r]
    summary['known_work_lower_bound_including_completed_failed_slots']={k:v for k,v in summary['confirmed_work_lower_bound'].items()}
    for r in native:
        if 'actual_work' in r:continue
        summary['known_work_lower_bound_including_completed_failed_slots']['requests']+=len(r.get('slot_costs',[]))
        summary['known_work_lower_bound_including_completed_failed_slots']['token_rows']+=sum(s['decoded_token_rows'] for s in r.get('slot_costs',[]))
        summary['known_work_lower_bound_including_completed_failed_slots']['operators']+=r.get('completed_operator_executions_lower_bound',0)
    summary['host_attempt_wall_seconds']=summary['host_process_seconds']
    summary['host_wall_scope']='Attempt clocks include prelaunch binding/model checks and postlaunch receipt validation. Outer normalization, archival and repair gaps are additionally captured by ELAPSED_STAGE_SPANS.json; spans/components overlap and must not be added.'
    publication=ROOT/'ARTIFACT_DELIVERY_PUBLISHED.json'
    if publication.exists():
        delivered=json.loads(publication.read_bytes())
        summary['artifact_delivery']={k:delivered[k] for k in ('release','total_zip_bytes','logical_files','logical_bytes','stream_and_part_upload_wall_s','publication_wall_s','wall_scope')}
        summary['artifact_delivery']['receipt_sha256']=sha(publication)
    write(DEST/'UNIFIED_COSTS.json',summary)
    engineering=[]
    for root in (ROOT,Path('D:/rtx184-operator')):
        for p in root.rglob('*.json'):
            if any(x in p.parts for x in ('native','source','native-arms')):continue
            try:r=json.loads(p.read_bytes())
            except (ValueError,OSError):continue
            if isinstance(r,dict) and 'argv' in r and 'seconds' in r and 'code' in r:engineering.append(dict(receipt=str(p),sha256=sha(p),**r))
    write(DEST/'ENGINEERING_COSTS.json',dict(executions=engineering,recorded_host_seconds=sum(r['seconds'] for r in engineering),scope='Separately recorded configure/compile/link and vocabulary-only tokenizer executions, including failures. Compound BUILD copies are not added again. No GPU model trajectories are inferred from these timings. Artifact and unrecorded installation wall time is not assumed zero.'))
    write(DEST/'RECEIPT_INDEX.json',dict(files={k:dict(source=str(v),sha256=sha(v)) for k,v in copies.items()},raw_archive_roots=['C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx184-evidence','F:/rtx184-O-evidence'],raw_restore='archive_host.restore reads each archive manifest and its chunks; select STORE for D or O; no GPU',storage_placement='O chunk prefixes00..67 reside on C; D archive prefixes00..0f reside on D, through recorded directory junctions. Manifest chunk hashes are independent of placement.'))
    print('collected',len(copies),'receipts;',len(attempts),'ledger entries')
if __name__=='__main__':main()
