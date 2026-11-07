"""Explicit CPU replacement only: no backend, model or GPU loader imports."""
import ctypes
import json
import os
from pathlib import Path
import sys
import time

case=json.loads(Path(sys.argv[1]).read_text());active=Path(case['active'])
k=ctypes.WinDLL('kernel32');k.GetModuleHandleW.argtypes=[ctypes.c_wchar_p];k.GetModuleHandleW.restype=ctypes.c_void_p
for lib in ('vulkan-1.dll','ggml-vulkan.dll','nvcuda.dll','cudart64_12.dll'):
    if k.GetModuleHandleW(lib):raise SystemExit('GPU library present in CPU child')
print(json.dumps(dict(event='READY',PID=os.getpid(),purpose='CPU_ONLY')),flush=True)
if case.get('quick_exit'):raise SystemExit(0)
if sys.stdin.readline()!='GO\n':raise SystemExit(19)
if case.get('bad_path'):
    p=Path(case['bad_path']);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'CPU_INTENTIONAL_SEALED_MUTATION')
ack=(active/'PRODUCER_ACK.txt').open('xb')
with (active/'DATA.bin').open('xb') as data:
    for i in range(case.get('frames',14)):
        line=(json.dumps(dict(event='FRAME',index=i,payload='x'*case.get('payload',256)))+'\n').encode()
        sys.stdout.buffer.write(line);sys.stdout.buffer.flush()
        sys.stderr.buffer.write(b'CPU_STDERR_APPEND\n');sys.stderr.buffer.flush()
        ack.write((str(i)+'\n').encode());ack.flush();os.fsync(ack.fileno())
        data.write(bytes([i%256])*4096);data.flush()
        time.sleep(case.get('interval',.04))
ack.close()
if case.get('timeout_child'):time.sleep(10)
if case.get('truncate_output'):
    with (active/'DATA.bin').open('wb') as f:f.write(b'truncated')
print(json.dumps(dict(event='CPU_RESULT',frames=case.get('frames',14))),flush=True)
if case.get('abnormal_exit'):raise SystemExit(23)
