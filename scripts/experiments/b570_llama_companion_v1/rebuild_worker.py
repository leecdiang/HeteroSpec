"""Build a successor host/observer executable against byte-identical frozen DLLs."""
from pathlib import Path
import argparse
import shutil
import subprocess
from common import read, write, sha, need, utc
from host import build_files, code_identity


def rebuild(parent_receipt, output):
    parent_receipt = Path(parent_receipt).resolve()
    parent = build_files(parent_receipt)
    output = Path(output).resolve()
    need(not output.exists(), 'fresh successor build directory')
    source = output / 'worker-source'
    source.mkdir(parents=True)
    here = Path(__file__).resolve().parent
    for name in ('worker.cpp', 'cycle.hpp', 'companion_scope.hpp'):
        shutil.copyfile(here / name, source / name)
    upstream = Path(parent['source']['root'])
    parent_build = parent_receipt.parent / 'build'
    # Runtime DLLs and their original import libraries are never rebuilt here.
    libraries = [parent_build / 'runtime/src/Release/llama.lib']
    libraries += [parent_build / ('runtime/ggml/src/Release/' + name + '.lib') for name in ('ggml', 'ggml-base')]
    need(all(p.is_file() for p in libraries), 'original import libraries missing')
    cmake = '''cmake_minimum_required(VERSION 3.20)
project(b570_worker_successor LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
add_executable(b570_llama worker.cpp)
target_compile_options(b570_llama PRIVATE /O2 /W4 /fp:precise /utf-8)
target_compile_definitions(b570_llama PRIVATE LLAMA_SHARED GGML_SHARED GGML_BACKEND_SHARED GGML_USE_CPU GGML_USE_VULKAN HS_COMPANION_ORACLE=%d)
''' % (parent['mode'] == 'oracle')
    cmake += 'target_include_directories(b570_llama PRIVATE ' + ' '.join('"'+(upstream/p).as_posix()+'"' for p in ('include', 'ggml/include', 'vendor')) + ')\n'
    cmake += 'target_link_libraries(b570_llama PRIVATE ' + ' '.join('"'+p.as_posix()+'"' for p in libraries) + ')\n'
    cmake += 'set_target_properties(b570_llama PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")\n'
    (source / 'CMakeLists.txt').write_text(cmake)
    commands = [['cmake', '-S', str(source), '-B', str(output/'build'), '-G', 'Visual Studio 17 2022', '-A', 'x64'],
                ['cmake', '--build', str(output/'build'), '--config', 'Release', '--parallel', '4']]
    write(output/'COMMANDS.json', {'utc': utc(), 'argv': commands, 'parent_build_sha256': sha(parent_receipt)})
    for i, command in enumerate(commands):
        with (output / f'command-{i}.log').open('xb') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=1200)
    exe = output/'build/bin/Release/b570_llama.exe'
    files = [exe]
    for f in parent['files']:
        p = Path(f['path'])
        if p.suffix.lower() == '.dll':
            dest = exe.parent / p.name
            shutil.copyfile(p, dest)
            need(sha(dest) == f['sha256'], 'numerical library changed')
            files.append(dest)
    supervisor = output/'supervisor.py'
    shutil.copyfile(parent['supervisor'], supervisor)
    receipt = dict(parent, executable=str(exe), supervisor=str(supervisor), supervisor_sha256=sha(supervisor),
                   files=[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files],
                   authoring_files=code_identity(), parent_build_receipt=str(parent_receipt), parent_build_sha256=sha(parent_receipt),
                   numerical_libraries_unchanged=True,
                   successor_worker_source={p.name:sha(p) for p in source.iterdir() if p.is_file()})
    write(output/'BUILD.json', receipt)
    print(output)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();rebuild(a.parent,a.out)
