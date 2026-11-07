"""Account for every reservation, retained record and unfinished slot without inference."""
import argparse,datetime,hashlib,json,pathlib
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def need(ok,msg):
    if not ok:raise ValueError(msg)
def main(root,out):
    root=pathlib.Path(root);out=pathlib.Path(out);need(not out.exists(),'fresh accounting output')
    ledger=root/'LEDGER.jsonl';events=[json.loads(l) for l in ledger.read_text().splitlines() if l];starts={};ends={}
    for e in events:
        target=starts if e['event']=='START' else ends;key=(e['epoch'],e['unit']);need(key not in target,'duplicate ledger lifecycle');target[key]=e
    need(starts.keys()==ends.keys(),'active/unsettled native process');units=[];records=incomplete=unrecorded=operators=charged=dev=0
    for key,start in starts.items():
        end=ends[key];unit=pathlib.Path(start['epoch'])/'units'/start['unit'];reserved=start['reserved_requests'];charged+=reserved
        if start['stage']=='development':dev+=reserved
        need(end['active_processes_after_wait']==0 and not end['lock_retained'],'unsettled cleanup')
        states=[]
        if start.get('operator_replays'):
            operators+=end.get('completed_operator_replays',0);need(start['model_requests']==0,'operator/model separation')
        elif reserved:
            slots=read(unit/'SLOTS.json');need(len(slots)==reserved,'schedule reservation mismatch');active=read(unit/'native/ACTIVE_SLOT.json')['slot_id'] if (unit/'native/ACTIVE_SLOT.json').exists() else None
            for s in slots:
                p=unit/'native'/(s['slot_id']+'.json')
                if p.exists():state='RETAINED_NATIVE_RECORD';records+=1
                elif s['slot_id']==active:state='STARTED_NO_COMPLETE_RECORD';incomplete+=1
                else:state='RESERVED_NO_RECORD';unrecorded+=1
                states.append({'slot_id':s['slot_id'],'state':state,'unit_completed_successfully':end['success'],'category':s['category'],'input_id':s['input_id']})
            if end['success']:need(all(s['state']=='RETAINED_NATIVE_RECORD' for s in states) and end['completed_requests']==reserved,'successful unit incomplete')
        units.append({'epoch':pathlib.Path(start['epoch']).name,'unit':start['unit'],'stage':start['stage'],'reserved_requests':reserved,'native_process_seconds':end['seconds'],'success':end['success'],'error':end.get('error'),'host_acknowledged_records':end.get('completed_requests',0),'operator_replays':end.get('completed_operator_replays',0),'slots':states})
    need(charged<=1200 and dev<=480,'budget exceeded')
    expected={'original_reference':24,'heldout':120,**{f'formal_s{i}':144 for i in range(4)}};scheduled={u['unit']:u['reserved_requests'] for u in units if u['epoch']=='epoch03'}
    report={'status':'CUMULATIVE_ACCOUNTING_COMPLETE','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ledger_sha256':hashlib.sha256(ledger.read_bytes()).hexdigest(),'charged_total':charged,'charged_development':dev,'charged_confirmation':charged-dev,'remaining_total':1200-charged,'remaining_development':480-dev,'old_PR156_requests_separate':40,'retained_native_records':records,'started_without_complete_record':incomplete,'reserved_slots_without_record_or_start_evidence':unrecorded,'completed_operator_replays':operators,'native_process_seconds':sum(x['native_process_seconds'] for x in units),'confirmation_units_never_started':{k:n for k,n in expected.items() if k not in scheduled},'units':units,'interpretation':'Failed stage reservations remain charged in full. Retained records from the failed fresh-lifetime attempt are failure evidence, not replacement qualification. Missing records are not counted as successful requests. Non-generating admissions are separately retained with zero model requests; eight operator replays are conservatively charged as development requests.'}
    with out.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k!='units'},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('out');a=p.parse_args();main(a.root,a.out)
