import ctypes,sys,os,json,hashlib,time
from pathlib import Path
k=ctypes.WinDLL('kernel32',use_last_error=True)
a=ctypes.create_unicode_buffer(32768);b=ctypes.create_unicode_buffer(32768)
assert k.GetWindowsDirectoryW(a,len(a)) and k.GetSystemDirectoryW(b,len(b))
r=dict(pid=os.getpid(),sys_executable=sys.executable,version=sys.version,os_name=os.name,windows_directory=a.value,system_directory=b.value,python_sha256=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),environment_presence={k:k in os.environ for k in ['SystemRoot','WINDIR','COMSPEC','PATH','TMP','TEMP']},at_ns=time.perf_counter_ns(),os_creation_filetime=None,os_exit_filetime=None)
print(json.dumps(r,sort_keys=True))
