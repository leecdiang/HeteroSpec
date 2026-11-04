#!/usr/bin/env python3
"""Compile isolated experimental operators; never interpret no GPU as a pass."""
import argparse, pathlib, subprocess, os, json, hashlib, re
p=argparse.ArgumentParser();p.add_argument('--cuda',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
root=pathlib.Path(__file__).resolve().parent;out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);(out/'tmp').mkdir()
env=os.environ.copy();env['TMPDIR']=str(out/'tmp');env['PATH']=str(a.cuda/'bin')+':'+env.get('PATH','')
records=[]
def run(cmd,log):
 r=subprocess.run(list(map(str,cmd)),env=env,capture_output=True,text=True);(out/log).write_text(r.stdout+r.stderr);records.append({'command':list(map(str,cmd)),'exit':r.returncode,'log':log});return r.returncode
nvcc=a.cuda/'bin/nvcc';flags=[nvcc,'-ccbin','/usr/bin/g++-14','-std=c++17']
rc=run(flags+['-arch=compute_89','-ptx',root/'kernels.cu','-o',out/'kernels-sm89.ptx'],'ptx.log')
if not rc:rc=run(flags+['-gencode','arch=compute_89,code=sm_89','-gencode','arch=compute_120a,code=sm_120a','-Xptxas=-v',root/'kernels.cu',root/'check_gpu.cu','-o',out/'check_gpu'],'compile.log')
execution='NOT_RUN'
if not rc:
 result=run([out/'check_gpu'],'run.log');execution={0:'FINITE_PREQUANTIZED_COMPARISON_PASS',77:'NOT_RUN_NO_DEVICE'}.get(result,'FAILED')
 sass=run([a.cuda/'bin/cuobjdump','--dump-sass',out/'check_gpu'],'sass.log')
else:sass=-1
receipt={'compile':'PASS' if not rc else 'FAILED','gpu_execution':execution,'sass_dump':'AVAILABLE_NOT_PROVEN' if sass==0 else 'UNAVAILABLE','frozen_runtime_equivalence':'NOT_ESTABLISHED','performance':'NOT_MEASURED','records':records,'source_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [root/'kernels.cu',root/'check_gpu.cu',root/'validate.py']},'artifact_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()}}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
raise SystemExit(1 if rc or execution=='FAILED' else 0)
