from pathlib import Path
import hashlib,json

HERE=Path(__file__).resolve().parent
BASE=HERE/'source';OUT=HERE/'final-source';cuda=OUT/'ggml/src/ggml-cuda'
cmake=cuda/'CMakeLists.txt';before=cmake.read_bytes()
(HERE/'final-source-stage-v1/CMakeLists_before_idempotent_fix.txt').write_bytes(before)
s=(BASE/'ggml/src/ggml-cuda/CMakeLists.txt').read_text(encoding='utf8')
anchor='    file(GLOB   GGML_SOURCES_CUDA "*.cu")'
if s.count(anchor)!=1:raise RuntimeError('CMake source anchor changed')
s=s.replace(anchor,anchor+'''
    list(APPEND GGML_SOURCES_CUDA hs_e03_runtime.cpp)
    if(GGML_CUDA_GRAPHS OR GGML_CUDA_NCCL OR NOT GGML_CUDA_NO_VMM)
        message(FATAL_ERROR "E03 requires graphs/NCCL OFF and NO_VMM ON for all arms")
    endif()
    if(CMAKE_CUDA_FLAGS MATCHES "GGML_CUDA_USE_PDL")
        message(FATAL_ERROR "E03 pair4 requires PDL disabled")
    endif()''')
cmake.write_text(s,encoding='utf8',newline='\n')
if s.count('list(APPEND GGML_SOURCES_CUDA hs_e03_runtime.cpp)')!=1:raise RuntimeError('duplicate runtime source entry')
receipt=json.loads((HERE/'FINAL_SOURCE_IDENTITIES.json').read_bytes())
(HERE/'FINAL_SOURCE_IDENTITIES_INITIAL.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
receipt['source_files_sha256']={p.relative_to(OUT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.rglob('*')) if p.is_file()}
receipt['PDL_policy']='disabled; build command list contains no GGML_CUDA_USE_PDL define; future supported entry rejects it'
(HERE/'FINAL_SOURCE_IDENTITIES.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps({'CMake_runtime_entries':s.count('list(APPEND GGML_SOURCES_CUDA hs_e03_runtime.cpp)'),'source_files':len(receipt['source_files_sha256'])}))
