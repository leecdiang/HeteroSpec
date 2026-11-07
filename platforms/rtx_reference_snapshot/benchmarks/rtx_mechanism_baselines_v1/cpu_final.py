"""Capture actual final CPU regression transcript after permanent GPU closure."""
import re,subprocess,sys,time
from common import V,load,save
from prepare_rtx import root
r=root();assert load(r/'GPU_EXECUTION_CLOSED.json')['status']=='PERMANENTLY_CLOSED'
cmd=[sys.executable,'-B','-m','unittest','-v','test_cpu','test_producer','test_adapter'];start=time.monotonic();p=subprocess.run(cmd,cwd=V,capture_output=True,timeout=180);text=p.stdout.decode(errors='replace')+p.stderr.decode(errors='replace');m=re.search(r'Ran (\d+) tests?',text);record=dict(command=cmd,exit=p.returncode,tests=int(m.group(1)) if m else None,seconds=time.monotonic()-start,transcript=text,GPU_calls=0,scope='actual protocol/P0/adapter regressions,real Windows CPU subprocesses,pre-CUDA rejections;raw evidence9 and PE/IAT4 negatives separately recorded')
save(r/'CPU_FINAL_TESTS.json',record);assert p.returncode==0 and m;save(V/'CPU_FINAL_TESTS.json',record);print(record['tests'],'CPU tests PASS')
