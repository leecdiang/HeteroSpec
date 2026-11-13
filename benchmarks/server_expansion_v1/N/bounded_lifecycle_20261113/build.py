"""CPU compile/link only, binding the dedicated successor root and manifest."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--host-root',required=True);p.add_argument('--ledger-root',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 here=Path(__file__).resolve().parent;root=Path(a.host_root);out=Path(a.out)
 if out.exists():raise RuntimeError('fresh build required')
 binding=json.loads((here.parent/'native_chain_successor_20261112/ORIGINAL_BUILD_BINDINGS.json').read_text());item=next(x for x in binding if x['build_root']=='run-01/build-R-01');archives=[]
 for r in item['archives']:
  f=root/r['path'].removeprefix('${HS_ROOT}/')
  if f.stat().st_size!=r['bytes'] or sha(f)!=r['sha256']:raise RuntimeError('frozen numerical archive differs')
  archives.append(f)
 identities=[('repository-01/benchmarks/linux_transfer_v1/native/reference.cpp','111401574d53c534e3a39cac75785ae5ae5fa9a61b44fc7ada989a96305f4723'),('run-01/stage-03/sources/reference/include/llama.h','3d1b18eda626c1b9ecf5bda0798e65b974a8f70f30d56726610633a980cb4160'),('run-01/stage-03/sources/reference/common/chat.cpp','abab0d03a111bd198693a518c7cdd07a33326a6a6685cc182a88d4fdae5f61dc'),('pr210-stage-b-build-02/frontend/worker.cpp','429ca63224bffdc62fff65cc0c4b4199ea0ae9677fa3b087d1bbbe1d01b12938'),('pr210-stage-b-build-02/frontend/resident_context.hpp','02b361035da2baa586e7c2192ca05a87036ef4336a478f954ee1a006fa6b8647')]
 for n,h in identities:
  if sha(root/n)!=h:raise RuntimeError('original source identity differs: '+n)
 out.mkdir();ref=root/identities[0][0];src=root/'run-01/stage-03/sources/reference';original=here.parent/'native_chain_successor_20261112/native'
 (out/'frozen_reference_primitives.inc').write_bytes(ref.read_bytes().split(b'int main(int argc,char**argv){try{')[0]);derivation={}
 for n in ['active_kv.hpp','active_kv.cpp']:
  new=(original/n).read_text().replace('ProductionGate','SuccessorGate').replace('#include "../budget_writer/hooks.hpp"','#include "'+str((original.parent/'budget_writer/hooks.hpp').resolve())+'"')
  if n.endswith('.hpp'):new=new.replace('#pragma once','#pragma once\n#include "successor_gate.hpp"',1)
  (out/n).write_text(new);derivation[n]=dict(original=sha(original/n),derived=sha(out/n),changes='admission type only; extraction unchanged')
 (out/'active_kv_host.hpp').write_bytes((original/'active_kv_host.hpp').read_bytes());(out/'budget_writer').symlink_to((original.parent/'budget_writer').resolve(),target_is_directory=True)
 flags=['-std=c++17','-O0','-g','-fno-inline','-fno-lto','-Wall','-Wextra','-DHS_SUCC_ROOT='+json.dumps(a.ledger_root),'-DHS_SUCC_MANIFEST_SHA='+json.dumps(sha(Path(a.ledger_root)/'MANIFEST.json'))]
 flags+=['-I'+str(x) for x in [out,here,src/'include',src/'src',src/'ggml/include',src/'ggml/src',src/'vendor',root/'repository-01/benchmarks/linux_transfer_v1/native']];commands=[]
 def run(c,n):
  commands.append(c)
  with (out/n).open('w') as f:r=subprocess.run(c,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),timeout=180)
  if r.returncode:raise RuntimeError('build failure retained: '+n)
 objs=[]
 for n,p in [('lifecycle',here/'lifecycle.cpp'),('active_kv',out/'active_kv.cpp')]:
  o=out/(n+'.o');run(['/usr/bin/g++']+flags+['-c',str(p),'-o',str(o)],n+'.log');objs.append(o)
 cuda=Path('/usr/local/cuda-12.5/targets/x86_64-linux/lib');exe=out/'bounded-reference'
 run(['/usr/bin/g++','-O0','-fno-lto']+list(map(str,objs))+['-Wl,--start-group']+list(map(str,archives))+['-Wl,--end-group','-lgomp','-lpthread','-lm',str(cuda/'libcudart.so'),str(cuda/'libcublas.so'),str(cuda/'libcublasLt.so'),str(cuda/'libculibos.a'),str(cuda/'stubs/libcuda.so'),'-ldl','-lrt','/usr/local/lib/libnccl.so','-Wl,-rpath,'+str(cuda)+':/usr/local/lib','-o',str(exe)],'link.log');run(['readelf','-d',str(exe)],'readelf.log')
 receipt=dict(status='COMPILED_NOT_EXECUTED',executable_sha256=sha(exe),bytes=exe.stat().st_size,derivation=derivation,archives=item['archives'],source_identities=identities,commands=commands,source_files={x.name:sha(x) for x in here.iterdir() if x.is_file()},GPU_calls=0)
 (out/'BUILD.private.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['status','executable_sha256','bytes']}))
if __name__=='__main__':main()
