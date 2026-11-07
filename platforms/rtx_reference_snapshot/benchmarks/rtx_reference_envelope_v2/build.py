"""Offline compile against unchanged shared core import libraries."""
import subprocess,time
from common import V,load,save,sha
from pathlib import Path
s=load(Path(load(V/'LOCAL_RUN.json')['root'])/'RUN_SPEC.json')
cmd=[s['compiler']['path'],'c++','-O3','-DNDEBUG','-D_CRT_SECURE_NO_WARNINGS','-std=c++17','-DGGML_BACKEND_DL','-DGGML_SHARED','-I'+s['ggml_include'],'-I'+s['vendor_include'],str(V/'native.cpp'),str(V/'build/libggml.dll.a'),str(V/'build/libggml-base.dll.a'),'-lpsapi','-lbcrypt','-o',str(V/'build/native.exe')]
t=time.perf_counter();r=subprocess.run(cmd,capture_output=True,timeout=600);save(V/'BUILD.json',dict(command=cmd,exit=r.returncode,stdout=r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace'),seconds=time.perf_counter()-t,source_sha256=sha(V/'native.cpp'),native_sha256=sha(V/'build/native.exe') if r.returncode==0 else None,GPU_calls=0));assert r.returncode==0
