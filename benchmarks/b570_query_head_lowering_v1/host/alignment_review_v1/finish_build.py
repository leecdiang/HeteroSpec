"""One scoped compile repair (diagnostic logger name collision); no GPU launch."""
import difflib
import pathlib
import shutil
import subprocess
import time
import sys
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'host'))
from common import load,save,sha,modules

before=modules()
output=ROOT/'host_outputs/alignment_review_v1'
original=(ROOT/'native/host/vulkan.cpp').read_text(encoding='utf-8')
fixed=(HERE/'generated/diagnostic.cpp').read_text(encoding='utf-8')
with (HERE/'diagnostic_fixed.diff').open('x',encoding='utf-8',newline='\n') as f:
    f.write(''.join(difflib.unified_diff(original.splitlines(True),fixed.splitlines(True),fromfile='frozen-host',tofile='diagnostic-name-repair')))
cmd=['C:/Program Files/CMake/bin/cmake.exe','--build',str(output/'build'),'--config','Release']
start=time.monotonic();r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
save(HERE/'OFFLINE_BUILD_REPAIR_01.json',dict(scope='rename logger variable physical_layout; no numerical or frozen-source changes',
    argv=cmd,returncode=r.returncode,elapsed_s=time.monotonic()-start,stdout=r.stdout,stderr=r.stderr,diagnostic_launched=False))
assert r.returncode==0
old=pathlib.Path('C:/hs/b570-geometry-p0/benchmarks/b570_geometry_state_codesign_v1/_host/build/Release')
runtime=output/'build/Release'
for name in ('ggml-base.dll','ggml-vulkan.dll'):shutil.copy2(old/name,runtime/name)
save(output/'CELLS.json',[x['cell'] for x in load(ROOT/'host/S1_INPUTS.json')])
cmd=[str(runtime/'alignment-metadata.exe'),str(output/'CELLS.json'),str(output/'METADATA.jsonl')]
start=time.monotonic();r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
save(HERE/'METADATA_PROCESS.json',dict(argv=cmd,returncode=r.returncode,elapsed_s=time.monotonic()-start,stdout=r.stdout,stderr=r.stderr,
    executable_sha256=sha(runtime/'alignment-metadata.exe'),modules_before=before,modules_after=modules(),
    diagnostic_launched=False,device_queries=0,graph_computes=0))
assert r.returncode==0
print(dict(metadata_exit=r.returncode,diagnostic_launched=False))
