#!/usr/bin/env python3
"""Compile/run independent CPU checks against an already built plan probe.

Does not configure/build native libraries, download anything, or use a GPU.
The supplied libraries must correspond to the supplied staged source. Their
hashes are recorded, not treated as correctness certificates.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--lib',type=Path,required=True)
    p.add_argument('--probe-include',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--sanitize',choices=('none','address-undefined'),default='none')
    a=p.parse_args()
    source=a.source.resolve();lib=a.lib.resolve();here=Path(__file__).resolve().parent
    includes=[source/'ggml/include',source/'ggml/src']
    if a.probe_include:includes.append(a.probe_include.resolve())
    results={}
    with tempfile.TemporaryDirectory(prefix='hs-independent-native-') as temporary:
        for name in ('test_plan_probe','test_eval_false_success'):
            binary=Path(temporary)/name
            cmd=['c++','-std=c++17','-O0','-g']
            if a.sanitize=='address-undefined':cmd+=['-fsanitize=address,undefined','-fno-sanitize-recover=all']
            for include in includes:cmd+=['-I',str(include)]
            cmd += [str(here/(name+'.cpp')),'-L',str(lib),'-Wl,-rpath,'+str(lib),
                    '-lggml','-lggml-base','-lggml-cpu','-o',str(binary)]
            subprocess.run(cmd,check=True,capture_output=True,text=True)
            run=subprocess.run([str(binary)],check=True,capture_output=True,text=True)
            results[name]=json.loads(run.stdout)
    report={
        'scope':'Native CPU scheduler diagnostics only; not CUDA, kernel equivalence, full-context transaction, or performance evidence.',
        'results':results,
        'test_sources_sha256':{name:sha(here/name) for name in ('test_plan_probe.cpp','test_eval_false_success.cpp','run_independent.py')},
        'staged_source_sha256':{name:sha(source/name) for name in ('ggml/src/ggml-backend.cpp','ggml/src/hs_plan_probe.h','ggml/src/hs_plan_probe.inc')},
        'libraries_sha256':{f.name:sha(f) for f in sorted(lib.glob('libggml*.so.0.23.0'))},
        'test_executable_sanitizers':a.sanitize,
        'asan_options':os.environ.get('ASAN_OPTIONS',''),
        'library_instrumentation':'Provided library build flags must be verified separately; not inferred from executable flags.',
        'gpu_tested':False,'formal_proof':False,
    }
    text=json.dumps(report,indent=2)+'\n'
    if a.output:a.output.write_text(text)
    print(text,end='')

if __name__=='__main__':main()
