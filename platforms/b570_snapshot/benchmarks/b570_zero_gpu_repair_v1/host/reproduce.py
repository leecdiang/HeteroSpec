"""One natural A-close/B-start reproduction, with fixed old sources ported safely."""
import sys,os,time,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H/'legacy'))
from common import BASE,write_new,sha
from supervisor import supervise
B=BASE/'e0';B.mkdir();(B/'protected').mkdir();(B/'protected/slots').mkdir();(B/'protected/inputs').mkdir();(B/'external').mkdir()
(B/'protected/inputs/frozen.bin').write_bytes(b'CPU_FIXTURE_NO_MODEL')
write_new(B/'external/REGISTER.json',dict(stage='E0',pairs=1,port_hashes={str(p.relative_to(H)):sha(p) for p in H.rglob('*.py')},at_ns=time.monotonic_ns()))
rows=[]
for name in ('A','B'):
    folder=B/'external'/name; case=B/'external'/(name+'.json'); active=B/'protected/slots'/name
    write_new(case,dict(active=str(active),frames=14,interval=.04))
    def received(row,proc):
        if row['event']=='READY':return b'GO\n'
    result=supervise([sys.executable,'-B',str(H/'legacy/cpu_child.py'),str(case)],active,[B/'protected/slots',B/'protected/inputs'],folder,5,received)
    write_new(B/'external'/(name+'_RESULT.json'),result);rows.append(dict(slot=name,result=result))
write_new(B/'external/REPRODUCTION.json',dict(rows=rows,natural_reproduced=any('sealed storage changed' in str(x['result']) for x in rows),writer_PID=None,actual_operation_time=None))
print(json.dumps(rows))
