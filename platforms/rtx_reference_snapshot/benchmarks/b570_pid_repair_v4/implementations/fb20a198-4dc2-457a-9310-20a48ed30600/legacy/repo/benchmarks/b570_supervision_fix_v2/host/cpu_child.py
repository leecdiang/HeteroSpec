"""Sacrificial CPU producer. No backend imports, discovery, model or graph entry."""
import hashlib,json,os,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
cfg=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'));active=Path(cfg['active']);mode=cfg['case_id']
def evidence(event,**kw):
    with Path(cfg['producer_journal']).open('ab',buffering=0) as f:
        f.write((json.dumps(dict(event=event,at_ns=time.perf_counter_ns(),pid=os.getpid(),**kw),sort_keys=True)+'\n').encode());os.fsync(f.fileno())
evidence('PRODUCER_STARTED',mode=mode)
if mode=='quick_exit':
    evidence('FAULT_CONTROL',code='EXIT_BEFORE_HANDSHAKE',exit_code=0);raise SystemExit(0)
print(json.dumps(dict(event='READY',pid=os.getpid(),image=sys.executable,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())),flush=True)
if sys.stdin.readline()!='GO\n':raise SystemExit(19)
evidence('GO_RECEIVED');print(json.dumps(dict(event='WORKING',pid=os.getpid())),flush=True)
if mode=='child_timeout':
    evidence('FAULT_CONTROL',code='EXCEED_CHILD_DEADLINE');sys.stdin.readline();raise SystemExit(20)
if sys.stdin.readline()!='CONTINUE\n':raise SystemExit(21)
evidence('CONTINUE_RECEIVED')
count=10000 if mode=='log_overflow' else 4
payload=4000 if mode=='log_overflow' else 128
if mode=='log_overflow':evidence('FAULT_CONTROL',code='EXCEED_LOG_SOFT_LIMIT')
with (active/'ACK.jsonl').open('xb',buffering=0) as ack,(active/'DATA.bin').open('xb',buffering=0) as data:
    for index in range(count):
        line=(json.dumps(dict(event='FRAME',index=index,payload='x'*payload),sort_keys=True)+'\n').encode()
        sys.stdout.buffer.write(line);sys.stdout.buffer.flush()
        sys.stderr.buffer.write(b'CPU_STDERR_FRAME\n');sys.stderr.buffer.flush()
        ack.write((json.dumps(dict(index=index,bytes=len(line),sha256=hashlib.sha256(line).hexdigest()),sort_keys=True)+'\n').encode());os.fsync(ack.fileno())
        data.write(bytes([index%256])*64);os.fsync(data.fileno())
        if mode!='log_overflow':time.sleep(.03)
if mode=='truncated_stdout':
    evidence('FAULT_CONTROL',code='EMIT_TRUNCATED_RECORD');sys.stdout.buffer.write(b'{"event":"INCOMPLETE"');sys.stdout.buffer.flush();raise SystemExit(0)
if mode=='abnormal_exit':
    evidence('FAULT_CONTROL',code='EXIT_NONZERO',exit_code=23);raise SystemExit(23)
print(json.dumps(dict(event='COMPLETE',frames=count)),flush=True)
evidence('PRODUCER_STREAMS_FLUSHED',frames=count)
