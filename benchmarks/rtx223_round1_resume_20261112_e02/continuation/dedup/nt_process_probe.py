"""Read-only NT process metadata, to distinguish sandbox view from host view."""
from pathlib import Path
import ctypes as C,struct,json,datetime
HERE=Path(__file__).resolve().parent
nt=C.WinDLL('ntdll',use_last_error=True)
f=nt.NtQuerySystemInformation
f.argtypes=[C.c_ulong,C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong)];f.restype=C.c_long
size=1024*1024;ret=C.c_ulong()
for _ in range(8):
    buf=C.create_string_buffer(size)
    status=f(5,buf,size,C.byref(ret))
    if status!=-1073741820:break
    size=max(size*2,ret.value+65536)
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'NtQuerySystemInformation(SystemProcessInformation)','status_hex':hex(status&0xffffffff),'returned_bytes':ret.value,'records':[]}
if status>=0:
    base=C.addressof(buf);offset=0
    while offset<ret.value:
        nxt,threads=struct.unpack_from('<II',buf,offset)
        created=struct.unpack_from('<q',buf,offset+32)[0]
        nbytes,maxbytes=struct.unpack_from('<HH',buf,offset+56)
        ptr=struct.unpack_from('<Q',buf,offset+64)[0]
        pid,ppid=struct.unpack_from('<QQ',buf,offset+80)
        if nbytes:
            if not base<=ptr<=base+ret.value-nbytes:raise RuntimeError('invalid returned string pointer')
            name=C.string_at(ptr,nbytes).decode('utf-16-le')
        else:name=''
        out['records'].append({'pid':pid,'ppid':ppid,'name':name,'threads':threads,'created_utc':datetime.datetime.fromtimestamp(created/10000000-11644473600,datetime.timezone.utc).isoformat() if created>0 else None})
        if not nxt:break
        offset+=nxt
(HERE/'private/NT_PROCESSES.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({'utc':out['utc'],'method':out['method'],'status_hex':out['status_hex'],'returned_bytes':out['returned_bytes'],'total_processes':len(out['records']),'relevant':[r for r in out['records'] if any(x in r['name'].lower() for x in ('worker','llama','python','nvcc','zig','codex','opencode','ninja'))]},indent=2))
