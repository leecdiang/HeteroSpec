"""Keep first compile source frozen; stage one consistent final rebuild source."""
from pathlib import Path
import argparse,hashlib,json,shutil

HERE=Path(__file__).resolve().parent
BASE=HERE/'source';OUT=HERE/'final-source'
parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');args=parser.parse_args()
if args.refresh:
    backup=HERE/'final-source-stage-v1';backup.mkdir(exist_ok=False)
    for name in ('mmvq.cu','ggml-cuda.cu','hs_e03_runtime.hpp','hs_e03_runtime.cpp','hs_launch_budget.hpp','hs_launch_budget.cu','CMakeLists.txt'):
        shutil.copy2(OUT/'ggml/src/ggml-cuda'/name,backup/name)
else:
    OUT.mkdir(exist_ok=False)
    for p in sorted(BASE.rglob('*')):
        if p.is_file():
            target=OUT/p.relative_to(BASE);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
cuda=OUT/'ggml/src/ggml-cuda';stage=HERE/'stage-v4';canonical=HERE.parent/'e03/launch_budget'
for name in ('mmvq.cu','ggml-cuda.cu','hs_e03_runtime.hpp','hs_e03_runtime.cpp'):shutil.copy2(stage/name,cuda/name)
shutil.copy2(canonical/'hs_launch_budget.hpp',cuda/'hs_launch_budget.hpp')
shutil.copy2(canonical/'hs_launch_budget.cpp',cuda/'hs_launch_budget.cu')
cmake=cuda/'CMakeLists.txt';s=(BASE/'ggml/src/ggml-cuda/CMakeLists.txt').read_text(encoding='utf8')
anchor='    file(GLOB   GGML_SOURCES_CUDA "*.cu")'
if s.count(anchor)!=1:raise RuntimeError('CMake source-list anchor changed')
s=s.replace(anchor,anchor+'''
    list(APPEND GGML_SOURCES_CUDA hs_e03_runtime.cpp)
    if(GGML_CUDA_GRAPHS OR GGML_CUDA_NCCL OR NOT GGML_CUDA_NO_VMM)
        message(FATAL_ERROR "E03 requires graphs/NCCL OFF and NO_VMM ON for all arms")
    endif()
    if(CMAKE_CUDA_FLAGS MATCHES "GGML_CUDA_USE_PDL")
        message(FATAL_ERROR "E03 pair4 requires PDL disabled")
    endif()''')
cmake.write_text(s,encoding='utf8',newline='\n')
identities={p.relative_to(OUT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.rglob('*')) if p.is_file()}
receipt={'schema':'heterospec.e03.final-runtime-source.v1','base_source':str(BASE),'final_source':str(OUT),'files':len(identities),
    'exactly_one_budget_implementation':'hs_launch_budget.cu copied from final canonical cpp',
    'provider_sha256':identities['ggml/src/ggml-cuda/hs_launch_budget.cu'],
    'provider_header_sha256':identities['ggml/src/ggml-cuda/hs_launch_budget.hpp'],
    'source_files_sha256':identities,'model_requests':0,'kernel_launches':0}
(HERE/'FINAL_SOURCE_IDENTITIES.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='source_files_sha256'}))
