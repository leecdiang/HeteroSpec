"""Conservative append-only phase journal anchored to the full inherited ledger.

This journal cannot grant GPU authority. A production host adapter must also hold
the shared allocation lock and bind its single registered journal path in F0.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
from support import digest_value, need, sha


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def integer(value):
    need(type(value)is int and value>=0,'Nonnegative integer budget required')
    return value


class Ledger:
    def __init__(self,path,inheritance,approval):
        self.path=Path(path);self.inherited=inheritance;self.approval=approval
        self.path.parent.mkdir(parents=True,exist_ok=True)

    @contextmanager
    def locked(self):
        with self.path.open('a+b') as f:
            fcntl.flock(f.fileno(),fcntl.LOCK_EX)
            try:yield f
            finally:fcntl.flock(f.fileno(),fcntl.LOCK_UN)

    def history(self,f):
        need(sha(self.inherited['ledger_path'])==digest_value(self.inherited['ledger_sha256']),
             'Inherited ledger changed; re-audit cumulative consumption')
        need(self.approval['scope']=='S1+S2' and self.approval['status']=='EXPLICITLY_APPROVED',
             'No explicit phase budget authority')
        for key in ('request_ceiling','row_ceiling','incremental_request_ceiling'):
            integer(self.approval[key])
        request_total=integer(self.inherited['requests'])
        row_total=integer(self.inherited['reserved_rows'])
        initial=request_total;events=[];operations={};parent='0'*64
        f.seek(0)
        for line in f:
            e=json.loads(line)
            need(e['parent_sha256']==parent,'Ledger hash chain discontinuity')
            digest=e.pop('event_sha256')
            need(hashlib.sha256(canonical(e)).hexdigest()==digest,'Ledger event hash')
            e['event_sha256']=digest;parent=digest
            need(e['inheritance_sha256']==self.inherited['ledger_sha256'],'Ledger origin changed')
            need(e['approval_sha256']==hashlib.sha256(canonical(self.approval)).hexdigest(),
                 'Approval changed inside a frozen journal')
            if e['kind']=='RESERVE':
                need(e['operation_id']not in operations,'Duplicate reservation')
                request_total+=1;row_total+=integer(e['reserved_rows'])
                operations[e['operation_id']]='RESERVE'
            else:
                transitions={'START':('RESERVE',),'COMPLETE':('START',),'FAILED':('START',),
                             'CANCELLED_NO_LAUNCH':('RESERVE',)}
                need(e['kind']in transitions and operations.get(e['operation_id'])in transitions[e['kind']],
                     'Invalid/missing operation transition')
                operations[e['operation_id']]=e['kind']
            need(request_total<=self.approval['request_ceiling'] and row_total<=self.approval['row_ceiling']
                 and request_total-initial<=self.approval['incremental_request_ceiling'],
                 'Cumulative budget exceeded')
            events.append(e)
        return dict(requests=request_total,reserved_rows=row_total,new_requests=request_total-initial,
                    operations=operations,events=events,parent=parent)

    def event(self,kind,operation_id,reserved_rows=None,**details):
        need(isinstance(operation_id,str)and operation_id,'Missing operation identity')
        need(not {'kind','operation_id','parent_sha256','approval_sha256','inheritance_sha256',
                  'event_sha256','reserved_rows'} & details.keys(),'Reserved ledger field')
        with self.locked() as f:
            state=self.history(f)
            if kind=='RESERVE':
                need(operation_id not in state['operations'],'Duplicate native operation')
                rows=integer(reserved_rows)
                need(state['requests']+1<=self.approval['request_ceiling'] and
                     state['new_requests']+1<=self.approval['incremental_request_ceiling'] and
                     state['reserved_rows']+rows<=self.approval['row_ceiling'],'Insufficient cumulative budget')
            else:
                allowed={'START':('RESERVE',),'COMPLETE':('START',),'FAILED':('START',),
                         'CANCELLED_NO_LAUNCH':('RESERVE',)}
                need(kind in allowed and state['operations'].get(operation_id)in allowed[kind],
                     'Invalid ledger transition')
                rows=None
            e=dict(kind=kind,operation_id=operation_id,parent_sha256=state['parent'],
                   inheritance_sha256=self.inherited['ledger_sha256'],
                   approval_sha256=hashlib.sha256(canonical(self.approval)).hexdigest(),**details)
            if kind=='RESERVE':e['reserved_rows']=rows
            e['event_sha256']=hashlib.sha256(canonical(e)).hexdigest()
            f.seek(0,2);f.write(canonical(e)+b'\n');f.flush();os.fsync(f.fileno())
            return self.history(f)

    def snapshot(self):
        with self.locked()as f:return self.history(f)
