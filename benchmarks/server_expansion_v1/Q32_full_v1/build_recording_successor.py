"""Same numerical archives; full binary PREFILL trace and pinned native SHA ABI.

Both numerical roles receive the identical new frontend. Clean requests keep
state/operand/descriptor observation disabled. Native source04 archives remain
byte-identical; no arithmetic, graph, transaction or proposal code is replaced.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,shutil
from build import read,sha,save,command
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--original',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir();src=Path(__file__).parent;old=a.original;f=a.out/'frontend';shutil.copytree(old/'frontend',f)
 shutil.copy2(src/'geometry_journal_observer.hpp',f/'geometry_observer.hpp');shutil.copy2(src/'native_hash_fast.hpp',f/'native_hash_fast.hpp')
 path=f/'worker.cpp';s=path.read_text();start=s.index('static std::string hash_file(');end=s.index('\n',start);s=s[:start]+'#include "native_hash_fast.hpp"\nstatic std::string hash_file(const fs::path&path){return fast_digest::file(path);}\n'+s[end:]
 anchor='obs=Observer{};';assert s.count(anchor)==1;s=s.replace(anchor,anchor+'obs.journal_path=dir/"prefill-operators.bin";',1)
 anchor='r["geometry"]=json::array();';assert s.count(anchor)==1;s=s.replace(anchor,'r["prefill_descriptor_journal"]=target->obs.journal_meta();'+anchor,1);path.write_text(s)
 path=f/'entry.cpp';s=path.read_text();anchor='result["cases"].push_back(record);';assert s.count(anchor)==1;s=s.replace(anchor,'record["prefill_descriptor_journal"]=ctx->obs.journal_meta();'+anchor,1);path.write_text(s)
 path=f/'m1_capability.hpp';s=path.read_text();anchor='{"threads",phase_threads}';assert s.count(anchor)==1;s=s.replace(anchor,'{"observer_device_type_policy","Per request: immutable device type once per actual device; fresh tensor buffer device every callback"},{"geometry_policy","PREFILL:complete binary descriptors;VERIFY/ORDINARY:JSON"},{"native_hash_file","Full SHA256, read-only mmap, pinned system libcrypto"},{"native_crypto_sha256",hash_file("/usr/lib/x86_64-linux-gnu/libcrypto.so.3")},'+anchor,1);path.write_text(s)
 path=f/'resident_context.hpp';s=path.read_text();anchor='auto t=Clock::now();int rc=llama_decode(owner.c,b);';assert s.count(anchor)==1;s=s.replace(anchor,'if(owner.capture)std::cerr<<"Q32_DECODE_BEGIN "<<phase<<" "<<owner.obs.base<<" "<<group.count<<" "<<wanted.size()<<std::endl;'+anchor,1);anchor='hsc::decode_end();owner.calls++;';assert s.count(anchor)==1;s=s.replace(anchor,anchor+'if(owner.capture)std::cerr<<"Q32_DECODE_END "<<phase<<" "<<owner.obs.base<<" "<<group.count<<" "<<since(t)<<std::endl;',1);path.write_text(s)
 crypto=Path('/usr/lib/x86_64-linux-gnu/libcrypto.so.3');assert crypto.is_file();crypto_sha=sha(crypto)
 verified=set()
 for core in('loop4','packed'):
  d=read(old/core/'DEPENDENCIES.json')
  for p,h in d['files'].items():
   if p not in verified:assert sha(p)==h;verified.add(p)
 def one(core):
  original=old/core;dest=a.out/core;dest.mkdir();native=a.root/'run-01'/f'build-{core}-01/native';args=read(original/'compile-frontend/command.json')['argv'];args=[x.replace(str(old/'frontend'),str(f))for x in args];args[args.index('-o')+1]=str(dest/'frontend.o');args[args.index('-MF')+1]=str(dest/'frontend.d');command(args,native,dest/'compile')
  args=read(original/'link-frontend/command.json')['argv'];args=[x.replace(str(original/'frontend.o'),str(dest/'frontend.o')).replace(str(original/'transfer-worker'),str(dest/'transfer-worker'))for x in args];command(args,native,dest/'link')
  deps=read(original/'DEPENDENCIES.json');names=dict(deps['files']);names[str(crypto)]=crypto_sha
  for s in(dest/'frontend.d').read_text().replace('\\\n',' ').split(':',1)[1].split():
   p=Path(s);p=p if p.is_absolute()else native/p;names[str(p.resolve())]=sha(p)
  for p in[dest/'frontend.o',dest/'transfer-worker.map',*f.rglob('*'),dest/'compile/command.json',dest/'link/command.json']:
   if p.is_file():names[str(p.resolve())]=sha(p)
  save(dest/'DEPENDENCIES.json',{**deps,'files':names,'numerical_archives_changed':False,'explicit_runtime_DSO':dict(path=str(crypto),sha256=crypto_sha)})
  base=read(original/'BUILD.json');exe=dest/'transfer-worker';save(dest/'BUILD.json',{**base,'executable':str(exe),'executable_sha256':sha(exe),'dependency_closure_sha256':sha(dest/'DEPENDENCIES.json'),'status':'RECORDING_ABI_SUCCESSOR_NOT_QUALIFIED','original_native_BUILD_sha256':sha(original/'BUILD.json'),'original_numerical_core_binding_sha256':sha(original/'CORE_BINDING.json'),'native_crypto_sha256':crypto_sha,'frontend':{str(p.relative_to(f)):sha(p)for p in f.rglob('*')if p.is_file()},'numerical_archives':'Exact unchanged source04 numerical core and original CUDA archives; new recording/SHA frontend only','qualification':'Must qualify same new frontend for both projection modes against unchanged own32B R'});print('Q32_RECORDING_SUCCESSOR_BUILT',core,sha(exe),flush=True)
  shutil.copy2(original/'CORE_BINDING.json',dest/'CORE_BINDING.json')
 with ThreadPoolExecutor(max_workers=2)as pool:list(pool.map(one,('loop4','packed')))
 save(a.out/'COMPLETE.json',dict(passed=True,numerical_archives_changed=False,qualified=False,originals_modified=False,crypto_DSO_sha256=crypto_sha,scope='Testable recording/ABI correction, not proof of the old timeout cause; no performance panel before full new qualification'))
if __name__=='__main__':main()
