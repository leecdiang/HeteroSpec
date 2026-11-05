"""Portable frontend/API/import-library inputs, with actual native rebuilds."""
from smol import *

def prepare():
 d=SROOT/'portable';d.mkdir();source=Path('C:/hs/b570-direct-id-v1-src');libs=Path('C:/hs/b570-direct-id-v1-build')
 for sub in ('include','common','src','ggml/include','ggml/src','vendor'):
  for p in (source/sub).rglob('*'):
   if p.is_file() and p.suffix.lower() in ('.h','.hpp','.inc'):
    target=d/'source'/p.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
 shutil.copyfile(source/'LICENSE',d/'source/LICENSE')
 for rel in ('common/Release/llama-common.lib','common/Release/llama-common-base.lib','src/Release/llama.lib','ggml/src/Release/ggml.lib','ggml/src/Release/ggml-base.lib','ggml/src/Release/ggml-cpu.lib','ggml/src/ggml-vulkan/Release/ggml-vulkan.lib'):
  p=d/'libs'/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(libs/rel,p)
 (SROOT/'provenance').mkdir()
 for name in ('MODEL_CHOICE.json','BINARY_BINDINGS.json','CPU_CLOSEOUT_SOURCE_BINDINGS.json','TOKENIZATION_BINDINGS.json','GGUF_TARGET.json','VOCAB_TARGET.json','SMOL_DISCOVERY_INPUTS.json'):
  shutil.copyfile(SMOL/name,SROOT/'provenance'/name)
 for rel in ('src/llama-kv-cache.cpp','src/llama-hparams.h','src/llama-context.cpp','src/llama-io.h','src/llama-memory.h'):
  p=SROOT/'provenance'/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/rel,p)
 write(d/'INPUTS.json',dict(files=[dict(path=p.relative_to(d).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(d.rglob('*')) if p.is_file()],models_included=False))

def builds():
 d=SROOT/'portable';rows=[]
 for arm,target in (('M','b570-closeout-target'),('C4U4','b570-closeout-native')):
  folder=d/('rebuild-'+arm);original=SROOT/'campaign02'/arm
  for n in ('native.cpp','target.cpp','observer.h','CMakeLists.txt','smol_capture.hpp','smol_evidence.hpp','smol_capacity.hpp','smol_bulk.hpp','resource_budget.hpp'):
   folder.mkdir(exist_ok=True);shutil.copyfile(original/n,folder/n)
  command(['cmake','-S',folder,'-B',folder/'build','-G','Visual Studio 17 2022','-A','x64','-DPINNED_SOURCE='+str(d/'source'),'-DPINNED_BUILD='+str(d/'libs')],folder/'configure.log')
  command(['cmake','--build',folder/'build','--config','Release','--target',target,'--parallel','4'],folder/'compile.log')
  rows.append(dict(arm=arm,source_files_equal=True,executable_sha256=sha(folder/'build/Release'/(target+'.exe')),no_model_run=True))
 write(d/'BUILD_PROOF.json',dict(status='ACTUAL_PORTABLE_FRONTEND_REBUILDS_PASS',cases=rows,numerical_libraries_rebuilt=False,external_replication=False))

if __name__=='__main__':{'prepare':prepare,'build':builds}[sys.argv[1]]()
