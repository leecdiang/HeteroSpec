"""Freeze and compile isolated old-B and verbatim fixed-upstream device code. No execution."""
from pathlib import Path
import os,json,hashlib,subprocess,importlib.util,re,time
here=Path(__file__).resolve().parent;study=here.parent;prior=study/'rtx223-e09-c1/build-001';runtime=study/'rtx223-round1-resume-20261112-e04/runtime';u=here/'u';cu=u/'ggml/src/ggml-cuda'
out=here/'build-002';out.mkdir(exist_ok=False);(out/'generated').mkdir()
sha=lambda f:hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def write(f,v):f.write_text(json.dumps(v,indent=2),encoding='utf8')
for name in ('bound_mmvq_prefix.cuh','bound_quantizer.cuh'):(out/name).write_bytes((prior/name).read_bytes())
source=(cu/'mmq-few.cu').read_text(encoding='utf8');prefix=source[:source.index('// ggml_is_constant')];prefix+='\n#endif // CUDA only, extracted device definitions\n'
(out/'bound_few_prefix.cuh').write_text(prefix,encoding='utf8')
spec=importlib.util.spec_from_file_location('extract',study/'rtx221-round1-20261112/build_tools/build_operator.py');extract=importlib.util.module_from_spec(spec);spec.loader.exec_module(extract)
qsource=(cu/'quantize.cu').read_text(encoding='utf8');q=extract.extract_function(qsource,'template <mmq_q8_1_ds_layout ds_layout>\nstatic __global__ void quantize_mmq_few_q8_1(');(out/'bound_few_quantizer.cuh').write_text(q,encoding='utf8')
(out/'upstream_wrap.cu').write_bytes((here/'upstream_wrap.cu').read_bytes())
old=(prior/'operator_probe.cu').read_text(encoding='utf8');helper=old[:old.index('static void launch_arm(')];helper=helper.replace('#include "c1_serial_groups.cuh"\n#include "explicit_budget.hpp"','')
main=helper+'\n#include <cmath>\n#include <cfloat>\n#include <cstring>\n'+(here/'main_body_v2.inc').read_text();(out/'main.cu').write_text(main,encoding='utf8')
recipe=json.loads((prior/'COMMAND.json').read_bytes());base=[];cmd=recipe['command'];base=cmd[:cmd.index('-I'+str(prior))];nvcc=base[0];env=recipe['environment'].copy();env['TEMP']=env['TMP']=str(out)
oldinc=[x for x in cmd if x.startswith('-I') and x!='-I'+str(prior)]
newinc=['-I'+str(u/'ggml/include'),'-I'+str(u/'ggml/src'),'-I'+str(u/'vendor'),'-I'+str(cu)]
commands=[]
for name,incs in [('main',oldinc),('upstream_wrap',newinc)]:
 source=out/(name+'.cu');obj=out/(name+'.obj');gen=out/'generated'/name;gen.mkdir()
 commands.append((name,[*base,'-I'+str(out),*incs,'-c',str(source),'-o',str(obj),'-MD','-MF',str(out/(name+'.d')),'--keep','--keep-dir',str(gen)]))
commands.append(('link',[*base,str(out/'main.obj'),str(out/'upstream_wrap.obj'),'-o',str(out/'operator-upstream.exe'),'psapi.lib','bcrypt.lib']))
write(out/'COMMANDS.json',dict(commands=commands,environment=env,PDL='raw standard launch equivalent PDL0 for both; source device PDL helpers unchanged'))
inputs=json.loads((prior/'FREEZE.json').read_bytes())['inputs']
for tree in [u/'ggml',u/'vendor',u/'include']:
 for f in tree.rglob('*'):
  if f.is_file() and f.suffix in ('.cu','.cuh','.cpp','.c','.hpp','.h'):inputs[str(f)]={'sha256':sha(f),'bytes':f.stat().st_size}
for f in [*out.iterdir(),Path(__file__),here/'main_body_v2.inc',here/'upstream_wrap.cu',here/'CONTRACT.json',here/'UPSTREAM_SOURCE.json',here/'PARENT_REUSE_VERIFIED.json',here/'C1_PARENT_VERIFIED.json']:
 if f.is_file():inputs[str(f)]={'sha256':sha(f),'bytes':f.stat().st_size}
write(out/'FREEZE.json',dict(inputs=inputs,upstream_commit='0fb8f157702702f33f4e018de8701b2569a1bc28',old_B_header_unchanged=True,CUDA_calls=0,diagnostic_not_original_candidate=True))
spec=importlib.util.spec_from_file_location('closure',runtime/'input_closure_v2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);held=m.ReadFreeze();started=time.monotonic();results=[]
try:
 for path,row in inputs.items():
  held.add(path)
  if sha(path)!=row['sha256']:raise RuntimeError('input drift '+path)
 for name,argv in commands:
  with (out/(name+'.log')).open('xb') as f:cp=subprocess.run(argv,cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
  results.append(dict(stage=name,returncode=cp.returncode));print(results[-1],flush=True)
  if cp.returncode:break
 changes=[path for path,row in inputs.items() if sha(path)!=row['sha256']];unbound=[]
 allowed={str(Path(x).resolve()).lower() for x in inputs}
 for name in ('main','upstream_wrap'):
  f=out/(name+'.d')
  if not f.exists():continue
  text=re.sub(r'\\\r?\n',' ',f.read_text(encoding='utf8')).strip();pos=text.find(': ')
  if pos<0:raise RuntimeError('bad dep target')
  for x in m.make_words(text[pos+1:]):
   if str(Path(x).resolve()).lower() not in allowed and not Path(x).resolve().is_relative_to(out/'generated'):unbound.append(x)
 result=dict(stages=results,input_changes=changes,unbound_dependencies=unbound,seconds=time.monotonic()-started,executable_sha256=sha(out/'operator-upstream.exe') if (out/'operator-upstream.exe').exists() else None,freeze_sha256=sha(out/'FREEZE.json'),CUDA_initializations=0,kernel_calls=0)
 write(out/'BUILD.json',result);print(json.dumps(result,indent=2),flush=True)
finally:held.release()
