"""Compile/link live R/candidate with original numerical archives, no ELF run."""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--out',required=True);a=p.parse_args();cfg=json.loads(Path(a.config).read_text());host=Path(cfg['host_root']);root=Path(cfg['root']);here=Path(__file__).resolve().parent;out=Path(a.out)
 if out.exists():raise RuntimeError('fresh build epoch')
 bindings=json.loads((here.parent/'native_chain_successor_20261112/ORIGINAL_BUILD_BINDINGS.json').read_text());old=json.loads((here.parent/'bounded_lifecycle_20261113/EVIDENCE/COMPILED_IDENTITIES.json').read_text())['images'][0]['receipt']['source_identities']
 for n,h in old:
  if sha(host/n)!=h:raise RuntimeError('original full source differs '+n)
 producer=Path(cfg['producer_build']);front=[producer/'build/common/libllama-common.a',producer/'build/common/libllama-common-base.a',producer/'build/vendor/cpp-httplib/libcpp-httplib.a'];frontobjs=[producer/'server-task-03.o',producer/'server-common-04.o',producer/'server-chat-06.o'];frozen={'build/common/libllama-common.a':'b04bb9125e580960afaab7140b1aea868010f4c434aed6591f07e3200a35b247','build/common/libllama-common-base.a':'0d32a74dbd666dc604c0f52a7aaede6826585d7286f7654babce0c3397cbe07f','build/vendor/cpp-httplib/libcpp-httplib.a':'d5f2e179c047c8ad3aaf517f355232ec5281e8d126094554734e008de1671d5e','server-task-03.o':'fd40bd3171993b7ceb5907a9bfabb3fc7c185be688ae8d05043a380c44e2a0bb','server-common-04.o':'13c3e162fa6c23154e671a4ac545e3bbad7050c9f64f63b78b180571dec2f155','server-chat-06.o':'a918caadb4103bb1f2162b62a52f4f36d61567b674c423141cd1a140db81d7ce'}
 for f in front+frontobjs:
  if sha(f)!=frozen[str(f.relative_to(producer))]:raise RuntimeError('pinned parser-only object differs')
 out.mkdir();ref=host/old[0][0];(out/'frozen_reference_primitives.inc').write_bytes(ref.read_bytes().split(b'int main(int argc,char**argv){try{')[0]);original=here.parent/'native_chain_successor_20261112/native'
 for n in ['active_kv.hpp','active_kv.cpp']:
  s=(original/n).read_text().replace('ProductionGate','LiveGate').replace('#include "../budget_writer/hooks.hpp"','#include "'+str((original.parent/'budget_writer/hooks.hpp').resolve())+'"')
  if n.endswith('.cpp'):
   point='need(buffer_owner->buffer,"actual view/source backend buffer");'
   if s.count(point)!=1:raise RuntimeError('unknown KV buffer validation point')
   s=s.replace(point,point+'auto* device=ggml_backend_buft_get_device(ggml_backend_buffer_get_type(buffer_owner->buffer));need(device&&ggml_backend_dev_type(device)==GGML_BACKEND_DEVICE_TYPE_GPU,"actual K/V must reside on GPU");')
  if n.endswith('.hpp'):s=s.replace('#pragma once','#pragma once\n#include "live_gate.hpp"',1)
  (out/n).write_text(s)
 (out/'active_kv_host.hpp').write_bytes((original/'active_kv_host.hpp').read_bytes());(out/'budget_writer').symlink_to((original.parent/'budget_writer').resolve(),target_is_directory=True);commands=[];artifacts=[];start=time.monotonic()
 def run(c,log):
  commands.append(c)
  with (out/log).open('x') as f:r=subprocess.run(c,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),timeout=180)
  if r.returncode:raise RuntimeError('retained build failure '+log)
 for kind,which in [('CANDIDATE','loop4')]:
  src=host/('run-01/stage-03/sources/reference' if which=='R' else 'run-01/stage-04/sources/loop4');item=next(x for x in bindings if x['build_root']=='run-01/build-'+which+'-01');archives=[]
  for x in item['archives']:
   f=host/x['path'].removeprefix('${HS_ROOT}/')
   if f.stat().st_size!=x['bytes'] or sha(f)!=x['sha256']:raise RuntimeError('original numerical archive differs')
   archives.append(f)
  inc=[out,here]+[src/x for x in ['include','src','ggml/include','ggml/src','common','vendor','tools/server','tools/mtmd']]+[host/'repository-01/benchmarks/linux_transfer_v1/native',host/'pr210-stage-b-build-02/frontend'];flags=['-std=c++17','-O0','-g','-fno-inline','-fno-lto','-Wall','-Wextra','-DHS_LIVE_ROOT='+json.dumps(str(root)),'-DHS_LIVE_MANIFEST_SHA='+json.dumps(sha(root/'MANIFEST.json')),'-DHS_LIVE_KIND='+json.dumps(kind)]+['-I'+str(x) for x in inc]
  if kind=='CANDIDATE':flags+=['-DLIVE_CANDIDATE=1','-DHS_LIVE_RESIDENT_HEADER='+json.dumps(str(host/'pr210-stage-b-build-02/frontend/resident_context.hpp'))]
  objs=[]
  for n,path in [('native',here/'native.cpp'),('producer',here/'producer.cpp'),('active_kv',out/'active_kv.cpp')]:
   obj=out/(kind+'-'+n+'.o');use=flags
   if n=='producer':
    frontend=host/'run-01/stage-03/sources/reference'
    use=[f for f in flags if not f.startswith('-I')]+['-I'+str(x) for x in [out,here]+[frontend/x for x in ['include','src','ggml/include','ggml/src','common','vendor','tools/server','tools/mtmd']]]
   run(['/usr/bin/g++']+use+['-c',str(path),'-o',str(obj)],kind+'-'+n+'.log');objs.append(obj)
  cuda=Path('/usr/local/cuda-12.5/targets/x86_64-linux/lib');exe=out/('live-'+kind.lower());run(['/usr/bin/g++','-O0','-fno-lto','-Wl,--gc-sections']+list(map(str,objs+frontobjs))+['-Wl,--start-group']+list(map(str,front+archives))+['-Wl,--end-group','-lgomp','-lpthread','-lm',str(cuda/'libcudart.so'),str(cuda/'libcublas.so'),str(cuda/'libcublasLt.so'),str(cuda/'libculibos.a'),str(cuda/'stubs/libcuda.so'),'-ldl','-lrt','/usr/local/lib/libnccl.so','-Wl,-rpath,'+str(cuda)+':/usr/local/lib','-o',str(exe)],kind+'-link.log');run(['readelf','-d',str(exe)],kind+'-readelf.log');artifacts.append(dict(kind=kind,file=exe.name,sha256=sha(exe),bytes=exe.stat().st_size,archives=item['archives']))
 receipt=dict(status='COMPILED_LINKED_NOT_EXECUTED',elapsed_s=time.monotonic()-start,artifacts=artifacts,source_identities=old,parser_objects=frozen,commands=commands,source_files={x.name:sha(x) for x in here.iterdir() if x.is_file()},original_gate_unchanged=True,generated_files={x.name:sha(x) for x in out.iterdir() if x.is_file() and x.suffix in ['.hpp','.cpp','.inc']},KV_derivation='concrete gate type + actual each K/V buffer GPU-placement assertion; arithmetic/extraction unchanged',GPU_contexts=0,model_objects=0,forwards=0)
 (out/'BUILD.private.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(status=receipt['status'],elapsed_s=receipt['elapsed_s'],artifacts=[{k:v for k,v in x.items() if k!='archives'} for x in artifacts])))
if __name__=='__main__':main()
