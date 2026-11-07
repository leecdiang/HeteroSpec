"""Rebuild delivered private cores/frontends using only delivered pinned inputs.

This is a zero-model build proof. New binaries need independent R qualification
before any new experiment; rebuilding does not inherit qualification by itself.
"""
from evidence_host import *

def rebuild(out,all_frontends=False,resume=False):
 out=Path(out).resolve();assert not LOCK.exists()
 if resume:assert out.is_dir() and not (out/'BUILD_PROOF.json').exists()
 else:assert not out.exists();out.mkdir(parents=True)
 deps=ROOT/'repro/native-inputs';pins=read(deps/'INPUTS.json')
 for f in pins['files']:
  p=deps/f['path'];assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256']
 originals='I:/HeteroSpec/b570-economics-20261106'
 reused=[]
 for name in ('core01','parallel-core02'):
  src=ROOT/name;dest=out/name
  cm=(src/'CMakeLists.txt').read_text()
  cm=cm.replace('C:/hs/b570-direct-id-v1-src',(deps/'source').as_posix())
  cm=cm.replace('C:/hs/b570-direct-id-v1-build/src',(deps/'generated').as_posix())
  cm=cm.replace('C:/hs/b570-direct-id-v1-build',(deps/'libs').as_posix())
  assert 'C:/hs/' not in cm
  if resume:
   assert (dest/'CMakeLists.txt').read_text(encoding='utf-8')==cm
   assert read(str(dest/'compile.log')+'.cost.json')['success']
   assert {p.relative_to(dest/'source').as_posix():sha(p) for p in (dest/'source').rglob('*') if p.is_file()}=={p.relative_to(src/'source').as_posix():sha(p) for p in (src/'source').rglob('*') if p.is_file()}
   reused.append(dict(core=name,compile_log_sha256=sha(dest/'compile.log'),compile_cost=read(str(dest/'compile.log')+'.cost.json'),dll_sha256=sha(dest/'build/Release/llama.dll'),lib_sha256=sha(dest/'build/Release/llama.lib'),source_manifest_sha256=sha(src/'OUTPUT_SOURCE.json')))
  else:
   dest.mkdir();shutil.copytree(src/'source',dest/'source');(dest/'CMakeLists.txt').write_text(cm,encoding='utf-8')
   command(['cmake','-S',dest,'-B',dest/'build','-G','Visual Studio 17 2022','-A','x64'],dest/'configure.log')
   command(['cmake','--build',dest/'build','--config','Release','--parallel','4'],dest/'compile.log')
 if resume:write(out/'RESUME_CORE_BINDING.json',dict(reused=reused,only_frontend_path_assertion_repaired=True,no_model_requests=True))
 choices=[('resident04','M-mode0','core01'),('parallel04','M-mode0','parallel-core02'),('parallel04','C4U4-mode0','parallel-core02')]
 if all_frontends:
  choices=[(kind,f'{arm}-mode{mode}','core01' if kind=='resident04' else 'parallel-core02') for kind in ('resident04','parallel04') for arm in ('M','H1','C4U4','C4U1') for mode in (0,1)]
 results=[]
 for kind,name,core in choices:
  src=ROOT/kind/name;dest=(out/'frontend-attempt02' if resume else out)/kind/name;dest.mkdir(parents=True)
  for p in src.iterdir():
   if p.is_file() and p.suffix.lower() in ('.cpp','.h','.hpp','.inc','.txt'):shutil.copyfile(p,dest/p.name)
  p=dest/'CMakeLists.txt';cm=p.read_text()
  for k in ('core01','parallel-core02'):cm=cm.replace(originals+'/'+k+'/build/Release/llama.lib',(out/k/'build/Release/llama.lib').as_posix())
  assert all(originals+'/'+k+'/build/Release/llama.lib' not in cm for k in ('core01','parallel-core02'))
  cm=cm.replace('C:/hs/b570-direct-id-v1-src',(deps/'source').as_posix()).replace('C:/hs/b570-direct-id-v1-build',(deps/'libs').as_posix())
  p.write_text(cm,encoding='utf-8')
  command(['cmake','-S',dest,'-B',dest/'build','-G','Visual Studio 17 2022','-A','x64','-DPINNED_SOURCE='+(deps/'source').as_posix(),'-DPINNED_BUILD='+(deps/'libs').as_posix()],dest/'configure.log')
  active='target' if name.startswith('M-') else 'native'
  command(['cmake','--build',dest/'build','--config','Release','--target','b570-closeout-'+active,'--parallel','4'],dest/'compile.log')
  bins=dest/'build/Release'
  for f in read(src/'FILES.json')['files']:
   path=native_path(f['path'])
   if path.suffix.lower()=='.dll' and path.name.lower()!='llama.dll':assert sha(path)==f['sha256'];shutil.copyfile(path,bins/path.name)
  shutil.copyfile(out/core/'build/Release/llama.dll',bins/'llama.dll')
  results.append(dict(kind=kind,name=name,core=core,files=[dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=sha(p)) for p in bins.iterdir() if p.suffix.lower() in ('.exe','.dll')]))
 result=dict(status='PORTABLE_PRIVATE_CORES_AND_FRONTENDS_COMPILE_PASS',model_requests=0,native_R_qualification_inherited=False,inputs_sha256=sha(deps/'INPUTS.json'),builds=results,reused_completed_core_compiles=reused,compiler='Visual Studio 17 2022 x64 Release',cuda_used=False,external_absolute_dependencies=False)
 write(out/'BUILD_PROOF.json',result);print(json.dumps(result,indent=2));return result

if __name__=='__main__':rebuild(sys.argv[1],'--all' in sys.argv[2:],'--resume' in sys.argv[2:])
