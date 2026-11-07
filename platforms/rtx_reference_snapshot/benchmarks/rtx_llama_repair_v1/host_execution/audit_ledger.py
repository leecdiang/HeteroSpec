"""Read every new-study reservation, including failed and partial attempts."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();ledger=a.root/'LEDGER.jsonl';rows=[json.loads(l) for l in ledger.read_text().splitlines() if l]
    starts={};ends={}
    for row in rows:
        key=(row['epoch'],row['unit']);dest=starts if row['event']=='START' else ends
        assert row['event'] in ('START','END') and key not in dest;dest[key]=row
    assert set(starts)==set(ends),'unfinished native reservation'
    units=[];model_requests=0;operators=0;shadow_decodes=0;forward_calls=0
    for key,start in starts.items():
        end=ends[key];unit=Path(key[0])/'units'/key[1]
        assert read(unit/'RECEIPT.json')==end
        assert end['active_processes_after_wait']==0 and not end['lock_retained']
        count=end['completed_requests'];model_requests+=count;operators+=end.get('completed_operator_replays',0)
        admission='--admit-pools' in start['argv'];events=unit/'EVENTS.jsonl'
        slots=read(unit/'SLOTS.json') if (unit/'SLOTS.json').exists() else []
        expected=0 if admission else start.get('operator_replays',sum(1+(s['k']+2 if s.get('llama_diag',{}).get('mode')=='pair' else 0) for s in slots))
        assert start['reserved_requests']==expected
        reported=0;dispositions=[]
        if slots:
            journal=[json.loads(l) for l in events.read_text().splitlines() if l] if events.exists() else []
            complete=[x for x in journal if x['event']=='REQUEST_COMPLETED']
            reported=len(complete)
            # A completed worker event can precede a failed host audit. Do not
            # relabel such a record as an audited completion or erase its work.
            assert len(complete)>=count
            assert [x['slot_id'] for x in complete]==[s['slot_id'] for s in slots[:reported]]
            ready=any(x['event']=='POOLS_READY' for x in journal)
            for index,s in enumerate(slots):
                if admission:status='RESOURCE_ADMISSION_ONLY_NO_MODEL_REQUEST'
                elif index<count:status='HOST_AUDITED_COMPLETE'
                elif index<reported:status='WORKER_COMPLETED_HOST_AUDIT_FAILED'
                elif not ready:status='NOT_STARTED_NO_RUN_HANDSHAKE'
                elif not end['success'] and reported==count and index==count:status='NO_COMPLETION_POSSIBLY_STARTED'
                else:status='NOT_STARTED'
                dispositions.append({'slot_id':s['slot_id'],'status':status,
                  'raw_record_exists':(unit/'native'/(s['slot_id']+'.json')).exists()})
            for s in slots[:count]:
                r=read(unit/'native'/(s['slot_id']+'.json'))
                forward_calls+=r['target_calls']+r.get('draft_calls',0)
                if s.get('llama_diag',{}).get('mode')=='pair':shadow_decodes+=s['k']+2
        units.append({'epoch':key[0],'unit':key[1],'success':end['success'],'reserved_credits':expected,
          'completed_model_requests':count,'completed_operator_replays':end.get('completed_operator_replays',0),
          'worker_reported_completed_requests':reported,
          'seconds':end['seconds'],'error':end['error'],'receipt_sha256':sha(unit/'RECEIPT.json'),'slot_disposition':dispositions})
    limits=a.root/'RESOURCE_POLICY.jsonl'
    policies=[json.loads(l) for l in limits.read_text().splitlines() if l]
    previous=None
    for row in policies:
        expected=None if previous is None else hashlib.sha256(json.dumps(previous,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
        assert row['previous']==expected and row['reason'];previous=row
    credits=sum(x['reserved_requests'] for x in starts.values());dev=sum(x['reserved_requests'] for x in starts.values() if x['stage']=='development')
    seconds=math.fsum(x['seconds'] for x in ends.values())
    assert credits<=previous['limits']['request_credits'] and dev<=previous['limits']['development_credits']
    assert seconds<=previous['limits']['total_native_seconds']
    unlaunched=[];unsealed=[];unused_builds=[]
    launched_epochs={str(Path(k[0]).resolve()).lower() for k in starts}
    for folder in sorted(a.root.iterdir()):
        if folder.is_dir() and folder.name.startswith(('epoch','qwen')) and not (folder/'EPOCH.json').exists():
            assert str(folder.resolve()).lower() not in launched_epochs
            unsealed.append({'directory':str(folder),'status':'NO_SEALED_EPOCH_NO_NATIVE_LAUNCH_IN_LEDGER',
              'files':sum(p.is_file() for p in folder.rglob('*')),'reserved_credits':0})
        schedule=folder/'SLOTS.json'
        if folder.is_dir() and schedule.exists() and str(folder.resolve()).lower() not in launched_epochs:
            unlaunched.append({'epoch':str(folder),'status':'PREPARED_NOT_LAUNCHED',
              'schedule_sha256':sha(schedule),'slots':[s['slot_id'] for s in read(schedule)],'reserved_credits':0})
    launched_executables={str(Path(r['argv'][0]).resolve()).lower() for r in starts.values()}
    for config in sorted(p for p in a.root.parent.glob('*config*') if p.is_dir()):
        build=config/'build/BUILD.json';exe=config/'build/bin/rtx-scope-transfer.exe'
        if build.exists() and exe.exists() and str(exe.resolve()).lower() not in launched_executables:
            assert sha(exe)==read(build)['executable_sha256']
            unused_builds.append({'configuration':str(config),'status':'BUILT_NOT_EXECUTED',
              'build_receipt_sha256':sha(build),'executable_sha256':sha(exe),'reserved_credits':0})
    result={'status':'COMPLETE_LEDGER_RECONSTRUCTED','reserved_credits':credits,'development_credits':dev,
      'completed_model_requests':model_requests,'completed_operator_replays':operators,'completed_extra_shadow_decodes':shadow_decodes,
      'recorded_natural_forward_calls':forward_calls,'native_supervised_wall_seconds':seconds,'units':units,
      'ledger_sha256':sha(ledger),'resource_policy_sha256':sha(limits),'limits':previous['limits'],
      'prepared_unlaunched_schedules':unlaunched,
      'preparation_directories_without_sealed_epoch':unsealed,'builds_without_native_launch':unused_builds,
      'partial_work_note':'Failed reservations are fully charged. Completed record counts are lower bounds on actual work in failed processes; missing partial forward telemetry is not treated as zero.',
      'historical_accounting':'PR151 54 requests and PR159 prior ledger remain historical, separately retained; neither is reset or credited back.',
      'scope':'Supervised wall time includes worker waits and host auditing, not only device execution. Natural forward counts exclude separately counted shadow decodes and standalone operators.'}
    with a.out.open('x') as f:json.dump(result,f,indent=2)
    print({k:v for k,v in result.items() if k!='units'})


if __name__=='__main__':main()
