"""Pure interval state + exact chained sample protocol; no process/device API."""
import hashlib,json
MAX_MONITOR_INTERVAL_NS=1_000_000_000
RUN_ID='pr116-s1b-cost-v1'
EXECUTION_ID='pr116-s1b-exact-r2'

def identities(f, a):
    if 'registration_id' in f or 'registration_id' in a:raise ValueError('obsolete ambiguous identity field')
    if f['run_id']!=RUN_ID or a['run_id']!=RUN_ID:
        raise ValueError('canonical run_id mismatch')
    if f['execution_id']!=EXECUTION_ID or a['execution_id']!=EXECUTION_ID:
        raise ValueError('execution_id mismatch')
    if a['run_id']==a['execution_id']:
        raise ValueError('run_id and execution_id must differ')

class Window:
    def __init__(self,armed_ns):
        assert type(armed_ns)is int and armed_ns>=0
        self.armed=armed_ns;self.last=None;self.samples=0;self.intervals=0
        self.maximum=0;self.coverage=0;self.missing=0;self.reason=None;self.closed=False
    def fail(self,reason,missing=False):
        self.reason=self.reason or reason
        if missing:self.missing=max(1,self.missing)
        raise ValueError(self.reason)
    def sample(self,t):
        if self.closed:self.fail('sample after closed runtime')
        if type(t)is not int or t<self.armed or (self.last is not None and t<=self.last):self.fail('timestamp anomaly/backwards')
        gap=t-(self.last if self.last is not None else self.armed)
        self.coverage=max(self.coverage,gap)
        if self.last is not None:self.intervals+=1;self.maximum=max(self.maximum,gap)
        if gap>MAX_MONITOR_INTERVAL_NS:self.fail('actual monitoring interval exceeded',True)
        self.last=t;self.samples+=1
    def check(self,now):
        if self.closed:return
        if type(now)is not int or now<(self.last if self.last is not None else self.armed):self.fail('watchdog timestamp anomaly')
        age=now-(self.last if self.last is not None else self.armed)
        self.coverage=max(self.coverage,age)
        if age>MAX_MONITOR_INTERVAL_NS:self.fail('watchdog missing qualified sample',True)
    def close(self,exit_observed_ns):
        self.check(exit_observed_ns)
        if not self.samples:self.fail('missing all samples',True)
        self.closed=True
    def report(self,decision=None):
        return dict(max_monitor_interval_ns=MAX_MONITOR_INTERVAL_NS,observed_max_interval_ns=self.maximum,
                    observed_max_coverage_gap_ns=self.coverage,interval_count=self.intervals,sample_count=self.samples,
                    missing_sample_count=self.missing,watchdog_decision=decision or ('FAIL' if self.reason else 'PASS'),
                    reason=self.reason,window_closed=self.closed)

def encode_sample(row, previous):
    payload=json.dumps(row,separators=(',',':')).encode()
    digest=hashlib.sha256(bytes.fromhex(previous)+payload).hexdigest()
    return payload+b'\t'+digest.encode()+b'\n',digest

def decode_sample(line, previous, config):
    payload,digest=line.rstrip(b'\n').rsplit(b'\t',1)
    if hashlib.sha256(bytes.fromhex(previous)+payload).hexdigest().encode()!=digest:raise ValueError('sample byte chain mismatch')
    row=json.loads(payload)
    if (row['run_id'],row['execution_id'],row['token'],row['target_pid'])!=(config['run_id'],config['execution_id'],config['token'],config['target_pid']):raise ValueError('sample identity mismatch')
    if not row['resource_valid'] or not row['target_alive']:raise ValueError('invalid resource sample')
    return row,digest.decode()
