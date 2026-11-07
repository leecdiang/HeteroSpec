"""Add a bounded shared-weight DVR frontend to the same private core."""
import shutil
from common import *
def main():
    cfg=read(LOCAL/'CONFIG.json');src=LOCAL/'native/source';build=LOCAL/'native/build';dest=src/'jsa-dvr'
    dest.mkdir(exist_ok=True);shutil.copyfile(Path(__file__).parent/'dvr_server.cpp',dest/'dvr_server.cpp')
    p=src/'CMakeLists.txt';text=p.read_text(encoding='utf-8');text=text.split('\nadd_executable(jsa-dvr-server')[0];p.write_text(text+'''
add_executable(jsa-dvr-server jsa-dvr/dvr_server.cpp)
target_compile_features(jsa-dvr-server PRIVATE cxx_std_17)
target_include_directories(jsa-dvr-server PRIVATE ${CMAKE_SOURCE_DIR}/vendor/nlohmann ${CMAKE_SOURCE_DIR}/vendor/cpp-httplib)
target_link_libraries(jsa-dvr-server PRIVATE llama cpp-httplib ws2_32)
''',encoding='utf-8',newline='\n')
    cmake=Path(cfg['asset'])/'.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe';cmd=[str(cmake),'--build',str(build),'--target','jsa-dvr-server','-j','4']
    attempt=len(list((LOCAL/'native').glob('build-dvr-*.log')))+1
    with (LOCAL/'native'/f'build-dvr-{attempt}.log').open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
    save(LOCAL/'native/DVR_BUILD_ATTEMPT.json',{'command':cmd,'exit_code':r.returncode});assert r.returncode==0
    save(PUB/'DVR_BUILD.json',{'exe_sha256':sha(build/'bin/jsa-dvr-server.exe'),'source_sha256':sha(dest/'dvr_server.cpp'),'CMakeLists_sha256':sha(p),'core_graph_sha256':sha(src/'src/llama-graph.cpp'),'cuda_sha256':sha(build/'bin/ggml-cuda.dll'),'status':'BUILT_NOT_QUALIFIED'})
    print('DVR BUILD COMPLETE',flush=True)
if __name__=='__main__':main()
