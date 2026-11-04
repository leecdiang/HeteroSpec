"""Recompile the unchanged experimental kernel with explicit FTZ; no GPU launch."""
from pathlib import Path
import argparse,subprocess,hashlib,json,os,re
if not __debug__: raise RuntimeError('Run without -O: assertions are verification checks')
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--cuda',type=Path,required=True);p.add_argument('--frozen-entries',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);(a.output/'tmp').mkdir()
src=HERE/'kernels-original.cu';assert hashlib.sha256(src.read_bytes()).hexdigest()=='a8a465ac224ba8aa9613946edbe5cf7291a063f1a4c171f366a143aa82586bb9'
env=os.environ.copy();env['TMPDIR']=str(a.output/'tmp');env['PATH']=str(a.cuda/'bin')+':'+env.get('PATH','');records=[]
def run(cmd,name):
 r=subprocess.run(list(map(str,cmd)),env=env,capture_output=True,text=True);(a.output/name).write_text(r.stdout+r.stderr);records.append({'command':list(map(str,cmd)),'returncode':r.returncode,'log':name});assert r.returncode==0,name
nvcc=a.cuda/'bin/nvcc';common=[nvcc,'-ccbin','/usr/bin/g++-14','-std=c++17']
for ftz in ('false','true'):
 run(common+['-ftz='+ftz,'-arch=compute_89','-ptx',src,'-o',a.output/(ftz+'.ptx')],ftz+'-ptx.log')
run(common+['-ftz=true','-gencode','arch=compute_89,code=sm_89','-gencode','arch=compute_120a,code=sm_120a','-Xptxas=-v','-c',src,'-o',a.output/'ftz.o'],'object.log')
run(common+['-ftz=true','-gencode','arch=compute_89,code=sm_89','-gencode','arch=compute_120a,code=sm_120a',HERE/'test_fma_witness.cu',a.output/'ftz.o','-o',a.output/'test_fma_witness'],'witness-compile.log')
probe=subprocess.run([str(a.output/'test_fma_witness')],env=env,capture_output=True,text=True);(a.output/'witness-run.log').write_text(probe.stdout+probe.stderr);records.append({'command':[str(a.output/'test_fma_witness')],'returncode':probe.returncode,'log':'witness-run.log'});assert probe.returncode in (0,77)
run([a.cuda/'bin/cuobjdump','--dump-sass',a.output/'ftz.o'],'sass.log');run([a.cuda/'bin/cuobjdump','--dump-resource-usage',a.output/'ftz.o'],'resources.log')
float_ops=lambda s: re.findall(r'\b(?:fma|add|mul)\.[\w.]*f32\b',s)
counts={}
for ftz in ('false','true'):
 ops=float_ops((a.output/(ftz+'.ptx')).read_text());assert ops;assert all(('.ftz.' in o)==(ftz=='true')for o in ops)
 counts[ftz]={op:ops.count(op)for op in sorted(set(ops))}
frozen={}
for name,pattern in [('q1','ptx228_sm_90_*mul_mat_vec_qIL9ggml_type8ELi1ELb0ELb0ELb0*.ptx'),('q4','ptx228_sm_90_*mul_mat_vec_qIL9ggml_type8ELi4ELb0ELb0ELb0*.ptx'),('quantizer','ptx288_sm_90_*quantize_q8_1*.ptx')]:
 aliases={'q1':'q8_mmvq_q1.sm90.ptx','q4':'q8_mmvq_q4.sm90.ptx','quantizer':'quantize_q8_1.sm90.ptx'}
 expected={'q1':'f117281b6439072168d6b42cec93ce19b27ce089b64bd77effe8d3d3c7f1999e','q4':'7d371052dce8d80f36801245b8c39ef04f40ed84d9781554c93f1c9ab684b7cb','quantizer':'6be2f3cf00f5feeeffb1d886c1c2d6e2d5bc9b3f629811f79ab6ae8d1559e2b1'}
 matches=list(a.frozen_entries.glob(pattern));short=a.frozen_entries/aliases[name]
 if short.exists():matches.append(short)
 assert len(matches)==1,(name,matches);f=matches[0];assert hashlib.sha256(f.read_bytes()).hexdigest()==expected[name], 'wrong frozen entry '+name
 s=f.read_text();ops=float_ops(s)
 frozen[name]={'filename':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'float_operation_counts':{op:ops.count(op)for op in sorted(set(ops))},'div_approx_ftz':len(re.findall(r'\bdiv.approx.ftz.f32\b',s))}
 if name!='quantizer':assert 'fma.rn.ftz.f32' in ops and 'mul.ftz.f32'in ops and 'add.ftz.f32'in ops
 else:assert frozen[name]['div_approx_ftz']>0
r={'status':'FTZ_VARIANT_COMPILED_RECIPE_FLAGS_CHECKED_NOT_EQUIVALENT','frozen_dll_sha256':'8df3d5d6363dab0b221f143992e816d1366be4b076b47ce6b1612a148c0bc09c','frozen_entries':frozen,'candidate_kernel_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'ptx_opcode_counts':counts,'records':records,'gpu_execution':'NOT_RUN_NO_DEVICE' if probe.returncode==77 else 'FINITE_WITNESS_ONLY_PASS','full_dataflow_equivalence':'NOT_PROVEN','quantizer':'NOT_IMPLEMENTED_NOT_QUALIFIED','artifact_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest()for f in a.output.iterdir()if f.is_file()}}
(a.output/'RECIPE_RESULTS.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
