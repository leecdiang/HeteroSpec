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
        reported=0
        if slots:
            complete=[json.loads(l) for l in events.read_text().splitlines() if l] if events.exists() else []
            complete=[x for x in complete if x['event']=='REQUEST_COMPLETED']
            reported=len(complete)
            # A completed worker event can precede a failed host audit. Do not
            # relabel such a record as an audited completion or erase its work.
            assert len(complete)>=count
            for s in slots[:count]:
                r=read(unit/'native'/(s['slot_id']+'.json'))
                forward_calls+=r['target_calls']+r.get('draft_calls',0)
                if s.get('llama_diag',{}).get('mode')=='pair':shadow_decodes+=s['k']+2
        units.append({'epoch':key[0],'unit':key[1],'success':end['success'],'reserved_credits':expected,
          'completed_model_requests':count,'completed_operator_replays':end.get('completed_operator_replays',0),
          'worker_reported_completed_requests':reported,
          'seconds':end['seconds'],'error':end['error'],'receipt_sha256':sha(unit/'RECEIPT.json')})
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
    result={'status':'COMPLETE_LEDGER_RECONSTRUCTED','reserved_credits':credits,'development_credits':dev,
      'completed_model_requests':model_requests,'completed_operator_replays':operators,'completed_extra_shadow_decodes':shadow_decodes,
      'recorded_natural_forward_calls':forward_calls,'native_supervised_wall_seconds':seconds,'units':units,
      'ledger_sha256':sha(ledger),'resource_policy_sha256':sha(limits),'limits':previous['limits'],
      'partial_work_note':'Failed reservations are fully charged. Completed record counts are lower bounds on actual work in failed processes; missing partial forward telemetry is not treated as zero.',
      'historical_accounting':'PR151 54 requests and PR159 prior ledger remain historical, separately retained; neither is reset or credited back.',
      'scope':'Supervised wall time includes worker waits and host auditing, not only device execution. Natural forward counts exclude separately counted shadow decodes and standalone operators.'}
    with a.out.open('x') as f:json.dump(result,f,indent=2)
    print({k:v for k,v in result.items() if k!='units'})


if __name__=='__main__':main()
