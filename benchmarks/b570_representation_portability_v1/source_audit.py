"""Bind local frozen backend bytes to existing build and runtime manifests."""
import argparse, datetime
from common import ROOT, load, save, sha, modules

def main():
    import pathlib
    p = argparse.ArgumentParser(); p.add_argument('--old', type=pathlib.Path, required=True)
    p.add_argument('--source', type=pathlib.Path, required=True)
    p.add_argument('--identity', type=pathlib.Path, required=True)
    a = p.parse_args(); before = modules(); identity = load(a.identity)
    paths = ['ggml/src/ggml.c', 'ggml/include/ggml.h', 'ggml/src/ggml-cpu/ops.cpp',
             'ggml/src/ggml-cpu/ggml-cpu.c', 'ggml/src/ggml-cpu/ggml-cpu.cpp',
             'ggml/src/ggml-cpu/vec.cpp', 'ggml/src/ggml-vulkan/ggml-vulkan.cpp',
             'ggml/src/ggml-vulkan/vulkan-shaders/soft_max.comp',
             'ggml/src/ggml-vulkan/vulkan-shaders/mul_mm.comp',
             'ggml/src/ggml-vulkan/vulkan-shaders/mul_mat_vec.comp']
    rows=[]
    for name in paths:
        f=a.source/name; expected=identity['pinned_source_files'].get(name)
        actual=sha(f) if f.exists() else None
        rows.append(dict(path=name, expected=expected, actual=actual,
                         status='MATCH' if expected and expected==actual else 'SOURCE_UNAVAILABLE'))
    runtime=load(a.old/'p0/RUNTIME.json')
    dlls=[]
    for name in ['ggml-base.dll','ggml-cpu.dll','ggml-vulkan.dll']:
        f=a.old/'_host/build/Release'/name
        expected=identity['binaries'][name]
        dlls.append(dict(name=name, expected=expected, actual=sha(f)))
        assert sha(f)==expected
    native=[]
    for name in ['native/local_attention.h','native/graph_numeric_cpu.cpp','native/graph_contract_cpu.cpp',
                 'p0/source-llama-graph.cpp.diff','p0/source-llama-context.cpp.diff',
                 'p0/source-llama-context.h.diff','_host/source/llama-graph.cpp','_host/source/llama-context.cpp']:
        native.append(dict(path=name,sha256=sha(a.old/name)))
    save(ROOT/'SOURCE_BINDINGS.json',dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
         parent='039a24bf61374042e0dc9f3a3619ea40b218a5ad', plan_commit='b69a9cd3',
         original_code='bb803c94f23af0e5ab4e250c52f74e0b60621a66',
         build_manifest_sha256=sha(a.identity), build_manifest_repo_path='benchmarks/b570_partition_intervention_v1/BUILD_IDENTITY.json',
         runtime_manifest_sha256=sha(a.old/'p0/RUNTIME.json'), F0_sha256=sha(a.old/'p0/F0_EXECUTION.json'),
         upstream_commit=identity['upstream_commit'], backend_sources=rows, dlls=dlls, native=native,
         provenance_scope='Existing frozen build manifest pins source bytes and identical inherited numerical DLL bytes. No reproducible binary rebuild claimed.',
         modules_before=before,modules_after=modules(),gpu_starts=0))
    print([(x['path'],x['status']) for x in rows])

if __name__=='__main__': main()
