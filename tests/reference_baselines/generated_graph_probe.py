"""Compile and run generated loop4 host-side probes.

This executes staged C++ mapping or graph-construction code on CPU. It does not
compile CUDA kernels, run a GPU, count GPU launches, or prove numerical
reference equivalence. The supplied library directory must contain a compatible
ggml-base built from the supplied candidate source.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import os
import shutil
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--candidate',type=Path,required=True)
p.add_argument('--library-dir',type=Path,required=True)
p.add_argument('--project-root',type=Path,help='Defaults to the repository root when installed under tests/reference_baselines')
p.add_argument('--compiler',default='g++')
p.add_argument('--sanitizer',choices=['none','undefined','address-undefined'],default='undefined')
p.add_argument('--disable-leak-check',action='store_true',help='For ASan under ptrace environments where LSan is unsupported')
options=p.parse_args()
root=options.project_root.resolve() if options.project_root else Path(__file__).resolve().parents[2];base=options.candidate.resolve();library=options.library_dir.resolve()
compiler=shutil.which(options.compiler)
if not compiler:raise SystemExit('C++ compiler not found: '+options.compiler)
include=base/'ggml/include'
if not include.is_dir() or not library.is_dir():raise SystemExit('Candidate include directory and library directory must exist')
stage_path=root/'scripts/reference_baselines/stage.py'
spec=importlib.util.spec_from_file_location('loop4_stage_under_test',stage_path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
work=tempfile.TemporaryDirectory(prefix='hs-loop4-generated-')
generated=Path(work.name)/'probe.cpp'
s=m.graph_variant((base/'src/llama-graph.cpp').read_text(),'backend_loop4')
a=s.index('    ggml_tensor * res = nullptr;',s.index('ggml_tensor * llm_graph_context::build_lora_mm('));b=s.index('    if (w_s)',a)
body=s[a:b]
generated.write_text('''#include "loop4_tensor.hpp"
#include <cassert>
#include <algorithm>
#include <iostream>
ggml_tensor * build(ggml_context * ctx0,ggml_tensor * w,ggml_tensor * cur,bool hs_query_batch){
'''+body+'''return res;}
int main(){int cases=0;for(int q=1;q<=40;++q)for(auto wt:{GGML_TYPE_Q8_0,GGML_TYPE_Q4_0,GGML_TYPE_F32})for(bool active:{false,true})for(bool contiguous:{false,true}){
 auto ctx=ggml_init({2*1024*1024,nullptr,true});auto w=ggml_new_tensor_2d(ctx,wt,32,7);auto base=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,contiguous?32:64,q);auto x=contiguous?base:ggml_view_2d(ctx,base,32,q,base->nb[1],0);
 auto out=build(ctx,w,x,active);auto graph=ggml_new_graph(ctx);ggml_build_forward_expand(graph,out);
 int marks=0,matmuls=0;for(int i=0;i<ggml_graph_n_nodes(graph);++i){auto n=ggml_graph_node(graph,i);marks+=hs_loop4::marked(n);matmuls+=n->op==GGML_OP_MUL_MAT;}
 bool eligible=active&&wt==GGML_TYPE_Q8_0&&q>4&&q<=32;
 assert(marks==int(eligible&&contiguous));assert(matmuls==(eligible&&!contiguous?(q+3)/4:1));assert(out->ne[0]==7&&out->ne[1]==q);if(marks)hs_loop4::require(w,x,out);++cases;ggml_free(ctx);
 }std::cout<<"GENERATED_GRAPH_MARKER_FALLBACK_CASES="<<cases<<" GPU_EXECUTIONS=0\\n";}
''')

flags=['-std=c++17','-Wall','-Wextra','-Werror','-pedantic']
if options.sanitizer!='none':
    flags+=['-fsanitize='+('address,undefined' if options.sanitizer=='address-undefined' else 'undefined'),'-fno-sanitize-recover=all']
exe=Path(work.name)/'probe'
command=[compiler,*flags,'-I'+str(root/'src/reference_baselines'),'-I'+str(include),str(generated),'-L'+str(library),'-Wl,-rpath,'+str(library),'-lggml-base','-o',str(exe)]
env=os.environ.copy()
if options.disable_leak_check:
    env['ASAN_OPTIONS']=env.get('ASAN_OPTIONS','')+':detect_leaks=0'
try:
    subprocess.run(command,check=True)
    subprocess.run([str(exe)],check=True,env=env)
    print('CUDA_COMPILE=NOT_RUN GPU_EXECUTIONS=0 NUMERICAL_REFERENCE_EQUIVALENCE=NOT_ESTABLISHED')
    print('STAGE_SCRIPT_SHA256='+hashlib.sha256(stage_path.read_bytes()).hexdigest())
finally:
    work.cleanup()
