"""Compile/link the one-attempt pilot against original R archives; no ELF execution."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(1048576),b''):h.update(x)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--host-root',required=True);p.add_argument('--attempt',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 here=Path(__file__).resolve().parent;root=Path(a.host_root);out=Path(a.out);attempt=json.loads(Path(a.attempt).read_text())
 if out.exists():raise RuntimeError('fresh compile directory')
 binding=json.loads((here.parent/'native_chain_successor_20261112/ORIGINAL_BUILD_BINDINGS.json').read_text())
 item=next(x for x in binding if x['build_root']=='run-01/build-R-01')
 archives=[]
 for r in item['archives']:
  f=root/r['path'].removeprefix('${HS_ROOT}/')
  if f.stat().st_size!=r['bytes'] or sha(f)!=r['sha256']:raise RuntimeError('original numerical archive differs')
  archives.append(f)
 ref=root/'repository-01/benchmarks/linux_transfer_v1/native/reference.cpp'
 if sha(ref)!='111401574d53c534e3a39cac75785ae5ae5fa9a61b44fc7ada989a96305f4723':raise RuntimeError('full original reference differs')
 out.mkdir();src=root/'run-01/stage-03/sources/reference';original=here.parent/'native_chain_successor_20261112/native'
 (out/'frozen_reference_primitives.inc').write_bytes(ref.read_bytes().split(b'int main(int argc,char**argv){try{')[0])
 derivation={}
 for name in ['active_kv.hpp','active_kv.cpp']:
  raw=(original/name).read_text();new=raw.replace('ProductionGate','PilotGate')
  new=new.replace('#include "../budget_writer/hooks.hpp"','#include "'+str((original.parent/'budget_writer/hooks.hpp').resolve())+'"')
  if name.endswith('.hpp'):new=new.replace('#pragma once','#pragma once\n#include "pilot_gate.hpp"',1)
  (out/name).write_text(new);derivation[name]=dict(original_sha256=sha(original/name),derived_sha256=sha(out/name),changes='concrete admission type only; tensor extraction/arithmetic unchanged')
 (out/'active_kv_host.hpp').write_bytes((original/'active_kv_host.hpp').read_bytes())
 # Preserve relative include resolution in the copied native headers.
 (out/'budget_writer').symlink_to((here.parent/'native_chain_successor_20261112/budget_writer').resolve(),target_is_directory=True)
 flags=['-std=c++17','-O0','-g','-fno-inline','-fno-lto','-Wall','-Wextra','-DHS_PILOT_RUN_ID='+json.dumps(attempt['run_id']),'-DHS_PILOT_OUTPUT='+json.dumps(attempt['native_output'])]
 flags+=['-I'+str(x) for x in [out,here,src/'include',src/'src',src/'ggml/include',src/'ggml/src',src/'vendor',root/'repository-01/benchmarks/linux_transfer_v1/native']]
 commands=[]
 def run(cmd,name):
  commands.append(cmd)
  with (out/name).open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),timeout=180)
  if r.returncode:raise RuntimeError('compile failed, retained '+name)
 objects=[]
 for name,path in [('pilot',here/'pilot.cpp'),('active_kv',out/'active_kv.cpp')]:
  obj=out/(name+'.o');run(['/usr/bin/g++']+flags+['-c',str(path),'-o',str(obj)],name+'-compile.log');objects.append(obj)
 cuda=Path('/usr/local/cuda-12.5/targets/x86_64-linux/lib');exe=out/'pilot-single-attempt'
 run(['/usr/bin/g++','-O0','-fno-lto']+list(map(str,objects))+['-Wl,--start-group']+list(map(str,archives))+['-Wl,--end-group','-lgomp','-lpthread','-lm',str(cuda/'libcudart.so'),str(cuda/'libcublas.so'),str(cuda/'libcublasLt.so'),str(cuda/'libculibos.a'),str(cuda/'stubs/libcuda.so'),'-ldl','-lrt','/usr/local/lib/libnccl.so','-Wl,-rpath,'+str(cuda)+':/usr/local/lib','-o',str(exe)],'link.log')
 run(['readelf','-d',str(exe)],'readelf.log')
 receipt=dict(status='COMPILED_NOT_EXECUTED',executable_sha256=sha(exe),bytes=exe.stat().st_size,derivation=derivation,archives=item['archives'],commands=commands,attempt=attempt,source_files={str(x.name):sha(x) for x in [here/'pilot.cpp',here/'pilot_gate.hpp',here/'CASE_FROZEN.json']},GPU_calls=0)
 (out/'BUILD.private.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['status','executable_sha256','bytes']}))
if __name__=='__main__':main()
