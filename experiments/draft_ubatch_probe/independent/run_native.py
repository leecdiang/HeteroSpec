#!/usr/bin/env python3
"""Compile one fixture and retain its exact outcome. Runtime libraries are unmodified."""
import argparse, pathlib, hashlib, json, subprocess
p=argparse.ArgumentParser()
for name in ['fixture','source','library-dir','model','output']:p.add_argument('--'+name,type=pathlib.Path,required=True)
p.add_argument('--expected-exit',type=int,default=0);p.add_argument('--expected-status');p.add_argument('--stderr-contains');a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False);out=a.output.resolve();src=a.source.resolve();lib=a.library_dir.resolve();fixture=a.fixture.resolve();model=a.model.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r={'fixture_sha256':sha(fixture),'model_sha256':sha(model),'library_sha256':{p.name:sha(p) for p in sorted(lib.glob('*.so'))},'sanitizer_scope':'UBSan executable only; linked runtime libraries not instrumented','attempts':[]}
def save():(out/'RECEIPT.json').write_text(json.dumps(r,indent=2)+'\n')
def run(name,cmd):
 row={'name':name,'command':cmd,'status':'STARTED'};r['attempts'].append(row);save()
 with (out/(name+'.stdout')).open('w') as o,(out/(name+'.stderr')).open('w') as e:code=subprocess.run(cmd,stdout=o,stderr=e).returncode
 row.update(status='FINISHED',returncode=code);save();return code
cmd=['c++','-std=c++17','-O2','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(src/'include'),'-I'+str(src/'ggml/include'),'-I'+str(src/'vendor'),str(fixture),'-L'+str(lib),'-Wl,-rpath,'+str(lib),'-lllama','-lggml','-lggml-base','-o',str(out/'native')]
if run('compile',cmd)!=0:raise SystemExit('Compilation failed; retained receipt')
code=run('native',[str(out/'native'),str(model),str(out/'attempts.jsonl')]);r['expected_exit']=a.expected_exit;r['expected_exit_observed']=code==a.expected_exit
try:
 result=json.loads((out/'native.stdout').read_text());cases=result.get('attempts',[])
 r['reported_status']=result.get('status');r['cases']=len(cases);r['cycles']=sum(len(x.get('cycles',[])) for x in cases)
 for key in ['serialized_committed_sequence_match','post_trim_continuation_match','endpoint_match']:
  r[key+'_failures']=sum(x.get(key) is False for x in cases)
except json.JSONDecodeError:result={}
if a.expected_status:r['expected_status_observed']=result.get('status')==a.expected_status
if a.stderr_contains:r['expected_stderr_observed']=a.stderr_contains in (out/'native.stderr').read_text()
r['review_check_pass']=all(v for k,v in r.items() if k.startswith('expected_') and k.endswith('_observed'));save();print(json.dumps(r,indent=2));raise SystemExit(0 if r['review_check_pass'] else 1)
