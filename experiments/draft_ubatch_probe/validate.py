#!/usr/bin/env python3
"""Compile/run the independent native CPU fixture, retaining every process log."""
import argparse,pathlib,subprocess,json,hashlib,os
p=argparse.ArgumentParser();p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--library-dir',type=pathlib.Path,required=True);p.add_argument('--model',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
root=pathlib.Path(__file__).resolve().parent;out=a.output.resolve();source=a.source.resolve();lib=a.library_dir.resolve();model=a.model.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt={'scope':'CPU synthetic same-model protocol fixture; no Windows-worker/GPU/old-R qualification','attempts':[],'model_sha256':sha(model),'source_hashes':{str(p.relative_to(source)):sha(p) for p in [source/'src/llama-context.cpp',source/'src/llama-graph.cpp',source/'src/llama-kv-cache.cpp',source/'include/llama.h']},'implementation_hashes':{p.name:sha(p) for p in [root/'test_native.cpp',root/'stage.py',root/'test_stage.py']},'library_hashes':{p.name:sha(p) for p in lib.glob('*.so')},'sanitizer_scope':'UBSan test executable only; native libraries not instrumented by this runner'}
def save(): (out/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
def run(name,cmd):
 rec={'name':name,'command':cmd,'status':'STARTED'};receipt['attempts'].append(rec);save()
 with (out/(name+'.stdout')).open('w') as o,(out/(name+'.stderr')).open('w') as e:rc=subprocess.run(cmd,stdout=o,stderr=e).returncode
 rec.update(returncode=rc,status='PASS' if rc==0 else 'FAIL');save()
 if rc:raise RuntimeError(name+' failed; retained in receipt')
run('stage-tests',['python',str(root/'test_stage.py')])
run('compile',['g++','-std=c++17','-O2','-g','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(source/'include'),'-I'+str(source/'ggml/include'),'-I'+str(source/'vendor'),str(root/'test_native.cpp'),'-L'+str(lib),'-Wl,-rpath,'+str(lib),'-lllama','-lggml','-lggml-base','-o',str(out/'native')])
run('native',[str(out/'native'),str(model),str(out/'attempts.jsonl')])
report=json.loads((out/'native.stdout').read_text());receipt.update(status=report['status'],cases=len(report['attempts']),checks=report['checks']);save()
