"""Extend the same32B journal with a byte-frozen historical approval prefix.

No counter reset, new journal or refunded request. Only events after the exact
immutable prefix can use the explicit S3 approval. Original514 remain anchored.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path


def need(value,message):
    if not value:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def integer(value):
    need(type(value)is int and value>=0,'Nonnegative integer budget required');return value


class Ledger:
    def __init__(self,path,inheritance,approval):
        self.path=Path(path);self.inherited=inheritance;self.approval=approval

    @contextmanager
    def locked(self):
        with self.path.open('a+b')as f:
            fcntl.flock(f.fileno(),fcntl.LOCK_EX)
            try:yield f
            finally:fcntl.flock(f.fileno(),fcntl.LOCK_UN)

    def history(self,f):
        a=self.approval;need(a['scope']=='S3'and a['status']=='EXPLICITLY_APPROVED','Explicit S3 authority required')
        need(sha(self.inherited['ledger_path'])==self.inherited['ledger_sha256'],'Original514 ledger changed')
        for key in ('request_ceiling','row_ceiling','incremental_request_ceiling','phase_request_ceiling'):integer(a[key])
        prefix=Path(self.inherited['approval_prefix_path']).read_bytes()
        need(len(prefix)==a['predecessor_prefix_bytes']and hashlib.sha256(prefix).hexdigest()==a['predecessor_prefix_sha256'],'Historical complete32B prefix changed')
        previous=a['predecessor_approval'];previous_sha=hashlib.sha256(canonical(previous)).hexdigest()
        need(previous['scope']=='S1+S2'and previous['status']=='EXPLICITLY_APPROVED','Predecessor authority')
        f.seek(0);raw=f.read();need(raw.startswith(prefix),'Same canonical32B journal prefix required')
        need(not prefix or prefix.endswith(b'\n'),'Complete historical event boundary')
        old_lines=len(prefix.splitlines());events=[];operations={};parent='0'*64
        requests=integer(self.inherited['requests']);rows=integer(self.inherited['reserved_rows']);initial=requests
        phase_requests=0;new_sha=hashlib.sha256(canonical(a)).hexdigest()
        for ordinal,line in enumerate(raw.splitlines()):
            e=json.loads(line);need(e['parent_sha256']==parent,'Ledger hash chain discontinuity')
            digest=e.pop('event_sha256');need(hashlib.sha256(canonical(e)).hexdigest()==digest,'Ledger event hash')
            e['event_sha256']=digest;parent=digest
            need(e['inheritance_sha256']==self.inherited['ledger_sha256'],'Original inherited ledger identity')
            old=ordinal<old_lines
            need(e['approval_sha256']==(previous_sha if old else new_sha),'Approval cannot move across immutable prefix')
            if e['kind']=='RESERVE':
                need(e['operation_id']not in operations,'Duplicate reservation')
                requests+=1;rows+=integer(e['reserved_rows']);operations[e['operation_id']]='RESERVE'
                if not old:phase_requests+=1
            else:
                transitions={'START':('RESERVE',),'COMPLETE':('START',),'FAILED':('START',),'CANCELLED_NO_LAUNCH':('RESERVE',)}
                need(e['kind']in transitions and operations.get(e['operation_id'])in transitions[e['kind']],'Invalid operation transition')
                operations[e['operation_id']]=e['kind']
            envelope=previous if old else a
            need(requests<=envelope['request_ceiling']and rows<=envelope['row_ceiling']and requests-initial<=envelope['incremental_request_ceiling'],'Cumulative budget exceeded')
            need(phase_requests<=a['phase_request_ceiling'],'S3 phase budget exceeded')
            events.append(e)
        need(requests-phase_requests==a['predecessor_requests'],'Real-time32B prefix total differs')
        return dict(requests=requests,reserved_rows=rows,new_requests=requests-initial,phase_requests=phase_requests,
                    operations=operations,events=events,parent=parent)

    def event(self,kind,operation_id,reserved_rows=None,**details):
        need(isinstance(operation_id,str)and operation_id,'Operation identity')
        need(not {'kind','operation_id','parent_sha256','approval_sha256','inheritance_sha256','event_sha256','reserved_rows'}&details.keys(),'Reserved journal field')
        with self.locked()as f:
            s=self.history(f)
            if kind=='RESERVE':
                need(operation_id not in s['operations'],'Duplicate operation')
                rows=integer(reserved_rows)
                need(s['requests']+1<=self.approval['request_ceiling']and s['new_requests']+1<=self.approval['incremental_request_ceiling']and
                     s['phase_requests']+1<=self.approval['phase_request_ceiling']and s['reserved_rows']+rows<=self.approval['row_ceiling'],'Insufficient cumulative/phase budget')
            else:
                transitions={'START':('RESERVE',),'COMPLETE':('START',),'FAILED':('START',),'CANCELLED_NO_LAUNCH':('RESERVE',)}
                need(kind in transitions and s['operations'].get(operation_id)in transitions[kind],'Invalid operation transition');rows=None
                # Historical operations are terminal; new approval never repairs
                # or completes a predecessor event with uncertain outcome.
                need(operation_id.startswith(self.approval['operation_prefix']),'S3 may not modify historical slots')
            need(operation_id.startswith(self.approval['operation_prefix']),'Registered S3 operation namespace')
            e=dict(kind=kind,operation_id=operation_id,parent_sha256=s['parent'],
                   inheritance_sha256=self.inherited['ledger_sha256'],approval_sha256=hashlib.sha256(canonical(self.approval)).hexdigest(),**details)
            if kind=='RESERVE':e['reserved_rows']=rows
            e['event_sha256']=hashlib.sha256(canonical(e)).hexdigest()
            f.seek(0,2);f.write(canonical(e)+b'\n');f.flush();os.fsync(f.fileno());return self.history(f)

    def snapshot(self):
        with self.locked()as f:return self.history(f)
