"""Append-only budget helper. Host must add the real owned-process watchdog."""
import os
import time
from core import need, encode

class Ledger:
    def __init__(self,path,slots,max_seconds):
        need(type(max_seconds) in (int,float) and 0<max_seconds<=86400,'budget')
        self.expected=set(slots);need(len(self.expected)==len(slots),'duplicate slots')
        self.file=open(path,'xb')
        self.started=set();self.active=None;self.charged=0.;self.maximum=max_seconds
        self._write(dict(event='OPEN',limit_seconds=max_seconds,slot_count=len(slots)))
    def _write(self,x):
        self.file.write(encode(x));self.file.flush();os.fsync(self.file.fileno())
    def begin(self,slot):
        need(slot in self.expected and slot not in self.started and self.active is None,'unknown/retry/concurrent start')
        need(self.charged<self.maximum,'budget exhausted')
        self.started.add(slot);self.active=(slot,time.monotonic())
        self._write(dict(event='ATTEMPT_BEFORE_PROCESS_CREATE',slot=slot))
    def finish(self,status):
        need(self.active is not None,'no active attempt')
        need(status in ('COMPLETED','FAILED','SKIPPED_UNSUPPORTED','ABORTED'),'terminal status')
        slot,t=self.active;elapsed=time.monotonic()-t;self.charged+=elapsed;self.active=None
        self._write(dict(event=status,slot=slot,charged_seconds=elapsed,total_seconds=self.charged))
        return self.charged<=self.maximum
    def close(self):
        need(self.active is None,'retain and reconcile active attempt before close')
        self._write(dict(event='CLOSE',started=len(self.started),unstarted=len(self.expected-self.started),charged_seconds=self.charged))
        self.file.close()
