"""Timer-repair CPU-only Job Object watchdog, conservative complete descendant lifetime cap."""
import argparse,ctypes,json,os,subprocess,sys,time
from ctypes import wintypes as W
from pathlib import Path
ROOT=Path(__file__).parent
def derived_bytes():
    total=0
    for x in ROOT.rglob('*'):
        try:
            if x.is_file():total+=x.stat().st_size
        except FileNotFoundError:pass # CMake/compiler scratch file disappeared during sampling.
    return total
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2);f.write('\n')
class Basic(ctypes.Structure):
    _fields_=[('process_time',ctypes.c_longlong),('job_time',ctypes.c_longlong),('flags',W.DWORD),('min_ws',ctypes.c_size_t),('max_ws',ctypes.c_size_t),('active',W.DWORD),('affinity',ctypes.c_size_t),('priority',W.DWORD),('scheduling',W.DWORD)]
class IO(ctypes.Structure):_fields_=[(x,ctypes.c_ulonglong) for x in ('ro','wo','oo','rb','wb','ob')]
class Extended(ctypes.Structure):_fields_=[('basic',Basic),('io',IO),('process_memory',ctypes.c_size_t),('job_memory',ctypes.c_size_t),('peak_process',ctypes.c_size_t),('peak_job',ctypes.c_size_t)]
class Accounting(ctypes.Structure):
    _fields_=[(x,ctypes.c_longlong) for x in ('user','kernel','period_user','period_kernel')]+[(x,W.DWORD) for x in ('faults','total','active','terminated')]
